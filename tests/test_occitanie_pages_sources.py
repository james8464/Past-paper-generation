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
        assert "V35" in text
        assert "—" not in text and "–" not in text
        assert "à compléter" not in text and "Présentation" not in text


def test_rtf_unicode_and_control_characters_are_escaped():
    assert sources.rtf_text("é {x} \\") == r"\u233? \{x\} \\"
    assert sources.rtf_text("😀") == r"\u-10179?\u-8704?"


def test_bold_lead_in_has_an_explicit_visible_separator():
    content = sources.body_section(
        "Regional source", "A separate activity", formal=False
    )
    assert r"Regional source.\b0\~ A separate activity" in content


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
