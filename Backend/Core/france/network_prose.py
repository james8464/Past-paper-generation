"""Finite original French prose for a grounded NSI network exercise."""

from __future__ import annotations

import json
from decimal import Decimal
from hashlib import sha256

from Backend.Core.france.network_binding import (
    canonical_network_answer,
    network_materials,
)
from Backend.Core.france.network_contract import NetworkContract

NETWORK_PROSE_VERSION = "fr-nsi-network-prose-v1"
_TASK_IDS = tuple(f"3{letter}" for letter in "abcdef")
_POINT_PROFILES = {
    ("0.5", "0.5", "1", "1", "1", "1.5"),
    ("0.5", "1", "1", "1", "1", "1.5"),
    ("0.5", "1", "1", "1", "1.5", "1.5"),
}
_SCENES = {
    "campus": (
        "Réseau et échanges d'un campus",
        "Un campus relie son centre à une station par deux relais.",
    ),
    "terrain": (
        "Liaisons d'une station de terrain",
        "Une station de terrain échange avec un centre par deux relais.",
    ),
}
_QUESTIONS = {
    "3a": (
        "Calculez le coût des deux routes de Central à Station et choisissez la moins coûteuse.",
        "Quelle route relie Central à Station au coût minimal initial ? Détaillez les deux calculs.",
    ),
    "3b": (
        "Après le changement de coût indiqué, calculez les deux nouveaux coûts et choisissez la route.",
        "La liaison R1–Station change de coût. Quelle route est désormais préférable ? Justifiez par les coûts.",
    ),
    "3c": (
        "Le tableau des processus représente-t-il un interblocage ? Justifiez avec les ressources détenues et attendues.",
        "Expliquez pourquoi B et C ne peuvent pas progresser dans l'état simultané affiché.",
    ),
    "3d": (
        "Comment résoudre cet état puis imposer l'ordre A avant B aux deux processus pour éviter ce cycle ?",
        "Indiquez l'action immédiate nécessaire à C, puis une règle commune d'acquisition empêchant ce cycle.",
    ),
    "3e": (
        "Proposez trois étapes pour établir une clé de session dans les conditions de sécurité indiquées.",
        "Décrivez l'obtention d'une clé de session commune en trois étapes, sans secret partagé initial.",
    ),
    "3f": (
        "Justifiez la confidentialité face à l'observateur passif et précisez deux limites du dispositif.",
        "Expliquez le rôle de la clé publique authentifiée et de la clé de session, puis les garanties qui restent hors portée.",
    ),
}


def network_catalogue_digest() -> str:
    return sha256(
        json.dumps(
            {"version": NETWORK_PROSE_VERSION, "scenes": _SCENES, "questions": _QUESTIONS},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def network_selection_schema(contract: NetworkContract) -> dict:
    if contract.to_dict()["task_ids"] != list(_TASK_IDS):
        raise ValueError("Incompatible network contract")

    def forms(suffix: str) -> dict:
        return {
            "type": "object",
            "properties": {
                task_id: {
                    "type": "string",
                    "enum": [f"{task_id}-{suffix}1", f"{task_id}-{suffix}2"],
                }
                for task_id in _TASK_IDS
            },
            "required": list(_TASK_IDS),
            "additionalProperties": False,
        }

    return {
        "type": "object",
        "properties": {
            "scene_id": {"type": "string", "enum": list(_SCENES)},
            "question_forms": forms("q"),
            "rubric_forms": forms("r"),
        },
        "required": ["scene_id", "question_forms", "rubric_forms"],
        "additionalProperties": False,
    }


def validate_network_selection(contract: NetworkContract, selection: dict) -> dict:
    schema = network_selection_schema(contract)
    if not isinstance(selection, dict) or set(selection) != set(schema["properties"]):
        raise ValueError("Network selection outside schema")
    if selection["scene_id"] not in _SCENES:
        raise ValueError("Unknown network scene")
    for field in ("question_forms", "rubric_forms"):
        chosen = selection[field]
        rules = schema["properties"][field]["properties"]
        if not isinstance(chosen, dict) or set(chosen) != set(rules):
            raise ValueError("Network selection fields mismatch")
        if any(chosen[task_id] not in rule["enum"] for task_id, rule in rules.items()):
            raise ValueError("Unknown network wording ID")
    return selection


def _rubric(task_id: str, contract: NetworkContract, points: str, variant: int) -> list[dict]:
    expected = contract.to_dict()["expected"]
    prefix = "Points accordés pour " if variant == 1 else "Vérifier "
    criteria = {
        "3a": [f"les deux coûts initiaux {expected['before']['cost']} et {expected['before']['other_cost']} et la route via R1."],
        "3b": [f"les nouveaux coûts {expected['after']['other_cost']} et {expected['after']['cost']} et la route via R2."],
        "3c": ["le cycle : B détient A, attend B ; C détient B, attend A."],
        "3d": ["la libération de B par C et l'ordre commun A avant B, qui supprime le cycle."],
        "3e": ["la clé publique authentifiée, la clé de session chiffrée et son usage symétrique."],
        "3f": [
            "la confidentialité conditionnelle face à un observateur passif et l'authenticité de la clé publique.",
            "les limites : terminal compromis, métadonnées ; un secret prépartagé changerait le protocole.",
        ],
    }[task_id]
    if len(criteria) == 2 and points == "1.5":
        return [
            {"points": "0.5", "criterion": prefix + criteria[0]},
            {"points": "1", "criterion": prefix + criteria[1]},
        ]
    return [{"points": points, "criterion": prefix + " ".join(criteria)}]


def render_network_candidate(
    contract: NetworkContract, selection: dict, task_specs: list[dict]
) -> dict:
    validate_network_selection(contract, selection)
    if (
        not isinstance(task_specs, list)
        or len(task_specs) != 6
        or any(not isinstance(plan, dict) for plan in task_specs)
        or [plan.get("id") for plan in task_specs] != list(_TASK_IDS)
        or tuple(plan.get("points") for plan in task_specs) not in _POINT_PROFILES
        or [plan.get("part_id") for plan in task_specs] != list("AABBCC")
        or sum(plan.get("estimated_minutes", 0) for plan in task_specs) != 70
    ):
        raise ValueError("Network blueprint credit or structure mismatch")
    data = contract.to_dict()
    title, lead = _SCENES[selection["scene_id"]]
    context = (
        lead
        + " Les quatre liaisons bidirectionnelles et leurs coûts initiaux sont "
        + "tous indiqués dans le premier tableau. Pour la question 3b, le coût "
        + f"de R1–Station passe de {data['links'][1][2]} à {data['change']['new_cost']} ; "
        + "les autres coûts sont inchangés. Le second tableau montre un état "
        + "simultané de deux processus utilisant les ressources A et B. "
        + "Pour les questions 3e et 3f, un capteur et la station ne disposent "
        + "d'aucun secret partagé initial ; la clé publique de la station est "
        + "authentifiée. On considère seulement un observateur passif du réseau."
    )
    questions = []
    for task_id, plan in zip(_TASK_IDS, task_specs, strict=True):
        prompt = _QUESTIONS[task_id][
            int(selection["question_forms"][task_id][-1]) - 1
        ]
        materials = ["links"] if task_id in {"3a", "3b"} else ["processes"] if task_id in {"3c", "3d"} else []
        questions.append(
            {
                "id": task_id,
                "prompt": prompt,
                "points": plan["points"],
                "answer": canonical_network_answer(task_id, contract),
                "marking": _rubric(
                    task_id, contract, plan["points"],
                    int(selection["rubric_forms"][task_id][-1]),
                ),
                "material_ids": materials,
                "curriculum_codes": [plan["required_curriculum_code"]],
                "operation": plan["operation"],
                "difficulty": plan["difficulty"],
                "estimated_minutes": plan["estimated_minutes"],
                "verification": {
                    "kind": "network_contract",
                    "contract": data,
                    "task_id": task_id,
                    "expected": data["expected"],
                },
            }
        )
    return {
        "id": "3",
        "title": title,
        "context": context,
        "topics": ["architectures-reseaux"],
        "minutes": 70,
        "target_points": str(sum((Decimal(plan["points"]) for plan in task_specs), Decimal(0))),
        "materials": network_materials(contract),
        "questions": questions,
    }
