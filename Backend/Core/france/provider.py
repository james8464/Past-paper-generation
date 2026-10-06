"""Explicit French transport policy; UK prompt detection remains unchanged."""

import json
from hashlib import sha256

from Backend.Core.france.graph_tree_authoring import (
    contract_question_schema,
    part_response_schema,
    part_selection_schema,
    question_selection_schema,
)
from Backend.Core.france.network import ollama_request
from Backend.Core.france.nsi import NSIQuestion, authoring_schema
from Backend.Core.france.pipeline import REVIEW_FLAGS
from Backend.Core.providers import HostedLLMClient


class FrenchOllamaClient(HostedLLMClient):
    def __init__(self, *, model: str, base_url: str, seed: int):
        super().__init__(provider="ollama", model=model, api_key="", base_url=base_url)
        self.generation_seed = seed

    def generate_json(self, prompt: str, retries: int = 2) -> dict:
        if not 1 <= retries <= 3:
            raise ValueError("Une à trois tentatives sont autorisées")
        schema, budget = response_policy(prompt)
        for attempt in range(retries):
            current = prompt
            if attempt:
                current += (
                    "\nRéparation : la réponse précédente était incomplète. "
                    "Renvoyer un objet JSON complet, sans commentaire ni omission."
                )
            seed = (
                int.from_bytes(
                    sha256(
                        f"{self.generation_seed}:{attempt}:{prompt}".encode()
                    ).digest()[:4],
                    "big",
                )
                % 2_147_483_647
            )
            try:
                return self._ollama(
                    current,
                    schema=schema,
                    output_budget=budget,
                    seed=seed,
                    request_function=ollama_request,
                )
            except ValueError:
                if attempt == retries - 1:
                    raise
        raise AssertionError("Unreachable retry state")


def response_policy(prompt: str) -> tuple[dict, int]:
    if prompt.startswith("Répare une sélection verrouillée"):
        embedded = json.loads(
            prompt.split("schéma :\n", 1)[1].split("\nDONNÉES_JSON\n", 1)[0]
        )
        request = json.loads(prompt.split("\nDONNÉES_JSON\n", 1)[1])
        schema = question_selection_schema(request["question_id"])
        if embedded != schema:
            raise ValueError("Schéma de réparation de sélection incohérent")
        return schema, 1024
    if prompt.startswith("Sélectionne la partie "):
        part = prompt[len("Sélectionne la partie ") : len("Sélectionne la partie ") + 1]
        schema = part_selection_schema(part)
        embedded = json.loads(
            prompt.split("schéma :\n", 1)[1].split("\nDONNÉES_JSON\n", 1)[0]
        )
        if embedded != schema:
            raise ValueError("Schéma de sélection incohérent")
        return schema, 2048
    if prompt.startswith("Répare la question verrouillée"):
        schema = contract_question_schema()
        embedded = json.loads(
            prompt.split("schéma :\n", 1)[1].split("\nDONNÉES_JSON\n", 1)[0]
        )
        if embedded != schema:
            raise ValueError("Schéma de réparation incohérent")
        return schema, 3072
    if prompt.startswith("Rédige la partie "):
        part = prompt[len("Rédige la partie ") : len("Rédige la partie ") + 1]
        schema = part_response_schema(part)
        embedded = json.loads(
            prompt.split("schéma :\n", 1)[1].split("\nDONNÉES_JSON\n", 1)[0]
        )
        if embedded != schema:
            raise ValueError("Schéma de partie incohérent")
        return schema, 4096
    if prompt.startswith("Rédige directement en français académique"):
        return authoring_schema(), 6144
    if prompt.startswith(
        ("Répare uniquement la question", "Répare uniquement le barème")
    ):
        schema = NSIQuestion.model_json_schema()
        schema["required"].extend(["material_ids", "verification"])
        return schema, 3072
    text = {"type": "string", "minLength": 1, "maxLength": 6000}
    issues = {"type": "array", "items": text, "maxItems": 32}
    if prompt.startswith("Résous indépendamment"):
        candidate = json.loads(prompt.split("\n", 1)[1])
        identifiers = [question["id"] for question in candidate["questions"]]
        properties = {
            "answers": {
                "type": "object",
                "properties": {key: text for key in identifiers},
                "required": identifiers,
                "additionalProperties": False,
            },
            "issues": issues,
            "minutes": {"type": "integer", "minimum": 1, "maximum": 210},
        }
        budget = 4096
    elif prompt.startswith("Vérifie ce sujet"):
        properties = {
            **{flag: {"type": "boolean"} for flag in REVIEW_FLAGS},
            "issues": issues,
            "rationale": text,
            "question_ids": {
                "type": "array",
                "items": {"type": "string", "maxLength": 3},
                "minItems": 4,
                "maxItems": 16,
            },
        }
        budget = 3072
    elif prompt.startswith("Contrôle indépendant des capacités"):
        request = json.loads(prompt.split("\nDONNÉES_JSON\n", 1)[1])
        identifiers = [item["id"] for item in request["question_blueprint"]]
        item = {
            "type": "object",
            "properties": {
                "question_id": {"type": "string", "enum": identifiers},
                "objective_code": {"type": "string", "minLength": 3, "maxLength": 40},
                "aligned": {"type": "boolean"},
                "rationale": {"type": "string", "minLength": 40, "maxLength": 1800},
                "issues": issues,
            },
            "required": [
                "question_id",
                "objective_code",
                "aligned",
                "rationale",
                "issues",
            ],
            "additionalProperties": False,
        }
        properties = {
            "questions": {
                "type": "array",
                "items": item,
                "minItems": len(identifiers),
                "maxItems": len(identifiers),
            }
        }
        budget = 3072
    else:
        raise ValueError("Type de requête française inconnu; aucun repli britannique")
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }, budget
