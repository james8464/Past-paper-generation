"""Immutable, application-owned facts for a deeper French NSI database case.

V2 is separate from V1 so saved V13-V15 packages retain their source identity.
"""

from __future__ import annotations

import json
import random
import sqlite3
from dataclasses import dataclass
from hashlib import sha256

_TASK_IDS = tuple(f"2{letter}" for letter in "abcdefghij")
_COLUMNS = {
    "agent": ["id_agent", "nom", "secteur"],
    "categorie": ["id_cat", "libelle"],
    "incident": ["id_incident", "id_agent", "id_cat", "statut"],
}
_FOREIGN_KEYS = [
    ["incident", "id_agent", "agent", "id_agent"],
    ["incident", "id_cat", "categorie", "id_cat"],
]
_INCIDENTS = [
    [101, 1, 2, "ouvert"],
    [102, 1, 3, "clos"],
    [103, 2, 1, "clos"],
    [104, 3, 2, "ouvert"],
    [105, 2, 2, "ouvert"],
    [106, 3, 1, "ouvert"],
]
_SELECT_PREFIX = (
    "SELECT incident.id_incident, categorie.libelle\n"
    "FROM incident\nJOIN categorie ON\n    "
)
_FAULTY_SQL = (
    _SELECT_PREFIX
    + "incident.id_agent = categorie.id_cat\nORDER BY incident.id_incident"
)
_CORRECT_SQL = (
    _SELECT_PREFIX + "incident.id_cat = categorie.id_cat\nORDER BY incident.id_incident"
)
_GROUP_SQL = (
    "SELECT categorie.id_cat, categorie.libelle,\n"
    "       COUNT(incident.id_incident)\n"
    "FROM categorie\nLEFT JOIN incident\n"
    "    ON incident.id_cat = categorie.id_cat\n"
    "GROUP BY categorie.id_cat, categorie.libelle\n"
    "ORDER BY categorie.id_cat"
)
_UPDATE_SQL = "UPDATE incident SET statut = 'clos'\nWHERE id_incident = 101"
_FAULTY_PYTHON = (
    "def nombre_clos(incidents):\n"
    "    total = 0\n"
    "    for incident in incidents:\n"
    "        if incident['statut'] == 'ouvert':\n"
    "            total += 1\n"
    "    return total"
)
_CORRECT_PYTHON = _FAULTY_PYTHON.replace("== 'ouvert'", "== 'clos'")


def _validated_rows(tables: object) -> dict[str, list[list]]:
    if not isinstance(tables, dict) or set(tables) != set(_COLUMNS):
        raise ValueError("Invalid database depth tables")
    rows_by_table = {}
    for name, columns in _COLUMNS.items():
        table = tables[name]
        if not isinstance(table, dict) or set(table) != {"columns", "rows"}:
            raise ValueError("Invalid database depth table fields")
        if table["columns"] != columns:
            raise ValueError("Invalid database depth columns")
        rows = table["rows"]
        if not isinstance(rows, list) or len(rows) != (6 if name == "incident" else 3):
            raise ValueError("Invalid database depth row count")
        if any(not isinstance(row, list) or len(row) != len(columns) for row in rows):
            raise ValueError("Nonrectangular database depth rows")
        keys = [row[0] for row in rows]
        if any(type(key) is not int or not 1 <= key <= 999 for key in keys):
            raise ValueError("Invalid database depth primary key")
        if len(set(keys)) != len(keys):
            raise ValueError("Duplicate database depth primary key")
        rows_by_table[name] = rows
    if [row[0] for row in rows_by_table["agent"]] != [1, 2, 3] or [
        row[0] for row in rows_by_table["categorie"]
    ] != [1, 2, 3]:
        raise ValueError("Database depth key identity changed")
    for name in ("agent", "categorie"):
        values = [value for row in rows_by_table[name] for value in row[1:]]
        if any(
            not isinstance(value, str) or not value.isalpha() or len(value) > 24
            for value in values
        ):
            raise ValueError("Invalid database depth label")
    if len({row[1] for row in rows_by_table["categorie"]}) != 3:
        raise ValueError("Database depth categories must differ")
    if any(
        type(row[1]) is not int or type(row[2]) is not int
        for row in rows_by_table["incident"]
    ):
        raise ValueError("Invalid database depth foreign key type")
    if rows_by_table["incident"] != _INCIDENTS:
        raise ValueError("Database depth incident facts changed")
    return rows_by_table


def _expected(rows: dict[str, list[list]]) -> dict:
    connection = sqlite3.connect(":memory:")
    try:
        connection.executescript(
            "PRAGMA foreign_keys = ON;"
            "CREATE TABLE agent(id_agent INTEGER PRIMARY KEY, nom TEXT, secteur TEXT);"
            "CREATE TABLE categorie(id_cat INTEGER PRIMARY KEY, libelle TEXT);"
            "CREATE TABLE incident(id_incident INTEGER PRIMARY KEY, id_agent INTEGER "
            "REFERENCES agent(id_agent), id_cat INTEGER REFERENCES categorie(id_cat), "
            "statut TEXT);"
        )
        for name, columns in _COLUMNS.items():
            slots = ",".join("?" for _ in columns)
            connection.executemany(f"INSERT INTO {name} VALUES ({slots})", rows[name])
        faulty = [list(row) for row in connection.execute(_FAULTY_SQL)]
        correct = [list(row) for row in connection.execute(_CORRECT_SQL)]
        groups = [list(row) for row in connection.execute(_GROUP_SQL)]
        closed_before = connection.execute(
            "SELECT COUNT(*) FROM incident WHERE statut = 'clos'"
        ).fetchone()[0]
        faulty_count = connection.execute(
            "SELECT COUNT(*) FROM incident WHERE statut = 'ouvert'"
        ).fetchone()[0]
        if faulty == correct or closed_before == faulty_count:
            raise ValueError("Database depth faults are not observable")
        cursor = connection.execute(_UPDATE_SQL)
        updated_ids = [
            row[0]
            for row in connection.execute(
                "SELECT id_incident FROM incident WHERE id_incident = 101 "
                "AND statut = 'clos'"
            )
        ]
        return {
            "faulty_join": faulty,
            "correct_join": correct,
            "category_counts": groups,
            "closed_before": closed_before,
            "faulty_python_count": faulty_count,
            "updated_ids": updated_ids,
            "updated_count": cursor.rowcount,
            "closed_after_update": connection.execute(
                "SELECT COUNT(*) FROM incident WHERE statut = 'clos'"
            ).fetchone()[0],
            "empty_closed_count": 0,
        }
    finally:
        connection.close()


@dataclass(frozen=True)
class DatabaseDepthContract:
    """Canonical JSON with every expected result recomputed from locked data."""

    _json: str

    def to_dict(self) -> dict:
        return json.loads(self._json)

    @property
    def digest(self) -> str:
        return sha256(self._json.encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, data: dict) -> DatabaseDepthContract:
        required = {
            "version",
            "seed",
            "exercise_id",
            "task_ids",
            "tables",
            "foreign_keys",
            "faulty_sql",
            "correct_sql",
            "group_sql",
            "update_sql",
            "faulty_python",
            "correct_python",
        }
        if not isinstance(data, dict) or set(data) not in (
            required,
            required | {"expected"},
        ):
            raise ValueError("Invalid database depth fields")
        if (
            type(data["version"]) is not int
            or data["version"] != 2
            or type(data["seed"]) is not int
            or data["exercise_id"] != "2"
            or data["task_ids"] != list(_TASK_IDS)
            or data["foreign_keys"] != _FOREIGN_KEYS
            or data["faulty_sql"] != _FAULTY_SQL
            or data["correct_sql"] != _CORRECT_SQL
            or data["group_sql"] != _GROUP_SQL
            or data["update_sql"] != _UPDATE_SQL
            or data["faulty_python"] != _FAULTY_PYTHON
            or data["correct_python"] != _CORRECT_PYTHON
        ):
            raise ValueError("Invalid database depth identity or source")
        rows = _validated_rows(data["tables"])
        expected = _expected(rows)
        if "expected" in data and data["expected"] != expected:
            raise ValueError("Database depth expected result mismatch")
        canonical = {**data, "expected": expected}
        return cls(
            json.dumps(
                canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
        )


def build_database_depth_contract(
    seed: int, exercise_id: str = "2"
) -> DatabaseDepthContract:
    if type(seed) is not int or exercise_id != "2":
        raise ValueError("Unsupported database depth seed or exercise")
    rng = random.Random(f"french-nsi-database-v2:{seed}:{exercise_id}")
    names = rng.sample(["Alice", "Benoit", "Camille", "David", "Emma", "Farid"], 3)
    sectors = rng.sample(["Nord", "Sud", "Est", "Ouest", "Centre"], 3)
    labels = rng.sample(["Materiel", "Logiciel", "Reseau", "Stockage", "Acces"], 3)
    return DatabaseDepthContract.from_dict(
        {
            "version": 2,
            "seed": seed,
            "exercise_id": exercise_id,
            "task_ids": list(_TASK_IDS),
            "tables": {
                "agent": {
                    "columns": _COLUMNS["agent"],
                    "rows": [[i, names[i - 1], sectors[i - 1]] for i in (1, 2, 3)],
                },
                "categorie": {
                    "columns": _COLUMNS["categorie"],
                    "rows": [[i, labels[i - 1]] for i in (1, 2, 3)],
                },
                "incident": {"columns": _COLUMNS["incident"], "rows": _INCIDENTS},
            },
            "foreign_keys": _FOREIGN_KEYS,
            "faulty_sql": _FAULTY_SQL,
            "correct_sql": _CORRECT_SQL,
            "group_sql": _GROUP_SQL,
            "update_sql": _UPDATE_SQL,
            "faulty_python": _FAULTY_PYTHON,
            "correct_python": _CORRECT_PYTHON,
        }
    )
