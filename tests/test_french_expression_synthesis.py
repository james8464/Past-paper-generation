"""Structural variety must be real, reproducible and independently checkable."""

from copy import deepcopy

import pytest

from Backend.Core.france.expression_synthesis import build_case, verify_case


def test_synthesis_changes_structure_not_only_leaf_numbers():
    cases = [build_case(seed) for seed in range(100)]
    shapes = {
        tuple((row[0], row[2], row[3]) for row in case["public"]["rows"])
        for case in cases
    }
    assert len(shapes) >= 30
    assert len({case["sha256"] for case in cases}) == 100
    for case in cases:
        assert case == build_case(case["seed"])
        assert verify_case(case)
        states = case["expected"]["states"]
        assert len(states) == 3
        assert all(state["independent_matches"] for state in states)
        assert states[0]["values"]["n0"] != states[1]["values"]["n0"]
        assert states[1]["values"]["n0"] != states[2]["values"]["n0"]
        assert all(
            abs(value) <= 10000
            for state in states
            for value in state["values"].values()
        )


def test_linked_changes_preserve_shape_and_accumulate():
    case = build_case(270103)
    rows = {row[0]: row[1:] for row in case["public"]["rows"]}
    first, second = case["public"]["changes"]
    assert rows[first["node"]][1:] == [None, None]
    assert rows[second["node"]][1] is not None
    assert first["node"] in case["expected"]["invalidated"]
    assert "n0" in case["expected"]["invalidated"]
    states = case["expected"]["states"]
    assert states[1]["values"][first["node"]] == first["value"]
    assert states[2]["values"][first["node"]] == first["value"]
    assert states[0]["values"][first["node"]] != first["value"]


@pytest.mark.parametrize("seed", [True, False, None, "1", 1.0, 2**63, -(2**63) - 1])
def test_rejects_invalid_seed(seed):
    with pytest.raises(ValueError):
        build_case(seed)


def test_verifier_recomputes_instead_of_trusting_evidence():
    case = build_case(-42)
    for field in ("public", "expected", "sha256"):
        forged = deepcopy(case)
        forged[field] = None
        assert not verify_case(forged)
    assert not verify_case([])
    assert not verify_case({})


def test_rehashed_wrong_answer_is_rejected():
    import json
    from hashlib import sha256

    case = build_case(27)
    case["expected"]["states"][1]["answer"] += 1
    case.pop("sha256")
    case["sha256"] = sha256(
        json.dumps(
            case, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()
    assert not verify_case(case)


def test_synthesis_preserves_v32_cases():
    from Backend.Core.france.tree_case_families import build_case as legacy_case

    before = [legacy_case(seed) for seed in range(270100, 270103)]
    for seed in range(-1000, 1000):
        build_case(seed)
    assert before == [legacy_case(seed) for seed in range(270100, 270103)]
