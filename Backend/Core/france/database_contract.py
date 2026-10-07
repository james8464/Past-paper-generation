"""Application-owned relational facts for a French NSI written exercise.

All SQL and Python shown to learners is fixed here. Only validated, seeded
data varies; no model-authored statement or code is executed.
"""

from __future__ import annotations

import json
import random
import sqlite3
from dataclasses import dataclass
from hashlib import sha256

_TASK_IDS = ("2a", "2b", "2c", "2d", "2e", "2f")
_COLUMNS = {
    "agent": ["id_agent", "nom", "secteur"],
    "categorie": ["id_cat", "libelle"],
    "incident": ["id_incident", "id_agent", "id_cat", "statut"],
}
_FOREIGN_KEYS = [
    ["incident", "id_agent", "agent", "id_agent"],
    ["incident", "id_cat", "categorie", "id_cat"],
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
_UPDATE_SQL = "UPDATE incident SET statut = 'clos'\nWHERE id_incident = {incident_id}"
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
        raise ValueError("Invalid database tables")
    rows_by_table: dict[str, list[list]] = {}
    for name, columns in _COLUMNS.items():
        table = tables[name]
        if not isinstance(table, dict) or set(table) != {"columns", "rows"}:
            raise ValueError("Invalid database table field")
        if table["columns"] != columns:
            raise ValueError("Invalid database columns")
        rows = table["rows"]
        if not isinstance(rows, list) or len(rows) != (4 if name == "incident" else 3):
            raise ValueError("Invalid database row count")
        if any(not isinstance(row, list) or len(row) != len(columns) for row in rows):
            raise ValueError("Nonrectangular database rows")
        keys = [row[0] for row in rows]
        if any(type(key) is not int or not 1 <= key <= 999 for key in keys):
            raise ValueError("Invalid primary key")
        if len(set(keys)) != len(keys):
            raise ValueError("Duplicate primary key")
        rows_by_table[name] = rows

    for row in rows_by_table["agent"]:
        if any(
            not isinstance(value, str) or not value.isalpha() or len(value) > 24
            for value in row[1:]
        ):
            raise ValueError("Invalid agent value")
    for row in rows_by_table["categorie"]:
        if not isinstance(row[1], str) or not row[1].isalpha() or len(row[1]) > 24:
            raise ValueError("Invalid category value")
    agent_ids = {row[0] for row in rows_by_table["agent"]}
    category_ids = {row[0] for row in rows_by_table["categorie"]}
    for row in rows_by_table["incident"]:
        if type(row[1]) is not int or row[1] not in agent_ids:
            raise ValueError("Broken agent foreign key")
        if type(row[2]) is not int or row[2] not in category_ids:
            raise ValueError("Broken category foreign key")
        if row[3] not in {"ouvert", "clos"}:
            raise ValueError("Invalid incident status")
    return rows_by_table


def _expected(rows: dict[str, list[list]], update_sql: str) -> dict:
    connection = sqlite3.connect(":memory:")
    try:
        connection.executescript(
            "CREATE TABLE agent(id_agent INTEGER PRIMARY KEY, nom TEXT, secteur TEXT);"
            "CREATE TABLE categorie(id_cat INTEGER PRIMARY KEY, libelle TEXT);"
            "CREATE TABLE incident(id_incident INTEGER PRIMARY KEY, id_agent INTEGER, "
            "id_cat INTEGER, statut TEXT);"
        )
        for name, columns in _COLUMNS.items():
            slots = ",".join("?" for _ in columns)
            connection.executemany(f"INSERT INTO {name} VALUES ({slots})", rows[name])
        faulty = [list(row) for row in connection.execute(_FAULTY_SQL)]
        correct = [list(row) for row in connection.execute(_CORRECT_SQL)]
        closed_before = sum(row[3] == "clos" for row in rows["incident"])
        faulty_count = sum(row[3] == "ouvert" for row in rows["incident"])
        if faulty == correct or closed_before == faulty_count:
            raise ValueError("Database fault is not observable")
        target = rows["incident"][0][0]
        if rows["incident"][0][3] != "ouvert":
            raise ValueError("Update target must begin open")
        cursor = connection.execute(update_sql)
        updated = [
            row[0]
            for row in connection.execute(
                "SELECT id_incident FROM incident WHERE statut = 'clos' "
                "AND id_incident = ?",
                (target,),
            )
        ]
        return {
            "faulty_join": faulty,
            "correct_join": correct,
            "closed_before": closed_before,
            "faulty_python_count": faulty_count,
            "updated_ids": updated,
            "updated_count": cursor.rowcount,
            "closed_after_update": connection.execute(
                "SELECT COUNT(*) FROM incident WHERE statut = 'clos'"
            ).fetchone()[0],
        }
    finally:
        connection.close()


@dataclass(frozen=True)
class DatabaseContract:
    """Canonical, immutable JSON with recomputed expected results."""

    _json: str

    def to_dict(self) -> dict:
        return json.loads(self._json)

    @property
    def digest(self) -> str:
        return sha256(self._json.encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, data: dict) -> DatabaseContract:
        if not isinstance(data, dict) or set(data) - {
            "version",
            "seed",
            "exercise_id",
            "task_ids",
            "tables",
            "foreign_keys",
            "faulty_sql",
            "correct_sql",
            "update_sql",
            "faulty_python",
            "correct_python",
            "expected",
        }:
            raise ValueError("Unexpected database contract field")
        if (
            data.get("version") != 1
            or type(data.get("seed")) is not int
            or data.get("exercise_id") != "2"
            or data.get("task_ids") != list(_TASK_IDS)
            or data.get("foreign_keys") != _FOREIGN_KEYS
            or data.get("faulty_sql") != _FAULTY_SQL
            or data.get("correct_sql") != _CORRECT_SQL
            or data.get("faulty_python") != _FAULTY_PYTHON
            or data.get("correct_python") != _CORRECT_PYTHON
        ):
            raise ValueError("Invalid database contract identity or code")
        rows = _validated_rows(data.get("tables"))
        target = rows["incident"][0][0]
        update_sql = _UPDATE_SQL.format(incident_id=target)
        if data.get("update_sql") != update_sql:
            raise ValueError("Invalid bounded update SQL")
        expected = _expected(rows, update_sql)
        if "expected" in data and data["expected"] != expected:
            raise ValueError("Canonical expected result mismatch")
        canonical = {**data, "expected": expected}
        if len(canonical) != 12:
            raise ValueError("Missing database contract field")
        return cls(
            json.dumps(
                canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
        )


def build_database_contract(seed: int, exercise_id: str = "2") -> DatabaseContract:
    if type(seed) is not int or exercise_id != "2":
        raise ValueError("Unsupported database seed or exercise")
    rng = random.Random(f"french-nsi-database-v1:{seed}:{exercise_id}")
    names = rng.sample(["Alice", "Benoit", "Camille", "David", "Emma", "Farid"], 3)
    sectors = rng.sample(["Nord", "Sud", "Est", "Ouest", "Centre"], 3)
    labels = rng.sample(["Materiel", "Logiciel", "Reseau", "Stockage", "Acces"], 3)
    incidents = [
        [101, 1, 2, "ouvert"],
        [102, 1, 3, "clos"],
        [103, 2, 1, "clos"],
        [104, 3, 2, "clos"],
    ]
    return DatabaseContract.from_dict(
        {
            "version": 1,
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
                "incident": {"columns": _COLUMNS["incident"], "rows": incidents},
            },
            "foreign_keys": _FOREIGN_KEYS,
            "faulty_sql": _FAULTY_SQL,
            "correct_sql": _CORRECT_SQL,
            "update_sql": _UPDATE_SQL.format(incident_id=incidents[0][0]),
            "faulty_python": _FAULTY_PYTHON,
            "correct_python": _CORRECT_PYTHON,
        }
    )
