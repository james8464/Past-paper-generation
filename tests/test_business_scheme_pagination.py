from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pymupdf as fitz
import pytest
from aqabizgen.cli import generate_package
from aqabizgen.render_pdf import render_mark_scheme

from Backend.Core.assessment_package import _extract_items
from Backend.Core.business_scheme_content import (
    BUSINESS_SCHEME_DATE,
    BUSINESS_SCHEME_MARKER,
    BUSINESS_SCHEME_PAGINATION,
    verify_business_paper_two_scheme,
)
from Backend.Core.exam_blueprints import GeneratedPaper
from Backend.Core.generation_date import generation_date
from Backend.Core.layout_conformance import (
    conform_generated_documents,
    runtime_page_count_policy,
)
from Backend.Core.layout_master import LayoutConformanceError
from Backend.Core.preview_presentation import preview_presentation

SYLLABUS = Path("Resources/business/aqa/generator/data/syllabus.json")


@pytest.fixture(scope="module")
def original(tmp_path_factory):
    return generate_package(
        paper="2",
        output_dir=tmp_path_factory.mktemp("business-policy"),
        seed=123,
        syllabus_path=SYLLABUS,
        dry_run=True,
    )


@pytest.fixture
def paths(original, tmp_path):
    result = {}
    for role, source in original.items():
        target = tmp_path / source.name
        shutil.copy2(source, target)
        result[role] = target
    return result


def _rewrite_package(paths, mutate, *, refresh_items=False):
    path = paths["assessment_package"]
    package = json.loads(path.read_text())
    mutate(package)
    if refresh_items:
        package["items"] = _extract_items(
            package["blueprint"], subject="business_aqa", paper_number="2"
        )
    path.write_text(json.dumps(package))
    return package


def test_business_public_policy_preserves_reference_and_all_printed_credit(paths):
    package = json.loads(paths["assessment_package"].read_text())
    dates = {
        q["authoring_context"][BUSINESS_SCHEME_DATE]
        for s in package["blueprint"]["sections"]
        for o in s["options"]
        for q in o["questions"]
    }
    assert dates == {generation_date().isoformat()}
    result = conform_generated_documents("business_aqa", "2", paths)["mark_scheme"]
    assert result["policy"] == BUSINESS_SCHEME_PAGINATION
    assert result["reference_page_count"] == 20
    assert result["actual_page_count"] == 19
    assert result["checked_parts"] == 11
    assert result["complete_printed_credit"]
    assert result["blank_padding_pages"] == 0


def test_business_retained_marked_cover_date_does_not_follow_later_environment(
    paths, monkeypatch
):
    package = json.loads(paths["assessment_package"].read_text())
    recorded = package["blueprint"]["sections"][0]["options"][0]["questions"][0][
        "authoring_context"
    ][BUSINESS_SCHEME_DATE]
    monkeypatch.setenv("KELDIN_GENERATED_ON", "2040-02-03")
    assert recorded != "2040-02-03"
    assert verify_business_paper_two_scheme(
        paths["mark_scheme"], paths["assessment_package"], 20
    )["complete_printed_credit"]


def test_business_cover_date_metadata_does_not_change_story_rng_or_credit(monkeypatch):
    from aqabizgen.configs import load_rule
    from aqabizgen.generator import build_paper
    from aqabizgen.syllabus import load_syllabus

    syllabus = load_syllabus(SYLLABUS)
    blueprints = []
    for generated_on in ("2026-11-07", "2040-02-03"):
        monkeypatch.setenv("KELDIN_GENERATED_ON", generated_on)
        blueprint = build_paper(load_rule("2"), syllabus, 20).model_dump(mode="json")
        for section in blueprint["sections"]:
            for option in section["options"]:
                for question in option["questions"]:
                    context = question["authoring_context"]
                    assert context[BUSINESS_SCHEME_MARKER] == BUSINESS_SCHEME_PAGINATION
                    assert context.pop(BUSINESS_SCHEME_DATE) == generated_on
        # Normalize only the asserted date field. Every pre-existing source,
        # prompt, random value and marking statement must remain identical.
        blueprints.append(blueprint)
    assert blueprints[0] == blueprints[1]


@pytest.mark.parametrize("seed", [20, 83])
def test_business_content_policy_also_verifies_bounded_other_seed_cases(tmp_path, seed):
    paths = generate_package(
        paper="2", output_dir=tmp_path, seed=seed, syllabus_path=SYLLABUS, dry_run=True
    )
    result = verify_business_paper_two_scheme(
        paths["mark_scheme"], paths["assessment_package"], 20
    )
    assert result["complete_printed_credit"]
    assert result["checked_parts"] == 11


@pytest.mark.parametrize(
    "mutation", ["missing", "malformed", "inconsistent", "compact-iso"]
)
def test_business_cover_date_is_complete_consistent_canonical_iso(paths, mutation):
    def mutate(package):
        question = package["blueprint"]["sections"][0]["options"][0]["questions"][0]
        context = question["authoring_context"]
        if mutation == "missing":
            del context[BUSINESS_SCHEME_DATE]
        elif mutation in {"malformed", "compact-iso"}:
            for section in package["blueprint"]["sections"]:
                for option in section["options"]:
                    for item in option["questions"]:
                        item["authoring_context"][BUSINESS_SCHEME_DATE] = (
                            "not-a-date" if mutation == "malformed" else "20261107"
                        )
        else:
            context[BUSINESS_SCHEME_DATE] = "2040-02-03"

    _rewrite_package(paths, mutate, refresh_items=True)
    with pytest.raises(LayoutConformanceError, match="generated-on"):
        verify_business_paper_two_scheme(
            paths["mark_scheme"], paths["assessment_package"], 20
        )


@pytest.mark.parametrize(
    "mutation", ["missing-credit", "duplicate-page", "blank-page", "wrong-mode"]
)
def test_business_policy_rejects_invalid_printed_bodies(paths, mutation):
    path = paths["mark_scheme"]
    if mutation == "wrong-mode":
        _rewrite_package(paths, lambda package: package.update(preview=False))
    else:
        with fitz.open(path) as document:
            if mutation == "missing-credit":
                rectangle = document[4].search_for("Award method credit")[0]
                document[4].add_redact_annot(rectangle)
                document[4].apply_redactions()
            elif mutation == "duplicate-page":
                document.fullcopy_page(4, 5)
            else:
                document.new_page(pno=5, width=595.32, height=841.92)
            document.saveIncr()
    with pytest.raises(LayoutConformanceError):
        verify_business_paper_two_scheme(path, paths["assessment_package"], 20)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing-item",
        "duplicate-item",
        "forged-number",
        "numeric-source",
        "chart-source",
        "unknown-marker",
        "partial-marker",
        "wrong-package",
        "budget",
    ],
)
def test_business_policy_rejects_invalid_package(paths, mutation):
    def mutate(package):
        question = package["blueprint"]["sections"][0]["options"][0]["questions"][0]
        if mutation == "missing-item":
            package["items"].pop()
        elif mutation == "duplicate-item":
            package["items"].append(package["items"][0])
        elif mutation == "forged-number":
            question["number"] = "99.1"
        elif mutation == "numeric-source":
            question["authoring_context"]["calculation_variables"]["start"] += 1
        elif mutation == "chart-source":
            package["blueprint"]["sections"][0]["options"][0]["chart_values"][0] += 1
        elif mutation == "unknown-marker":
            question["authoring_context"][BUSINESS_SCHEME_MARKER] = "future-version"
        elif mutation == "partial-marker":
            del question["authoring_context"][BUSINESS_SCHEME_MARKER]
        elif mutation == "wrong-package":
            package["paper"] = "1"
        else:
            question["prompt"] = "x" * 100_001

    _rewrite_package(
        paths, mutate, refresh_items=mutation not in {"missing-item", "duplicate-item"}
    )
    with pytest.raises(LayoutConformanceError):
        verify_business_paper_two_scheme(
            paths["mark_scheme"], paths["assessment_package"], 20
        )


def test_business_policy_independent_credit_check_catches_shared_renderer_omission(
    paths, monkeypatch
):
    import aqabizgen.render_pdf as renderer

    original_block = renderer._scheme_block

    def omit_method(question):
        if question.number == "01.1":
            question = question.model_copy(
                update={"mark_scheme": question.mark_scheme[1:]}
            )
        return original_block(question)

    monkeypatch.setattr(renderer, "_scheme_block", omit_method)
    package = json.loads(paths["assessment_package"].read_text())
    with preview_presentation(True):
        renderer.render_mark_scheme(
            GeneratedPaper.model_validate(package["blueprint"]), paths["mark_scheme"]
        )
    with pytest.raises(LayoutConformanceError, match=r"credit for 01\.1"):
        verify_business_paper_two_scheme(
            paths["mark_scheme"], paths["assessment_package"], 20
        )


@pytest.mark.parametrize("mutation", ["wrong-owner", "duplicate-credit"])
def test_business_independent_projection_rejects_shared_renderer_extra_credit(
    paths, monkeypatch, mutation
):
    import aqabizgen.render_pdf as renderer

    original_block = renderer._scheme_block
    package = json.loads(paths["assessment_package"].read_text())
    paper = GeneratedPaper.model_validate(package["blueprint"])
    moved = paper.sections[0].options[0].questions[0].mark_scheme[-1]

    def corrupt(question):
        points = list(question.mark_scheme)
        if mutation == "duplicate-credit" and question.number == "01.1":
            points.append(points[-1])
        elif mutation == "wrong-owner" and question.number == "01.1":
            points.pop()
        elif mutation == "wrong-owner" and question.number == "01.2":
            points.append(moved)
        return original_block(question.model_copy(update={"mark_scheme": points}))

    monkeypatch.setattr(renderer, "_scheme_block", corrupt)
    with preview_presentation(True):
        renderer.render_mark_scheme(paper, paths["mark_scheme"])
    with pytest.raises(LayoutConformanceError, match=r"credit for 01\.1"):
        verify_business_paper_two_scheme(
            paths["mark_scheme"], paths["assessment_package"], 20
        )


@pytest.mark.parametrize("preview,enlarged_table", [(False, False), (True, True)])
def test_business_content_policy_preserves_mode_and_content_driven_size(
    paths, monkeypatch, preview, enlarged_table
):
    import aqabizgen.render_pdf as renderer
    from reportlab.lib.styles import ParagraphStyle

    package = _rewrite_package(paths, lambda package: package.update(preview=preview))
    if enlarged_table:
        # A bounded renderer-layout fixture, not a new public large-print mode.
        style = ParagraphStyle(
            "expanded-credit-fixture",
            parent=renderer.STYLES["scheme_small"],
            fontSize=11,
            leading=13,
        )
        monkeypatch.setitem(renderer.STYLES, "scheme_small", style)
    with preview_presentation(preview):
        renderer.render_mark_scheme(
            GeneratedPaper.model_validate(package["blueprint"]), paths["mark_scheme"]
        )
    result = verify_business_paper_two_scheme(
        paths["mark_scheme"], paths["assessment_package"], 20
    )
    assert result["complete_printed_credit"]
    if enlarged_table:
        assert result["actual_page_count"] > 19


def test_business_policy_canonical_render_failure_propagates(paths, monkeypatch):
    seen = {}

    def fail(_paper, path):
        seen["directory"] = path.parent
        raise RuntimeError("owned renderer failed")

    monkeypatch.setattr("aqabizgen.render_pdf.render_mark_scheme", fail)
    with pytest.raises(RuntimeError, match="owned renderer failed"):
        verify_business_paper_two_scheme(
            paths["mark_scheme"], paths["assessment_package"], 20
        )
    assert not seen["directory"].exists()


def test_business_policy_preserves_published_non_numeric_credit_not_seed_answers(paths):
    def author(package):
        question = package["blueprint"]["sections"][0]["options"][0]["questions"][1]
        old = question["mark_scheme"][0]
        text = "01.1 supplies the context; a developed chain connects this business decision to customer demand."
        question["mark_scheme"][0] = text
        for point in question["structured_mark_scheme"]:
            if point["text"] == old:
                point["text"] = text

    package = _rewrite_package(paths, author, refresh_items=True)
    with preview_presentation(True):
        render_mark_scheme(
            GeneratedPaper.model_validate(package["blueprint"]), paths["mark_scheme"]
        )
    assert verify_business_paper_two_scheme(
        paths["mark_scheme"], paths["assessment_package"], 20
    )["complete_printed_credit"]


def test_business_historical_unmarked_policy_retains_exact_twenty_pages(paths):
    def body_fingerprints(path):
        with fitz.open(path) as document:
            result = []
            for page in document:
                body = fitz.Rect(
                    0,
                    25 * 72 / 25.4,
                    page.rect.width,
                    page.rect.height - 18 * 72 / 25.4,
                )
                if page.get_text(clip=body).strip():
                    raster = page.get_pixmap(
                        clip=body, dpi=72, colorspace=fitz.csGRAY, alpha=False
                    )
                    result.append(hashlib.sha256(raster.samples).digest())
            return result

    current_bodies = body_fingerprints(paths["mark_scheme"])

    def unmark(package):
        for section in package["blueprint"]["sections"]:
            for option in section["options"]:
                for question in option["questions"]:
                    del question["authoring_context"][BUSINESS_SCHEME_MARKER]

    package = _rewrite_package(paths, unmark, refresh_items=True)
    assert (
        verify_business_paper_two_scheme(
            paths["mark_scheme"], paths["assessment_package"], 20
        )
        is None
    )
    with pytest.raises(LayoutConformanceError, match="19 pages; expected 20"):
        conform_generated_documents("business_aqa", "2", paths)
    with preview_presentation(True):
        render_mark_scheme(
            GeneratedPaper.model_validate(package["blueprint"]), paths["mark_scheme"]
        )
    with fitz.open(paths["mark_scheme"]) as document:
        assert len(document) == 20
    assert body_fingerprints(paths["mark_scheme"]) == current_bodies
    assert "mark_scheme" not in conform_generated_documents("business_aqa", "2", paths)


@pytest.mark.parametrize(
    "subject,paper,role",
    [
        ("business_aqa", "1", "mark_scheme"),
        ("economics", "2", "mark_scheme"),
        ("business_aqa", "2", "question_paper"),
    ],
)
def test_business_policy_cannot_be_misrouted(
    paths, monkeypatch, tmp_path, subject, paper, role
):
    import Backend.Core.layout_conformance as conformance

    registry = {
        "papers": {
            f"{subject}:{paper}": {
                "family": "aqa-business",
                role.replace("_", "-"): {
                    "page_count": 20,
                    "page_count_policy": {"kind": BUSINESS_SCHEME_PAGINATION},
                },
            }
        }
    }
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps(registry))
    monkeypatch.setattr(conformance, "REGISTRY_PATH", registry_path)
    with pytest.raises(LayoutConformanceError, match="cannot apply"):
        conform_generated_documents(subject, paper, paths)


def test_business_policy_requires_package_and_only_selects_paper_two_scheme(paths):
    with pytest.raises(LayoutConformanceError, match="assessment package"):
        verify_business_paper_two_scheme(paths["mark_scheme"], None, 20)
    assert runtime_page_count_policy("aqa-business", "mark-scheme", 20, paper="2") == {
        "kind": BUSINESS_SCHEME_PAGINATION
    }
    for paper in ("1", "3"):
        assert (
            runtime_page_count_policy("aqa-business", "mark-scheme", 20, paper=paper)[
                "kind"
            ]
            == "exact"
        )
    assert (
        runtime_page_count_policy("aqa-business", "question-paper", 24, paper="2")[
            "kind"
        ]
        == "exact"
    )
