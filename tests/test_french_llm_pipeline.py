"""V36 authors content through providers, never a finite question catalogue."""

from copy import deepcopy

import pytest
from jsonschema.exceptions import ValidationError as SchemaValidationError

from Backend.Core.france import llm_pipeline as subject
from tests.test_nsi_pipeline import make_index


def raw_exercise(identifier="1", marker="Aventure originale"):
    topic, code = {
        "1": ("structures-donnees", "SD-LINEAIRE"),
        "2": ("bases-donnees", "BDD-MODELE"),
        "3": ("architectures-reseaux", "ASR-PROCESSUS"),
    }[identifier]
    return {
        "id": identifier,
        "title": marker,
        "context": f"Une équipe étudie ses données dans le contexte {marker}.",
        "topics": [topic],
        "minutes": 70,
        "target_points": "6",
        "materials": [
            {
                "kind": "table",
                "id": "donnees",
                "title": "Données du contexte",
                "columns": ["Objet", "Valeur"],
                "rows": [["Alpha", "2"], ["Beta", "4"]],
            }
        ],
        "questions": [
            dict(
                id=str(i + 1),
                prompt=f"Justifiez le résultat de l'étape {i + 1} dans {marker}.",
                points="1",
                answer=f"Réponse développée pour {marker}, étape {i + 1}.",
                marking=[
                    {
                        "points": "1",
                        "criterion": "Raisonnement cohérent avec les données.",
                    }
                ],
                material_ids=["donnees"],
                curriculum_codes=[code],
                operation=["apply", "analyse", "design", "debug", "justify", "analyse"][
                    i
                ],
                difficulty=[2, 2, 3, 3, 4, 4][i],
                estimated_minutes=[10, 10, 10, 10, 15, 15][i],
                verification={"kind": "human"},
            )
            for i in range(6)
        ],
    }


class Client:
    provider = "ollama"
    model = "mock-model"

    def __init__(self, marker="Aventure originale", mutate=None):
        self.marker, self.mutate = marker, mutate
        self.requests = []

    def generate_request(self, request):
        self.requests.append(request)
        properties = request.schema["properties"]
        if "id" in properties:
            result = raw_exercise(properties["id"]["const"], self.marker)
            if self.mutate:
                self.mutate(result)
            return result
        if "answers" in properties:
            assert (
                "marking" not in request.prompt and "verification" not in request.prompt
            )
            assert "Réponse développée" not in request.prompt
            return {
                "answers": {
                    identifier: "Solution indépendante détaillée."
                    for identifier in properties["answers"]["properties"]
                },
                "issues": [],
            }
        return {
            identifier: {
                "correct": True,
                "answer_complete": True,
                "rubric_consistent": True,
                "curriculum_aligned": True,
                "french": True,
                "self_contained": True,
                "issues": [],
            }
            for identifier in properties
        }


def generate(tmp_path, client):
    path = tmp_path / "index.sqlite"
    make_index(path)
    return subject.generate(index_path=path, client=client, seed=42)


def test_different_model_responses_produce_different_substantive_papers(tmp_path):
    a = generate(tmp_path, Client("Aventure Alpha"))
    b = generate(tmp_path, Client("Recherche Beta"))
    assert a["exercises"] != b["exercises"]
    assert a["identity"]["content_sha256"] != b["identity"]["content_sha256"]
    assert a["model_used"] is True and a["generation_origin"] == "model_authored"
    assert a["status"] == "unreviewed_draft"
    assert len(subject.validate_package(a)) == 3
    assert (a["technical_points"], a["language_points"], a["minutes"]) == (
        "18",
        "2",
        210,
    )
    assert a["warnings"] and all(
        item["state"] == "not_checked" for item in a["warnings"]
    )


def test_requests_use_typed_schema_and_no_fixed_question_or_answer_bank(tmp_path):
    client = Client()
    package = generate(tmp_path, client)
    assert len(client.requests) == 9
    assert all(
        request.operation == "french_nsi_authoring" for request in client.requests
    )
    assert all(
        review["status"] == "model_reviewed_not_proven" for review in package["reviews"]
    )
    for request in client.requests[::3]:
        assert "Invente le contexte" in request.prompt
        assert "Réponse développée" not in request.prompt
        assert request.output_budget == 8192
    assert {item["category"] for item in package["references"]} == {
        "programme",
        "official_paper",
    }


@pytest.mark.parametrize(
    "provider,budgets",
    [
        ("ollama", [8192, 6000, 4096]),
        ("apple", [8192, 6000, 4096]),
        ("openai", [8192, 6000, 4096]),
        ("anthropic", [8192, 6000, 4096]),
        ("deepseek", [16384, 16384, 16384]),
    ],
)
def test_phase_output_allowances_are_explicit_and_provider_scoped(
    tmp_path, provider, budgets
):
    client = Client()
    client.provider = provider
    generate(tmp_path, client)
    assert [request.output_budget for request in client.requests] == budgets * 3


def test_authoring_budget_override_does_not_modify_schema_prompt_or_sampling_identity():
    default = subject.exercise_request(
        "1", 42, [], previous_topics=("Bases de données",)
    )
    larger = subject.exercise_request(
        "1", 42, [], previous_topics=("Bases de données",), output_budget=16384
    )
    assert default.output_budget == 8192 and larger.output_budget == 16384
    for field in (
        "prompt",
        "operation",
        "schema",
        "generation_seed",
        "seed",
        "attempt",
        "temperature",
        "expected_ids",
    ):
        assert getattr(default, field) == getattr(larger, field)


def test_structural_deepseek_regeneration_keeps_allowance_and_owned_schema_seed(
    tmp_path,
):
    class Retry(Client):
        provider = "deepseek"

        def generate_request(self, request):
            result = super().generate_request(request)
            if "id" in request.schema["properties"] and request.attempt == 1:
                result["topics"] = ["not-in-the-taxonomy"]
            return result

    client = Retry()
    generate(tmp_path, client)
    authors = [
        request for request in client.requests if "id" in request.schema["properties"]
    ]
    assert [request.attempt for request in authors] == [1, 2] * 3
    for first, second in zip(authors[::2], authors[1::2], strict=True):
        assert first.output_budget == second.output_budget == 16384
        assert first.schema == second.schema
        assert first.generation_seed == second.generation_seed
        assert first.temperature == second.temperature


def test_authoring_grammar_exposes_the_taxonomy_and_contract_keys():
    from jsonschema import Draft202012Validator

    from Backend.Core.france.nsi import CURRICULUM_OBJECTIVES, TOPICS

    schema = subject.exercise_request("1", 42, []).schema
    assert set(schema["properties"]["topics"]["items"]["enum"]) == TOPICS
    question = schema["$defs"]["NSIQuestion"]["properties"]
    assert set(question["curriculum_codes"]["items"]["enum"]) == set(
        CURRICULUM_OBJECTIVES
    )
    raw = raw_exercise()
    raw["questions"][0]["verification"] = {"type": "human"}
    assert list(Draft202012Validator(schema).iter_errors(raw))


def test_one_structural_regeneration_does_not_patch_answers_or_relax_marks(tmp_path):
    class Retry(Client):
        def generate_request(self, request):
            result = super().generate_request(request)
            if "id" in request.schema["properties"] and request.attempt == 1:
                result["topics"] = ["SD-LINEAIRE"]
            return result

    client = Retry()
    package = generate(tmp_path, client)
    authors = [
        request for request in client.requests if "id" in request.schema["properties"]
    ]
    assert [request.attempt for request in authors] == [1, 2] * 3
    assert all(
        "REGENERATION" in request.prompt for request in authors if request.attempt == 2
    )
    assert all("Réponse développée" not in request.prompt for request in authors)
    assert [item["attempts"] for item in package["authoring_attempts"]] == [2, 2, 2]
    assert len(subject.validate_package(package)) == 3


def test_second_invalid_structural_response_stops_without_review_or_catalogue(tmp_path):
    from Backend.Core.generation_diagnostics import GenerationEvidenceError

    client = Client(mutate=lambda raw: raw.update(topics=["not-a-topic"]))
    with pytest.raises(GenerationEvidenceError) as failure:
        generate(tmp_path, client)
    assert len(client.requests) == 2
    assert len(failure.value.details["attempts"]) == 2
    assert isinstance(failure.value.__cause__, SchemaValidationError)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda raw: raw.update(target_points="7"),
        lambda raw: raw.update(minutes=60),
        lambda raw: raw["questions"][0].update(points="2"),
        lambda raw: raw["questions"][0]["marking"][0].update(points="0.5"),
        lambda raw: raw["questions"][0].pop("verification"),
        lambda raw: raw["questions"][0].update(curriculum_codes=["UK-AO1"]),
        lambda raw: raw["questions"][0].update(
            answer="```python\nimport os\nos.remove('paper.pdf')\n```"
        ),
        lambda raw: raw["questions"][0].update(
            answer="```python\nvalue = open('secret')\n```"
        ),
        lambda raw: raw["questions"][0].update(
            verification={"kind": "tree_case_contract", "seed": 123}
        ),
        lambda raw: raw["questions"][0].update(
            verification={
                "kind": "python_trace",
                "code": "x = 2 + 3",
                "variable": "x",
                "expected": 6,
            }
        ),
    ],
)
def test_malformed_marks_curriculum_unsafe_code_and_fixed_contracts_refuse(mutate):
    raw = raw_exercise()
    mutate(raw)
    with pytest.raises((ValueError, SchemaValidationError)):
        subject.validate_authored_exercise(raw, "1")


def test_generic_execution_is_bounded_and_does_not_trust_model_expected_value():
    raw = raw_exercise()
    raw["questions"][0]["verification"] = {
        "kind": "python_trace",
        "code": "resultat = 2 + 3",
        "variable": "resultat",
        "expected": 5,
    }
    assert subject.validate_authored_exercise(raw, "1")
    raw["questions"][0]["verification"]["code"] = (
        "import os\nresultat = os.listdir('.')"
    )
    with pytest.raises(ValueError):
        subject.validate_authored_exercise(raw, "1")


def test_no_compatible_references_means_no_model_calls_and_no_catalogue_fallback(
    tmp_path,
):
    from Backend.Core.scoped_references import ReferenceIndex

    path = tmp_path / "empty.sqlite"
    with ReferenceIndex(path):
        pass
    client = Client()
    with pytest.raises(ValueError):
        subject.generate(index_path=path, client=client, seed=42)
    assert not client.requests


def test_negative_model_review_fails_instead_of_selecting_a_fixed_family(tmp_path):
    class Negative(Client):
        def generate_request(self, request):
            result = super().generate_request(request)
            if "1" in result:
                result["1"]["correct"] = False
                result["1"]["issues"] = ["Réponse incorrecte."]
            return result

    client = Negative()
    with pytest.raises(ValueError, match="refuse"):
        generate(tmp_path, client)
    assert len(client.requests) == 3


def test_restore_revalidates_reviews_even_if_content_hash_is_recomputed(tmp_path):
    package = generate(tmp_path, Client())
    package["reviews"][0]["question_review"]["1"]["correct"] = False
    package["identity"]["content_sha256"] = subject._digest(
        {key: value for key, value in package.items() if key != "identity"}
    )
    with pytest.raises(ValueError, match=r"contrôle|review"):
        subject.validate_package(package)


def test_changed_content_or_false_model_identity_cannot_replay(tmp_path):
    package = generate(tmp_path, Client())
    for mutate in (
        lambda p: p.update(model_used=False),
        lambda p: p["exercises"][0].update(title="Texte remplacé"),
        lambda p: p["identity"].update(seed=True),
    ):
        changed = deepcopy(package)
        mutate(changed)
        with pytest.raises(ValueError):
            subject.validate_package(changed)


def test_unimported_system_access_in_snippet_is_still_rejected():
    raw = raw_exercise()
    raw["questions"][0]["answer"] = "```python\nos.system('commande')\n```"
    with pytest.raises(ValueError, match="non autorisé"):
        subject.validate_authored_exercise(raw, "1")


def test_actual_installed_mlx_grammar_compiles_authoring_and_review_shapes():
    import json

    llguidance = pytest.importorskip("llguidance")
    from Backend.Core.providers import _mlx_decoder_schema

    exercise = subject.validate_authored_exercise(raw_exercise(), "1")
    for schema in (
        subject.exercise_request("1", 42, []).schema,
        subject._solution_schema(exercise),
        subject._review_schema(exercise),
    ):
        grammar = llguidance.grammar_from(
            "json", json.dumps(_mlx_decoder_schema(schema))
        )
        assert not llguidance.LLMatcher.validate_grammar(grammar)


def test_holdout_sources_are_never_used_for_generation(tmp_path):
    import sqlite3

    path = tmp_path / "index.sqlite"
    make_index(path)
    with sqlite3.connect(path) as db:
        db.execute("UPDATE sources SET split='holdout'")
    client = Client()
    with pytest.raises(ValueError):
        subject.generate(index_path=path, client=client, seed=42)
    assert not client.requests


@pytest.mark.parametrize(
    "field,value",
    [
        ("reviews", []),
        ("checks", []),
        ("warnings", []),
        ("language_rubric", {}),
        ("references", []),
        ("teacher_review", "approved"),
    ],
)
def test_recomputed_hash_cannot_bypass_required_evidence(tmp_path, field, value):
    package = generate(tmp_path, Client())
    package[field] = value
    package["identity"]["content_sha256"] = subject._digest(
        {key: value for key, value in package.items() if key != "identity"}
    )
    with pytest.raises(ValueError):
        subject.validate_package(package)
