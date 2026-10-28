"""Experimental V35 must replay all five families and preserve refusal."""

import json
from copy import deepcopy

import pytest

from Backend.Core.france.nsi import NSIExercise
from Backend.Core.france.pipeline import digest, exercise_candidate_text
from tests.test_nsi_pipeline import make_index


def generate(root, seed=270104, history=None):
    from Backend.Core.france.expanded_pipeline import generate

    index = root / "references.sqlite"
    if not index.exists():
        make_index(index)
    return generate(
        index_path=index,
        seed=seed,
        checkpoint=root / f"checkpoint-{seed}.json",
        previous_texts=history,
    )


@pytest.mark.parametrize("seed", range(270100, 270105))
def test_five_complete_packages_replay(tmp_path, seed):
    from Backend.Core.france.expanded_pipeline import validate

    package = generate(tmp_path, seed)
    assert package["identity"]["prompt_version"] == "fr-nsi-written-2027-v35"
    assert package["identity"]["family"] == seed % 5
    assert package["identity"]["model"] == "app-owned-v35"
    assert package["identity"]["print_policy"] == "fr-nsi-v35-internal-review-v1"
    assert validate(package)["structural_checks"] == "passed"
    assert package["teacher_review"] == {"state": "not_run"}
    assert package["empirical_calibration"] == {"state": "not_run"}
    assert sum(len(e["questions"]) for e in package["exercises"]) == (
        36 if seed == 270104 else 34
    )
    assert generate(tmp_path, seed) == package


def test_repeated_preference_selects_five_families_then_refuses_without_writes(
    tmp_path,
):
    from Backend.Core.france.expanded_pipeline import (
        FamilyCatalogueExhausted,
        choose_fresh_seed,
    )

    history, selected = [], []
    for _ in range(5):
        seed = choose_fresh_seed(270100, previous_texts=history)
        selected.append(seed)
        package = generate(tmp_path, seed, history)
        history.extend(
            exercise_candidate_text(NSIExercise.model_validate(e))
            for e in package["exercises"]
        )
    assert selected == list(range(270100, 270105))
    before = {
        path.name: path.read_bytes() for path in tmp_path.iterdir() if path.is_file()
    }
    with pytest.raises(FamilyCatalogueExhausted):
        choose_fresh_seed(270100, previous_texts=history)
    assert {
        path.name: path.read_bytes() for path in tmp_path.iterdir() if path.is_file()
    } == before
    assert len(history) == 15


@pytest.mark.parametrize("seed", [-(2**63), -(2**63) + 1, 2**63 - 2, 2**63 - 1])
def test_boundary_selection_visits_each_family_once(seed):
    from Backend.Core.france.expanded_pipeline import _family_seeds

    candidates = _family_seeds(seed)
    assert candidates[0] == seed
    assert len(candidates) == 5
    assert {value % 5 for value in candidates} == set(range(5))
    assert all(-(2**63) <= value < 2**63 for value in candidates)


@pytest.mark.parametrize("field", ["prompt", "answer", "marking", "verification"])
def test_rehashed_changes_to_any_exercise_are_rejected(tmp_path, field):
    from Backend.Core.france.expanded_pipeline import validate

    original = generate(tmp_path)
    for position in range(3):
        changed = deepcopy(original)
        changed["exercises"][position]["questions"][0][field] = "changed"
        changed["content_sha256"] = digest(changed["exercises"])
        changed["evidence"][position]["exercise_sha256"] = digest(
            changed["exercises"][position]
        )
        with pytest.raises(ValueError):
            validate(changed)


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", "approved"),
        ("teacher_review", {"state": "passed"}),
        ("empirical_calibration", {"state": "passed"}),
        ("extra", True),
    ],
)
def test_approval_and_unknown_fields_remain_refused(tmp_path, field, value):
    from Backend.Core.france.expanded_pipeline import validate

    package = generate(tmp_path)
    package[field] = value
    with pytest.raises(ValueError):
        validate(package)


@pytest.mark.parametrize("seed", range(270100, 270104))
def test_retained_exercises_are_not_rewritten_by_the_new_version(seed):
    from Backend.Core.france.expanded_pipeline import _source
    from Backend.Core.france.extended_pipeline import _source as retained_source

    assert _source(seed)[1:] == retained_source(seed)[1:]


@pytest.mark.parametrize("seed", [True, 1.5, "270104", -(2**63) - 1, 2**63])
def test_selection_refuses_invalid_seed_without_writing(seed):
    from Backend.Core.france.expanded_pipeline import choose_fresh_seed

    with pytest.raises(ValueError):
        choose_fresh_seed(seed)


@pytest.mark.parametrize("history", ["text", [""], [False], ["x" * 100001], ["x"] * 21])
def test_selection_refuses_invalid_history(history):
    from Backend.Core.france.expanded_pipeline import choose_fresh_seed

    with pytest.raises(ValueError):
        choose_fresh_seed(270104, previous_texts=history)


def test_checkpoint_with_forged_request_does_not_get_overwritten(tmp_path):
    generate(tmp_path)
    path = tmp_path / "checkpoint-270104.json"
    state = json.loads(path.read_text())
    state["request"]["history"] = "forged"
    path.write_text(json.dumps(state))
    before = path.read_bytes()
    with pytest.raises(ValueError, match="checkpoint identity"):
        generate(tmp_path)
    assert path.read_bytes() == before


def test_forged_print_policy_cannot_replay(tmp_path):
    from Backend.Core.france.expanded_pipeline import validate

    package = generate(tmp_path)
    package["identity"]["print_policy"] = "fr-nsi-v34-internal-review-v1"
    with pytest.raises(ValueError):
        validate(package)


def test_v35_runtime_dispatch_does_not_use_an_older_validator():
    from Backend.Core.france.runtime import (
        database_pdf_contract_version,
        network_pdf_contract_version,
    )

    assert database_pdf_contract_version("fr-nsi-written-2027-v35") == "v35"
    assert network_pdf_contract_version("fr-nsi-written-2027-v35") == "v35"
    assert database_pdf_contract_version("fr-nsi-written-2027-v34") == "v34"
    assert network_pdf_contract_version("fr-nsi-written-2027-v34") == "v34"
