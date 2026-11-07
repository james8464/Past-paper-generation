from __future__ import annotations

import hashlib
import json
import re
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pymupdf as fitz
import pytest
from ocregen import render_pdf as renderer
from ocregen.configs import RULES
from ocregen.generator import build_paper
from ocregen.syllabus import load_syllabus
from reportlab.pdfbase import pdfmetrics

from Backend.Core.exam_blueprints import validate_rule
from Backend.Core.independent_solver import IndependentSolver, reconcile_solution

ROOT = Path(__file__).resolve().parents[1]
SYLLABUS = load_syllabus(ROOT / "data/syllabus.json")
BASELINE = {
    "paper_1": "c6c15ba5e70c3be2dafe8705dda1ad4f9ca2f7ec85e4d0694f498308885ad008",
    "paper_2": "028a595359e0c7a01c04368ba93137f7cdbcad3c35fdd49fadb544505eff7832",
    "paper_3": "72fa957d773bd11bfb6513513f8393e3969b96c1943c772d0305257796c4a076",
}


def _questions(paper):
    return [q for s in paper.sections for o in s.options for q in o.questions]


def _plain(value):
    if isinstance(value, (list, tuple)):
        return [text for part in value for text in _plain(part)]
    return [value.getPlainText() if hasattr(value, "getPlainText") else str(value)]


def _compact(text):
    return re.sub(r"\s+", "", text)


@pytest.fixture(params=list(RULES), scope="module")
def paper_and_pdfs(request, tmp_path_factory):
    assert Path(renderer.__file__).resolve() == ROOT / "ocregen/render_pdf.py"
    paper = build_paper(RULES[request.param], SYLLABUS, 123)
    snapshot = paper.model_dump(mode="json")
    directory = tmp_path_factory.mktemp(request.param)
    question_path = directory / "questions.pdf"
    scheme_path = directory / "scheme.pdf"
    renderer.render_question_paper(paper, question_path)
    renderer.render_mark_scheme(paper, scheme_path)
    assert paper.model_dump(mode="json") == snapshot
    return paper, question_path, scheme_path


def test_existing_source_levels_are_the_only_printed_bands(paper_and_pdfs):
    paper, _, path = paper_and_pdfs
    for question in _questions(paper):
        table = renderer._scheme_block(question)[0]
        printed = _plain(table._cellvalues)
        source = list(
            dict.fromkeys(
                [
                    *question.mark_scheme,
                    *(point.text for point in question.structured_mark_scheme),
                ]
            )
        )
        for point in source:
            assert point in printed, (question.number, point)
        expected_levels = [point for point in source if point.startswith("Level ")]
        actual_levels = [point for point in printed if point.startswith("Level ")]
        assert actual_levels == expected_levels, question.number
        if expected_levels:
            credited = []
            for point in expected_levels:
                band = re.match(r"Level \d+ \((\d+)[–-](\d+)\)", point)
                if band:
                    credited.extend(range(int(band[1]), int(band[2]) + 1))
            assert sorted(credited) == list(range(1, question.marks + 1))
    with fitz.open(path) as document:
        text = _compact("\n".join(page.get_text() for page in document))
    if paper.paper_id == "paper_3":
        assert "Level4(13–15):" in text
        assert "Level3(9–12marks):" not in text


def test_actual_cover_matches_compulsory_and_optional_sections(paper_and_pdfs):
    paper, path, _ = paper_and_pdfs
    compulsory = all(s.answer_options == len(s.options) for s in paper.sections)
    expected = (
        "Answer all questions."
        if compulsory
        else "Answer all questions in Section A and one question in Sections B and C."
    )
    with fitz.open(path) as document:
        cover = " ".join(document[0].get_text().split())
    assert expected in cover
    if compulsory:
        assert "Sections B and C" not in cover


def test_annotation_credit_label_is_legible_text_in_actual_pdf(paper_and_pdfs):
    _, _, path = paper_and_pdfs
    with fitz.open(path) as document:
        page = next(
            page for page in document if "ANNOTATION CONVENTIONS" in page.get_text()
        )
        labels = page.search_for("Tick")
        meaning = page.search_for("Creditworthy point")
        assert len(labels) == len(meaning) == 1
        assert labels[0].x1 < meaning[0].x0
        assert labels[0].y0 == pytest.approx(meaning[0].y0, abs=1)
    table = renderer._annotation_conventions_page()[-1]
    assert _plain([row[0] for row in table._cellvalues[1:]]) == [
        "Tick",
        "DEV",
        "APP",
        "EVAL",
        "J",
        "BOD",
        "ECF",
        "REP",
        "CON",
        "MAX",
        "0",
        "NR",
    ]


def test_assessed_scheme_has_no_spacer_only_page_before_appendices(paper_and_pdfs):
    _, _, path = paper_and_pdfs
    with fitz.open(path) as document:
        for index in range(10, len(document) - 1):
            page = document[index]
            body = page.get_text(clip=fitz.Rect(30, 45, 800, page.rect.height - 35))
            assert re.search(r"[A-Za-z]", body), index + 1


def test_compulsory_cover_selection_is_not_a_paper_id_switch():
    paper = build_paper(RULES["paper_1"], SYLLABUS, 123)
    for section in paper.sections:
        section.answer_options = len(section.options)
    assert "Answer all questions." in renderer._cover_profile(paper).instructions


@pytest.mark.parametrize(
    "allocation", [{}, {"AO1": 1}, {"AO9": 2}, {"AO1": True, "AO2": 1}]
)
def test_missing_or_invalid_legacy_ao_metadata_is_not_guessed(allocation):
    paper = build_paper(RULES["paper_1"], SYLLABUS, 123)
    question = _questions(paper)[0].model_copy(
        update={"assessment_objectives": allocation}
    )
    with pytest.raises(ValueError, match="validated AO allocation"):
        renderer._assessment_allocation(question)


def test_ao_rows_and_actual_pdf_use_exact_validated_allocations(paper_and_pdfs):
    paper, _, path = paper_and_pdfs
    questions = _questions(paper)
    table = renderer._assessment_objectives_page(paper, questions)[-1]
    rows = table._cellvalues
    source_groups = [[q] for q in questions]
    if paper.paper_id == "paper_3":
        source_groups = [questions[:30], *[[q] for q in questions[30:]]]
    else:
        source_groups = [[q] for q in questions[:6]] + [[questions[6]], [questions[8]]]
    for row, group in zip(rows[1:-1], source_groups, strict=True):
        expected = [
            sum(q.assessment_objectives.get(ao, 0) for q in group)
            for ao in ("AO1", "AO2", "AO3", "AO4")
        ]
        assert [int(value or 0) for value in row[1:5]] == expected, row[0]
    with fitz.open(path) as document:
        grid = _compact(document[-2].get_text())
    if paper.paper_id == "paper_3":
        assert "1–30157830" in grid


def test_chart_title_does_not_invent_a_base_year(paper_and_pdfs):
    paper, path, _ = paper_and_pdfs
    if paper.paper_id != "paper_3":
        return
    with fitz.open(path) as document:
        text = "\n".join(page.get_text() for page in document)
    assert "2019 = 100" not in text
    assert "index points" in text
    figures = [
        q.authoring_context["figure"] for q in paper.sections[1].options[0].questions
    ]
    assert any(
        series["values"][0] != 100 for figure in figures for series in figure["series"]
    )
    for figure in figures:
        assert "2019 = 100" not in figure["title"]
        assert "index points" in figure["title"]


def test_entire_blueprint_unchanged_except_owned_figure_titles_and_resolved_timing(
    paper_and_pdfs,
):
    paper, _, _ = paper_and_pdfs
    data = paper.model_dump(mode="json")
    for section in data["sections"]:
        for option in section["options"]:
            for question in option["questions"]:
                if question["kind"] != "multiple_choice":
                    expected = round(
                        paper.duration_minutes * question["marks"] / paper.total_marks,
                        2,
                    )
                    assert (
                        question["authoring_context"]["completion_time_minutes"]
                        == question["expected_minutes"]
                        == expected
                    )
                    # The pre-repair cold build enriched before rule validation;
                    # only this diagnosed timing field was incorrectly None.
                    question["authoring_context"]["completion_time_minutes"] = None
    if paper.paper_id == "paper_3":
        for section in data["sections"]:
            for option in section["options"]:
                if "(index points)" in option["chart_title"]:
                    option["chart_title"] = option["chart_title"].replace(
                        "(index points)", "(2019 = 100)"
                    )
                for question in option["questions"]:
                    figure = question["authoring_context"].get("figure")
                    if figure:
                        assert figure["title"].endswith("(index points)")
                        figure["title"] = figure["title"].replace(
                            "(index points)", "(2019 = 100)"
                        )
    digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    assert digest == BASELINE[paper.paper_id]


@pytest.mark.parametrize("paper_id", list(RULES))
def test_cold_warm_and_repeated_builds_match_without_mutating_rule(paper_id):
    cold = RULES[paper_id].model_copy(deep=True)
    for section in cold.sections:
        for rules in [section.questions, *section.question_overrides.values()]:
            for question in rules:
                # These are the declared optional defaults in the built-in rules.
                question.expected_minutes = None
                question.intended_demand = None
    warm = cold.model_copy(deep=True)
    validate_rule(warm, SYLLABUS.topic_ids)
    cold_snapshot = cold.model_dump(mode="json")
    warm_snapshot = warm.model_dump(mode="json")
    first = build_paper(cold, SYLLABUS, 123).model_dump(mode="json")
    repeated = build_paper(cold, SYLLABUS, 123).model_dump(mode="json")
    prevalidated = build_paper(warm, SYLLABUS, 123).model_dump(mode="json")
    assert first == repeated == prevalidated
    assert cold.model_dump(mode="json") == cold_snapshot
    assert warm.model_dump(mode="json") == warm_snapshot


def test_nondefault_rule_timing_and_demand_are_preserved():
    rule = RULES["paper_1"].model_copy(deep=True)
    rule.sections[0].questions[0].expected_minutes = 7.25
    rule.sections[0].questions[0].intended_demand = "high"
    snapshot = rule.model_dump(mode="json")
    paper = build_paper(rule, SYLLABUS, 123)
    question = _questions(paper)[0]
    assert question.expected_minutes == 7.25
    assert question.authoring_context["completion_time_minutes"] == 7.25
    assert question.intended_demand == "high"
    assert rule.model_dump(mode="json") == snapshot


def test_invalid_rule_is_rejected_without_mutating_its_defaults():
    rule = RULES["paper_1"].model_copy(deep=True)
    rule.total_marks += 1
    snapshot = rule.model_dump(mode="json")
    with pytest.raises(ValueError, match="candidate marks total"):
        build_paper(rule, SYLLABUS, 123)
    assert rule.model_dump(mode="json") == snapshot


def test_actual_seed_fifteen_half_tie_matches_typed_answer_and_print(tmp_path):
    paper = build_paper(RULES["paper_1"], SYLLABUS, 15)
    question = next(q for q in _questions(paper) if q.kind == "calculation")
    assert question.authoring_context["calculation_variables"] == {
        "start": 88.0,
        "end": 86.9,
    }
    assert "Correct answer: −1.3%." in question.mark_scheme
    solution = IndependentSolver().solve(question, [])
    assert reconcile_solution(solution, question).passed
    incorrect = question.model_copy(update={"mark_scheme": ["Correct answer: -1.2%."]})
    assert not reconcile_solution(solution, incorrect).passed
    path = tmp_path / "half-tie-scheme.pdf"
    renderer.render_mark_scheme(paper, path)
    with fitz.open(path) as document:
        text = _compact("\n".join(page.get_text() for page in document))
    assert "Correctanswer:−1.3%." in text


def test_first_128_legal_seeds_use_exact_half_up_calculation():
    checked = 0
    for seed in range(128):
        for rule in RULES.values():
            paper = build_paper(rule, SYLLABUS, seed)
            for question in _questions(paper):
                if question.kind != "calculation":
                    continue
                checked += 1
                values = question.authoring_context["calculation_variables"]
                start, end = (Decimal(str(values[key])) for key in ("start", "end"))
                expected = ((end - start) / start * 100).quantize(
                    Decimal("0.1"), rounding=ROUND_HALF_UP
                )
                printed = [point.replace("−", "-") for point in question.mark_scheme]
                assert f"Correct answer: {expected:.1f}%." in printed
                assert any(point.endswith(f"= {expected:.1f}%.") for point in printed)
    assert checked == 384


@pytest.fixture(params=[True, False])
def shifted_diagram(request):
    compact = request.param
    paper = build_paper(RULES["paper_1"], SYLLABUS, 15)
    question = next(q for q in _questions(paper) if q.kind == "diagram_analysis")
    assert question.topic_id == "micro-6"
    drawing = renderer.Drawing(
        98 * renderer.mm if compact else 245 * renderer.mm,
        70 * renderer.mm if compact else 76 * renderer.mm,
    )
    geometry = dict(
        x0=18 if compact else 388,
        y0=18 if compact else 38,
        width=235 if compact else 250,
        height=63 if compact else 145,
        compact=compact,
    )
    renderer._add_economics_diagram(drawing, question, shifted=True, **geometry)
    return drawing, question, geometry


def test_shifted_guide_ends_at_actual_drawn_curve_intersection(shifted_diagram):
    drawing, _, geometry = shifted_diagram
    lines = [part for part in drawing.contents if isinstance(part, renderer.Line)]
    demand = next(line for line in lines if line.x2 > line.x1 and line.y2 < line.y1)
    supplies = [line for line in lines if line.x2 > line.x1 and line.y2 > line.y1]
    shifted_supply = max(supplies, key=lambda line: line.x1)
    guide = next(
        line for line in lines if line.x1 == line.x2 and line.x1 != geometry["x0"]
    )
    for curve in (demand, shifted_supply):
        y = curve.y1 + (guide.x1 - curve.x1) * (curve.y2 - curve.y1) / (
            curve.x2 - curve.x1
        )
        assert guide.y2 == pytest.approx(y, abs=1e-8)


def test_shifted_labels_clear_curves_and_each_other(shifted_diagram):
    drawing, question, geometry = shifted_diagram
    labels = [
        part
        for part in drawing.contents
        if isinstance(part, renderer.String) and part.text in {"MPC", "MSC", "E1"}
    ]
    assert len(labels) == 3
    bounds = []
    for label in labels:
        ascent, descent = pdfmetrics.getAscentDescent(label.fontName, label.fontSize)
        box = fitz.Rect(
            label.x,
            label.y + descent,
            label.x
            + pdfmetrics.stringWidth(label.text, label.fontName, label.fontSize),
            label.y + ascent,
        )
        assert fitz.Rect(0, 0, drawing.width, drawing.height).contains(box)
        for part in drawing.contents:
            if not isinstance(part, renderer.Line) or part.x2 <= part.x1:
                continue
            left, right = max(box.x0, part.x1), min(box.x1, part.x2)
            if left > right:
                continue
            ys = [
                part.y1 + (x - part.x1) * (part.y2 - part.y1) / (part.x2 - part.x1)
                for x in (left, right)
            ]
            half_stroke = part.strokeWidth / 2
            assert max(ys) + half_stroke < box.y0 or min(ys) - half_stroke > box.y1, (
                label.text
            )
        bounds.append(box)
    for index, box in enumerate(bounds):
        assert not any(box.intersects(other) for other in bounds[index + 1 :])
    # The unshifted diagram's established label position must remain unchanged.
    unshifted = renderer.Drawing(drawing.width, drawing.height)
    renderer._add_economics_diagram(unshifted, question, shifted=False, **geometry)
    label = next(
        part
        for part in unshifted.contents
        if isinstance(part, renderer.String) and part.text == "MPC"
    )
    inset = 10 if geometry["compact"] else 18
    assert (label.x, label.y) == (
        geometry["x0"] + geometry["width"] - inset + 1,
        geometry["y0"] + geometry["height"] - inset - 2,
    )
