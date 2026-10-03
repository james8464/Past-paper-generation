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
        paragraph.text for paragraph in technical.paragraphs
    )


def test_technical_report_shows_and_describes_the_real_mac_workflow() -> None:
    document = Document(build_technical_dossier())

    assert len(document.inline_shapes) == 1
    picture = document.inline_shapes[0]._inline.docPr
    assert "French NSI" in picture.get("descr", "")
    assert any("prototype interface" in paragraph.text.lower() for paragraph in document.paragraphs)


def test_supporting_reports_have_a_distinct_editorial_hierarchy() -> None:
    application = Document(build_application())
    technical = Document(build_technical_dossier())
    mathematical = Document(build_mathematical_analysis())

    assert application.paragraphs[0].runs[0].font.size.pt == 22
    for document in (technical, mathematical):
        assert document.paragraphs[0].runs[0].font.size.pt >= 28
    assert technical.styles["Normal"].font.size.pt >= 11
    assert mathematical.styles["Normal"].font.size.pt >= 10.5


def test_supporting_sources_are_clickable_without_long_printed_urls() -> None:
    for path, expected_links in (
        (build_technical_dossier(), 9),
        (build_mathematical_analysis(), 4),
    ):
        document = Document(path)
        links = [
            relation.target_ref
            for relation in document.part.rels.values()
            if relation.reltype.endswith("/hyperlink")
        ]
        assert len(links) == expected_links
        assert all(link.startswith("https://") for link in links)
        assert not any("https://" in paragraph.text for paragraph in document.paragraphs)


def test_editorial_reports_do_not_break_large_grids_across_pages() -> None:
    technical = Document(build_technical_dossier())
    mathematical = Document(build_mathematical_analysis())

    assert not technical.tables
    assert len(mathematical.tables) == 1


def test_formal_application_uses_readable_milestones_instead_of_split_grids() -> None:
    application = Document(build_application())
    text = " ".join(paragraph.text for paragraph in application.paragraphs)

    assert not application.tables
    assert "Mois 10 à 12" in text
    assert "500 €" in text
    assert "À compléter" in text
