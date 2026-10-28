from __future__ import annotations

import re
from copy import deepcopy
from pathlib import Path

import pymupdf
import pytest
from aqaaccountgen.configs import load_rule
from aqaaccountgen.generator import build_paper
from aqaaccountgen.render_pdf import _indicative_content_page, render_mark_scheme
from aqaaccountgen.syllabus import load_syllabus
from reportlab.platypus import SimpleDocTemplate

from Backend.Core.assessment_package import (
    _assessment_contract,
    _validate_response_bands,
)

ROOT = Path(__file__).resolve().parents[1]
SYLLABUS = load_syllabus(ROOT / "Resources/accounting/aqa/generator/data/syllabus.json")


@pytest.fixture
def paper():
    return build_paper(load_rule("1"), SYLLABUS, 270100)


def question(paper, rule_id):
    return next(
        q
        for section in paper.sections
        for q in section.options[0].questions
        if q.rule_id == rule_id
    )


def pdf_text(path):
    with pymupdf.open(path) as document:
        return "\n".join(page.get_text() for page in document)


@pytest.mark.parametrize(
    "rule_id,count",
    [
        ("statement_extract", 7),
        ("ledger_calculation", 5),
        ("accounting_concept", 2),
        ("company_statement", 14),
        ("partnership_1", 6),
        ("partnership_2", 8),
    ],
)
def test_explicit_closed_task_allocations_include_credit_entries(paper, rule_id, count):
    item = question(paper, rule_id)
    awarded = [point for point in item.structured_mark_scheme if point.marks]
    assert len(awarded) == count
    assert all(point.marks == 1 for point in awarded)
    assert (
        item.authoring_context["accounting_marking_policy"]
        == "aqa-accounting-explicit-credit-v1"
    )


def test_trade_discount_has_two_distinct_three_mark_reason_budgets(paper):
    item = question(paper, "explain_trade")
    assert item.scheme_mode == "levels"
    awarded = [point for point in item.structured_mark_scheme if point.marks]
    assert [point.marks for point in awarded] == [3, 3]
    assert all(
        point.credit_type == "level" and point.assessment_objective == "AO1"
        for point in awarded
    )
    assert "first distinct reason" in awarded[0].text.casefold()
    assert "second distinct reason" in awarded[1].text.casefold()


def test_paper_one_prints_no_extra_asset_presentation_mark(paper, tmp_path):
    path = tmp_path / "scheme.pdf"
    render_mark_scheme(paper, path)
    text = pdf_text(path)
    assert "Award one mark for the correct presentation" not in text
    assert "not additional" in text


def test_supplied_tax_charge_is_not_recalculated_for_own_figures(paper, tmp_path):
    path = tmp_path / "scheme.pdf"
    render_mark_scheme(paper, path)
    text = pdf_text(path)
    assert "Credit a tax charge calculated consistently" not in text
    assert "supplied taxation charge" in text
    assert "do not recalculate" in text


def test_renderer_rejects_a_different_allocation_with_the_same_total(paper, tmp_path):
    item = question(paper, "ledger_calculation")
    points = [point for point in item.structured_mark_scheme if point.marks]
    points[0].marks += 1
    points[1].marks -= 1
    assert sum(point.marks for point in item.structured_mark_scheme) == item.marks
    with pytest.raises(ValueError, match="marking policy"):
        render_mark_scheme(paper, tmp_path / "forged.pdf")


def test_renderer_requires_the_explicit_policy_not_a_legacy_fallback(paper, tmp_path):
    question(paper, "ledger_calculation").authoring_context.pop(
        "accounting_marking_policy", None
    )
    with pytest.raises(ValueError, match="marking policy"):
        render_mark_scheme(paper, tmp_path / "missing-policy.pdf")


def test_indicative_content_uses_typed_source_content_not_enriched_guidance(
    paper, tmp_path
):
    item = question(paper, "company_adjustment")
    source_point = "AO3: A credit-control check can change this firm's decision."
    item.authoring_context["accounting_source_content"] = [
        {"role": "indicative", "text": source_point},
        {
            "role": "level_descriptor",
            "text": "Level 3 (5-6): Example level descriptor.",
        },
    ]
    item.mark_scheme.append("AO3: GENERIC_POLICY_SENTINEL")
    path = tmp_path / "typed-content.pdf"
    SimpleDocTemplate(str(path)).build(_indicative_content_page(item, "Question 14.2"))
    text = re.sub(r"\s+", " ", pdf_text(path))
    assert source_point in text
    assert "GENERIC_POLICY_SENTINEL" not in text
    assert "Example level descriptor" not in text


def grouped_item(paper):
    item = question(paper, "explain_trade")
    policy = {
        "id": "aqa-accounting-two-reasons-v1",
        "schema_version": 1,
        "distinct_reasons_required": True,
        "groups": [
            {
                "id": "first_reason",
                "maximum_mark": 3,
                "assessment_objective": "AO1",
                "observable_mark_points": [
                    "A larger order is a valid reason.",
                    "A lower effective price can increase the quantity bought.",
                    "Higher volume can improve revenue or inventory turnover.",
                ],
            },
            {
                "id": "second_reason",
                "maximum_mark": 3,
                "assessment_objective": "AO1",
                "observable_mark_points": [
                    "Repeat purchasing is a different valid reason.",
                    "The discount gives an incentive to return.",
                    "Customer retention can make future revenue more predictable.",
                ],
            },
        ],
        "levels": [
            {
                "level": level,
                "minimum_mark": level,
                "maximum_mark": level,
                "minimum_coverage": coverage,
                "descriptor": text,
            }
            for level, coverage, text in [
                (0, 0.0, "Nothing worthy of credit."),
                (1, 0.01, "A relevant reason is identified."),
                (2, 0.5, "The reason is partly explained."),
                (3, 0.75, "A thorough explanation shows a business benefit."),
            ]
        ],
    }
    return {
        "id": "11",
        "subject": "accounting_aqa",
        "paper": "1",
        "marks": 6,
        "command_word": "Explain",
        "scheme_mode": "levels",
        "prompt": item.prompt,
        "structured_mark_scheme": [
            point.model_dump(mode="json") for point in item.structured_mark_scheme
        ],
        "assessment_contract": {
            "level_policy_id": "aqa-standard-4-level",
            "grouped_level_policy": policy,
            "accounting_marking_policy": "aqa-accounting-explicit-credit-v1",
        },
    }


def test_two_reason_simulation_checks_each_three_mark_group(paper):
    result = _validate_response_bands(grouped_item(paper))
    assert result["marks"] == [2, 4, 6]
    assert result["annotations_complete"] is True
    assert result["simulation_kind"] == "synthetic-grouped-reasons"
    assert [group["marks"] for group in result["groups"]] == [[1, 2, 3], [1, 2, 3]]
    assert all(group["maximum_mark"] == 3 for group in result["groups"])


@pytest.mark.parametrize("subject", ["accounting", "accounting_aqa"])
def test_two_reason_simulation_retains_supported_subject_aliases(paper, subject):
    item = grouped_item(paper)
    item["subject"] = subject
    assert _validate_response_bands(item)["marks"] == [2, 4, 6]


@pytest.mark.parametrize("subject", ["economics", "computer_science", "", None])
def test_accounting_reason_policy_cannot_be_applied_to_other_subjects(paper, subject):
    item = grouped_item(paper)
    item["subject"] = subject
    with pytest.raises(ValueError, match="outside its supported Accounting task"):
        _validate_response_bands(item)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "absent",
        "cap",
        "ao",
        "duplicate",
        "shape",
        "repeated_reason",
        "weights",
        "boolean",
    ],
)
def test_two_reason_simulation_rejects_invalid_contracts(paper, mutation):
    item = grouped_item(paper)
    policy = item["assessment_contract"]["grouped_level_policy"]
    if mutation == "missing":
        policy["groups"].pop()
    elif mutation == "absent":
        del item["assessment_contract"]["grouped_level_policy"]
    elif mutation == "cap":
        policy["groups"][0]["maximum_mark"] = 4
    elif mutation == "ao":
        policy["groups"][0]["assessment_objective"] = "AO2"
    elif mutation == "duplicate":
        policy["groups"][1]["id"] = "first_reason"
    elif mutation == "shape":
        policy["groups"] = "two groups"
    elif mutation == "repeated_reason":
        policy["groups"][1]["observable_mark_points"] = deepcopy(
            policy["groups"][0]["observable_mark_points"]
        )
    elif mutation == "weights":
        item["structured_mark_scheme"][0]["marks"] = 4
        item["structured_mark_scheme"][1]["marks"] = 2
    else:
        policy["schema_version"] = True
    with pytest.raises(ValueError, match="grouped level policy"):
        _validate_response_bands(item)


def test_grouped_policy_survives_existing_assessment_contract_projection(paper):
    item = question(paper, "explain_trade")
    raw = item.model_dump(mode="json")
    policy = grouped_item(paper)["assessment_contract"]["grouped_level_policy"]
    raw["authoring_context"]["grouped_level_policy"] = policy
    raw["contract"] = {"level_policy_id": "aqa-standard-4-level"}
    assert _assessment_contract(raw)["grouped_level_policy"] == policy


@pytest.mark.parametrize(
    "rule_id", ["ledger_calculation", "accounting_concept", "partnership_1"]
)
def test_full_paper_pdf_award_cells_match_persisted_credit_routes(
    paper, tmp_path, rule_id
):
    path = tmp_path / "full-paper-scheme.pdf"
    render_mark_scheme(paper, path)
    item = question(paper, rule_id)
    with pymupdf.open(path) as document:
        for point in (
            point for point in item.structured_mark_scheme if point.marks > 0
        ):
            needle = " ".join(point.text.split()[:5])
            cells = []
            for page in document:
                for rect in page.search_for(needle):
                    cells.extend(
                        word[4]
                        for word in page.get_text("words")
                        if word[0] > page.rect.width * 0.80
                        and rect.y0 <= (word[1] + word[3]) / 2 <= rect.y1
                    )
            assert cells == [str(point.marks)], (item.number, point.text, cells)
