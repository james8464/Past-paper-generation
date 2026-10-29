import pytest

from tools import build_occitanie_pages_sources as sources


def test_three_editable_rtf_sources_have_explicit_page_plans(tmp_path):
    paths = sources.build(tmp_path)
    assert len(paths) == 3
    assert all(path.suffix == ".rtf" for path in paths)
    assert [
        sources.render(report).count(r"\page" + "\n") + 1 for report in sources.REPORTS
    ] == [3, 4, 3]
    for path in paths:
        content = path.read_text("ascii")
        assert content.startswith(r"{\rtf1")
        assert r"\fs21" in content and r"\fs40" in content
        assert r"\trftsWidth3\trwWidth9600" in content
        assert r"\clftsWidth3\clwWidth2700" in content
        assert r"\clftsWidth3\clwWidth6900" in content
        assert (
            r"\clbrdrt\brdrnil\clbrdrl\brdrnil\clbrdrb\brdrnil\clbrdrr\brdrnil"
            in content
        )
        assert r"\fldinst PAGE" in content
        assert "SF Pro Text" in content
        assert r"\pict" not in content and "docx" not in content


def test_form_preserves_required_headings_and_only_personal_unknowns():
    labels = [label for page in sources.APPLICATION.pages for label, _ in page.rows]
    assert labels == [
        "Identité",
        "Présentez-vous brièvement",
        "Titre du projet",
        "Description synthétique de votre projet",
        "Quelle est l'originalité de votre projet ?",
        "A qui pourra bénéficier le projet que vous proposez ?",
        "A quel stade de développement en est votre projet ?",
        "Avez-vous déjà eu l’opportunité de présenter ce projet ? et ce projet a-t-il déjà fait l’objet d’une demande d’aide ?",
        "Eléments complémentaires que vous souhaitez apporter pour préciser votre projet",
    ]
    assert sources.APPLICATION.cover is None
    for report in sources.REPORTS:
        text = " ".join(
            value for page in report.pages for pair in page.rows for value in pair
        )
        assert "V35" in text
        assert "—" not in text and "–" not in text
        assert (
            "teacher approval" not in text
            or "No examiner approval" in text
            or "Teacher review" in text
        )


def test_rtf_unicode_and_control_characters_are_escaped():
    assert sources.rtf_text("é {x} \\") == r"\u233? \{x\} \\"
    assert sources.rtf_text("😀") == r"\u-10179?\u-8704?"


def test_existing_personal_documents_are_not_overwritten(tmp_path):
    path = tmp_path / sources.APPLICATION.filename
    path.write_text("personal edits", encoding="utf-8")
    with pytest.raises(FileExistsError):
        sources.build(tmp_path)
    assert path.read_text() == "personal edits"
    assert len(list(tmp_path.iterdir())) == 1
