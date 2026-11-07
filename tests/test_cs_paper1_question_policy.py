"""Public CS1 pagination accepts complete content, never a page-count waiver."""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pymupdf
import pytest
from cspapergen.generator import build_paper1_blueprint
from cspapergen.render_pdf import render_question_paper
from cspapergen.syllabus import load_syllabus

from Backend.Core import layout_conformance
from Backend.Core.assessment_package import _extract_items, write_assessment_package
from Backend.Core.layout_master import LayoutConformanceError

POLICY = "generated-aqa-cs-paper1-question-content-v1"
REGISTRY = Path("Resources/layout-master-runtime.json")


@pytest.fixture(scope="module")
def original(tmp_path_factory):
    folder = tmp_path_factory.mktemp("cs1-policy")
    blueprint, _context = build_paper1_blueprint(load_syllabus(), seed=270100)
    paths = {
        "question_paper": folder / "questions.pdf",
        "assessment_package": folder / "assessment.json",
    }
    render_question_paper(blueprint, paths["question_paper"])
    write_assessment_package(
        blueprint,
        paths["assessment_package"],
        subject="computer_science",
        paper_number="1",
        preview=True,
        provider=None,
        model=None,
    )
    return paths


@pytest.fixture
def paths(original, tmp_path):
    result = {}
    for role, source in original.items():
        target = tmp_path / source.name
        shutil.copy2(source, target)
        result[role] = target
    return result


def test_public_policy_preserves_measured_reference_and_complete_content(paths):
    master = json.loads(REGISTRY.read_text())["papers"]["computer_science:1"]
    assert master["question-paper"]["page_count"] == 24
    assert master["question-paper"]["page_count_policy"] == {"kind": POLICY}
    report = layout_conformance.conform_generated_documents(
        "computer_science", "1", paths
    )
    assert report["question_paper"]["policy"] == POLICY
    assert report["question_paper"]["checked_questions"] == 12
    assert report["question_paper"]["checked_marks"] == 100
    assert report["question_paper"]["blank_padding_pages"] == 0


@pytest.mark.parametrize(
    "mutation",
    [
        "subject",
        "paper",
        "delivery",
        "items",
        "duplicate-items",
        "question",
        "part",
        "code",
        "missing",
    ],
)
def test_public_policy_rejects_package_misidentity_or_items(paths, mutation):
    path = paths["assessment_package"]
    package = json.loads(path.read_text())
    if mutation == "subject":
        package["subject"] = "computer_science_ocr"
    elif mutation == "paper":
        package["paper"] = "2"
    elif mutation == "delivery":
        package["blueprint"]["delivery_mode"] = "written"
    elif mutation == "items":
        package["items"] = package["items"][:-1]
    elif mutation == "duplicate-items":
        package["items"].append(copy.deepcopy(package["items"][0]))
    elif mutation == "missing":
        paths.pop("assessment_package")
    else:
        if mutation == "question":
            package["blueprint"]["questions"][-1]["number"] = 13
        elif mutation == "part":
            package["blueprint"]["questions"][0]["parts"][1]["label"] = "1"
        else:
            package["blueprint"]["paper_code"] = "7517/2"
        package["items"] = _extract_items(
            package["blueprint"], subject="computer_science", paper_number="1"
        )
    path.write_text(json.dumps(package))
    with pytest.raises(LayoutConformanceError):
        layout_conformance.conform_generated_documents("computer_science", "1", paths)


@pytest.mark.parametrize(
    "mutation",
    [
        "prompt",
        "code",
        "table",
        "mark",
        "duplicate",
        "blank",
        "duplicate-prompt",
        "unowned-page",
        "fsm",
        "bounds",
        "a4",
    ],
)
def test_public_policy_rejects_missing_printed_content_or_padding(paths, mutation):
    package = json.loads(paths["assessment_package"].read_text())
    questions = package["blueprint"]["questions"]
    pdf = paths["question_paper"]
    with pymupdf.open(pdf) as document:
        if mutation == "blank":
            document.new_page(width=595.32, height=841.92)
        elif mutation == "unowned-page":
            page = document.new_page(pno=len(document) - 1, width=595.32, height=841.92)
            page.insert_text((118, 200), "Unowned padding: no candidate task.")
        elif mutation == "a4":
            document[1].set_mediabox(pymupdf.Rect(0, 0, 600, 850))
        elif mutation == "bounds":
            document[1].insert_text((560, 200), "EDGE")
        elif mutation == "fsm":
            removed = False
            for page in document:
                for drawing in page.get_drawings():
                    rect = drawing["rect"]
                    if abs(rect.width - 44) < 0.1 and abs(rect.height - 44) < 0.1:
                        page.add_redact_annot(rect, fill=(1, 1, 1))
                        page.apply_redactions(graphics=2)
                        removed = True
                        break
                if removed:
                    break
            assert removed
        elif mutation == "duplicate-prompt":
            prompt = questions[0]["parts"][0]["prompt"]
            for page in document:
                if page.search_for(prompt):
                    page.insert_text((118, 730), prompt, fontsize=7)
                    break
        elif mutation == "duplicate":
            with pymupdf.open(stream=document.tobytes(), filetype="pdf") as clone:
                document.insert_pdf(clone, from_page=1, to_page=1)
        else:
            target = {
                "prompt": questions[0]["parts"][0]["prompt"],
                "code": questions[2]["stimulus"]["code"].splitlines()[0],
                "table": questions[5]["stimulus"]["headers"][0],
                "mark": "[1 mark]",
            }[mutation]
            found = False
            for page in document:
                rectangles = page.search_for(target)
                if rectangles:
                    for rectangle in rectangles:
                        page.add_redact_annot(rectangle, fill=(1, 1, 1))
                    page.apply_redactions()
                    found = True
                    break
            assert found, target
        document.saveIncr()
    with pytest.raises(LayoutConformanceError):
        layout_conformance.conform_generated_documents("computer_science", "1", paths)


@pytest.mark.parametrize("mutation", ["unknown", "family", "role", "paper", "subject"])
def test_public_content_kind_fails_closed_outside_its_scope(
    paths, tmp_path, monkeypatch, mutation
):
    registry = copy.deepcopy(json.loads(REGISTRY.read_text()))
    record = registry["papers"]["computer_science:1"]
    payload = {"kind": POLICY}
    if mutation == "unknown":
        payload = {"kind": POLICY + "-unknown", "minimum": 1, "maximum": 128}
    if mutation == "family":
        record["family"] = "ocr-computer-science"
    subject, paper = "computer_science", "1"
    if mutation in {"paper", "subject"}:
        subject, paper = (
            ("computer_science", "2")
            if mutation == "paper"
            else ("computer_science_ocr", "1")
        )
        record = registry["papers"][f"{subject}:{paper}"]
    role = "mark-scheme" if mutation == "role" else "question-paper"
    record[role]["page_count_policy"] = payload
    if mutation == "role":
        paths = {
            "mark_scheme": paths["question_paper"],
            "assessment_package": paths["assessment_package"],
        }
    override = tmp_path / "registry.json"
    override.write_text(json.dumps(registry))
    monkeypatch.setattr(layout_conformance, "REGISTRY_PATH", override)
    with pytest.raises(LayoutConformanceError):
        layout_conformance.conform_generated_documents(subject, paper, paths)


def test_owned_builder_refresh_changes_only_cs1_question_policy(tmp_path, monkeypatch):
    from tools import build_supported_layout_masters as builder

    current = json.loads(REGISTRY.read_text())
    old = copy.deepcopy(current)
    old["papers"]["computer_science:1"]["question-paper"]["page_count_policy"] = {
        "kind": "exact",
        "minimum": 24,
        "maximum": 24,
    }
    target = tmp_path / "runtime.json"
    target.write_text(json.dumps(old))
    monkeypatch.setattr(builder, "RUNTIME_OUTPUT", target)
    builder.refresh_question_policies()
    assert json.loads(target.read_text()) == current
    assert current["papers"]["computer_science:1"]["question-paper"]["page_count"] == 24


@pytest.mark.parametrize("role", ["question_paper", "assessment_package"])
def test_existing_resource_caps_precede_pdf_or_package_parse(paths, monkeypatch, role):
    from Backend.Core import computer_science_question_content as content

    path = paths[role]
    cap = (
        content._MAX_PDF_BYTES
        if role == "question_paper"
        else content._MAX_PACKAGE_BYTES
    )
    with path.open("wb") as stream:
        stream.truncate(cap + 1)
    if role == "question_paper":
        monkeypatch.setattr(
            content.pymupdf,
            "open",
            lambda *_args, **_kwargs: pytest.fail("oversized PDF parsed"),
        )
    else:
        original_read = Path.read_text

        def read_text(candidate, *args, **kwargs):
            if candidate == path:
                pytest.fail("oversized package parsed")
            return original_read(candidate, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", read_text)
    with pytest.raises(LayoutConformanceError):
        content.verify_cs_paper1_questions(
            paths["question_paper"], paths["assessment_package"], 24
        )


def test_public_policy_uses_canonical_pack_syllabus_not_module_default(
    paths, monkeypatch, tmp_path
):
    from cspapergen import syllabus

    missing = tmp_path / "_internal" / "data" / "syllabus_seed.json"
    monkeypatch.setattr(syllabus, "DEFAULT_SYLLABUS_PATH", missing)
    report = layout_conformance.conform_generated_documents(
        "computer_science", "1", paths
    )
    assert report["question_paper"]["checked_questions"] == 12
    assert report["question_paper"]["checked_marks"] == 100


def test_public_policy_refuses_missing_canonical_pack_syllabus(
    paths, monkeypatch, tmp_path
):
    from cspapergen import syllabus

    from Backend.Core import computer_science_question_content as content

    # The ordinary source module default remains valid: it must not be a fallback.
    assert syllabus.DEFAULT_SYLLABUS_PATH.is_file()
    monkeypatch.setattr(content, "CS_ROOT", tmp_path / "missing-pack", raising=False)
    with pytest.raises(LayoutConformanceError, match=r"syllabus_seed\.json"):
        layout_conformance.conform_generated_documents("computer_science", "1", paths)
