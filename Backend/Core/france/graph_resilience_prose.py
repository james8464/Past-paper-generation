"""Finite French wording and exact marks for the V20 graph-resilience case."""

from __future__ import annotations

import json
from decimal import Decimal
from hashlib import sha256
from itertools import pairwise

from Backend.Core.france.graph_resilience_contract import GraphResilienceContract
from Backend.Core.france.graph_tree_binding import graph_edge_manifest
from Backend.Core.france.graph_tree_depth_prose import _answer as _v3_answer
from Backend.Core.france.graph_tree_depth_prose import graph_tree_depth_catalogue_digest

GRAPH_RESILIENCE_PROSE_VERSION = "fr-nsi-graph-resilience-prose-v1"
_IDS = tuple(f"1{letter}" for letter in "abcdefghij")
_MINUTES = (6, 6, 8, 7, 8, 7, 7, 7, 7, 7)
_PARTS = "AAAABBBCCC"
_CODES = (
    "SD-GRAPHE",
    "SD-GRAPHE",
    "ALG-GRAPHES",
    "ALG-GRAPHES",
    "ALG-GRAPHES",
    "ALG-GRAPHES",
    "ALG-GRAPHES",
    "ALG-ARBRES",
    "ALG-ARBRES",
    "ALG-ARBRES",
)
_OPERATIONS = (
    "apply",
    "analyse",
    "analyse",
    "justify",
    "apply",
    "debug",
    "justify",
    "apply",
    "analyse",
    "debug",
)
_SCENES = {
    "service": (
        "Réseau résilient et arbre de recherche",
        "Un service relie six postes par un réseau pondéré. Un arbre binaire de recherche distinct classe ses identifiants d'intervention.",
    ),
    "collecte": (
        "Trajets de collecte et continuité du réseau",
        "Une équipe de collecte relie six postes par un réseau pondéré. Un arbre binaire de recherche distinct classe ses demandes.",
    ),
}
_QUESTIONS = {
    "1a": "Quel est le degré du sommet A dans `reseau` ?",
    "1b": "Calculez le coût du détour A–C–E–F en additionnant les poids de ses liaisons.",
    "1c": "Depuis A, tracez les deux premières fixations de Dijkstra : distances provisoires et prédécesseurs connus après chacune.",
    "1d": "Déduisez un chemin de poids minimal de A à F et justifiez son coût par les liaisons parcourues.",
    "1f": "Quelle erreur provoque `parcours_largeur` ? Corrigez uniquement le nom fautif et nommez l'exception.",
    "1g": "La liaison {closed} est fermée. Sans l'emprunter, trouvez un nouveau trajet minimal de A à F et son poids. Comparez ce poids avec celui du trajet initial à partir de vos calculs.",
    "1h": "Dans l'ABR `arbre`, suivez les comparaisons pour insérer {insert_key}, puis indiquez le parent et le côté du nouveau nœud. Chaque nœud possède `valeur`, `gauche` et `droite` ; — signifie l'absence d'enfant.",
    "1i": "Après cette insertion, donnez le parcours infixe de `arbre` et expliquez pourquoi ses clés sont ordonnées.",
    "1j": "Corrigez la comparaison fautive dans `contient`, puis tracez la recherche de {insert_key} après insertion et justifiez le résultat.\n\n```python\n{search_code}\n```",
}
_CRITERIA = {
    "1a": ("le degré de A",),
    "1b": ("l'addition correcte des poids du détour A–C–E–F",),
    "1c": (
        "les distances provisoires après A",
        "les prédécesseurs après A",
        "les distances après la deuxième fixation",
        "les prédécesseurs après la deuxième fixation",
    ),
    "1d": (
        "les sommets d'un chemin minimal",
        "l'addition des poids des liaisons parcourues",
    ),
    "1f": ("l'exception NameError causée par `visin`", "le nom corrigé `voisin`"),
    "1g": (
        "l'exclusion de la liaison fermée",
        "un nouveau trajet minimal",
        "son poids calculé",
        "la comparaison correcte avec le poids initial",
    ),
    "1h": ("les clés comparées", "le parent et le côté de l'insertion"),
    "1i": (
        "l'ordre infixe après insertion",
        "la justification par la propriété de l'ABR",
    ),
    "1j": (
        "la comparaison corrigée",
        "le chemin de recherche après insertion",
        "le résultat de la recherche",
        "la justification par l'ordre de l'ABR",
    ),
}


def graph_resilience_catalogue_digest() -> str:
    payload = {
        "version": GRAPH_RESILIENCE_PROSE_VERSION,
        "scenes": _SCENES,
        "questions": _QUESTIONS,
        "criteria": _CRITERIA,
        "minutes": _MINUTES,
        "parts": _PARTS,
        "codes": _CODES,
        "operations": _OPERATIONS,
        "reused_v3_answer_catalogue_digest": graph_tree_depth_catalogue_digest(),
    }
    return sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


def graph_resilience_selection_schema(contract: GraphResilienceContract) -> dict:
    if contract.to_dict()["task_ids"] != list(_IDS):
        raise ValueError("Incompatible graph resilience contract")

    def forms(suffix: str) -> dict:
        return {
            "type": "object",
            "properties": {
                task_id: {"type": "string", "enum": [f"{task_id}-{suffix}1"]}
                for task_id in _IDS
            },
            "required": list(_IDS),
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


def validate_graph_resilience_selection(
    contract: GraphResilienceContract, selection: dict
) -> dict:
    schema = graph_resilience_selection_schema(contract)["properties"]
    if not isinstance(selection, dict) or set(selection) != set(schema):
        raise ValueError("Graph resilience selection outside schema")
    if type(selection["scene_id"]) is not str or selection["scene_id"] not in _SCENES:
        raise ValueError("Unknown graph resilience scene")
    for field in ("question_forms", "rubric_forms"):
        chosen = selection[field]
        allowed = schema[field]["properties"]
        if not isinstance(chosen, dict) or set(chosen) != set(allowed):
            raise ValueError("Graph resilience selection fields mismatch")
        if any(
            type(chosen[key]) is not str or chosen[key] not in rule["enum"]
            for key, rule in allowed.items()
        ):
            raise ValueError("Unknown graph resilience wording ID")
    return selection


def _profile(total: str) -> tuple[str, ...]:
    base = ["0.25", "0.25", "1", "0.5", "0.5", "0.5", "1", "0.5", "0.5", "0.5"]
    if total in ("6", "6.5"):
        base[4] = "1"
    if total == "6.5":
        base[9] = "1"
    return tuple(base)


def _answer(task_id: str, result: dict, facts: dict) -> str:
    if task_id == "1a":
        return f"Le degré de A est {result['degree']}."
    if task_id == "1d":
        weights = {
            frozenset((left, right)): weight
            for left, right, weight in facts["graph"]["edges"]
        }
        path = result["path"]
        addition = " + ".join(
            str(weights[frozenset((left, right))])
            for left, right in pairwise(path)
        )
        return (
            "Le chemin minimal est "
            + " → ".join(path)
            + f" ; son poids est {addition} = {result['weight']}."
        )
    if task_id == "1e":
        states = result["states"]
        return (
            "L'ordre complet est "
            + " → ".join(result["order"])
            + ". "
            + "Après A : file "
            + ", ".join(states[0]["queue"])
            + " ; découverts "
            + ", ".join(states[0]["visited"])
            + ". Après B : file "
            + ", ".join(states[1]["queue"])
            + " ; découverts "
            + ", ".join(states[1]["visited"])
            + "."
        )
    if task_id == "1g":
        return (
            "La liaison fermée est exclue. Le nouveau chemin minimal est "
            + " → ".join(result["route_after"])
            + f", de poids {result['cost_after']} ; son poids est {result['comparison']} à celui du trajet initial ({result['cost_before']})."
        )
    return _v3_answer(task_id, result, facts)


def _criteria(task_id: str, points: str) -> tuple[str, ...]:
    if task_id == "1e":
        return (
            ("l'ordre complet du parcours", "la file après le retrait de A")
            if points == "0.5"
            else (
                "l'ordre complet du parcours",
                "la file après A",
                "la file après B",
                "les sommets découverts après B",
            )
        )
    if task_id == "1j" and points == "0.5":
        return (
            "la comparaison corrigée",
            "le chemin de recherche menant à la clé insérée",
        )
    return _CRITERIA[task_id]


def render_graph_resilience_candidate(
    contract: GraphResilienceContract, selection: dict, task_specs: list[dict]
) -> dict:
    validate_graph_resilience_selection(contract, selection)
    if not isinstance(task_specs, list) or len(task_specs) != 10:
        raise ValueError("Graph resilience blueprint structure mismatch")
    totals = tuple(item.get("points") for item in task_specs if isinstance(item, dict))
    total = (
        str(sum((Decimal(value) for value in totals), Decimal()).normalize())
        if len(totals) == 10
        else ""
    )
    if (
        any(not isinstance(item, dict) for item in task_specs)
        or total not in {"5.5", "6", "6.5"}
        or totals != _profile(total)
        or [item.get("id") for item in task_specs] != list(_IDS)
        or tuple(item.get("estimated_minutes") for item in task_specs) != _MINUTES
        or "".join(item.get("part_id", "") for item in task_specs) != _PARTS
        or tuple(item.get("required_curriculum_code") for item in task_specs) != _CODES
        or tuple(item.get("operation") for item in task_specs) != _OPERATIONS
    ):
        raise ValueError("Graph resilience blueprint credit or sequence mismatch")
    facts = contract.to_dict()
    graph, tree = facts["graph"], facts["tree"]
    title, lead = _SCENES[selection["scene_id"]]
    context = (
        lead
        + " Les liaisons de `reseau` sont bidirectionnelles ; leurs poids figurent sur le graphe. "
        + "À poids égal, retenir la suite de sommets première dans l'ordre alphabétique. "
        + "Le parcours en largeur examine les voisins dans l'ordre alphabétique et marque un sommet dès son enfilage.\n\n"
        + graph_edge_manifest(graph)
        + "\n\nLe programme suivant comporte une faute :\n\n```python\n"
        + facts["debug_case"]["faulty_code"]
        + "\n```"
    )
    materials = [
        {
            "kind": "weighted_graph",
            "id": graph["id"],
            "title": "Réseau pondéré des postes",
            "nodes": graph["nodes"],
            "edges": graph["edges"],
            "directed": graph["directed"],
        },
        {
            "kind": "table",
            "id": tree["id"],
            "title": "Arbre des identifiants",
            "columns": tree["columns"],
            "rows": [
                [str(value) if value is not None else "—" for value in row]
                for row in tree["rows"]
            ],
        },
    ]
    questions = []
    for task_id, plan in zip(_IDS, task_specs, strict=True):
        result = facts["expected"][task_id]
        prompt = _QUESTIONS.get(task_id, "")
        if task_id == "1e":
            prompt = (
                "Après correction, donnez l'ordre complet du parcours en largeur et la file après le retrait de A."
                if plan["points"] == "0.5"
                else "Après correction, donnez l'ordre complet du parcours en largeur, la file après les retraits de A et B et les sommets découverts après B."
            )
        if task_id == "1j" and plan["points"] == "0.5":
            prompt = (
                "Corrigez la comparaison fautive dans `contient`, puis tracez "
                "la recherche de {insert_key} après insertion et donnez son résultat."
                "\n\n```python\n{search_code}\n```"
            )
        prompt = prompt.format(
            closed="–".join(facts["closed_edge"]),
            insert_key=tree["insert_key"],
            search_code=facts["search_code"],
        )
        criteria = _criteria(task_id, plan["points"])
        if len(criteria) != int(Decimal(plan["points"]) * 4):
            raise ValueError("Graph resilience rubric and credit disagree")
        questions.append(
            {
                "id": task_id,
                "prompt": prompt,
                "points": plan["points"],
                "answer": _answer(task_id, result, facts),
                "marking": [
                    {"points": "0.25", "criterion": "Accorder pour " + criterion + "."}
                    for criterion in criteria
                ],
                "material_ids": ["reseau"] if task_id <= "1g" else ["arbre"],
                "curriculum_codes": [plan["required_curriculum_code"]],
                "operation": plan["operation"],
                "difficulty": plan["difficulty"],
                "estimated_minutes": plan["estimated_minutes"],
                "verification": {
                    "kind": "graph_resilience_contract",
                    "contract": facts,
                    "task_id": task_id,
                    "expected": result,
                },
            }
        )
    return {
        "id": "1",
        "title": title,
        "context": context,
        "topics": ["structures-donnees", "algorithmique"],
        "minutes": 70,
        "target_points": total,
        "materials": materials,
        "questions": questions,
    }
