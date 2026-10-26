"""Experimental V33 must use complete-content checks and exact package replay."""

from copy import deepcopy

import pytest

from Backend.Core.france.pipeline import digest, generate_assessment, validate_package
from tests.test_nsi_pipeline import make_index


class NoModel:
    def generate_json(self, *args, **kwargs):
        pytest.fail("Synthesized app-owned generation must not call a model")


def generate(tmp_path, seed=270100, **kwargs):
    index = tmp_path / "references.sqlite"
    make_index(index)
    return generate_assessment(
        index_path=index,
        client=NoModel(),
        seed=seed,
        checkpoint=tmp_path / f"checkpoint-{seed}.json",
        contract_graph_tree=True,
        contract_authoring_version="v33",
        **kwargs,
    )


@pytest.mark.parametrize("seed", range(270100, 270106))
def test_v33_full_package_replays_without_model(tmp_path, seed):
    package = generate(tmp_path, seed)
    assert validate_package(package)["structural_checks"] == "passed"
    assert package["identity"]["prompt_version"] == "fr-nsi-written-2027-v33"
    assert package["identity"]["provider"] == "application-owned"
    assert package["evidence"][0]["model_used"] is False
    assert all(
        c["scope"] == "canonical_question_replay"
        for c in package["evidence"][0]["deterministic"]
    )
    assert generate(tmp_path, seed) == package


@pytest.mark.parametrize("field", ["prompt", "answer", "marking", "verification"])
def test_rehashed_question_tampering_rejected(tmp_path, field):
    package = generate(tmp_path)
    for position in range(3):
        changed = deepcopy(package)
        changed["exercises"][position]["questions"][0][field] = "tampered"
        changed["content_sha256"] = digest(changed["exercises"])
        changed["evidence"][position]["exercise_sha256"] = digest(
            changed["exercises"][position]
        )
        with pytest.raises(ValueError):
            validate_package(changed)


def test_history_still_refuses_repeated_paper(tmp_path):
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.pipeline import exercise_candidate_text

    package = generate(tmp_path)
    previous = [
        exercise_candidate_text(NSIExercise.model_validate(e))
        for e in package["exercises"]
    ]
    with pytest.raises(ValueError):
        generate(tmp_path, previous_texts=previous)


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", "approved"),
        ("teacher_review", {"state": "passed"}),
        ("content_sha256", "0" * 64),
        ("extra", True),
    ],
)
def test_false_approval_and_extra_package_data_rejected(tmp_path, field, value):
    package = generate(tmp_path)
    package[field] = value
    with pytest.raises(ValueError):
        validate_package(package)


def test_checkpoint_cannot_substitute_another_valid_package(tmp_path):
    import json

    generate(tmp_path, 270100)
    other = generate(tmp_path, 270101)
    path = tmp_path / "checkpoint-270100.json"
    state = json.loads(path.read_text())
    state["package"] = other
    path.write_text(json.dumps(state))
    with pytest.raises(ValueError):
        generate(tmp_path, 270100)


@pytest.mark.parametrize("seed", [True, 1.2, 2**63, -(2**63) - 1])
def test_invalid_seed_rejected(tmp_path, seed):
    with pytest.raises(ValueError):
        generate(tmp_path, seed)


@pytest.mark.parametrize("seed", [270100, 270101])
@pytest.mark.parametrize("correction", [False, True])
@pytest.mark.parametrize("large_print", [False, True])
def test_v33_complete_printed_content_gate(tmp_path, seed, correction, large_print):
    from Backend.Core.france.whole_case_pdf import validate_whole_case_pdf
    from tests.test_french_whole_case_pdf import render

    package = generate(tmp_path, seed)
    path = tmp_path / "paper.pdf"
    render(path, package, correction, large_print=large_print)
    validate_whole_case_pdf(path, package, correction=correction)
    with pytest.raises(ValueError):
        validate_whole_case_pdf(path, package, correction=not correction)


@pytest.mark.parametrize("large_print", [False, True])
def test_recursive_correction_does_not_strand_introduction(tmp_path, large_print):
    import pymupdf

    from tests.test_french_whole_case_pdf import render

    package = generate(tmp_path)
    path = tmp_path / "correction.pdf"
    render(path, package, True, large_print=large_print)
    with pymupdf.open(path) as pdf:
        introduction = next(
            page.get_text()
            for page in pdf
            if "Un atelier représente" in page.get_text()
        )
    assert "Arbre initial S0" in introduction
    assert "n10" in introduction


@pytest.mark.parametrize(
    "field,value",
    [
        ("provider", "ollama"),
        ("seed", 270101),
        ("implementation_sha256", "0" * 64),
        ("synthesized_family", "postfix"),
    ],
)
def test_identity_tampering_rejected(tmp_path, field, value):
    package = generate(tmp_path)
    package["identity"][field] = value
    with pytest.raises(ValueError):
        validate_package(package)


def test_reference_categories_and_false_model_evidence_rejected(tmp_path):
    original = generate(tmp_path)
    for key, value in (("model_used", 0), ("origin", "model"), ("extra", True)):
        package = deepcopy(original)
        package["evidence"][0][key] = value
        with pytest.raises(ValueError):
            validate_package(package)
    package = deepcopy(original)
    package["evidence"][0]["references"] = [
        r for r in package["evidence"][0]["references"] if r["category"] == "programme"
    ]
    with pytest.raises(ValueError):
        validate_package(package)


def test_originality_failure_is_retained_without_retries(tmp_path):
    import json

    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.pipeline import exercise_candidate_text

    package = generate(tmp_path)
    previous = [
        exercise_candidate_text(NSIExercise.model_validate(package["exercises"][0]))
    ]
    # Same family, fresh checkpoint: screening, not checkpoint mismatch, must fail.
    with pytest.raises(ValueError):
        generate(tmp_path, 270102, previous_texts=previous)
    state = json.loads((tmp_path / "checkpoint-270102.json").read_text())
    assert state["package"] is None
    assert len(state["failures"]) == 1
    assert state["failures"][0]["error"]
