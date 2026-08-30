from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from aqaaccountgen.configs import load_rule
from aqaaccountgen.generator import build_paper
from aqaaccountgen.render_pdf import render_mark_scheme, render_question_paper
from aqaaccountgen.syllabus import load_syllabus
from Backend.Core.family_adapter import ArtifactSpec, FamilyAdapter, run_family_adapter
from Backend.Core.model_recommendations import default_ollama_model


def _artifacts(generated, _context, _syllabus, paper: str) -> tuple[ArtifactSpec, ...]:
    stem = f"aqa-accounting-paper-{paper}"
    return (
        ArtifactSpec(
            "question_paper",
            f"{stem}-question-paper.pdf",
            lambda path: render_question_paper(generated, path),
            "Rendering question paper",
        ),
        ArtifactSpec(
            "mark_scheme",
            f"{stem}-mark-scheme.pdf",
            lambda path: render_mark_scheme(generated, path),
            "Rendering mark scheme",
        ),
    )


ADAPTER = FamilyAdapter(
    id="aqa/accounting",
    subject_label="AQA A-level Accounting",
    backend_subject="accounting_aqa",
    load_message="Loading AQA Accounting specification map",
    build_message="Building AQA 7127 paper blueprint",
    prompt_version="ai-assessment-v5",
    load_syllabus=load_syllabus,
    load_rule=load_rule,
    build=lambda rule, syllabus, seed: build_paper(rule, syllabus, seed),
    artifacts=_artifacts,
    stem=lambda _rule, paper: f"aqa-accounting-paper-{paper}",
)


def generate_package(
    *,
    paper: str,
    syllabus_path: Path,
    output_dir: Path,
    seed: int | None = None,
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
