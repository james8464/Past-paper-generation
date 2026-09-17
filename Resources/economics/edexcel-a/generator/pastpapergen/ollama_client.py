from __future__ import annotations

import json
import logging
import re
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from threading import Lock

from Backend.Core.assessment_checkpoints import AssessmentCheckpointStore
from Backend.Core.assessment_contracts import EvidenceRecord
from Backend.Core.assessment_quality import (
    validate_economics_causal_direction,
)
from Backend.Core.candidate_identity import edexcel_difficulty_candidate_projection
from Backend.Core.independent_solver import (
    IndependentSolver,
    require_solution_matches_scheme,
)
from Backend.Core.model_review import (
    assert_materially_new,
    require_difficulty_review,
    require_independent_review,
)
from Backend.Core.reference_demand import build_item_demand_target, profile_for
from pastpapergen.extended_scenarios import SCENARIOS
from pastpapergen.models import (
    MultipleChoiceOption,
    PaperBlueprint,
    QuestionBlueprint,
    QuestionPart,
    Syllabus,
    SyllabusTopic,
)
from pastpapergen.notes import note_context_for_topic
from pastpapergen.render_pdf import candidate_stimulus_data

_logger = logging.getLogger(__name__)


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
            try:
                return self._call(prompt)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as error:
                last_error = error
                if attempt < retries - 1:
                    delay = 2 ** attempt * 5
                    _logger.warning("Ollama call failed (attempt %d/%d), retrying in %ds: %s", attempt + 1, retries, delay, error)
                    time.sleep(delay)
        raise RuntimeError(f"Ollama request failed after {retries} retries") from last_error

    def _call(self, prompt: str) -> dict[str, object]:
        payload = json.dumps(
            {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "think": False,
                "options": {
                    "temperature": 0.45,
                    "num_predict": 1600,
                },
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url.rstrip('/')}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=240) as response:
            payload = response.read(2_097_153)
            if len(payload) > 2_097_152:
                raise ValueError("Ollama response exceeded the 2 MB limit")
            raw = json.loads(payload.decode("utf-8"))
        raw_dict = raw if isinstance(raw, dict) else {}
        text = str(raw_dict.get("response", "{}"))
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise json.JSONDecodeError("Expected dict", text, 0)
        return parsed


def build_question_prompt(
    question: QuestionBlueprint,
    topic: SyllabusTopic,
    paper_id: str | None = None,
) -> str:
    points = "\n".join(f"- {point}" for point in topic.points)
    note_context = note_context_for_topic(
        topic.id,
        title=topic.title,
        keywords=topic.points,
    )[:1800]
    demand_target = ""
    if paper_id is not None:
        profile = profile_for(
            "pearson-edexcel/economics-a-2015",
            _normalise_profile_paper_id(paper_id),
        )
        targets = [
            build_item_demand_target(item, profile).model_dump(mode="json")
            for item in _question_demand_items(question)
        ]
        demand_target = (
            "\nImmutable reference-demand targets (one per rendered item):\n"
            f"{json.dumps(targets, sort_keys=True)}\n"
            "Match each target's cognitive depth, reasoning chain, context use, "
            "and judgement requirement exactly; do not make it easier or harder.\n"
        )
    return f"""You are writing an unofficial A-Level Economics paper.

Use only this syllabus topic:
Topic ID: {topic.id}
Theme: {topic.theme}
Title: {topic.title}
Syllabus points (you must align every mark scheme bullet to these):
{points}

Revision-note context for factual grounding:
{note_context}

Write one genuinely new, independent Edexcel A-style question. Do not copy, reconstruct, or closely paraphrase any live, historic, or draft paper question.
Question number: {question.number}
Section: {question.section}
Marks: {question.marks}
Command word: {question.command_word}
Parts: {_parts_for_prompt(question)}
Stimulus kind: {question.stimulus_kind or "none"}
Draft intent: {question.prompt}
Verified source context: {question.source_text[:1600] or "none"}
Authoring task: {"Return a new one- or two-sentence fictional scenario context in question_text; do not repeat the multipart wrapper or any part prompt." if question.parts else "Return a materially new question that preserves the command word and source-reference pattern."}
{demand_target}

Style rules:
- Match the command word exactly: {question.command_word}.
- Preserve the command word and source reference pattern from the draft intent.
- Keep question_text to at most {max(12, len(question.prompt.split()) + 2)} words so it fits the measured examiner-paper layout.
- Preserve these specification scope terms verbatim when present: {', '.join(_required_scope_terms(question)) or 'none'}.
- Preserve the exact task framing. In particular, do not turn a question asking for one likely effect on an outcome into a question about how a policy tool is used.
- 12-mark questions usually use discuss whether, discuss the extent, or to what extent.
- 10-mark questions usually use assess whether, assess the, or to what extent.
- For Section A, match the stimulus kind: graph, table, pay-off matrix, line graph or short context.
- The verified source text, source reference, options, keyed answer, mark breakdown, mark scheme and indicative content are immutable. Do not return or rewrite them.
- Do not add instructions such as 'Consider both positive and negative arguments' or 'include relevant theories'.
- Do not include '(4 marks)' or similar mark text in any question or part text.
- If parts are supplied, rewrite each part separately rather than combining the parts into the main question text.
- Do not start part prompts with labels such as '(a)', 'a)' or 'Question 1(a)' because labels are rendered separately.
- If stimulus_kind is set, include a graph_params object with numeric values for equilibrium price and quantity that match the question context. This makes the diagram specific to the question data.
- Return every supplied part label exactly once. Return an empty parts array when Parts is none.

VERIFIED MARKING IS IMMUTABLE. Return only the compact authoring fields below.

Return JSON only with this schema:
{{
  "question_text": "string",
  "graph_params": {{
    "eq_price": <integer between 20 and 200, matching source data>,
    "eq_quantity": <integer between 30 and 300, matching source data>,
    "kind": <string: "demand_supply", "ad_as", "keynesian", "monopoly", "laffer", "labour", "externality", "ppf", "trade_cycle", "phillips", "lorenz", or "cost_revenue">
  }},
  "parts": [
    {{
      "label": "a",
      "prompt": "string"
    }}
  ]
}}
"""


def _parts_for_prompt(question: QuestionBlueprint) -> str:
    if not question.parts:
        return "none"
    return "; ".join(
        f"({part.label}) {part.marks} marks, {part.command_word}: {part.prompt}"
        for part in question.parts
    )


def generate_questions_with_ollama(
    client: OllamaClient,
    blueprint: PaperBlueprint,
    syllabus: Syllabus,
    progress: Callable[[str], None] | None = None,
    checkpoint_store: AssessmentCheckpointStore | None = None,
) -> PaperBlueprint:
    emit = progress or (lambda _message: None)
    total = len(blueprint.questions)
    results: dict[int, QuestionBlueprint] = {}
    results_lock = Lock()
    # Ollama serves one generation sequence per loaded local model. Sending several
    # long exam prompts at once only queues work inside the server and makes the
    # client-side requests time out. Hosted providers can still run concurrently.
    supports_parallel = getattr(
        client,
        "supports_parallel_generation",
        not isinstance(client, OllamaClient),
    )
    max_workers = max(1, min(total, 4)) if supports_parallel else 1

    def _build_task(question_index: int, question: QuestionBlueprint) -> str:
        index = question_index + 1
        checkpoint_key = f"question-{question.number}"
        if checkpoint_store is not None:
            stored = checkpoint_store.load_payload(checkpoint_key)
            if stored is not None:
                try:
                    candidate = QuestionBlueprint.model_validate(stored)
                    if _uses_review_only_generation(question) or candidate.provenance == "reviewed-deterministic-contract":
                        if candidate.model_copy(update={"provenance": question.provenance}) != question:
                            raise ValueError("stored immutable question changed")
                    else:
                        _validate_ai_question(question, candidate)
                except (ValueError, TypeError):
                    checkpoint_store.discard_item(checkpoint_key)
                else:
                    with results_lock:
                        results[question_index] = candidate
                    return (
                        f"Resumed reviewed question {index}/{total}: "
                        f"{question.number}"
                    )
        try:
            topic = syllabus.get_topic(question.topic_id)
        except KeyError as error:
            raise ValueError(
                f"unknown topic {question.topic_id!r} for question "
                f"{question.number}"
            ) from error
        emit(
            f"Generating question {index}/{total}: {question.number} "
            f"(Section {question.section}, {question.marks} marks, {topic.title})"
        )
        if _uses_review_only_generation(question):
            require_independent_review(
                client,
                item_id=f"question-{question.number}",
                subject="Edexcel A-level Economics A",
                blueprint=_multipart_review_view(question),
                candidate=_multipart_review_view(question),
                specification=_review_specification(topic, question),
            )
            reviewed = question.model_copy(update={"provenance": "reviewed-deterministic-contract"})
            if checkpoint_store is not None:
                checkpoint_store.save_payload(
                    checkpoint_key,
                    reviewed.model_dump(mode="json"),
                )
            with results_lock:
                results[question_index] = reviewed
            return (
                f"Reviewed immutable question {index}/{total}: "
                f"{question.number} ({topic.title})"
            )
        base_prompt = build_question_prompt(question, topic, blueprint.paper_id)
        failure = ""
        for attempt in range(1, 4):
            retry_prompt = (
                base_prompt
                if not failure
                else f"{base_prompt}\nPrevious attempt rejected: {failure}\nCorrect every issue in the next response."
            )
            payload = client.generate_json(retry_prompt)
            question_text = _merge_question_text(question, str(payload.get("question_text") or ""))
            source_text = _merge_source_text(str(payload.get("source_text") or ""), question.source_text, question)
            source_reference = question.source_reference
            # Source binding, answer data and AO allocation are immutable
            # properties of the verified paper plan, not creative model output.
            mark_breakdown = question.mark_breakdown
            indicative_content = question.indicative_content
            mark_scheme = question.mark_scheme
            parts = question.parts
            # Diagram geometry and numerical parameters are assessment data.
            # Keep the seeded blueprint values instead of accepting an unrelated
            # chart type invented by the authoring model.
            graph_params = question.graph_params
            candidate = question.model_copy(
                update={
                    "prompt": question_text,
                    "source_text": source_text,
                    "source_reference": source_reference,
                    "mark_breakdown": mark_breakdown,
                    "indicative_content": indicative_content,
                    "mark_scheme": mark_scheme,
                    "parts": parts,
                    "graph_params": graph_params,
                }
            )
            try:
                _validate_ai_question(question, candidate)
                require_independent_review(
                    client,
                    item_id=f"question-{question.number}",
                    subject="Edexcel A-level Economics A",
                    blueprint=_multipart_review_view(question),
                    candidate=_multipart_review_view(candidate),
                    specification=_review_specification(topic, candidate),
                )
                candidate = candidate.model_copy(update={"provenance": "ai-authored-stem-reviewed-contract"})
                break
            except ValueError as error:
                failure = str(error)
                if attempt == 3:
                    fallback_eligible = any(
                        reason in failure
                        for reason in (
                            "only a paraphrase of the draft",
                            "stem word budget",
                            "changed required scope term",
                        )
                    )
                    if (
                        not supports_parallel
                        and fallback_eligible
                    ):
                        try:
                            require_independent_review(
                                client,
                                item_id=f"question-{question.number}",
                                subject="Edexcel A-level Economics A",
                                blueprint=_multipart_review_view(question),
                                candidate=_multipart_review_view(question),
                                specification=_review_specification(topic, question),
                            )
                        except ValueError as review_error:
                            failure = str(review_error)
                        else:
                            candidate = question.model_copy(update={"provenance": "reviewed-deterministic-contract"})
                            break
                    raise ValueError(
                        f"question-{question.number} failed after 3 reviewed attempts: {failure}"
                    ) from error
        if checkpoint_store is not None:
            checkpoint_store.save_payload(
                checkpoint_key,
                candidate.model_dump(mode="json"),
            )
        with results_lock:
            results[question_index] = candidate
        return (
            f"Generated and reviewed question {index}/{total}: "
            f"{question.number} ({topic.title})"
        )

    if max_workers == 1:
        for index, question in enumerate(blueprint.questions):
            emit(_build_task(index, question))
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_build_task, i, question): i
                for i, question in enumerate(blueprint.questions)
            }
            completed_messages: dict[int, str] = {}
            next_message = 0
            for future in as_completed(futures):
                question_index = futures[future]
                completed_messages[question_index] = future.result()
                while next_message in completed_messages:
                    emit(completed_messages.pop(next_message))
                    next_message += 1
    questions = [results[i] for i in range(total)]
    return blueprint.model_copy(update={"questions": questions})


def review_blueprint_difficulty(
    client: object,
    blueprint: PaperBlueprint,
    syllabus: Syllabus,
    progress: Callable[[str], None] | None = None,
) -> PaperBlueprint:
    """Run an independent demand-only gate over every rendered question item."""

    emit = progress or (lambda _message: None)
    profile = profile_for(
        "pearson-edexcel/economics-a-2015",
        _normalise_profile_paper_id(blueprint.paper_id),
    )
    item_count = sum(len(_question_demand_items(question)) for question in blueprint.questions)
    item_index = 0
    reviewed_questions: list[QuestionBlueprint] = []
    for question in blueprint.questions:
        topic = syllabus.get_topic(question.topic_id)
        items = _question_demand_items(question)
        evidences: list[dict[str, object]] = []
        for item, part in zip(items, question.parts or [question], strict=True):
            item_index += 1
            label = str(item.get("label") or question.number)
            emit(f"Calibrating difficulty {item_index}/{item_count}: {question.number}{label}")
            projection = _question_solver_projection(question, part)
            solver_item = projection.item
            solution = IndependentSolver(client).solve(
                solver_item, projection.evidence
            )
            require_solution_matches_scheme(
                solution,
                solver_item,
                expected_choice=projection.expected_choice,
            )
            evidence = require_difficulty_review(
                client,
                item_id=f"question-{question.number}-{label}",
                subject="Edexcel A-level Economics A",
                candidate=_difficulty_candidate(
                    question,
                    part,
                    solver_item=solver_item,
                ),
                target=build_item_demand_target(item, profile),
                specification=_review_specification(topic, question),
                canonical_solution=solution,
            )
            evidences.append(evidence.model_dump(mode="json"))
        if question.parts:
            parts = [
                part.model_copy(update={"difficulty_evidence": evidence})
                for part, evidence in zip(question.parts, evidences, strict=True)
            ]
            reviewed_questions.append(question.model_copy(update={"parts": parts}))
        else:
            reviewed_questions.append(
                question.model_copy(update={"difficulty_evidence": evidences[0]})
            )
    return blueprint.model_copy(update={"questions": reviewed_questions})


def _normalise_profile_paper_id(paper_id: str) -> str:
    return str(paper_id).removeprefix("paper_").removeprefix("paper-")


def _question_solver_item(
    question: QuestionBlueprint, part: QuestionPart | QuestionBlueprint
) -> dict[str, object]:
    return _question_solver_projection(question, part).item


def _difficulty_candidate(
    question: QuestionBlueprint,
    part: QuestionPart | QuestionBlueprint,
    *,
    solver_item: dict[str, object] | None = None,
) -> object:
    return edexcel_difficulty_candidate_projection(
        question=question,
        part=part,
        review_content=(
            solver_item
            if solver_item is not None
            else _question_solver_projection(question, part).item
        ),
    )


@dataclass(frozen=True)
class _SolverProjection:
    item: dict[str, object]
    evidence: tuple[EvidenceRecord, ...]
    expected_choice: str | None


_PRIVATE_STIMULUS_KEYS = {
    "assessment_contract",
    "correct_choice",
    "correct_option",
    "difficulty_evidence",
    "indicative_content",
    "mark_breakdown",
    "mark_scheme",
    "structured_mark_scheme",
}


def _assert_public_stimulus(value: object) -> None:
    if isinstance(value, dict):
        private = _PRIVATE_STIMULUS_KEYS.intersection(value)
        if private:
            raise ValueError(
                "solver evidence contains private assessment fields: "
                f"{sorted(private)}"
            )
        for child in value.values():
            _assert_public_stimulus(child)
    elif isinstance(value, list):
        for child in value:
            _assert_public_stimulus(child)


def _validate_solver_projection(
    item: dict[str, object],
    evidence: list[EvidenceRecord] | tuple[EvidenceRecord, ...],
) -> None:
    stimulus = item.get("stimulus")
    if not isinstance(stimulus, dict):
        raise ValueError("Edexcel solver stimulus must be a public mapping")
    _assert_public_stimulus(stimulus)
    source_id = stimulus.get("source_id")
    if source_id is None:
        if evidence:
            raise ValueError("source-free Edexcel item cannot register evidence")
        return
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("Edexcel source identity must be non-empty")
    identities = [record.id for record in evidence]
    if len(evidence) != 1 or len(set(identities)) != len(identities):
        raise ValueError("Edexcel item requires one unique selected source")
    if identities != [source_id]:
        raise ValueError("Edexcel evidence identity differs from selected source")
    try:
        public_source = json.loads(evidence[0].text)
    except json.JSONDecodeError as error:
        raise ValueError("Edexcel evidence must contain the public source JSON") from error
    _assert_public_stimulus(public_source)
    if public_source != stimulus:
        raise ValueError("Edexcel evidence differs from selected public source")


def _question_solver_projection(
    question: QuestionBlueprint, part: QuestionPart | QuestionBlueprint
) -> _SolverProjection:
    options = getattr(part, "options", [])
    expected_choice = None
    correct_choice = None
    if options:
        labels = [option.label.strip().casefold() for option in options]
        if any(not label for label in labels) or len(set(labels)) != len(labels):
            raise ValueError("Edexcel choice labels must be non-empty and unique")
        key = str(getattr(part, "correct_option", "")).strip().casefold()
        matches = [index for index, label in enumerate(labels) if label == key]
        if len(matches) != 1:
            raise ValueError("Edexcel correct option must select one labelled choice")
        correct_choice = matches[0]
        expected_choice = options[correct_choice].text
    stimulus = candidate_stimulus_data(question)
    item = {
        **part.model_dump(mode="json"),
        "id": f"question-{question.number}-{getattr(part, 'label', question.number)}",
        "context": [question.prompt, question.source_text] if question.parts else question.source_text,
        "stimulus": stimulus,
        "kind": "multiple_choice" if options else question.stimulus_kind,
        "choices": [option.text for option in options],
        "authoring_context": {"expected_answer_form": (
            "numeric" if part.command_word.casefold() in {"calculate", "determine"}
            else "constructed_response"
        ), **({"economics_input_contract": {
            "source": question.source_instance.model_dump(mode="json"),
            "source_fingerprint": question.source_instance.fingerprint(),
            "requested_prompt": part.prompt, "marks": part.marks,
        }} if part.command_word == "calculate" and question.source_instance else {})},
    }
    if correct_choice is not None:
        item["correct_choice"] = correct_choice
    evidence = (
        (
            EvidenceRecord(
                id=str(stimulus.get("source_id", "")),
                text=json.dumps(stimulus, ensure_ascii=False, sort_keys=True),
            ),
        )
        if question.source_instance is not None
        else ()
    )
    _validate_solver_projection(item, evidence)
    return _SolverProjection(
        item=item,
        evidence=evidence,
        expected_choice=expected_choice,
    )


def _question_demand_items(question: QuestionBlueprint) -> list[dict[str, object]]:
    shared = {
        "kind": question.stimulus_kind or "written",
        "context": question.source_text,
        "source_reference": question.source_reference,
    }
    if question.parts:
        return [
            {
                **shared,
                "label": part.label,
                "marks": part.marks,
                "command_word": part.command_word,
                "prompt": part.prompt,
                "assessment_objectives": part.assessment_objectives,
            }
            for part in question.parts
        ]
    return [
        {
            **shared,
            "label": question.number,
            "marks": question.marks,
            "command_word": question.command_word,
            "prompt": question.prompt,
            "assessment_objectives": question.assessment_objectives,
        }
    ]


def _multipart_review_view(question: QuestionBlueprint) -> QuestionBlueprint:
    """Keep a multipart review focused on the rendered part-level guidance."""

    if not question.parts:
        return question
    return question.model_copy(
        update={
            "mark_breakdown": "",
            "mark_scheme": [],
            "indicative_content": [],
        }
    )


def _review_specification(
    topic: SyllabusTopic,
    question: QuestionBlueprint,
) -> dict[str, object]:
    return {
        "topic": topic.model_dump(mode="json"),
        "rendered_stimulus": {
            **candidate_stimulus_data(question),
            "description": _stimulus_description(question.stimulus_kind),
            "source_text": question.source_instance.context if question.source_instance else question.source_text,
            "placement": "Candidate source projection; question stem and part-level responses are reviewed separately.",
        },
    }


def _stimulus_description(kind: str) -> str:
    if kind == "cost_revenue_graph":
        return (
            "The paper renders labelled costs/revenues and output axes for the "
            "candidate's AR, MR, AC and MC diagram before both subparts."
        )
    return ""


def _merge_parts(question: QuestionBlueprint, raw_parts: object) -> list:
    if not isinstance(raw_parts, list):
        return question.parts
    by_label = {str(item.get("label", "")): item for item in raw_parts if isinstance(item, dict)}
    merged = []
    for part in question.parts:
        raw = by_label.get(part.label, {})
        options = part.options
        raw_options = raw.get("options") if isinstance(raw, dict) else None
        if isinstance(raw_options, list):
            parsed_options = [
                MultipleChoiceOption(label=str(option.get("label", "")), text=str(option.get("text", "")))
                for option in raw_options
                if isinstance(option, dict)
            ]
            if len(parsed_options) == 4:
                options = parsed_options
        mark_scheme_raw = raw.get("mark_scheme") if isinstance(raw, dict) else None
        indicative_raw = raw.get("indicative_content") if isinstance(raw, dict) else None
        merged.append(
            part.model_copy(
                update={
                    "prompt": _merge_part_prompt(part, raw),
                    "mark_breakdown": str(raw.get("mark_breakdown") or part.mark_breakdown) if isinstance(raw, dict) else part.mark_breakdown,
                    "mark_scheme": _merge_text_list(mark_scheme_raw, part.mark_scheme),
                    "indicative_content": _merge_text_list(indicative_raw, part.indicative_content),
                    "options": options,
                    "correct_option": str(raw.get("correct_option") or part.correct_option) if isinstance(raw, dict) else part.correct_option,
                }
            )
        )
    return merged


def _merge_text_list(raw: object, fallback: list[str]) -> list[str]:
    if not isinstance(raw, list):
        return fallback
    items = [str(item).strip() for item in raw if str(item).strip()]
    return items or fallback


def _clean_prompt(prompt: str) -> str:
    cleaned = re.sub(r"[\(\[]\s*\d+\s*marks?\s*[\)\]]", "", prompt, flags=re.IGNORECASE)
    cleaned = re.sub(r"\(Total\s+for\s+(Question\s+)?\d+\s*=\s*\d+\s*marks?\s*\)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bfigure\s+\d+\b", "the diagram", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\btable\s+\d+\b", "the table", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bconsider both positive and negative arguments to support your answer\.?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r",?\s*considering both positive and negative impacts?\.?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(?:include|use)\s+relevant\s+economic\s+theor(?:y|ies)\s+to\s+support\s+your\s+(?:discussion|answer)\.?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\byou\s+should\s+weigh\s+up\s+both\s+sides\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bexplore\s+both\s+(?:sides\s+of\s+the\s+)?argument", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bbring\s+in\s+relevant\s+economic\s+concepts\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r",?\s*both\s+in\s+the\s+short\s+run\s+and\s+the\s+long\s+run\.?", "", cleaned, flags=re.IGNORECASE)
    return " ".join(cleaned.split())


def _merge_part_prompt(part, _raw: dict) -> str:
    return _strip_part_label(_clean_prompt(part.prompt), part.label)


def _validate_ai_question(
    original: QuestionBlueprint,
    candidate: QuestionBlueprint,
) -> None:
    immutable = (
        original.section,
        original.number,
        original.marks,
        original.command_word,
        original.topic_id,
        original.stimulus_kind,
        original.choice_group,
    )
    actual = (
        candidate.section,
        candidate.number,
        candidate.marks,
        candidate.command_word,
        candidate.topic_id,
        candidate.stimulus_kind,
        candidate.choice_group,
    )
    if actual != immutable:
        raise ValueError(
            f"question-{original.number} changed an immutable blueprint field"
        )
    verified_assessment_data = (
        original.source_reference,
        original.source_title,
        original.source_text,
        original.mark_breakdown,
        original.mark_scheme,
        original.indicative_content,
        original.parts,
        original.graph_params,
        original.source_instance,
        original.assessment_objectives,
        original.assessment_contract,
        original.scheme_mode,
    )
    actual_assessment_data = (
        candidate.source_reference,
        candidate.source_title,
        candidate.source_text,
        candidate.mark_breakdown,
        candidate.mark_scheme,
        candidate.indicative_content,
        candidate.parts,
        candidate.graph_params,
        candidate.source_instance,
        candidate.assessment_objectives,
        candidate.assessment_contract,
        candidate.scheme_mode,
    )
    if actual_assessment_data != verified_assessment_data:
        raise ValueError(
            f"question-{original.number} changed verified assessment data"
        )
    maximum_stem_words = max(12, len(original.prompt.split()) + 2)
    if len(candidate.prompt.split()) > maximum_stem_words:
        raise ValueError(
            f"question-{original.number} exceeds the {maximum_stem_words}-word stem word budget"
        )
    candidate_scope_text = candidate.prompt.casefold().replace("firms'", "firm's")
    missing_scope_terms = [
        term
        for term in _required_scope_terms(original)
        if term not in candidate_scope_text
    ]
    if missing_scope_terms:
        raise ValueError(
            f"question-{original.number} changed required scope term(s): "
            + ", ".join(missing_scope_terms)
        )
    if (
        original.topic_id == "2.6"
        and original.marks == 5
        and (
            "one likely effect" not in candidate.prompt.casefold()
            or "on inflation" not in candidate.prompt.casefold()
        )
    ):
        raise ValueError(
            f"question-{original.number} changed the required effect-on-inflation task framing"
        )
    original_text = " ".join(
        [original.prompt, *(part.prompt for part in original.parts)]
    )
    candidate_text = " ".join(
        [candidate.prompt, *(part.prompt for part in candidate.parts)]
    )
    validate_economics_causal_direction(
        " ".join(
            [
                candidate_text,
                *candidate.mark_scheme,
                *candidate.indicative_content,
                *(
                    point
                    for part in candidate.parts
                    for point in [*part.mark_scheme, *part.indicative_content]
                ),
            ]
        )
    )
    assert_materially_new(
        original_text,
        candidate_text,
        item_id=f"question-{original.number}",
        similarity_limit=0.9,
        preserve_numbers=False,
    )
    if len(candidate.parts) != len(original.parts):
        raise ValueError(f"question-{original.number} changed its part count")
    for original_part, candidate_part in zip(
        original.parts, candidate.parts, strict=True
    ):
        if (
            candidate_part.label,
            candidate_part.marks,
            candidate_part.command_word,
        ) != (
            original_part.label,
            original_part.marks,
            original_part.command_word,
        ):
            raise ValueError(
                f"question-{original.number}-{original_part.label} changed "
                "its blueprint"
            )
        _validate_content_lists(
            candidate_part.marks,
            candidate_part.mark_scheme,
            candidate_part.indicative_content,
            item_id=f"question-{original.number}-{original_part.label}",
        )
        if candidate_part.options:
            labels = [option.label for option in candidate_part.options]
            answers = [option.text.casefold().strip() for option in candidate_part.options]
            if (
                labels != ["A", "B", "C", "D"]
                or len(set(answers)) != 4
                or candidate_part.correct_option not in labels
            ):
                raise ValueError(
                    f"question-{original.number}-{original_part.label} "
                    "has invalid multiple-choice data"
                )
    if not candidate.parts:
        _validate_content_lists(
            candidate.marks,
            candidate.mark_scheme,
            candidate.indicative_content,
            item_id=f"question-{original.number}",
        )
    if (
        candidate.stimulus_kind
        and candidate.graph_params.kind
        and (
            (
                candidate.graph_params.eq_price is not None
                and not 20 <= candidate.graph_params.eq_price <= 200
            )
            or (
                candidate.graph_params.eq_quantity is not None
                and not 30 <= candidate.graph_params.eq_quantity <= 300
            )
        )
    ):
        raise ValueError(
            f"question-{original.number} has out-of-range graph parameters"
        )


def _validate_content_lists(
    marks: int,
    mark_scheme: list[str],
    indicative_content: list[str],
    *,
    item_id: str,
) -> None:
    scheme = [item.strip() for item in mark_scheme if item.strip()]
    indicative = [item.strip() for item in indicative_content if item.strip()]
    minimum = min(8, max(1, marks))
    indicative_minimum = min(6, max(1, marks))
    if len(set(item.casefold() for item in scheme)) < minimum:
        raise ValueError(f"{item_id} has insufficient specific marking guidance")
    if (
        marks >= 5
        and len(set(item.casefold() for item in indicative))
        < indicative_minimum
    ):
        raise ValueError(f"{item_id} has insufficient indicative content")


def _strip_part_label(prompt: str, label: str) -> str:
    cleaned = prompt.strip()
    label_pattern = re.escape(label)
    patterns = [
        rf"^(?:question\s+\d+\s*)?\(\s*{label_pattern}\s*\)\s*",
        rf"^{label_pattern}\)\s*",
        rf"^{label_pattern}\.\s*",
    ]
    changed = True
    while changed:
        changed = False
        for pattern in patterns:
            updated = re.sub(pattern, "", cleaned, count=1, flags=re.IGNORECASE).strip()
            if updated != cleaned:
                cleaned = updated
                changed = True
    return cleaned


def _required_scope_terms(question: QuestionBlueprint) -> tuple[str, ...]:
    prompt = question.prompt.casefold().replace("firms'", "firm's")
    terms = [
        "non-profit objectives",
        "training, childcare and infrastructure",
    ]
    scenario = SCENARIOS.get(question.topic_id)
    if scenario is not None:
        for scope in (scenario.event, scenario.outcome, *scenario.outcome.split(" and ")):
            normalised = scope.replace("firms'", "firm's")
            if normalised in prompt:
                terms.append(normalised)
    return tuple(dict.fromkeys(term for term in terms if term in prompt))


def _merge_question_text(question: QuestionBlueprint, generated: str) -> str:
    if question.parts:
        if question.section == "A" and question.stimulus_kind:
            return question.prompt
        source = " ".join(question.source_text.split())
        if source:
            sentence = re.split(r"(?<=[.!?])\s+", source, maxsplit=1)[0]
            return " ".join(sentence.split()[:50])
        return f"This question concerns {question.source_title or question.topic_id}."
    cleaned = _clean_prompt(generated or question.prompt)
    if not _matches_expected_question_style(question, cleaned):
        return question.prompt
    return _restore_source_reference(cleaned, question.source_reference)


def _uses_review_only_generation(question: QuestionBlueprint) -> bool:
    """Keep calibrated Section A stimuli aligned with rendered assessment data."""
    return question.section == "A" and bool(question.stimulus_kind)


def _restore_source_reference(prompt: str, source_reference: str) -> str:
    restored = prompt
    if not source_reference:
        return restored
    figure = re.search(r"Figure\s+\d+", source_reference, flags=re.IGNORECASE)
    table = re.search(r"Table\s+\d+", source_reference, flags=re.IGNORECASE)
    extract = re.search(r"Extract\s+[A-Z]", source_reference, flags=re.IGNORECASE)
    if figure:
        restored = re.sub(r"\bthe diagram\b", figure.group(0), restored, count=1, flags=re.IGNORECASE)
    if table:
        restored = re.sub(r"\bthe table\b", table.group(0), restored, count=1, flags=re.IGNORECASE)
    if extract:
        restored = re.sub(r"\bthe extract\b", extract.group(0), restored, count=1, flags=re.IGNORECASE)
    return restored


def _has_word_starts(text: str, *words: str) -> bool:
    lowered = text.lstrip()
    for word in words:
        pattern = rf"^(?:critically\s+)?{re.escape(word)}\b"
        if re.search(pattern, lowered):
            return True
    return False


def _matches_expected_question_style(question: QuestionBlueprint, prompt: str) -> bool:
    lowered = prompt.lower()
    command = question.command_word.lower()

    ref_lowered = question.source_reference.lower() if question.source_reference else None
    has_ref = True
    if ref_lowered:
        if ref_lowered.startswith("extract "):
            ref_text = "the extract"
        elif ref_lowered.startswith("figure "):
            ref_text = "the diagram"
        elif ref_lowered.startswith("table "):
            ref_text = "the table"
        else:
            ref_text = "the source material" if ref_lowered == "source material" else ref_lowered
        has_ref = (
            f"with reference to {ref_text}" in lowered
            or f"with reference to {ref_lowered}" in lowered
        )

    if question.section == "C":
        has_ref = True

    if question.marks == 15 and question.section == "B":
        return has_ref and "discuss" in lowered

    if question.marks == 12:
        return (has_ref or not ref_lowered) and ("discuss whether" in lowered or "discuss the extent" in lowered or "to what extent" in lowered)

    if question.marks == 10:
        return (has_ref or not ref_lowered) and ("assess whether" in lowered or "assess the" in lowered or "to what extent" in lowered)

    if question.marks == 8:
        return (has_ref or not ref_lowered) and _has_word_starts(lowered, "examine")

    if question.marks == 5 and question.section in {"A", "B"}:
        return (has_ref or not ref_lowered) and "explain" in lowered

    if question.marks == 25:
        return _has_word_starts(lowered, "evaluate") or "to what extent" in lowered

    if ref_lowered and not has_ref and question.section in {"A", "B"}:
        return False
    return command in lowered


def _merge_source_text(generated: str, fallback: str, question: QuestionBlueprint) -> str:
    if question.section == "A" and question.stimulus_kind:
        return fallback
    cleaned = " ".join(generated.split())
    if not cleaned:
        return fallback
    lowered = cleaned.lower()
    if lowered.startswith("this source concerns"):
        cleaned = cleaned[len("this source concerns"):].strip()
        cleaned = cleaned[0].upper() + cleaned[1:] if cleaned else cleaned
    if (
        "may include evidence" in lowered
        or "|" in cleaned
        or "---" in cleaned
        or (question.section == "A" and len(cleaned) > 220)
        or (question.section == "B" and len(cleaned) < 700)
        or (question.section == "C" and len(cleaned) < 80)
    ):
        return fallback
    return cleaned
