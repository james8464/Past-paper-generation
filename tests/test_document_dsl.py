from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

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
from Backend.Core.reportlab_theme import (
    AnswerLineFlowable,
    AQAAnswerLines,
    AQACompactAnswerLines,
    OCRAnswerLines,
    OCRComputerScienceAnswerLines,
)


@pytest.mark.parametrize(
    "profile_id", ["aqa", "cambridge-international", "ocr", "pearson-edexcel"]
)
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


def test_scheme_grid_wraps_long_guidance_inside_the_page(tmp_path: Path) -> None:
    ending = "supported conclusion at the end of the response"
    guidance = (
        "Credit an accurate applied chain of reasoning that distinguishes the "
        "initial change, the intermediate mechanism and a " + ending
    )
    spec = DocumentSpec(
        profile_id="cambridge-international",
        role=DocumentRole.MARK_SCHEME,
        pages=(
            PageSpec(
                role=PageRole.SCHEME,
                components=(
                    SchemeGrid(
                        headers=("Question", "Answer / marking guidance", "Marks"),
                        rows=(("1", guidance, "4"),),
                    ),
                ),
            ),
        ),
        metadata=DocumentMetadata(title="Scheme", author="Paper Creator"),
    )
    destination = tmp_path / "scheme.pdf"

    ReportLabBackend().render(Paginator().layout(spec), destination)

    with fitz.open(destination) as document:
        page = document[0]
        text = page.get_text()
        assert ending in " ".join(text.split())
        assert all(
            block[0] >= 0
            and block[1] >= 0
            and block[2] <= page.rect.width
            and block[3] <= page.rect.height
            for block in page.get_text("blocks")
        )


def test_scheme_grid_prioritises_guidance_column() -> None:
    grid = SchemeGrid(
        headers=("Question", "Answer / marking guidance", "Marks"),
        rows=(("1", "Credit a developed applied explanation.", "4"),),
    )

    assert grid.column_weights() == pytest.approx((0.14, 0.74, 0.12))


def test_question_mark_label_does_not_collide_with_prompt(tmp_path: Path) -> None:
    prompt = (
        "Analyse how a sustained increase in production costs could affect "
        "the organisation in the scenario."
    )
    spec = DocumentSpec(
        profile_id="cambridge-international",
        role=DocumentRole.QUESTION_PAPER,
        pages=(
            PageSpec(
                role=PageRole.QUESTION,
                components=(QuestionBlock(number="4", prompt=prompt, marks=8),),
            ),
        ),
        metadata=DocumentMetadata(title="Question", author="Paper Creator"),
    )
    destination = tmp_path / "question.pdf"

    ReportLabBackend().render(Paginator().layout(spec), destination)

    with fitz.open(destination) as document:
        words = document[0].get_text("words")
        mark_words = [word for word in words if "marks" in word[4]]
        assert len(mark_words) == 1
        mark = mark_words[0]
        prompt_words = [word for word in words if word[4].strip(".[]") in prompt]
        same_line = [
            word
            for word in prompt_words
            if word[1] < mark[3] and word[3] > mark[1]
        ]
        assert all(word[2] < mark[0] for word in same_line)


def test_cover_fits_long_paper_titles_inside_the_page(tmp_path: Path) -> None:
    spec = DocumentSpec(
        profile_id="cambridge-international",
        role=DocumentRole.MARK_SCHEME,
        pages=(
            PageSpec(
                role=PageRole.COVER,
                components=(
                    Cover(
                        title="Data Response and Essays Mark Scheme",
                        subtitle="Original practice material",
                        code="9708/2",
                    ),
                ),
            ),
        ),
        metadata=DocumentMetadata(title="Scheme", author="Paper Creator"),
    )
    destination = tmp_path / "long-cover.pdf"

    ReportLabBackend().render(Paginator().layout(spec), destination)

    with fitz.open(destination) as document:
        page = document[0]
        assert all(block[2] <= page.rect.width for block in page.get_text("blocks"))


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


def test_board_answer_line_presets_own_repeated_renderer_geometry() -> None:
    aqa = AQAAnswerLines(2)
    aqa_compact = AQACompactAnswerLines(2)
    ocr = OCRAnswerLines(2, spacing_mm=8)
    ocr_cs = OCRComputerScienceAnswerLines(2)

    assert (aqa.width * 25.4 / 72, aqa.spacing * 25.4 / 72) == pytest.approx(
        (167, 6)
    )
    assert (aqa.rule_width, aqa.dashed) == (0.35, False)
    assert (
        aqa_compact.width * 25.4 / 72,
        aqa_compact.spacing * 25.4 / 72,
    ) == pytest.approx((165, 6.2))
    assert (ocr.width * 25.4 / 72, ocr.spacing * 25.4 / 72) == pytest.approx(
        (167, 8)
    )
    assert (ocr_cs.width * 25.4 / 72, ocr_cs.spacing * 25.4 / 72) == pytest.approx(
        (165, 4.7)
    )


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


def test_shared_aqa_question_header_preserves_measured_geometry_and_text(
    tmp_path: Path,
) -> None:
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate
    from reportlab.platypus import Table as ReportLabTable

    import Backend.Core.document_dsl as document_dsl

    factory_type = getattr(document_dsl, "AQAQuestionHeaderFactory", None)
    assert factory_type is not None, "shared AQA question headers are not implemented"

    class FamilyTable(ReportLabTable):
        pass

    factory = factory_type(
        body_style=ParagraphStyle("QuestionBody", fontName="Helvetica", fontSize=11),
        marks_style=ParagraphStyle("QuestionMarks", fontName="Helvetica-Bold"),
        bold_font="Helvetica-Bold",
        ink=colors.black,
        table_class=FamilyTable,
    )
    table = factory.question_table(
        SimpleNamespace(number="1.2", prompt="Calculate the exact value.", marks=2)
    )

    assert isinstance(table, FamilyTable)
    assert isinstance(table._cellvalues[0][0], FamilyTable)
    assert table._colWidths == pytest.approx([14 * mm, 134 * mm, 19 * mm])
    destination = tmp_path / "aqa-question-header.pdf"
    SimpleDocTemplate(str(destination), pagesize=(210 * mm, 297 * mm)).build([table])
    with fitz.open(destination) as document:
        text = " ".join(document[0].get_text().split())
    assert "Calculate the exact value." in text
    assert "[2 marks]" in text


def test_shared_ocr_question_header_supports_board_specific_star_and_deferred_marks(
    tmp_path: Path,
) -> None:
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate
    from reportlab.platypus import Table as ReportLabTable

    import Backend.Core.document_dsl as document_dsl

    factory_type = getattr(document_dsl, "OCRQuestionHeaderFactory", None)
    assert factory_type is not None, "shared OCR question headers are not implemented"

    class FamilyTable(ReportLabTable):
        pass

    factory = factory_type(
        body_style=ParagraphStyle("OCRQuestionBody", fontName="Helvetica", fontSize=11),
        marks_style=ParagraphStyle("OCRQuestionMarks", fontName="Helvetica-Bold"),
        extended_response_threshold=15,
        table_class=FamilyTable,
    )
    question = SimpleNamespace(
        number="4",
        prompt="Evaluate the policy in the stated context.",
        marks=20,
    )
    table = factory.question_table(question, show_marks=False)

    assert isinstance(table, FamilyTable)
    assert table._colWidths == pytest.approx([155 * mm, 12 * mm])
    destination = tmp_path / "ocr-question-header.pdf"
    SimpleDocTemplate(str(destination), pagesize=(210 * mm, 297 * mm)).build([table])
    with fitz.open(destination) as document:
        text = " ".join(document[0].get_text().split())
    assert "4*" in text
    assert "Evaluate the policy in the stated context." in text
    assert "[20]" not in text


def test_shared_single_cell_panel_preserves_width_style_and_family_table() -> None:
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Table as ReportLabTable

    import Backend.Core.document_dsl as document_dsl

    factory_type = getattr(document_dsl, "SingleCellPanelFactory", None)
    assert factory_type is not None, "shared single-cell panels are not implemented"

    class FamilyTable(ReportLabTable):
        pass

    panel = factory_type(
        paragraph_style=ParagraphStyle("Panel", fontName="Helvetica-Bold"),
        width=167 * mm,
        background=colors.black,
        padding=7,
        table_class=FamilyTable,
    ).panel("Section A")

    assert isinstance(panel, FamilyTable)
    assert panel._colWidths == pytest.approx([167 * mm])
    assert panel._cellvalues[0][0].getPlainText() == "Section A"
