from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable

from cspapergen.models import MarkingGuidance, PaperBlueprint, Question, QuestionPart, Syllabus
from cspapergen.notes import note_context_for_topic


@dataclass(frozen=True)
class OllamaClient:
    base_url: str
    model: str

    def generate_json(self, prompt: str) -> dict[str, object]:
        payload = json.dumps({"model": self.model, "prompt": prompt, "stream": False, "format": "json"}).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url.rstrip('/')}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=160) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as error:
            raise RuntimeError(f"Could not reach Ollama at {self.base_url}") from error
        return json.loads(str(raw.get("response", "{}")))


def improve_questions_with_ollama(
    client: OllamaClient,
    blueprint: PaperBlueprint,
    syllabus: Syllabus,
    progress: Callable[[str], None] | None = None,
) -> PaperBlueprint:
    emit = progress or (lambda _message: None)
    improved: list[Question] = []
    total = len(blueprint.questions)
    for index, question in enumerate(blueprint.questions, start=1):
        topic = syllabus.get_topic(question.topic_id)
        emit(f"Generating question {index}/{total}: 0 {question.number:02d} ({topic.title})")
        payload = client.generate_json(_prompt(question, topic.title, note_context_for_topic(topic.id, topic.title)))
        improved.append(_merge_question(question, payload))
        emit(f"Generated question {index}/{total}: 0 {question.number:02d}")
    return blueprint.model_copy(update={"questions": improved})


def _prompt(question: Question, topic_title: str, notes: str) -> str:
    parts = "\n".join(f"- Part {part.label}: {part.marks} marks, {part.prompt}" for part in question.parts)
    return f"""You are writing an unofficial AQA A-level Computer Science 7517/2 Paper 2 practice paper.

Use only this syllabus topic: {question.topic_id} {topic_title}
Revision-note context:
{notes}

Rewrite this question so it sounds like a real AQA Paper 2 question. Preserve marks, part labels, answer units, stimulus meaning and correct answers.

Question stem: {question.stem}
Parts:
{parts}

Return JSON only:
{{
  "stem": "string",
  "parts": [
    {{
      "label": "1",
      "prompt": "string",
      "marking_points": ["specific mark point;", "specific mark point;"],
      "accept": ["optional acceptable answer"],
      "reject": ["optional rejected answer"]
    }}
  ]
}}
"""


def _merge_question(question: Question, payload: dict[str, object]) -> Question:
    stem = _clean(str(payload.get("stem") or question.stem))
    raw_parts = payload.get("parts")
    parts = question.parts
    if isinstance(raw_parts, list):
        by_label = {str(item.get("label")): item for item in raw_parts if isinstance(item, dict)}
        merged = []
        for part in question.parts:
            raw = by_label.get(part.label, {})
            prompt = _clean(str(raw.get("prompt") or part.prompt)) if isinstance(raw, dict) else part.prompt
            points = _text_list(raw.get("marking_points") if isinstance(raw, dict) else None, part.marking.points)
            accept = _text_list(raw.get("accept") if isinstance(raw, dict) else None, part.marking.accept)
            reject = _text_list(raw.get("reject") if isinstance(raw, dict) else None, part.marking.reject)
            marking = MarkingGuidance(ao=part.marking.ao, points=points, accept=accept, reject=reject, levels=part.marking.levels)
            merged.append(part.model_copy(update={"prompt": prompt, "marking": marking}))
        parts = merged
    return question.model_copy(update={"stem": stem, "parts": parts})


def _text_list(raw: object, fallback: list[str]) -> list[str]:
    if not isinstance(raw, list):
        return fallback
    values = [str(item).strip() for item in raw if str(item).strip()]
    return values or fallback


def _clean(text: str) -> str:
    text = re.sub(r"\[\s*\d+\s*marks?\s*\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\(\s*\d+\s*marks?\s*\)", "", text, flags=re.IGNORECASE)
    return " ".join(text.split())
