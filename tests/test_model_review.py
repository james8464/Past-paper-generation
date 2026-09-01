from __future__ import annotations

import pytest

from Backend.Core import model_review
from Backend.Core.model_review import (
    ReviewResult,
    independent_review,
    require_independent_review,
)


class ReviewClient:
    def __init__(self, response: dict[str, object]) -> None:
        self.response = response
        self.prompt = ""

    def generate_json(self, prompt: str) -> dict[str, object]:
        self.prompt = prompt
        return self.response


@pytest.mark.parametrize("field", list(ReviewResult.model_fields))
@pytest.mark.parametrize("mutation", ["missing", "null", "wrong_type"])
def test_live_content_review_requires_every_explicit_strict_check(field, mutation):
    response = ReviewResult(approved=True).model_dump()
    if mutation == "missing":
        del response[field]
    else:
        response[field] = None if mutation == "null" else (
            "true" if field == "approved" else "clear"
        )
    with pytest.raises(ValueError, match="invalid review response"):
        independent_review(ReviewClient(response), item_id="q", subject="Economics",
                           blueprint={}, candidate={}, specification={})


@pytest.mark.parametrize("bad", [1, [], {}, [None], [1]])
def test_live_content_review_rejects_invalid_issue_members(bad):
    response = ReviewResult(approved=True).model_dump()
    response["source_issues"] = bad
    if bad == []:
        response["approved"] = 1
    with pytest.raises(ValueError, match="invalid review response"):
        independent_review(ReviewClient(response), item_id="q", subject="Economics",
                           blueprint={}, candidate={}, specification={})


def test_live_content_review_rejects_extra_raw_fields() -> None:
    response = ReviewResult(approved=True).model_dump()
    response["confidence"] = 0.9
    with pytest.raises(ValueError, match="invalid review response"):
        independent_review(
            ReviewClient(response), item_id="q", subject="Economics",
            blueprint={}, candidate={}, specification={},
        )


@pytest.mark.parametrize(
    "missing",
    ["observed_cognitive_operations", "cognitive_operations_fit", "reasoning_range_fit",
     "shortcut_resistant", "timing_fit", "scaffolding_fit", "estimated_minutes"],
)
def test_live_difficulty_response_must_explicitly_include_every_check(missing) -> None:
    response = model_review.DifficultyReviewResult(
        approved=True, estimated_demand="low", reasoning_steps=1,
        tariff_fit=True, command_word_fit=True, context_fit=True, profile_fit=True,
        observed_cognitive_operations=["retrieve"], estimated_minutes=1.5,
    ).model_dump(mode="json")
    del response[missing]
    with pytest.raises(ValueError, match="invalid difficulty review response"):
        model_review.difficulty_review(
            ReviewClient(response), item_id="q1", subject="Accounting",
            target={}, candidate={}, specification={},
        )


def test_live_difficulty_response_rejects_extra_raw_fields() -> None:
    response = model_review.DifficultyReviewResult(
        approved=True, estimated_demand="low", reasoning_steps=1,
        tariff_fit=True, command_word_fit=True, context_fit=True, profile_fit=True,
        observed_cognitive_operations=["retrieve"], estimated_minutes=1.5,
    ).model_dump(mode="json")
    response["confidence"] = 0.9
    with pytest.raises(ValueError, match="invalid difficulty review response"):
        model_review.difficulty_review(
            ReviewClient(response), item_id="q1", subject="Economics",
            target={}, candidate={}, specification={},
        )


def test_independent_review_returns_structured_repair_diagnostics() -> None:
    client = ReviewClient(
        {
            "approved": False,
            "factual_issues": ["The exchange-rate direction is reversed."],
            "marking_issues": [],
            "source_issues": [],
            "difficulty_issues": [],
            "ambiguity_issues": [],
        }
    )
    result = independent_review(
        client,
        item_id="q1",
        subject="Economics",
        blueprint={"marks": 4},
        candidate={"prompt": "Explain the effect."},
        specification={"topic": "exchange rates"},
    )

    assert result == ReviewResult(
        approved=False,
        factual_issues=["The exchange-rate direction is reversed."],
    )
    assert result.issues == ["The exchange-rate direction is reversed."]
    assert "Semantically equivalent original wording is expected" in client.prompt


def test_require_independent_review_preserves_rejecting_wrapper_behavior() -> None:
    client = ReviewClient(
        {
            "approved": False,
            "factual_issues": [],
            "marking_issues": [],
            "source_issues": [],
            "difficulty_issues": [],
            "ambiguity_issues": [],
        }
    )

    with pytest.raises(ValueError, match="not approved"):
        require_independent_review(
            client,
            item_id="q1",
            subject="Economics",
            blueprint={},
            candidate={},
            specification={},
        )


def test_independent_review_rejects_approval_with_reported_issues() -> None:
    result = independent_review(
        ReviewClient(
            {
                "approved": True,
                "factual_issues": [],
                "marking_issues": ["The scheme cannot award all four marks."],
                "source_issues": [],
                "difficulty_issues": [],
                "ambiguity_issues": [],
            }
        ),
        item_id="q1",
        subject="Economics",
        blueprint={},
        candidate={},
        specification={},
    )

    assert result.approved is False
    assert result.marking_issues == ["The scheme cannot award all four marks."]


def test_difficulty_review_is_a_separate_structured_judgement() -> None:
    client = ReviewClient(
        {
            "approved": False,
            "estimated_demand": "low",
            "reasoning_steps": 1,
            "tariff_fit": False,
            "command_word_fit": False,
            "context_fit": True,
            "profile_fit": False,
            "observed_cognitive_operations": ["retrieve"],
            "cognitive_operations_fit": False,
            "reasoning_range_fit": False,
            "shortcut_resistant": False,
            "timing_fit": False,
            "scaffolding_fit": False,
            "estimated_minutes": 2.0,
            "issues": ["The response requires recall only, not evaluation."],
        }
    )

    result = model_review.difficulty_review(
        client,
        item_id="q8",
        subject="Economics",
        target={
            "demand_band": "high",
            "minimum_reasoning_steps": 4,
            "requires_judgement": True,
        },
        candidate={"prompt": "State one effect.", "marks": 15},
        specification={"topic": "market failure"},
    )

    assert result == model_review.DifficultyReviewResult(
        approved=False,
        estimated_demand="low",
        reasoning_steps=1,
        tariff_fit=False,
        command_word_fit=False,
        context_fit=True,
        profile_fit=False,
        observed_cognitive_operations=["retrieve"],
        cognitive_operations_fit=False,
        reasoning_range_fit=False,
        shortcut_resistant=False,
        timing_fit=False,
        scaffolding_fit=False,
        estimated_minutes=2.0,
        issues=["The response requires recall only, not evaluation."],
    )
    assert "difficulty calibration specialist" in client.prompt
    assert "factual correctness is reviewed separately" in client.prompt


def test_require_difficulty_review_rejects_under_demanded_item() -> None:
    client = ReviewClient(
        {
            "approved": True,
            "estimated_demand": "standard",
            "reasoning_steps": 2,
            "tariff_fit": True,
            "command_word_fit": True,
            "context_fit": True,
            "profile_fit": True,
            "observed_cognitive_operations": ["explain", "analyse"],
            "cognitive_operations_fit": True,
            "reasoning_range_fit": True,
            "shortcut_resistant": True,
            "timing_fit": True,
            "scaffolding_fit": True,
            "estimated_minutes": 4.0,
            "issues": [],
        }
    )

    with pytest.raises(ValueError, match="minimum 4"):
        model_review.require_difficulty_review(
            client,
            item_id="q8",
            subject="Economics",
            target={
                "demand_band": "high",
                "minimum_reasoning_steps": 4,
                "requires_judgement": True,
            },
            candidate={"prompt": "Evaluate the decision.", "marks": 15},
            specification={"topic": "market failure"},
        )


def test_require_difficulty_review_rejects_over_demanded_item() -> None:
    client = ReviewClient(
        {
            "approved": True,
            "estimated_demand": "standard",
            "reasoning_steps": 7,
            "tariff_fit": True,
            "command_word_fit": True,
            "context_fit": True,
            "profile_fit": True,
            "observed_cognitive_operations": ["explain", "analyse"],
            "cognitive_operations_fit": True,
            "reasoning_range_fit": False,
            "shortcut_resistant": True,
            "timing_fit": True,
            "scaffolding_fit": True,
            "estimated_minutes": 8.0,
            "issues": [],
        }
    )

    with pytest.raises(ValueError, match="maximum 4"):
        model_review.require_difficulty_review(
            client,
            item_id="q4",
            subject="Computer Science",
            target={
                "demand_band": "standard",
                "minimum_reasoning_steps": 2,
                "maximum_reasoning_steps": 4,
                "required_cognitive_operations": ["explain", "analyse"],
                "requires_shortcut_resistance": True,
                "expected_minutes_min": 4.0,
                "expected_minutes_max": 7.0,
            },
            candidate={"prompt": "Explain the process.", "marks": 4},
            specification={"topic": "networks"},
            canonical_solution={
                "answer": "A complete answer",
                "integrity_version": "closed-numeric-v2",
                "steps": ["one", "two", "three", "four", "five", "six", "seven"],
            },
        )


def test_difficulty_review_receives_independent_solution_and_operation_contract() -> None:
    client = ReviewClient(
        {
            "approved": True,
            "estimated_demand": "high",
            "reasoning_steps": 4,
            "tariff_fit": True,
            "command_word_fit": True,
            "context_fit": True,
            "profile_fit": True,
            "observed_cognitive_operations": ["contextualise", "analyse", "integrate", "judge"],
            "cognitive_operations_fit": True,
            "reasoning_range_fit": True,
            "shortcut_resistant": True,
            "timing_fit": True,
            "scaffolding_fit": True,
            "estimated_minutes": 18.0,
            "issues": [],
        }
    )

    result = model_review.require_difficulty_review(
        client,
        item_id="q8",
        subject="Economics",
        target={
            "demand_band": "high",
            "minimum_reasoning_steps": 4,
            "maximum_reasoning_steps": 7,
            "required_cognitive_operations": ["contextualise", "analyse", "integrate", "judge"],
            "requires_shortcut_resistance": True,
            "expected_minutes_min": 14.0,
            "expected_minutes_max": 22.0,
            "reference_profile_fingerprint": "a" * 64,
        },
        candidate={"prompt": "Evaluate the decision.", "marks": 15},
        specification={"topic": "market failure"},
        canonical_solution={"answer": "Judgement", "steps": ["a", "b", "c", "d"], "integrity_version": "closed-numeric-v2"},
    )

    assert result.schema_version == 2
    assert result.target_profile_fingerprint == "a" * 64
    assert result.independent_solution_steps == 4
    assert "canonical_solution" in client.prompt
    assert "shortcut" in client.prompt.casefold()


def test_difficulty_review_makes_low_demand_operation_tokens_unambiguous() -> None:
    class VocabularySensitiveClient:
        def generate_json(self, prompt: str) -> dict[str, object]:
            explicit_contract = (
                "copy every required cognitive-operation token verbatim" in prompt
                and "retrieval and contextualisation still count" in prompt
            )
            return {
                "approved": explicit_contract,
                "estimated_demand": "low",
                "reasoning_steps": 1,
                "tariff_fit": True,
                "command_word_fit": True,
                "context_fit": True,
                "profile_fit": True,
                "observed_cognitive_operations": (
                    ["retrieve", "contextualise"] if explicit_contract else []
                ),
                "cognitive_operations_fit": explicit_contract,
                "reasoning_range_fit": True,
                "shortcut_resistant": True,
                "timing_fit": True,
                "scaffolding_fit": True,
                "estimated_minutes": 1.0,
                "issues": [],
            }

    result = model_review.require_difficulty_review(
        VocabularySensitiveClient(),
        item_id="q1",
        subject="Accounting",
        target={
            "demand_band": "low",
            "minimum_reasoning_steps": 1,
            "maximum_reasoning_steps": 2,
            "required_cognitive_operations": ["retrieve", "contextualise"],
            "expected_minutes_min": 0.5,
            "expected_minutes_max": 1.5,
        },
        candidate={"prompt": "Which treatment is correct?", "marks": 1},
        specification={"topic": "financial accounting"},
        canonical_solution={"answer": "B", "steps": ["identify the treatment"], "integrity_version": "closed-numeric-v2"},
    )

    assert result.approved is True
    assert result.observed_cognitive_operations == ["retrieve", "contextualise"]


def test_difficulty_review_makes_single_item_timing_units_unambiguous() -> None:
    class TimingSensitiveClient:
        def generate_json(self, prompt: str) -> dict[str, object]:
            minutes_are_explicit = (
                "estimated_minutes is minutes for this one item" in prompt
                and "9.0 means nine minutes" in prompt
                and "never seconds" in prompt
            )
            return {
                "approved": True,
                "estimated_demand": "standard",
                "reasoning_steps": 3,
                "tariff_fit": True,
                "command_word_fit": True,
                "context_fit": True,
                "profile_fit": True,
                "observed_cognitive_operations": ["apply", "transform"],
                "cognitive_operations_fit": True,
                "reasoning_range_fit": True,
                "shortcut_resistant": True,
                "timing_fit": True,
                "scaffolding_fit": True,
                "estimated_minutes": 9.0 if minutes_are_explicit else 90.0,
                "issues": [],
            }

    result = model_review.require_difficulty_review(
        TimingSensitiveClient(),
        item_id="q11",
        subject="Accounting",
        target={
            "demand_band": "standard",
            "minimum_reasoning_steps": 2,
            "maximum_reasoning_steps": 5,
            "required_cognitive_operations": ["apply", "transform"],
            "requires_shortcut_resistance": True,
            "expected_minutes_min": 6.75,
            "expected_minutes_max": 11.25,
        },
        candidate={"prompt": "Prepare the account.", "marks": 9},
        specification={"topic": "financial accounting"},
        canonical_solution={"answer": "Account", "steps": ["a", "b", "c"], "integrity_version": "closed-numeric-v2"},
    )

    assert result.estimated_minutes == 9.0


def test_difficulty_review_surfaces_exact_target_checklist_before_payload() -> None:
    class ChecklistSensitiveClient:
        def generate_json(self, prompt: str) -> dict[str, object]:
            checklist_is_prominent = (
                'REQUIRED_COGNITIVE_OPERATIONS=["explain", "contextualise", "analyse"]'
                in prompt
                and "EXPECTED_MINUTES_RANGE=6.75..11.25" in prompt
            )
            return {
                "approved": checklist_is_prominent,
                "estimated_demand": "standard",
                "reasoning_steps": 3,
                "tariff_fit": True,
                "command_word_fit": True,
                "context_fit": True,
                "profile_fit": True,
                "observed_cognitive_operations": (
                    ["explain", "contextualise", "analyse"]
                    if checklist_is_prominent
                    else ["contextualise", "analyse"]
                ),
                "cognitive_operations_fit": checklist_is_prominent,
                "reasoning_range_fit": True,
                "shortcut_resistant": True,
                "timing_fit": True,
                "scaffolding_fit": True,
                "estimated_minutes": 9.0,
                "issues": [],
            }

    result = model_review.require_difficulty_review(
        ChecklistSensitiveClient(),
        item_id="q11",
        subject="Accounting",
        target={
            "demand_band": "standard",
            "minimum_reasoning_steps": 2,
            "maximum_reasoning_steps": 4,
            "required_cognitive_operations": [
                "explain",
                "contextualise",
                "analyse",
            ],
            "requires_shortcut_resistance": True,
            "expected_minutes_min": 6.75,
            "expected_minutes_max": 11.25,
        },
        candidate={"prompt": "Explain the accounting effect.", "marks": 6},
        specification={"topic": "financial accounting"},
        canonical_solution={"answer": "Explanation", "steps": ["a", "b", "c"], "integrity_version": "closed-numeric-v2"},
    )

    assert result.approved is True


def test_difficulty_prompt_distinguishes_authored_sql_from_supplied_sql_analysis() -> None:
    response = model_review.DifficultyReviewResult(
        approved=True,
        estimated_demand="standard",
        reasoning_steps=2,
        tariff_fit=True,
        command_word_fit=True,
        context_fit=True,
        profile_fit=True,
        observed_cognitive_operations=["program"],
        estimated_minutes=3.0,
    ).model_dump(mode="json")
    client = ReviewClient(response)
    model_review.difficulty_review(
        client,
        item_id="sql",
        subject="Computer Science",
        target={"required_cognitive_operations": ["program"]},
        candidate={"prompt": "Write the SELECT statement."},
        specification={},
    )
    assert "candidate-authored declarative SQL SELECT or INSERT" in client.prompt
    assert "analysis of SQL already supplied" in client.prompt


@pytest.mark.parametrize(
    ("prompt", "task_operation", "observed_operation"),
    [
        (
            "Identify the result produced by the supplied SELECT query.",
            "analyse",
            "analyse",
        ),
        (
            "Identify the rows affected by the supplied UPDATE statement.",
            "analyse",
            "analyse",
        ),
        (
            "Identify the row removed by the supplied DELETE statement.",
            "analyse",
            "analyse",
        ),
        (
            "Write a Python function that returns the larger argument.",
            "program",
            "program",
        ),
    ],
)
def test_difficulty_prompt_limits_declarative_sql_fact_to_authored_select_or_insert(
    prompt, task_operation, observed_operation
) -> None:
    response = model_review.DifficultyReviewResult(
        approved=True,
        estimated_demand="low",
        reasoning_steps=1,
        tariff_fit=True,
        command_word_fit=True,
        context_fit=True,
        profile_fit=True,
        observed_cognitive_operations=[observed_operation],
        estimated_minutes=1.5,
    ).model_dump(mode="json")
    client = ReviewClient(response)

    model_review.difficulty_review(
        client,
        item_id="sql-analysis",
        subject="Computer Science",
        target={"required_cognitive_operations": [observed_operation]},
        candidate={
            "part": {
                "prompt": prompt,
                "task_operation": task_operation,
            }
        },
        specification={},
    )

    assert "LITERAL_CANDIDATE_TASK_FACTS=" in client.prompt
    assert '"candidate_authors_declarative_sql": false' in client.prompt
    assert '"declarative_sql_statement_kind": null' in client.prompt
    assert client.prompt.index("END_UNTRUSTED_REVIEW_PAYLOAD") < client.prompt.rindex(
        "LITERAL_CANDIDATE_TASK_FACTS="
    )
    assert client.prompt.rindex("FINAL_SEMANTIC_RESPONSE_CHECK=") < client.prompt.rindex(
        "Return JSON only:"
    )


def test_sql_literal_fact_does_not_mirror_a_program_target_for_supplied_analysis() -> None:
    target = {
        "demand_band": "low",
        "minimum_reasoning_steps": 1,
        "maximum_reasoning_steps": 2,
        "required_cognitive_operations": ["program"],
    }
    response = model_review.DifficultyReviewResult(
        approved=True,
        estimated_demand="low",
        reasoning_steps=1,
        tariff_fit=True,
        command_word_fit=True,
        context_fit=True,
        profile_fit=True,
        observed_cognitive_operations=["analyse"],
        estimated_minutes=1.5,
    ).model_dump(mode="json")
    client = ReviewClient(response)

    with pytest.raises(ValueError, match="missing required cognitive operations: program"):
        model_review.require_difficulty_review(
            client,
            item_id="supplied-select",
            subject="Computer Science",
            target=target,
            candidate={
                "part": {
                    "prompt": "Identify the result produced by this supplied SELECT query.",
                    "task_operation": "analyse",
                }
            },
            specification={},
        )

    assert '"candidate_authors_declarative_sql": false' in client.prompt
