"""Versioned question markers precede unchanged code-first prompts."""

import pytest

from Backend.Core.france.llm_pdf import validate_llm_pdf
from Backend.Core.france.llm_pipeline import validate_authored_exercise
from tests.test_french_llm_pdf import exercises, render
from tests.test_french_llm_pipeline import raw_exercise


@pytest.mark.parametrize("large_print", [False, True])
@pytest.mark.parametrize("code_only", [False, True])
@pytest.mark.parametrize("correction", [False, True])
def test_code_first_question_number_precedes_listing(
    tmp_path, large_print, code_only, correction
):
    raw = raw_exercise()
    raw["questions"][0]["prompt"] = (
        "```python\nx = 1\n# Donnez la valeur finale de x.\n```"
    )
    if not code_only:
        raw["questions"][0]["prompt"] += "\nQuelle est la valeur finale de x ?"
    first = validate_authored_exercise(raw, "1", large_print=large_print)
    source = [first, *exercises()[1:]]
    path = tmp_path / "code-first-v2.pdf"
    render(path, source, large_print=large_print, correction=correction)
    validate_llm_pdf(path, source, correction=correction, large_print=large_print)


def test_native_expected_policy_matches_current_backend():
    from pathlib import Path

    from Backend.Core.france.llm_pipeline import PRINT_POLICY
    from Backend.Core.france.print_policy import (
        INTERNAL_REVIEW_POLICIES,
        V36_LEGACY_PRINT_POLICY,
    )

    text = (
        Path(__file__).resolve().parents[1]
        / "macOS/Keldin/Domain/FrenchLLMAssessmentRequest.swift"
    ).read_text()
    assert f'static let printPolicy = "{PRINT_POLICY}"' in text
    assert PRINT_POLICY != V36_LEGACY_PRINT_POLICY
    assert V36_LEGACY_PRINT_POLICY in INTERNAL_REVIEW_POLICIES
