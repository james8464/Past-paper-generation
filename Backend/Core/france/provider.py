"""Explicit French transport policy; UK prompt detection remains unchanged."""

import json
from hashlib import sha256

from Backend.Core.france.network import ollama_request
from Backend.Core.france.nsi import authoring_schema
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
    if prompt.startswith("Rédige directement en français académique"):
        return authoring_schema(), 6144
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
    else:
        raise ValueError("Type de requête française inconnu; aucun repli britannique")
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }, budget
