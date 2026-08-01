from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path

from Backend.Core.ai_assessment import generate_unique_paper
from Backend.Core.assessment_package import write_assessment_package
from Backend.Core.providers import HostedLLMClient
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
    model: str = "qwen2.5:14b",
    ollama_url: str = "http://localhost:11434",
    dry_run: bool = True,
    progress: Callable[[str], None] | None = None,
    client: object | None = None,
) -> dict[str, Path]:
    emit = progress or (lambda _message: None)
    emit("Loading AQA Economics specification map")
    syllabus = load_syllabus(syllabus_path)
    rule = load_rule(paper)
    emit("Building syllabus-specific paper blueprint")
    generated = build_paper(rule, syllabus, seed)
    question_client = client
    if not dry_run:
        question_client = question_client or HostedLLMClient(
            provider="ollama",
            model=model,
            api_key="",
            base_url=ollama_url,
        )
        emit(f"Generating and independently reviewing questions with {model}")
        generated = generate_unique_paper(
            generated,
            rule=rule,
            syllabus_topics=syllabus.topics,
            syllabus_topic_ids=syllabus.topic_ids,
            client=question_client,
            subject="AQA A-level Economics",
            progress=progress,
        )
    else:
        emit("Using the deterministic blueprint preview")
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
    assessment = output_dir / f"aqa-economics-{stem}-assessment.json"
    write_assessment_package(
        generated,
        assessment,
        subject="economics_aqa",
        paper_number=paper,
        preview=dry_run,
        provider=getattr(question_client, "provider", None),
        model=getattr(question_client, "model", model),
    )
    paths["assessment_package"] = assessment
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
