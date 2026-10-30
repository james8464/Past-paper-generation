"""Generation schemas describe credit syntax and existing table-cell limits."""

import json

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from Backend.Core.france.llm_pipeline import exercise_request
from Backend.Core.france.nsi import NSIExercise, authoring_schema
from tests.test_french_llm_pipeline import raw_exercise


def constrained_schema():
    return authoring_schema(machine_field_constraints=True)


@pytest.mark.parametrize("location", ["credit", "question", "exercise"])
@pytest.mark.parametrize(
    "value", ["0,5", "0,25", "+0.5", "-1", "1e2", "NaN", 0.5, "1234567", "0.12345"]
)
def test_authoring_schema_rejects_invalid_machine_credit(location, value):
    schema = constrained_schema()
    field = {
        "credit": schema["$defs"]["Credit"]["properties"]["points"],
        "question": schema["$defs"]["NSIQuestion"]["properties"]["points"],
        "exercise": schema["properties"]["target_points"],
    }[location]
    assert not Draft202012Validator(field).is_valid(value)


@pytest.mark.parametrize("value", ["0.5", "0.25", "1", "999999.1234"])
def test_authoring_schema_accepts_valid_machine_credit(value):
    assert Draft202012Validator(
        constrained_schema()["$defs"]["Credit"]["properties"]["points"]
    ).is_valid(value)


@pytest.mark.parametrize("location", ["column", "cell"])
@pytest.mark.parametrize("value", ["", " \t\n", "x" * 181, None, 2])
def test_authoring_schema_rejects_invalid_table_cell(location, value):
    raw = raw_exercise()
    if location == "column":
        raw["materials"][0]["columns"][0] = value
    else:
        raw["materials"][0]["rows"][0][0] = value
    assert not Draft202012Validator(constrained_schema()).is_valid(raw)


def test_valid_table_and_decimal_rubric_pass_schema_and_domain_validation():
    raw = raw_exercise()
    raw["questions"][0]["marking"] = [
        {"points": value, "criterion": "Crédit distinct conforme aux données."}
        for value in ("0.5", "0.25", "0.25")
    ]
    raw["materials"][0]["rows"][0][0] = "é" * 180
    Draft202012Validator(constrained_schema()).validate(raw)
    NSIExercise.model_validate(raw, context={"authoring_profile": "v36-model-authored"})


def test_historical_reader_schema_is_not_tightened():
    schema = NSIExercise.model_json_schema()
    assert "pattern" not in schema["$defs"]["Credit"]["properties"]["points"]
    assert (
        "maxLength"
        not in schema["$defs"]["NSITableMaterial"]["properties"]["columns"]["items"]
    )
    assert (
        "pattern" not in authoring_schema()["$defs"]["Credit"]["properties"]["points"]
    )
    assert exercise_request("1", 42, []).schema["$defs"]["Credit"]["properties"][
        "points"
    ]["pattern"]


def test_runtime_still_rejects_decimal_with_trailing_newline():
    raw = raw_exercise()
    raw["questions"][0]["marking"][0]["points"] = "1\n"
    with pytest.raises(ValidationError, match="decimal string"):
        NSIExercise.model_validate(raw)


def test_installed_mlx_compiles_authoring_schema_constraints():
    llguidance = pytest.importorskip("llguidance")
    from Backend.Core.providers import _mlx_decoder_schema

    grammar = llguidance.grammar_from(
        "json", json.dumps(_mlx_decoder_schema(constrained_schema()))
    )
    assert not llguidance.LLMatcher.validate_grammar(grammar)
