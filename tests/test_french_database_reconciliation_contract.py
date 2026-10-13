"""V24's database and algorithm results are app-owned, not model answers."""

from __future__ import annotations

import copy
import importlib

import pytest


def _module():
    try:
        return importlib.import_module(
            "Backend.Core.france.database_reconciliation_contract"
        )
    except ModuleNotFoundError:
        pytest.fail("The V24 database reconciliation contract is not implemented")


def test_eight_rows_make_the_join_and_algorithm_defects_observable() -> None:
    data = _module().build_database_reconciliation_contract(270100).to_dict()

    assert data["version"] == 4
    assert data["task_ids"] == [f"2{letter}" for letter in "abcdefghijkl"]
    assert data["tables"]["incident"]["rows"] == [
        [101, 1, 2, "ouvert"],
        [102, 1, 3, "clos"],
        [103, 2, 1, "clos"],
        [104, 3, 2, "ouvert"],
        [105, 2, 3, "clos"],
        [106, 3, 1, "ouvert"],
        [107, 4, 4, "clos"],
        [108, 4, 4, "ouvert"],
    ]
    expected = data["expected"]
    assert expected["mismatch_ids"] == [101, 102, 103, 104, 105, 106]
    assert expected["matching_ids"] == [107, 108]
    assert expected["category_counts"] == [2, 2, 2, 2]
    assert expected["faulty_python_by_state"] == [2, 2, 2]
    assert expected["correct_python_by_state"] == [0, 1, 2]
    assert expected["closed_by_state"] == [4, 5, 6]
    assert expected["updated_ids"] == [101, 104]
    assert expected["updated_counts"] == [1, 1]
    assert expected["hypothetical_empty_category_count"] == 0
    assert expected["invalid_insert_rejected"] is True
    assert len(expected["faulty_join"]) == len(expected["correct_join"]) == 8


@pytest.mark.parametrize("seed", [0, 1, 270100, 270101])
def test_seeded_facts_round_trip_with_the_same_digest(seed: int) -> None:
    module = _module()
    contract = module.build_database_reconciliation_contract(seed)
    assert (
        module.DatabaseReconciliationContract.from_dict(contract.to_dict()).digest
        == contract.digest
    )
    assert contract.digest == module.build_database_reconciliation_contract(seed).digest


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.update(version=3),
        lambda d: d.update(seed=d["seed"] + 1),
        lambda d: d["tables"]["incident"]["rows"][0].__setitem__(3, "clos"),
        lambda d: d["tables"]["incident"]["rows"][0].__setitem__(1, 999),
        lambda d: d.update(faulty_sql="SELECT 1"),
        lambda d: d.update(faulty_python="def f(): return 2"),
        lambda d: d["expected"]["correct_python_by_state"].__setitem__(1, 2),
        lambda d: d["expected"]["mismatch_ids"].pop(),
        lambda d: d.pop("correct_sql"),
    ],
)
def test_contract_rejects_tampered_or_mixed_facts(mutate) -> None:
    module = _module()
    data = copy.deepcopy(
        module.build_database_reconciliation_contract(270100).to_dict()
    )
    mutate(data)
    with pytest.raises(ValueError):
        module.DatabaseReconciliationContract.from_dict(data)


def test_wrong_seed_type_and_exercise_fail_closed() -> None:
    module = _module()
    with pytest.raises(ValueError):
        module.build_database_reconciliation_contract(True)
    with pytest.raises(ValueError):
        module.build_database_reconciliation_contract(270100, "3")
