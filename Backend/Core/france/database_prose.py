"""Finite, versioned French wording for the controlled database exercise."""

from __future__ import annotations

import json
from decimal import Decimal
from hashlib import sha256

from Backend.Core.france.database_binding import (
    canonical_database_answer,
    database_materials,
)
from Backend.Core.france.database_contract import DatabaseContract

DATABASE_PROSE_VERSION = "fr-nsi-database-prose-v1"
_TASK_IDS = tuple(f"2{letter}" for letter in "abcdef")
_POINT_PROFILES = {
    ("0.5", "0.5", "1", "1", "1", "1.5"),
    ("0.5", "1", "1", "1", "1", "1.5"),
    ("0.5", "1", "1", "1", "1.5", "1.5"),
}
_SCENES = {
    "atelier": (
        "Incidents et traitement des données",
        "Un atelier enregistre ses incidents dans trois relations liées.",
    ),
    "service": (
        "Suivi des incidents",
        "Un service suit ses interventions dans trois relations liées.",
    ),
}
_QUESTIONS = {
    "2a": (
        "On propose un incident d'identifiant 105 avec id_agent = 999 et id_cat = 1. Repérez l'anomalie d'insertion et justifiez-la.",
        "Pourquoi l'insertion d'un incident 105 lié à id_agent = 999 et id_cat = 1 doit-elle être refusée ?",
    ),
    "2b": (
        "Déterminez la catégorie de l'incident {incident_id} à l'aide des clés indiquées et justifiez la jointure.",
        "Quelle catégorie correspond à l'incident {incident_id} ? Précisez les attributs qui relient les deux relations.",
    ),
    "2c": (
        "La requête SQL fournie associe une mauvaise catégorie. Corrigez sa condition de jointure et indiquez le nombre de lignes renvoyées.",
        "Corrigez la jointure de la requête affichée pour obtenir les catégories réelles des incidents ; combien de lignes sont renvoyées ?",
    ),
    "2d": (
        "Écrivez une requête UPDATE ne modifiant que l'incident {incident_id} pour le rendre clos. Combien d'incidents sont alors clos ?",
        "Rendez clos uniquement l'incident {incident_id} au moyen de SQL, puis indiquez le nouveau nombre d'incidents clos.",
    ),
    "2e": (
        "Proposez un test par assertion, construit avec les statuts des quatre incidents, qui révèle le défaut de nombre_clos.",
        "Écrivez une assertion vérifiant le nombre d'incidents clos à partir des lignes fournies et montrez qu'elle échoue sur le code affiché.",
    ),
    "2f": (
        "Corrigez la condition fautive de nombre_clos et justifiez le résultat sur les quatre incidents affichés.",
        "Quelle condition faut-il changer dans nombre_clos ? Donnez le résultat corrigé et expliquez pourquoi.",
    ),
}


def database_catalogue_digest() -> str:
    payload = {
        "version": DATABASE_PROSE_VERSION,
        "scenes": _SCENES,
        "questions": _QUESTIONS,
    }
    return sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


def database_selection_schema(contract: DatabaseContract) -> dict:
    if contract.to_dict()["task_ids"] != list(_TASK_IDS):
        raise ValueError("Incompatible database contract")

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


def validate_database_selection(contract: DatabaseContract, selection: dict) -> dict:
    schema = database_selection_schema(contract)
    if not isinstance(selection, dict) or set(selection) != set(schema["properties"]):
        raise ValueError("Database selection outside schema")
    if selection["scene_id"] not in _SCENES:
        raise ValueError("Unknown database scene")
    for field in ("question_forms", "rubric_forms"):
        chosen = selection[field]
        rules = schema["properties"][field]["properties"]
        if not isinstance(chosen, dict) or set(chosen) != set(rules):
            raise ValueError("Database selection fields mismatch")
        if any(chosen[task_id] not in rule["enum"] for task_id, rule in rules.items()):
            raise ValueError("Unknown database wording ID")
    return selection


def _rubric(
    task_id: str, contract: DatabaseContract, points: str, variant: int
) -> list[dict]:
    data = contract.to_dict()
    expected = data["expected"]
    incident_id = data["tables"]["incident"]["rows"][0][0]
    prefix = "Points accordés pour " if variant == 1 else "Vérifier "
    criteria = {
        "2a": ["la clé étrangère invalide : id_agent = 999 n'existe pas dans agent."],
        "2b": [
            f"la catégorie {expected['correct_join'][0][1]} de l'incident {incident_id} via id_cat."
        ],
        "2c": [
            "la jointure incident.id_cat = categorie.id_cat et ses "
            f"{len(expected['correct_join'])} lignes."
        ],
        "2d": [
            f"l'UPDATE borné à l'incident {incident_id} ; "
            f"{expected['updated_count']} ligne modifiée et "
            f"{expected['closed_after_update']} incidents clos."
        ],
        "2e": [
            f"un test assert qui attend {expected['closed_before']} incidents clos.",
            f"l'échec du test : le code compte les statuts ouvert et renvoie {expected['faulty_python_count']}.",
        ],
        "2f": [
            "la condition corrigée statut == 'clos'.",
            f"la justification sur les données : {expected['closed_before']} clos, "
            f"contre {expected['faulty_python_count']} pour le code fautif.",
        ],
    }[task_id]
    if len(criteria) == 2 and points == "1.5":
        return [
            {"points": "0.5", "criterion": prefix + criteria[0]},
            {"points": "1", "criterion": prefix + criteria[1]},
        ]
    return [{"points": points, "criterion": prefix + " ".join(criteria)}]


def render_database_candidate(
    contract: DatabaseContract, selection: dict, task_specs: list[dict]
) -> dict:
    validate_database_selection(contract, selection)
    if (
        not isinstance(task_specs, list)
        or [plan.get("id") for plan in task_specs if isinstance(plan, dict)]
        != list(_TASK_IDS)
        or len(task_specs) != 6
        or tuple(plan.get("points") for plan in task_specs) not in _POINT_PROFILES
        or [plan.get("part_id") for plan in task_specs] != list("AABBCC")
        or sum(plan.get("estimated_minutes", 0) for plan in task_specs) != 70
    ):
        raise ValueError("Database blueprint credit or structure mismatch")
    data = contract.to_dict()
    title, lead = _SCENES[selection["scene_id"]]
    first_incident = data["tables"]["incident"]["rows"][0][0]
    context = (
        lead
        + " Les attributs id_agent, id_cat et id_incident sont des clés primaires "
        + "dans leur relation respective. Dans incident, id_agent référence "
        + "agent.id_agent et id_cat référence categorie.id_cat. "
        + "Les trois tableaux ci-dessous donnent l'état initial des données. "
        + "Pour les questions 2c et 2d, les requêtes concernent cet état initial. "
        + "La requête suivante est erronée :\n\n```sql\n"
        + data["faulty_sql"]
        + "\n```\n\nLa fonction suivante doit compter les incidents clos. "
        + "Son argument est une liste de dictionnaires ayant au moins la clé statut :\n\n```python\n"
        + data["faulty_python"]
        + "\n```"
    )
    questions = []
    for task_id, plan in zip(_TASK_IDS, task_specs, strict=True):
        answer = canonical_database_answer(task_id, contract)
        question_variant = int(selection["question_forms"][task_id][-1]) - 1
        rubric_variant = int(selection["rubric_forms"][task_id][-1])
        prompt = _QUESTIONS[task_id][question_variant].format(
            incident_id=first_incident
        )
        questions.append(
            {
                "id": task_id,
                "prompt": prompt,
                "points": plan["points"],
                "answer": answer,
                "marking": _rubric(task_id, contract, plan["points"], rubric_variant),
                "material_ids": ["agent", "categorie", "incident"],
                "curriculum_codes": [plan["required_curriculum_code"]],
                "operation": plan["operation"],
                "difficulty": plan["difficulty"],
                "estimated_minutes": plan["estimated_minutes"],
                "verification": {
                    "kind": "database_contract",
                    "contract": data,
                    "task_id": task_id,
                    "expected": data["expected"],
                },
            }
        )
    return {
        "id": "2",
        "title": title,
        "context": context,
        "topics": ["bases-donnees", "langages-programmation"],
        "minutes": 70,
        "target_points": str(
            sum((Decimal(plan["points"]) for plan in task_specs), Decimal(0))
        ),
        "materials": database_materials(contract),
        "questions": questions,
    }
