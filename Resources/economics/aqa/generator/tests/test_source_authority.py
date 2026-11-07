from __future__ import annotations

import random
from copy import deepcopy
from pathlib import Path

import pytest
from aqaecongen import generator, render_pdf
from aqaecongen.configs import RULES
from aqaecongen.syllabus import load_syllabus
from aqaecongen.written_tasks import PROFILES
from reportlab.graphics.shapes import Line, PolyLine, String

from Backend.Core.assessment_package import _extract_items
from Backend.Core.independent_solver import IndependentSolver, reconcile_solution

SYLLABUS = load_syllabus(Path(__file__).parents[1] / "data/syllabus.json")


def test_seeded_public_calculation_agrees_with_its_output_contract():
    paper = generator.build_paper(RULES["paper_1"], SYLLABUS, seed=72)
    before = deepcopy(paper.model_dump(mode="json"))
    option = paper.sections[0].options[0]
    question = option.questions[0]
    assert option.chart_values == [88.0, 99.4, 112.3, 113.4, 111.1]
    assert question.authoring_context["calculation_variables"] == {
        "start": 88.0,
        "end": 111.1,
    }
    assert "((111.1 − 88.0) ÷ 88.0) × 100" in question.mark_scheme[0]
    solution = IndependentSolver().solve(question.model_dump(mode="json"), [])
    assert solution.answer_slots == {"percentage_change": "26.3%"}
    assert reconcile_solution(solution, question).passed
    assert "Correct answer: 26.3%." in question.mark_scheme
    exported = _extract_items(before, subject="economics_aqa", paper_number="1")[0]
    assert "Correct answer: 26.3%." in exported["mark_scheme"]
    assert reconcile_solution(solution, exported).passed
    stale = question.model_copy(update={"mark_scheme": ["Correct answer: 26.2%."]})
    assert not reconcile_solution(solution, stale).passed
    assert paper.model_dump(mode="json") == before


@pytest.mark.parametrize(
    ("start", "end", "answer"),
    [
        (80.0, 80.6, "0.8%"),
        (80.0, 79.4, "−0.8%"),
        (100.0, 105.0, "5.0%"),
        (100.0, 100.0, "0.0%"),
    ],
)
def test_calculation_and_indicative_content_share_the_numeric_display(
    start, end, answer
):
    topic = next(topic for topic in SYLLABUS.topics if topic.id == "4.1.3")
    profile = PROFILES[topic.id]
    values = [start, end]
    question = generator._written_question(
        RULES["paper_1"].sections[0].questions[0],
        "1",
        topic,
        "rail freight",
        1234,
        values,
        random.Random(1),
        is_data=True,
        paper_id="paper_1",
        task_profile=profile,
    )
    solution = IndependentSolver().solve(question.model_dump(mode="json"), [])
    assert solution.answer_slots == {"percentage_change": answer}
    assert f"Correct answer: {answer}." in question.mark_scheme
    indicative = generator._paper_three_indicative_content(
        topic,
        "rail freight",
        1234,
        values,
        "demand",
        include_evaluation=False,
    )
    assert f"equivalent to {answer}," in indicative[0]
    assert values == [start, end]


def _on_curve(point, curve):
    x1, y1, x2, y2 = curve.points
    x, y = point
    assert (x - x1) * (y2 - y1) == pytest.approx((y - y1) * (x2 - x1))
    assert min(x1, x2) <= x <= max(x1, x2)
    assert min(y1, y2) <= y <= max(y1, y2)


def test_externality_guides_end_at_both_actual_drawn_curves():
    contract = deepcopy(PROFILES["4.1.8"].diagram_contract)
    before = deepcopy(contract)
    drawing = render_pdf._economic_diagram("4.1.8", "3", contract)
    msb, mpc, msc = [item for item in drawing.contents if isinstance(item, PolyLine)]
    guides = [
        item
        for item in drawing.contents
        if isinstance(item, Line) and item.strokeDashArray == [3, 3]
    ]
    assert len(guides) == 2
    social, market = guides
    assert social.x1 == social.x2 < market.x1 == market.x2
    assert social.y1 == market.y1 == 28
    for guide, cost in ((social, msc), (market, mpc)):
        _on_curve((guide.x2, guide.y2), msb)
        _on_curve((guide.x2, guide.y2), cost)
    labels = {item.text: item for item in drawing.contents if isinstance(item, String)}
    assert labels["Q*"].x + 7 == social.x1
    assert labels["Qm"].x + 7 == market.x1
    assert {"MSB", "MPC", "MSC", "Q*", "Qm"} <= labels.keys()
    assert contract == before


def test_generated_expected_diagram_uses_the_bound_source_without_mutation(monkeypatch):
    paper = generator.build_paper(RULES["paper_1"], SYLLABUS, seed=6)
    before = deepcopy(paper.model_dump(mode="json"))
    question = paper.sections[0].options[1].questions[2]
    assert question.topic_id == "4.1.8" and question.kind == "diagram_analysis"
    original = render_pdf._economic_diagram
    captured = []

    def capture(topic_id, number, visual):
        drawing = original(topic_id, number, visual)
        captured.append(drawing)
        return drawing

    monkeypatch.setattr(render_pdf, "_economic_diagram", capture)
    render_pdf._scheme_question_page(question, segment=2, segment_count=2)
    assert len(captured) == 1
    curves = [item for item in captured[0].contents if isinstance(item, PolyLine)]
    guides = [
        item
        for item in captured[0].contents
        if isinstance(item, Line) and item.strokeDashArray == [3, 3]
    ]
    for guide, cost in zip(guides, (curves[2], curves[1]), strict=True):
        _on_curve((guide.x2, guide.y2), curves[0])
        _on_curve((guide.x2, guide.y2), cost)
    assert paper.model_dump(mode="json") == before


@pytest.mark.parametrize(
    ("first", "second", "message"),
    [
        ([0, 0, 1, 1], [0, 1, 1, 2], "no unique intersection"),
        ([0, 0, 1, 1], [2, 0, 2, 1], "outside drawn segments"),
    ],
)
def test_intersection_refuses_non_intersecting_segments(first, second, message):
    with pytest.raises(ValueError, match=message):
        render_pdf._line_intersection(first, second)


@pytest.mark.parametrize(
    ("topic_id", "first_curve"),
    [
        ("4.1.1", [86, 129, 168, 120, 248, 96, 316, 59]),
        ("4.1.7", [78, 28, 358, 133]),
        ("4.1.3", [133, 44, 353, 132]),
        ("4.1.6", [133, 44, 353, 132]),
        ("4.2.2", [133, 44, 353, 132]),
        ("4.2.5", [133, 130, 353, 44]),
    ],
)
def test_other_economic_diagram_kinds_keep_their_curve_operations(
    topic_id, first_curve
):
    contract = deepcopy(PROFILES[topic_id].diagram_contract)
    before = deepcopy(contract)
    drawing = render_pdf._economic_diagram(topic_id, "3", contract)
    curves = [item for item in drawing.contents if isinstance(item, PolyLine)]
    assert curves[0].points == first_curve
    assert not any(
        isinstance(item, Line) and item.strokeDashArray == [3, 3]
        for item in drawing.contents
    )
    assert contract == before
