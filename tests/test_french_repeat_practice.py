from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from Backend.Core.cli import build_parser
from Backend.Core.france import runtime
from Backend.Core.france.expanded_pipeline import VERSION, FamilyCatalogueExhausted
from tests.test_nsi_pipeline import make_index

POLICY = "repeat-practice-v1"


@pytest.fixture
def practice_runtime(tmp_path, monkeypatch):
    index = tmp_path / "references.sqlite"
    make_index(index)
    calls = []
    generate = runtime.generate_assessment

    def capture(**kwargs):
        calls.append(kwargs)
        return generate(**kwargs)

    def render(path, _renderer, *, role, **_kwargs):
        path.write_bytes(f"retained fake PDF: {role}".encode())

    monkeypatch.setattr(runtime, "generate_assessment", capture)
    monkeypatch.setattr(runtime, "render_pdf_atomically", render)
    monkeypatch.setattr(runtime, "validate_pdf", lambda _path: None)
    monkeypatch.setattr(
        "Backend.Core.france.whole_case_pdf.validate_whole_case_pdf",
        lambda *_args, **_kwargs: None,
    )
    args = Namespace(
        assessment="fr-bac-general-nsi-written-2027",
        reference_index=index,
        output=str(tmp_path / "output"),
        seed=270100,
        model="unused",
        provider="application-owned",
        ollama_url="http://localhost:11434",
        allow_remote=False,
        large_print=False,
        exclude_family=[],
        repeat_practice=True,
    )
    return args, calls


def test_cli_requires_explicit_repeat_practice_flag(tmp_path):
    command = [
        "generate-assessment",
        "--assessment",
        "fr-bac-general-nsi-written-2027",
        "--reference-index",
        str(tmp_path / "references.sqlite"),
        "--seed",
        "270100",
    ]
    assert build_parser().parse_args(command).repeat_practice is False
    assert (
        build_parser().parse_args([*command, "--repeat-practice"]).repeat_practice
        is True
    )


def test_repeat_practice_prefers_unused_then_repeats_without_clearing_history(
    practice_runtime,
):
    args, calls = practice_runtime
    output = Path(args.output)
    saved = []
    retained = {}
    for index in range(7):
        existing = {
            path: path.read_bytes() for path in output.rglob("*") if path.is_file()
        }
        args.seed = 270100 + 5 * index
        args.exclude_family = saved.copy()
        assert runtime.handle_generate_assessment(args) == 0
        assert all(path.read_bytes() == content for path, content in existing.items())
        manifest = next(
            path for path in output.glob("nsi-*/manifest.json") if path not in retained
        )
        record = json.loads(manifest.read_text())
        family = record["identity"]["family"]
        assert family == (index if index < 5 else 0)
        if family not in saved:
            saved.append(family)
        assert record["practice_policy"] == POLICY
        assert record["cross_history_comparison"] == "not_performed"
        assert record["teacher_review"] == "not_run"
        assert record["empirical_calibration"] == "not_run"
        package = json.loads((manifest.parent / "assessment.json").read_text())
        runtime.validate_package(package)
        assert package["identity"] == record["identity"]
        assert record["identity"]["seed"] == calls[-1]["seed"]
        assert str(record["identity"]["seed"]) in manifest.parent.name
        assert calls[-1]["previous_texts"] == []
        assert POLICY in calls[-1]["checkpoint"].name
        assert VERSION in calls[-1]["checkpoint"].name
        retained[manifest] = manifest.read_bytes()
        assert all(path.read_bytes() == content for path, content in retained.items())
    assert len(list(output.glob("nsi-*"))) == 7
    assert runtime.load_originality_history(output)


def test_strict_default_still_refuses_all_used_families(practice_runtime):
    args, calls = practice_runtime
    del args.repeat_practice
    args.exclude_family = list(range(5))
    assert runtime.handle_generate_assessment(args) == 1
    assert not calls
    assert not list(Path(args.output).glob("nsi-*"))


def test_repeat_and_strict_checkpoint_names_cannot_alias(practice_runtime):
    args, calls = practice_runtime
    args.repeat_practice = False
    assert runtime.handle_generate_assessment(args) == 0
    strict = calls[-1]["checkpoint"]
    assert POLICY not in strict.name
    manifest = next(Path(args.output).glob("nsi-*/manifest.json"))
    assert "practice_policy" not in json.loads(manifest.read_text())
    before = strict.read_bytes()
    args.repeat_practice = True
    args.output = str(Path(args.output).parent / "repeat-output")
    assert runtime.handle_generate_assessment(args) == 0
    assert calls[-1]["checkpoint"].name != strict.name
    assert strict.read_bytes() == before


@pytest.mark.parametrize(
    "failure", [ValueError("invalid family"), RuntimeError("source")]
)
def test_repeat_mode_does_not_swallow_other_selection_failures(
    practice_runtime, monkeypatch, failure
):
    args, calls = practice_runtime

    def refuse(*_args, **_kwargs):
        raise failure

    monkeypatch.setattr(runtime, "choose_fresh_seed", refuse)
    assert runtime.handle_generate_assessment(args) == 1
    assert not calls


def test_repeat_mode_keeps_reference_and_current_package_validation(
    practice_runtime, monkeypatch
):
    args, calls = practice_runtime

    def reject(_package):
        raise ValueError("current-paper validation refused")

    monkeypatch.setattr(runtime, "validate_package", reject)
    assert runtime.handle_generate_assessment(args) == 1
    assert len(calls) == 1
    assert not list(Path(args.output).glob("nsi-*"))
    args.reference_index = args.reference_index.parent / "missing.sqlite"
    assert runtime.handle_generate_assessment(args) == 1
    assert len(calls) == 1


@pytest.mark.parametrize("mutation", ["answer", "mark", "duplicate-question"])
def test_repeat_mode_rejects_real_current_paper_contract_mutation(
    practice_runtime, monkeypatch, mutation
):
    args, calls = practice_runtime
    generate = runtime.generate_assessment

    def changed(**kwargs):
        package = generate(**kwargs)
        questions = package["exercises"][0]["questions"]
        if mutation == "answer":
            questions[0]["answer"] += " Incorrect changed answer."
        elif mutation == "mark":
            questions[0]["points"] = "99"
        else:
            questions[1] = questions[0].copy()
        return package

    monkeypatch.setattr(runtime, "generate_assessment", changed)
    assert runtime.handle_generate_assessment(args) == 1
    assert len(calls) == 1
    assert not list(Path(args.output).glob("nsi-*"))


def test_repeat_mode_rejects_ineligible_reference_index(practice_runtime):
    args, calls = practice_runtime
    # An empty but valid SQLite index must not become eligible merely because
    # cross-history comparison is omitted.
    from Backend.Core.scoped_references import ReferenceIndex

    args.reference_index = args.reference_index.parent / "empty.sqlite"
    with ReferenceIndex(args.reference_index):
        pass
    assert runtime.handle_generate_assessment(args) == 1
    assert len(calls) == 1
    assert not list(Path(args.output).glob("nsi-*"))


@pytest.mark.parametrize("exclusions", [[True], [5], "0"])
def test_repeat_mode_refuses_invalid_saved_exclusions(practice_runtime, exclusions):
    args, calls = practice_runtime
    args.exclude_family = exclusions
    assert runtime.handle_generate_assessment(args) == 1
    assert not calls


def test_repeat_mode_refuses_historical_model_route_before_model_access(
    practice_runtime, monkeypatch
):
    args, calls = practice_runtime
    args.provider = "ollama"
    monkeypatch.setattr(
        runtime, "model_identity", lambda *_args: pytest.fail("must not access model")
    )
    assert runtime.handle_generate_assessment(args) == 1
    assert not calls


def test_only_catalogue_exhaustion_allows_requested_seed_reuse(
    practice_runtime, monkeypatch
):
    args, calls = practice_runtime

    def exhausted(*_args, **_kwargs):
        raise FamilyCatalogueExhausted("all used")

    monkeypatch.setattr(runtime, "choose_fresh_seed", exhausted)
    assert runtime.handle_generate_assessment(args) == 0
    assert calls[-1]["seed"] == args.seed
    assert calls[-1]["previous_texts"] == []


def test_repeating_identical_explicit_seed_keeps_existing_destination_and_files(
    practice_runtime,
):
    args, calls = practice_runtime
    assert runtime.handle_generate_assessment(args) == 0
    output = Path(args.output)
    before = {path: path.read_bytes() for path in output.rglob("*") if path.is_file()}
    args.exclude_family = list(range(5))
    assert runtime.handle_generate_assessment(args) == 1
    assert calls[-1]["seed"] == args.seed
    assert {
        path: path.read_bytes() for path in output.rglob("*") if path.is_file()
    } == before
    assert len(list(output.glob("nsi-*"))) == 1
