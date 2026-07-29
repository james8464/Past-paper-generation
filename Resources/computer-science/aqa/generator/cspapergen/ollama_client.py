from __future__ import annotations

import json
import re
import time
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
        try:
            payload = client.generate_json(
                _prompt(
                    question,
                    topic.title,
                    note_context_for_topic(topic.id, topic.title),
                    blueprint,
                )
            )
            improved.append(_merge_question(question, payload))
            emit(f"Generated question {index}/{total}: 0 {question.number:02d}")
        except (RuntimeError, json.JSONDecodeError, ValueError, KeyError) as error:
            improved.append(question)
            emit(
                f"Question {index}/{total}: 0 {question.number:02d} "
                f"(using validated draft after model error: {error})"
            )
    return blueprint.model_copy(update={"questions": improved})


def _prompt(
    question: Question,
    topic_title: str,
    notes: str,
    blueprint: PaperBlueprint,
) -> str:
    parts = "\n".join(f"- Part {part.label}: {part.marks} marks, {part.prompt}" for part in question.parts)
    return f"""You are writing an unofficial A-level Computer Science {blueprint.paper_code} Paper {blueprint.paper_number} practice paper.

Use only this syllabus topic: {question.topic_id} {topic_title}
Revision-note context:
{notes}

Rewrite this question in concise UK exam style. Preserve marks, part labels, answer units, stimulus meaning, scenario names and correct answers. Do not add exam-board branding or copied past-paper text.

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
    text = text.replace("$", "")
    text = re.sub(r"\\(?:texttt|mathrm|mathbf)\{([^{}]+)\}", r"\1", text)
    text = text.replace(r"\(", "").replace(r"\)", "")
    return " ".join(text.split())
