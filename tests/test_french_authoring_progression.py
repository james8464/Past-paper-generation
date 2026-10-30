"""The V36 author brief asks for sustained, well-defined tasks, not a bank."""

from Backend.Core.france.llm_pipeline import exercise_request
from Backend.Core.france.nsi import authoring_schema


def test_authoring_brief_connects_reasoning_without_cross_exercise_dependencies():
    request = exercise_request("2", 42, [])
    prompt = request.prompt
    assert "Trois exercices indépendants" in prompt
    assert "sans prérequis provenant des autres exercices" in prompt
    assert "Développe un problème suivi" in prompt
    assert "interpréter une représentation ou un état" in prompt
    assert "construire ou adapter une solution" in prompt
    assert "en examiner le fonctionnement et en justifier les limites" in prompt
    assert "réutiliser le travail précédent au sein de cet exercice" in prompt
    assert "Énonce les définitions, les conventions, les cas limites" in prompt
    assert "chaque élément demandé est traité dans la réponse et crédité" in prompt
    assert "sans remplir des pages à vide" not in prompt
    assert "nombre précis d’erreurs" not in prompt


def test_progression_brief_preserves_transport_marks_and_historical_schema_defaults():
    request = exercise_request("2", 42, [])
    assert request.operation == "french_nsi_authoring"
    assert request.generation_seed == 42
    assert request.temperature == 0.6
    assert request.output_budget == 8192
    assert request.schema["properties"]["id"]["const"] == "2"
    assert request.schema["properties"]["target_points"]["const"] == "6"
    assert request.schema["properties"]["minutes"]["const"] == 70
    assert "Les 2 points indicatifs de langue sont séparés" in request.prompt
    assert "Ne sélectionne pas une famille connue" in request.prompt
    assert "ne reformule pas un sujet de référence" in request.prompt
    assert authoring_schema()["properties"]["materials"]["minItems"] == 1
    assert "pattern" not in authoring_schema()["$defs"]["Credit"]["properties"]["points"]
