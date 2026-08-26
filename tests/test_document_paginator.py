from __future__ import annotations

import pytest

from Backend.Core.document_dsl import (
    AnswerSpace,
    DocumentMetadata,
    DocumentRole,
    DocumentSpec,
    InstructionBlock,
    PageRole,
    PageSpec,
    PaginationError,
    Paginator,
    QuestionBlock,
)


def _document(*components: object) -> DocumentSpec:
    return DocumentSpec(
        profile_id="aqa",
        role=DocumentRole.QUESTION_PAPER,
        pages=(PageSpec(role=PageRole.QUESTION, components=components),),
        metadata=DocumentMetadata(title="Test", author="Paper Creator"),
    )


def test_paginator_splits_answer_space_only_at_deterministic_line_boundary() -> None:
    spec = _document(
        QuestionBlock(number="01", prompt="Discuss the issue.", marks=25),
        AnswerSpace(lines=80),
    )

    first = Paginator().layout(spec)
    second = Paginator().layout(spec)

    assert first == second
    assert len(first.pages) >= 2
    laid_out_lines = [
        box.component.lines
        for page in first.pages
        for box in page.boxes
        if isinstance(box.component, AnswerSpace)
    ]
    assert sum(laid_out_lines) == 80
    assert all(lines >= 3 for lines in laid_out_lines)


def test_paginator_keeps_heading_with_minimum_body_lines() -> None:
    filler = AnswerSpace(lines=42)
    block = InstructionBlock(
        heading="Information",
        items=tuple(f"Instruction {index}" for index in range(1, 10)),
        minimum_lines_after_heading=2,
    )
    plan = Paginator().layout(_document(filler, block))

    block_boxes = [
        box
        for page in plan.pages
        for box in page.boxes
        if isinstance(box.component, InstructionBlock)
    ]
    assert block_boxes
    assert all(box.height.pt >= block.minimum_fragment_height.pt for box in block_boxes)


def test_paginator_fails_fast_for_unsplittable_oversize_component() -> None:
    spec = _document(
        QuestionBlock(
            number="01",
            prompt="OneWord" * 20_000,
            marks=1,
            allow_split=False,
        )
    )

    with pytest.raises(PaginationError, match="cannot fit"):
        Paginator(max_operations=50).layout(spec)


def test_progress_watchdog_stops_non_progressing_splitter() -> None:
    class BrokenAnswerSpace(AnswerSpace):
        def split(self, profile, available):  # type: ignore[no-untyped-def]
            return self, self

    with pytest.raises(PaginationError, match="progress"):
        Paginator(max_operations=20).layout(_document(BrokenAnswerSpace(lines=100)))
