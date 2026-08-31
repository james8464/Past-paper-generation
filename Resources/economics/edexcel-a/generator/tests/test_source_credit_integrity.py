"""Candidate-source, selected-credit and printed-source integrity regressions."""

import ast
import json
import re
from decimal import Decimal
from pathlib import Path

import pymupdf
import pytest
from pastpapergen.generator import build_paper_blueprint
from pastpapergen.ollama_client import _question_solver_item
from pastpapergen.paper_configs import load_builtin_paper_config
from pastpapergen.render_pdf import (
    candidate_stimulus_data,
    render_mark_scheme,
    render_question_paper,
)
from pastpapergen.syllabus import load_syllabus

from Backend.Core.assessment_package import _extract_items
from Backend.Core.independent_solver import IndependentSolver
from Backend.Core.model_review import independent_review
from Backend.Core.subjects.economics_contracts import SourceCell, calculation_working
from tests.support.edexcel import forced_part


def paper(seed):
    return build_paper_blueprint(
        load_builtin_paper_config("paper_3"),
        load_syllabus(Path(__file__).parents[1] / "data/syllabus_seed.json"),
        seed,
    )


@pytest.mark.parametrize("kind", ["multipart", "standalone", "mcq"])
def test_blind_solver_never_receives_private_credit_but_reviews_keep_it(kind):
    if kind == "standalone":
        question = paper(26083051).questions[0]
        part = question
    else:
        question = build_paper_blueprint(
            load_builtin_paper_config("paper_1"),
            load_syllabus(Path(__file__).parents[1] / "data/syllabus_seed.json"),
            26083049,
        ).questions[0]
        part = question.parts[1 if kind == "mcq" else 0]
    item = _question_solver_item(question, part)
    private_sentinel = "PRIVATE_MARKING_CONTRACT_SENTINEL_" + kind
    item["assessment_contract"]["private_regression_note"] = private_sentinel
    original_contract = json.loads(json.dumps(item["assessment_contract"]))
    item["stimulus"]["supplier_terms"] = {"credit": "30-day trade credit"}
    prompts = []

    class Client:
        def generate_json(self, prompt):
            prompts.append(prompt)
            answer = (
                item["choices"][0]
                if item["choices"]
                else "Independent explanation from candidate evidence."
            )
            return {
                "answer": answer,
                "mark_points": [answer],
                "steps": ["Use the candidate source."],
                "evidence_ids": [],
            }

    IndependentSolver(Client()).solve(item, [])
    blind = json.loads(prompts[0].split("\n", 1)[1])["item"]
    assert "assessment_contract" not in blind
    assert private_sentinel not in prompts[0]
    assert not any(statement in prompts[0] for statement in original_contract["credit"])
    assert blind["stimulus"] == item["stimulus"]
    assert blind["choices"] == item["choices"]
    assert blind["prompt"] == item["prompt"]
    assert blind["authoring_context"] == item["authoring_context"]
    assert item["assessment_contract"] == original_contract

    class Reviewer:
        def generate_json(self, prompt):
            prompts.append(prompt)
            return {
                "approved": True,
                "factual_issues": [],
                "marking_issues": [],
                "source_issues": [],
                "difficulty_issues": [],
                "ambiguity_issues": [],
            }

    independent_review(
        Reviewer(),
        item_id="captured-contract",
        subject="Edexcel Economics",
        blueprint=item,
        candidate=item,
        specification={"source": item["stimulus"]},
    )
    reviewed = json.loads(prompts[-1].split("\n", 1)[1])["candidate"]
    assert reviewed["assessment_contract"] == original_contract
    assert reviewed["mark_scheme"] == item["mark_scheme"]


REFERENCES = {
    "1(a)": {"Figure 1", "Extract A"},
    "1(b)": {"Figure 2", "Extract A"},
    "1(c)": {"Extract B"},
    "1(d)": {"Extract C"},
    "1(e)": {"Extract C"},
    "2(a)": {"Figure 3", "Extract D"},
    "2(b)": {"Extract E"},
    "2(c)": {"Extract E"},
    "2(d)": {"Extract E"},
    "2(e)": {"Extract F"},
}


def test_all_eight_selected_case_variants_bind_credit_to_both_source_groups():
    seen = set()
    for seed in range(80):
        blueprint = paper(seed)
        for q in blueprint.questions:
            seen.add((q.section, q.source_title))
            credit = " ".join(q.mark_scheme)
            refs = set(re.findall(r"Figure \d+|Extract [A-F]", credit))
            assert refs <= REFERENCES[q.number], (seed, q.number, refs)
            if q.topic_id in {"1.3", "1.4"} and q.marks == 12:
                price = re.search(r"prices changed by (\d+)%", q.source_text).group(1)
                assert set(re.findall(r"\b\d+%", credit)) == {price + "%"}
            if "Healthcare" not in q.source_title:
                assert not any(
                    word in credit.casefold()
                    for word in ("pharmaceutical", "patients", "medicine", "healthcare")
                ) or (q.topic_id == "1.3" and q.marks == 5)
            if "energy and utilities" not in q.source_title:
                assert not any(
                    word in credit.casefold()
                    for word in (
                        "energy-sector",
                        "energy prices",
                        "energy supply",
                        "generation or network capacity",
                        "sector-sector",
                    )
                )
    assert len(seen) == 16  # all eight case selections in each of A and B


@pytest.mark.parametrize(
    "seed,number,required,forbidden",
    [
        (
            26083051,
            "1(a)",
            ("Figure 1", "Extract A", "117", "100", "£6"),
            ("Figure 3", "Extract D"),
        ),
        (
            26083051,
            "1(b)",
            ("Extract A", "28%", "14 weeks", "12%", "9%"),
            ("Extract E",),
        ),
        (26083051, "1(c)", ("Extract B", "13%"), ("Extract E", "28%")),
        (26083052, "2(c)", ("Extract E",), ("Extract B", "energy output")),
        (
            26083052,
            "2(d)",
            ("Extract E", "transport"),
            ("Extract C", "sector-sector", "energy", "generation or network capacity"),
        ),
    ],
)
def test_actual_exported_and_printed_credit_contains_selected_instance_facts(
    tmp_path, seed, number, required, forbidden
):
    blueprint = paper(seed)
    items = _extract_items(
        blueprint.model_dump(mode="json"), subject="economics", paper_number="3"
    )
    item = next(item for item in items if item["id"].split("@")[0] == number)
    credit = " ".join(item["mark_scheme"])
    for text in required:
        assert text.casefold() in credit.casefold()
    for text in forbidden:
        assert text.casefold() not in credit.casefold()
    output = tmp_path / "scheme.pdf"
    render_mark_scheme(
        blueprint,
        load_syllabus(Path(__file__).parents[1] / "data/syllabus_seed.json"),
        output,
    )
    with pymupdf.open(output) as document:
        printed = " ".join(" ".join(page.get_text() for page in document).split())
    for line in item["mark_scheme"]:
        assert " ".join(line.split()) in printed


def concentration_item(shares):
    q = forced_part("concentration_ratio_table", "calculate", 4)
    source = q.source_instance.model_copy(deep=True)
    source = source.model_copy(
        update={
            "rows": [
                source.rows[0][:2],
                *[
                    [
                        SourceCell(text=f"Firm {index}"),
                        SourceCell(number=Decimal(str(value)), unit="%"),
                    ]
                    for index, value in enumerate(shares)
                ],
            ]
        }
    )
    q = q.model_copy(update={"source_instance": source})
    return q, _question_solver_item(q, q.parts[0])


@pytest.mark.parametrize(
    "shares,want,working",
    [
        ([10, 5, 20, 30, 35], "85.0%", "35 + 30 + 20"),
        ([35, 10, 30, 5, 20], "85.0%", "35 + 30 + 20"),
        ([20, 20, 20, 20, 20], "60.0%", "20 + 20 + 20"),
        ([1, 2, 3, 4, 90], "97.0%", "90 + 4 + 3"),
    ],
)
def test_candidate_boundary_selects_three_largest_valid_shares(shares, want, working):
    q, item = concentration_item(shares)
    result = IndependentSolver().solve(item, [])
    assert ast.literal_eval(result.answer) == {"result": want}
    assert calculation_working(q.source_instance, 4) == working


@pytest.mark.parametrize(
    "mutation",
    [
        "negative",
        "over100",
        "total",
        "few",
        "duplicate",
        "unit",
        "missing",
        "nan",
        "stale",
        "candidate",
        "prompt",
    ],
)
def test_concentration_candidate_boundary_rejects_malformed_or_stale_inputs(mutation):
    q, item = concentration_item([10, 5, 20, 30, 35])
    source = q.source_instance.model_copy(deep=True)
    if mutation in {"negative", "over100", "total"}:
        source.rows[-1][1] = SourceCell(
            number={"negative": -1, "over100": 101, "total": 40}[mutation], unit="%"
        )
    elif mutation == "few":
        source = source.model_copy(update={"rows": source.rows[:3]})
    elif mutation == "duplicate":
        source.rows[2][0] = source.rows[1][0]
    elif mutation == "unit":
        source.rows[1][1] = SourceCell(number=10, unit="1")
    elif mutation == "missing":
        source.rows[1][1] = SourceCell(text="Not supplied")
    elif mutation == "nan":
        source.rows[1][1] = source.rows[1][1].model_copy(
            update={"number": Decimal("NaN")}
        )
    elif mutation == "stale":
        source.rows[1][1] = SourceCell(number=11, unit="%")
    contract = item["authoring_context"]["economics_input_contract"]
    contract["source"] = source.model_dump(mode="json")
    if mutation != "stale":
        contract["source_fingerprint"] = source.fingerprint()
    item["stimulus"] = candidate_stimulus_data(
        q.model_copy(update={"source_instance": source})
    )
    if mutation == "candidate":
        item["stimulus"]["rows"][1][1] = "99%"
    if mutation == "prompt":
        item["prompt"] = "Calculate the two-firm concentration ratio."
    with pytest.raises(ValueError):
        IndependentSolver().solve(item, [])


def test_all_paper_three_source_page_headings_are_inside_frame(tmp_path):
    output = tmp_path / "questions.pdf"
    render_question_paper(paper(26083051), output)
    with pymupdf.open(output) as document:
        assert "Annual staff turnover" in document[1].get_text()
        for page_index, label in [
            (1, "SECTION A"),
            (2, "Extract A"),
            (3, "Extract C"),
            (17, "SECTION B"),
            (18, "Extract E"),
            (19, "Extract F"),
        ]:
            page = document[page_index]
            hits = page.search_for(label)
            assert hits, (page_index, label)
            assert hits[0].y0 >= page.rect.height - 808 + 26, (
                page_index,
                label,
                hits[0],
            )
