"""Offline grid/export contracts; isolated form audit is not qualification."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from aqaaccountgen.cli import ADAPTER
from aqaaccountgen.configs import load_rule
from aqaaccountgen.generator import build_paper
from aqaaccountgen.marking_policy import printed_level_rows
from aqaaccountgen.scheme_policy import question_rows
from aqaaccountgen.syllabus import load_syllabus

from Backend.Core import assessment_package as packages
from Backend.Core.assessment_checkpoints import (
    AssessmentCheckpointStore,
    CheckpointMismatch,
    identity_for_blueprint,
)
from Backend.Core.assessment_contracts import contract_for_question
from Backend.Core.level_of_response import scale_level_policy

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def papers(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Grid contract tests must not use network or subprocesses")

    monkeypatch.setattr("socket.create_connection", forbidden)
    monkeypatch.setattr("subprocess.run", forbidden)
    syllabus = load_syllabus(
        ROOT / "Resources/accounting/aqa/generator/data/syllabus.json"
    )
    return {
        paper: build_paper(load_rule(paper), syllabus, seed=123) for paper in ("1", "2")
    }


def questions(paper):
    return [
        question
        for section in paper.sections
        for option in section.options
        for question in option.questions
    ]


@pytest.mark.parametrize("paper_number", ["1", "2"])
def test_public_export_matches_existing_printed_grids(
    papers, paper_number, tmp_path, monkeypatch
):
    paper = papers[paper_number]
    # This test establishes export/grid identity, not whole-form qualification.
    monkeypatch.setattr(packages, "_reference_demand_audit", lambda **kwargs: None)
    path = tmp_path / "assessment.json"
    packages.write_assessment_package(
        paper,
        path,
        subject="accounting_aqa",
        paper_number=paper_number,
        preview=True,
        provider=None,
        model=None,
    )
    exported = json.loads(path.read_text())
    for question, item in zip(questions(paper), exported["items"], strict=True):
        if question.scheme_mode != "levels" or question.rule_id == "explain_trade":
            continue
        policy_id = f"aqa-accounting-{question.marks}-mark"
        assert item["assessment_contract"]["level_policy_id"] == policy_id
        assert contract_for_question(question).level_policy_id == policy_id
        scaled = scale_level_policy(
            packages._level_policies()[policy_id], question.marks
        )
        expected = [
            str(level.minimum_mark)
            if level.minimum_mark == level.maximum_mark
            else f"{level.minimum_mark}-{level.maximum_mark}"
            for level in reversed(scaled.levels)
        ]
        printed = (
            [row[1].replace("–", "-") for row in question_rows(question)[1]]
            if paper_number == "2"
            else [row[1].replace("–", "-") for row in printed_level_rows(question)]
        )
        assert printed == expected
        assert packages._validate_response_bands(item)["monotonic"] is True


@pytest.mark.parametrize("contract_location", ["context", "typed"])
def test_typed_contract_rejects_legacy_generic_policy(papers, contract_location):
    question = next(q for q in questions(papers["2"]) if q.marks == 25)
    if contract_location == "typed":
        question.contract = contract_for_question(question).model_copy(
            update={"level_policy_id": "aqa-standard-4-level"}
        )
    else:
        question.authoring_context["level_policy_id"] = "aqa-standard-4-level"
    with pytest.raises(ValueError, match=r"Accounting.*level"):
        contract_for_question(question)


def test_public_export_rejects_legacy_generic_policy(papers, tmp_path, monkeypatch):
    monkeypatch.setattr(packages, "_reference_demand_audit", lambda **kwargs: None)
    paper = papers["2"]
    next(q for q in questions(paper) if q.marks == 25).authoring_context[
        "level_policy_id"
    ] = "aqa-standard-4-level"
    with pytest.raises(ValueError, match=r"Accounting.*level"):
        packages.write_assessment_package(
            paper,
            tmp_path / "stale.json",
            subject="accounting_aqa",
            paper_number="2",
            preview=True,
            provider=None,
            model=None,
        )


def test_replay_rejects_legacy_generic_policy(papers):
    raw = papers["2"].model_dump(mode="json")
    item = next(
        item
        for item in packages._extract_items(
            raw, subject="accounting_aqa", paper_number="2"
        )
        if item["marks"] == 25
    )
    item["assessment_contract"]["level_policy_id"] = "aqa-standard-4-level"
    with pytest.raises(ValueError, match=r"Accounting.*level"):
        packages._validate_response_bands(item)


def test_checkpoint_identity_changes_with_policy_binding(papers, tmp_path):
    paper = papers["2"]
    current = identity_for_blueprint(
        paper, provider="ollama", model="fixture", prompt_version=ADAPTER.prompt_version
    )
    legacy = paper.model_copy(deep=True)
    for question in questions(legacy):
        if question.scheme_mode == "levels":
            question.authoring_context["level_policy_id"] = "aqa-standard-4-level"
    old = identity_for_blueprint(
        legacy,
        provider="ollama",
        model="fixture",
        prompt_version="ai-assessment-v13-accounting-paper2-human-scheme",
    )
    assert current != old
    assert ADAPTER.prompt_version != "ai-assessment-v13-accounting-paper2-human-scheme"
    path = tmp_path / "checkpoint.json"
    AssessmentCheckpointStore(path, old).save_payload("retained", {"existing": "data"})
    before = path.read_bytes()
    with pytest.raises(CheckpointMismatch):
        AssessmentCheckpointStore(path, current)
    assert path.read_bytes() == before


def test_public_replay_refuses_stale_policy_without_rewriting_saved_package(
    papers, tmp_path, monkeypatch
):
    monkeypatch.setattr(packages, "_reference_demand_audit", lambda **kwargs: None)
    path = tmp_path / "legacy.json"
    packages.write_assessment_package(
        papers["2"],
        path,
        subject="accounting_aqa",
        paper_number="2",
        preview=True,
        provider=None,
        model=None,
    )
    document = json.loads(path.read_text())
    for section in document["blueprint"]["sections"]:
        for option in section["options"]:
            for question in option["questions"]:
                if question["scheme_mode"] == "levels":
                    question["authoring_context"]["level_policy_id"] = (
                        "aqa-standard-4-level"
                    )
    for item in document["items"]:
        if item["scheme_mode"] == "levels":
            item["assessment_contract"]["level_policy_id"] = "aqa-standard-4-level"
    path.write_text(json.dumps(document))
    before = path.read_bytes()
    with pytest.raises(ValueError, match=r"Accounting.*level"):
        packages.validate_assessment_package(
            path,
            subject="accounting_aqa",
            paper_number="2",
            preview=True,
            provider=None,
            model=None,
        )
    assert path.read_bytes() == before


@pytest.mark.parametrize("paper_number", ["1", "2"])
def test_typed_contract_rejects_grid_mutation_even_with_current_id(
    papers, paper_number
):
    question = next(q for q in questions(papers[paper_number]) if q.marks == 25)
    question.mark_scheme = [
        text.replace("21–25", "20–25") for text in question.mark_scheme
    ]
    with pytest.raises(ValueError, match="Accounting printed level grid"):
        contract_for_question(question)


def test_grouped_explain_trade_remains_separate(papers):
    question = next(q for q in questions(papers["1"]) if q.rule_id == "explain_trade")
    assert (
        contract_for_question(question).level_policy_id
        == "aqa-accounting-two-reasons-v1"
    )
    assert [row[1] for row in printed_level_rows(question)] == ["3", "2", "1", "0"]
    assert [
        point.marks for point in question.structured_mark_scheme if point.marks
    ] == [3, 3]


def test_unrelated_subject_keeps_generic_policy():
    from types import SimpleNamespace

    from Backend.Core.exam_blueprints import GeneratedQuestion
    from Backend.Core.mark_scheme_enrichment import _enrich_question

    question = GeneratedQuestion(
        rule_id="unrelated",
        number="1",
        marks=25,
        kind="extended_response",
        command_word="Assess",
        topic_id="topic",
        prompt="Assess this subject.",
        mark_scheme=["Indicative route."],
    )
    question = _enrich_question(
        question, SimpleNamespace(title="Subject", points=["Point"]), "business"
    )
    assert question.authoring_context["level_policy_id"] == "aqa-standard-4-level"


@pytest.mark.parametrize("marker", ["grouped", "explicit_without_group"])
@pytest.mark.parametrize("boundary", ["export", "replay"])
def test_forged_grouped_marker_cannot_waive_standalone_contract(
    papers, tmp_path, monkeypatch, marker, boundary
):
    monkeypatch.setattr(packages, "_reference_demand_audit", lambda **kwargs: None)
    paper = papers["2"]
    question = next(q for q in questions(paper) if q.marks == 25)
    if marker == "grouped":
        question.authoring_context["grouped_level_policy"] = {}
    else:
        question.authoring_context["accounting_marking_policy"] = (
            "aqa-accounting-explicit-credit-v1"
        )
    if boundary == "export":
        with pytest.raises(ValueError, match="grouped level policy"):
            packages.write_assessment_package(
                paper,
                tmp_path / "forged.json",
                subject="accounting_aqa",
                paper_number="2",
                preview=True,
                provider=None,
                model=None,
            )
    else:
        raw = question.model_dump(mode="json")
        raw.update(subject="accounting_aqa", paper="2", id=question.number)
        raw["assessment_contract"] = packages._assessment_contract(raw)
        with pytest.raises(ValueError, match="grouped level policy"):
            packages._validate_response_bands(raw)
