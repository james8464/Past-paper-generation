from cspapergen.generator import build_paper2_blueprint
from cspapergen.question_bank import STYLE_IDS
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
