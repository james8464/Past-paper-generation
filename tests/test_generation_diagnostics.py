from __future__ import annotations

import json
import stat
from argparse import Namespace

import pytest

from Backend.Core.generation import handle_generate
from Backend.Core.independent_solver import (
    CanonicalSolution,
    require_solution_matches_scheme,
)


def rejected_solution():
    solution = CanonicalSolution(
        item_id="graph-2",
        answer="A-B-F",
        steps=["Use the adjacency list."],
        response_slots=["route-in-order"],
        answer_slots={"route-in-order": "A-B-F"},
    )
    with pytest.raises(ValueError) as raised:
        require_solution_matches_scheme(
            solution, {"closed_answers": {"route-in-order": ["A-C-F"]}}
        )
    return raised.value


def test_failed_solution_survives_staging_cleanup(tmp_path, monkeypatch, capsys):
    error = rejected_solution()

    def crash(*args, **kwargs):
        raise RuntimeError("Generation rejected") from error

    monkeypatch.setattr("Backend.Core.generation._invoke_plugin", crash)
    request = Namespace(
        output=str(tmp_path),
        api_key="private-api-key",
        model="test-model",
        subject="economics",
        paper="1",
        provider="ollama",
        dry_run=False,
        seed=7,
    )
    assert handle_generate(request) == 1
    event = json.loads(capsys.readouterr().out.splitlines()[-1])
    from pathlib import Path

    path = Path(event["diagnostic_path"])
    record = json.loads(path.read_text())
    assert record["details"]["answer_slots"] == {"route-in-order": "A-B-F"}
    assert record["details"]["item_id"] == "graph-2"
    assert record["details"]["issues"]
    assert "private-api-key" not in path.read_text()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert list(tmp_path.iterdir()) == [path.parent]


def test_diagnostics_are_bounded_redacted_and_do_not_follow_symlinks(tmp_path):
    from Backend.Core.generation_diagnostics import (
        GenerationEvidenceError,
        save_failure_diagnostic,
    )

    error = GenerationEvidenceError(
        "not serialized", details={"answer": "secret" + "x" * 100_000}
    )
    for _ in range(23):
        path = save_failure_diagnostic(tmp_path, error, secrets=("secret",))
    assert path is not None
    assert path.stat().st_size < 32_768
    assert "secret" not in path.read_text()
    assert len(list(path.parent.glob("failure-*.json"))) == 20
    other = tmp_path / "other"
    other.mkdir()
    (other / ".papercreator-diagnostics").symlink_to(
        path.parent, target_is_directory=True
    )
    assert save_failure_diagnostic(other, error) is None


def test_reconciliation_evidence_does_not_retain_open_text():
    solution = CanonicalSolution(
        item_id="open",
        answer="private source text",
        steps=["private source text"],
        mark_points=["private source text"],
    )
    with pytest.raises(ValueError) as raised:
        require_solution_matches_scheme(solution, {})
    details = raised.value.details
    assert "private source text" not in json.dumps(details)
    assert len(details["answer_sha256"]) == 64


def test_tree_diagnostics_keep_only_finite_structural_values():
    from Backend.Core.independent_solver import solution_failure_evidence

    solution = CanonicalSolution(
        item_id="tree",
        answer="private explanation",
        answer_slots={
            "node-40-parent": "none",
            "node-40-side": "left",
            "node-20-parent": "40",
            "node-20-side": "private explanation",
        },
    )
    evidence = solution_failure_evidence(solution, [])
    assert evidence["answer_slots"] == {
        "node-40-parent": "none",
        "node-40-side": "left",
        "node-20-parent": "40",
    }
    assert "private explanation" not in json.dumps(evidence)


def test_exhausted_item_retries_preserve_original_evidence(monkeypatch):
    from Backend.Core.ai_assessment import GenerationPolicy, _generate_item_transaction
    from Backend.Core.generation_diagnostics import GenerationEvidenceError

    error = GenerationEvidenceError(
        "incomplete output", details={"kind": "provider_structure"}
    )

    class Client:
        provider = "ollama"

        def generate_json(self, prompt):
            raise error

    monkeypatch.setattr(
        "Backend.Core.ai_assessment._generation_prompt",
        lambda *args, **kwargs: "prompt",
    )
    with pytest.raises(RuntimeError) as raised:
        _generate_item_transaction(
            Namespace(question=Namespace(number="7")),
            client=Client(),
            subject="Economics",
            seed=7,
            policy=GenerationPolicy(attempts=2),
            progress=None,
            accepted_prompts=[],
        )
    assert raised.value.__cause__ is error
