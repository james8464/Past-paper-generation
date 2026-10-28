"""Experimental V35 must replay all five families and preserve refusal."""

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
