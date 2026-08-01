from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from Backend.Core.ai_assessment import generate_unique_paper
from Backend.Core.assessment_package import write_assessment_package
from Backend.Core.providers import HostedLLMClient
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
    model: str = "qwen2.5:14b",
    ollama_url: str = "http://localhost:11434",
    dry_run: bool = True,
    progress: Callable[[str], None] | None = None,
    client: object | None = None,
) -> dict[str, Path]:
    emit = progress or (lambda _message: None)
    emit("Loading AQA Business specification map")
    syllabus = load_syllabus(syllabus_path)
    rule = load_rule(paper)
    emit("Building AQA 7132 paper blueprint")
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
            subject="AQA A-level Business",
            progress=progress,
        )
    else:
        emit("Using the deterministic blueprint preview")
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
    assessment = output_dir / f"aqa-business-{stem}-assessment.json"
    write_assessment_package(
        generated,
        assessment,
        subject="business_aqa",
        paper_number=paper,
        preview=dry_run,
        provider=getattr(question_client, "provider", None),
        model=getattr(question_client, "model", model),
    )
    paths["assessment_package"] = assessment
    return paths
