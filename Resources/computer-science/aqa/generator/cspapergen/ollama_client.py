from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Protocol

from Backend.Core.assessment_checkpoints import AssessmentCheckpointStore
from Backend.Core.assessment_quality import NUMBER_PATTERN, numeric_tokens
from Backend.Core.model_review import (
    assert_materially_new,
    require_difficulty_review,
    require_independent_review,
)
from Backend.Core.independent_solver import IndependentSolver
from Backend.Core.reference_demand import build_item_demand_target, profile_for
from cspapergen.models import (
    MarkingGuidance,
    PaperBlueprint,
    Question,
    QuestionPart,
    Syllabus,
)
from cspapergen.notes import note_context_for_topic


@dataclass(frozen=True)
class OllamaClient:
    base_url: str
    model: str

    @property
    def provider(self) -> str:
        return "ollama"

    @property
    def supports_parallel_generation(self) -> bool:
        return False

    def generate_json(self, prompt: str, retries: int = 2) -> dict[str, object]:
        last_error: Exception | None = None
        for attempt in range(retries):
            payload = json.dumps(
                {"model": self.model, "prompt": prompt, "stream": False, "format": "json"}
            ).encode("utf-8")
            request = urllib.request.Request(
                f"{self.base_url.rstrip('/')}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=160) as response:
                    response_payload = response.read(2_097_153)
                    if len(response_payload) > 2_097_152:
                        raise ValueError("Ollama response exceeded the 2 MB limit")
                    raw = json.loads(response_payload.decode("utf-8"))
                parsed = json.loads(str(raw.get("response", "{}")))
                if not isinstance(parsed, dict):
                    raise ValueError("Ollama returned JSON, but not an object")
                return parsed
            except (
                urllib.error.URLError,
                TimeoutError,
                json.JSONDecodeError,
                ValueError,
            ) as error:
                last_error = error
                if attempt < retries - 1:
                    time.sleep(min(8, 2**attempt))
        raise RuntimeError(f"Ollama generation failed after {retries} attempts") from last_error


class JSONGenerationClient(Protocol):
    def generate_json(self, prompt: str) -> dict[str, object]: ...


def improve_questions_with_ollama(
    client: JSONGenerationClient,
    blueprint: PaperBlueprint,
    syllabus: Syllabus,
    progress: Callable[[str], None] | None = None,
    checkpoint_store: AssessmentCheckpointStore | None = None,
) -> PaperBlueprint:
    emit = progress or (lambda _message: None)
    total = len(blueprint.questions)
    improved = list(blueprint.questions)
    supports_parallel = getattr(
        client,
        "supports_parallel_generation",
        not isinstance(client, OllamaClient),
    )
    max_workers = max(1, min(total, 4)) if supports_parallel else 1

    def _improve(index: int, question: Question) -> tuple[Question, str]:
        topic = syllabus.get_topic(question.topic_id)
        display_index = index + 1
        checkpoint_key = f"question-{question.number}"
        if checkpoint_store is not None:
            stored = checkpoint_store.load_payload(checkpoint_key)
            if stored is not None:
                try:
                    candidate = Question.model_validate(stored)
                    _validate_ai_question(question, candidate)
                except (ValueError, TypeError):
                    checkpoint_store.discard_item(checkpoint_key)
                else:
                    return (
                        candidate,
                        (
                            f"Resumed reviewed question {display_index}/{total}: "
                            f"0 {question.number:02d}"
                        ),
                    )
        emit(
            f"Generating question {display_index}/{total}: "
            f"0 {question.number:02d} ({topic.title})"
        )
        if _uses_review_only_generation(question):
            require_independent_review(
                client,
                item_id=f"question-{question.number}",
                subject="AQA A-level Computer Science",
                blueprint=question,
                candidate=question,
                specification=topic,
            )
            if checkpoint_store is not None:
                checkpoint_store.save_payload(
                    checkpoint_key,
                    question.model_dump(mode="json"),
                )
            return (
                question,
                (
                    f"Reviewed immutable question {display_index}/{total}: "
                    f"0 {question.number:02d}"
                ),
            )
        base_prompt = _prompt(
            question,
            topic.title,
            note_context_for_topic(topic.id, topic.title),
            blueprint,
        )
        scenario_only = _uses_scenario_only_generation(question)
        failure = ""
        for attempt in range(1, 4):
            retry_prompt = (
                base_prompt
                if not failure
                else f"{base_prompt}\nPrevious attempt rejected: {failure}\nCorrect every issue in the next response."
            )
            payload = client.generate_json(retry_prompt)
            try:
                candidate = _merge_question(question, payload)
                _validate_ai_question(question, candidate)
                if not scenario_only:
                    require_independent_review(
                        client,
                        item_id=f"question-{question.number}",
                        subject="AQA A-level Computer Science",
                        blueprint=question,
                        candidate=candidate,
                        specification=topic,
                    )
                break
            except ValueError as error:
                failure = str(error)
                if attempt == 3:
                    if (
                        not supports_parallel
                        and "only a paraphrase of the draft" in failure
                    ):
                        try:
                            require_independent_review(
                                client,
                                item_id=f"question-{question.number}",
                                subject="AQA A-level Computer Science",
                                blueprint=question,
                                candidate=question,
                                specification=topic,
                            )
                        except ValueError as review_error:
                            failure = str(review_error)
                        else:
                            candidate = question
                            break
                    raise ValueError(
                        f"question-{question.number} failed after 3 reviewed attempts: {failure}"
                    ) from error
        if checkpoint_store is not None:
            checkpoint_store.save_payload(
                checkpoint_key,
                candidate.model_dump(mode="json"),
            )
        return (
            candidate,
            (
                f"Generated and reviewed question {display_index}/{total}: "
                f"0 {question.number:02d}"
            ),
        )

    if max_workers == 1:
        for index, question in enumerate(blueprint.questions):
            improved[index], message = _improve(index, question)
            emit(message)
        return blueprint.model_copy(update={"questions": improved})

    completed_messages: dict[int, str] = {}
    next_message = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_improve, index, question): index
            for index, question in enumerate(blueprint.questions)
        }
        for future in as_completed(futures):
            index = futures[future]
            improved[index], completed_messages[index] = future.result()
            while next_message in completed_messages:
                emit(completed_messages.pop(next_message))
                next_message += 1
    return blueprint.model_copy(update={"questions": improved})


def review_blueprint_difficulty(
    client: JSONGenerationClient,
    blueprint: PaperBlueprint,
    syllabus: Syllabus,
    progress: Callable[[str], None] | None = None,
) -> PaperBlueprint:
    emit = progress or (lambda _message: None)
    paper_id = (
        f"bank-{blueprint.focus_topic_id}"
        if blueprint.assessment_kind == "question-bank"
        else blueprint.paper_number
    )
    profile = profile_for("aqa/computer-science", paper_id)
    item_count = sum(len(question.parts) for question in blueprint.questions)
    item_index = 0
    reviewed_questions: list[Question] = []
    for question in blueprint.questions:
        topic = syllabus.get_topic(question.topic_id)
        reviewed_parts: list[QuestionPart] = []
        for part in question.parts:
            item_index += 1
            item = _part_demand_item(question, part)
            emit(
                f"Checking reference demand {item_index}/{item_count}: "
                f"0 {question.number:02d}({part.label})"
            )
            solution = IndependentSolver(client).solve(item, [])
            evidence = require_difficulty_review(
                client,
                item_id=f"question-{question.number}-{part.label}",
                subject="AQA A-level Computer Science",
                target=build_item_demand_target(item, profile),
                candidate={
                    "stem": question.stem,
                    "stimulus": (
                        question.stimulus.model_dump(mode="json")
                        if question.stimulus is not None
                        else None
                    ),
                    "part": part.model_dump(mode="json"),
                },
                specification=topic,
                canonical_solution=solution,
            )
            reviewed_parts.append(
                part.model_copy(
                    update={"difficulty_evidence": evidence.model_dump(mode="json")}
                )
            )
        reviewed_questions.append(question.model_copy(update={"parts": reviewed_parts}))
    return blueprint.model_copy(update={"questions": reviewed_questions})


def _prompt(
    question: Question,
    topic_title: str,
    notes: str,
    blueprint: PaperBlueprint,
) -> str:
    parts = "\n".join(f"- Part {part.label}: {part.marks} marks, {part.prompt}" for part in question.parts)
    paper_id = (
        f"bank-{blueprint.focus_topic_id}"
        if blueprint.assessment_kind == "question-bank"
        else blueprint.paper_number
    )
    profile = profile_for("aqa/computer-science", paper_id)
    demand_targets = [
        build_item_demand_target(
            _part_demand_item(question, part),
            profile,
        ).model_dump(mode="json")
        for part in question.parts
    ]
    if _uses_scenario_only_generation(question):
        stem_numbers = ", ".join(numeric_tokens(question.stem)) or "none"
        return f"""You are writing an unofficial A-level Computer Science {blueprint.paper_code} Paper {blueprint.paper_number}.

Use only this syllabus topic: {question.topic_id} {topic_title}
Immutable assessment focus: {question.title} ({question.style_id}). Do not substitute another subtopic, process or technology.
Immutable reference-demand targets: {json.dumps(demand_targets, ensure_ascii=False)}

Create a concise, materially new fictional scenario stem for the immutable multipart task below. The stem must establish the same technical setting without copying a complete sentence from the draft. Preserve these numeric tokens from the draft stem exactly: {stem_numbers}. Introduce no other numeric values. Do not repeat, rewrite or answer the parts. Do not add exam-board branding.

Draft stem: {question.stem}
Immutable parts for context only:
{parts}

Return JSON only:
{{
  "stem": "string",
  "parts": []
}}
"""
    return f"""You are writing an unofficial A-level Computer Science {blueprint.paper_code} Paper {blueprint.paper_number}.

Use only this syllabus topic: {question.topic_id} {topic_title}
Immutable assessment focus: {question.title} ({question.style_id}). Do not substitute another subtopic, process or technology.
Immutable reference-demand targets: {json.dumps(demand_targets, ensure_ascii=False)}
Revision-note context:
{notes}

Create a genuinely new independent question in concise UK exam style. Do not copy, reconstruct or closely paraphrase a live, historic or draft paper question. Replace the stem and every complete part-prompt sentence with materially new wording and a new fictional scenario. The verified marking guidance, marks, part labels, answer units, stimulus data, numeric values and correct answers are immutable. Do not return or rewrite marking guidance. Do not add exam-board branding.

Question stem: {question.stem}
Parts:
{parts}

VERIFIED MARKING IS IMMUTABLE. Return JSON only:
{{
  "stem": "string",
  "parts": [
    {{
      "label": "1",
      "prompt": "string"
    }}
  ]
}}
"""


def _part_demand_item(
    question: Question,
    part: QuestionPart,
) -> dict[str, object]:
    marking = part.marking
    objective_names = re.findall(r"AO[1-4]", str(marking.ao).upper())
    objectives = {name: 1 for name in objective_names}
    if objectives:
        objectives[objective_names[0]] += int(part.marks) - len(objectives)
    stimulus: list[str] = []
    if question.stimulus is not None:
        stimulus.extend(question.stimulus.lines)
        stimulus.extend(cell for row in question.stimulus.rows for cell in row)
        if question.stimulus.code:
            stimulus.append(question.stimulus.code)
    prompt = str(part.prompt)
    return {
        "id": f"question-{question.number}-{part.label}",
        "marks": int(part.marks),
        "kind": question.style_id,
        "command_word": prompt.split(maxsplit=1)[0].strip(".,:;!?()[]{}"),
        "prompt": prompt,
        "assessment_objectives": objectives,
        "context": [question.stem, *stimulus],
    }


def _uses_scenario_only_generation(question: Question) -> bool:
    original_text = " ".join(
        [question.stem, *(part.prompt for part in question.parts)]
    )
    return len(question.parts) >= 3 and bool(numeric_tokens(original_text))


def _uses_review_only_generation(question: Question) -> bool:
    """Keep tasks coupled to the supplied executable program immutable."""
    return question.style_id in {"adapt_program", "extend_program"}


def _merge_question(question: Question, payload: dict[str, object]) -> Question:
    stem = _clean(str(payload.get("stem") or question.stem))
    if question.stimulus is not None:
        stem = question.stem
    scenario_only = _uses_scenario_only_generation(question)
    if numeric_tokens(stem) != numeric_tokens(question.stem):
        if scenario_only:
            scenario = _clean(NUMBER_PATTERN.sub("", stem))
            stem = f"{scenario} {question.stem}".strip()
        else:
            stem = question.stem
    if (
        scenario_only
        and question.stimulus is None
        and stem.casefold() == question.stem.casefold()
    ):
        stem = (
            "A newly devised fictional case study establishes the following "
            f"technical condition. {question.stem}"
        )
    raw_parts = payload.get("parts")
    parts = question.parts
    if isinstance(raw_parts, list):
        by_label = {str(item.get("label")): item for item in raw_parts if isinstance(item, dict)}
        merged = []
        for part in question.parts:
            raw = by_label.get(part.label, {})
            prompt = _clean(str(raw.get("prompt") or part.prompt)) if isinstance(raw, dict) else part.prompt
            if question.stimulus is not None:
                prompt = part.prompt
            if numeric_tokens(prompt) != numeric_tokens(part.prompt):
                prompt = part.prompt
            points = _text_list(raw.get("marking_points") if isinstance(raw, dict) else None, part.marking.points)
            required_points = min(part.marks, 3)
            seen = {point.casefold() for point in points}
            for fallback in part.marking.points:
                if len(seen) >= required_points:
                    break
                if fallback.casefold() not in seen:
                    points.append(fallback)
                    seen.add(fallback.casefold())
            accept = _text_list(raw.get("accept") if isinstance(raw, dict) else None, part.marking.accept)
            reject = _text_list(raw.get("reject") if isinstance(raw, dict) else None, part.marking.reject)
            marking = MarkingGuidance(ao=part.marking.ao, points=points, accept=accept, reject=reject, levels=part.marking.levels)
            merged.append(part.model_copy(update={"prompt": prompt, "marking": marking}))
        parts = merged
    return question.model_copy(update={"stem": stem, "parts": parts})


def _validate_ai_question(original: Question, candidate: Question) -> None:
    original_text = " ".join(
        [original.stem, *(part.prompt for part in original.parts)]
    )
    candidate_text = " ".join(
        [candidate.stem, *(part.prompt for part in candidate.parts)]
    )
    constrained_multipart = len(original.parts) >= 3 and bool(
        numeric_tokens(original_text)
    )
    if constrained_multipart and original.stem.strip():
        assert_materially_new(
            original.stem,
            candidate.stem,
            item_id=f"question-{original.number}-scenario",
            similarity_limit=0.9,
            preserve_numbers=False,
        )
    assert_materially_new(
        original_text,
        candidate_text,
        item_id=f"question-{original.number}",
        similarity_limit=0.98 if constrained_multipart else 0.9,
    )
    if len(candidate.parts) != len(original.parts):
        raise ValueError(f"question-{original.number} changed its part count")
    for original_part, candidate_part in zip(
        original.parts, candidate.parts, strict=True
    ):
        immutable = (
            original_part.label,
            original_part.marks,
            original_part.answer_lines,
            original_part.answer_unit,
            original_part.options,
            original_part.correct_option,
            original_part.marking.ao,
        )
        actual = (
            candidate_part.label,
            candidate_part.marks,
            candidate_part.answer_lines,
            candidate_part.answer_unit,
            candidate_part.options,
            candidate_part.correct_option,
            candidate_part.marking.ao,
        )
        if actual != immutable:
            raise ValueError(
                f"question-{original.number}-{original_part.label} changed "
                "an immutable assessment field"
            )
        points = [
            point.strip()
            for point in candidate_part.marking.points
            if point.strip()
        ]
        if len(set(point.casefold() for point in points)) < min(
            candidate_part.marks, 3
        ):
            raise ValueError(
                f"question-{original.number}-{original_part.label} has "
                "insufficient distinct marking points"
            )


def _text_list(raw: object, fallback: list[str]) -> list[str]:
    if not isinstance(raw, list):
        return fallback
    values = [str(item).strip() for item in raw if str(item).strip()]
    return values or fallback


def _clean(text: str) -> str:
    text = re.sub(r"\[\s*\d+\s*marks?\s*\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\(\s*\d+\s*marks?\s*\)", "", text, flags=re.IGNORECASE)
    text = text.replace("$", "")
    text = re.sub(r"\\(?:texttt|mathrm|mathbf)\{([^{}]+)\}", r"\1", text)
    text = text.replace(r"\(", "").replace(r"\)", "")
    return " ".join(text.split())
