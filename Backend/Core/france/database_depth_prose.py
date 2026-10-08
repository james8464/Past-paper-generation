"""Finite French wording and exact credit for the V2 written database case."""

from __future__ import annotations

import json
from decimal import Decimal
from hashlib import sha256

from Backend.Core.france.database_binding import database_materials
from Backend.Core.france.database_depth_contract import DatabaseDepthContract
from Backend.Core.france.nsi import NSIExercise

DATABASE_DEPTH_PROSE_VERSION = "fr-nsi-database-prose-v2"
_IDS = tuple(f"2{letter}" for letter in "abcdefghij")
_MINUTES = (6, 6, 7, 7, 8, 8, 7, 7, 7, 7)
_SCENES = {
    "atelier": (
        "Analyse d'une base d'incidents",
        "Un atelier suit les incidents déclarés par ses agents.",
    ),
    "service": (
        "Étude d'un registre d'incidents",
        "Un service consigne les incidents signalés par ses agents.",
    ),
}
_QUESTIONS = {
    "2a": (
        "Identifiez les clés primaires des trois relations et les deux clés étrangères de incident. Expliquez le rôle de l'une de ces clés étrangères.",
        "Nommez les clés primaires et les références étrangères de incident ; précisez ce que garantit l'une de ces références.",
    ),
    "2b": (
        "On souhaite insérer un incident 107 avec id_agent = 999 et id_cat = 1. Cette insertion est-elle valide ? Justifiez votre réponse.",
        "Un nouvel incident 107 référence l'agent 999 et la catégorie 1. Déterminez si la base doit accepter cette ligne et pourquoi.",
    ),
    "2c": (
        "Retrouvez la catégorie de l'incident 101. Indiquez les deux attributs à rapprocher pour établir ce résultat.",
        "À partir des tableaux, donnez le libellé de catégorie de l'incident 101 et expliquez la correspondance utilisée.",
    ),
    "2d": (
        "La requête de jointure fournie est fautive. Identifiez la condition incorrecte et montrez sur l'incident 101 en quoi le résultat diffère du résultat attendu.",
        "Expliquez l'erreur de liaison dans la requête affichée, puis comparez la catégorie obtenue pour l'incident 101 à sa vraie catégorie.",
    ),
    "2e": (
        "Écrivez la requête corrigée qui renvoie l'identifiant et le libellé de catégorie de chaque incident, dans l'ordre des identifiants. Donnez le nombre de lignes obtenues.",
        "Corrigez la jointure SQL pour lister les incidents et leur catégorie par identifiant croissant ; combien de résultats produit-elle ?",
    ),
    "2f": (
        "Écrivez une requête qui compte les incidents de chaque catégorie, y compris une catégorie sans incident. Donnez les trois effectifs obtenus.",
        "Calculez en SQL le nombre d'incidents pour chacune des trois catégories, en conservant les catégories vides ; indiquez les effectifs.",
    ),
    "2g": (
        "Écrivez une instruction SQL qui clôt uniquement l'incident 101. Indiquez le nombre de lignes modifiées et le nouveau nombre d'incidents clos.",
        "Mettez à jour le seul incident 101 pour que son statut devienne clos ; précisez l'effet de la requête et le total clos après modification.",
    ),
    "2h": (
        "À partir de l'état initial des six incidents, proposez une assertion qui met en évidence le défaut de nombre_clos. Indiquez la valeur réellement renvoyée par la fonction affichée.",
        "Écrivez un test par assertion du nombre initial d'incidents clos, puis comparez l'attendu au résultat du programme fourni.",
    ),
    "2i": (
        "Corrigez la condition de la fonction nombre_clos. Justifiez son résultat sur les six incidents initiaux.",
        "Quelle condition de nombre_clos faut-il remplacer ? Donnez la valeur calculée après correction sur les données initiales.",
    ),
    "2j": (
        "Quel résultat la fonction corrigée doit-elle donner pour une liste vide ? Expliquez pourquoi ce cas limite est utile dans un test.",
        "Testez la fonction corrigée sur une liste ne contenant aucun incident. Donnez l'attendu et justifiez ce cas limite.",
    ),
}


def database_depth_catalogue_digest() -> str:
    return sha256(
        json.dumps(
            {
                "version": DATABASE_DEPTH_PROSE_VERSION,
                "scenes": _SCENES,
                "questions": _QUESTIONS,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def database_depth_selection_schema(contract: DatabaseDepthContract) -> dict:
    if contract.to_dict()["task_ids"] != list(_IDS):
        raise ValueError("Incompatible database depth contract")

    def forms(suffix: str) -> dict:
        return {
            "type": "object",
            "properties": {
                task_id: {
                    "type": "string",
                    "enum": [f"{task_id}-{suffix}1", f"{task_id}-{suffix}2"],
                }
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


def validate_database_depth_selection(
    contract: DatabaseDepthContract, selection: dict
) -> dict:
    schema = database_depth_selection_schema(contract)
    if not isinstance(selection, dict) or set(selection) != set(schema["properties"]):
        raise ValueError("Database depth selection outside schema")
    if selection["scene_id"] not in _SCENES:
        raise ValueError("Unknown database depth scene")
    for field in ("question_forms", "rubric_forms"):
        chosen = selection[field]
        rules = schema["properties"][field]["properties"]
        if not isinstance(chosen, dict) or set(chosen) != set(rules):
            raise ValueError("Database depth selection fields mismatch")
        if any(chosen[task_id] not in rule["enum"] for task_id, rule in rules.items()):
            raise ValueError("Unknown database depth wording ID")
    return selection


def _credit_profile(total: str) -> tuple[str, ...]:
    if total not in {"5.5", "6", "6.5"}:
        raise ValueError("Unsupported database depth allocation")
    extras = {"2e"}
    if total in {"6", "6.5"}:
        extras.add("2f")
    if total == "6.5":
        extras.add("2i")
    return tuple("1" if task_id in extras else "0.5" for task_id in _IDS)


def _answer(task_id: str, data: dict) -> str:
    expected = data["expected"]
    categories = {row[0]: row[1] for row in data["tables"]["categorie"]["rows"]}
    if task_id == "2a":
        return (
            "Clés primaires : agent.id_agent, categorie.id_cat et incident.id_incident. "
            "Dans incident, id_agent référence agent.id_agent et id_cat référence "
            "categorie.id_cat ; une clé étrangère interdit une référence absente."
        )
    if task_id == "2b":
        return "L'insertion est refusée : id_agent = 999 n'existe pas dans agent ; la clé étrangère serait violée."
    if task_id == "2c":
        return f"L'incident 101 a la catégorie {categories[2]} : incident.id_cat = categorie.id_cat."
    if task_id == "2d":
        wrong = expected["faulty_join"][0][1]
        return (
            "La condition fautive utilise incident.id_agent = categorie.id_cat au lieu "
            f"de incident.id_cat = categorie.id_cat. Pour 101, elle donne {wrong}, "
            f"au lieu de {categories[2]}."
        )
    if task_id == "2e":
        return (
            "La jointure corrigée est :\n```sql\n" + data["correct_sql"] + "\n```\n"
            f"Elle renvoie {len(expected['correct_join'])} lignes, une par incident."
        )
    if task_id == "2f":
        counts = ", ".join(
            f"{label} : {count}" for _, label, count in expected["category_counts"]
        )
        return (
            "La requête est :\n```sql\n"
            + data["group_sql"]
            + "\n```\nEffectifs : "
            + counts
            + "."
        )
    if task_id == "2g":
        return (
            "La mise à jour est :\n```sql\n" + data["update_sql"] + "\n```\n"
            f"{expected['updated_count']} ligne est modifiée ; "
            f"{expected['closed_after_update']} incidents sont alors clos."
        )
    if task_id == "2h":
        statuses = [row[3] for row in data["tables"]["incident"]["rows"]]
        values = ", ".join("{'statut': '" + status + "'}" for status in statuses)
        return (
            f"assert nombre_clos([{values}]) == {expected['closed_before']}\n"
            f"La fonction fournie renvoie {expected['faulty_python_count']} : ce test échoue."
        )
    if task_id == "2i":
        return (
            "Remplacer la condition par `incident['statut'] == 'clos'`. "
            f"La fonction corrigée compte {expected['closed_before']} incidents clos "
            f"sur les six lignes, au lieu des {expected['faulty_python_count']} ouverts."
        )
    if task_id == "2j":
        return (
            "Pour une liste vide, le résultat attendu est "
            f"{expected['empty_closed_count']} : aucune itération ne modifie total. "
            "Ce test vérifie le cas sans incident, sans accès à un premier élément."
        )
    raise ValueError("Unknown database depth task")


def _marking(task_id: str, points: str, data: dict, variant: int) -> list[dict]:
    prefix = "Points pour " if variant == 1 else "Vérifier "
    if points == "1":
        expected = data["expected"]
        pieces = {
            "2e": (
                "la condition incident.id_cat = categorie.id_cat.",
                f"le tri et les {len(expected['correct_join'])} lignes obtenues.",
            ),
            "2f": (
                "la jointure gauche, le groupement et COUNT(incident.id_incident).",
                "les trois effectifs exacts : 2, 3 et 1.",
            ),
            "2i": (
                "la condition statut == 'clos'.",
                f"la justification du résultat {expected['closed_before']} sur les six lignes.",
            ),
        }[task_id]
        return [{"points": "0.5", "criterion": prefix + piece} for piece in pieces]
    return [{"points": points, "criterion": prefix + _answer(task_id, data)}]


def render_database_depth_candidate(
    contract: DatabaseDepthContract, selection: dict, task_specs: list[dict]
) -> dict:
    validate_database_depth_selection(contract, selection)
    if not isinstance(task_specs, list) or len(task_specs) != len(_IDS):
        raise ValueError("Database depth blueprint size mismatch")
    if any(not isinstance(plan, dict) for plan in task_specs):
        raise ValueError("Database depth blueprint malformed")
    total = str(
        sum(
            (Decimal(plan.get("points", "0")) for plan in task_specs), Decimal(0)
        ).normalize()
    )
    if (
        [plan.get("id") for plan in task_specs] != list(_IDS)
        or total not in {"5.5", "6", "6.5"}
        or tuple(plan.get("points") for plan in task_specs) != _credit_profile(total)
        or tuple(plan.get("estimated_minutes") for plan in task_specs) != _MINUTES
        or any(not plan.get("required_curriculum_code") for plan in task_specs)
    ):
        raise ValueError("Database depth blueprint credit or order mismatch")
    data = contract.to_dict()
    title, lead = _SCENES[selection["scene_id"]]
    context = (
        lead + " Les trois tableaux représentent l'état initial des données. "
        "Chaque relation possède une clé primaire indiquée par son nom ; dans incident, "
        "id_agent et id_cat sont des clés étrangères. Toutes les questions, sauf la "
        "mise à jour demandée en 2g, portent sur cet état initial. La requête suivante "
        "est erronée :\n\n```sql\n" + data["faulty_sql"] + "\n```\n\n"
        "La fonction suivante est censée compter les incidents clos. Son argument "
        "est une liste de dictionnaires possédant la clé statut :\n\n```python\n"
        + data["faulty_python"]
        + "\n```"
    )
    questions = []
    for task_id, plan in zip(_IDS, task_specs, strict=True):
        answer = _answer(task_id, data)
        question_variant = int(selection["question_forms"][task_id][-1]) - 1
        rubric_variant = int(selection["rubric_forms"][task_id][-1])
        questions.append(
            {
                "id": task_id,
                "prompt": _QUESTIONS[task_id][question_variant],
                "points": plan["points"],
                "answer": answer,
                "marking": _marking(task_id, plan["points"], data, rubric_variant),
                "material_ids": ["agent", "categorie", "incident"],
                "curriculum_codes": [plan["required_curriculum_code"]],
                "operation": plan["operation"],
                "difficulty": plan["difficulty"],
                "estimated_minutes": plan["estimated_minutes"],
                "verification": {
                    "kind": "database_depth_contract",
                    "contract": data,
                    "task_id": task_id,
                    "expected": data["expected"],
                },
            }
        )
    candidate = {
        "id": "2",
        "title": title,
        "context": context,
        "topics": ["bases-donnees", "langages-programmation"],
        "minutes": 70,
        "target_points": total,
        "materials": database_materials(contract),
        "questions": questions,
    }
    NSIExercise.model_validate(candidate)
    return candidate
