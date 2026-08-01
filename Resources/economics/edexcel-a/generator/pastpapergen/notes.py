from __future__ import annotations

import re
import sys
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_BUNDLE_ROOT = (
    Path(getattr(sys, "_MEIPASS"))
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")
    else PROJECT_ROOT
)
_BUNDLED_NOTES_TEXT_DIR = (
    _BUNDLE_ROOT
    / "Resources"
    / "economics"
    / "edexcel-a"
    / "generator"
    / "data"
    / "notes"
    / "text"
)
NOTES_TEXT_DIR = (
    _BUNDLED_NOTES_TEXT_DIR
    if _BUNDLED_NOTES_TEXT_DIR.is_dir()
    else PROJECT_ROOT / "data" / "notes" / "text"
)


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
        if _is_exam_point(cleaned) and cleaned not in points:
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
    try:
        text = note_file_for_topic(topic_id).read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        return ""
    text = text.replace("\u200b", "").replace("​", "")
    text = re.sub(r"www\\.pmt\\.education|Edexcel Economics \\(A\\) A-level", " ", text)
    return text


def _ranked_note_chunks(topic_id: str, title: str, keywords: list[str] | tuple[str, ...]) -> list[str]:
    return _ranked_note_chunks_cached(topic_id, title, tuple(keywords))


@lru_cache(maxsize=512)
def _ranked_note_chunks_cached(topic_id: str, title: str, keywords: tuple[str, ...]) -> list[str]:
    text = _note_text(topic_id)
    chunks = [_clean_chunk(chunk) for chunk in _note_chunks(text)]
    chunks = [chunk for chunk in chunks if 35 <= len(chunk) <= 320]
    terms = _search_terms(title, keywords)

    def score(chunk: str) -> tuple[int, int]:
        lowered = chunk.lower()
        exact = sum(3 for term in terms if term and term in lowered)
        partial = sum(1 for term in terms for word in term.split() if len(word) > 4 and word in lowered)
        return exact + partial, -len(chunk)

    ranked = sorted(chunks, key=score, reverse=True)
    return ranked or [_clean_chunk(text[:280])]


def _note_chunks(text: str) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    for raw_line in text.replace("\f", "\n").splitlines():
        line = _clean_chunk(raw_line)
        if not line:
            _flush_note_chunk(chunks, current)
            current = []
            continue
        if _is_note_noise(line):
            continue
        bullet = re.match(r"^(?:[•●]|\-\s+|o\s+)(.+)$", line)
        if bullet:
            _flush_note_chunk(chunks, current)
            current = [bullet.group(1).strip()]
            continue
        if current and _looks_like_heading(line):
            _flush_note_chunk(chunks, current)
            current = []
            continue
        current.append(line)
    _flush_note_chunk(chunks, current)
    return chunks


def _flush_note_chunk(chunks: list[str], current: list[str]) -> None:
    cleaned = _clean_chunk(" ".join(current))
    if cleaned:
        chunks.append(cleaned)


def _is_note_noise(line: str) -> bool:
    lowered = line.lower()
    return (
        lowered.startswith("theme ")
        or lowered.startswith("edexcel economics")
        or lowered == "detailed notes"
        or "www.pmt.education" in lowered
        or "bit.ly/pmt" in lowered
        or "licensed under" in lowered
    )


def _looks_like_heading(line: str) -> bool:
    if line.endswith(":") and len(line.split()) <= 7:
        return True
    return bool(re.match(r"^\d+(?:\.\d+)+\s+[A-Z]", line))


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
    cleaned = re.sub(r"^(?:[•●]\s*|\-\s+|o\s+)+", "", cleaned)
    cleaned = re.sub(r"\s+([,.;:])", r"\1", cleaned)
    return cleaned.strip()


def _is_exam_point(cleaned: str) -> bool:
    if not 45 <= len(cleaned) <= 260:
        return False
    if len(cleaned.split()) < 8:
        return False
    lowered = cleaned.lower()
    if "http" in lowered or "pmt" in lowered:
        return False
    if cleaned[-1] not in ".;?)":
        return False
    if cleaned[0].islower() or cleaned[0].isdigit():
        return False
    if cleaned.endswith(":"):
        return False
    weak_starts = (
        "advantage",
        "disadvantage",
        "advantages",
        "disadvantages",
        "some example",
        "as a result",
        "this diagram",
        "this shifts",
        "shown by",
    )
    return not lowered.startswith(weak_starts)
