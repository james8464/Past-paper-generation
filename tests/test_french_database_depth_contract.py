"""The richer written database case is immutable and independently checkable."""

from copy import deepcopy

import pytest

from Backend.Core.france.database_depth_contract import (
    DatabaseDepthContract,
    build_database_depth_contract,
)


def test_database_depth_case_has_ten_tasks_and_hand_checked_sql_facts():
    contract = build_database_depth_contract(270100)
    data = contract.to_dict()
    assert data["version"] == 2
    assert data["task_ids"] == [f"2{letter}" for letter in "abcdefghij"]
    assert data["tables"]["incident"]["rows"] == [
        [101, 1, 2, "ouvert"],
        [102, 1, 3, "clos"],
        [103, 2, 1, "clos"],
        [104, 3, 2, "ouvert"],
        [105, 2, 2, "ouvert"],
        [106, 3, 1, "ouvert"],
    ]
    labels = {row[0]: row[1] for row in data["tables"]["categorie"]["rows"]}
    assert data["expected"]["correct_join"] == [
        [101, labels[2]],
        [102, labels[3]],
        [103, labels[1]],
        [104, labels[2]],
        [105, labels[2]],
        [106, labels[1]],
    ]
    assert data["expected"]["category_counts"] == [
        [1, labels[1], 2],
        [2, labels[2], 3],
        [3, labels[3], 1],
    ]
    assert data["expected"]["closed_before"] == 2
    assert data["expected"]["faulty_python_count"] == 4
    assert data["expected"]["updated_ids"] == [101]
    assert data["expected"]["updated_count"] == 1
    assert data["expected"]["closed_after_update"] == 3
    assert data["expected"]["empty_closed_count"] == 0
    assert data["expected"]["faulty_join"] != data["expected"]["correct_join"]
    assert all(
        max(map(len, data[field].splitlines())) <= 46
        for field in (
            "faulty_sql",
            "correct_sql",
            "group_sql",
            "update_sql",
            "faulty_python",
            "correct_python",
        )
    )


def test_database_depth_seed_and_canonical_digest_are_stable():
    first = build_database_depth_contract(270100)
    assert first.to_dict() == build_database_depth_contract(270100).to_dict()
    assert first.digest == DatabaseDepthContract.from_dict(first.to_dict()).digest
    assert first.digest != build_database_depth_contract(270101).digest
    for seed in (0, 1, 2, 270100, 270101):
        expected = build_database_depth_contract(seed).to_dict()["expected"]
        assert expected["faulty_join"] != expected["correct_join"]
        assert expected["faulty_python_count"] != expected["closed_before"]


@pytest.mark.parametrize(
    "tamper",
    [
        lambda value: value["task_ids"].reverse(),
        lambda value: value["tables"]["incident"]["rows"].pop(),
        lambda value: value["tables"]["incident"]["rows"][0].__setitem__(1, 999),
        lambda value: value["tables"]["incident"]["rows"][0].__setitem__(1, True),
        lambda value: value.__setitem__("version", 2.0),
        lambda value: value.__setitem__("faulty_sql", "SELECT 1"),
        lambda value: value["expected"].__setitem__("closed_before", 99),
    ],
)
def test_database_depth_rejects_tampered_contract(tamper):
    value = deepcopy(build_database_depth_contract(270100).to_dict())
    tamper(value)
    with pytest.raises(ValueError):
        DatabaseDepthContract.from_dict(value)


def test_database_depth_rejects_non_integer_seed_and_wrong_exercise():
    with pytest.raises(ValueError):
        build_database_depth_contract(True)
    with pytest.raises(ValueError):
        build_database_depth_contract(270100, "1")


def test_database_depth_deterministic_verifier_rejects_changed_expected_result():
    from Backend.Core.france.verification import verify_contract

    data = build_database_depth_contract(270100).to_dict()
    claim = {
        "kind": "database_depth_contract",
        "contract": data,
        "task_id": "2f",
        "expected": data["expected"],
    }
    assert verify_contract(claim)["state"] == "passed"
    tampered = deepcopy(claim)
    tampered["expected"]["closed_before"] = 99
    assert verify_contract(tampered)["state"] == "failed"
