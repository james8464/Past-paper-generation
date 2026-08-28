from __future__ import annotations

from pathlib import Path

from Backend.Core.document_dsl.components import (
    AnswerSpace,
    Cover,
    InstructionBlock,
    QuestionBlock,
    SchemeGrid,
    SourcePanel,
)
from Backend.Core.document_dsl.model import (
    DocumentMetadata,
    DocumentRole,
    DocumentSpec,
    PageRole,
    PageSpec,
)
from Backend.Core.document_dsl.paginator import Paginator
from Backend.Core.document_dsl.reportlab_backend import ReportLabBackend
from Backend.Core.exam_blueprints import GeneratedPaper
from configuredgen.models import ConfiguredSyllabus, PaperSpecification


def render_question_paper(
    paper: GeneratedPaper,
    destination: Path,
    *,
    syllabus: ConfiguredSyllabus,
    specification: PaperSpecification,
) -> None:
    pages = [
        PageSpec(
            role=PageRole.COVER,
            label="cover",
            components=(
                Cover(
                    title=paper.title,
                    subtitle=_duration(paper.duration_minutes),
                    code=paper.paper_code,
                    board_label="PAPER CREATOR • CAMBRIDGE-STYLE PRACTICE",
                ),
                InstructionBlock(
                    heading="Instructions",
                    items=tuple(
                        [
                            *specification.instructions,
                            f"The total mark for this paper is {paper.total_marks}.",
                            "This original practice paper is not endorsed by Cambridge International.",
                        ]
                    ),
                ),
            ),
        )
    ]
    for section in paper.sections:
        components: list[object] = [
            InstructionBlock(
                heading=section.title,
                items=(section.instructions,),
            )
        ]
        for option in section.options:
            if option.stimulus:
                components.append(
                    SourcePanel(
                        title=option.title,
                        body=" ".join(option.stimulus),
                    )
                )
            for question in option.questions:
                prompt = question.prompt
                if question.choices:
                    prompt += " " + " ".join(
                        f"{chr(65 + index)} {choice}"
                        for index, choice in enumerate(question.choices)
                    )
                components.append(
                    QuestionBlock(
                        number=question.number,
                        prompt=prompt,
                        marks=question.marks,
                    )
                )
                if question.kind != "multiple_choice":
                    components.append(
                        AnswerSpace(lines=max(3, min(20, question.marks)))
                    )
        pages.append(
            PageSpec(
                role=PageRole.QUESTION,
                label=f"section-{section.id}",
                components=tuple(components),
            )
        )
    _render(
        DocumentSpec(
            profile_id=syllabus.board_profile,
            role=DocumentRole.QUESTION_PAPER,
            pages=tuple(pages),
            metadata=_metadata(paper, syllabus),
        ),
        destination,
    )


def render_mark_scheme(
    paper: GeneratedPaper,
    destination: Path,
    *,
    syllabus: ConfiguredSyllabus,
) -> None:
    components: list[object] = [
        Cover(
            title=f"{paper.title} mark scheme",
            subtitle="Original practice material",
            code=paper.paper_code,
            board_label="PAPER CREATOR",
        )
    ]
    for section in paper.sections:
        for option in section.options:
            for question in option.questions:
                rows = tuple(
                    (
                        question.number if index == 0 else "",
                        point.text,
                        str(point.marks),
                    )
                    for index, point in enumerate(question.structured_mark_scheme)
                )
                components.append(
                    SchemeGrid(
                        headers=("Question", "Answer / marking guidance", "Marks"),
                        rows=rows,
                    )
                )
    _render(
        DocumentSpec(
            profile_id=syllabus.board_profile,
            role=DocumentRole.MARK_SCHEME,
            pages=(
                PageSpec(
                    role=PageRole.SCHEME,
                    label="mark-scheme",
                    components=tuple(components),
                ),
            ),
            metadata=_metadata(paper, syllabus),
        ),
        destination,
    )


def _render(specification: DocumentSpec, destination: Path) -> None:
    plan = Paginator().layout(specification)
    evidence = ReportLabBackend().render(plan, destination)
    if not evidence.selectable_text or not evidence.atomic_publication:
        raise RuntimeError("configured renderer did not produce a usable PDF")


def _metadata(
    paper: GeneratedPaper,
    syllabus: ConfiguredSyllabus,
) -> DocumentMetadata:
    return DocumentMetadata(
        title=f"{paper.title} – original practice",
        author="Paper Creator",
        subject=syllabus.subject_label,
        keywords=(
            "unofficial practice",
            syllabus.specification_version,
            syllabus.blueprint_version,
        ),
    )


def _duration(minutes: int) -> str:
    hours, remainder = divmod(minutes, 60)
    parts: list[str] = []
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if remainder:
        parts.append(f"{remainder} minutes")
    return " ".join(parts)
