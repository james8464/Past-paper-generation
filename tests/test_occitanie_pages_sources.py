from xml.etree import ElementTree

import pytest

from tools import build_occitanie_pages_sources as sources


def test_english_rtf_has_explicit_pages_and_no_tables(tmp_path):
    paths = sources.build(tmp_path)
    assert len(paths) == 3
    assert [
        sources.render(report).count(r"\page" + "\n") + 1 for report in sources.REPORTS
    ] == [3, 4, 3]
    for path in paths:
        content = path.read_text("ascii")
        assert content.startswith(r"{\rtf1")
        assert r"\fs20" in content and r"\fs40" in content
        assert r"\trowd" not in content and r"\cell" not in content
        assert r"\intbl" not in content and r"\pict" not in content
        assert "SF Pro Text" in content and r"\lang2057" in content
        assert r"\fldinst PAGE" in content
    for report in (sources.TECHNICAL, sources.RELIABILITY):
        content = sources.render(report)
        assert r"\li3800" in content and r"\li3500" in content
        assert r"\sl-3400\slmult0 \u160?\par" in content
        assert r"\sb3400" not in content
        assert r"\pard\f1\fs56" in content
        assert r"\pard\f1\fs32" in content
        assert content.index(r"\u160?\par") < content.index("Keldin\\par")
        assert all(
            len(" ".join(text for _, text in page.sections).split()) <= 250
            for page in report.pages
        )


def test_form_has_translated_official_headings_and_language_notice():
    labels = [label for page in sources.APPLICATION.pages for label, _ in page.sections]
    assert labels == [
        "Identity",
        "Briefly introduce yourself",
        "Project title",
        "Summary of your project",
        "What is original about your project?",
        "Who could benefit from your project?",
        "What stage of development has your project reached?",
        "Have you already presented this project, and has it been the subject of a request for support?",
        "Additional information to explain your project",
    ]
    assert sources.APPLICATION.subtitle is None
    assert "English working draft" in sources.render(sources.APPLICATION)
    for report in sources.REPORTS:
        text = " ".join(
            value for page in report.pages for pair in page.sections for value in pair
        )
        assert "—" not in text and "–" not in text
        assert "à compléter" not in text and "Présentation" not in text


def test_rtf_unicode_and_control_characters_are_escaped():
    assert sources.rtf_text("é {x} \\") == r"\u233? \{x\} \\"
    assert sources.rtf_text("😀") == r"\u-10179?\u-8704?"


def test_supporting_report_uses_headings_and_paragraphs_not_bullet_lead_ins():
    content = sources.body_section(
        "Regional source", "A separate activity", formal=False
    )
    assert r"\b Regional source\par" in content
    assert r"\b0 A separate activity\par" in content
    assert r"\u8226?" not in content
    assert content.count(r"\li3800") == 2
    continuation = sources.body_section("", "The next paragraph.", formal=False)
    assert continuation.count(r"\par") == 2  # one paragraph command and its terminator
    assert r"\b " not in continuation


def test_current_reports_distinguish_model_generation_from_historical_catalogue():
    for report in (sources.TECHNICAL, sources.RELIABILITY):
        text = " ".join(text for page in report.pages for _, text in page.sections)
        assert "V36" in text
        assert "V35" in text
        assert "Public V35 constructs" not in text
        assert "model-free French route" not in text
    technical = " ".join(
        text for page in sources.TECHNICAL.pages for _, text in page.sections
    )
    assert (
        "has not yet produced a complete French paper that passes qualification"
        in technical
    )
    assert "asks the model to write" in technical
    assert (
        "French teacher review and learner timing studies have not been conducted"
        in technical
    )
    assert sources.DIAGRAMS["paper-structure.svg"][0] == "French V36"


def test_report_leads_with_regional_problem_and_avoids_labelled_block_rhythm():
    first_page = sources.TECHNICAL.pages[0]
    assert "CLEMENT MAROT" in first_page.sections[0][1]
    assert (
        sum(not label for page in sources.TECHNICAL.pages for label, _ in page.sections)
        >= 4
    )
    application = " ".join(
        text for page in sources.APPLICATION.pages for _, text in page.sections
    )
    assert "V35" not in application and "V36" not in application
    assert "Budget allocation: applicant to complete" in application
    for report in sources.REPORTS:
        text = " ".join(text for page in report.pages for _, text in page.sections)
        assert "not just" not in text and "not only" not in text
    reliability = " ".join(
        text for page in sources.RELIABILITY.pages for _, text in page.sections
    )
    assert "341-page review" in reliability
    assert "0 of 10" in reliability and "9.5%" in reliability


def test_existing_personal_documents_are_not_overwritten(tmp_path):
    path = tmp_path / sources.APPLICATION.filename
    path.write_text("personal edits", encoding="utf-8")
    with pytest.raises(FileExistsError):
        sources.build(tmp_path)
    assert path.read_text() == "personal edits"
    assert len(list(tmp_path.iterdir())) == 1


def test_original_diagrams_are_valid_bounded_svg(tmp_path):
    sources.build(tmp_path)
    assert len(list(tmp_path.glob("*.svg"))) == 4
    for path in tmp_path.glob("*.svg"):
        svg = ElementTree.parse(path).getroot()
        assert svg.attrib["viewBox"] == "0 0 150 360"
        content = path.read_text()
        assert "#FF9500" in content
        assert "<image" not in content and "href=" not in content
