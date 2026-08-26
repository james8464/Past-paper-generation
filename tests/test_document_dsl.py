from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from Backend.Core.document_dsl import (
    AccountingTable,
    AnswerSpace,
    BlankPage,
    BoardProfile,
    ContinuationPage,
    Cover,
    Diagram,
    DocumentMetadata,
    DocumentRole,
    DocumentSpec,
    EconomicCurve,
    Graph,
    InstructionBlock,
    LevelTable,
    LogicCircuit,
    MarkBox,
    MathematicalPlot,
    Molecule,
    PageRole,
    PageSpec,
    Paginator,
    ProgramTraceTable,
    QuestionBlock,
    RendererContract,
    ReportLabBackend,
    RuleSet,
    SchemeGrid,
    ScientificApparatus,
    SourcePanel,
    StatisticalChart,
    Table,
    board_profile,
    renderer_contract,
)
from Backend.Core.exam_cover import CoverProfile, QuestionPaperCover
from Backend.Core.exam_pages import ExamPage, ExamPageProfile
from Backend.Core.reportlab_theme import AnswerLineFlowable


@pytest.mark.parametrize("profile_id", ["aqa", "ocr", "pearson-edexcel"])
def test_every_existing_board_profile_has_print_safe_geometry(profile_id: str) -> None:
    profile = board_profile(profile_id)

    assert profile.page_width.pt == pytest.approx(595.2756, abs=0.1)
    assert profile.page_height.pt == pytest.approx(841.8898, abs=0.1)
    assert profile.content_frame.width.pt > 450
    assert profile.content_frame.height.pt > 650
    assert min(inset.pt for inset in profile.safe_print_insets) >= 14.17
    assert profile.fonts.body.name
    assert profile.rules.hairline.width.pt >= 0.1


def test_every_component_has_deterministic_positive_geometry() -> None:
    profile = board_profile("aqa")
    components = (
        Cover(title="Economics", subtitle="Paper 1", code="7136/1"),
        InstructionBlock(heading="Instructions", items=("Answer all questions.",)),
        QuestionBlock(number="01.1", prompt="Calculate the value.", marks=2),
        AnswerSpace(lines=4),
        MarkBox(marks=6),
        RuleSet(lines=3),
        Table(headers=("Year", "Value"), rows=(("2025", "10"),)),
        Graph(x_label="Quantity", y_label="Price", series=((0.0, 1.0), (1.0, 0.0))),
        Diagram(kind="logic", nodes=("A", "AND", "Q"), edges=((0, 1), (1, 2))),
        SourcePanel(title="Extract A", body="A short piece of source material."),
        SchemeGrid(headers=("Question", "Answer", "Marks"), rows=(("1", "10", "2"),)),
        LevelTable(levels=(("4", "Detailed analysis", "7–9"),)),
        BlankPage(message="BLANK PAGE"),
    )

    for component in components:
        first = component.measure(profile, profile.content_frame.size)
        second = component.measure(profile, profile.content_frame.size)
        assert first == second
        assert first.width.pt > 0
        assert first.height.pt > 0
        assert first.width.pt <= profile.content_frame.width.pt


def test_reportlab_backend_renders_selectable_tagged_metadata_atomically(
    tmp_path: Path,
) -> None:
    spec = DocumentSpec(
        profile_id="aqa",
        role=DocumentRole.QUESTION_PAPER,
        pages=(
            PageSpec(
                role=PageRole.COVER,
                components=(
                    Cover(title="Economics", subtitle="Paper 1", code="7136/1"),
                    InstructionBlock(
                        heading="Instructions",
                        items=("Answer all questions.",),
                    ),
                ),
            ),
            PageSpec(
                role=PageRole.QUESTION,
                components=(
                    QuestionBlock(number="01", prompt="Explain one reason.", marks=4),
                    AnswerSpace(lines=8),
                ),
            ),
        ),
        metadata=DocumentMetadata(
            title="Economics Paper 1",
            author="Paper Creator",
            subject="Independent practice material",
            language="en-GB",
        ),
    )
    destination = tmp_path / "nested" / "paper.pdf"
    evidence = ReportLabBackend().render(Paginator().layout(spec), destination)

    assert destination.exists()
    assert not destination.with_suffix(".pdf.tmp").exists()
    assert evidence.page_count == 2
    assert evidence.elapsed_seconds < 5
    assert evidence.sha256
    assert evidence.selectable_text
    with fitz.open(destination) as document:
        assert "Explain one reason" in "".join(page.get_text() for page in document)
        assert document.metadata["title"] == "Economics Paper 1"


def test_board_profile_rejects_content_outside_safe_print_area() -> None:
    with pytest.raises(ValueError, match="safe-print"):
        BoardProfile.testing(content_left=1)


def test_legacy_cover_and_special_pages_expose_dsl_components() -> None:
    cover = QuestionPaperCover(
        CoverProfile(
            board="aqa",
            subject="Economics",
            code="7136/1",
            paper_title="Paper 1",
            duration="2 hours",
            total_marks=80,
        ),
        font="Times-Roman",
        bold_font="Times-Bold",
    )
    page = ExamPage(
        ExamPageProfile(
            board="aqa",
            code="7136/1",
            heading="Extra space",
            variant="continuation",
        ),
        font="Times-Roman",
        bold_font="Times-Bold",
    )

    assert isinstance(cover.component, Cover)
    assert cover.component.code == "7136/1"
    assert page.component == ContinuationPage(heading="Extra space")


def test_shared_answer_lines_preserve_measured_geometry() -> None:
    lines = AnswerLineFlowable(5, width_mm=165, spacing_mm=6.2)

    assert lines.line_count == 5
    assert lines.height == pytest.approx(31 * 72 / 25.4)


def test_typed_vector_contracts_cover_current_and_future_subject_visuals() -> None:
    profile = board_profile("aqa")
    visuals = (
        EconomicCurve("Quantity", "Price", ((0, 1), (1, 0))),
        AccountingTable(("Account", "£"), (("Revenue", "100"),)),
        ProgramTraceTable(("Step", "x"), (("1", "2"),)),
        LogicCircuit("logic-circuit", ("A", "AND", "Q"), ((0, 1), (1, 2))),
        ScientificApparatus("scientific-apparatus", ("flask", "sensor"), ((0, 1),)),
        Molecule("molecule", ("C", "O", "O"), ((0, 1), (0, 2))),
        MathematicalPlot("x", "f(x)", ((-1, 1), (0, 0), (1, 1)), expression="x²"),
        StatisticalChart("Year", "Index", ((2024, 100), (2025, 105))),
    )

    assert all(
        visual.measure(profile, profile.content_frame.size).height.pt > 0
        for visual in visuals
    )


def test_renderer_contract_is_versioned_and_profile_backed() -> None:
    contract = renderer_contract(
        "ocr",
        roles=(DocumentRole.QUESTION_PAPER, DocumentRole.MARK_SCHEME),
        vector_components=("program-trace", "logic-circuit"),
    )

    assert isinstance(contract, RendererContract)
    assert contract.schema_version == 1
    assert contract.profile.id == "ocr"
