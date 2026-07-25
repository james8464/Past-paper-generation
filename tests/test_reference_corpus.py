import json
from pathlib import Path

import pytest

from tools.reference_corpus import (
    download_manifest,
    document_path,
    parse_aqa_resources,
    parse_ocr_resources,
    parse_ocr_specifications,
    parse_pearson_resource,
    summarize_profiles,
)


def test_parse_aqa_resources_filters_modified_papers() -> None:
    page = r'''
    \"originalFilename\":\"AQA-71271-QP-JUN25.PDF\",\"sha1hash\":\"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\",\"size\":12,\"url\":\"https://cdn.sanity.io/files/p28bar15/green/a.pdf\"}},\"title\":\"Question paper: Paper 1 - June 2025\"
    \"originalFilename\":\"AQA-71271-QP-JUN25-MQP36.PDF\",\"sha1hash\":\"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\",\"size\":13,\"url\":\"https://cdn.sanity.io/files/p28bar15/green/b.pdf\"}},\"title\":\"Question paper (Modified A4 36pt): Paper 1 - June 2025\"
    '''

    resources = parse_aqa_resources(
        page,
        page_url="https://www.aqa.org.uk/example",
        subject="accounting",
        qualification_slug="accounting-7127",
    )

    assert len(resources) == 1
    assert resources[0]["kind"] == "question-papers"
    assert resources[0]["filename"] == "AQA-71271-QP-JUN25.PDF"


def test_document_path_stays_inside_corpus(tmp_path: Path) -> None:
    item = {
        "qualification": "a-level",
        "board": "aqa",
        "subject": "accounting",
        "qualification_slug": "accounting-7127",
        "kind": "question-papers",
        "filename": "../../paper.pdf",
    }

    resolved = document_path(item, tmp_path).resolve()

    assert resolved.is_relative_to(tmp_path.resolve())
    assert resolved.name == "paper.pdf"


def test_document_path_requires_filename() -> None:
    item = {
        "qualification": "a-level",
        "board": "aqa",
        "subject": "accounting",
        "qualification_slug": "accounting-7127",
        "kind": "question-papers",
        "filename": "..",
    }

    with pytest.raises(ValueError):
        document_path(item, Path("/tmp/corpus"))


def test_parse_ocr_resources_uses_a_level_tab_only() -> None:
    page = '''
    <div id="specification-tab-1">
      <a href="/Images/726711-question-paper-fundamentals.pdf">Question paper - Fundamentals</a>
      <a href="/Images/726832-mark-scheme-fundamentals.pdf">Mark scheme - Fundamentals</a>
      <a href="/Images/726713-question-paper-advance-notice.pdf">Question paper - Advance notice article</a>
    </div>
    <div id="specification-tab-2">
      <a href="/Images/111111-question-paper-as.pdf">Question paper - AS paper</a>
    </div>
    '''

    resources = parse_ocr_resources(
        page,
        page_url="https://www.ocr.org.uk/example/",
        subject="physics-b-advancing-physics",
        qualification_slug="physics-b-advancing-physics-h157-h557-from-2015",
    )

    assert [item["kind"] for item in resources] == [
        "question-papers",
        "mark-schemes",
        "inserts",
    ]
    assert all("111111" not in item["filename"] for item in resources)


def test_parse_ocr_specifications_keeps_a_level_not_as_level() -> None:
    page = """
    <a href="/Images/123-specification-a-level.pdf">Download A Level specification</a>
    <a href="/Images/456-specification-as-level.pdf">Download AS Level specification</a>
    """

    resources = parse_ocr_specifications(
        page,
        page_url="https://www.ocr.org.uk/example/",
        subject="economics",
        qualification_slug="economics-h060-h460-from-2019",
    )

    assert len(resources) == 1
    assert resources[0]["filename"] == "123-specification-a-level.pdf"


def test_parse_pearson_resource_keeps_public_question_paper() -> None:
    resource = parse_pearson_resource(
        {
            "objectID": "abc",
            "extension": "PDF",
            "gating": False,
            "title": "Question paper - Paper 1",
            "url": "/content/dam/pdf/A-Level/Economics/paper.pdf",
            "category": [
                "Pearson-UK:Qualification-Family/A-Level",
                "Pearson-UK:Document-Type/Question-paper",
            ],
        },
        page_url="https://qualifications.pearson.com/course.html",
        subject="economics-a-2015",
        qualification_slug="al15-economics-a",
    )

    assert resource is not None
    assert resource["kind"] == "question-papers"
    assert resource["url"].startswith("https://qualifications.pearson.com/")


def test_parse_pearson_resource_rejects_secure_and_quotes_public_paths() -> None:
    base = {
        "objectID": "abc",
        "extension": "PDF",
        "gating": False,
        "title": "Question paper",
        "category": ["Pearson-UK:Document-Type/Question-paper"],
    }

    secure = parse_pearson_resource(
        {**base, "url": "/content/dam/secure/silver/paper.pdf"},
        page_url="https://qualifications.pearson.com/course.html",
        subject="mathematics-2017",
        qualification_slug="maths-2017-as-al",
    )
    public = parse_pearson_resource(
        {**base, "url": "/content/dam/pdf/A Level/paper one.pdf"},
        page_url="https://qualifications.pearson.com/course.html",
        subject="mathematics-2017",
        qualification_slug="maths-2017-as-al",
    )

    assert secure is None
    assert public is not None
    assert "%20" in public["url"]


def test_download_manifest_records_failure_and_continues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        """{"documents":[
        {"id":"ok","board":"aqa","subject":"biology","url":"https://example/ok"},
        {"id":"denied","board":"aqa","subject":"biology","url":"https://example/denied"}
        ]}""",
        encoding="utf-8",
    )

    def fake_download(item, _root):
        if item["id"] == "denied":
            raise PermissionError("401")
        return True

    monkeypatch.setattr("tools.reference_corpus._download_one", fake_download)

    downloaded, existing, failures = download_manifest(manifest, tmp_path)

    assert (downloaded, existing) == (1, 0)
    assert failures == [
        {
            "id": "denied",
            "url": "https://example/denied",
            "error": "PermissionError: 401",
        }
    ]


def test_summarize_profiles_writes_derived_layout_only(tmp_path: Path) -> None:
    item = {
        "id": "paper",
        "qualification": "a-level",
        "board": "aqa",
        "subject": "biology",
        "qualification_slug": "biology-7402",
        "kind": "question-papers",
        "filename": "paper.pdf",
        "url": "https://example/paper.pdf",
    }
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        '{"documents":[' + json.dumps(item) + "]}",
        encoding="utf-8",
    )
    profile = document_path(item, tmp_path).with_suffix(".layout.json")
    profile.parent.mkdir(parents=True)
    profile.write_text(
        """{
          "pages": 24,
          "page_sizes": [{"width": 595.32, "height": 841.92, "count": 24}],
          "median_text_margins": {"left": 45, "top": 28, "right": 48, "bottom": 16},
          "fonts": [{"family": "ArialMT", "size": 11, "characters": 1000}],
          "stroke_widths": [{"width": 0.5, "count": 100}]
        }""",
        encoding="utf-8",
    )
    output = tmp_path / "summary.json"

    assert summarize_profiles(manifest, tmp_path, output) == 1
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["derived_data_only"] is True
    assert payload["profiles"][0]["page_count"]["median"] == 24
