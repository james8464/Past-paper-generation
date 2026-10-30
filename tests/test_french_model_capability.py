import io
import json
from copy import deepcopy

import pytest

from tools import french_model_capability as probe


def test_plan_counterbalances_modes_and_is_bounded():
    plan = probe.plan([270100, 270101], provider="ollama")
    assert [(job["seed"], job["thinking"]) for job in plan[::2]] == [
        (270100, False),
        (270100, True),
        (270101, True),
        (270101, False),
    ]
    assert len(plan) == 8
    assert {job["kind"] for job in plan} == {"authoring", "known_logic"}
    assert all(job["max_tokens"] <= 14000 for job in plan)
    assert all(not job["thinking"] for job in probe.plan([1], provider="apple"))
    with pytest.raises(ValueError):
        probe.plan([1, 2, 3], provider="ollama")


def test_known_answers_are_computed_and_schema_does_not_force_them():
    request, expected = probe.logic_request(270100)
    assert probe.check_logic(expected, expected)["passed"]
    wrong = deepcopy(expected)
    wrong["distance"] += 1
    assert not probe.check_logic(wrong, expected)["passed"]
    wrong["distance"] = True
    assert not probe.check_logic(wrong, expected)["passed"]
    assert "enum" not in json.dumps(request.schema)
    assert expected != probe.logic_request(270101)[1]


@pytest.mark.parametrize("thinking", [False, True])
def test_probe_transport_changes_only_thinking_and_explicit_output_budget(
    monkeypatch, thinking
):
    request, expected = probe.logic_request(270100)
    seen = []

    def transport(url, body, headers, **kwargs):
        seen.append(json.loads(body))
        return io.BytesIO(
            json.dumps(
                {
                    "done": True,
                    "done_reason": "stop",
                    "eval_count": 45,
                    "message": {
                        "thinking": "raisonnement privé",
                        "content": json.dumps(expected),
                    },
                }
            ).encode()
        )

    monkeypatch.setattr(probe, "urllib_request", transport)
    client = probe.ProbeClient(
        provider="ollama", model="fixture", thinking=thinking, max_tokens=2048
    )
    assert client.generate_request(request) == expected
    assert len(seen) == 1
    assert seen[0]["think"] is thinking
    assert seen[0]["options"]["num_predict"] == 2048
    assert seen[0]["options"]["num_ctx"] == 16384
    assert seen[0]["format"] == request.schema
    assert client.calls[0]["thinking_token_count"] is None
    assert client.calls[0]["total_generated_tokens"] == 45
    assert client.calls[0]["thinking_characters"] > 0


def test_truncated_completion_is_preserved_and_not_repaired(monkeypatch):
    calls = []

    def transport(*args, **kwargs):
        calls.append(1)
        return io.BytesIO(
            b'{"done":true,"done_reason":"length","message":{"thinking":"long", "content":"{"}}'
        )

    monkeypatch.setattr(probe, "urllib_request", transport)
    client = probe.ProbeClient(
        provider="ollama", model="fixture", thinking=True, max_tokens=2048
    )
    with pytest.raises(ValueError):
        client.generate_request(probe.logic_request(1)[0])
    assert len(calls) == 1 and len(client.calls) == 1


def test_plan_only_cli_never_resolves_a_model_or_creates_output(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(
        probe, "_model_digest", lambda *args: pytest.fail("plan queried model")
    )
    output = tmp_path / "private"
    assert probe.main(["--model", "fixture", "--output", str(output)]) == 0
    assert not output.exists()
    assert "capability_only" in capsys.readouterr().out


def test_existing_evidence_directory_is_preserved(tmp_path, monkeypatch):
    marker = tmp_path / "previous.txt"
    marker.write_text("retained")
    monkeypatch.setattr(probe, "_model_digest", lambda *args: "a" * 64)
    with pytest.raises(FileExistsError):
        probe.run_plan(
            model="fixture",
            expected_digest="a" * 64,
            provider="ollama",
            output=tmp_path,
            seeds=[1],
            ollama_url="http://localhost:11434",
            timeout=600,
        )
    assert marker.read_text() == "retained"
