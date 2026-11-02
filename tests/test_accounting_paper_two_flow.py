import json
from pathlib import Path

import pymupdf
import pytest
from aqaaccountgen.cli import generate_package
from aqaaccountgen.configs import RULES
from aqaaccountgen.generator import build_paper
from aqaaccountgen.render_pdf import render_mark_scheme
from aqaaccountgen.syllabus import load_syllabus

from Backend.Core.ai_assessment import (
    _difficulty_candidate,
    _generation_prompt,
    _review_prompt,
    _tasks,
)
from Backend.Core.answer_projection import without_private_answer_keys
from Backend.Core.assessment_package import _extract_items
from Backend.Core.exam_blueprints import GeneratedPaper, MarkSchemePoint
from Backend.Core.layout_conformance import conform_generated_documents
from Backend.Core.layout_master import LayoutConformanceError

POLICY = "generated-aqa-accounting-paper2-human-scheme-v1"
KEY = "accounting_marking_policy"


@pytest.fixture
def paths(tmp_path):
    return generate_package(
        paper="2",
        output_dir=tmp_path,
        seed=270100,
        dry_run=True,
        syllabus_path=Path("Resources/accounting/aqa/generator/data/syllabus.json"),
    )


def test_public_paper_two_builder_declares_human_flow_policy(paths):
    package = json.loads(paths["assessment_package"].read_text())
    questions = [
        q
        for s in package["blueprint"]["sections"]
        for q in s["options"][0]["questions"]
    ]
    assert all(q["authoring_context"].get(KEY) == POLICY for q in questions)
    report = conform_generated_documents("accounting_aqa", "2", paths)["mark_scheme"]
    assert report["policy"] == POLICY
    assert report["checked_parts"] == 24


def test_new_scheme_has_no_technical_padding_or_repeated_boilerplate(paths):
    with pymupdf.open(paths["mark_scheme"]) as document:
        text = "\n".join(page.get_text() for page in document)
        assert "verification record" not in text
        assert "verified_answers." not in text
        assert "source_data." not in text
        assert text.count("General marking guidance") == 1
        assert text.count("This guidance is written for this independent practice") <= 1
        assert len(document) < 28
        methods = [
            span
            for page in document
            for block in page.get_text("dict")["blocks"]
            if "lines" in block
            for line in block["lines"]
            for span in line["spans"]
            if span["text"].startswith("Method:")
        ]
        assert methods and all(abs(span["size"] - 11) < 0.01 for span in methods)
        for page in document:
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        assert page.rect.contains(pymupdf.Rect(span["bbox"]))


def _package(paths):
    return json.loads(paths["assessment_package"].read_text())


def _questions(package):
    return [
        q
        for s in package["blueprint"]["sections"]
        for q in s["options"][0]["questions"]
    ]


def _save(paths, package, *, render=False):
    package["items"] = _extract_items(
        package["blueprint"], subject=package["subject"], paper_number="2"
    )
    paths["assessment_package"].write_text(json.dumps(package))
    if render:
        render_mark_scheme(
            GeneratedPaper.model_validate(package["blueprint"]), paths["mark_scheme"]
        )


def test_unmarked_paper_two_replays_legacy_without_upgrading_it(paths):
    package = _package(paths)
    for question in _questions(package):
        question["authoring_context"].pop(KEY)
    _save(paths, package, render=True)
    with pymupdf.open(paths["mark_scheme"]) as document:
        assert len(document) == 28
        assert sum("verification record" in page.get_text() for page in document) == 12
    assert conform_generated_documents("accounting_aqa", "2", paths) == {}


def test_forged_mode_cannot_remove_the_applicable_decision_grid(paths):
    package = _package(paths)
    question = _questions(package)[-1]
    question["scheme_mode"] = "points"
    question["structured_mark_scheme"] = [
        point
        for point in question["structured_mark_scheme"]
        if not point["text"].startswith("Level ")
    ]
    with pytest.raises((LayoutConformanceError, ValueError)):
        _save(paths, package, render=True)
        conform_generated_documents("accounting_aqa", "2", paths)


def test_positive_reserved_heading_cannot_disappear_from_a_complete_package(paths):
    package = _package(paths)
    question = next(q for q in _questions(package) if q["number"] == "14.1")
    point = next(p for p in question["structured_mark_scheme"] if p["marks"] == 1)
    point["text"] = "Levels-based marking"
    # Same tariff, source inputs and assessment items: this used to render only
    # three of the four awarded marks, then pass the shared-row verifier.
    with pytest.raises((ValueError, LayoutConformanceError), match=r"award|reserved"):
        _save(paths, package, render=True)
        conform_generated_documents("accounting_aqa", "2", paths)


def test_actual_printed_award_total_is_independent_of_shared_row_filters(
    paths, monkeypatch
):
    from aqaaccountgen import render_pdf, scheme_policy

    original = scheme_policy.question_rows

    def lose_one_award(question):
        rows, levels = original(question)
        if question.number == "14.1":
            index = next(i for i, row in enumerate(rows) if row[1] == "1")
            rows = rows[:index] + rows[index + 1 :]
        return rows, levels

    # Simulate any future shared-helper filtering bug in BOTH render and proof.
    monkeypatch.setattr(scheme_policy, "question_rows", lose_one_award)
    monkeypatch.setattr(render_pdf, "question_rows", lose_one_award)
    package = _package(paths)
    _save(paths, package, render=True)
    with pytest.raises(LayoutConformanceError, match=r"printed.*award.*total"):
        conform_generated_documents("accounting_aqa", "2", paths)


@pytest.mark.parametrize(
    "mutation",
    [
        "unknown",
        "partial",
        "items",
        "tariff",
        "section",
        "grid",
        "missing-package",
        "stripped-policy",
    ],
)
def test_forged_policy_and_incomplete_credit_cannot_select_new_layout(paths, mutation):
    package = _package(paths)
    questions = _questions(package)
    if mutation == "missing-package":
        paths.pop("assessment_package")
    elif mutation == "items":
        package["items"].pop()
        paths["assessment_package"].write_text(json.dumps(package))
    else:
        if mutation == "unknown":
            questions[0]["authoring_context"][KEY] = "unrecognised"
        elif mutation == "partial":
            questions[0]["authoring_context"].pop(KEY)
        elif mutation == "stripped-policy":
            for question in questions:
                question["authoring_context"].pop(KEY)
        elif mutation == "tariff":
            questions[11]["structured_mark_scheme"][0]["marks"] += 1
        elif mutation == "section":
            package["blueprint"]["sections"][0]["candidate_marks"] += 1
        elif mutation == "grid":
            questions[-1]["structured_mark_scheme"] = [
                p
                for p in questions[-1]["structured_mark_scheme"]
                if not p["text"].startswith("Level 5 ")
            ]
        _save(paths, package)
    with pytest.raises((LayoutConformanceError, ValueError)):
        conform_generated_documents("accounting_aqa", "2", paths)


def _replace_cell(page, cell, text):
    rect = pymupdf.Rect(cell)
    page.add_redact_annot(
        pymupdf.Rect(rect.x0 + 0.5, rect.y0 + 0.5, rect.x1 - 0.5, rect.y1 - 0.5)
    )
    page.apply_redactions(graphics=0)
    page.insert_text((rect.x0 + 4, rect.y0 + 10), text, fontsize=7.6)


@pytest.mark.parametrize(
    "mutation",
    [
        "award",
        "method",
        "header",
        "band",
        "blank-page",
        "repeat-page",
        "notes-page",
        "missing-cover",
    ],
)
def test_real_pdf_mutations_cannot_hide_behind_other_present_credit(paths, mutation):
    with pymupdf.open(paths["mark_scheme"]) as document:
        if mutation == "blank-page":
            document.new_page(width=595.32, height=841.92)
        elif mutation == "notes-page":
            document.new_page(width=595.32, height=841.92).insert_text(
                (72, 72), "Notes"
            )
        elif mutation == "missing-cover":
            document.delete_page(0)
        elif mutation == "repeat-page":
            document.fullcopy_page(2)
        else:
            target = (
                "Question 17: levels grid" if mutation == "band" else "Question 12.1:"
            )
            pymupdf.no_recommend_layout()
            page, table = next(
                (page, table)
                for page in document
                for table in page.find_tables().tables
                if (table.extract()[0][0] or "").startswith(target)
            )
            if mutation == "award":
                _replace_cell(page, table.rows[1].cells[1], "2")
            elif mutation == "method":
                _replace_cell(page, table.rows[1].cells[0], "A different method")
            elif mutation == "header":
                _replace_cell(
                    page, table.rows[0].cells[0], "Question 12.2: wrong owner"
                )
            else:
                _replace_cell(page, table.rows[1].cells[1], "20-25")
        document.saveIncr()
    with pytest.raises(LayoutConformanceError):
        conform_generated_documents("accounting_aqa", "2", paths)


def test_alternatives_exclusions_dependencies_and_literal_text_survive(paths):
    package = _package(paths)
    point = _questions(package)[11]["structured_mark_scheme"][0]
    point.update(
        alternatives=["An equivalent method with A < B & C > D"],
        allow=["A clearly labelled equivalent working"],
        do_not_accept=["An unrelated accounting identity"],
        ignore=["An immaterial spelling difference"],
        depends_on=["The preceding method is shown"],
    )
    _save(paths, package, render=True)
    assert (
        conform_generated_documents("accounting_aqa", "2", paths)["mark_scheme"][
            "policy"
        ]
        == POLICY
    )
    with pymupdf.open(paths["mark_scheme"]) as document:
        text = " ".join(" ".join(page.get_text().split()) for page in document)
        for phrase in (
            "A < B & C > D",
            "Allow:",
            "Do not accept:",
            "Ignore:",
            "Depends on:",
        ):
            assert phrase in text
        for page in document:
            for rect in page.search_for("An equivalent method"):
                page.add_redact_annot(rect)
            page.apply_redactions(graphics=0)
        document.saveIncr()
    with pytest.raises(LayoutConformanceError):
        conform_generated_documents("accounting_aqa", "2", paths)


def test_genuinely_oversized_question_flows_without_losing_credit(paths):
    package = _package(paths)
    question = _questions(package)[11]
    question["structured_mark_scheme"].extend(
        MarkSchemePoint(
            text=f"Additional distinct method note {i}: retain the stated precision and explain the accounting treatment.",
            marks=0,
            credit_type="guidance",
        ).model_dump(mode="json")
        for i in range(90)
    )
    _save(paths, package, render=True)
    report = conform_generated_documents("accounting_aqa", "2", paths)["mark_scheme"]
    assert report["checked_parts"] == 24
    with pymupdf.open(paths["mark_scheme"]) as document:
        text = "\n".join(page.get_text() for page in document)
        assert all(f"Additional distinct method note {i}:" in text for i in range(90))


def test_paper_two_policy_cannot_be_applied_to_paper_one(tmp_path):
    paths = generate_package(
        paper="1",
        output_dir=tmp_path,
        seed=270100,
        dry_run=True,
        syllabus_path=Path("Resources/accounting/aqa/generator/data/syllabus.json"),
    )
    package = _package(paths)
    questions = _questions(package)
    assert all(
        q["authoring_context"].get(KEY) in (None, "aqa-accounting-explicit-credit-v1")
        for q in questions
    )
    for question in questions:
        question["authoring_context"][KEY] = POLICY
    with pytest.raises(ValueError, match="policy"):
        render_mark_scheme(
            GeneratedPaper.model_validate(package["blueprint"]), paths["mark_scheme"]
        )
    package["items"] = _extract_items(
        package["blueprint"], subject=package["subject"], paper_number="1"
    )
    paths["assessment_package"].write_text(json.dumps(package))
    with pytest.raises(LayoutConformanceError, match="Paper 1"):
        conform_generated_documents("accounting_aqa", "1", paths)


@pytest.mark.parametrize("seed", [270100, 270101])
def test_policy_changes_only_declared_metadata_not_any_model_evidence(seed):
    syllabus = load_syllabus(
        Path("Resources/accounting/aqa/generator/data/syllabus.json")
    )
    current = build_paper(RULES["paper_2"], syllabus, seed)
    legacy = current.model_copy(deep=True)
    for section in legacy.sections:
        for question in section.options[0].questions:
            question.authoring_context.pop(KEY)

    def without_policy(value):
        if isinstance(value, dict):
            return {
                k: without_policy(v)
                for k, v in value.items()
                if not (k == KEY and v == POLICY)
                and not (k == "question_context" and v == {KEY: POLICY})
            }
        if isinstance(value, list):
            return [without_policy(v) for v in value]
        return value

    assert without_policy(current.model_dump(mode="json")) == legacy.model_dump(
        mode="json"
    )
    topics = {topic.id: topic for topic in syllabus.topics}
    for task, old in zip(_tasks(current, topics), _tasks(legacy, topics), strict=True):
        # This is the exact recursive projection used by IndependentSolver.
        assert without_private_answer_keys(
            task.question.model_dump(mode="json")
        ) == without_private_answer_keys(old.question.model_dump(mode="json"))
        for marker, new_prompt, old_prompt in (
            (
                "BLUEPRINT_DATA=",
                _generation_prompt(
                    [task],
                    subject="accounting",
                    seed=seed,
                    attempt=1,
                    previous_failure="",
                ),
                _generation_prompt(
                    [old],
                    subject="accounting",
                    seed=seed,
                    attempt=1,
                    previous_failure="",
                ),
            ),
            (
                "REVIEW_DATA=",
                _review_prompt([task], [task.question], subject="accounting"),
                _review_prompt([old], [old.question], subject="accounting"),
            ),
        ):
            prefix, data = new_prompt.split(marker)
            old_prefix, old_data = old_prompt.split(marker)
            assert prefix == old_prefix
            assert without_policy(json.loads(data)) == json.loads(old_data)
        assert (
            without_policy(_difficulty_candidate(task, task.question).review_content)
            == _difficulty_candidate(old, old.question).review_content
        )
