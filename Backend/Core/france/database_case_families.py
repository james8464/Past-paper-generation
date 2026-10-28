# V32 relational cases with separate public sources and private oracles; only fixed app
# SQL runs. Never execute model SQL/code

import json
import sqlite3
from copy import deepcopy
from hashlib import sha256

VERSION = "fr-nsi-database-cases-v1"
FAMILIES = ("sensors", "bookings", "stock")


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _table(name, columns, rows):
    return {"name": name, "columns": columns, "rows": rows}


# single pass over (sensor, temperature, valid); unknown IDs are invalid inputs
#
# Sensor IDs are unique. None represents no valid observation, not zero degrees
# Inputs are not mutated; observations may be a one-shot iterator
def sensor_extrema(sensor_ids, observations):
    result = dict.fromkeys(sensor_ids)
    for sensor, value, valid in observations:
        if valid:
            bounds = result[sensor]
            if bounds is None:
                result[sensor] = (value, value)
            else:
                low, high = bounds
                result[sensor] = (
                    min(low, value),
                    max(high, value),
                )
    return result


# subtract confirmed group sizes; negative availability remains an alert
#
# Reservations are (session, positive seats, confirmed), with known session IDs
def remaining_places(capacities, reservations):
    result = capacities.copy()
    for session, seats, valid in reservations:
        if valid:
            result[session] -= seats
    return result


# return first failing movement ID, not final balance or list position
#
# Precondition: initial >= 0; (ID, signed delta) rows already chronologically
# ordered for one article. A balance of exactly zero is permitted
def first_stock_deficit(initial, movements):
    balance = initial
    for identifier, delta in movements:
        balance += delta
        if balance < 0:
            return identifier
    return None


def _check_algorithm(family, public, expected):
    parents, events = (table["rows"] for table in public["tables"])
    if family == "sensors":
        bounds = sensor_extrema(
            [row[0] for row in parents],
            ((row[1], row[3], row[4] == 1) for row in events),
        )
        result = [
            [key, *(value if value is not None else (None, None))]
            for key, value in bounds.items()
        ]
        matches = result == expected["result"]
    elif family == "bookings":
        remaining = remaining_places(
            {row[0]: row[2] for row in parents},
            ((row[1], row[2], row[3] == 1) for row in events),
        )
        matches = [list(pair) for pair in remaining.items()] == expected["result"]
    else:
        initial = next(row[2] for row in parents if row[0] == 1)
        ordered = sorted((row for row in events if row[1] == 1), key=lambda row: row[2])
        matches = (
            first_stock_deficit(initial, ((row[0], row[3]) for row in ordered))
            == expected["first_invalid"]
        )
    if not matches:
        raise ValueError("Algorithm and independent case evidence disagree")


def _source(family, seed):
    if family == "sensors":
        offset = seed % 5
        return {
            "title": "Des mesures brutes au bilan des capteurs",
            "context": (
                "Une serre conserve chaque relevé, même lorsqu'un contrôle le déclare "
                "invalide. Un bilan doit utiliser uniquement les lignes dont valide vaut 1, "
                "sans effacer les mesures brutes. Les instants sont des minutes depuis "
                "l'ouverture ; les températures sont des entiers en degrés Celsius. "
                "Un capteur sans observation exploitable doit rester visible dans le bilan."
            ),
            "schema": (
                "capteur : id entier, clé primaire ; zone texte. "
                "releve : id entier, clé primaire ; capteur entier, clé étrangère vers "
                "capteur.id ; minute entier positif ou nul ; temperature entier ; "
                "valide entier égal à 0 ou 1. Le couple (capteur, minute) est unique."
            ),
            "tables": [
                _table(
                    "capteur",
                    ["id", "zone"],
                    [[1, "Serre"], [2, "Bassin"], [3, "Atelier"]],
                ),
                _table(
                    "releve",
                    ["id", "capteur", "minute", "temperature", "valide"],
                    [
                        [11, 1, 0, 18 + offset, 1],
                        [12, 1, 10, 24 + offset, 1],
                        [13, 1, 20, 99, 0],
                        [14, 2, 0, 12 + offset, 1],
                        [15, 2, 10, 16 + offset, 1],
                    ],
                ),
            ],
        }
    if family == "bookings":
        return {
            "title": "Réservations confirmées et capacité d'une séance",
            "context": (
                "Un festival reçoit des réservations de groupes. Une ligne représente "
                "un groupe, pas une personne. Seules les réservations confirmées occupent "
                "des places ; les demandes en attente sont conservées séparément par le "
                "drapeau confirmee. Le rapport doit signaler un dépassement de capacité "
                "plutôt que remplacer une disponibilité négative par zéro."
            ),
            "schema": (
                "seance : numero entier, clé primaire ; film texte ; capacite entier "
                "strictement positif. reservation : code entier, clé primaire ; seance "
                "entier, clé étrangère vers seance.numero ; places entier strictement "
                "positif ; confirmee entier égal à 0 ou 1."
            ),
            "tables": [
                _table(
                    "seance",
                    ["numero", "film", "capacite"],
                    [[1, "Atlas", 4], [2, "Boreal", 3], [3, "Cirrus", 5]],
                ),
                _table(
                    "reservation",
                    ["code", "seance", "places", "confirmee"],
                    [[11, 1, 2, 1], [12, 1, 3, 1], [13, 2, 2, 0], [14, 2, 1, 1]],
                ),
            ],
        }
    initial = 6 + seed % 3
    return {
        "title": "Audit chronologique des mouvements de matériel",
        "context": (
            "Un atelier journalise les entrées et les sorties de matériel. Chaque "
            "variation est signée : une entrée est positive, une sortie négative. "
            "Le stock initial est celui d'avant le premier mouvement. L'audit cherche "
            "le premier mouvement qui ferait passer le stock sous zéro ; le bilan "
            "de fin de journée ne suffit pas à vérifier tous les états intermédiaires."
        ),
        "schema": (
            "article : reference entier, clé primaire ; designation texte ; initial "
            "entier positif ou nul. mouvement : numero entier, clé primaire ; article "
            "entier, clé étrangère vers article.reference ; instant entier positif ou nul ; "
            "delta entier non nul. Pour un même article, deux instants sont distincts."
        ),
        "tables": [
            _table(
                "article",
                ["reference", "designation", "initial"],
                [[1, "Lentille", initial], [2, "Pied", 3], [3, "Cable", 10]],
            ),
            _table(
                "mouvement",
                ["numero", "article", "instant", "delta"],
                [
                    [11, 1, 1, -(initial + 2)],
                    [12, 1, 2, 4],
                    [13, 2, 1, -1],
                    [14, 2, 3, 2],
                    [15, 3, 1, -4],
                ],
            ),
        ],
    }


_SCHEMAS = {
    "sensors": """
        CREATE TABLE capteur(id INTEGER PRIMARY KEY, zone TEXT NOT NULL);
        CREATE TABLE releve(id INTEGER PRIMARY KEY,
          capteur INTEGER NOT NULL REFERENCES capteur(id),
          minute INTEGER NOT NULL CHECK(minute >= 0),
          temperature INTEGER NOT NULL,
          valide INTEGER NOT NULL CHECK(valide IN (0,1)), UNIQUE(capteur, minute));
    """,
    "bookings": """
        CREATE TABLE seance(numero INTEGER PRIMARY KEY, film TEXT NOT NULL,
          capacite INTEGER NOT NULL CHECK(capacite > 0));
        CREATE TABLE reservation(code INTEGER PRIMARY KEY,
          seance INTEGER NOT NULL REFERENCES seance(numero),
          places INTEGER NOT NULL CHECK(places > 0),
          confirmee INTEGER NOT NULL CHECK(confirmee IN (0,1)));
    """,
    "stock": """
        CREATE TABLE article(reference INTEGER PRIMARY KEY, designation TEXT NOT NULL,
          initial INTEGER NOT NULL CHECK(initial >= 0));
        CREATE TABLE mouvement(numero INTEGER PRIMARY KEY,
          article INTEGER NOT NULL REFERENCES article(reference),
          instant INTEGER NOT NULL CHECK(instant >= 0),
          delta INTEGER NOT NULL CHECK(delta != 0), UNIQUE(article, instant));
    """,
}

_QUERIES = {
    "sensors": """SELECT c.id, MIN(r.temperature), MAX(r.temperature)
        FROM capteur c LEFT JOIN releve r ON r.capteur=c.id AND r.valide=1
        GROUP BY c.id ORDER BY c.id""",
    "bookings": """SELECT s.numero, s.capacite-COALESCE(SUM(r.places),0)
        FROM seance s LEFT JOIN reservation r ON r.seance=s.numero AND r.confirmee=1
        GROUP BY s.numero, s.capacite ORDER BY s.numero""",
    "stock": """SELECT a.reference, a.initial+COALESCE(SUM(m.delta),0)
        FROM article a LEFT JOIN mouvement m ON m.article=a.reference
        GROUP BY a.reference, a.initial ORDER BY a.reference""",
}

_BAD_INSERTS = {
    "sensors": "INSERT INTO releve VALUES (99,999,30,20,1)",
    "bookings": "INSERT INTO reservation VALUES (99,999,1,1)",
    "stock": "INSERT INTO mouvement VALUES (99,999,30,1)",
}


# fixed application-owned actions, used in the correction and SQL oracle
def linked_sql(family, public):
    if family == "sensors":
        corrected = public["tables"][1]["rows"][0][3] + 3
        return [
            "UPDATE releve SET valide=0\nWHERE id=12;",
            f"UPDATE releve\nSET temperature={corrected}, valide=1\nWHERE id=13;",
        ]
    if family == "bookings":
        return [
            "UPDATE reservation SET seance=3\nWHERE code=12;",
            "UPDATE reservation SET confirmee=1\nWHERE code=13;",
            "UPDATE reservation SET confirmee=0\nWHERE code=14;",
        ]
    if family == "stock":
        return [
            "UPDATE mouvement SET instant=0\nWHERE numero=12;",
            "INSERT INTO mouvement\nVALUES (16,1,3,-3);",
            "INSERT INTO mouvement\nVALUES (17,1,4,5);",
        ]
    raise ValueError("Unknown database case family")


# transform lists directly, independently of SQL statement interpretation
def _independent_states(family, public):
    current = deepcopy(public)
    states = [deepcopy(current)]
    rows = current["tables"][1]["rows"]
    if family == "sensors":
        next(row for row in rows if row[0] == 12)[4] = 0
        states.append(deepcopy(current))
        corrected = next(row for row in rows if row[0] == 11)[3] + 3
        row = next(row for row in rows if row[0] == 13)
        row[3], row[4] = corrected, 1
        states.append(deepcopy(current))
    elif family == "bookings":
        for identifier, column, value in ((12, 1, 3), (13, 3, 1), (14, 3, 0)):
            next(row for row in rows if row[0] == identifier)[column] = value
            states.append(deepcopy(current))
    elif family == "stock":
        next(row for row in rows if row[0] == 12)[2] = 0
        states.append(deepcopy(current))
        for movement in ([16, 1, 3, -3], [17, 1, 4, 5]):
            rows.append(movement)
            states.append(deepcopy(current))
    else:
        raise ValueError("Unknown database case family")
    return states


def _state_evidence(connection, family, public):
    states = _independent_states(family, public)
    statements = linked_sql(family, public)
    evidence = []
    connection.execute("SAVEPOINT linked_states")
    try:
        for index, state in enumerate(states):
            if index:
                cursor = connection.execute(statements[index - 1])
                if cursor.rowcount != 1:
                    raise ValueError("Linked action must affect exactly one row")
            expected = _independent(family, state)
            _check_algorithm(family, state, expected)
            rows = [list(row) for row in connection.execute(_QUERIES[family])]
            if rows != expected["result"]:
                raise ValueError("Linked SQL and independent state disagree")
            # check the entire source, not only aggregate totals that could hide
            # a wrong row mutation or a chronology error
            for table in state["tables"]:
                actual = [
                    list(row)
                    for row in connection.execute(
                        f"SELECT * FROM {table['name']} ORDER BY 1"
                    )
                ]
                if actual != sorted(table["rows"], key=lambda row: row[0]):
                    raise ValueError("Linked SQL changed the wrong source rows")
            evidence.append({"name": f"S{index}", **expected})
    finally:
        connection.execute("ROLLBACK TO linked_states")
        connection.execute("RELEASE linked_states")
    return evidence


def _independent(family, public):
    parents, events = (table["rows"] for table in public["tables"])
    if family == "sensors":
        result = []
        for key, _zone in parents:
            values = [r[3] for r in events if r[1] == key and r[4] == 1]
            result.append(
                [key, min(values) if values else None, max(values) if values else None]
            )
        return {"result": result}
    if family == "bookings":
        result = [
            [key, capacity - sum(r[2] for r in events if r[1] == key and r[3] == 1)]
            for key, _film, capacity in parents
        ]
        return {
            "result": result,
            "overbooked": [key for key, free in result if free < 0],
        }
    result = [
        [key, initial + sum(r[3] for r in events if r[1] == key)]
        for key, _label, initial in parents
    ]
    # independent prefix-sum oracle for article 1. The candidate algorithm will
    # scan incrementally; this oracle sums each prefix afresh
    selected = sorted((r for r in events if r[1] == 1), key=lambda r: r[2])
    initial = next(r[2] for r in parents if r[0] == 1)
    prefixes = [
        [row[0], initial + sum(r[3] for r in selected[: i + 1])]
        for i, row in enumerate(selected)
    ]
    return {
        "result": result,
        "prefix_balances": prefixes,
        "first_invalid": next((key for key, value in prefixes if value < 0), None),
    }


def _evidence(family, public):
    expected = _independent(family, public)
    _check_algorithm(family, public, expected)
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.executescript(_SCHEMAS[family])
        for table in public["tables"]:
            placeholders = ",".join("?" for _ in table["columns"])
            connection.executemany(
                f"INSERT INTO {table['name']} VALUES ({placeholders})", table["rows"]
            )
        rows = [list(row) for row in connection.execute(_QUERIES[family])]
        if rows != expected["result"]:
            raise ValueError("SQL and independent case evidence disagree")
        if family == "stock":
            prefixes = [
                list(row)
                for row in connection.execute("""
                SELECT m.numero, a.initial + (
                  SELECT SUM(p.delta) FROM mouvement p
                  WHERE p.article=m.article AND p.instant<=m.instant)
                FROM mouvement m JOIN article a ON a.reference=m.article
                WHERE m.article=1 ORDER BY m.instant
            """)
            ]
            if prefixes != expected["prefix_balances"]:
                raise ValueError("Chronological SQL and independent prefixes disagree")
        connection.execute("SAVEPOINT invalid_foreign_key")
        rejected = False
        try:
            connection.execute(_BAD_INSERTS[family])
        except sqlite3.IntegrityError:
            rejected = True
        finally:
            connection.execute("ROLLBACK TO invalid_foreign_key")
            connection.execute("RELEASE invalid_foreign_key")
        if not rejected:
            raise ValueError("Foreign-key case was not rejected")
        return {
            **expected,
            "foreign_key_rejected": rejected,
            "sql_matches_independent": True,
            "algorithm_matches_independent": True,
            "states": _state_evidence(connection, family, public),
            "states_sql_matches_independent": True,
            "states_algorithm_matches_independent": True,
        }
    finally:
        connection.close()


def build_case(seed):
    if type(seed) is not int:
        raise ValueError("Whole-case seed must be an integer")
    family = FAMILIES[(seed - 270100) % 3]
    public = _source(family, seed)
    payload = {
        "version": VERSION,
        "seed": seed,
        "family": family,
        "public": public,
        "expected": _evidence(family, public),
    }
    return {**payload, "sha256": sha256(_canonical(payload).encode()).hexdigest()}


def verify_case(case):
    try:
        return _canonical(case) == _canonical(build_case(case["seed"]))
    except (KeyError, TypeError, ValueError):
        return False
