"""V21 incident-audit facts must be independent of model-written answers."""

from __future__ import annotations

import copy
import importlib

import pytest


def _audit_module():
    try:
        return importlib.import_module("Backend.Core.france.database_audit_contract")
    except ModuleNotFoundError:
        pytest.fail("The V21 database audit contract is not implemented")


def test_eight_incidents_and_three_states_are_locked() -> None:
    data = _audit_module().build_database_audit_contract(270100).to_dict()

    assert data["version"] == 3
    assert data["task_ids"] == [f"2{letter}" for letter in "abcdefghij"]
    assert [row[0] for row in data["tables"]["agent"]["rows"]] == [1, 2, 3, 4]
    assert [row[0] for row in data["tables"]["categorie"]["rows"]] == [1, 2, 3, 4]
    assert data["tables"]["incident"]["rows"] == [
        [101, 1, 2, "ouvert"],
        [102, 1, 3, "clos"],
        [103, 2, 1, "clos"],
        [104, 3, 2, "ouvert"],
        [105, 2, 2, "ouvert"],
        [106, 3, 1, "ouvert"],
        [107, 4, 4, "clos"],
        [108, 4, 3, "ouvert"],
    ]
    assert data["expected"]["category_counts"] == [2, 3, 2, 1]
    assert data["expected"]["closed_by_state"] == [3, 4, 5]
    assert data["expected"]["faulty_python_by_state"] == [5, 4, 3]
    assert data["expected"]["correct_python_by_state"] == [3, 4, 5]
    assert data["expected"]["updated_ids"] == [101, 105]
    assert data["expected"]["updated_counts"] == [1, 1]
    assert data["expected"]["hypothetical_empty_category_count"] == 0


def test_correct_and_faulty_join_have_observable_counterexamples() -> None:
    data = _audit_module().build_database_audit_contract(270100).to_dict()
    true_rows = {row[0]: row[1] for row in data["expected"]["correct_join"]}
    wrong_rows = {row[0]: row[1] for row in data["expected"]["faulty_join"]}
    labels = {row[0]: row[1] for row in data["tables"]["categorie"]["rows"]}

    assert len(true_rows) == len(wrong_rows) == 8
    assert [true_rows[key] for key in (101, 102, 107, 108)] == [
        labels[2],
        labels[3],
        labels[4],
        labels[3],
    ]
    assert [wrong_rows[key] for key in (101, 102, 107, 108)] == [
        labels[1],
        labels[1],
        labels[4],
        labels[4],
    ]
    assert true_rows[101] != wrong_rows[101]
    assert true_rows[108] != wrong_rows[108]


@pytest.mark.parametrize("seed", [0, 1, 270100, 270101])
def test_seeded_contract_round_trips_with_stable_digest(seed: int) -> None:
    module = _audit_module()
    contract = module.build_database_audit_contract(seed)
    assert (
        module.DatabaseAuditContract.from_dict(contract.to_dict()).digest
        == contract.digest
    )
    assert contract.digest == module.build_database_audit_contract(seed).digest


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.update(seed=d["seed"] + 1),
        lambda d: d["tables"]["incident"]["rows"][0].__setitem__(3, "clos"),
        lambda d: d["tables"]["incident"]["rows"][0].__setitem__(1, 999),
        lambda d: d.update(faulty_sql="SELECT 1"),
        lambda d: d.update(update_sql_2="UPDATE incident SET statut = 'clos'"),
        lambda d: d["expected"]["closed_by_state"].__setitem__(1, 5),
        lambda d: d["expected"]["faulty_python_by_state"].__setitem__(2, 0),
    ],
)
def test_contract_rejects_mutated_facts_or_source(mutate) -> None:
    module = _audit_module()
    data = copy.deepcopy(module.build_database_audit_contract(270100).to_dict())
    mutate(data)
    with pytest.raises(ValueError):
        module.DatabaseAuditContract.from_dict(data)


def test_non_integer_seed_and_wrong_exercise_fail_closed() -> None:
    module = _audit_module()
    with pytest.raises(ValueError):
        module.build_database_audit_contract(True)
    with pytest.raises(ValueError):
        module.build_database_audit_contract(270100, "1")
