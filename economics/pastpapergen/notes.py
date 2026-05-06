from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NOTES_TEXT_DIR = PROJECT_ROOT / "data" / "notes" / "text"


def note_file_for_topic(topic_id: str) -> Path:
    prefix = _note_prefix(topic_id)
    matches = sorted(NOTES_TEXT_DIR.glob(f"{prefix}*.txt"))
    if not matches:
        raise FileNotFoundError(f"No notes file found for topic {topic_id}")
    return matches[0]


def note_context_for_topic(
    topic_id: str,
    *,
    title: str = "",
    keywords: list[str] | tuple[str, ...] = (),
    max_chars: int = 1800,
) -> str:
    chunks = _ranked_note_chunks(topic_id, title, keywords)
    context = " ".join(chunks[:10])
    return context[:max_chars].strip()


def note_points_for_topic(
    topic_id: str,
    *,
    title: str = "",
    keywords: list[str] | tuple[str, ...] = (),
    limit: int = 6,
) -> list[str]:
    points: list[str] = []
    for chunk in _ranked_note_chunks(topic_id, title, keywords):
        cleaned = _clean_chunk(chunk)
        if 45 <= len(cleaned) <= 240 and cleaned not in points:
            points.append(cleaned)
        if len(points) == limit:
            break
    return points


def essay_capable_topic_ids(topic_ids: set[str]) -> set[str]:
    blocked = {"1.1", "1.2.1"}
    return {topic_id for topic_id in topic_ids if topic_id not in blocked}


def _note_prefix(topic_id: str) -> str:
    parts = topic_id.split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}."
    return f"{topic_id}."


@lru_cache(maxsize=None)
def _note_text(topic_id: str) -> str:
    text = note_file_for_topic(topic_id).read_text(encoding="utf-8", errors="ignore")
    text = text.replace("\u200b", "").replace("​", "")
    text = re.sub(r"www\\.pmt\\.education|Edexcel Economics \\(A\\) A-level", " ", text)
    return text


def _ranked_note_chunks(topic_id: str, title: str, keywords: list[str] | tuple[str, ...]) -> list[str]:
    text = _note_text(topic_id)
    chunks = [_clean_chunk(line) for line in re.split(r"[\n•]+", text)]
    chunks = [chunk for chunk in chunks if 35 <= len(chunk) <= 280]
    terms = _search_terms(title, keywords)

    def score(chunk: str) -> tuple[int, int]:
        lowered = chunk.lower()
        exact = sum(3 for term in terms if term and term in lowered)
        partial = sum(1 for term in terms for word in term.split() if len(word) > 4 and word in lowered)
        return exact + partial, -len(chunk)

    ranked = sorted(chunks, key=score, reverse=True)
    return ranked or [_clean_chunk(text[:280])]


def _search_terms(title: str, keywords: list[str] | tuple[str, ...]) -> list[str]:
    raw_terms = [title, *keywords]
    terms: list[str] = []
    for term in raw_terms:
        lowered = term.lower().strip()
        if lowered and lowered not in terms:
            terms.append(lowered)
    return terms


def _clean_chunk(chunk: str) -> str:
    cleaned = " ".join(chunk.split())
    cleaned = re.sub(r"\s+([,.;:])", r"\1", cleaned)
    return cleaned.strip()
