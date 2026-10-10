"""Immutable, app-owned incident-audit facts for French NSI V21.

The V3 source is separate from earlier database contracts so saved papers replay
against the exact facts and executable queries that originally produced them.
"""

from __future__ import annotations

import json
import random
import sqlite3
from dataclasses import dataclass
from hashlib import sha256

_TASK_IDS = [f"2{letter}" for letter in "abcdefghij"]
_COLUMNS = {
    "agent": ["id_agent", "nom", "secteur"],
    "categorie": ["id_cat", "libelle"],
    "incident": ["id_incident", "id_agent", "id_cat", "statut"],
}
_INCIDENTS = [
    [101, 1, 2, "ouvert"],
    [102, 1, 3, "clos"],
    [103, 2, 1, "clos"],
    [104, 3, 2, "ouvert"],
    [105, 2, 2, "ouvert"],
    [106, 3, 1, "ouvert"],
    [107, 4, 4, "clos"],
    [108, 4, 3, "ouvert"],
]
_FOREIGN_KEYS = [
    ["incident", "id_agent", "agent", "id_agent"],
    ["incident", "id_cat", "categorie", "id_cat"],
]
_JOIN_PREFIX = (
    "SELECT incident.id_incident, categorie.libelle\n"
    "FROM incident\nJOIN categorie ON\n    "
)
_FAULTY_SQL = (
    _JOIN_PREFIX + "incident.id_agent = categorie.id_cat\nORDER BY incident.id_incident"
)
_CORRECT_SQL = (
    _JOIN_PREFIX + "incident.id_cat = categorie.id_cat\nORDER BY incident.id_incident"
)
_GROUP_SQL = (
    "SELECT categorie.id_cat, COUNT(incident.id_incident)\n"
    "FROM categorie LEFT JOIN incident ON incident.id_cat = categorie.id_cat\n"
    "GROUP BY categorie.id_cat ORDER BY categorie.id_cat"
)
_UPDATE_SQL_1 = "UPDATE incident SET statut = 'clos' WHERE id_incident = 101"
_UPDATE_SQL_2 = "UPDATE incident SET statut = 'clos' WHERE id_incident = 105"
_FAULTY_PYTHON = (
    "def nombre_clos(incidents):\n"
    "    total = 0\n"
    "    for incident in incidents:\n"
    "        if incident['statut'] == 'ouvert':\n"
    "            total += 1\n"
    "    return total"
)
_CORRECT_PYTHON = _FAULTY_PYTHON.replace("== 'ouvert'", "== 'clos'")
_SOURCE = {
    "foreign_keys": _FOREIGN_KEYS,
    "faulty_sql": _FAULTY_SQL,
    "correct_sql": _CORRECT_SQL,
    "group_sql": _GROUP_SQL,
    "update_sql_1": _UPDATE_SQL_1,
    "update_sql_2": _UPDATE_SQL_2,
    "faulty_python": _FAULTY_PYTHON,
    "correct_python": _CORRECT_PYTHON,
}


def _tables(seed: int) -> dict:
    rng = random.Random(f"french-nsi-database-audit-v3:{seed}:2")
    names = rng.sample(["Alice", "Benoit", "Camille", "David", "Emma", "Farid"], 4)
    sectors = rng.sample(["Nord", "Sud", "Est", "Ouest", "Centre"], 4)
    labels = rng.sample(["Materiel", "Logiciel", "Reseau", "Stockage", "Acces"], 4)
    return {
        "agent": {
            "columns": _COLUMNS["agent"],
            "rows": [[i, names[i - 1], sectors[i - 1]] for i in (1, 2, 3, 4)],
        },
        "categorie": {
            "columns": _COLUMNS["categorie"],
            "rows": [[i, labels[i - 1]] for i in (1, 2, 3, 4)],
        },
        "incident": {"columns": _COLUMNS["incident"], "rows": _INCIDENTS},
    }


def _count(connection: sqlite3.Connection, status: str) -> int:
    return connection.execute(
        "SELECT COUNT(*) FROM incident WHERE statut = ?", (status,)
    ).fetchone()[0]


def _expected(tables: dict) -> dict:
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
            placeholders = ",".join("?" for _ in columns)
            connection.executemany(
                f"INSERT INTO {name} VALUES ({placeholders})", tables[name]["rows"]
            )
        faulty_join = [list(row) for row in connection.execute(_FAULTY_SQL)]
        correct_join = [list(row) for row in connection.execute(_CORRECT_SQL)]
        category_counts = [row[1] for row in connection.execute(_GROUP_SQL)]
        invalid_insert_rejected = False
        try:
            connection.execute("INSERT INTO incident VALUES (109, 999, 1, 'ouvert')")
        except sqlite3.IntegrityError:
            invalid_insert_rejected = True
        if not invalid_insert_rejected:
            raise ValueError("Foreign-key counterexample was accepted")
        closed_by_state = [_count(connection, "clos")]
        faulty_python_by_state = [_count(connection, "ouvert")]
        updated_counts = []
        for sql in (_UPDATE_SQL_1, _UPDATE_SQL_2):
            updated_counts.append(connection.execute(sql).rowcount)
            closed_by_state.append(_count(connection, "clos"))
            faulty_python_by_state.append(_count(connection, "ouvert"))
        connection.execute("INSERT INTO categorie VALUES (5, 'Hypothetique')")
        hypothetical_empty_category_count = list(connection.execute(_GROUP_SQL))[-1][1]
        if (
            len(correct_join) != 8
            or len(faulty_join) != 8
            or correct_join == faulty_join
            or category_counts != [2, 3, 2, 1]
            or closed_by_state != [3, 4, 5]
            or updated_counts != [1, 1]
            or hypothetical_empty_category_count != 0
        ):
            raise ValueError("The incident-audit counterexamples are not observable")
        return {
            "faulty_join": faulty_join,
            "correct_join": correct_join,
            "category_counts": category_counts,
            "closed_by_state": closed_by_state,
            "faulty_python_by_state": faulty_python_by_state,
            "correct_python_by_state": closed_by_state[:],
            "updated_ids": [101, 105],
            "updated_counts": updated_counts,
            "hypothetical_empty_category_count": hypothetical_empty_category_count,
            "invalid_insert_rejected": invalid_insert_rejected,
        }
    finally:
        connection.close()


@dataclass(frozen=True)
class DatabaseAuditContract:
    """Canonical JSON, including deterministic, independently checked results."""

    _json: str

    def to_dict(self) -> dict:
        return json.loads(self._json)

    @property
    def digest(self) -> str:
        return sha256(self._json.encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, data: dict) -> DatabaseAuditContract:
        required = {
            "version",
            "seed",
            "exercise_id",
            "task_ids",
            "tables",
            *_SOURCE,
        }
        if not isinstance(data, dict) or set(data) not in (
            required,
            required | {"expected"},
        ):
            raise ValueError("Invalid incident-audit contract fields")
        if (
            type(data["version"]) is not int
            or data["version"] != 3
            or type(data["seed"]) is not int
            or data["exercise_id"] != "2"
            or data["task_ids"] != _TASK_IDS
            or any(data[name] != value for name, value in _SOURCE.items())
            or data["tables"] != _tables(data["seed"])
        ):
            raise ValueError("Incident-audit facts or source identity changed")
        expected = _expected(data["tables"])
        if "expected" in data and data["expected"] != expected:
            raise ValueError("Incident-audit expected result mismatch")
        canonical = {**data, "expected": expected}
        return cls(
            json.dumps(
                canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
        )


def build_database_audit_contract(
    seed: int, exercise_id: str = "2"
) -> DatabaseAuditContract:
    if type(seed) is not int or exercise_id != "2":
        raise ValueError("Unsupported incident-audit seed or exercise")
    return DatabaseAuditContract.from_dict(
        {
            "version": 3,
            "seed": seed,
            "exercise_id": exercise_id,
            "task_ids": _TASK_IDS,
            "tables": _tables(seed),
            **_SOURCE,
        }
    )
