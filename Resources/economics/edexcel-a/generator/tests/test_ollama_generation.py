import re
from pathlib import Path

import pytest
from pastpapergen.generator import build_paper_blueprint
from pastpapergen.ollama_client import (
    _clean_prompt,
    _merge_question_text,
    _merge_source_text,
    _validate_ai_question,
    generate_questions_with_ollama,
    review_blueprint_difficulty,
)
from pastpapergen.paper_configs import load_builtin_paper_config
from pastpapergen.syllabus import load_syllabus

from Backend.Core.assessment_checkpoints import (
    AssessmentCheckpointStore,
    identity_for_blueprint,
)

GUIDANCE = [
    "AO1: Defines the exact syllabus concept used in the question.",
    "AO1: Distinguishes the concept from a plausible alternative.",
    "AO2: Applies the concept directly to the stated market context.",
    "AO2: Uses the evidence in the source to support the application.",
    "AO3: Develops a causal chain from incentives to market outcomes.",
    "AO3: Explains the likely effect on consumers and producers.",
    "AO4: Identifies a condition that could change the predicted effect.",
    "AO4: Reaches a supported judgement tied to the question.",
]


def test_blueprint_receives_a_separate_reference_demand_review() -> None:
    syllabus = load_syllabus(
        Path(__file__).parents[1] / "data" / "syllabus_seed.json"
    )
    config = load_builtin_paper_config("paper_1")
    full = build_paper_blueprint(config, syllabus, seed=7)
    hardest = max(full.questions, key=lambda question: question.marks)
    blueprint = full.model_copy(update={"questions": [hardest]})

    class Client:
        def __init__(self) -> None:
            self.prompts: list[str] = []

        def generate_json(self, prompt: str) -> dict[str, object]:
            self.prompts.append(prompt)
            if "Independently solve" in prompt:
                return {
                    "answer": "A supported judgement.",
                    "steps": ["Analyse the evidence.", "Reach a judgement."],
                    "mark_points": [],
                    "evidence_ids": [],
                    "alternatives": [],
                    "partial_credit_boundaries": [],
                    "follow_through_rules": [],
                }
            return {
                "approved": True,
                "estimated_demand": "high",
                "reasoning_steps": 6,
                "tariff_fit": True,
                "command_word_fit": True,
                "context_fit": True,
                "profile_fit": True,
                "observed_cognitive_operations": ["retrieve", "apply", "transform", "explain", "contextualise", "analyse", "integrate", "judge"],
                "cognitive_operations_fit": True,
                "reasoning_range_fit": True,
                "shortcut_resistant": True,
                "timing_fit": True,
                "scaffolding_fit": True,
                "issues": [],
            }

    client = Client()
    reviewed = review_blueprint_difficulty(client, blueprint, syllabus)

    difficulty_prompts = [prompt for prompt in client.prompts if "difficulty calibration specialist" in prompt]
    assert len(difficulty_prompts) == 1
    assert '"reference_profile_fingerprint"' in difficulty_prompts[0]
    assert '"requires_judgement": true' in difficulty_prompts[0]
    assert reviewed.questions[0].difficulty_evidence["approved"] is True


class BlueprintAwareClient:
    supports_parallel_generation = True

    def generate_json(self, prompt: str) -> dict[str, object]:
        if "second-pass UK A-level assessment editor" in prompt:
            return {
                "approved": True,
                "factual_issues": [],
                "marking_issues": [],
                "source_issues": [],
                "difficulty_issues": [],
                "ambiguity_issues": [],
            }
        command = _line(prompt, "Command word")
        marks = int(_line(prompt, "Marks"))
        draft = _line(prompt, "Draft intent")
        reference_match = re.search(r"Extract [A-Z]", draft)
        reference = reference_match.group(0) if reference_match else ""
        question_text = _new_question(
            command=command,
            marks=marks,
            reference=reference,
        )
        draw = "4 marks, draw:" in _line(prompt, "Parts")
        part_a = (
            "Draw a cost and revenue diagram for a retailer choosing between "
            "two output objectives."
            if draw
            else (
                "With reference to the data above, explain how the evidence "
                "could alter a firm's pricing decision."
            )
        )
        return {
            "question_text": question_text,
            "source_text": "",
            "source_reference": reference,
            "mark_breakdown": "AO1 2, AO2 2, AO3 2, AO4 2",
            "indicative_content": GUIDANCE,
            "mark_scheme": GUIDANCE,
            "parts": [
                {
                    "label": "a",
                    "prompt": part_a,
                    "indicative_content": GUIDANCE,
                    "mark_scheme": GUIDANCE,
                },
                {
                    "label": "b",
                    "prompt": (
                        "Which one of the following is most likely to follow "
                        "from the changed incentive?"
                    ),
                    "options": [
                        {"label": "A", "text": "Output rises"},
                        {"label": "B", "text": "Scarcity disappears"},
                        {"label": "C", "text": "Demand becomes infinite"},
                        {"label": "D", "text": "All costs become fixed"},
                    ],
                    "correct_option": "A",
                    "indicative_content": [],
                    "mark_scheme": ["The only correct answer is A"],
                },
            ],
        }


class EmptyClient(BlueprintAwareClient):
    def generate_json(self, prompt: str) -> dict[str, object]:
        if "second-pass UK A-level assessment editor" in prompt:
            return super().generate_json(prompt)
        return {}


class RejectingReviewerClient(BlueprintAwareClient):
    def generate_json(self, prompt: str) -> dict[str, object]:
        if "second-pass UK A-level assessment editor" in prompt:
            return {
                "approved": False,
                "factual_issues": ["Unsupported causal claim"],
                "marking_issues": [],
                "source_issues": [],
                "difficulty_issues": [],
                "ambiguity_issues": [],
            }
        return super().generate_json(prompt)


def _line(prompt: str, label: str) -> str:
    match = re.search(rf"^{re.escape(label)}:\s*(.+)$", prompt, re.MULTILINE)
    assert match
    return match.group(1).strip()


def _new_question(*, command: str, marks: int, reference: str) -> str:
    prefix = f"With reference to {reference}, " if reference else ""
    if marks == 5:
        return (
            f"{prefix}explain how changing production technology could alter "
            "a growing firm's unit costs."
        )
    if marks == 8:
        return "Examine two ways limited management capacity could constrain expansion."
    if marks == 10:
        return "Assess whether lower barriers to entry will always improve competition."
    if marks == 12:
        return (
            f"{prefix}discuss whether vertical integration is preferable to "
            "expanding within the firm's existing market."
        )
    if marks == 15:
        return (
            f"{prefix}discuss how a demerger may affect workers, consumers "
            "and long-run costs."
        )
    if marks == 25:
        return (
            "Evaluate the likely microeconomic effects of a sustained fall in "
            "market concentration."
        )
    return f"{command.title()} the likely effect of a change in market incentives."


def _paper(seed: int = 5):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    return syllabus, build_paper_blueprint(config, syllabus, seed=seed)


def test_generation_reviews_fixed_stimuli_and_reauthors_extended_questions() -> None:
    syllabus, blueprint = _paper()
    events: list[str] = []

    generated = generate_questions_with_ollama(
        BlueprintAwareClient(),
        blueprint,
        syllabus,
        progress=events.append,
    )

    for original, candidate in zip(
        blueprint.questions, generated.questions, strict=True
    ):
        original_text = " ".join(
            [original.prompt, *(part.prompt for part in original.parts)]
        )
        candidate_text = " ".join(
            [candidate.prompt, *(part.prompt for part in candidate.parts)]
        )
        if original.section == "A" and original.stimulus_kind:
            assert candidate == original
        else:
            assert candidate_text != original_text
        assert candidate.marks == original.marks
        assert candidate.topic_id == original.topic_id
        assert [part.prompt for part in candidate.parts] == [
            part.prompt for part in original.parts
        ]
    assert events[0].startswith("Generating question 1/12: 1 ")
    assert events[-1].startswith("Generated and reviewed question 12/12: 8 ")


def test_generation_resumes_family_questions_from_checkpoint(
    tmp_path: Path,
) -> None:
    syllabus, blueprint = _paper()
    identity = identity_for_blueprint(
        {
            "paper_id": blueprint.paper_id,
            "seed": 5,
            "blueprint": blueprint.model_dump(mode="json"),
        },
        provider="ollama",
        model="test",
        prompt_version="edexcel-economics-v1",
    )
    store = AssessmentCheckpointStore(tmp_path / "job.json", identity)
    generated = generate_questions_with_ollama(
        BlueprintAwareClient(),
        blueprint,
        syllabus,
        checkpoint_store=store,
    )

    class NoCallsClient(BlueprintAwareClient):
        def generate_json(self, _prompt: str) -> dict[str, object]:
            raise AssertionError("accepted Edexcel questions must resume")

    resumed = generate_questions_with_ollama(
        NoCallsClient(),
        blueprint,
        syllabus,
        checkpoint_store=store,
    )

    assert resumed == generated


def test_resume_validation_rejects_changed_verified_marking_data() -> None:
    _syllabus, blueprint = _paper(seed=26080122)
    question = blueprint.questions[7]
    stale = question.model_copy(
        update={"mark_scheme": question.mark_scheme[:10]}
    )

    with pytest.raises(ValueError, match="verified assessment data"):
        _validate_ai_question(question, stale)


def test_generated_stem_cannot_exceed_reference_word_budget() -> None:
    _syllabus, blueprint = _paper(seed=26080122)
    question = blueprint.questions[7]
    verbose = question.model_copy(
        update={
            "prompt": question.prompt
            + " with additional unnecessary wording that changes the page rhythm"
        }
    )

    with pytest.raises(ValueError, match="stem word budget"):
        _validate_ai_question(question, verbose)


def test_generated_stem_preserves_required_specification_scope() -> None:
    _syllabus, blueprint = _paper(seed=26080122)
    question = blueprint.questions[6]
    narrowed = question.model_copy(
        update={
            "prompt": "Examine two conflicts between profit maximisation and revenue maximisation objectives."
        }
    )

    with pytest.raises(ValueError, match="required scope term"):
        _validate_ai_question(question, narrowed)

    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    paper_two = build_paper_blueprint(
        load_builtin_paper_config("paper_2"), syllabus, seed=26080123
    )
    policy_question = paper_two.questions[8]
    broadened = policy_question.model_copy(
        update={
            "prompt": "With reference to Extract C, discuss the likely effectiveness of supply-side policies."
        }
    )
    with pytest.raises(ValueError, match="training, childcare and infrastructure"):
        _validate_ai_question(policy_question, broadened)


def test_generation_rejects_unchanged_template_fallback() -> None:
    syllabus, full_blueprint = _paper()
    question = next(question for question in full_blueprint.questions if not question.parts)
    blueprint = full_blueprint.model_copy(update={"questions": [question]})

    with pytest.raises(ValueError, match="only a paraphrase"):
        generate_questions_with_ollama(EmptyClient(), blueprint, syllabus)


def test_generation_rejects_failed_second_pass_review() -> None:
    syllabus, blueprint = _paper()

    with pytest.raises(ValueError, match="Unsupported causal claim"):
        generate_questions_with_ollama(
            RejectingReviewerClient(),
            blueprint,
            syllabus,
        )


def test_local_generation_retries_only_the_rejected_question() -> None:
    syllabus, full_blueprint = _paper()
    question = next(
        question for question in full_blueprint.questions if not question.parts
    )
    blueprint = full_blueprint.model_copy(
        update={"questions": [question]}
    )

    class FlakyClient(BlueprintAwareClient):
        supports_parallel_generation = False

        def __init__(self) -> None:
            self.authoring_calls = 0

        def generate_json(self, prompt: str) -> dict[str, object]:
            if "second-pass UK A-level assessment editor" in prompt:
                return super().generate_json(prompt)
            self.authoring_calls += 1
            if self.authoring_calls == 1:
                return {}
            return super().generate_json(prompt)

    client = FlakyClient()
    generated = generate_questions_with_ollama(
        client,
        blueprint,
        syllabus,
    )

    assert client.authoring_calls == 2
    assert generated.questions[0].prompt != blueprint.questions[0].prompt


def test_local_generation_stops_before_queued_question_after_failure() -> None:
    syllabus, full_blueprint = _paper()
    questions = [
        question for question in full_blueprint.questions if not question.parts
    ][:2]
    blueprint = full_blueprint.model_copy(
        update={"questions": questions}
    )

    class RejectingLocalClient(EmptyClient):
        supports_parallel_generation = False

        def __init__(self) -> None:
            self.authoring_calls = 0

        def generate_json(self, prompt: str) -> dict[str, object]:
            if "second-pass UK A-level assessment editor" in prompt:
                return {
                    "approved": False,
                    "factual_issues": ["Seeded fallback remains invalid"],
                    "marking_issues": [],
                    "source_issues": [],
                    "difficulty_issues": [],
                    "ambiguity_issues": [],
                }
            self.authoring_calls += 1
            return {}

    client = RejectingLocalClient()
    with pytest.raises(ValueError, match="failed after 3 reviewed attempts"):
        generate_questions_with_ollama(client, blueprint, syllabus)

    assert client.authoring_calls == 3


def test_local_paper_three_uses_reviewed_seeded_fallback_after_paraphrases() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    full_blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_3"), syllabus, seed=26080124
    )
    question = full_blueprint.questions[0]
    blueprint = full_blueprint.model_copy(update={"questions": [question]})

    class ParaphrasingLocalClient(BlueprintAwareClient):
        supports_parallel_generation = False

        def __init__(self) -> None:
            self.authoring_calls = 0

        def generate_json(self, prompt: str) -> dict[str, object]:
            if "second-pass UK A-level assessment editor" in prompt:
                return super().generate_json(prompt)
            self.authoring_calls += 1
            return {"question_text": question.prompt, "parts": []}

    client = ParaphrasingLocalClient()
    generated = generate_questions_with_ollama(client, blueprint, syllabus)

    assert client.authoring_calls == 3
    assert generated.questions == [question]


def test_local_paper_one_uses_reviewed_source_bound_fallback_after_paraphrases() -> None:
    syllabus, full_blueprint = _paper(seed=26080122)
    question = full_blueprint.questions[5]
    blueprint = full_blueprint.model_copy(update={"questions": [question]})

    class ParaphrasingLocalClient(BlueprintAwareClient):
        supports_parallel_generation = False

        def __init__(self) -> None:
            self.authoring_calls = 0

        def generate_json(self, prompt: str) -> dict[str, object]:
            if "second-pass UK A-level assessment editor" in prompt:
                return super().generate_json(prompt)
            self.authoring_calls += 1
            return {"question_text": question.prompt}

    client = ParaphrasingLocalClient()
    generated = generate_questions_with_ollama(client, blueprint, syllabus)

    assert client.authoring_calls == 3
    assert generated.questions == [question]


def test_local_generation_uses_reviewed_fallback_after_scope_drift() -> None:
    syllabus, full_blueprint = _paper(seed=26080122)
    question = full_blueprint.questions[6]
    blueprint = full_blueprint.model_copy(update={"questions": [question]})

    class ScopeDriftClient(BlueprintAwareClient):
        supports_parallel_generation = False

        def __init__(self) -> None:
            self.authoring_calls = 0

        def generate_json(self, prompt: str) -> dict[str, object]:
            if "second-pass UK A-level assessment editor" in prompt:
                return super().generate_json(prompt)
            self.authoring_calls += 1
            return {
                "question_text": "Examine two conflicts between profit maximisation and revenue maximisation objectives."
            }

    client = ScopeDriftClient()
    generated = generate_questions_with_ollama(client, blueprint, syllabus)

    assert client.authoring_calls == 3
    assert generated.questions == [question]


def test_multipart_question_keeps_verified_stem_and_source_separate() -> None:
    _syllabus, blueprint = _paper()
    question = blueprint.questions[0]

    merged = _merge_question_text(
        question,
        "A newly established bicycle repair market faces changing input costs.",
    )

    assert merged == question.prompt
    assert "bicycle repair market" not in merged

    fallback = _merge_question_text(question, question.prompt)
    assert fallback == question.prompt


def test_exact_data_chart_is_reviewed_without_model_rewriting() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    full_blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_2"), syllabus, seed=26080123
    )
    question = full_blueprint.questions[0]
    blueprint = full_blueprint.model_copy(update={"questions": [question]})

    class ReviewClient:
        supports_parallel_generation = False
        authoring_calls = 0

        def generate_json(self, prompt: str) -> dict[str, object]:
            if "second-pass UK A-level assessment editor" not in prompt:
                self.authoring_calls += 1
            return {
                "approved": True,
                "factual_issues": [],
                "marking_issues": [],
                "source_issues": [],
                "difficulty_issues": [],
                "ambiguity_issues": [],
            }

    client = ReviewClient()
    generated = generate_questions_with_ollama(client, blueprint, syllabus)

    assert client.authoring_calls == 0
    assert generated.questions == [question]
    assert generated.questions[0].graph_params == question.graph_params


def test_section_a_context_and_stem_remain_bound_to_rendered_source() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_1"), syllabus, seed=26080122
    )
    question = blueprint.questions[3]

    assert _merge_question_text(question, "A consumer has £30 available.") == question.prompt
    assert _merge_source_text(
        "A consumer has £30 available.", question.source_text, question
    ) == question.source_text


def test_generated_paper_three_prompt_restores_numbered_source_reference() -> None:
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_3"), syllabus, seed=26080124
    )
    question = blueprint.questions[0]

    merged = _merge_question_text(
        question,
        "With reference to the diagram and Extract A, explain why energy supply may respond slowly to a price rise.",
    )

    assert "Figure 1 and Extract A" in merged
    assert "the diagram" not in merged


def test_source_length_guard_keeps_layout_safe_fallback() -> None:
    _syllabus, blueprint = _paper()
    section_a = blueprint.questions[0]
    section_b = next(
        question
        for question in blueprint.questions
        if question.section == "B" and question.source_text
    )

    assert (
        _merge_source_text("word " * 80, section_a.source_text, section_a)
        == section_a.source_text
    )
    assert (
        _merge_source_text("too short", section_b.source_text, section_b)
        == section_b.source_text
    )


def test_prompt_cleaning_removes_renderer_owned_marks_and_figure_labels() -> None:
    cleaned = _clean_prompt(
        "(a) Explain the change shown in Figure 1. [5 marks] "
        "Consider both positive and negative arguments to support your answer."
    )

    assert "[5 marks]" not in cleaned
    assert "Figure 1" not in cleaned
    assert "the diagram" in cleaned
    assert "positive and negative" not in cleaned
