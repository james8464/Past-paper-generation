from __future__ import annotations

from pathlib import Path
from typing import Callable

from aqaaccountgen.configs import load_rule
from aqaaccountgen.generator import build_paper
from aqaaccountgen.render_pdf import render_mark_scheme, render_question_paper
from aqaaccountgen.syllabus import load_syllabus


def generate_package(
    *,
    paper: str,
    syllabus_path: Path,
    output_dir: Path,
    seed: int | None = None,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Path]:
    update = progress or (lambda _message: None)
    update("Loading AQA Accounting specification map")
    syllabus = load_syllabus(syllabus_path)
    rule = load_rule(paper)
    update("Building AQA 7127 paper blueprint")
    generated = build_paper(rule, syllabus, seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"aqa-accounting-paper-{paper}"
    question_path = output_dir / f"{stem}-question-paper.pdf"
    scheme_path = output_dir / f"{stem}-mark-scheme.pdf"
    update("Rendering question paper")
    render_question_paper(generated, question_path)
    update("Rendering mark scheme")
    render_mark_scheme(generated, scheme_path)
    return {"question_paper": question_path, "mark_scheme": scheme_path}
