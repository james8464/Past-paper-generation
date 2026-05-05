from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable

from pastpapergen.models import MultipleChoiceOption, PaperBlueprint, QuestionBlueprint, Syllabus, SyllabusTopic


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
    return f"""You are writing an unofficial A-Level Economics practice paper.

Use only this syllabus topic:
Topic ID: {topic.id}
Theme: {topic.theme}
Title: {topic.title}
Allowed points:
{points}

Write one Edexcel A-style question.
Question number: {question.number}
Section: {question.section}
Marks: {question.marks}
Command word: {question.command_word}
Parts: {_parts_for_prompt(question)}
Draft intent: {question.prompt}

Style rules:
- 5-mark questions usually explain one reason or one effect.
- 8-mark questions usually examine two reasons, effects, advantages or problems.
- 12-mark questions usually use discuss whether and require balanced analysis.
- 10-mark questions usually use assess whether and require judgement.
- 15-mark questions usually use discuss and require developed evaluation.
- 25-mark questions usually use evaluate and must sound like an essay choice question.
- Do not include '(4 marks)' or similar mark text in any question or part text.
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
        question_text = _clean_prompt(str(payload.get("question_text") or question.prompt))
        source_text = str(payload.get("source_text") or "")
        source_reference = str(payload.get("source_reference") or question.source_reference)
        mark_breakdown = str(payload.get("mark_breakdown") or question.mark_breakdown)
        indicative_raw = payload.get("indicative_content") or question.indicative_content
        indicative_content = [str(item) for item in indicative_raw] if isinstance(indicative_raw, list) else question.indicative_content
        mark_scheme_raw = payload.get("mark_scheme") or []
        mark_scheme = [str(item) for item in mark_scheme_raw] if isinstance(mark_scheme_raw, list) else []
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
                    "prompt": _clean_prompt(str(raw.get("prompt") or part.prompt)) if isinstance(raw, dict) else part.prompt,
                    "mark_breakdown": str(raw.get("mark_breakdown") or part.mark_breakdown) if isinstance(raw, dict) else part.mark_breakdown,
                    "mark_scheme": [str(item) for item in mark_scheme_raw] if isinstance(mark_scheme_raw, list) else part.mark_scheme,
                    "indicative_content": [str(item) for item in indicative_raw] if isinstance(indicative_raw, list) else part.indicative_content,
                    "options": options,
                    "correct_option": str(raw.get("correct_option") or part.correct_option) if isinstance(raw, dict) else part.correct_option,
                }
            )
        )
    return merged


def _clean_prompt(prompt: str) -> str:
    return " ".join(re.sub(r"\(\s*\d+\s*marks?\s*\)", "", prompt, flags=re.IGNORECASE).split())
