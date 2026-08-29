from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path

from aqaecongen.configs import load_rule
from aqaecongen.generator import build_paper
from aqaecongen.render_pdf import (
    render_mark_scheme,
    render_question_paper,
    render_source_booklet,
)
from aqaecongen.syllabus import load_syllabus
from Backend.Core.family_adapter import ArtifactSpec, FamilyAdapter, run_family_adapter
from Backend.Core.model_recommendations import default_ollama_model


def _artifacts(generated, _context, _syllabus, paper: str) -> tuple[ArtifactSpec, ...]:
    stem = f"aqa-economics-paper-{paper}"
    values = [
        ArtifactSpec(
            "question_paper",
            f"{stem}-question-paper.pdf",
            lambda path: render_question_paper(generated, path),
            "Rendering question paper",
        )
    ]
    if paper == "3":
        values.append(
            ArtifactSpec(
                "source_booklet",
                f"{stem}-source-insert.pdf",
                lambda path: render_source_booklet(generated, path),
                "Rendering source insert",
            )
        )
    values.append(
        ArtifactSpec(
            "mark_scheme",
            f"{stem}-mark-scheme.pdf",
            lambda path: render_mark_scheme(generated, path),
            "Rendering mark scheme",
        )
    )
    return tuple(values)


ADAPTER = FamilyAdapter(
    id="aqa/economics",
    subject_label="AQA A-level Economics",
    backend_subject="economics_aqa",
    load_message="Loading AQA Economics specification map",
    build_message="Building syllabus-specific paper blueprint",
    prompt_version="ai-assessment-v2",
    load_syllabus=load_syllabus,
    load_rule=load_rule,
    build=lambda rule, syllabus, seed: build_paper(rule, syllabus, seed),
    artifacts=_artifacts,
    stem=lambda _rule, paper: f"aqa-economics-paper-{paper}",
)


def generate_package(
    *,
    paper: str,
    syllabus_path: Path,
    output_dir: Path,
    seed: int | None,
    model: str = default_ollama_model(),
    ollama_url: str = "http://localhost:11434",
    dry_run: bool = True,
    progress: Callable[[str], None] | None = None,
    client: object | None = None,
    checkpoint_path: Path | None = None,
) -> dict[str, Path]:
    return run_family_adapter(
        ADAPTER,
        paper=paper,
        syllabus_path=syllabus_path,
        output_dir=output_dir,
        seed=seed,
        model=model,
        ollama_url=ollama_url,
        dry_run=dry_run,
        progress=progress,
        client=client,
        checkpoint_path=checkpoint_path,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate an independent AQA 7136 practice paper."
    )
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
