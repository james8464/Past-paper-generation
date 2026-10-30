"""DeepSeek receives a system JSON contract without changing requested content."""

import json

import pytest

from Backend.Core.generation_diagnostics import GenerationEvidenceError
from Backend.Core.generation_requests import GenerationRequest
from tests.test_deepseek_provider import KEY, SCHEMA, client, mock_transport, response


@pytest.mark.parametrize("operation", ["review", "solver", "french_nsi_authoring"])
def test_plain_user_prompt_receives_exact_typed_schema_in_system_instructions(
    monkeypatch, operation
):
    calls = mock_transport(monkeypatch, response())
    prompt = "Donne la réponse demandée."
    request = GenerationRequest(prompt, operation, SCHEMA, output_budget=8192)
    assert client().generate_request(request) == {"answer": 42}
    assert len(calls) == 1
    _, payload, _, options = calls[0]
    instructions = payload["instructions"]
    assert "one valid JSON object" in instructions
    assert "trailing commas" in instructions
    assert "comments" in instructions
    assert "outer" in instructions
    assert "Preserve the language" in instructions
    assert json.loads(instructions.split("\nOUTPUT_SCHEMA=\n", 1)[1]) == request.schema
    assert payload["text"]["format"] == {
        "type": "json_schema",
        "name": "keldin_generation",
        "schema": request.schema,
    }
    assert payload["input"] == prompt
    assert payload["max_output_tokens"] == 8192
    assert payload["reasoning"]["effort"] == (
        "low" if operation == "french_nsi_authoring" else "high"
    )
    assert options["attempts"] == 1
    assert KEY not in instructions + payload["input"]


def test_requested_python_fences_and_french_markup_remain_allowed_inside_json_strings(
    monkeypatch,
):
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["code", "note"],
        "properties": {"code": {"type": "string"}, "note": {"type": "string"}},
    }
    expected = {
        "code": '```python\ndef saluer():\n    return "Bonjour"\n```',
        "note": "**Réponse** en français.",
    }
    envelope = response()
    envelope["output"][1]["content"][0]["text"] = json.dumps(
        expected, ensure_ascii=False
    )
    calls = mock_transport(monkeypatch, envelope)
    request = GenerationRequest(
        "Fournis le code et la note en français.",
        "french_nsi_authoring",
        schema,
        output_budget=8192,
    )
    assert client().generate_request(request) == expected
    instructions = calls[0][1]["instructions"]
    assert "inside JSON string values are allowed" in instructions
    assert "escape" in instructions
    assert json.loads(instructions.split("\nOUTPUT_SCHEMA=\n", 1)[1]) == schema
    assert len(calls) == 1


@pytest.mark.parametrize(
    "invalid",
    ['{"answer":42,}', '{"answer":42 // note\n}', '```json\n{"answer":42}\n```'],
)
def test_explicit_instructions_never_repair_or_retry_invalid_final_json(
    monkeypatch, invalid
):
    envelope = response()
    envelope["output"][1]["content"][0]["text"] = invalid
    calls = mock_transport(monkeypatch, envelope)
    request = GenerationRequest(
        "Donne le résultat.", "french_nsi_authoring", SCHEMA, output_budget=8192
    )
    with pytest.raises(GenerationEvidenceError):
        client().generate_request(request)
    assert len(calls) == 1
