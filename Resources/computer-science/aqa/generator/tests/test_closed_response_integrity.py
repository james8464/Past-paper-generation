import random
from io import BytesIO

import pymupdf
import pytest
from cspapergen.generator import build_paper2_blueprint
from cspapergen.ollama_client import _part_solver_item, review_blueprint_difficulty
from cspapergen.question_bank import QUESTION_STYLES, build_question
from cspapergen.render_pdf import _draw_classification_diagram, candidate_stimulus_data
from cspapergen.syllabus import load_syllabus
from reportlab.pdfgen import canvas

from Backend.Core.independent_solver import (
    IndependentSolver,
    require_solution_matches_scheme,
)
from Backend.Core.providers import _ollama_json_schema


def classification():
    return build_paper2_blueprint(load_syllabus(), seed=26083031).questions[0]


def test_figure_exposes_same_maintenance_evidence_to_reader_and_solver():
    question = classification()
    stimulus = question.stimulus
    data = candidate_stimulus_data(stimulus)
    assert data["links"][0] == {"parent": "Software", "child": "1"}
    assert data["lines"]
    assert "backup" in " ".join(data["lines"]).lower()
    assert "malware" in " ".join(data["lines"]).lower()
    output = BytesIO()
    pdf = canvas.Canvas(output)
    _draw_classification_diagram(pdf, stimulus, 118, 700)
    pdf.save()
    with pymupdf.open(stream=output.getvalue(), filetype="pdf") as document:
        text = " ".join(document[0].get_text().split())
        for line in data["lines"]:
            assert " ".join(line.split()) in text
        assert "Application software" not in text
        assert "Utility software" not in text
        assert "1" in text and "2" in text
    assert question.parts[0].marks == 2


def test_classification_slot_contract_reaches_solver_without_answers():
    question = classification()
    item = _part_solver_item(question, question.parts[0])
    assert item["response_slots"] == ["1", "2"]
    captured = []

    class Client:
        def generate_json(self, prompt):
            captured.append(prompt)
            answer = {"1": "applications", "2": "Utility software"}
            return {"answer": answer, "mark_points": answer}

    solution = IndependentSolver(Client()).solve(item, [])
    assert "Application software" not in captured[0]
    assert "Utility software" not in captured[0]
    require_solution_matches_scheme(solution, question.parts[0].marking.model_dump())
    # The production Ollama path must allow both mapping-valued fields.
    schema = _ollama_json_schema(captured[0])
    assert schema["properties"]["answer"]["required"] == ["1", "2"]


def test_classification_final_review_rejects_swapped_slots_before_demand_review():
    calls = []

    class Client:
        def generate_json(self, prompt):
            calls.append(prompt)
            answer = {"1": "Utility software", "2": "Application software"}
            return {"answer": answer, "mark_points": answer}

    with pytest.raises(ValueError, match="slot"):
        review_blueprint_difficulty(
            Client(), build_paper2_blueprint(load_syllabus(), seed=7), load_syllabus()
        )
    assert len(calls) == 1


@pytest.mark.parametrize(
    "style_id,part_index,slots",
    [
        ("truth_table_completion", 0, ["row-1", "row-2", "row-3", "row-4"]),
        ("bitmap_storage", 0, ["result"]),
        ("bitmap_size", 0, ["result"]),
        ("floating_point", 1, ["result"]),
        ("sound_sampling", 0, ["result"]),
        ("sound_sampling", 1, ["result"]),
        ("rle_compression", 1, ["before", "after"]),
    ],
)
def test_specialist_closed_shapes_declare_required_slots(style_id, part_index, slots):
    style = next(style for style in QUESTION_STYLES if style.id == style_id)
    question = build_question(style, 1, style.totals[0], random.Random(7))
    part = question.parts[part_index]
    assert _part_solver_item(question, part)["response_slots"] == slots
    assert set(part.marking.closed_answers) == set(slots)


def test_old_figure_review_is_not_current_evidence(tmp_path):
    from cspapergen.cli import ADAPTER

    from Backend.Core.assessment_checkpoints import (
        AssessmentCheckpointStore,
        CheckpointMismatch,
        identity_for_blueprint,
    )

    blueprint = build_paper2_blueprint(load_syllabus(), seed=7)
    identity_data = ADAPTER.checkpoint_identity(blueprint, None, "2")
    current = identity_for_blueprint(
        identity_data,
        provider="ollama",
        model="test",
        prompt_version=ADAPTER.prompt_version,
    )
    old = current.model_copy(update={"prompt_version": "aqa-computer-science-v7"})
    path = tmp_path / "checkpoint.json"
    AssessmentCheckpointStore(path, old).save_payload("question-1", {"approved": True})
    with pytest.raises(CheckpointMismatch):
        AssessmentCheckpointStore(path, current)
    old_figure = blueprint.questions[0].stimulus.model_copy(update={"lines": []})
    with pytest.raises(ValueError, match="maintenance examples"):
        candidate_stimulus_data(old_figure)


@pytest.mark.parametrize(
    "answer", ["24.72 MiB", "24.72MiB", "24.71923828125 MiB", "24.71923828125MiB"]
)
def test_sound_slot_accepts_documented_exact_and_rounded_results(answer):
    # 48000 samples/s * 180 s * 24 bits * 1 channel / 8 / 1024**2.
    question = build_paper2_blueprint(load_syllabus(), seed=26083031).questions[1]

    class Client:
        def generate_json(self, prompt):
            values = {"result": answer}
            return {"answer": values, "mark_points": values}

    part = question.parts[0]
    solution = IndependentSolver(Client()).solve(_part_solver_item(question, part), [])
    require_solution_matches_scheme(solution, part.marking.model_dump())


@pytest.mark.parametrize("answer", ["24.72 MB", "24.71923828126 MiB", "24.71 MiB"])
def test_sound_slot_rejects_wrong_units_and_incorrect_exact_or_rounded_result(answer):
    question = build_paper2_blueprint(load_syllabus(), seed=26083031).questions[1]

    class Client:
        def generate_json(self, prompt):
            values = {"result": answer}
            return {"answer": values, "mark_points": values}

    part = question.parts[0]
    solution = IndependentSolver(Client()).solve(_part_solver_item(question, part), [])
    with pytest.raises(ValueError, match="slot result"):
        require_solution_matches_scheme(solution, part.marking.model_dump())
