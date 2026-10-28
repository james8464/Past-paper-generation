"""Four real whole-paper families must replay and retain originality refusal."""

from copy import deepcopy

import pytest

from Backend.Core.france.nsi import NSIExercise
from Backend.Core.france.pipeline import (
    digest,
    exercise_candidate_text,
    generate_assessment,
    validate_package,
)
from tests.test_nsi_pipeline import make_index


class NoModel:
    def generate_json(self, *args, **kwargs):
        pytest.fail("The new application-owned route must not call a model")


def generate(root, seed=270103, previous=None):
    index = root / "references.sqlite"
    if not index.exists():
        make_index(index)
    return generate_assessment(
        index_path=index,
        client=NoModel(),
        seed=seed,
        checkpoint=root / f"checkpoint-{seed}.json",
        contract_graph_tree=True,
        contract_authoring_version="v34",
        previous_texts=previous,
    )


@pytest.mark.parametrize("seed", range(270100, 270104))
def test_four_source_families_replay(tmp_path, seed):
    package = generate(tmp_path, seed)
    assert package["identity"]["prompt_version"] == "fr-nsi-written-2027-v34"
    assert package["identity"]["family"] == seed % 4
    assert validate_package(package)["structural_checks"] == "passed"
    assert package["teacher_review"] == {"state": "not_run"}
    assert package["empirical_calibration"] == {"state": "not_run"}
    assert sum(len(e["questions"]) for e in package["exercises"]) == 34
    assert all(
        c["scope"] == "canonical_question_replay"
        for e in package["evidence"]
        for c in e["deterministic"]
    )
    assert generate(tmp_path, seed) == package


def test_all_four_work_in_one_history_then_repetition_is_refused(tmp_path):
    previous = []
    for seed in range(270100, 270104):
        package = generate(tmp_path, seed, previous)
        previous.extend(
            exercise_candidate_text(NSIExercise.model_validate(e))
            for e in package["exercises"]
        )
    with pytest.raises(ValueError, match=r"[Ss]imilar|[Oo]riginal|précédent"):
        generate(tmp_path, 270104, previous)


@pytest.mark.parametrize("field", ["prompt", "answer", "marking", "verification"])
def test_rehashed_question_changes_are_not_accepted(tmp_path, field):
    original = generate(tmp_path)
    for position in range(3):
        changed = deepcopy(original)
        changed["exercises"][position]["questions"][0][field] = "changed"
        changed["content_sha256"] = digest(changed["exercises"])
        changed["evidence"][position]["exercise_sha256"] = digest(
            changed["exercises"][position]
        )
        with pytest.raises(ValueError):
            validate_package(changed)


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", "approved"),
        ("teacher_review", {"state": "passed"}),
        ("empirical_calibration", {"state": "passed"}),
        ("extra", True),
    ],
)
def test_approval_and_unknown_package_fields_cannot_be_forged(tmp_path, field, value):
    package = generate(tmp_path)
    package[field] = value
    with pytest.raises(ValueError):
        validate_package(package)


@pytest.mark.parametrize("seed", [-(2**63), -(2**63) + 1, 2**63 - 2, 2**63 - 1])
def test_signed_seed_boundaries_keep_private_case_seed_in_range(seed):
    from Backend.Core.france.extended_pipeline import _source

    family, source_seed, exercises = _source(seed)
    assert family == seed % 4
    assert -(2**63) <= source_seed < 2**63
    assert len(exercises) == 3


@pytest.mark.parametrize(
    "offset,expected",
    [
        (0, ("rank", "sensors", "routing")),
        (1, ("expression", "bookings", "locks")),
        (2, ("prefix", "stock", "delivery")),
    ],
)
def test_retained_family_names_match_their_source_selection(offset, expected):
    from Backend.Core.france import (
        database_case_families,
        system_case_families,
        tree_case_families,
    )
    from Backend.Core.france.extended_pipeline import _source

    _, source_seed, _ = _source(270100 + offset)
    assert (
        tuple(
            module.build_case(source_seed)["family"]
            for module in (
                tree_case_families,
                database_case_families,
                system_case_families,
            )
        )
        == expected
    )


@pytest.mark.parametrize(
    "failures",
    [
        None,
        {},
        [None],
        [{}],
        [{"error": 1, "cancelled": False}],
        [{"error": "cancelled", "cancelled": 1}],
    ],
)
def test_corrupt_checkpoint_history_is_not_overwritten(tmp_path, failures):
    import json

    generate(tmp_path)
    path = tmp_path / "checkpoint-270103.json"
    state = json.loads(path.read_text())
    state["failures"] = failures
    original = json.dumps(state)
    path.write_text(original)
    with pytest.raises(ValueError, match="checkpoint"):
        generate(tmp_path)
    assert path.read_text() == original


@pytest.mark.parametrize("seed", range(270100, 270104))
@pytest.mark.parametrize("correction", [False, True])
@pytest.mark.parametrize("large_print", [False, True])
def test_all_four_families_have_complete_printed_content(
    tmp_path, seed, correction, large_print
):
    from Backend.Core.france.whole_case_pdf import validate_whole_case_pdf
    from tests.test_french_whole_case_pdf import render

    package = generate(tmp_path, seed)
    path = tmp_path / "paper.pdf"
    render(path, package, correction, large_print)
    validate_whole_case_pdf(path, package, correction=correction)


@pytest.mark.parametrize("exercise,source", [("2", "Atlas"), ("3", "Durée CPU")])
def test_enlarged_new_correction_keeps_source_table_with_introduction(
    tmp_path, exercise, source
):
    import pymupdf

    from tests.test_french_whole_case_pdf import render

    package = generate(tmp_path)
    path = tmp_path / "loan-correction.pdf"
    render(path, package, True, large_print=True)
    with pymupdf.open(path) as pdf:
        introduction = [
            page for page in pdf if page.search_for(f"Exercice {exercise} (6 points)")
        ]
        assert len(introduction) == 1
        # A case heading alone gives the reader no data to work with.
        assert source in introduction[0].get_text()


def test_v34_correction_replaces_only_blank_code_with_subject_reference():
    from Backend.Core.france.rendering import correction_prompt

    prompt = (
        "Compléter A.\n```python\nreturn __A__\n```\n"
        "Corriger aussi ce programme :\n```python\nreturn 1 / 0\n```"
    )
    printed = correction_prompt(prompt)
    assert "return __A__" not in printed
    assert "return 1 / 0" in printed
    assert "Compléter A." in printed
    assert "Le code à compléter figure dans le sujet." in printed


def test_v34_correction_keeps_filled_code_and_subject_keeps_blanks(tmp_path):
    import pymupdf

    from tests.test_french_whole_case_pdf import render

    package = generate(tmp_path)
    subject, correction = tmp_path / "subject.pdf", tmp_path / "correction.pdf"
    render(subject, package, False, large_print=True)
    render(correction, package, True, large_print=True)
    with pymupdf.open(subject) as pdf:
        assert "__A__" in "".join(page.get_text() for page in pdf)
    with pymupdf.open(correction) as pdf:
        text = "".join(page.get_text() for page in pdf)
        assert "return pile[0]" in text
        assert "pile.append(__A__)" not in text


def test_compact_correction_has_no_footer_only_page_between_exercises(tmp_path):
    import pymupdf

    from tests.test_french_whole_case_pdf import render

    package = generate(tmp_path, seed=270100)
    path = tmp_path / "no-blank-page.pdf"
    render(path, package, True)
    with pymupdf.open(path) as pdf:
        for page in pdf:
            body = page.get_text(clip=pymupdf.Rect(0, 0, page.rect.width, 760))
            assert body.strip(), f"Content-empty page {page.number + 1}"
