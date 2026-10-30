"""Prompt compaction removes JSON whitespace, never reference or schema data."""

import json

from Backend.Core.france import llm_pipeline as subject


def test_author_json_is_compact_and_losslessly_recovers_full_source_and_schema():
    refs = [
        {
            "source_id": "exact-source",
            "text": "  Première ligne\n    indentation conservée.  ",
        }
    ]
    request = subject.exercise_request("1", 42, refs, primary_topic="algorithmique")
    data, schema = request.prompt.split("DONNÉES_JSON\n", 1)[1].split(
        "\nOUTPUT_SCHEMA=", 1
    )
    assert json.loads(data)["references"] == refs
    assert json.loads(data)["curriculum"] == {
        key: list(value) for key, value in subject.CURRICULUM_OBJECTIVES.items()
    }
    assert json.loads(schema) == request.schema
    for text in (data, schema):
        assert text == json.dumps(
            json.loads(text), ensure_ascii=False, separators=(",", ":")
        )
    assert request.output_budget == 8192
