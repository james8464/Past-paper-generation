"""Bind bounded SQL execution to typed, candidate-visible table rows."""

import math
import re
import sqlite3
from collections import Counter
from collections.abc import Sequence
from decimal import Decimal

from Backend.Core.france.nsi import NSIExercise, NSIQuestion, NSITableMaterial

SQL_SOURCE_POLICY = "fr-nsi-v36-sql-source-v1"

# Only unquoted SQL words can introduce COLLATE. Quoted identifiers/literals
# and comments are inert here; SQLite has already parsed the complete DDL.
_DDL_TOKENS = re.compile(
    r"--[^\r\n]*|/\*.*?\*/|'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\""
    r"|`(?:[^`]|``)*`|\[[^\]]*\]|(?P<word>[A-Za-z_][A-Za-z_0-9]*)",
    re.S,
)


def _has_collation(declaration: str) -> bool:
    return any(
        match.group("word") is not None and match.group("word").upper() == "COLLATE"
        for match in _DDL_TOKENS.finditer(declaration)
    )


def sql_caption(material: NSITableMaterial) -> str:
    descriptor = material.sql
    if descriptor is None:
        return ""
    columns = "; ".join(
        f"{name} : {kind}{' (NULL autorisé)' if nullable else ' (non NULL)'}"
        for name, kind, nullable in zip(
            material.columns, descriptor.column_types, descriptor.nullable, strict=True
        )
    )
    caption = (
        f"Relation SQLite {descriptor.table_name}. {columns}. "
        "NULL désigne une valeur absente uniquement dans une colonne nullable; "
        "ailleurs, les textes sont conservés exactement."
    )
    if "REAL" in descriptor.column_types:
        caption += " REAL utilise des nombres binaires approchés; les décimaux sont écrits avec un point."
    return caption


def _cell(
    value: str, kind: str, nullable: bool
) -> tuple[str, str | int | float | None]:
    if value == "NULL" and nullable:
        return ("null", None)
    if kind == "TEXT":
        return ("text", value)
    if kind == "INTEGER":
        if re.fullmatch(r"0|-?[1-9][0-9]{0,18}", value) is None:
            raise ValueError("Entier SQL imprimé ambigu")
        number = int(value)
        if not -(2**63) <= number < 2**63:
            raise ValueError("Entier SQL imprimé hors limites")
        return ("integer", number)
    # A bounded, canonical decimal whose shortest float spelling preserves its
    # decimal value. Never silently round extra precision or accept NaN/Infinity.
    if re.fullmatch(r"-?(?:0|[1-9][0-9]{0,14})\.[0-9]{1,14}", value) is None:
        raise ValueError("REAL SQL imprimé ambigu")
    real_number = float(value)
    if not math.isfinite(real_number) or Decimal(str(real_number)) != Decimal(value):
        raise ValueError("Précision REAL SQL imprimée non prise en charge")
    return ("real", real_number)


def bound_materials(
    exercise: NSIExercise, question: NSIQuestion
) -> list[NSITableMaterial]:
    ids = question.verification.get("source_material_ids")
    if (
        not isinstance(ids, list)
        or not 1 <= len(ids) <= 6
        or any(not isinstance(value, str) for value in ids)
        or len(set(ids)) != len(ids)
        or set(ids) - set(question.material_ids)
    ):
        raise ValueError("Sources SQL imprimées absentes ou invalides")
    by_id = {material.id: material for material in exercise.materials}
    result = []
    for identifier in ids:
        material = by_id.get(identifier)
        if not isinstance(material, NSITableMaterial) or material.sql is None:
            raise ValueError("La source SQL doit être un tableau typé imprimé")
        result.append(material)
    names = [material.sql.table_name.lower() for material in result if material.sql]
    if len(set(names)) != len(names):
        raise ValueError("Relations SQL imprimées répétées")
    return result


def validate_database(
    db: sqlite3.Connection, materials: Sequence[NSITableMaterial]
) -> dict[str, frozenset[str]]:
    """Called only during owned inspection, before enabling query-only access."""
    if not materials or any(material.sql is None for material in materials):
        raise ValueError("Descripteur SQL imprimé absent")
    expected = {
        material.sql.table_name: material for material in materials if material.sql
    }
    if len({name.lower() for name in expected}) != len(materials):
        raise ValueError("Relations SQL imprimées répétées")
    objects = db.execute(
        "SELECT 'main',name,type,tbl_name,sql FROM main.sqlite_schema UNION ALL "
        "SELECT 'temp',name,type,tbl_name,sql FROM temp.sqlite_schema"
    ).fetchall()
    tables = []
    for database, name, kind, owner, declaration in objects:
        # SQLite owns these reserved, SQL-less indexes for PRIMARY KEY/UNIQUE.
        # They add no source relation. Explicit/user indexes remain unsupported.
        if (
            database == "main"
            and kind == "index"
            and declaration is None
            and owner in expected
            and re.fullmatch(
                r"sqlite_autoindex_" + re.escape(owner) + r"_[1-9][0-9]*", name
            )
        ):
            continue
        if (
            database != "main"
            or kind != "table"
            or name not in expected
            or owner != name
        ):
            raise ValueError("Objet SQL privé sans source imprimée")
        tables.append((name, declaration))
    if {name for name, _ in tables} != set(expected) or len(tables) != len(expected):
        raise ValueError("Relation SQL imprimée absente ou répétée")
    if any(_has_collation(declaration) for _, declaration in tables):
        raise ValueError("Collation SQL privée non déclarée dans la source imprimée")
    for name, material in expected.items():
        assert material.sql is not None
        # Identifiers are validated before use, and the SQL here is owned code.
        columns = db.execute(f'PRAGMA main.table_xinfo("{name}")').fetchall()
        wanted_columns = list(
            zip(material.columns, material.sql.column_types, strict=True)
        )
        if [(row[1], row[2]) for row in columns] != wanted_columns or any(
            row[6] for row in columns
        ):
            raise ValueError("Colonnes SQL différentes de la source imprimée")
        wanted_rows = Counter(
            tuple(
                _cell(value, kind, nullable)
                for value, kind, nullable in zip(
                    row, material.sql.column_types, material.sql.nullable, strict=True
                )
            )
            for row in material.rows
        )
        fields = ",".join(
            f'"{column}",typeof("{column}")' for column in material.columns
        )
        rows = db.execute(f'SELECT {fields} FROM main."{name}"').fetchmany(31)
        actual = Counter(
            tuple((row[i + 1], row[i]) for i in range(0, len(row), 2)) for row in rows
        )
        if actual != wanted_rows:
            raise ValueError("Données SQL différentes de la source imprimée")
    return {name: frozenset(material.columns) for name, material in expected.items()}
