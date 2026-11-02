"""Offline public-entrypoint checks: preview status is presentation, not content."""

import hashlib
import json
import subprocess
import sys
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

import pymupdf as fitz
import pytest

from Backend.Core.generation import _invoke_plugin
from Backend.Core.generator_registry import generator_capabilities, generator_capability


def _export(subject: str, paper: str, output: Path) -> dict[str, Path]:
    args = Namespace(
        subject=subject,
        paper=paper,
        seed=123,
        model="unused-offline",
        ollama_url="http://invalid.invalid",
        dry_run=True,
        notes=None,
        provider="ollama",
        api_key="",
    )
    return _invoke_plugin(
        generator_capability(subject),
        args,
        output,
        checkpoint_path=output / "unused-checkpoint.json",
    )


def test_real_accounting_preview_exports_disclose_status(tmp_path: Path) -> None:
    paths = _export("accounting_aqa", "2", tmp_path)
    for path in paths.values():
        if path.suffix == ".pdf":
            with fitz.open(path) as document:
                text = document[0].get_text()
                assert "LAYOUT PREVIEW" in text
                assert "Unreviewed sample content" in text


PUBLIC_CASES = [
    (subject, paper)
    for subject, capability in generator_capabilities().items()
    for paper in capability.papers
]


@pytest.mark.parametrize(("subject", "paper"), PUBLIC_CASES)
def test_every_public_preview_pdf_preserves_body_geometry(
    subject: str,
    paper: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from Backend.Core import family_adapter
    from Backend.Core.preview_presentation import (
        preview_presentation,
        validate_preview_pdf,
    )

    paths = _export(subject, paper, tmp_path / "preview")
    # Render the identical blueprint through the former/default presentation.
    # No authoring or review is bypassed: both calls remain offline previews.
    with monkeypatch.context() as patch:
        patch.setattr(
            family_adapter,
            "preview_presentation",
            lambda _enabled: preview_presentation(False),
        )
        patch.setattr(family_adapter, "validate_preview_pdf", lambda _path: {})
        plain = _export(subject, paper, tmp_path / "plain")
    assert paths.keys() == plain.keys()
    for role, path in paths.items():
        if path.suffix != ".pdf":
            assert path.read_bytes() == plain[role].read_bytes()
            continue
        report = validate_preview_pdf(path)
        assert report["policy"] == "uk-layout-preview-v1"
        with fitz.open(path) as preview, fitz.open(plain[role]) as default:
            assert len(preview) == len(default)
            first = preview[0]
            assert first.get_text().count("LAYOUT PREVIEW") == 1
            assert "unofficial" in first.get_text().lower()
            # Every unchanged first-page word retains its exact position, too.
            before = default[0].get_text("words")
            for word in before:
                if word[:5] in [value[:5] for value in first.get_text("words")]:
                    continue
                # Only the original branding/subtitle line may be replaced.
                assert any(
                    abs(word[1] - rect.y0) < 25
                    for rect in first.search_for("LAYOUT PREVIEW")
                ), word
            # Changed cover furniture cannot reflow, move or remove body work.
            for index in range(1, len(preview)):
                assert preview[index].rect == default[index].rect
                assert preview[index].get_text("words") == default[index].get_text(
                    "words"
                )
                assert (
                    preview[index].get_pixmap().samples
                    == default[index].get_pixmap().samples
                )


def test_preview_context_is_nested_and_reset_after_errors() -> None:
    from Backend.Core.preview_presentation import preview_copy, preview_presentation

    assert preview_copy("original") == "original"
    with pytest.raises(RuntimeError), preview_presentation(True):
        assert "LAYOUT PREVIEW" in preview_copy("original")
        with preview_presentation(False):
            assert preview_copy("original") == "original"
        assert "LAYOUT PREVIEW" in preview_copy("original")
        raise RuntimeError("renderer failed")
    assert preview_copy("original") == "original"


@pytest.mark.parametrize("dry_run", [True, False])
def test_adapter_scopes_supporting_artifacts_and_restores_outer_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    dry_run: bool,
) -> None:
    from Backend.Core import family_adapter
    from Backend.Core.family_contracts import FamilyAdapter
    from Backend.Core.preview_presentation import preview_copy, preview_presentation

    def fail_support(*_args: object) -> dict:
        assert ("LAYOUT PREVIEW" in preview_copy("original")) == dry_run
        raise RuntimeError("support renderer failed")

    adapter = FamilyAdapter(
        id="test",
        subject_label="test",
        backend_subject="test",
        load_message="",
        build_message="",
        prompt_version="test",
        load_syllabus=lambda _: SimpleNamespace(topics=[], topic_ids=set()),
        load_rule=lambda _: None,
        build=lambda *_: {},
        artifacts=lambda *_: (),
        stem=lambda *_: "test",
        supporting_artifacts=fail_support,
    )
    monkeypatch.setattr(family_adapter, "profile_for", lambda *_: None)
    monkeypatch.setattr(
        family_adapter, "generate_unique_paper", lambda assessment, **_: assessment
    )
    with preview_presentation(not dry_run):
        with pytest.raises(RuntimeError, match="support renderer failed"):
            family_adapter.run_family_adapter(
                adapter,
                paper="1",
                syllabus_path=tmp_path / "unused",
                output_dir=tmp_path,
                seed=123,
                dry_run=dry_run,
                client=object(),
            )
        assert ("LAYOUT PREVIEW" in preview_copy("original")) == (not dry_run)
    assert preview_copy("original") == "original"


@pytest.mark.parametrize(
    "kind", ["missing", "invisible", "white", "small", "clipped", "duplicate"]
)
def test_invalid_notices_fail_closed(tmp_path: Path, kind: str) -> None:
    from Backend.Core.preview_presentation import PREVIEW_NOTICE, validate_preview_pdf

    path = tmp_path / "invalid.pdf"
    with fitz.open() as document:
        page = document.new_page()
        if kind != "missing":
            page.insert_text(
                (500 if kind == "clipped" else 40, 80),
                PREVIEW_NOTICE,
                fontsize=5 if kind == "small" else 10,
                render_mode=3 if kind == "invisible" else 0,
                color=(1, 1, 1) if kind == "white" else (0, 0, 0),
            )
        if kind == "duplicate":
            page.insert_text((40, 120), PREVIEW_NOTICE, fontsize=10)
        document.save(path)
    before = path.read_bytes()
    with pytest.raises(ValueError, match="layout-preview notice"):
        validate_preview_pdf(path)
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "background", ["earlier_opaque", "later_transparent", "later_opaque"]
)
@pytest.mark.parametrize("prefix", ["", "A-level Economics · "])
@pytest.mark.parametrize("covered", ["full", "PREVIEW", "sample content", "Y"])
def test_notice_visibility_respects_artwork_draw_order(
    tmp_path: Path,
    background: str,
    prefix: str,
    covered: str,
) -> None:
    from Backend.Core.preview_presentation import PREVIEW_NOTICE, validate_preview_pdf

    path = tmp_path / f"{background}.pdf"
    with fitz.open() as document:
        page = document.new_page()
        if background == "earlier_opaque":
            page.draw_rect(fitz.Rect(35, 60, 450, 90), fill=(1, 1, 1), color=None)
        page.insert_text((40, 80), prefix + PREVIEW_NOTICE, fontsize=10)
        bounds = page.search_for(PREVIEW_NOTICE if covered == "full" else covered)[0]
        if background.startswith("later_"):
            page.draw_rect(
                bounds + fitz.Rect(-2, -2, 2, 2),
                fill=(1, 1, 1),
                color=None,
                fill_opacity=1 if background == "later_opaque" else 0.2,
                overlay=True,
            )
        document.save(path)
    before = path.read_bytes()
    with fitz.open(path) as document:
        crop = document[0].get_pixmap(clip=bounds, colorspace=fitz.csRGB).samples
    if background == "later_opaque":
        assert all(value == 255 for value in crop)
        with pytest.raises(ValueError, match="layout-preview notice"):
            validate_preview_pdf(path)
    else:
        assert any(value < 255 for value in crop)
        assert validate_preview_pdf(path)["first_page_notice"] is True
    assert path.read_bytes() == before


def test_missing_notice_preserves_existing_pdf_and_resets_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from Backend.Core.preview_presentation import preview_copy

    capability = generator_capability("accounting_aqa")
    # Load the ordinary entrypoint before replacing its renderer with a broken one.
    _export("accounting_aqa", "2", tmp_path)
    import aqaaccountgen.cli as cli

    path = tmp_path / "aqa-accounting-paper-2-question-paper.pdf"
    original = path.read_bytes()

    def missing_notice(output: Path, *_args: object) -> None:
        with fitz.open() as document:
            document.new_page().insert_text((40, 80), "Unlabelled sample")
            document.save(output)

    monkeypatch.setattr(
        cli, "render_question_paper", lambda _paper, path: missing_notice(path)
    )
    with pytest.raises(ValueError, match="layout-preview notice"):
        _export(capability.backend_subject, "2", tmp_path)
    assert path.read_bytes() == original
    assert not list(tmp_path.glob(".*.tmp"))
    assert preview_copy("original") == "original"


def test_public_publication_records_preview_policy_and_final_hashes(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            str(root / "bridge.py"),
            "generate",
            "--subject",
            "accounting_aqa",
            "--paper",
            "2",
            "--dry-run",
            "--seed",
            "123",
            "--output",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    manifest = json.loads(next(tmp_path.glob("*-package.json")).read_text())
    for item in manifest["outputs"].values():
        path = tmp_path / item["filename"]
        assert item["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        if path.suffix == ".pdf":
            assert item["pdf_validation"]["presentation"] == {
                "policy": "uk-layout-preview-v1",
                "first_page_notice": True,
            }


def test_support_pdf_notice_is_checked_before_atomic_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from Backend.Core.preview_presentation import preview_presentation

    paths = _export("computer_science", "1", tmp_path)
    from cspapergen import paper1_assets

    old_bytes = paths["preliminary_material"].read_bytes()
    header = paper1_assets._practice_header

    def unmarked_header(*args: object) -> None:
        with preview_presentation(False):
            header(*args)

    monkeypatch.setattr(paper1_assets, "_practice_header", unmarked_header)
    with pytest.raises(ValueError, match="layout-preview notice"):
        _export("computer_science", "1", tmp_path)
    assert paths["preliminary_material"].read_bytes() == old_bytes
    assert not list(tmp_path.glob(".*.tmp"))


def test_post_conformance_notice_loss_cannot_be_published(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from Backend.Core import generation

    stage = tmp_path / "stage"
    paths = _export("accounting_aqa", "2", stage)
    output = tmp_path / "public"
    output.mkdir()
    old_pdf = output / paths["question_paper"].name
    old_bytes = paths["question_paper"].read_bytes()
    old_pdf.write_bytes(old_bytes)

    def lose_notice(*_args: object) -> dict:
        with fitz.open(paths["mark_scheme"]) as document:
            for rect in document[0].search_for("LAYOUT PREVIEW"):
                document[0].add_redact_annot(rect)
            document[0].apply_redactions()
            document.saveIncr()
        return {}

    monkeypatch.setattr(generation, "conform_generated_documents", lose_notice)
    with pytest.raises(ValueError, match="layout-preview notice"):
        generation.finalize_generated_documents(
            args=Namespace(subject="accounting_aqa", paper="2", dry_run=True),
            capability=generator_capability("accounting_aqa"),
            staging_dir=stage,
            output_dir=output,
            paths=paths,
        )
    assert old_pdf.read_bytes() == old_bytes
    assert list(output.iterdir()) == [old_pdf]
    assert not list(stage.glob("*-package.json"))
