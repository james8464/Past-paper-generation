import pytest

from Backend.Core.shared_source_scope import (
    shared_source_requires_context,
    uses_shared_option_source,
)


@pytest.mark.parametrize("option", [{}, {"title": ""}, {"title": " "}])
def test_missing_or_blank_title_does_not_create_a_source_dependency(option):
    question = {"kind": "short_answer", "prompt": "Explain  caching."}
    assert uses_shared_option_source(question, option) is False
    assert shared_source_requires_context(question, option) is False


@pytest.mark.parametrize(
    "question",
    [
        {"prompt": "Use the information provided to explain the change."},
        {"prompt": "Explain caching.", "source_references": ["Extract A"]},
        {
            "prompt": "Explain caching.",
            "authoring_context": {"source_data": {"rate": 10}},
        },
    ],
)
def test_explicit_shared_source_cues_survive_a_blank_title(question):
    assert shared_source_requires_context(question, {"title": ""}) is True


def test_nonempty_case_title_still_binds_its_named_prompt():
    question = {"kind": "short_answer", "prompt": "Assess growth at Willow Components."}
    assert uses_shared_option_source(question, {"title": "Willow Components"}) is True
