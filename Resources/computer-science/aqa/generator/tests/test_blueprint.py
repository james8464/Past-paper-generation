import random
import threading
import time

import pytest

from cspapergen.generator import (
    PAPER2_QUESTION_PLAN,
    QUESTION_TOTALS,
    build_paper2_blueprint,
)
from cspapergen.ollama_client import improve_questions_with_ollama
from cspapergen.question_bank import QUESTION_STYLES, STYLE_IDS, build_question
from cspapergen.syllabus import load_syllabus


def test_blueprint_is_deterministic_for_seed():
    syllabus = load_syllabus()

    first = build_paper2_blueprint(syllabus, seed=123)
    second = build_paper2_blueprint(syllabus, seed=123)

    assert first.model_dump() == second.model_dump()


def test_blueprint_totals_100_marks_and_uses_paper2_topics_only():
    syllabus = load_syllabus()
    blueprint = build_paper2_blueprint(syllabus, seed=7)

    assert blueprint.total_marks == 100
    assert sum(part.marks for question in blueprint.questions for part in question.parts) == 100
    assert [question.total_marks for question in blueprint.questions] == QUESTION_TOTALS
    assert len(blueprint.questions) == 14
    assert {question.topic_id for question in blueprint.questions} <= syllabus.topic_ids
    assert all(question.topic_id.startswith(("4.5", "4.6", "4.7", "4.8", "4.9", "4.10", "4.11", "4.12")) for question in blueprint.questions)


def test_blueprint_varies_between_unseeded_runs():
    syllabus = load_syllabus()

    first = build_paper2_blueprint(syllabus)
    second = build_paper2_blueprint(syllabus)

    assert first.model_dump() != second.model_dump()


def test_seeded_runs_keep_reference_question_styles_and_vary_content():
    syllabus = load_syllabus()

    blueprints = [build_paper2_blueprint(syllabus, seed=seed) for seed in range(40)]

    expected_styles = [style_id for style_id, _marks in PAPER2_QUESTION_PLAN]
    assert all(
        [question.style_id for question in paper.questions] == expected_styles
        for paper in blueprints
    )
    assert len({paper.model_dump_json() for paper in blueprints}) > 1


def test_paper_2_uses_reference_part_mark_pattern():
    blueprint = build_paper2_blueprint(load_syllabus(), seed=7)

    assert [
        tuple(part.marks for part in question.parts)
        for question in blueprint.questions
    ] == [marks for _style_id, marks in PAPER2_QUESTION_PLAN]


def test_all_question_styles_are_specific_to_paper2_spec_topics():
    syllabus = load_syllabus()

    assert {style.topic_id for style in QUESTION_STYLES} <= syllabus.topic_ids
    assert all(style.topic_id.startswith(("4.5", "4.6", "4.7", "4.8", "4.9", "4.10", "4.11", "4.12")) for style in QUESTION_STYLES)


def test_question_bank_covers_expected_aqa_paper2_styles():
    expected = {
        "bitmap_size",
        "sound_sampling",
        "rle_compression",
        "floating_point",
        "logic_truth_table",
        "truth_table_completion",
        "boolean_algebra",
        "processor_buses",
        "packet_switching",
        "network_topology",
        "sql_normalisation",
        "big_data",
        "functional_programming",
        "ethics_extended",
    }

    assert expected <= STYLE_IDS


def test_packet_stimulus_is_introduced_as_figure_context():
    style = next(style for style in QUESTION_STYLES if style.id == "packet_switching")

    question = build_question(style, number=6, total=10, rng=random.Random(1))

    assert "Figure 1" in question.stem
    assert "packet" in question.stem.lower()


def test_functional_type_stimulus_uses_renderable_exam_notation():
    style = next(style for style in QUESTION_STYLES if style.id == "functional_type_short")

    question = build_question(style, number=1, total=4, rng=random.Random(1))

    assert question.stimulus is not None
    assert question.stimulus.code == "f: Natural -> Real"


def test_new_visual_styles_have_renderable_stimuli():
    truth_style = next(style for style in QUESTION_STYLES if style.id == "truth_table_completion")
    network_style = next(style for style in QUESTION_STYLES if style.id == "network_topology")

    truth_question = build_question(truth_style, number=4, total=8, rng=random.Random(2))
    network_question = build_question(network_style, number=5, total=8, rng=random.Random(3))

    assert truth_question.stimulus is not None
    assert truth_question.stimulus.kind == "truth_table"
    assert truth_question.stimulus.headers == ["A", "B", "C", "X"]
    assert network_question.stimulus is not None
    assert network_question.stimulus.kind == "network"


def test_hosted_question_generation_runs_independent_prompts_concurrently():
    class HostedTestClient:
        supports_parallel_generation = True

        def __init__(self) -> None:
            self.active = 0
            self.maximum_active = 0
            self.lock = threading.Lock()

        def generate_json(self, _prompt: str) -> dict[str, object]:
            with self.lock:
                self.active += 1
                self.maximum_active = max(self.maximum_active, self.active)
            time.sleep(0.01)
            with self.lock:
                self.active -= 1
            return {}

    syllabus = load_syllabus()
    blueprint = build_paper2_blueprint(syllabus, seed=7)
    client = HostedTestClient()

    with pytest.raises(ValueError, match="only a paraphrase"):
        improve_questions_with_ollama(client, blueprint, syllabus)

    assert client.maximum_active == 4
