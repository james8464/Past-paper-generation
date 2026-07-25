from __future__ import annotations

import json
import logging
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from threading import Lock
from typing import Callable

from pastpapergen.models import GraphParams, MultipleChoiceOption, PaperBlueprint, QuestionBlueprint, Syllabus, SyllabusTopic
from pastpapergen.notes import note_context_for_topic

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OllamaClient:
    base_url: str
    model: str

    def generate_json(self, prompt: str, retries: int = 3) -> dict[str, object]:
        last_error: Exception | None = None
        for attempt in range(retries):
            try:
                return self._call(prompt)
            except (urllib.error.URLError, json.JSONDecodeError, KeyError) as error:
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
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url.rstrip('/')}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=180) as response:
            raw = json.loads(response.read().decode("utf-8"))
        raw_dict = raw if isinstance(raw, dict) else {}
        text = str(raw_dict.get("response", "{}"))
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise json.JSONDecodeError("Expected dict", text, 0)
        return parsed


def build_question_prompt(question: QuestionBlueprint, topic: SyllabusTopic) -> str:
    points = "\n".join(f"- {point}" for point in topic.points)
    note_context = note_context_for_topic(topic.id, title=topic.title, keywords=topic.points)
    return f"""You are writing an unofficial A-Level Economics practice paper.

Use only this syllabus topic:
Topic ID: {topic.id}
Theme: {topic.theme}
Title: {topic.title}
Syllabus points (you must align every mark scheme bullet to these):
{points}

Uploaded revision-note context (use this data for source figures, extraction content and specific examples):
{note_context}

Write one Edexcel A-style question.
Question number: {question.number}
Section: {question.section}
Marks: {question.marks}
Command word: {question.command_word}
Parts: {_parts_for_prompt(question)}
Stimulus kind: {question.stimulus_kind or "none"}
Draft intent: {question.prompt}

Style rules:
- Match the command word exactly: {question.command_word}.
- Preserve the command word and source reference pattern from the draft intent.
- 12-mark questions usually use discuss whether, discuss the extent, or to what extent.
- 10-mark questions usually use assess whether, assess the, or to what extent.
- For Section A, match the stimulus kind: graph, table, pay-off matrix, line graph or short context.
- For Section C, write a short source-style extract in source_text; the question paper displays both choices first.
- Do not add instructions such as 'Consider both positive and negative arguments' or 'include relevant theories'.
- Do not include '(4 marks)' or similar mark text in any question or part text.
- If parts are supplied, rewrite each part separately rather than combining the parts into the main question text.
- Do not start part prompts with labels such as '(a)', 'a)' or 'Question 1(a)' because labels are rendered separately.
- If a one-mark MCQ is supplied, return four options A-D and one correct_option.
- If stimulus_kind is set, include a graph_params object with numeric values for equilibrium price and quantity that match the question context. This makes the diagram specific to the question data.
- Return ALL JSON fields — do not omit anything.

CRITICAL: MARK SCHEME REQUIREMENTS
Mark scheme bullets must be specific to the generated question.
The mark_scheme and indicative_content fields must be EXCESSIVELY DETAILED. Follow these rules exactly:

1. The mark_scheme array must have at least 8-15 bullets, depending on marks.
2. Each bullet must be explicitly linked to one or more of the syllabus points listed above.
3. Structure the mark scheme in three sections separated by empty-string bullets:
   - "AO1 (Knowledge/Understanding):" then 2-4 specific knowledge bullets tied to exact syllabus points (e.g. "AO1: Recall that PED = %ΔQd / %ΔP (syllabus point: price elasticity of demand)")
   - "AO2 (Application):" then 2-4 bullets using SPECIFIC numeric data from the source text, extract or figure (e.g. "AO2: Using the PED value of -1.4 and the 5% price fall from Figure 1, correctly calculates 5% × 1.4 = 7% increase in quantity demanded")
   - "AO3 (Analysis):" then 2-4 bullets showing logical chains of reasoning with economic theory (e.g. "AO3: Explains that the price fall increases consumer surplus because the lower price expands the market along the demand curve")
   - For questions of 10+ marks, also add:
     - "AO4 (Evaluation):" then 2-4 bullets with counter-arguments, real-world limitations, stakeholder trade-offs, or judgement criteria
4. Every bullet must reference actual numbers, syllabus concepts, or source data — never generic phrases like "accurate economic theory" or "relevant application".
5. The indicative_content array must list 8-15 specific, concrete answer points that a top-band student would make, each directly addressing the question.
6. For parts (sub-questions), each part must have its own mark_scheme and indicative_content following the same level of detail.
7. Use exact syllabus terminology (e.g., "marginal social cost", "de-mutualisation", "quantitative easing") rather than vague terms.

EXAMPLE of a good 8-mark mark_scheme:
[
  "",
  "AO1 (Knowledge/Understanding):",
  "Correctly identifies that PES measures the responsiveness of quantity supplied to a change in price (syllabus: price elasticity of supply).",
  "States the formula PES = %ΔQs / %ΔP and recognises that PES > 1 indicates elastic supply.",
  "",
  "AO2 (Application):",
  "Using the rural market PES value of 1.8 from the extract, correctly applies 3.6% / 1.8 = 2.0%.",
  "Correctly interprets the result: price increases by 2.0% because supply is relatively elastic.",
  "",
  "AO3 (Analysis):",
  "Explains that elastic supply in the rural market is due to spare capacity, available substitutes or time period (long run).",
  "Analyses how the smaller price rise benefits consumers by limiting pass-through of cost increases."
]

Return JSON only with this schema:
{{
  "question_text": "string",
  "source_text": "string or empty string",
  "source_reference": "Figure 1, Extract A, Extract B, or empty string",
  "mark_breakdown": "string such as 'Knowledge 2, Application 2'",
  "indicative_content": ["8-15 specific answer points a top student would make"],
  "mark_scheme": ["8-15 detailed bullets structured as AO1/AO2/AO3(/AO4 for 10+ marks), each tied to specific syllabus points and source data"],
  "graph_params": {{
    "eq_price": <integer between 20 and 200, matching source data>,
    "eq_quantity": <integer between 30 and 300, matching source data>,
    "kind": <string: "demand_supply", "ad_as", "keynesian", "monopoly", "laffer", "labour", "externality", "ppf", "trade_cycle", "phillips", "lorenz", or "cost_revenue">
  }},
  "parts": [
    {{
      "label": "a",
      "prompt": "string",
      "mark_breakdown": "string",
      "mark_scheme": ["8-15 detailed bullets per part, same AO structure"],
      "indicative_content": ["specific answer points for this part"],
      "options": [
        {{"label": "A", "text": "string"}},
        {{"label": "B", "text": "string"}},
        {{"label": "C", "text": "string"}},
        {{"label": "D", "text": "string"}}
      ],
      "correct_option": "A"
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
) -> PaperBlueprint:
    emit = progress or (lambda _message: None)
    total = len(blueprint.questions)
    results: dict[int, QuestionBlueprint] = {}
    results_lock = Lock()
    max_workers = min(total, 4)

    def _build_task(question_index: int, question: QuestionBlueprint) -> None:
        index = question_index + 1
        try:
            topic = syllabus.get_topic(question.topic_id)
        except KeyError as error:
            _logger.error("Unknown topic '%s' for question %s, skipping LLM: %s", question.topic_id, question.number, error)
            with results_lock:
                results[question_index] = question
            emit(f"Question {index}/{total}: {question.number} (unknown topic, template fallback)")
            return
        emit(
            f"Generating question {index}/{total}: {question.number} "
            f"(Section {question.section}, {question.marks} marks, {topic.title})"
        )
        try:
            payload = client.generate_json(build_question_prompt(question, topic))
            question_text = _merge_question_text(question, str(payload.get("question_text") or ""))
            source_text = _merge_source_text(str(payload.get("source_text") or ""), question.source_text, question)
            source_reference = str(payload.get("source_reference") or question.source_reference)
            mark_breakdown = str(payload.get("mark_breakdown") or question.mark_breakdown)
            indicative_content = _merge_text_list(payload.get("indicative_content"), question.indicative_content)
            mark_scheme = _merge_text_list(payload.get("mark_scheme"), question.mark_scheme)
            parts = _merge_parts(question, payload.get("parts"))
            graph_params_raw = payload.get("graph_params")
            graph_params = GraphParams.from_dict(graph_params_raw) if isinstance(graph_params_raw, dict) else GraphParams()
            with results_lock:
                results[question_index] = question.model_copy(
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
            emit(f"Generated question {index}/{total}: {question.number} ({topic.title})")
        except (RuntimeError, json.JSONDecodeError, ValueError, KeyError) as error:
            _logger.error("Failed to generate question %s, keeping template: %s", question.number, error)
            with results_lock:
                results[question_index] = question
            emit(f"Question {index}/{total}: {question.number} (fallback to template)")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_build_task, i, q): i for i, q in enumerate(blueprint.questions)}
        for future in as_completed(futures):
            question_index = futures[future]
            try:
                future.result()
            except Exception as error:  # noqa: BLE001 - one bad response must not abort the paper.
                question = blueprint.questions[question_index]
                _logger.exception("Unexpected generation failure for question %s", question.number)
                with results_lock:
                    results[question_index] = question
                emit(
                    f"Question {question_index + 1}/{total}: {question.number} "
                    f"(unexpected failure, template fallback: {error})"
                )
    questions = [results[i] for i in range(total)]
    return blueprint.model_copy(update={"questions": questions})


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


def _merge_part_prompt(part, raw: dict) -> str:
    if not isinstance(raw, dict):
        return part.prompt
    fallback = _strip_part_label(_clean_prompt(part.prompt), part.label)
    if part.command_word in {"calculate", "draw"}:
        return fallback
    candidate = _strip_part_label(_clean_prompt(str(raw.get("prompt") or part.prompt)), part.label)
    lowered = candidate.lower()
    if part.command_word == "draw" and "explain your answer" in lowered:
        return fallback
    if part.command_word == "calculate" and "calculate" not in lowered:
        return fallback
    if part.command_word == "explain" and "explain" not in lowered:
        return fallback
    if part.command_word == "mcq" and "which one of the following" not in lowered:
        return fallback
    return candidate


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


def _merge_question_text(question: QuestionBlueprint, generated: str) -> str:
    if question.parts:
        return question.prompt
    cleaned = _clean_prompt(generated or question.prompt)
    if not _matches_expected_question_style(question, cleaned):
        return question.prompt
    return cleaned


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
