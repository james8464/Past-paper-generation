# Experimental structural synthesis for the next French authoring contract.
#
# Not selected by the public generator. Structural diversity is not evidence of
# original wording, calibrated demand, or educational equivalence. Publication
# still requires the complete authoring, originality and PDF gates.

import json
from copy import deepcopy
from hashlib import sha256
from itertools import pairwise
from random import Random

from Backend.Core.france.tree_case_families import _evaluate

VERSION = "fr-nsi-expression-synthesis-v2"


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _tree(random, leaves):
    rows = []

    def branch(count):
        identifier = f"n{len(rows)}"
        row = [identifier, None, None, None]
        rows.append(row)
        if count == 1:
            row[1] = random.choice([-5, -3, -2, 1, 2, 3, 4, 5, 7, 9])
        else:
            left_count = random.randrange(1, count)
            row[1] = random.choice(["+", "-", "*"])
            row[2] = branch(left_count)
            row[3] = branch(count - left_count)
        return identifier

    branch(leaves)
    return rows


def _invalidated(rows, leaf):
    parents = {
        child: identifier
        for identifier, _, left, right in rows
        for child in (left, right)
        if child is not None
    }
    path = [leaf]
    while path[-1] in parents:
        path.append(parents[path[-1]])
    return path


# Build bounded arithmetic cases with two causally effective revisions.
#
# Tree shape, operation placement, leaf data and mutation targets vary. The
# existing recursive solution is checked against bottom-up dependency
# evaluation at every state; no generated code is executed.
def build_case(seed):
    if type(seed) is not int or not -(2**63) <= seed < 2**63:
        raise ValueError("Expression synthesis requires a signed 64-bit integer seed")
    random = Random(f"{VERSION}:{seed}")
    for _ in range(128):
        rows = _tree(random, random.randrange(5, 8))
        leaves = [row for row in rows if row[2] is None]
        operators = [row for row in rows if row[2] is not None]
        leaf = random.choice(leaves)
        operator = random.choice(operators)
        changes = [
            {"node": leaf[0], "value": leaf[1] + random.choice([-4, -2, 2, 3])},
            {
                "node": operator[0],
                "value": random.choice(
                    [value for value in ("+", "-", "*") if value != operator[1]]
                ),
            },
        ]
        public = {"root": "n0", "rows": rows, "changes": changes}
        current = deepcopy(public)
        states = []
        for index in range(3):
            if index:
                change = changes[index - 1]
                next(row for row in current["rows"] if row[0] == change["node"])[1] = (
                    change["value"]
                )
            evidence = _evaluate(current, "expression")
            states.append({"id": f"S{index}", **evidence, "independent_matches": True})
        if any(
            abs(value) > 10000 for state in states for value in state["values"].values()
        ):
            continue
        if any(a["answer"] == b["answer"] for a, b in pairwise(states)):
            continue
        faulty = deepcopy(public)
        for row in faulty["rows"]:
            if row[1] == "-":
                row[2], row[3] = row[3], row[2]
        reversed_subtraction = _evaluate(faulty, "expression")
        if reversed_subtraction["answer"] == states[0]["answer"]:
            # A masked or absent fault is not a useful debugging task. Do not
            # claim this case demonstrates an error that it cannot reveal.
            continue
        if any(abs(value) > 10000 for value in reversed_subtraction["values"].values()):
            continue
        reversed_subtraction["divergent_nodes"] = sorted(
            node
            for node, value in reversed_subtraction["values"].items()
            if value != states[0]["values"][node]
        )
        case = {
            "version": VERSION,
            "seed": seed,
            "public": public,
            "expected": {
                "states": states,
                "invalidated": _invalidated(rows, leaf[0]),
                "reversed_subtraction": reversed_subtraction,
                "variations": [
                    state["answer"] - states[0]["answer"] for state in states[1:]
                ],
            },
        }
        return {**case, "sha256": sha256(_canonical(case).encode()).hexdigest()}
    raise ValueError("No bounded, causally effective expression case found")


# Reject modified source or answers even if their outer hash was replaced.
def verify_case(case):
    try:
        return isinstance(case, dict) and _canonical(case) == _canonical(
            build_case(case["seed"])
        )
    except (KeyError, TypeError, ValueError):
        return False
