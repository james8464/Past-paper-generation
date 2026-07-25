from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from ocregen.configs import load_rule
from ocregen.generator import build_paper
from ocregen.render_pdf import render_mark_scheme, render_question_paper
from ocregen.syllabus import load_syllabus


def generate_package(
    *,
    paper: str,
    syllabus_path: Path,
    output_dir: Path,
    seed: int | None,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Path]:
    emit = progress or (lambda _message: None)
    emit("Loading OCR Economics specification map")
    syllabus = load_syllabus(syllabus_path)
    rule = load_rule(paper)
    emit("Building OCR syllabus-specific blueprint")
    generated = build_paper(rule, syllabus, seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = rule.id.replace("_", "-")
    question = output_dir / f"ocr-economics-{stem}-question-paper.pdf"
    scheme = output_dir / f"ocr-economics-{stem}-mark-scheme.pdf"
    emit("Rendering question paper")
    render_question_paper(generated, question)
    emit("Rendering mark scheme")
    render_mark_scheme(generated, scheme)
    return {"question_paper": question, "mark_scheme": scheme}
