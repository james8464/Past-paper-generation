"""Bind new cash/profit budget givens to the printed task, preserving legacy data."""

import hashlib
import json
from pathlib import Path

import pytest
from aqaaccountgen.configs import RULES
from aqaaccountgen.generator import _management_calculation, build_paper
from aqaaccountgen.syllabus import load_syllabus

from Backend.Core.ai_assessment import (
    _independently_validate_candidate,
    _validate_checkpoint_item,
)
from Backend.Core.answer_projection import without_private_answer_keys
from Backend.Core.assessment_prompts import (
    AssessmentPromptTask,
    generation_prompt,
    task_source,
)
from Backend.Core.solver_prompts import build_solver_prompt
from Backend.Core.subjects.accounting import solve_accounting_calculation

ROOT = Path(__file__).resolve().parents[1]
SYLLABUS = load_syllabus(ROOT / "Resources/accounting/aqa/generator/data/syllabus.json")
ASSUMPTIONS = (
    "Assume sales receipts equal revenue earned in this budget period, and "
    "variable- and fixed-cost payments equal expenses incurred in it. "
    "There are no inventory changes, accruals, prepayments or non-cash charges. "
    "The capital payment purchases a non-current asset; there are no other transactions."
)


def budget_task(seed: int = 270100) -> AssessmentPromptTask:
    paper = build_paper(RULES["paper_2"], SYLLABUS, seed)
    for si, section in enumerate(paper.sections):
        for oi, option in enumerate(section.options):
            for qi, question in enumerate(option.questions):
                if question.rule_id == "budget":
                    topic = next(
                        t for t in SYLLABUS.topics if t.id == question.topic_id
                    )
                    return AssessmentPromptTask((si, oi, qi), question, option, topic)
    raise AssertionError("budget task missing")


def digest(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def test_new_budget_prints_the_same_unsolved_public_assumptions_for_every_role() -> (
    None
):
    task = budget_task()
    question = task.question
    assert ASSUMPTIONS in question.prompt
    assert question.authoring_context["independent_solver_instructions"] == [
        ASSUMPTIONS
    ]
    assert task_source(task)["question_context"]["independent_solver_instructions"] == [
        ASSUMPTIONS
    ]
    writer = generation_prompt(
        [task], subject="accounting", seed=270100, attempt=1, previous_failure=""
    )
    assert ASSUMPTIONS in writer
    blind = without_private_answer_keys(question.model_dump(mode="json"))
    assert blind["authoring_context"]["independent_solver_instructions"] == [
        ASSUMPTIONS
    ]
    assert "verified_answers" not in blind["authoring_context"]
    assert "mark_scheme" not in blind and "structured_mark_scheme" not in blind
    assert ASSUMPTIONS in build_solver_prompt(blind, [], [])
    assert not any(char.isdigit() for char in ASSUMPTIONS)


@pytest.mark.parametrize("mutation", ["omit", "change", "declaration"])
def test_declared_budget_assumptions_cannot_diverge_from_the_printed_task(
    mutation: str,
) -> None:
    raw = budget_task().question.model_dump(mode="json")
    raw["authoring_context"]["independent_solver_instructions"] = [ASSUMPTIONS]
    if mutation == "omit":
        raw["prompt"] = raw["prompt"].replace(ASSUMPTIONS, "")
    elif mutation == "change":
        raw["prompt"] = raw["prompt"].replace(
            ASSUMPTIONS, "Assume some costs are prepaid."
        )
    else:
        raw["authoring_context"]["independent_solver_instructions"] = [
            "Assume some costs are prepaid."
        ]
    with pytest.raises(ValueError, match=r"budget.*assumption"):
        solve_accounting_calculation(raw)


@pytest.mark.parametrize("replacement", ["", "Assume some expenses are unpaid."])
def test_author_and_checkpoint_cannot_drop_new_assumptions_while_retaining_context(
    replacement: str,
) -> None:
    task = budget_task()
    candidate = task.question.model_copy(
        update={"prompt": task.question.prompt.replace(ASSUMPTIONS, replacement)}
    )
    with pytest.raises(ValueError, match=r"immutable.*prompt"):
        _independently_validate_candidate(task, candidate, client=object())
    with pytest.raises(ValueError, match=r"immutable.*prompt"):
        _validate_checkpoint_item(task, candidate)


def test_current_candidate_cannot_downgrade_the_public_declaration_to_legacy() -> None:
    task = budget_task()
    context = dict(task.question.authoring_context)
    context.pop("independent_solver_instructions")
    candidate = task.question.model_copy(update={"authoring_context": context})
    with pytest.raises(ValueError, match="changed"):
        _independently_validate_candidate(task, candidate, client=object())
    with pytest.raises(ValueError, match="changed"):
        _validate_checkpoint_item(task, candidate)


def test_native_figures_arithmetic_and_legacy_reading_remain_unchanged() -> None:
    prompt, scheme, context = _management_calculation(
        "budget", "Copper Lane Foods", [97, 103, 115, 109, 118]
    )
    raw = {"rule_id": "budget", "prompt": prompt, "authoring_context": context}
    result = solve_accounting_calculation(raw)
    assert context["source_data"] == {
        "sales_receipts": 118000,
        "variable_cost_payments": 115000,
        "fixed_cost_payments": 103000,
        "opening_cash": 48500,
        "capital_payment": 43600,
    }
    assert context["verified_answers"] == {
        "contribution": 3000,
        "budgeted_profit": -100000,
        "net_cash_flow": -143600,
        "closing_cash": -95100,
    }
    legacy = {
        **raw,
        "prompt": prompt.replace(ASSUMPTIONS + " ", ""),
        "authoring_context": {
            k: v for k, v in context.items() if k != "independent_solver_instructions"
        },
    }
    before = json.dumps(legacy, sort_keys=True)
    assert solve_accounting_calculation(legacy) == result
    assert json.dumps(legacy, sort_keys=True) == before
    assert len(scheme) == 8


def test_nonbudget_content_and_all_old_numeric_contracts_are_unchanged() -> None:
    expected = {
        "1": "1eecc968af212c412561c9ce4265634c9560c08908acf3b3e09d50716fad7c0d",
        "2": "95e3518cb9c7bd1d00c1596efa67ba58f94d2649d91395c60b6a375aa382ea4d",
    }
    for component in ("1", "2"):
        raw = build_paper(RULES[f"paper_{component}"], SYLLABUS, 270100).model_dump(
            mode="json"
        )
        for section in raw["sections"]:
            for option in section["options"]:
                for question in option["questions"]:
                    if question["rule_id"] == "budget":
                        assert question["marks"] == 8
                        question["prompt"] = "BUDGET_PROMPT"
                        question["authoring_context"].pop(
                            "independent_solver_instructions", None
                        )
                        # The existing enrichment derives this presentation budget
                        # from the now-longer explicit statement, not from numbers.
                        question["authoring_context"]["max_prompt_words"] = 40
        assert digest(raw) == expected[component]
