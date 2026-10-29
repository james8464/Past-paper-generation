# The unpublished fifth family must coexist without relaxing similarity rules.

import ast
import re

import pytest

from Backend.Core.france import (
    allocation_exercise,
    channel_exercise,
    directory_exercise,
)
from Backend.Core.france.extended_pipeline import _source
from Backend.Core.france.nsi import NSIExercise
from Backend.Core.france.originality import SimilarityRejected, screen_originality
from Backend.Core.france.pipeline import exercise_candidate_text

MODULES = (directory_exercise, allocation_exercise, channel_exercise)


def test_fifth_family_is_distinct_from_all_twelve_retained_exercises():
    history = [
        exercise_candidate_text(NSIExercise.model_validate(exercise))
        for seed in range(270100, 270104)
        for exercise in _source(seed)[2]
    ]
    for module in MODULES:
        exercise = NSIExercise.model_validate(module.render_case(270104))
        candidate = exercise_candidate_text(exercise)
        result = screen_originality(candidate, [], previous_texts=history)
        assert result["state"] == "passed_calibrated_screen"
        history.append(candidate)
        with pytest.raises(SimilarityRejected):
            screen_originality(candidate, [], previous_texts=history)
    assert len(history) == 15


@pytest.mark.parametrize("module", MODULES)
def test_correction_code_is_syntactically_complete_and_has_no_blank_tokens(module):
    raw = module.render_case(270104)
    for question in raw["questions"]:
        assert not re.search(r"__[A-Z]__", question["answer"])
        for source in re.findall(r"```python\n(.*?)\n```", question["answer"], re.S):
            ast.parse(source)


def test_all_sustained_algorithm_scaffolds_have_real_blanks():
    for module, index in [
        (directory_exercise, 9),
        (allocation_exercise, 7),
        (channel_exercise, 5),
    ]:
        prompt = module.render_case(270104)["questions"][index]["prompt"]
        assert "__A__" in prompt
        assert "__B__" in prompt
        assert "__C__" in prompt
