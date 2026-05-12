import random

from cspapergen.generator import build_paper2_blueprint
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
    assert {question.topic_id for question in blueprint.questions} <= syllabus.topic_ids
    assert all(question.topic_id.startswith(("4.5", "4.6", "4.7", "4.8", "4.9", "4.10", "4.11", "4.12")) for question in blueprint.questions)


def test_blueprint_varies_between_unseeded_runs():
    syllabus = load_syllabus()

    first = build_paper2_blueprint(syllabus)
    second = build_paper2_blueprint(syllabus)

    assert first.model_dump() != second.model_dump()


def test_seeded_runs_randomise_first_and_final_question_styles():
    syllabus = load_syllabus()

    blueprints = [build_paper2_blueprint(syllabus, seed=seed) for seed in range(40)]

    assert len({paper.questions[0].style_id for paper in blueprints}) > 1
    assert len({paper.questions[-1].style_id for paper in blueprints}) > 1


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
        "boolean_algebra",
        "processor_buses",
        "packet_switching",
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
