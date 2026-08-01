import re
from pathlib import Path

import pytest

from pastpapergen.generator import build_paper_blueprint
from pastpapergen.ollama_client import (
    _clean_prompt,
    _merge_source_text,
    generate_questions_with_ollama,
)
from pastpapergen.paper_configs import load_builtin_paper_config
from pastpapergen.syllabus import load_syllabus


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


class BlueprintAwareClient:
    supports_parallel_generation = True

    def generate_json(self, prompt: str) -> dict[str, object]:
        if "independent UK A-level assessment editor" in prompt:
            return {
                "approved": True,
                "factual_issues": [],
                "marking_issues": [],
                "source_issues": [],
                "difficulty_issues": [],
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
        if "independent UK A-level assessment editor" in prompt:
            return super().generate_json(prompt)
        return {}


class RejectingReviewerClient(BlueprintAwareClient):
    def generate_json(self, prompt: str) -> dict[str, object]:
        if "independent UK A-level assessment editor" in prompt:
            return {
                "approved": False,
                "factual_issues": ["Unsupported causal claim"],
                "marking_issues": [],
                "source_issues": [],
                "difficulty_issues": [],
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
            f"{prefix}discuss the likely effects of a demerger on workers, "
            "consumers and the firm's long-run costs."
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


def test_generation_replaces_every_draft_and_runs_review() -> None:
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
        assert candidate_text != original_text
        assert candidate.marks == original.marks
        assert candidate.topic_id == original.topic_id
    assert events[0].startswith("Generating question 1/12: 1 ")
    assert events[-1].startswith("Generated and reviewed question 12/12: 8 ")


def test_generation_rejects_unchanged_template_fallback() -> None:
    syllabus, blueprint = _paper()

    with pytest.raises(ValueError, match="only a paraphrase"):
        generate_questions_with_ollama(EmptyClient(), blueprint, syllabus)


def test_generation_rejects_failed_independent_review() -> None:
    syllabus, blueprint = _paper()

    with pytest.raises(ValueError, match="Unsupported causal claim"):
        generate_questions_with_ollama(
            RejectingReviewerClient(),
            blueprint,
            syllabus,
        )


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
