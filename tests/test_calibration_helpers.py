from __future__ import annotations

import hashlib
import importlib
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

TOOLS = [
    "aqa_accounting_calibration",
    "aqa_business_calibration",
    "ocr_economics_calibration",
    "ocr_computer_science_calibration",
    "difficulty_calibration",
]


@pytest.mark.parametrize("name", TOOLS)
def test_existing_named_fingerprints_and_json_bytes_are_preserved(name, tmp_path):
    module = importlib.import_module(f"tools.{name}")
    paths = [tmp_path / "évidence.pdf", tmp_path / "second.pdf"]
    for path, content in zip(paths, [b"first\x00", b"second\n"], strict=True):
        path.write_bytes(content)
    digest = hashlib.sha256()
    for path in reversed(paths):
        digest.update(path.name.encode())
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    assert module._fingerprint(list(reversed(paths))) == digest.hexdigest()
    assert module._fingerprint([]) == hashlib.sha256().hexdigest()
    assert module.render_json({"é": [1, 2]}) == '{\n  "é": [\n    1,\n    2\n  ]\n}\n'


@pytest.mark.parametrize("name", TOOLS[:-1])
def test_existing_band_and_sequence_inventory_semantics_are_preserved(name):
    module = importlib.import_module(f"tools.{name}")
    assert module._band([4, 1]) == {"minimum": 1, "median": 2.5, "maximum": 4}
    assert type(module._band([3])["median"]) is int
    with pytest.raises(ValueError):
        module._band([])
    inventory = getattr(
        module, "_inventory", getattr(module, "_sequence_inventory", None)
    )
    assert inventory([[3, 1], [], [2], [3, 1]]) == [
        {"sequence": [], "documents": 1},
        {"sequence": [2], "documents": 1},
        {"sequence": [3, 1], "documents": 2},
    ]
    assert inventory([]) == []


def _paper():
    return {
        "seed": 1,
        "sections": [
            {
                "id": "A",
                "options": [
                    {
                        "title": "Unprinted planning title",
                        "stimulus": [],
                        "questions": [
                            {
                                "number": "1",
                                "marks": 5,
                                "kind": "calculation",
                                "prompt": "Prepare the account from the supplied figures.",
                                "choices": [],
                                "authoring_context": {
                                    "source_data": {"receipts": 100, "credit": 20},
                                    "verified_answers": [999],
                                    "accounting_source_content": [{"text": "PRIVATE"}],
                                },
                            }
                        ],
                    }
                ],
            }
        ],
    }


def test_assessed_content_identity_ignores_seed_and_private_credit_but_binds_public_inputs():
    common = importlib.import_module("tools.calibration_common")
    paper = _paper()
    same = deepcopy(paper)
    same["seed"] = 100
    context = same["sections"][0]["options"][0]["questions"][0]["authoring_context"]
    context["verified_answers"] = [12345]
    context["accounting_source_content"] = [{"text": "DIFFERENT PRIVATE CREDIT"}]
    assert common.paper_content_fingerprint(paper) == common.paper_content_fingerprint(
        same
    )
    assert common.paper_content_fingerprint(
        paper, source_only=True
    ) == common.paper_content_fingerprint(same, source_only=True)
    context["source_data"]["credit"] = 21
    assert common.paper_content_fingerprint(paper) != common.paper_content_fingerprint(
        same
    )
    assert common.paper_content_fingerprint(
        paper, source_only=True
    ) != common.paper_content_fingerprint(same, source_only=True)


def test_public_projection_keeps_only_source_used_by_the_item():
    common = importlib.import_module("tools.calibration_common")
    paper = _paper()
    other = deepcopy(paper)
    option = other["sections"][0]["options"][0]
    option["title"] = "DIFFERENT UNPRINTED PLAN"
    option["stimulus"] = ["Unprinted planning profit is 999999."]
    assert common.paper_content_fingerprint(paper) == common.paper_content_fingerprint(
        other
    )
    assert "PRIVATE" not in str(common.public_candidate_content(paper))


def test_private_accounting_working_does_not_add_public_variety():
    from tools.calibration_common import paper_content_fingerprint

    original = _paper()
    changed = deepcopy(original)
    context = changed["sections"][0]["options"][0]["questions"][0]["authoring_context"]
    context["required_entries"] = {"debit": "PRIVATE SOLVED PLACEMENT"}
    context["calculation_variables"] = {"derived_answer": 12345}
    assert paper_content_fingerprint(original) == paper_content_fingerprint(changed)


@pytest.mark.parametrize(
    "field,value",
    [
        ("inputs", {"curve": "D", "direction": "right"}),
        ("rows", [{"label": "Factory", "output": 100, "employees": 5}]),
    ],
)
def test_selected_response_visible_tables_and_diagrams_bind_scoped_identity(
    field, value
):
    from tools.calibration_common import paper_content_fingerprint

    original = _paper()
    changed = deepcopy(original)
    context = changed["sections"][0]["options"][0]["questions"][0]["authoring_context"]
    context["selected_response_contract"] = {field: value, "correct_choice": "PRIVATE"}
    assert paper_content_fingerprint(original) != paper_content_fingerprint(changed)
    same = deepcopy(changed)
    same["sections"][0]["options"][0]["questions"][0]["authoring_context"][
        "selected_response_contract"
    ]["correct_choice"] = "OTHER PRIVATE"
    assert paper_content_fingerprint(changed) == paper_content_fingerprint(same)


def test_nested_public_seed_is_data_not_run_identity():
    from tools.calibration_common import paper_content_fingerprint

    original = _paper()
    changed = deepcopy(original)
    changed["sections"][0]["options"][0]["questions"][0]["authoring_context"][
        "source_data"
    ]["seed"] = 12
    assert paper_content_fingerprint(original) != paper_content_fingerprint(changed)


def test_shared_source_changes_and_choice_changes_are_identity_bearing():
    common = importlib.import_module("tools.calibration_common")
    paper = _paper()
    option = paper["sections"][0]["options"][0]
    question = option["questions"][0]
    question["authoring_context"] = {}
    question["prompt"] = "Use the information in Extract 1 to select the answer."
    question["kind"] = "multiple_choice"
    question["choices"] = ["A", "B", "C", "D"]
    option["stimulus"] = ["Extract 1 reports revenue of 100."]
    changed = deepcopy(paper)
    changed["sections"][0]["options"][0]["stimulus"] = [
        "Extract 1 reports revenue of 101."
    ]
    assert common.paper_content_fingerprint(paper) != common.paper_content_fingerprint(
        changed
    )
    changed = deepcopy(paper)
    changed["sections"][0]["options"][0]["questions"][0]["choices"][0] = "Different"
    assert common.paper_content_fingerprint(paper) != common.paper_content_fingerprint(
        changed
    )


@pytest.mark.parametrize("name", TOOLS)
def test_new_reports_use_versioned_output_and_never_replace_legacy(
    name, tmp_path, monkeypatch
):
    module = importlib.import_module(f"tools.{name}")
    legacy = tmp_path / "difficulty-calibration.json"
    legacy.write_bytes(b"retained historical PASS\n")
    current = tmp_path / "difficulty-calibration-v2.json"
    monkeypatch.setattr(module, "OUTPUT", legacy)
    monkeypatch.setattr(module, "REPORT_OUTPUT_V2", current, raising=False)
    monkeypatch.setattr(
        module,
        "build_report",
        lambda *_args: {
            "schema_version": 2,
            "calibration_policy": "public-candidate-content-v2",
        },
    )
    assert module.main(["--write"]) == 0
    assert current.is_file()
    assert legacy.read_bytes() == b"retained historical PASS\n"
    current.unlink()
    with pytest.raises(SystemExit, match=r"v2|version 2"):
        module.main(["--check"])


def test_accounting_uses_owned_public_cases_and_typed_mcq_demand(monkeypatch):
    from aqaaccountgen import render_pdf

    from tools import aqa_accounting_calibration as module

    monkeypatch.setattr(render_pdf, "render_question_paper", lambda *_args: None)
    monkeypatch.setattr(render_pdf, "render_mark_scheme", lambda *_args: None)
    monkeypatch.setattr(module, "_pages", lambda *_args: 36)
    monkeypatch.setattr(module, "_text", lambda *_args: "Test preview")
    reference = {
        "papers": {
            paper: {
                "current_printed_mark_sequence": [],
                "page_count": {"minimum": 1, "maximum": 100},
            }
            for paper in ("1", "2")
        }
    }
    profile = module.build_generated_profile(reference, seeds=range(100, 102))
    first = profile["papers"]["1"]
    assert first["unique_public_source_fingerprints"] == 2
    assert first["checks"]["unique_public_source_batch"] is True
    assert first["mcq_demand"] == {"declared_transform": 4, "other_or_unspecified": 6}
    assert first["checks"]["declared_mcq_operation_mix"] is True


@pytest.mark.parametrize("name", TOOLS)
def test_missing_v2_check_refuses_before_loading_or_regenerating_old_evidence(
    name, tmp_path, monkeypatch
):
    module = importlib.import_module(f"tools.{name}")
    monkeypatch.setattr(
        module, "REPORT_OUTPUT_V2", tmp_path / "difficulty-calibration-v2.json"
    )

    def unexpected(*_args):
        raise AssertionError("Missing v2 should not trigger corpus or generation work")

    monkeypatch.setattr(module, "build_report", unexpected)
    with pytest.raises(SystemExit, match="missing"):
        module.main(["--check"])


@pytest.mark.parametrize("name", TOOLS)
def test_each_tool_rejects_seed_only_changes_as_content_variety(name, monkeypatch):
    module = importlib.import_module(f"tools.{name}")
    package = {
        "aqa_accounting_calibration": "aqaaccountgen",
        "aqa_business_calibration": "aqabizgen",
        "ocr_economics_calibration": "ocregen",
        "ocr_computer_science_calibration": "ocrcsgen",
        "difficulty_calibration": "aqaecongen",
    }[name]
    generator = importlib.import_module(f"{package}.generator")
    rendering = importlib.import_module(f"{package}.render_pdf")
    original = generator.build_paper

    def same_content(rule, syllabus, seed):
        return original(rule, syllabus, 100).model_copy(update={"seed": seed})

    monkeypatch.setattr(generator, "build_paper", same_content)
    for attribute in (
        "render_question_paper",
        "render_mark_scheme",
        "render_source_booklet",
    ):
        if hasattr(rendering, attribute):
            monkeypatch.setattr(rendering, attribute, lambda *_args: None)
    for attribute in ("_pages", "_page_count"):
        monkeypatch.setattr(module, attribute, lambda *_args: 36, raising=False)
    for attribute in ("_text", "_pdf_text"):
        monkeypatch.setattr(
            module, attribute, lambda *_args: "Test preview", raising=False
        )
    band = {"minimum": 0, "maximum": 1000}
    reference = {
        "papers": {
            paper: {
                "current_printed_mark_sequence": [],
                "printed_mark_sequence": [],
                "page_count": band,
                "source_insert": {
                    "page_count": band,
                    "word_count": band,
                    "document_word_count": band,
                },
            }
            for paper in ("1", "2", "3")
        }
    }
    report = module.build_generated_profile(reference, seeds=range(100, 102))
    for paper in report["papers"].values():
        assert paper["unique_candidate_content_fingerprints"] == 1
        assert paper["checks"]["unique_candidate_content_batch"] is False


@pytest.mark.parametrize("name", TOOLS)
@pytest.mark.parametrize("entry", ["script", "module"])
def test_calibration_cli_help_supports_both_entry_modes_without_environment_paths(
    name, entry
):
    root = Path(__file__).resolve().parents[1]
    command = [sys.executable]
    command += (
        [str(root / "tools" / f"{name}.py")]
        if entry == "script"
        else ["-m", f"tools.{name}"]
    )
    result = subprocess.run(
        [*command, "--help"],
        cwd=root,
        env={**os.environ, "PYTHONPATH": ""},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert "--check" in result.stdout
