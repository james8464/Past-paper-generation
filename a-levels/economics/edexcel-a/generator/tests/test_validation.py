from pathlib import Path

import pytest

from pastpapergen.generator import build_paper_blueprint
from pastpapergen.models import QuestionBlueprint
from pastpapergen.paper_configs import load_builtin_paper_config
from pastpapergen.syllabus import load_syllabus
from pastpapergen.validation import validate_blueprint


def test_validate_blueprint_accepts_generated_paper():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=1)

    validate_blueprint(blueprint, config, syllabus)


def test_validate_blueprint_rejects_topic_outside_paper_themes():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=1)
    bad_question = blueprint.questions[0].model_copy(update={"topic_id": "2.1"})
    bad_blueprint = blueprint.model_copy(
        update={"questions": [bad_question, *blueprint.questions[1:]]}
    )

    with pytest.raises(ValueError, match="not allowed"):
        validate_blueprint(bad_blueprint, config, syllabus)


def test_validate_blueprint_rejects_unstructured_mcq():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=1)
    first = blueprint.questions[0]
    bad_parts = [
        part.model_copy(update={"options": [], "correct_option": ""}) if part.marks == 1 else part
        for part in first.parts
    ]
    bad_blueprint = blueprint.model_copy(
        update={"questions": [first.model_copy(update={"parts": bad_parts}), *blueprint.questions[1:]]}
    )

    with pytest.raises(ValueError, match="MCQ"):
        validate_blueprint(bad_blueprint, config, syllabus)


def test_validate_blueprint_rejects_llm_mark_text_in_prompt():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=1)
    bad_question = blueprint.questions[0].model_copy(update={"prompt": "Explain something. (4 marks)"})
    bad_blueprint = blueprint.model_copy(update={"questions": [bad_question, *blueprint.questions[1:]]})

    with pytest.raises(ValueError, match="marks text"):
        validate_blueprint(bad_blueprint, config, syllabus)
