"""Closed, versioned French text for one immutable NSI graph/tree contract.

Only finite IDs cross the model boundary. Printed facts come from the contract;
the catalogue itself is part of the checkpoint/package identity.
"""

from __future__ import annotations

import json
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256

from Backend.Core.france.graph_tree_binding import canonical_answer
from Backend.Core.france.graph_tree_contract import GraphTreeContract

PROSE_CONTRACT_VERSION = "fr-nsi-graph-tree-prose-v2"

_SCENES = {
    "service": {
        "interventions": (
            "Réseau et arbre de recherche",
            "Un service coordonne des interventions entre plusieurs postes. "
            "Le réseau pondéré et l'arbre binaire de recherche ci-dessous "
            "représentent deux structures distinctes.",
        ),
        "demandes": (
            "Réseau et arbre de recherche",
            "Un service organise des demandes entre plusieurs postes. "
            "Le réseau pondéré et l'arbre binaire de recherche ci-dessous "
            "représentent deux structures distinctes.",
        ),
    },
    "collecte": {
        "collectes": (
            "Collectes en réseau et arbre de recherche",
            "Un service planifie des collectes entre plusieurs postes. "
            "Le réseau pondéré et l'arbre binaire de recherche ci-dessous "
            "représentent deux structures distinctes.",
        ),
    },
}

_QUESTIONS = {
    "1a": (
        "Déterminez dans `reseau` un chemin de poids minimal de A à F et donnez son poids total.",
        "Quel chemin de A à F minimise le poids total dans `reseau` ? Précisez ce poids.",
    ),
    "1b": (
        "Indiquez les voisins de A dans `reseau`, puis calculez la somme des poids des arêtes incidentes à A.",
        "Quels sont les voisins de A dans `reseau` ? Calculez le poids total des arêtes qui touchent A.",
    ),
    "1c": (
        "Repérez la faute dans le programme fourni, corrigez-la et indiquez le parcours alors obtenu.",
        "Pourquoi le programme fourni échoue-t-il ? Donnez la correction et l'ordre du parcours corrigé.",
    ),
    "1d": (
        "Effectuez le parcours en largeur de `reseau` depuis A et donnez l'ordre de visite des sommets.",
        "En partant de A, indiquez dans quel ordre le parcours en largeur de `reseau` visite les sommets.",
    ),
    "1e": (
        "Dans `arbre`, indiquez le chemin de recherche pour insérer la clé {insert_key}, puis sa position finale.",
        "Pour ajouter {insert_key} à `arbre`, donnez les clés traversées et l'emplacement du nouveau nœud.",
    ),
    "1f": (
        "Après cette insertion dans `arbre`, donnez le parcours infixe et rappelez le principe d'un ABR.",
        "Quel est le parcours infixe de `arbre` après insertion ? Justifiez l'ordre à partir de la propriété d'un ABR.",
    ),
}

_RUBRIC_WORDING = {
    "1a": (
        ("Chemin minimal et poids correct : {answer}",),
        ("Résultat vérifié : {answer}",),
    ),
    "1b": (
        (
            "Voisins de A correctement relevés : {neighbours}.",
            "Somme des poids incidents correcte : {weight_sum}.",
        ),
        (
            "Liste des voisins de A : {neighbours}.",
            "Total des poids des arêtes incidentes à A : {weight_sum}.",
        ),
    ),
    "1c": (
        (
            "Faute repérée : `visin` provoque NameError.",
            "Correction `voisin` et ordre obtenu : {corrected_order}.",
        ),
        (
            "Variable fautive `visin` et erreur NameError identifiées.",
            "Nom `voisin` rétabli ; parcours corrigé : {corrected_order}.",
        ),
    ),
    "1d": (
        ("Ordre du parcours correct : {order}.",),
        ("Sommets visités dans l'ordre vérifié : {order}.",),
    ),
    "1e": (
        (
            "Chemin de recherche correct : {search_path}.",
            "Clé {insert_key} placée comme enfant {side} de {parent}.",
        ),
        (
            "Clés parcourues avant insertion : {search_path}.",
            "Emplacement correct pour {insert_key} : enfant {side} de {parent}.",
        ),
    ),
    "1f": (
        (
            "Parcours infixe correct : {inorder}.",
            "Propriété d'un ABR : clés du sous-arbre gauche inférieures à la racine et clés du sous-arbre droit supérieures à la racine.",
        ),
        (
            "Ordre infixe après insertion : {inorder}.",
            "Propriété de recherche : clés à gauche inférieures à la racine et clés à droite supérieures à la racine.",
        ),
    ),
}


def prose_catalogue_digest() -> str:
    payload = {
        "version": PROSE_CONTRACT_VERSION,
        "scenes": _SCENES,
        "questions": _QUESTIONS,
        "rubric": _RUBRIC_WORDING,
    }
    return sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


def _task_ids(part: str) -> tuple[str, str]:
    if part not in ("A", "B", "C"):
        raise ValueError("Partie NSI inconnue")
    start = {"A": 0, "B": 2, "C": 4}[part]
    return tuple(_QUESTIONS)[start : start + 2]


def selection_schema(part: str) -> dict:
    ids = _task_ids(part)
    question = {
        "type": "object",
        "properties": {
            "contract_task_id": {"type": "string", "enum": list(ids)},
            "claimed_result": {"type": "object"},
            "question_form_id": {
                "type": "string",
                "enum": [f"{key}-q{n}" for key in ids for n in (1, 2)],
            },
            "rubric_form_id": {
                "type": "string",
                "enum": [f"{key}-r{n}" for key in ids for n in (1, 2)],
            },
        },
        "required": [
            "contract_task_id",
            "claimed_result",
            "question_form_id",
            "rubric_form_id",
        ],
        "additionalProperties": False,
    }
    properties = {
        "questions": {"type": "array", "items": question, "minItems": 2, "maxItems": 2}
    }
    if part == "A":
        properties = {
            "scene_id": {"type": "string", "enum": list(_SCENES)},
            "slots": {
                "type": "object",
                "properties": {
                    "activity": {
                        "type": "string",
                        "enum": sorted(
                            {
                                activity
                                for values in _SCENES.values()
                                for activity in values
                            }
                        ),
                    }
                },
                "required": ["activity"],
                "additionalProperties": False,
            },
            **properties,
        }
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def validate_selection(
    part: str, selection: dict, task: dict, contract: GraphTreeContract
) -> None:
    ids = _task_ids(part)
    expected_keys = {"scene_id", "slots", "questions"} if part == "A" else {"questions"}
    if not isinstance(selection, dict) or set(selection) != expected_keys:
        raise ValueError("Sélection de partie hors schéma")
    if part == "A" and (
        not isinstance(selection["scene_id"], str)
        or selection["scene_id"] not in _SCENES
        or not isinstance(selection["slots"], dict)
        or set(selection["slots"]) != {"activity"}
        or not isinstance(selection["slots"]["activity"], str)
        or selection["slots"]["activity"] not in _SCENES[selection["scene_id"]]
    ):
        raise ValueError("Situation ou emplacement inconnu")
    chosen = selection["questions"]
    if not isinstance(chosen, list) or len(chosen) != 2:
        raise ValueError("Deux sélections sont requises")
    data = contract.to_dict()
    if data["task_ids"] != list(_QUESTIONS):
        raise ValueError("Contrat de tâches incompatible")
    plans = task["question_blueprint"]
    for index, (choice, task_id) in enumerate(zip(chosen, ids, strict=True)):
        if (
            not isinstance(choice, dict)
            or set(choice)
            != {
                "contract_task_id",
                "claimed_result",
                "question_form_id",
                "rubric_form_id",
            }
            or choice["contract_task_id"] != task_id
            or choice["claimed_result"] != data["expected"][task_id]
            or choice["question_form_id"] not in (f"{task_id}-q1", f"{task_id}-q2")
            or choice["rubric_form_id"] not in (f"{task_id}-r1", f"{task_id}-r2")
            or plans[{"A": 0, "B": 2, "C": 4}[part] + index]["id"] != task_id
        ):
            raise ValueError("Sélection de question incompatible avec le contrat")


def _credit_parts(total: str, task_id: str) -> tuple[str, ...]:
    value = Decimal(total)
    if task_id not in ("1b", "1c", "1e", "1f"):
        return (total,)
    first = Decimal("0.25") if value == Decimal("0.5") else value - Decimal("0.5")
    return (str(first), str(value - first))


def _rubric_values(task_id: str, result: dict, answer: str) -> dict:
    values = {"answer": answer}
    if task_id == "1b":
        values.update(
            neighbours=", ".join(result["neighbours"]), weight_sum=result["weight_sum"]
        )
    elif task_id == "1c":
        values.update(corrected_order=" → ".join(result["corrected_order"]))
    elif task_id == "1d":
        values.update(order=" → ".join(result["order"]))
    elif task_id == "1e":
        path = result["search_path"]
        values.update(
            search_path=" → ".join(map(str, path)),
            insert_key=result["insert_key"],
            side="gauche" if result["insert_key"] < path[-1] else "droite",
            parent=path[-1],
        )
    elif task_id == "1f":
        values.update(inorder=" → ".join(map(str, result["inorder"])))
    return values


def render_graph_tree_candidate(
    task: dict, contract: GraphTreeContract, selections: list[dict]
) -> dict:
    if not isinstance(selections, list) or len(selections) != 3:
        raise ValueError("Trois parties sont requises")
    for part, selection in zip("ABC", selections, strict=True):
        validate_selection(part, selection, task, contract)
    data = contract.to_dict()
    scene = selections[0]
    title, context = _SCENES[scene["scene_id"]][scene["slots"]["activity"]]
    questions = []
    for choice, plan in zip(
        (item for part in selections for item in part["questions"]),
        task["question_blueprint"],
        strict=True,
    ):
        task_id = plan["id"]
        result = data["expected"][task_id]
        answer = canonical_answer(task_id, result)
        question_variant = int(choice["question_form_id"][-1]) - 1
        rubric_variant = int(choice["rubric_form_id"][-1]) - 1
        criterion_forms = _RUBRIC_WORDING[task_id][rubric_variant]
        credits = _credit_parts(plan["points"], task_id)
        questions.append(
            {
                "id": task_id,
                "contract_task_id": task_id,
                "claimed_result": deepcopy(result),
                "prompt": _QUESTIONS[task_id][question_variant].format(
                    insert_key=data["tree"]["insert_key"]
                ),
                "points": plan["points"],
                "answer": answer,
                "marking": [
                    {
                        "points": points,
                        "criterion": form.format(
                            **_rubric_values(task_id, result, answer)
                        ),
                    }
                    for points, form in zip(credits, criterion_forms, strict=True)
                ],
                "material_ids": [
                    "reseau" if task_id in ("1a", "1b", "1c", "1d") else "arbre"
                ],
                "curriculum_codes": [plan["required_curriculum_code"]],
                "operation": plan["operation"],
                "difficulty": plan["difficulty"],
                "estimated_minutes": plan["estimated_minutes"],
                "verification": {
                    "kind": "graph_tree",
                    "contract": data,
                    "task_id": task_id,
                    "expected": deepcopy(result),
                },
            }
        )
    return {
        "id": "1",
        "title": title,
        "context": context,
        "topics": task["topics"],
        "minutes": task["minutes"],
        "target_points": task["technical_points"],
        "materials": [],
        "questions": questions,
    }
