from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

DEFAULT_NOTES_SOURCE = Path("/Users/james/Downloads/CS Notes")
DEFAULT_NOTES_CACHE = Path.home() / "Library" / "Caches" / "Past Paper Creation" / "cs-notes"


@dataclass(frozen=True)
class NotesManifest:
    source_dir: Path
    cache_dir: Path
    pdf_count: int
    text_count: int


def discover_note_pdfs(source_dir: Path = DEFAULT_NOTES_SOURCE) -> list[Path]:
    if not source_dir.exists():
        return []
    return sorted(source_dir.glob("*.pdf"))


def cache_notes(source_dir: Path = DEFAULT_NOTES_SOURCE, cache_dir: Path = DEFAULT_NOTES_CACHE) -> NotesManifest:
    raw_dir = cache_dir / "raw"
    text_dir = cache_dir / "text"
    raw_dir.mkdir(parents=True, exist_ok=True)
    text_dir.mkdir(parents=True, exist_ok=True)

    pdfs = discover_note_pdfs(source_dir)
    text_count = 0
    for pdf in pdfs:
        copied = raw_dir / pdf.name
        if not copied.exists() or copied.stat().st_size != pdf.stat().st_size:
            shutil.copy2(pdf, copied)
        text_path = text_dir / f"{pdf.stem}.txt"
        if not text_path.exists() or text_path.stat().st_mtime < copied.stat().st_mtime:
            _extract_text(copied, text_path)
        if text_path.exists() and text_path.stat().st_size > 0:
            text_count += 1

    return NotesManifest(source_dir=source_dir, cache_dir=cache_dir, pdf_count=len(pdfs), text_count=text_count)


def note_context_for_topic(topic_id: str, title: str, cache_dir: Path = DEFAULT_NOTES_CACHE, max_chars: int = 2200) -> str:
    text_dir = cache_dir / "text"
    if not text_dir.exists():
        return ""
    prefixes = _topic_prefixes(topic_id)
    chunks: list[str] = []
    for text_file in sorted(text_dir.glob("*.txt")):
        if any(text_file.name.startswith(prefix) for prefix in prefixes):
            chunks.append(text_file.read_text(encoding="utf-8", errors="ignore")[:max_chars])
    if not chunks:
        for text_file in sorted(text_dir.glob("*.txt")):
            content = text_file.read_text(encoding="utf-8", errors="ignore")
            if title.lower().split()[0] in content.lower():
                chunks.append(content[:max_chars])
                break
    return "\n\n".join(chunks)[:max_chars]


def _topic_prefixes(topic_id: str) -> tuple[str, ...]:
    mapping = {
        "4.5": ("5.",),
        "4.6": ("6.",),
        "4.7": ("7.",),
        "4.8": ("8.",),
        "4.9": ("9.",),
        "4.10": ("10.",),
        "4.11": ("11.",),
        "4.12": ("12.",),
    }
    return mapping.get(topic_id, (topic_id,))


def _extract_text(pdf: Path, text_path: Path) -> None:
    try:
        subprocess.run(["pdftotext", "-layout", str(pdf), str(text_path)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError):
        text_path.write_text("", encoding="utf-8")
