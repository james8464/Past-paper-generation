"""V36 authors see the bounded verifier's capabilities before choosing a kind."""

from copy import deepcopy

import pytest

from Backend.Core.france import llm_pipeline as subject
from Backend.Core.france.nsi import authoring_schema
from Backend.Core.france.verification import verify_contract
from tests.test_french_llm_pipeline import raw_exercise


def contracts():
    choices = subject.exercise_request("1", 42, []).schema["$defs"]["NSIQuestion"][
        "properties"
    ]["verification"]["oneOf"]
    return {choice["properties"]["kind"]["const"]: choice for choice in choices}


def test_v36_schema_documents_python_subset_and_bounds_not_general_python():
    description = contracts()["python_trace"]["description"]
    for phrase in (
        "assignation",
        "for",
        "if",
        "range",
        "len",
        "5000",
        "1000",
        "256",
        "4096",
        "10**9",
    ):
        assert phrase in description
    for phrase in (
        "def",
        "while",
        "lambda",
        "dictionnaires",
        "récursion",
        "appels de fonctions",
    ):
        assert phrase in description
    assert "type JSON exact" in description


def test_v36_schema_documents_sql_results_and_graph_material_binding():
    schemas = contracts()
    sql = schemas["sql"]["description"]
    for phrase in (
        "SQLite",
        "mémoire",
        "schema",
        "INSERT",
        "query",
        "256",
        "64",
        "8000",
        "ORDER BY",
        "[]",
    ):
        assert phrase in sql
    assert "coalesce" in sql and "load_extension" in sql
    graph = schemas["shortest_path"]["description"]
    for phrase in (
        "material_id",
        "material_ids",
        "edges",
        "directed",
        "accessible",
        "entiers",
        "distance",
    ):
        assert phrase in graph
    assert "ne prouve pas" in graph
    assert "human" in schemas["human"]["description"]


def test_brief_exposes_capabilities_without_changing_historical_schema():
    request = subject.exercise_request("1", 42, [])
    assert (
        "Le contrat python_trace ne fait pas tourner un interpréteur Python général"
        in request.prompt
    )
    assert "Si le travail dépasse ces capacités" in request.prompt
    historical = authoring_schema()["$defs"]["NSIQuestion"]["properties"][
        "verification"
    ]
    assert "oneOf" not in historical


def test_supported_trace_still_passes_and_function_definition_still_refuses():
    raw = raw_exercise()
    contract = {
        "kind": "python_trace",
        "code": "total = 0\nfor x in range(4):\n    total = total + x",
        "variable": "total",
        "expected": 6,
    }
    raw["questions"][0]["verification"] = contract
    assert verify_contract(contract)["passed"] is True
    assert subject.validate_authored_exercise(raw, "1")
    bad = deepcopy(raw)
    bad["questions"][0]["verification"]["code"] = "def f():\n    return 6\ntotal = f()"
    assert verify_contract(bad["questions"][0]["verification"])["passed"] is False
    with pytest.raises(ValueError, match="Vérification générique échouée"):
        subject.validate_authored_exercise(bad, "1")
