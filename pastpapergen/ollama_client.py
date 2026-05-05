from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable

from pastpapergen.models import MultipleChoiceOption, PaperBlueprint, QuestionBlueprint, Syllabus, SyllabusTopic
from pastpapergen.notes import note_context_for_topic


@dataclass(frozen=True)
class OllamaClient:
    base_url: str
    model: str

    def generate_json(self, prompt: str) -> dict[str, object]:
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
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as error:
            raise RuntimeError(f"Could not reach Ollama at {self.base_url}") from error

        text = str(raw.get("response", "{}"))
        return json.loads(text)


def build_question_prompt(question: QuestionBlueprint, topic: SyllabusTopic) -> str:
    points = "\n".join(f"- {point}" for point in topic.points)
    note_context = note_context_for_topic(topic.id, title=topic.title, keywords=topic.points)
    return f"""You are writing an unofficial A-Level Economics practice paper.

Use only this syllabus topic:
Topic ID: {topic.id}
Theme: {topic.theme}
Title: {topic.title}
Allowed points:
{points}

Uploaded revision-note context:
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
- 5-mark questions usually explain one reason or one effect.
- 8-mark questions usually examine two reasons, effects, advantages or problems.
- 12-mark questions usually use discuss whether and require balanced analysis.
- 10-mark questions usually use assess whether and require judgement.
- 15-mark questions usually use discuss and require developed evaluation.
- 25-mark questions usually use evaluate and must sound like an essay choice question.
- Preserve the command word and source reference pattern from the draft intent.
- For Section A, match the stimulus kind: graph, table, pay-off matrix, line graph or short context.
- For Section C, write a short source-style extract in source_text; the question paper displays both choices first.
- Do not add instructions such as 'Consider both positive and negative arguments' or 'include relevant theories'.
- Do not include '(4 marks)' or similar mark text in any question or part text.
- Mark scheme bullets must be specific to the generated question, using its source data, correct option, likely answer points and evaluation judgement.
- If parts are supplied, rewrite each part separately rather than combining the parts into the main question text.
- If a one-mark MCQ is supplied, return four options A-D and one correct_option.

Return JSON only with this schema:
{{
  "question_text": "string",
  "source_text": "string or empty string",
  "source_reference": "Figure 1, Extract A, Extract B, or empty string",
  "mark_breakdown": "string such as Knowledge 2, Application 2",
  "indicative_content": ["bullet 1", "bullet 2"],
  "mark_scheme": ["bullet 1", "bullet 2", "bullet 3"],
  "parts": [
    {{
      "label": "a",
      "prompt": "string",
      "mark_breakdown": "string",
      "mark_scheme": ["bullet 1"],
      "indicative_content": ["bullet 1"],
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
    questions: list[QuestionBlueprint] = []
    total = len(blueprint.questions)
    for index, question in enumerate(blueprint.questions, start=1):
        topic = syllabus.get_topic(question.topic_id)
        emit(
            f"Generating question {index}/{total}: {question.number} "
            f"(Section {question.section}, {question.marks} marks, {topic.title})"
        )
        payload = client.generate_json(build_question_prompt(question, topic))
        question_text = _merge_question_text(question, str(payload.get("question_text") or ""))
        source_text = _merge_source_text(str(payload.get("source_text") or ""), question.source_text, question)
        source_reference = str(payload.get("source_reference") or question.source_reference)
        mark_breakdown = str(payload.get("mark_breakdown") or question.mark_breakdown)
        indicative_content = _merge_text_list(payload.get("indicative_content"), question.indicative_content)
        mark_scheme = _merge_text_list(payload.get("mark_scheme"), question.mark_scheme)
        parts = _merge_parts(question, payload.get("parts"))
        questions.append(
            question.model_copy(
                update={
                    "prompt": question_text,
                    "source_text": source_text,
                    "source_reference": source_reference,
                    "mark_breakdown": mark_breakdown,
                    "indicative_content": indicative_content,
                    "mark_scheme": mark_scheme,
                    "parts": parts,
                }
            )
        )
        emit(f"Generated question {index}/{total}: {question.number} ({topic.title})")
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
    cleaned = re.sub(
        r"\bConsider both positive and negative arguments to support your answer\.?",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r",?\s*considering both positive and negative impacts\.?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bInclude relevant economic theories to support your discussion\.?", "", cleaned, flags=re.IGNORECASE)
    return " ".join(cleaned.split())


def _merge_part_prompt(part, raw: dict) -> str:
    if not isinstance(raw, dict):
        return part.prompt
    candidate = _clean_prompt(str(raw.get("prompt") or part.prompt))
    lowered = candidate.lower()
    if part.command_word == "draw" and "explain your answer" in lowered:
        return part.prompt
    if part.command_word == "calculate" and "calculate" not in lowered:
        return part.prompt
    if part.command_word == "explain" and "explain" not in lowered:
        return part.prompt
    if part.command_word == "mcq" and "which one of the following" not in lowered:
        return part.prompt
    return candidate


def _merge_question_text(question: QuestionBlueprint, generated: str) -> str:
    if question.parts:
        return question.prompt
    cleaned = _clean_prompt(generated or question.prompt)
    if not _matches_expected_question_style(question, cleaned):
        return question.prompt
    return cleaned


def _matches_expected_question_style(question: QuestionBlueprint, prompt: str) -> bool:
    lowered = prompt.lower()
    command = question.command_word.lower()
    if question.marks == 15 and question.section == "B":
        if question.source_reference:
            reference = question.source_reference.lower()
            return lowered.startswith(f"with reference to {reference}") and "discuss" in lowered
        return lowered.startswith("discuss")
    if question.section in {"A", "B"} and question.source_reference:
        reference = (
            "the source material"
            if question.source_reference == "source material"
            else question.source_reference.lower()
        )
        if f"with reference to {reference}" not in lowered:
            return False
    if question.marks == 12:
        if question.source_reference:
            return lowered.startswith("with reference to") and "discuss whether" in lowered
        return lowered.startswith("discuss whether")
    if question.marks == 10:
        if question.source_reference:
            return lowered.startswith("with reference to") and "assess whether" in lowered
        return lowered.startswith("assess whether")
    if question.marks == 8:
        if question.source_reference:
            return lowered.startswith("with reference to") and "examine" in lowered
        return lowered.startswith("examine")
    if question.marks == 5 and question.section in {"A", "B"}:
        if question.source_reference:
            return lowered.startswith("with reference to") and "explain" in lowered
        return lowered.startswith("explain")
    if question.marks == 25:
        return lowered.startswith("evaluate")
    return command in lowered


def _merge_source_text(generated: str, fallback: str, question: QuestionBlueprint) -> str:
    cleaned = " ".join(generated.split())
    lowered = cleaned.lower()
    if (
        not cleaned
        or lowered.startswith("this source concerns")
        or "may include evidence" in lowered
        or "|" in cleaned
        or "---" in cleaned
        or (question.section == "A" and len(cleaned) > 220)
        or (question.section == "B" and len(cleaned) < 260)
        or (question.section == "C" and len(cleaned) < 80)
    ):
        return fallback
    return cleaned
