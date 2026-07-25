from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from aqabizgen.configs import load_rule
from aqabizgen.generator import build_paper
from aqabizgen.render_pdf import (
    render_mark_scheme,
    render_question_paper,
    render_source_booklet,
)
from aqabizgen.syllabus import load_syllabus


def generate_package(
    *,
    paper: str,
    syllabus_path: Path,
    output_dir: Path,
    seed: int | None,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Path]:
    emit = progress or (lambda _message: None)
    emit("Loading AQA Business specification map")
    syllabus = load_syllabus(syllabus_path)
    rule = load_rule(paper)
    emit("Building AQA 7132 paper blueprint")
    generated = build_paper(rule, syllabus, seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = rule.id.replace("_", "-")
    question = output_dir / f"aqa-business-{stem}-question-paper.pdf"
    scheme = output_dir / f"aqa-business-{stem}-mark-scheme.pdf"
    emit("Rendering question paper")
    render_question_paper(generated, question)
    emit("Rendering mark scheme")
    render_mark_scheme(generated, scheme)
    paths = {"question_paper": question, "mark_scheme": scheme}
    if rule.id == "paper_3":
        source = output_dir / f"aqa-business-{stem}-source-booklet.pdf"
        emit("Rendering source booklet")
        render_source_booklet(generated, source)
        paths = {
            "question_paper": question,
            "source_booklet": source,
            "mark_scheme": scheme,
        }
    return paths
