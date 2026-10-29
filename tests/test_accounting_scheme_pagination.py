import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pymupdf
import pytest
from aqaaccountgen.cli import generate_package
from aqaaccountgen.render_pdf import render_mark_scheme

from Backend.Core.assessment_package import _extract_items
from Backend.Core.exam_blueprints import GeneratedPaper
from Backend.Core.layout_conformance import conform_generated_documents
from Backend.Core.layout_master import LayoutConformanceError


@pytest.fixture
def paths(tmp_path):
    return generate_package(
        paper="1",
        output_dir=tmp_path,
        seed=270100,
        dry_run=True,
        syllabus_path=Path("Resources/accounting/aqa/generator/data/syllabus.json"),
    )


def test_compact_accounting_scheme_has_an_explicit_printed_credit_policy(paths):
    report = conform_generated_documents("accounting_aqa", "1", paths)["mark_scheme"]
    assert report["policy"] == "generated-aqa-accounting-paper1-credit-v1"
    assert report["actual_page_count"] == 24
    assert report["reference_page_count"] == 26
    assert report["checked_parts"] == 21
    assert report["checked_credit_statements"] > 40


@pytest.mark.parametrize(
    "mutation",
    [
        "blank-padding",
        "missing-page",
        "missing-credit",
        "policy",
        "items",
        "missing-package",
    ],
)
def test_compact_accounting_scheme_refuses_incomplete_or_forged_credit(paths, mutation):
    if mutation == "missing-package":
        paths.pop("assessment_package")
    elif mutation in {"policy", "items"}:
        path = paths["assessment_package"]
        data = json.loads(path.read_text(encoding="utf-8"))
        if mutation == "items":
            data["items"].pop()
        else:
            data["blueprint"]["sections"][0]["options"][0]["questions"][10][
                "authoring_context"
            ]["accounting_marking_policy"] = "unknown"
            data["items"] = _extract_items(
                data["blueprint"], subject=data["subject"], paper_number="1"
            )
        path.write_text(json.dumps(data), encoding="utf-8")
    else:
        with pymupdf.open(paths["mark_scheme"]) as document:
            if mutation == "blank-padding":
                document.new_page()
            elif mutation == "missing-page":
                document.delete_page(23)
            else:
                for rect in document[16].search_for("missing cash"):
                    document[16].add_redact_annot(rect)
                document[16].apply_redactions()
            document.saveIncr()
    with pytest.raises((LayoutConformanceError, ValueError)):
        conform_generated_documents("accounting_aqa", "1", paths)


def test_unmarked_historical_scheme_retains_exact_legacy_page_count(tmp_path):
    path = tmp_path / "legacy-scheme.pdf"
    with pymupdf.open() as document:
        for number in range(26):
            page = document.new_page(width=595.32, height=841.92)
            page.insert_text((70, 70), f"Retained legacy page {number + 1}")
        document.save(path)
    assert (
        conform_generated_documents("accounting_aqa", "1", {"mark_scheme": path}) == {}
    )


def _table(document, page_number, headings):
    tables = [
        table
        for table in document[page_number].find_tables().tables
        if [(cell or "").replace("\n", " ") for cell in table.extract()[0]] == headings
    ]
    assert len(tables) == 1, (page_number, headings)
    return tables[0]


@pytest.mark.parametrize(
    "page_number,headings",
    [
        (10, ["Requirement", "Mark"]),
        (20, ["Level", "Marks", "Descriptor"]),
        (22, ["Level", "Marks", "Descriptor"]),
    ],
)
def test_printed_award_tables_and_level_grids_are_required(
    paths, page_number, headings
):
    with pymupdf.open(paths["mark_scheme"]) as document:
        table = _table(document, page_number, headings)
        document[page_number].add_redact_annot(table.bbox)
        document[page_number].apply_redactions(graphics=0)
        document.saveIncr()
    with pytest.raises(LayoutConformanceError):
        conform_generated_documents("accounting_aqa", "1", paths)


def _replace_cell(page, rect, value):
    rect = pymupdf.Rect(rect)
    inset = pymupdf.Rect(rect.x0 + 0.5, rect.y0 + 0.5, rect.x1 - 0.5, rect.y1 - 0.5)
    page.add_redact_annot(inset)
    page.apply_redactions(graphics=0)
    page.insert_text((rect.x0 + 4, rect.y0 + 10), value, fontsize=7.6)


@pytest.mark.parametrize("mutation", ["ledger-awards", "income-awards", "level-band"])
def test_printed_awards_cannot_be_changed_while_all_figures_remain(paths, mutation):
    with pymupdf.open(paths["mark_scheme"]) as document:
        if mutation == "ledger-awards":
            table = _table(document, 10, ["Requirement", "Mark"])
            cells = [table.rows[index].cells[-1] for index in (1, 2)]
            for rect, value in zip(cells, ["2", "0"], strict=True):
                _replace_cell(document[10], rect, value)
        elif mutation == "income-awards":
            table = _table(document, 12, ["", "£", "£", "Marks"])
            cells = [table.rows[index].cells[-1] for index in (2, 6)]
            for rect, value in zip(cells, ["1", "2"], strict=True):
                _replace_cell(document[12], rect, value)
        else:
            table = _table(document, 20, ["Level", "Marks", "Descriptor"])
            _replace_cell(document[20], table.rows[1].cells[1], "20-25")
        document.saveIncr()
    with pytest.raises(LayoutConformanceError):
        conform_generated_documents("accounting_aqa", "1", paths)


@pytest.mark.parametrize(
    "mutation", ["duplicate-written-part", "wrong-written-rule", "wrong-mcq-rule"]
)
def test_compact_policy_requires_exact_question_shape_not_only_count_and_sets(
    paths, mutation
):
    path = paths["assessment_package"]
    data = json.loads(path.read_text(encoding="utf-8"))
    sections = data["blueprint"]["sections"]
    questions = sections[0]["options"][0]["questions"]
    if mutation == "duplicate-written-part":
        questions[8] = deepcopy(questions[12])
        option = sections[0]["options"][0]
        option["selection_context"]["question_ids"] = [
            question["number"] for question in questions
        ]
    elif mutation == "wrong-written-rule":
        sections[1]["options"][0]["questions"][1]["rule_id"] = "partnership_3"
    else:
        questions[0]["rule_id"] = "mcq_2"
    data["items"] = _extract_items(
        data["blueprint"], subject=data["subject"], paper_number="1"
    )
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(LayoutConformanceError):
        conform_generated_documents("accounting_aqa", "1", paths)


def test_compact_credit_checks_preserve_the_bridge_json_stream(paths):
    # A fresh process retains PyMuPDF's default recommendation setting. Merely
    # testing in this process could miss an advertisement printed once earlier.
    script = """
import json
import sys
from pathlib import Path
from Backend.Core.layout_conformance import conform_generated_documents
paths = {key: Path(value) for key, value in json.loads(sys.argv[1]).items()}
report = conform_generated_documents("accounting_aqa", "1", paths)
print(json.dumps({"type": "done", "report": report}))
"""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            script,
            json.dumps({key: str(value) for key, value in paths.items()}),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
        env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
    )
    lines = result.stdout.splitlines()
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0])["report"]["mark_scheme"]["checked_parts"] == 21


def test_missing_quiet_table_support_fails_with_actionable_error(paths, monkeypatch):
    monkeypatch.delattr(pymupdf, "no_recommend_layout")
    with pytest.raises(LayoutConformanceError, match="pinned PyMuPDF build"):
        conform_generated_documents("accounting_aqa", "1", paths)


def test_forged_scheme_mode_cannot_bypass_the_decision_grid_check(paths):
    path = paths["assessment_package"]
    data = json.loads(path.read_text(encoding="utf-8"))
    data["blueprint"]["sections"][2]["options"][0]["questions"][0]["scheme_mode"] = (
        "points"
    )
    data["items"] = _extract_items(
        data["blueprint"], subject=data["subject"], paper_number="1"
    )
    path.write_text(json.dumps(data), encoding="utf-8")
    with pymupdf.open(paths["mark_scheme"]) as document:
        table = _table(document, 20, ["Level", "Marks", "Descriptor"])
        document[20].add_redact_annot(table.bbox)
        document[20].apply_redactions(graphics=0)
        document.saveIncr()
    with pytest.raises(LayoutConformanceError):
        conform_generated_documents("accounting_aqa", "1", paths)


@pytest.mark.parametrize(
    "mutation",
    [
        "mcq-letter",
        "mcq-row-swap",
        "asset-carrying-swap",
        "income-expense-sign",
        "appropriation-period-swap",
        "ledger-sides",
        "sales-sides",
        "capital-partners",
    ],
)
def test_printed_answers_bind_question_row_column_and_accounting_sign(paths, mutation):
    with pymupdf.open(paths["mark_scheme"]) as document:
        if mutation in {"mcq-letter", "mcq-row-swap"}:
            page = document[7]
            table = _table(document, 7, ["Question", "Answer", "Mark"])
            if mutation == "mcq-letter":
                answer = table.extract()[1][1]
                letter = answer[7]
                _replace_cell(
                    page,
                    table.rows[1].cells[1],
                    answer.replace(
                        f"Option {letter}:",
                        f"Option {'B' if letter == 'A' else 'A'}:",
                        1,
                    ),
                )
            else:
                values = [row[1] for row in table.extract()[1:3]]
                for cell, value in zip(
                    [table.rows[1].cells[1], table.rows[2].cells[1]],
                    reversed(values),
                    strict=True,
                ):
                    _replace_cell(page, cell, value)
        else:
            specifications = {
                "asset-carrying-swap": (
                    9,
                    [
                        "Non-current assets",
                        "Cost £",
                        "Accumulated depreciation £",
                        "Carrying amount £",
                        "Marks",
                    ],
                    (1, 3),
                    (2, 3),
                ),
                "income-expense-sign": (12, ["", "£", "£", "Marks"], (2, 1), None),
                "appropriation-period-swap": (
                    18,
                    ["", "First period £", "Second period £", "Marks"],
                    (1, 1),
                    (1, 2),
                ),
                "ledger-sides": (
                    10,
                    ["Date", "Details", "£", "Date", "Details", "£"],
                    (1, 2),
                    (1, 5),
                ),
                "sales-sides": (
                    11,
                    ["Date", "Details", "£", "Date", "Details", "£"],
                    (1, 2),
                    (1, 5),
                ),
                "capital-partners": (
                    17,
                    [
                        "Date",
                        "Details",
                        "Alex £",
                        "Morgan £",
                        "Date",
                        "Details",
                        "Alex £",
                        "Morgan £",
                    ],
                    (1, 2),
                    (1, 3),
                ),
            }
            index, headings, first, second = specifications[mutation]
            page = document[index]
            # The asset headings are wrapped in the extracted cells.
            tables = page.find_tables().tables
            table = next(
                table
                for table in tables
                if [" ".join((cell or "").split()) for cell in table.extract()[0]]
                == headings
            )
            values = table.extract()
            if second is None:
                _replace_cell(
                    page,
                    table.rows[first[0]].cells[first[1]],
                    values[first[0]][first[1]].strip("()"),
                )
            else:
                first_value, second_value = (
                    values[first[0]][first[1]],
                    values[second[0]][second[1]],
                )
                assert first_value != second_value
                _replace_cell(page, table.rows[first[0]].cells[first[1]], second_value)
                _replace_cell(page, table.rows[second[0]].cells[second[1]], first_value)
        document.saveIncr()
    with pytest.raises(LayoutConformanceError):
        conform_generated_documents("accounting_aqa", "1", paths)


def test_mcq_renderer_uses_choices_and_key_not_mutable_scheme_prose(paths, tmp_path):
    data = json.loads(paths["assessment_package"].read_text(encoding="utf-8"))
    question = data["blueprint"]["sections"][0]["options"][0]["questions"][0]
    question["mark_scheme"][0] = "WRONG MUTABLE ANSWER"
    output = tmp_path / "mutated-scheme.pdf"
    render_mark_scheme(GeneratedPaper.model_validate(data["blueprint"]), output)
    with pymupdf.open(output) as document:
        text = document[7].get_text()
    assert "WRONG MUTABLE ANSWER" not in text
    expected = f"Option {'ABCD'[question['correct_choice']]}: {question['choices'][question['correct_choice']]}".removesuffix(
        "."
    )
    assert expected in text


def _render_live_gearing_choice(paths, suffix):
    """Reproduce the accepted live Q05 without depending on ignored artifacts."""
    data = json.loads(paths["assessment_package"].read_text(encoding="utf-8"))
    question = data["blueprint"]["sections"][0]["options"][0]["questions"][4]
    question["prompt"] = (
        "Select the statement that correctly describes how an increase in "
        "long-term debt affects a company's gearing ratio."
    )
    question["choices"] = [
        f"It decreases the gearing of the business{suffix}",
        f"It increases the gearing of the business{suffix}",
        f"It has no effect on the gearing of the business{suffix}",
        f"It only impacts the liquidity ratios{suffix}",
    ]
    question["correct_choice"] = 1
    answer = question["choices"][1]
    question["mark_scheme"] = [answer]
    question["structured_mark_scheme"][0]["text"] = answer
    data["items"] = _extract_items(
        data["blueprint"], subject=data["subject"], paper_number="1"
    )
    paths["assessment_package"].write_text(json.dumps(data), encoding="utf-8")
    render_mark_scheme(
        GeneratedPaper.model_validate(data["blueprint"]), paths["mark_scheme"]
    )


@pytest.mark.parametrize("suffix", ["", "."])
def test_mcq_credit_validation_accepts_canonical_printed_terminal_stop(paths, suffix):
    _render_live_gearing_choice(paths, suffix)
    with pymupdf.open(paths["mark_scheme"]) as document:
        table = _table(document, 7, ["Question", "Answer", "Mark"])
        assert table.extract()[5] == [
            "5",
            "Option B: It increases the gearing of the business",
            "1",
        ]
    report = conform_generated_documents("accounting_aqa", "1", paths)["mark_scheme"]
    assert report["checked_parts"] == 21


@pytest.mark.parametrize("mutation", ["letter", "missing-row", "text", "credit"])
def test_punctuated_choice_still_requires_its_exact_printed_row(paths, mutation):
    _render_live_gearing_choice(paths, ".")
    with pymupdf.open(paths["mark_scheme"]) as document:
        page = document[7]
        table = _table(document, 7, ["Question", "Answer", "Mark"])
        row = table.rows[5]
        if mutation == "missing-row":
            for cell in row.cells:
                _replace_cell(page, cell, "")
        elif mutation == "credit":
            _replace_cell(page, row.cells[2], "2")
        else:
            replacement = (
                "Option A: It increases the gearing of the business"
                if mutation == "letter"
                else "Option B: It decreases the gearing of the business"
            )
            _replace_cell(page, row.cells[1], replacement)
        document.saveIncr()
    with pytest.raises(
        LayoutConformanceError,
        match=r"Accounting scheme (printed awards differ|omits or repeats the credit table)",
    ):
        conform_generated_documents("accounting_aqa", "1", paths)
