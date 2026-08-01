from __future__ import annotations

from pathlib import Path
from typing import Callable

from Backend.Core.ai_assessment import generate_unique_paper
from Backend.Core.assessment_package import write_assessment_package
from Backend.Core.providers import HostedLLMClient
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
    model: str = "qwen2.5:14b",
    ollama_url: str = "http://localhost:11434",
    dry_run: bool = True,
    progress: Callable[[str], None] | None = None,
    client: object | None = None,
) -> dict[str, Path]:
    update = progress or (lambda _message: None)
    update("Loading AQA Accounting specification map")
    syllabus = load_syllabus(syllabus_path)
    rule = load_rule(paper)
    update("Building AQA 7127 paper blueprint")
    generated = build_paper(rule, syllabus, seed)
    question_client = client
    if not dry_run:
        question_client = question_client or HostedLLMClient(
            provider="ollama",
            model=model,
            api_key="",
            base_url=ollama_url,
        )
        update(f"Generating and independently reviewing questions with {model}")
        generated = generate_unique_paper(
            generated,
            rule=rule,
            syllabus_topics=syllabus.topics,
            syllabus_topic_ids=syllabus.topic_ids,
            client=question_client,
            subject="AQA A-level Accounting",
            progress=progress,
        )
    else:
        update("Using the deterministic blueprint preview")
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"aqa-accounting-paper-{paper}"
    question_path = output_dir / f"{stem}-question-paper.pdf"
    scheme_path = output_dir / f"{stem}-mark-scheme.pdf"
    update("Rendering question paper")
    render_question_paper(generated, question_path)
    update("Rendering mark scheme")
    render_mark_scheme(generated, scheme_path)
    assessment_path = output_dir / f"{stem}-assessment.json"
    write_assessment_package(
        generated,
        assessment_path,
        subject="accounting_aqa",
        paper_number=paper,
        preview=dry_run,
        provider=getattr(question_client, "provider", None),
        model=getattr(question_client, "model", model),
    )
    return {
        "question_paper": question_path,
        "mark_scheme": scheme_path,
        "assessment_package": assessment_path,
    }
