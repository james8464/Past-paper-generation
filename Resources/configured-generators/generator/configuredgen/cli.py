from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from Backend.Core.family_adapter import (
    ArtifactSpec,
    FamilyAdapter,
    run_family_adapter,
)
from Backend.Core.model_recommendations import default_ollama_model
from configuredgen.generator import build_paper
from configuredgen.models import ConfiguredSyllabus, load_syllabus
from configuredgen.render_pdf import render_mark_scheme, render_question_paper


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
    syllabus = load_syllabus(syllabus_path)
    specification = syllabus.paper(paper)
    adapter = _adapter(syllabus, specification.id)
    return run_family_adapter(
        adapter,
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


def _adapter(syllabus: ConfiguredSyllabus, paper_id: str) -> FamilyAdapter:
    specification = syllabus.paper(paper_id)

    def artifacts(generated, _context, _loaded, paper: str):
        stem = f"{syllabus.subject_plugin}-{syllabus.board_profile}-paper-{paper}"
        return (
            ArtifactSpec(
                "question_paper",
                f"{stem}-question-paper.pdf",
                lambda path: render_question_paper(
                    generated,
                    path,
                    syllabus=syllabus,
                    specification=specification,
                ),
                "Rendering question paper",
            ),
            ArtifactSpec(
                "mark_scheme",
                f"{stem}-mark-scheme.pdf",
                lambda path: render_mark_scheme(
                    generated,
                    path,
                    syllabus=syllabus,
                ),
                "Rendering mark scheme",
            ),
        )

    def supporting(
        _assessment,
        _context,
        _loaded,
        paper: str,
        output: Path,
        emit,
    ) -> dict[str, Path]:
        result: dict[str, Path] = {}
        roles = set(syllabus.paper(paper).output_roles)
        if "evidence_document" in roles:
            emit("Creating practical testing-evidence template")
            path = output / f"{syllabus.subject_plugin}-paper-{paper}-evidence.txt"
            path.write_text(
                "Testing evidence\n\nTest data:\nExpected result:\nActual result:\n",
                encoding="utf-8",
            )
            result["evidence_document"] = path
        if "source_file" in roles:
            emit("Creating practical source-file template")
            path = output / f"{syllabus.subject_plugin}-paper-{paper}-solution.py"
            path.write_text(
                '"""Candidate source file. Complete this original task offline."""\n\n'
                "def main() -> None:\n"
                "    raise NotImplementedError(\"Complete the examination task\")\n\n"
                'if __name__ == "__main__":\n'
                "    main()\n",
                encoding="utf-8",
            )
            result["source_file"] = path
        return result

    return FamilyAdapter(
        id=syllabus.family_id,
        subject_label=syllabus.subject_label,
        backend_subject=syllabus.backend_subject,
        load_message=f"Loading {syllabus.specification_version} specification map",
        build_message="Building specification-constrained paper blueprint",
        prompt_version="configured-assessment-v2",
        load_syllabus=lambda _path: syllabus,
        load_rule=syllabus.rule,
        build=build_paper,
        artifacts=artifacts,
        stem=lambda _rule, paper: (
            f"{syllabus.subject_plugin}-{syllabus.board_profile}-paper-{paper}"
        ),
        supporting_artifacts=(
            supporting
            if {"evidence_document", "source_file"}
            & set(specification.output_roles)
            else None
        ),
        output_order=tuple(specification.output_roles),
    )
