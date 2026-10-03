from docx import Document

from tools.build_occitanie_submission import (
    build_application,
    build_mathematical_analysis,
    build_technical_dossier,
    configure_document,
    finalize_fonts,
    title_block,
)


def test_application_title_uses_a_real_title_paragraph() -> None:
    document = Document()
    configure_document(document, compact=True)

    title_block(document, "Candidature au Prix Occitanie 2026", "Paper Creator")

    assert document.paragraphs[0].style.name == "Title"
    assert document.paragraphs[0].text == "Candidature au Prix Occitanie 2026"
    assert document.paragraphs[1].text == "Paper Creator"
    assert not document.tables


def test_explicit_fonts_preserve_the_document_hierarchy() -> None:
    document = Document()
    configure_document(document, compact=True)
    title_block(document, "Candidature au Prix Occitanie 2026", "Paper Creator")
    heading = document.add_heading("Présentation du candidat", level=1)
    heading.add_run(" ")

    finalize_fonts(document)

    assert document.paragraphs[0].runs[0].font.size.pt == 22
    assert document.paragraphs[0].runs[0].font.name == "Arial"
    assert heading.runs[0].font.size.pt == 13.5


def test_supporting_reports_are_in_english_while_the_application_stays_french() -> None:
    application = Document(build_application())
    technical = Document(build_technical_dossier())
    mathematical = Document(build_mathematical_analysis())

    assert application.paragraphs[0].text == "Candidature au Prix Occitanie 2026"
    assert technical.paragraphs[0].text == "Paper Creator for French NSI"
    assert mathematical.paragraphs[0].text == "Mathematical analysis of qualification"
    assert "0/10 accepted" in " ".join(
        cell.text for table in technical.tables for row in table.rows for cell in row.cells
    )
