from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from Backend.Core.ai_assessment import generate_unique_paper
from Backend.Core.assessment_package import write_assessment_package
from Backend.Core.providers import HostedLLMClient
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
    model: str = "qwen2.5:14b",
    ollama_url: str = "http://localhost:11434",
    dry_run: bool = True,
    progress: Callable[[str], None] | None = None,
    client: object | None = None,
) -> dict[str, Path]:
    emit = progress or (lambda _message: None)
    emit("Loading OCR Economics specification map")
    syllabus = load_syllabus(syllabus_path)
    rule = load_rule(paper)
    emit("Building OCR syllabus-specific blueprint")
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
            subject="OCR A-level Economics",
            progress=progress,
        )
    else:
        emit("Using the deterministic blueprint preview")
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = rule.id.replace("_", "-")
    question = output_dir / f"ocr-economics-{stem}-question-paper.pdf"
    scheme = output_dir / f"ocr-economics-{stem}-mark-scheme.pdf"
    emit("Rendering question paper")
    render_question_paper(generated, question)
    emit("Rendering mark scheme")
    render_mark_scheme(generated, scheme)
    assessment = output_dir / f"ocr-economics-{stem}-assessment.json"
    write_assessment_package(
        generated,
        assessment,
        subject="economics_ocr",
        paper_number=paper,
        preview=dry_run,
        provider=getattr(question_client, "provider", None),
        model=getattr(question_client, "model", model),
    )
    return {
        "question_paper": question,
        "mark_scheme": scheme,
        "assessment_package": assessment,
    }
