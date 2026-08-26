from __future__ import annotations

import pytest

from Backend.Core.ai_assessment import (
    GenerationPolicy,
    _batches_for_client,
    _candidate_question,
    _clean_generated_prompt,
    _effective_batch_size,
    _generate_batch,
    _generate_item_transaction,
    _generation_prompt,
    _normalise_calculation_guidance,
    _normalise_command_word,
    _normalise_level_allocations,
    _normalise_multiple_choice_answer,
    _repair_prompt,
    _required_awarded_entries,
    _review_prompt,
    _seeded_fallback_allowed,
    _Task,
    _task_source,
    _upgrade_checkpoint_metadata,
    _validate_checkpoint_item,
    _validate_mark_points,
    _validate_prompt_length,
)
from Backend.Core.assessment_contracts import (
    AssessmentContract,
    NumericValueContract,
)
from Backend.Core.exam_blueprints import (
    GeneratedOption,
    GeneratedQuestion,
    MarkSchemePoint,
)
from Backend.Core.model_review import ReviewResult


def test_complete_command_receives_method_guidance() -> None:
    question = GeneratedQuestion(
        rule_id="trace",
        number="3(a)",
        marks=4,
        kind="analysis",
        command_word="complete",
        topic_id="systems",
        prompt="Complete the trace table.",
        mark_scheme=["Credit correct results."],
        assessment_objectives={"AO2": 4},
    )
    points = [
        MarkSchemePoint(
            text="Credit a correct result.",
            marks=4,
            assessment_objective="AO2",
        )
    ]

    normalised = _normalise_calculation_guidance(question, points)

    assert any("method credit" in point.text.casefold() for point in normalised)


def test_equivalent_leading_command_is_normalised_to_blueprint_word() -> None:
    assert _normalise_command_word(
        "Identify 2 consequences for the program.",
        "State",
    ) == "State 2 consequences for the program."
    assert _normalise_command_word(
        "The developer should identify a suitable test.",
        "State",
    ) == "The developer should identify a suitable test."


def test_family_prompt_word_limit_rejects_layout_breaking_text() -> None:
    question = GeneratedQuestion(
        rule_id="programming",
        number="9(e)",
        marks=5,
        kind="programming",
        command_word="Develop",
        topic_id="algorithms",
        prompt="Develop a concise solution.",
        mark_scheme=["Credit a valid solution."],
        assessment_objectives={"AO3": 5},
        authoring_context={"max_prompt_words": 12},
    )

    with pytest.raises(ValueError, match="maximum is 12"):
        _validate_prompt_length(
            question,
            "Develop a solution that includes many unnecessary explanatory words "
            "which would force the response area onto another page.",
        )


def test_local_seeded_fallback_is_limited_to_safe_stem_failures() -> None:
    assert _seeded_fallback_allowed(
        provider="ollama",
        failure="calculation changed the required precision instruction",
    )
    assert _seeded_fallback_allowed(
        provider="ollama",
        failure="question 7 is only a paraphrase of the draft (1.000)",
    )
    assert _seeded_fallback_allowed(
        provider="ollama",
        failure="question 8 prompt has 27 words; maximum is 20",
    )
    assert _seeded_fallback_allowed(
        provider="ollama",
        failure="question 9 omitted a required source or visual term",
    )
    assert _seeded_fallback_allowed(
        provider="ollama",
        failure=(
            "mcq changed immutable numeric data: expected Counter(), "
            "got Counter({'2016': 1})"
        ),
    )
    assert not _seeded_fallback_allowed(
        provider="openai",
        failure="calculation changed the required precision instruction",
    )
    assert not _seeded_fallback_allowed(
        provider="ollama",
        failure="mark scheme has incorrect causal reasoning",
    )


def test_local_precision_drift_uses_independently_reviewed_seeded_stem() -> None:
    point = MarkSchemePoint(
        text="Award two marks for the correct method and result.",
        marks=2,
        assessment_objective="AO2",
    )
    question = GeneratedQuestion(
        rule_id="calculation",
        number="1",
        marks=2,
        kind="calculation",
        command_word="Calculate",
        topic_id="indices",
        prompt="Calculate the change from 2024 to 2028 to one decimal place.",
        mark_scheme=[point.text],
        structured_mark_scheme=[point],
        assessment_objectives={"AO2": 2},
        authoring_context={
            "preserve_mark_scheme": True,
            "max_prompt_words": 14,
        },
    )
    task = _Task(
        key=(0, 0, 0),
        question=question,
        option=GeneratedOption(id="data", title="Indices", questions=[question]),
        topic=type(
            "Topic",
            (),
            {"id": "indices", "title": "Index numbers", "points": []},
        )(),
    )

    class Client:
        provider = "ollama"
        model = "test"

        def __init__(self) -> None:
            invalid = {
                "questions": [
                    {
                        "id": "0/0/0",
                        "prompt": (
                            "Calculate the change from 2024 to 2028 to 2 decimal places."
                        ),
                    }
                ]
            }
            self.responses = iter(
                [invalid, invalid, invalid, _review_response("0/0/0", approved=True)]
            )

        def generate_json(self, _prompt: str) -> dict[str, object]:
            return next(self.responses)

    result = _generate_item_transaction(
        task,
        client=Client(),
        subject="Economics",
        seed=1,
        policy=GenerationPolicy(attempts=3),
        progress=None,
        accepted_prompts=[],
    )

    assert result.prompt == question.prompt
    assert result.provenance == "reviewed-seeded-fallback:ollama"


class _Client:
    def __init__(self, *, parallel: bool) -> None:
        self.supports_parallel_generation = parallel


def test_local_generation_uses_smaller_structured_output_batches() -> None:
    policy = GenerationPolicy(batch_size=6)

    assert _effective_batch_size(_Client(parallel=False), policy) == 3
    assert _effective_batch_size(_Client(parallel=True), policy) == 6


def test_generated_prompt_drops_renderer_owned_number_and_mark_label() -> None:
    question = GeneratedQuestion(
        rule_id="q01",
        number="01",
        marks=1,
        kind="multiple_choice",
        command_word="select",
        topic_id="topic",
        prompt="Which source document records a credit purchase?",
        mark_scheme=["Purchase invoice."],
    )

    assert _clean_generated_prompt(
        "Question 01: Which document is evidence of a credit purchase? [1 mark]",
        question=question,
    ) == "Which document is evidence of a credit purchase?"


def test_generated_prompt_drops_an_unprotected_renderer_source_number() -> None:
    question = GeneratedQuestion(
        rule_id="q12",
        number="12",
        marks=7,
        kind="calculation",
        command_word="prepare",
        topic_id="topic",
        prompt="Prepare the non-current assets section. Show all workings.",
        mark_scheme=["Credit valid workings."],
    )

    assert _clean_generated_prompt(
        "Prepare the non-current assets section using Extract 1. [7 marks]",
        question=question,
    ) == "Prepare the non-current assets section using the extract."


def test_multiple_choice_answer_shorthand_is_normalised_to_the_full_choice() -> None:
    question = GeneratedQuestion(
        rule_id="q01",
        number="01",
        marks=1,
        kind="multiple_choice",
        command_word="select",
        topic_id="topic",
        prompt="Select the correct statement.",
        mark_scheme=["Choice C"],
        assessment_objectives={"AO1": 1},
    )
    points = [
        MarkSchemePoint(
            text="Statement C",
            marks=1,
            assessment_objective="AO1",
        )
    ]

    normalised = _normalise_multiple_choice_answer(
        question,
        points,
        "Year-end adjustments match income to the correct period.",
    )

    assert normalised[0].text == "Year-end adjustments match income to the correct period."
    assert normalised[0].marks == 1
    assert _clean_generated_prompt(
        "1. Which document is evidence of a credit purchase?",
        question=question,
    ) == "Which document is evidence of a credit purchase?"


def test_local_batches_separate_high_mark_items() -> None:
    option = GeneratedOption(
        id="option",
        title="Option",
        questions=[],
    )

    def task(index: int, marks: int) -> _Task:
        return _Task(
            key=(0, 0, index),
            option=option,
            topic=object(),
            question=GeneratedQuestion(
                rule_id=f"q{index}",
                number=str(index + 1),
                marks=marks,
                kind="essay" if marks > 1 else "multiple_choice",
                command_word="assess" if marks > 1 else "select",
                topic_id="topic",
                prompt="Assess the decision." if marks > 1 else "Select the item.",
                mark_scheme=["Credit a valid response."],
            ),
        )

    tasks = [task(0, 1), task(1, 1), task(2, 1), task(3, 16), task(4, 12)]
    local = _batches_for_client(
        tasks,
        client=_Client(parallel=False),
        policy=GenerationPolicy(),
    )
    remote = _batches_for_client(
        tasks,
        client=_Client(parallel=True),
        policy=GenerationPolicy(),
    )

    assert [len(batch) for batch in local] == [3, 1, 1]
    assert [len(batch) for batch in remote] == [5]


def test_generation_prompt_exposes_semantics_but_withholds_draft_marking_points() -> None:
    question = GeneratedQuestion(
        rule_id="q1",
        number="1",
        marks=4,
        kind="explain",
        command_word="explain",
        topic_id="topic",
        prompt="Explain the forbidden planning draft phrase.",
        mark_scheme=["Forbidden planning mark point."],
    )
    task = _Task(
        key=(0, 0, 0),
        question=question,
        option=GeneratedOption(id="option", title="Case study", questions=[question]),
        topic=type(
            "Topic",
            (),
            {
                "id": "topic",
                "title": "Topic title",
                "points": ["Specification point"],
            },
        )(),
    )

    prompt = _generation_prompt(
        [task],
        subject="Test subject",
        seed=123,
        attempt=1,
        previous_failure="",
    )

    assert '"semantic_task_contract": {' in prompt
    assert (
        '"required_task_terms": ["forbidden", "planning", "draft", "phrase"]'
        in prompt
    )
    assert "forbidden planning mark point" not in prompt.casefold()
    assert "draft_to_replace" not in prompt
    assert '"required_exact_tokens": []' in prompt
    assert '"minimum_substantive_mark_scheme_points": 2' in prompt
    assert "an empty list means the prompt contains no numeric token" in prompt
    assert "source labels such as `Extract 1`" in prompt
    assert "Compose fresh prose around those elements" in prompt


def test_generation_prompt_skips_model_scheme_for_verified_guidance() -> None:
    question = GeneratedQuestion(
        rule_id="q1",
        number="1",
        marks=2,
        kind="calculation",
        command_word="Calculate",
        topic_id="indices",
        prompt="Calculate the index change.",
        mark_scheme=["Award the verified method and answer."],
        assessment_objectives={"AO2": 2},
        authoring_context={
            "preserve_mark_scheme": True,
            "max_prompt_words": 14,
        },
    )
    task = _Task(
        key=(0, 0, 0),
        question=question,
        option=GeneratedOption(id="data", title="Indices", questions=[question]),
        topic=type(
            "Topic",
            (),
            {"id": "indices", "title": "Index numbers", "points": []},
        )(),
    )

    prompt = _generation_prompt(
        [task],
        subject="Economics",
        seed=1,
        attempt=1,
        previous_failure="",
    )

    assert '"mark_scheme_locked": true' in prompt
    assert '"minimum_substantive_mark_scheme_points": 0' in prompt
    assert '"required_awarded_entries": []' in prompt
    assert '"maximum_prompt_words": 14' in prompt
    assert "return an empty `mark_scheme` array" in prompt
    assert "must not exceed `maximum_prompt_words`" in prompt


def test_self_contained_numeric_mcq_excludes_unrelated_option_stimulus() -> None:
    question = GeneratedQuestion(
        rule_id="q07",
        number="07",
        marks=1,
        kind="multiple_choice",
        command_word="select",
        topic_id="topic",
        prompt=(
            "Glenmore Trading has revenue of £185000 and cost of sales of £35000. "
            "What is gross profit?"
        ),
        mark_scheme=["£150000"],
    )
    task = _Task(
        key=(0, 0, 0),
        question=question,
        option=GeneratedOption(
            id="option",
            title="Glenmore Trading",
            stimulus=[
                "Extract 1. Glenmore Trading reported revenue of £1060000 and "
                "profit of £105000."
            ],
            questions=[question],
        ),
        topic=object(),
    )

    source = _task_source(task)

    assert source["scope"] == "self_contained_question"
    assert "stimulus" not in source
    assert "£1060000" not in str(source)


def test_explicit_source_question_retains_option_material() -> None:
    question = GeneratedQuestion(
        rule_id="q16",
        number="16",
        marks=25,
        kind="extended_response",
        command_word="advise",
        topic_id="topic",
        prompt="Use the information in the case to advise Glenmore Trading.",
        mark_scheme=["Credit a justified recommendation."],
    )
    task = _Task(
        key=(0, 0, 0),
        question=question,
        option=GeneratedOption(
            id="option",
            title="Glenmore Trading",
            stimulus=["Extract 1. Revenue was £1060000."],
            questions=[question],
        ),
        topic=object(),
    )

    source = _task_source(task)

    assert source["stimulus"] == ["Extract 1. Revenue was £1060000."]


def test_generated_question_must_preserve_visual_contract_terms() -> None:
    question = GeneratedQuestion(
        rule_id="visual",
        number="2",
        marks=1,
        kind="multiple_choice",
        command_word="select",
        topic_id="topic",
        prompt=(
            "Figure 2 shows a D curve shifting to the right. Which outcome "
            "follows?"
        ),
        mark_scheme=["Equilibrium price and quantity rise."],
        choices=["Both rise", "Both fall", "Price rises", "Quantity falls"],
        correct_choice=0,
        assessment_objectives={"AO2": 1},
        authoring_context={
            "required_prompt_terms": ["Figure 2", "D", "right"],
        },
    )
    task = _Task(
        key=(0, 0, 0),
        question=question,
        option=GeneratedOption(id="visual", title="Visual", questions=[question]),
        topic=object(),
    )
    raw = {
        "prompt": "Using Figure 2, what follows from the movement of the D curve?",
        "choices": ["Both rise", "Both fall", "Price rises", "Quantity falls"],
        "correct_choice": 0,
        "mark_scheme": [
            {
                "text": "Both rise",
                "marks": 1,
                "credit_type": "answer",
                "assessment_objective": "AO2",
            }
        ],
    }

    with pytest.raises(ValueError, match="omitted a required source or visual term"):
        _candidate_question(
            task,
            raw,
            client=type("Client", (), {"provider": "test", "model": "test"})(),
            policy=GenerationPolicy(),
        )


def test_candidate_question_accepts_unordered_contract_values() -> None:
    question = GeneratedQuestion(
        rule_id="calculation",
        number="2",
        marks=2,
        kind="calculation",
        command_word="calculate",
        topic_id="topic",
        prompt="Calculate the result using 55 followed by 5%.",
        mark_scheme=["Credit a valid calculation."],
        assessment_objectives={"AO2": 2},
        contract=AssessmentContract(
            item_id="calculation",
            marks=2,
            assessment_objectives={"AO2": 2},
            numeric_values=[
                NumericValueContract(text="55"),
                NumericValueContract(text="5%"),
            ],
        ),
    )
    task = _Task(
        key=(0, 0, 0),
        question=question,
        option=GeneratedOption(id="option", title="Option", questions=[question]),
        topic=object(),
    )
    raw = {
        "prompt": "Calculate the outcome after applying 5% to 55.",
        "mark_scheme": [
            {
                "text": "Apply the percentage correctly.",
                "marks": 1,
                "assessment_objective": "AO2",
            },
            {
                "text": "State the correct outcome.",
                "marks": 1,
                "assessment_objective": "AO2",
            },
        ],
    }

    candidate = _candidate_question(
        task,
        raw,
        client=type("Client", (), {"provider": "test", "model": "test"})(),
        policy=GenerationPolicy(),
    )

    assert candidate.prompt == "Calculate the outcome after applying 5% to 55."


def test_legacy_candidate_question_treats_values_as_an_unordered_contract() -> None:
    question = GeneratedQuestion(
        rule_id="calculation",
        number="2",
        marks=2,
        kind="calculation",
        command_word="calculate",
        topic_id="topic",
        prompt="Calculate the result using 55 followed by 5%.",
        mark_scheme=["Credit a valid calculation."],
        assessment_objectives={"AO2": 2},
    )
    task = _Task(
        key=(0, 0, 0),
        question=question,
        option=GeneratedOption(id="option", title="Option", questions=[question]),
        topic=object(),
    )

    candidate = _candidate_question(
        task,
        {
            "prompt": "Calculate the outcome after applying 5% to 55.",
            "mark_scheme": [
                {
                    "text": "Apply the percentage correctly.",
                    "marks": 1,
                    "assessment_objective": "AO2",
                },
                {
                    "text": "State the correct outcome.",
                    "marks": 1,
                    "assessment_objective": "AO2",
                },
            ],
        },
        client=type("Client", (), {"provider": "test", "model": "test"})(),
        policy=GenerationPolicy(),
    )

    assert candidate.prompt == "Calculate the outcome after applying 5% to 55."


def test_generated_question_rejects_a_forbidden_semantic_relationship() -> None:
    question = GeneratedQuestion(
        rule_id="partnership",
        number="15.1",
        marks=2,
        kind="calculation",
        command_word="prepare",
        topic_id="partnerships",
        prompt="Prepare the continuing partners' capital accounts after retirement.",
        mark_scheme=["Credit the goodwill adjustments and balances."],
        assessment_objectives={"AO1": 1, "AO2": 1},
        authoring_context={
            "forbidden_prompt_terms": ["retiring partner's account"],
        },
    )
    task = _Task(
        key=(0, 0, 0),
        question=question,
        option=GeneratedOption(id="case", title="Partnership", questions=[question]),
        topic=object(),
    )
    raw = {
        "prompt": (
            "Prepare capital accounts after goodwill is written back out of the "
            "retiring partner's account."
        ),
        "mark_scheme": [
            {
                "text": "Credit the goodwill adjustment.",
                "marks": 1,
                "assessment_objective": "AO1",
            },
            {
                "text": "Calculate the closing balances.",
                "marks": 1,
                "assessment_objective": "AO2",
            },
        ],
    }

    with pytest.raises(ValueError, match="included a forbidden semantic term"):
        _candidate_question(
            task,
            raw,
            client=type("Client", (), {"provider": "test", "model": "test"})(),
            policy=GenerationPolicy(),
        )


def test_generated_mark_scheme_must_cover_each_required_period() -> None:
    question = GeneratedQuestion(
        rule_id="partnership",
        number="15.2",
        marks=2,
        kind="calculation",
        command_word="prepare",
        topic_id="partnerships",
        prompt="Prepare the appropriation account for both periods.",
        mark_scheme=["Credit calculations for both periods."],
        assessment_objectives={"AO1": 1, "AO2": 1},
        authoring_context={
            "required_mark_scheme_terms": ["first period", "second period"],
        },
    )
    task = _Task(
        key=(0, 0, 0),
        question=question,
        option=GeneratedOption(id="case", title="Partnership", questions=[question]),
        topic=object(),
    )
    raw = {
        "prompt": "Prepare a two-part appropriation account from the supplied data.",
        "mark_scheme": [
            {
                "text": "Calculate interest for the first period.",
                "marks": 1,
                "assessment_objective": "AO1",
            },
            {
                "text": "Calculate first period residual profit.",
                "marks": 1,
                "assessment_objective": "AO2",
            },
        ],
    }

    with pytest.raises(ValueError, match="omitted required marking content"):
        _candidate_question(
            task,
            raw,
            client=type("Client", (), {"provider": "test", "model": "test"})(),
            policy=GenerationPolicy(),
        )


def test_generated_mark_scheme_rejects_forbidden_semantic_relationship() -> None:
    question = GeneratedQuestion(
        rule_id="partnership",
        number="15.1",
        marks=1,
        kind="calculation",
        command_word="prepare",
        topic_id="partnerships",
        prompt="Prepare the continuing partners' capital accounts.",
        mark_scheme=["Credit the goodwill adjustment."],
        assessment_objectives={"AO2": 1},
        authoring_context={
            "forbidden_mark_scheme_terms": ["Riley's goodwill write-off"],
        },
    )
    task = _Task(
        key=(0, 0, 0),
        question=question,
        option=GeneratedOption(id="case", title="Partnership", questions=[question]),
        topic=object(),
    )
    raw = {
        "prompt": "Prepare capital accounts for the partners who continue trading.",
        "mark_scheme": [
            {
                "text": "Calculate Riley's goodwill write-off.",
                "marks": 1,
                "assessment_objective": "AO2",
            }
        ],
    }

    with pytest.raises(ValueError, match="included forbidden marking content"):
        _candidate_question(
            task,
            raw,
            client=type("Client", (), {"provider": "test", "model": "test"})(),
            policy=GenerationPolicy(),
        )


def test_generated_extended_mark_scheme_adds_examiner_guidance() -> None:
    question = GeneratedQuestion(
        rule_id="evaluation",
        number="16",
        marks=12,
        kind="extended_response",
        command_word="assess",
        topic_id="decision-making",
        prompt="Assess whether the business should make the investment.",
        mark_scheme=["Credit a supported decision."],
        assessment_objectives={"AO1": 2, "AO2": 2, "AO3": 4, "AO4": 4},
        scheme_mode="levels",
    )
    task = _Task(
        key=(0, 0, 0),
        question=question,
        option=GeneratedOption(id="case", title="Business case", questions=[question]),
        topic=object(),
    )
    raw = {
        "prompt": "Assess the case for proceeding with the proposed investment.",
        "mark_scheme": [
            {
                "text": "Define the relevant accounting principle.",
                "marks": 2,
                "assessment_objective": "AO1",
            },
            {
                "text": "Apply the source figures to the proposed investment.",
                "marks": 2,
                "assessment_objective": "AO2",
            },
            {
                "text": "Develop a causal chain from finance cost to liquidity.",
                "marks": 4,
                "assessment_objective": "AO3",
            },
            {
                "text": "Reach a supported judgement using the source evidence.",
                "marks": 4,
                "assessment_objective": "AO4",
            },
            *[
                {
                    "text": f"Level {level}: descriptor for this band.",
                    "marks": 0,
                    "credit_type": "level",
                    "assessment_objective": None,
                }
                for level in range(1, 4)
            ],
        ],
    }

    candidate = _candidate_question(
        task,
        raw,
        client=type("Client", (), {"provider": "test", "model": "test"})(),
        policy=GenerationPolicy(),
    )

    assert any(point.alternatives for point in candidate.structured_mark_scheme)
    assert any(point.do_not_accept for point in candidate.structured_mark_scheme)


def test_checkpointed_item_must_still_meet_release_quality_gate() -> None:
    question = GeneratedQuestion(
        rule_id="evaluation",
        number="16",
        marks=12,
        kind="extended_response",
        command_word="assess",
        topic_id="decision-making",
        prompt="Assess whether the business should make the investment.",
        mark_scheme=[
            "AO1: define the principle.",
            "AO2: apply the source.",
            "AO3: develop the causal chain.",
            "AO4: reach a supported judgement.",
        ],
        structured_mark_scheme=[
            MarkSchemePoint(
                text=f"{objective} allocation within the levels grid.",
                marks=marks,
                assessment_objective=objective,
            )
            for objective, marks in {"AO1": 2, "AO2": 2, "AO3": 4, "AO4": 4}.items()
        ]
        + [
            MarkSchemePoint(
                text=f"Level {level}: descriptor for this band.",
                marks=0,
                credit_type="level",
            )
            for level in range(1, 4)
        ],
        assessment_objectives={"AO1": 2, "AO2": 2, "AO3": 4, "AO4": 4},
        scheme_mode="levels",
    )
    task = _Task(
        key=(0, 0, 0),
        question=question,
        option=GeneratedOption(id="case", title="Business case", questions=[question]),
        topic=object(),
    )

    with pytest.raises(ValueError, match="alternative-answer guidance"):
        _validate_checkpoint_item(task, question)


def test_checkpoint_cannot_replace_a_locked_verified_mark_scheme() -> None:
    verified = MarkSchemePoint(
        text="Credit the verified economic relationship.",
        marks=1,
        assessment_objective="AO1",
    )
    question = GeneratedQuestion(
        rule_id="q1",
        number="1",
        marks=1,
        kind="explain",
        command_word="Explain",
        topic_id="economics",
        prompt="Explain the economic relationship.",
        mark_scheme=[verified.text],
        structured_mark_scheme=[verified],
        assessment_objectives={"AO1": 1},
        authoring_context={"preserve_mark_scheme": True},
    )
    task = _Task(
        key=(0, 0, 0),
        question=question,
        option=GeneratedOption(id="case", title="Case", questions=[question]),
        topic=object(),
    )
    replacement = MarkSchemePoint(
        text="Credit an unrelated replacement relationship.",
        marks=1,
        assessment_objective="AO1",
    )
    checkpoint = question.model_copy(
        update={
            "mark_scheme": [replacement.text],
            "structured_mark_scheme": [replacement],
        }
    )

    with pytest.raises(ValueError, match="changed verified marking guidance"):
        _validate_checkpoint_item(task, checkpoint)


def test_checkpoint_can_adopt_a_new_prompt_budget_without_content_changes() -> None:
    point = MarkSchemePoint(
        text="A change in the independent variable changes the outcome.",
        marks=1,
        assessment_objective="AO1",
    )
    current = GeneratedQuestion(
        rule_id="q1",
        number="1",
        marks=1,
        kind="explain",
        command_word="Explain",
        topic_id="economics",
        prompt="Explain the relationship.",
        mark_scheme=[point.text],
        structured_mark_scheme=[point],
        assessment_objectives={"AO1": 1},
        authoring_context={
            "preserve_mark_scheme": True,
            "max_prompt_words": 12,
        },
    )
    task = _Task(
        key=(0, 0, 0),
        question=current,
        option=GeneratedOption(id="case", title="Case", questions=[current]),
        topic=object(),
    )
    stored = current.model_copy(
        update={"authoring_context": {"preserve_mark_scheme": True}}
    )

    upgraded = _upgrade_checkpoint_metadata(task, stored)

    assert upgraded.authoring_context == current.authoring_context
    _validate_checkpoint_item(task, upgraded)


def test_source_constrained_calculation_preserves_its_verified_prompt() -> None:
    question = GeneratedQuestion(
        rule_id="partnership",
        number="15.2",
        marks=1,
        kind="calculation",
        command_word="prepare",
        topic_id="partnerships",
        prompt="Prepare the appropriation account for both periods.",
        mark_scheme=["Credit both periods."],
        assessment_objectives={"AO2": 1},
        authoring_context={
            "preserve_prompt": True,
            "required_mark_scheme_terms": ["both periods"],
        },
    )
    task = _Task(
        key=(0, 0, 0),
        question=question,
        option=GeneratedOption(id="case", title="Partnership", questions=[question]),
        topic=object(),
    )
    raw = {
        "prompt": (
            "Prepare the account using £80,400, a 6% rate and every figure from "
            "the source panel."
        ),
        "mark_scheme": [
            {
                "text": "Calculate the allocation for both periods.",
                "marks": 1,
                "assessment_objective": "AO2",
            }
        ],
    }

    candidate = _candidate_question(
        task,
        raw,
        client=type("Client", (), {"provider": "test", "model": "test"})(),
        policy=GenerationPolicy(),
    )

    assert candidate.prompt == question.prompt


def test_source_constrained_calculation_preserves_its_verified_mark_scheme() -> None:
    verified_point = MarkSchemePoint(
        text="Credit both periods using the verified figures.",
        marks=1,
        assessment_objective="AO2",
    )
    examiner_guidance = [
        MarkSchemePoint(
            text=f"Examiner guidance {index}.",
            marks=0,
            credit_type="guidance",
        )
        for index in range(13)
    ]
    question = GeneratedQuestion(
        rule_id="partnership",
        number="15.2",
        marks=1,
        kind="calculation",
        command_word="prepare",
        topic_id="partnerships",
        prompt="Prepare the appropriation account for both periods.",
        mark_scheme=[verified_point.text],
        structured_mark_scheme=[verified_point, *examiner_guidance],
        assessment_objectives={"AO2": 1},
        authoring_context={
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
        },
    )
    task = _Task(
        key=(0, 0, 0),
        question=question,
        option=GeneratedOption(id="case", title="Partnership", questions=[question]),
        topic=object(),
    )
    raw = {
        "prompt": "Prepare the account from the supplied data.",
        "mark_scheme": [
            {
                "text": "Credit only the first period.",
                "marks": 1,
                "assessment_objective": "AO2",
            }
        ],
    }

    candidate = _candidate_question(
        task,
        raw,
        client=type("Client", (), {"provider": "test", "model": "test"})(),
        policy=GenerationPolicy(),
    )

    assert candidate.mark_scheme == question.mark_scheme
    assert candidate.structured_mark_scheme == question.structured_mark_scheme


def test_verified_contract_item_bypasses_model_generation() -> None:
    verified_point = MarkSchemePoint(
        text="Credit the verified calculation.",
        marks=1,
        assessment_objective="AO2",
    )
    question = GeneratedQuestion(
        rule_id="verified",
        number="15.1",
        marks=1,
        kind="calculation",
        command_word="prepare",
        topic_id="partnerships",
        prompt="Prepare the verified capital accounts.",
        mark_scheme=[verified_point.text],
        structured_mark_scheme=[verified_point],
        assessment_objectives={"AO2": 1},
        authoring_context={
            "preserve_prompt": True,
            "preserve_mark_scheme": True,
        },
    )
    task = _Task(
        key=(0, 0, 0),
        question=question,
        option=GeneratedOption(id="case", title="Partnership", questions=[question]),
        topic=object(),
    )

    class Client:
        provider = "ollama"
        model = "test"

        def generate_json(self, _prompt: str) -> dict[str, object]:
            raise AssertionError("verified contracts must not invoke the model")

    class Checkpoint:
        def load_item(self, _key: str) -> GeneratedQuestion | None:
            raise AssertionError("verified contracts must not reload a checkpoint")

    result = _generate_batch(
        [task],
        client=Client(),
        subject="accounting",
        seed=1,
        policy=GenerationPolicy(),
        progress=None,
        checkpoint_store=Checkpoint(),  # type: ignore[arg-type]
    )

    assert result[task.key].prompt == question.prompt
    assert result[task.key].provenance == "verified-contract"


def test_rejected_second_item_does_not_regenerate_accepted_first_item() -> None:
    first = GeneratedQuestion(
        rule_id="q1",
        number="1",
        marks=1,
        kind="explain",
        command_word="explain",
        topic_id="topic",
        prompt="Explain how a cost change affects profit.",
        mark_scheme=["Higher costs reduce profit, other things being equal."],
        assessment_objectives={"AO1": 1},
    )
    second = first.model_copy(
        update={
            "rule_id": "q2",
            "number": "2",
            "prompt": "Explain how an exchange-rate change affects imports.",
        }
    )
    option = GeneratedOption(
        id="option",
        title="Case study",
        questions=[first, second],
    )
    topic = type(
        "Topic",
        (),
        {"id": "topic", "title": "Applied economics", "points": []},
    )()
    tasks = [
        _Task(key=(0, 0, 0), question=first, option=option, topic=topic),
        _Task(key=(0, 0, 1), question=second, option=option, topic=topic),
    ]

    class ScriptedClient:
        provider = "ollama"
        model = "test"
        supports_parallel_generation = False

        def __init__(self) -> None:
            self.responses = iter(
                [
                    _question_response(
                        "0/0/0",
                        "Explain why higher costs can reduce a firm's profit.",
                    ),
                    _review_response("0/0/0", approved=True),
                    _question_response(
                        "0/0/1",
                        "Explain why a tariff always lowers import prices.",
                    ),
                    _review_response(
                        "0/0/1",
                        approved=False,
                        factual_issues=["The exchange-rate direction is reversed."],
                    ),
                    _question_response(
                        "0/0/1",
                        "Explain why a tariff can raise import prices.",
                    ),
                    _review_response("0/0/1", approved=True),
                ]
            )

        def generate_json(self, _prompt: str) -> dict[str, object]:
            return next(self.responses)

    generated = _generate_batch(
        tasks,
        client=ScriptedClient(),
        subject="Economics",
        seed=1,
        policy=GenerationPolicy(attempts=2),
        progress=None,
    )

    assert generated[tasks[0].key].prompt == (
        "Explain why higher costs can reduce a firm's profit."
    )
    assert generated[tasks[1].key].prompt == (
        "Explain why a tariff can raise import prices."
    )


def test_repair_prompt_targets_the_rejected_item_and_issues() -> None:
    question = GeneratedQuestion(
        rule_id="q1",
        number="1",
        marks=1,
        kind="explain",
        command_word="explain",
        topic_id="topic",
        prompt="Explain how exchange rates affect imports.",
        mark_scheme=["Credit a correct relationship."],
        assessment_objectives={"AO1": 1},
    )
    task = _Task(
        key=(0, 0, 0),
        question=question,
        option=GeneratedOption(id="option", title="Option", questions=[question]),
        topic=type(
            "Topic",
            (),
            {"id": "topic", "title": "Exchange rates", "points": []},
        )(),
    )
    candidate = question.model_copy(
        update={"prompt": "Explain why appreciation raises import costs."}
    )

    prompt = _repair_prompt(
        task,
        candidate,
        ReviewResult(
            approved=False,
            factual_issues=["The exchange-rate direction is reversed."],
        ),
        subject="Economics",
        seed=1,
        attempt=2,
    )

    assert "The exchange-rate direction is reversed." in prompt
    assert '"id": "0/0/0"' in prompt
    assert "other paper items" not in prompt.casefold()


def _question_response(item_id: str, prompt: str) -> dict[str, object]:
    return {
        "questions": [
            {
                "id": item_id,
                "prompt": prompt,
                "mark_scheme": [
                    {
                        "text": (
                            "The stated change affects the outcome through a "
                            "relevant causal relationship."
                        ),
                        "marks": 1,
                        "assessment_objective": "AO1",
                    }
                ],
            }
        ]
    }


def _review_response(
    item_id: str,
    *,
    approved: bool,
    factual_issues: list[str] | None = None,
) -> dict[str, object]:
    return {
        "reviews": [
            {
                "id": item_id,
                "approved": approved,
                "factual_issues": factual_issues or [],
                "marking_issues": [],
                "source_issues": [],
                "difficulty_issues": [],
                "ambiguity_issues": [],
            }
        ]
    }


def test_review_prompt_uses_structured_semantics_not_withheld_draft_prose() -> None:
    question = GeneratedQuestion(
        rule_id="q1",
        number="1",
        marks=4,
        kind="explain",
        command_word="explain",
        topic_id="topic",
        prompt="Explain the forbidden planning sentence about contestability.",
        mark_scheme=["Credit valid analysis."],
        assessment_objectives={"AO1": 1, "AO2": 1, "AO3": 2},
    )
    task = _Task(
        key=(0, 0, 0),
        question=question,
        option=GeneratedOption(id="option", title="Case study", questions=[question]),
        topic=type(
            "Topic",
            (),
            {"title": "Market structures", "points": ["Contestable markets"]},
        )(),
    )
    candidate = question.model_copy(
        update={"prompt": "Explain how contestability can influence a market."}
    )

    prompt = _review_prompt([task], [candidate], subject="Economics")

    assert '"required_task_terms": [' in prompt
    assert "forbidden planning sentence about contestability" not in prompt.casefold()
    assert '"protected_numeric_tokens": []' in prompt
    assert "do not compare the candidate against withheld draft prose" in prompt


def test_points_scheme_prompt_requires_enough_distinct_awarded_rows() -> None:
    question = GeneratedQuestion(
        rule_id="q12",
        number="12",
        marks=7,
        kind="explain",
        command_word="explain",
        topic_id="topic",
        prompt="Explain the accounting treatment.",
        mark_scheme=["Credit valid accounting treatment."],
        assessment_objectives={"AO1": 2, "AO2": 2, "AO3": 3},
    )

    entries = _required_awarded_entries(question)

    assert len(entries) == 7
    assert {entry["marks"] for entry in entries} == {1}
    assert [entry["assessment_objective"] for entry in entries].count("AO3") == 3


def test_high_mark_points_scheme_caps_rows_without_losing_ao_marks() -> None:
    question = GeneratedQuestion(
        rule_id="q16",
        number="16",
        marks=12,
        kind="analysis",
        command_word="analyse",
        topic_id="topic",
        prompt="Analyse the accounting decision.",
        mark_scheme=["Credit developed analysis."],
        assessment_objectives={"AO1": 3, "AO2": 3, "AO3": 6},
    )

    entries = _required_awarded_entries(question)

    assert len(entries) == 8
    assert sum(int(entry["marks"]) for entry in entries) == 12
    for objective, marks in question.assessment_objectives.items():
        assert sum(
            int(entry["marks"])
            for entry in entries
            if entry["assessment_objective"] == objective
        ) == marks


def test_levels_scheme_uses_ao_allocations_and_descriptors() -> None:
    question = GeneratedQuestion(
        rule_id="q1",
        number="1",
        marks=12,
        kind="analysis",
        command_word="analyse",
        topic_id="topic",
        prompt="Analyse the decision.",
        mark_scheme=["Levels-based marking."],
        assessment_objectives={"AO1": 3, "AO2": 3, "AO3": 6},
        scheme_mode="levels",
    )
    points = [
        MarkSchemePoint(
            text="Accurate knowledge.",
            marks=3,
            assessment_objective="AO1",
        ),
        MarkSchemePoint(
            text="Applied case evidence.",
            marks=3,
            assessment_objective="AO2",
        ),
        MarkSchemePoint(
            text="Developed chain of reasoning.",
            marks=6,
            assessment_objective="AO3",
        ),
        *[
            MarkSchemePoint(
                text=f"Level {level} descriptor.",
                marks=0,
                credit_type="level",
            )
            for level in range(1, 4)
        ],
    ]

    _validate_mark_points(question, points)


def test_levels_scheme_requires_explicit_descriptors() -> None:
    import pytest

    question = GeneratedQuestion(
        rule_id="q1",
        number="1",
        marks=12,
        kind="analysis",
        command_word="analyse",
        topic_id="topic",
        prompt="Analyse the decision.",
        mark_scheme=["Levels-based marking."],
        assessment_objectives={"AO1": 3, "AO2": 3, "AO3": 6},
        scheme_mode="levels",
    )
    points = [
        MarkSchemePoint(
            text="Knowledge.",
            marks=3,
            assessment_objective="AO1",
        ),
        MarkSchemePoint(
            text="Application.",
            marks=3,
            assessment_objective="AO2",
        ),
        MarkSchemePoint(
            text="Analysis.",
            marks=6,
            assessment_objective="AO3",
        ),
    ]

    with pytest.raises(ValueError, match="level descriptors"):
        _validate_mark_points(question, points)


@pytest.mark.parametrize(
    "text",
    [
        "Indicative content",
        "Award each reason only when it is developed in the business context.",
        "Examiner guidance: accept any other reasonable response.",
    ],
)
def test_awarded_mark_points_reject_examiner_meta_guidance(text: str) -> None:
    question = GeneratedQuestion(
        rule_id="q1",
        number="1",
        marks=1,
        kind="short_answer",
        command_word="state",
        topic_id="topic",
        prompt="State one valid reason.",
        mark_scheme=["One valid reason."],
        assessment_objectives={"AO1": 1},
    )

    with pytest.raises(ValueError, match="candidate answer content"):
        _validate_mark_points(
            question,
            [
                MarkSchemePoint(
                    text=text,
                    marks=1,
                    assessment_objective="AO1",
                )
            ],
        )


def test_levels_scheme_normalises_model_arithmetic_to_blueprint() -> None:
    question = GeneratedQuestion(
        rule_id="q1",
        number="1",
        marks=12,
        kind="analysis",
        command_word="analyse",
        topic_id="topic",
        prompt="Analyse the decision.",
        mark_scheme=["Levels-based marking."],
        assessment_objectives={"AO1": 3, "AO2": 3, "AO3": 6},
        scheme_mode="levels",
    )
    raw = [
        MarkSchemePoint(
            text="Knowledge.",
            marks=1,
            assessment_objective="AO1",
        ),
        MarkSchemePoint(
            text="Application.",
            marks=1,
            assessment_objective="AO2",
        ),
        MarkSchemePoint(
            text="Analysis.",
            marks=1,
            assessment_objective="AO3",
        ),
        *[
            MarkSchemePoint(
                text=f"Level {level}.",
                marks=level,
                credit_type="level",
                assessment_objective="AO3",
            )
            for level in range(1, 4)
        ],
    ]

    normalised = _normalise_level_allocations(question, raw)

    assert [point.marks for point in normalised] == [
        3,
        3,
        6,
        0,
        0,
        0,
        0,
        0,
        0,
    ]
    assert sum(point.marks for point in normalised) == 12
    _validate_mark_points(question, normalised)


def test_levels_scheme_recovers_unlabelled_substantive_ao_content() -> None:
    question = GeneratedQuestion(
        rule_id="q1",
        number="1",
        marks=12,
        kind="analysis",
        command_word="analyse",
        topic_id="topic",
        prompt="Analyse the decision.",
        mark_scheme=["Levels-based marking."],
        assessment_objectives={"AO1": 3, "AO2": 3, "AO3": 6},
        scheme_mode="levels",
    )
    raw = [
        MarkSchemePoint(
            text="Accurate knowledge of the business concept.",
            marks=1,
            assessment_objective="AO1",
        ),
        MarkSchemePoint(
            text="Application to the source evidence and business context.",
            marks=1,
            assessment_objective="AO2",
        ),
        MarkSchemePoint(
            text=(
                "A developed causal chain showing the effect on costs and "
                "therefore the consequence for profit."
            ),
            marks=0,
            assessment_objective=None,
        ),
        MarkSchemePoint(
            text="Additional acceptable indicative content.",
            marks=2,
            assessment_objective="AO2",
        ),
        *[
            MarkSchemePoint(
                text=f"Level {level}.",
                marks=level,
                credit_type="level",
                assessment_objective="AO3",
            )
            for level in range(1, 4)
        ],
    ]

    normalised = _normalise_level_allocations(question, raw)

    awarded = [point for point in normalised if point.marks]
    assert [(point.assessment_objective, point.marks) for point in awarded] == [
        ("AO1", 3),
        ("AO2", 3),
        ("AO3", 6),
    ]
    assert next(
        point for point in normalised if point.text.startswith("Additional")
    ).credit_type == "guidance"
    _validate_mark_points(question, normalised)


def test_levels_scheme_adds_missing_objective_rubric_row() -> None:
    question = GeneratedQuestion(
        rule_id="q1",
        number="1",
        marks=12,
        kind="analysis",
        command_word="analyse",
        topic_id="topic",
        prompt="Analyse the decision.",
        mark_scheme=["Levels-based marking."],
        assessment_objectives={"AO1": 3, "AO2": 3, "AO3": 6},
        scheme_mode="levels",
    )
    raw = [
        MarkSchemePoint(
            text="Accurate understanding of the concept.",
            marks=1,
            assessment_objective="AO1",
        ),
        MarkSchemePoint(
            text="Application to the source evidence.",
            marks=1,
            assessment_objective="AO2",
        ),
        *[
            MarkSchemePoint(
                text=f"Level {level}.",
                marks=level,
                credit_type="level",
                assessment_objective="AO3",
            )
            for level in range(1, 4)
        ],
    ]

    normalised = _normalise_level_allocations(question, raw)

    assert [point.assessment_objective for point in normalised[:3]] == [
        "AO1",
        "AO2",
        "AO3",
    ]
    assert "allocation within the levels grid" in normalised[2].text
    assert [point.marks for point in normalised[:3]] == [3, 3, 6]
    assert any(point.alternatives for point in normalised)
    assert any(point.do_not_accept for point in normalised)
    _validate_mark_points(question, normalised)
