# Four real whole-paper families must replay and retain originality refusal.

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


@pytest.mark.parametrize(
    "seed,exercise",
    [
        (seed, exercise)
        for seed in range(270100, 270104)
        for exercise in range(3)
        # Postfix starts with an inline calculation, before the tree is needed.
        if (seed, exercise) != (270103, 0)
    ],
)
def test_enlarged_correction_keeps_source_table_with_introduction(
    tmp_path, seed, exercise
):
    import pymupdf

    from tests.test_french_whole_case_pdf import render

    package = generate(tmp_path, seed)
    path = tmp_path / "correction.pdf"
    render(path, package, True, large_print=True)
    with pymupdf.open(path) as pdf:
        introduction = [
            page
            for page in pdf
            if page.search_for(f"Exercice {exercise + 1} (6 points)")
        ]
        assert len(introduction) == 1
        # A case heading alone gives the reader no data to work with.
        source_title = package["exercises"][exercise]["materials"][0]["title"]
        assert " ".join(source_title.split()) in " ".join(
            introduction[0].get_text().split()
        )


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


def test_enlarged_correction_keeps_later_working_table_with_its_question(tmp_path):
    import pymupdf

    from tests.test_french_whole_case_pdf import render

    package = generate(tmp_path, seed=270100)
    path = tmp_path / "routing-correction.pdf"
    render(path, package, True, large_print=True)
    with pymupdf.open(path) as pdf:
        table_pages = [
            page for page in pdf if page.search_for("Tableau à compléter pour 3c")
        ]
        assert len(table_pages) == 1
        assert "Compléter les trois tours du tableau" in " ".join(
            table_pages[0].get_text().split()
        )


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


@pytest.mark.parametrize("correction", [False, True])
@pytest.mark.parametrize("large_print", [False, True])
def test_v34_print_policy_states_actual_review_limits(
    tmp_path, correction, large_print
):
    import pymupdf

    from tests.test_french_whole_case_pdf import render

    package = generate(tmp_path)
    assert package["identity"]["print_policy"] == "fr-nsi-v34-internal-review-v1"
    assert package["teacher_review"] == {"state": "not_run"}
    assert package["empirical_calibration"] == {"state": "not_run"}
    path = tmp_path / "review-notice.pdf"
    render(path, package, correction, large_print)
    with pymupdf.open(path) as pdf:
        cover = " ".join(pdf[0].get_text().split())
        assert "Difficulté et durée non calibrées." in cover
        assert "doit être relu par un enseignant" not in cover
        assert "à confirmer par un enseignant" not in cover
        assert "—" not in cover
        if correction:
            assert "Barème indicatif, sans validation enseignante." in cover
            assert "sans validation enseignante ni calibration auprès d'élèves" in (
                " ".join(pdf[1].get_text().split())
            )
        for page in pdf:
            assert "Keldin - entraînement non officiel - non calibré" in page.get_text()


def test_v34_print_policy_identity_cannot_be_relabelled(tmp_path):
    package = generate(tmp_path)
    package["identity"]["print_policy"] = "approved"
    with pytest.raises(ValueError):
        validate_package(package)


def test_unknown_print_policy_is_rejected_before_writing(tmp_path):
    from Backend.Core.france.rendering import render_assessment

    path = tmp_path / "invalid.pdf"
    with pytest.raises(ValueError, match="print policy"):
        render_assessment(path, [], correction=False, print_policy="approved")
    assert not path.exists()


def test_v34_pdf_cannot_silently_use_historical_notices(tmp_path):
    from Backend.Core.france.rendering import render_assessment
    from Backend.Core.france.whole_case_pdf import validate_whole_case_pdf
    from Backend.Core.render_transaction import render_pdf_atomically

    package = generate(tmp_path)
    path = tmp_path / "wrong-policy.pdf"
    render_pdf_atomically(
        path,
        lambda destination: render_assessment(
            destination,
            [NSIExercise.model_validate(raw) for raw in package["exercises"]],
            correction=False,
            human_readable_graph_titles=True,
            coherent_material_flow=True,
            compact_correction=True,
        ),
        role="question_paper",
        language="fr-FR",
    )
    with pytest.raises(ValueError, match="Pied de page"):
        validate_whole_case_pdf(path, package, correction=False)


def family_history(seed):
    from Backend.Core.france.extended_pipeline import _source

    return [
        exercise_candidate_text(NSIExercise.model_validate(raw))
        for raw in _source(seed)[2]
    ]


@pytest.mark.parametrize("seed", [270100, 270101, 270102, 270103, -(2**63), 2**63 - 1])
def test_unused_family_selection_preserves_preferred_seed(seed):
    from Backend.Core.france.extended_pipeline import choose_fresh_seed

    assert choose_fresh_seed(seed) == seed


@pytest.mark.parametrize("remaining", range(4))
def test_unused_family_selection_finds_only_remaining_whole_paper(remaining):
    from Backend.Core.france.extended_pipeline import choose_fresh_seed

    history = [
        text
        for family in range(4)
        if family != remaining
        for text in family_history(270100 + family)
    ]
    before = history.copy()
    selected = choose_fresh_seed(270100, previous_texts=history)
    assert selected == 270100 + remaining
    assert history == before


def test_same_preference_generates_four_families_then_reports_exhaustion(tmp_path):
    from Backend.Core.france.extended_pipeline import (
        FamilyCatalogueExhausted,
        choose_fresh_seed,
    )

    history, selected = [], []
    for _ in range(4):
        seed = choose_fresh_seed(270100, previous_texts=history)
        package = generate(tmp_path, seed, history)
        assert package["identity"]["seed"] == seed
        selected.append(package["identity"]["family"])
        history.extend(
            exercise_candidate_text(NSIExercise.model_validate(raw))
            for raw in package["exercises"]
        )
    before = history.copy()
    assert selected == [0, 1, 2, 3]
    with pytest.raises(FamilyCatalogueExhausted, match="quatre familles"):
        choose_fresh_seed(270100, previous_texts=history)
    assert history == before
    assert len(list(tmp_path.glob("checkpoint-*.json"))) == 4


def test_one_repeated_exercise_excludes_the_entire_family():
    from Backend.Core.france.extended_pipeline import choose_fresh_seed

    assert (
        choose_fresh_seed(270100, previous_texts=family_history(270100)[:1]) == 270101
    )


def test_unused_family_selection_wraps_signed_seed_without_overflow():
    from Backend.Core.france.extended_pipeline import choose_fresh_seed

    seed = 2**63 - 1
    assert choose_fresh_seed(seed, previous_texts=family_history(seed)) == -(2**63)


@pytest.mark.parametrize("history", [(), {}, [None], [""], ["x" * 100001], ["x"] * 21])
def test_unused_family_selection_rejects_malformed_history(history):
    from Backend.Core.france.extended_pipeline import choose_fresh_seed

    with pytest.raises(ValueError, match="history"):
        choose_fresh_seed(270100, previous_texts=history)


@pytest.mark.parametrize("seed", [True, "270100", 1.5, -(2**63) - 1, 2**63])
def test_unused_family_selection_rejects_invalid_seed(seed):
    from Backend.Core.france.extended_pipeline import choose_fresh_seed

    with pytest.raises(ValueError, match="seed"):
        choose_fresh_seed(seed)


def test_unused_family_selection_does_not_swallow_unrelated_validation_errors(
    monkeypatch,
):
    from Backend.Core.france import extended_pipeline, originality

    def broken_screen(*args, **kwargs):
        raise ValueError("broken fixture, not a similarity rejection")

    monkeypatch.setattr(originality, "screen_originality", broken_screen)
    with pytest.raises(ValueError, match="broken fixture"):
        extended_pipeline.choose_fresh_seed(270100)
