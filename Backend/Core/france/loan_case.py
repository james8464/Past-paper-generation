"""Finite loan intervals with separate Python and fixed-SQL availability checks.

An interval contains its start but not its return time. None means a loan has
not been returned. These sources belong to one new family, not unlimited variety.
"""

import sqlite3

AVAILABILITY_QUERY = """SELECT e.code
FROM exemplaire AS e
LEFT JOIN emprunt AS p
 ON p.exemplaire = e.code
 AND p.debut <= ?
 AND (p.retour IS NULL OR p.retour > ?)
WHERE p.id IS NULL
ORDER BY e.code"""
ACTIVE_LOANS_QUERY = """SELECT e.code, e.titre, p.id
FROM exemplaire AS e
JOIN emprunt AS p
 ON p.exemplaire = e.code
WHERE p.debut <= ?
 AND (p.retour IS NULL OR p.retour > ?)
ORDER BY e.code, p.id"""


def _validate(copies, loans):
    if type(copies) not in (list, tuple) or not 1 <= len(copies) <= 32:
        raise ValueError("Between one and 32 copies are required")
    identifiers = set()
    for row in copies:
        if (
            type(row) not in (list, tuple)
            or len(row) != 2
            or type(row[0]) is not int
            or row[0] < 1
            or row[0] in identifiers
            or type(row[1]) is not str
            or not row[1].strip()
            or len(row[1]) > 100
        ):
            raise ValueError("Invalid copy")
        identifiers.add(row[0])
    if type(loans) not in (list, tuple) or len(loans) > 64:
        raise ValueError("At most 64 loans are supported")
    seen = set()
    for row in loans:
        if type(row) not in (list, tuple) or len(row) != 5:
            raise ValueError("A loan needs five fields")
        identifier, copy, borrower, start, end = row
        if (
            type(identifier) is not int
            or identifier < 1
            or identifier in seen
            or type(copy) is not int
            or copy not in identifiers
            or type(borrower) is not str
            or not borrower.strip()
            or len(borrower) > 100
            or type(start) is not int
            or not 0 <= start <= 100
            or (end is not None and (type(end) is not int or not start < end <= 100))
        ):
            raise ValueError("Invalid loan")
        seen.add(identifier)


def _time(time):
    if type(time) is not int or not 0 <= time <= 100:
        raise ValueError("Snapshot time must be an integer from zero to 100")


def available(copies, loans, time):
    """Set-based availability; order and previous returned loans do not matter."""
    _validate(copies, loans)
    _time(time)
    occupied = {
        copy
        for _, copy, _, start, end in loans
        if start <= time and (end is None or time < end)
    }
    return sorted(code for code, _ in copies if code not in occupied)


def sql_available(copies, loans, time):
    """Run only the fixed application query; never accept a candidate SQL string."""
    _validate(copies, loans)
    _time(time)
    with sqlite3.connect(":memory:") as database:
        database.execute("PRAGMA foreign_keys = ON")
        database.executescript(
            "CREATE TABLE exemplaire (code INTEGER PRIMARY KEY, titre TEXT NOT NULL);"
            "CREATE TABLE emprunt (id INTEGER PRIMARY KEY, exemplaire INTEGER NOT NULL "
            "REFERENCES exemplaire(code), lecteur TEXT NOT NULL, debut INTEGER NOT NULL, retour INTEGER);"
        )
        database.executemany("INSERT INTO exemplaire VALUES (?, ?)", copies)
        database.executemany("INSERT INTO emprunt VALUES (?, ?, ?, ?, ?)", loans)
        return [row[0] for row in database.execute(AVAILABILITY_QUERY, (time, time))]


def overlaps(loans):
    """Find all overlapping pairs independently, including nested intervals."""
    if type(loans) not in (list, tuple):
        raise ValueError("Loans must be a finite sequence")
    # Reuse the field checks without requiring an external copy catalogue.
    try:
        copies = [[code, "Copy"] for code in sorted({row[1] for row in loans})]
    except (TypeError, IndexError) as error:
        raise ValueError("Malformed loans") from error
    if not loans:
        return []
    _validate(copies, loans)
    pairs = []
    for index, left in enumerate(loans):
        for right in loans[index + 1 :]:
            left_end = 101 if left[4] is None else left[4]
            right_end = 101 if right[4] is None else right[4]
            if left[1] == right[1] and max(left[3], right[3]) < min(
                left_end, right_end
            ):
                pairs.append(sorted((left[0], right[0])))
    return sorted(pairs)


def build_case(seed):
    if type(seed) is not int or not -(2**63) <= seed < 2**63:
        raise ValueError("A signed 64-bit integer seed is required")
    return {
        "family": "loan_intervals",
        "copies": [[10, "Atlas"], [11, "Atlas"], [20, "Boreal"], [30, "Cirrus"]],
        "loans": [
            [101, 10, "Lea", 0, 4],
            [102, 10, "Noe", 4, None],
            [103, 11, "Lea", 1, 6],
            [104, 20, "Ines", 3, 5],
        ],
        "revised_loans": [
            [101, 10, "Lea", 0, 4],
            [102, 10, "Noe", 4, None],
            [103, 11, "Lea", 1, 5],
            [104, 20, "Ines", 3, 5],
            [105, 11, "Eli", 5, None],
        ],
    }
