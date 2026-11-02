"""The typed full-cell response has one complete, source-bound printed matrix."""

from copy import deepcopy

import pymupdf
import pytest
from cspapergen.generator import build_paper1_blueprint
from cspapergen.ollama_client import _part_solver_item
from cspapergen.render_pdf import _full_cell_matrix, render_mark_scheme
from cspapergen.syllabus import load_syllabus

from Backend.Core.independent_solver import IndependentSolver, reconcile_solution
from tests.support.solver_responses import complete_solver_response


def solve(question, part, answers):
    class Client:
        def generate_json(self, _prompt):
            return complete_solver_response({"answer": answers, "mark_points": answers})

    return IndependentSolver(Client()).solve(_part_solver_item(question, part), [])


def test_full_cell_contract_prints_exactly_one_complete_answer_grid(tmp_path):
    blueprint, _ = build_paper1_blueprint(load_syllabus(), seed=270100)
    before = deepcopy(blueprint.model_dump(mode="json"))
    question = blueprint.questions[2]
    part = question.parts[2]
    output = tmp_path / "scheme.pdf"
    render_mark_scheme(blueprint, output)
    with pymupdf.open(output) as pdf:
        pages = [
            page for page in pdf if "Completed adjacency matrix" in page.get_text()
        ]
        assert len(pages) == 1
        page = pages[0]
        assert "Alternative" not in page.get_text()
        cells = sorted(
            (
                drawing["rect"]
                for drawing in page.get_drawings()
                if drawing["rect"].width == pytest.approx(16)
                and drawing["rect"].height == pytest.approx(16)
            ),
            key=lambda rect: (rect.y0, rect.x0),
        )
        assert len(cells) == 49
        actual = {
            f"r{row}c{column}": page.get_textbox(cells[row * 7 + column]).strip()
            for row in range(1, 7)
            for column in range(1, 7)
        }
        expected = {
            key: values[0] for key, values in part.marking.closed_answers.items()
        }
        assert actual == expected
        assert set(actual) == set(part.response_slots)
        assert "all and only the listed edges" in page.get_text()
    assert blueprint.model_dump(mode="json") == before


def test_full_cell_solver_still_refuses_partial_and_incorrect_responses():
    blueprint, _ = build_paper1_blueprint(load_syllabus(), seed=270100)
    question = blueprint.questions[2]
    part = question.parts[2]
    answers = {key: values[0] for key, values in part.marking.closed_answers.items()}
    assert reconcile_solution(
        solve(question, part, answers), part.marking.model_dump()
    ).passed
    with pytest.raises(ValueError, match="every slot"):
        solve(
            question,
            part,
            {key: value for key, value in answers.items() if key != "r1c1"},
        )
    assert not reconcile_solution(
        solve(question, part, {**answers, "r1c2": "0"}), part.marking.model_dump()
    ).passed


@pytest.mark.parametrize("change", ["missing", "extra", "nonbinary", "duplicate_slot"])
def test_full_cell_rendering_refuses_malformed_answer_binding(change):
    blueprint, _ = build_paper1_blueprint(load_syllabus(), seed=270100)
    part = blueprint.questions[2].parts[2]
    if change == "missing":
        del part.marking.closed_answers["r1c1"]
    elif change == "extra":
        part.marking.closed_answers["r7c7"] = ["0"]
    elif change == "nonbinary":
        part.marking.closed_answers["r1c1"] = ["2"]
    else:
        part.response_slots.append("r1c1")
    with pytest.raises(ValueError, match="bind every binary cell"):
        _full_cell_matrix(part)
