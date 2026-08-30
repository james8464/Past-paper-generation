from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from Backend.Core.family_adapter import ArtifactSpec, FamilyAdapter, run_family_adapter
from Backend.Core.model_recommendations import default_ollama_model
from ocrcsgen.configs import load_rule
from ocrcsgen.generator import build_paper
from ocrcsgen.render_pdf import render_mark_scheme, render_question_paper
from ocrcsgen.syllabus import load_syllabus


def _stem(rule, _paper: str) -> str:
    return f"ocr-computer-science-{rule.id.replace('_', '-')}"


def _artifacts(generated, _context, _syllabus, paper: str) -> tuple[ArtifactSpec, ...]:
    stem = f"ocr-computer-science-paper-{paper}"
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
    id="ocr/computer-science",
    subject_label="OCR A-level Computer Science",
    backend_subject="computer_science_ocr",
    load_message="Loading OCR Computer Science specification map",
    build_message="Building OCR H446 paper blueprint",
    prompt_version="ai-assessment-v3",
    load_syllabus=load_syllabus,
    load_rule=load_rule,
    build=lambda rule, syllabus, seed: build_paper(rule, syllabus, seed),
    artifacts=_artifacts,
    stem=_stem,
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
