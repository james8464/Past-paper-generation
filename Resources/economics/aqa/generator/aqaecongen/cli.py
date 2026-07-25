from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path

from aqaecongen.configs import load_rule
from aqaecongen.generator import build_paper
from aqaecongen.render_pdf import render_mark_scheme, render_question_paper, render_source_booklet
from aqaecongen.syllabus import load_syllabus


def generate_package(
    *,
    paper: str,
    syllabus_path: Path,
    output_dir: Path,
    seed: int | None,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Path]:
    emit = progress or (lambda _message: None)
    emit("Loading AQA Economics specification map")
    syllabus = load_syllabus(syllabus_path)
    rule = load_rule(paper)
    emit("Building syllabus-specific paper blueprint")
    generated = build_paper(rule, syllabus, seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = rule.id.replace("_", "-")
    question_paper = output_dir / f"aqa-economics-{stem}-question-paper.pdf"
    mark_scheme = output_dir / f"aqa-economics-{stem}-mark-scheme.pdf"
    emit("Rendering question paper")
    render_question_paper(generated, question_paper)
    source_booklet = output_dir / f"aqa-economics-{stem}-source-insert.pdf"
    if rule.id == "paper_3":
        emit("Rendering source insert")
        render_source_booklet(generated, source_booklet)
    emit("Rendering mark scheme")
    render_mark_scheme(generated, mark_scheme)
    emit("Done")
    paths = {"question_paper": question_paper}
    if rule.id == "paper_3":
        paths["source_booklet"] = source_booklet
    paths["mark_scheme"] = mark_scheme
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate an independent AQA 7136 practice paper.")
    parser.add_argument("--paper", required=True)
    parser.add_argument("--syllabus", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int)
    args = parser.parse_args(argv)
    paths = generate_package(
        paper=args.paper,
        syllabus_path=args.syllabus,
        output_dir=args.out,
        seed=args.seed,
    )
    print(paths["question_paper"])
    print(paths["mark_scheme"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
