from docx import Document

from tools.build_occitanie_submission import (
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
