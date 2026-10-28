# finite French V24 questions and working surfaces for incident reconciliation

from __future__ import annotations

import json
from decimal import Decimal
from hashlib import sha256

from Backend.Core.france.database_binding import database_materials
from Backend.Core.france.database_reconciliation_contract import (
    DatabaseReconciliationContract,
)
from Backend.Core.france.nsi import NSIExercise

DATABASE_RECONCILIATION_PROSE_VERSION = "fr-nsi-database-reconciliation-prose-v1"
_IDS = tuple(f"2{letter}" for letter in "abcdefghijkl")
_MINUTES = (4, 5, 8, 6, 7, 8, 6, 6, 6, 6, 4, 4)
_QUARTERS = {
    "5.5": (1, 2, 2, 2, 2, 3, 2, 2, 2, 2, 1, 1),
    "6": (1, 2, 3, 2, 2, 4, 2, 2, 2, 2, 1, 1),
    "6.5": (1, 2, 3, 2, 2, 4, 3, 2, 2, 3, 1, 1),
}
_SCENES = {
    "atelier": (
        "Réconciliation d'un registre d'incidents",
        "Un atelier compare son registre d'incidents à un rapport de catégories.",
    ),
    "service": (
        "Réconciliation d'un service technique",
        "Un service technique vérifie les catégories attribuées aux incidents.",
    ),
}
_QUESTIONS = {
    "2a": (
        "Partie A — intégrité. Relevez les trois clés primaires et les deux clés étrangères ; précisez ce que garantissent ces dernières.",
        "Partie A — intégrité. Nommez les clés des trois tables et expliquez le rôle des références de incident.",
    ),
    "2b": (
        "On envisage séparément l'incident 109 avec id_agent = 999 et id_cat = 1. Pourquoi l'insertion est-elle refusée ? Donnez une clé d'agent existante qui la rendrait valide.",
        "L'incident hypothétique 109 désigne l'agent 999. Justifiez le refus puis remplacez cette référence par une clé existante.",
    ),
    "2c": (
        "Partie B — comparaison. Pour chacun des incidents 101 à 108, complétez la table de travail : id_cat, libellé réel et libellé du rapport obtenu par la jointure fautive.",
        "Partie B — comparaison. Reconstituez les huit lignes du rapport : catégorie vraie et catégorie affichée par la jointure fautive.",
    ),
    "2d": (
        "Relevez les identifiants des six incidents dont le libellé est erroné. Expliquez pourquoi les deux autres lignes ne prouvent pas que la jointure est correcte.",
        "Distinguez les six écarts des deux coïncidences dans 2c, puis identifiez la mauvaise clé de jointure.",
    ),
    "2e": (
        "Écrivez la requête corrigée donnant identifiant et vrai libellé des huit incidents, ordonnés par identifiant. Justifiez le nombre de lignes.",
        "Réparez la condition ON du rapport, conservez le tri par identifiant et expliquez pourquoi huit lignes sont obtenues.",
    ),
    "2f": (
        "Écrivez une requête comptant les incidents par catégorie et calculez les quatre effectifs. Dans une hypothèse distincte, une catégorie 5 vide doit apparaître avec zéro : justifiez LEFT JOIN et le COUNT choisi.",
        "Calculez les effectifs de S0 par catégorie. Comment conserver une catégorie 5 hypothétique sans incident dans le résultat, avec un effectif nul ?",
    ),
    "2g": (
        "Partie C — algorithme et états. Cette fonction doit compter les incidents clos de la catégorie demandée :\n```python\n{faulty_python}\n```\nSur S0 et id_cat = 2, tracez les lignes comptées et le résultat fautif.",
        "Partie C — algorithme et états. Tracez sur S0 la fonction suivante appelée avec id_cat = 2 :\n```python\n{faulty_python}\n```\nQuels incidents sont comptés, et quel résultat est retourné ?",
    ),
    "2h": (
        "Corrigez une seule condition de la fonction pour qu'elle compte la catégorie, non l'agent. Donnez le résultat corrigé sur S0.",
        "Quelle comparaison faut-il modifier dans la fonction ? Justifiez le résultat corrigé pour la catégorie 2 sur S0.",
    ),
    "2i": (
        "Sur une copie de S0, fermez seulement l'incident 101 pour obtenir S1, puis seulement 104 pour obtenir S2. Écrivez les deux UPDATE ciblés et indiquez le nombre de lignes modifiées par chacun.",
        "Construisez S1 puis S2 en fermant successivement 101 et 104. Donnez les deux instructions SQL et leurs effectifs de mise à jour.",
    ),
    "2j": (
        "Complétez la table S0/S1/S2 : nombre total de clos, résultat fautif et résultat corrigé de nombre_clos_categorie(..., 2). Expliquez les changements entre états.",
        "Tracez les trois états et les deux versions de la fonction pour la catégorie 2 ; distinguez le total global des clos du compte ciblé.",
    ),
    "2k": (
        "En S2, les deux fonctions renvoient 2. Pourquoi cet accord ne valide-t-il pas la version fautive ? Citez un état qui la réfute.",
        "Les résultats fautif et corrigé coïncident en S2. Donnez un contre-exemple parmi les autres états et concluez.",
    ),
    "2l": (
        "Que renvoie la fonction corrigée pour une liste vide ? Pourquoi sa boucle n'accède-t-elle à aucun élément absent ?",
        "Testez la fonction corrigée sur une liste vide : résultat et justification de sûreté.",
    ),
}
_CRITERIA = {
    "2a": (
        "Les clés primaires, les deux références et leur contrainte sont identifiées.",
    ),
    "2b": (
        "L'agent 999 absent rend la référence invalide.",
        "Une clé existante est proposée sans modifier S0.",
    ),
    "2c": (
        "Les huit id_cat sont exacts.",
        "Les huit libellés réels sont exacts.",
        "Les huit libellés fautifs sont exacts.",
    ),
    "2d": (
        "Les six identifiants erronés sont exacts.",
        "Les deux coïncidences et la mauvaise clé id_agent sont expliquées.",
    ),
    "2e": (
        "La jointure lie les deux id_cat.",
        "Le tri et les huit lignes sont justifiés.",
    ),
    "2f": (
        "La jointure gauche conserve les catégories.",
        "COUNT porte sur l'identifiant d'incident.",
        "Les quatre effectifs 2, 2, 2, 2 sont exacts.",
        "Le zéro de la catégorie 5 hypothétique est justifié.",
    ),
    "2g": (
        "La condition fautive compare id_agent.",
        "Les incidents 103 et 105 sont tracés.",
        "Le retour fautif vaut 2 sur S0.",
    ),
    "2h": (
        "La comparaison utilise incident['id_cat'].",
        "Le retour corrigé vaut 0 sur S0.",
    ),
    "2i": (
        "Le premier UPDATE cible seulement 101 et modifie une ligne.",
        "Le second UPDATE cible seulement 104 et modifie une ligne.",
    ),
    "2j": (
        "Les comptes globaux 4, 5, 6 sont exacts.",
        "La trace fautive donne 2, 2, 2.",
        "La trace corrigée donne 0, 1, 2.",
    ),
    "2k": ("S0 ou S1 réfute la fonction fautive malgré l'accord fortuit de S2.",),
    "2l": ("Le résultat zéro et l'absence d'itération sont justifiés.",),
}
_MATERIAL_IDS = {
    "2a": ["agent", "categorie", "incident"],
    "2b": ["agent", "categorie", "incident"],
    "2c": ["recon_jointure"],
    "2d": ["recon_jointure"],
    "2e": ["recon_jointure"],
    "2f": ["recon_effectifs"],
    "2g": ["incident"],
    "2h": ["incident"],
    "2i": ["recon_etats"],
    "2j": ["recon_etats"],
    "2k": ["recon_etats"],
    "2l": ["recon_etats"],
}


def database_reconciliation_catalogue_digest() -> str:
    payload = {
        "version": DATABASE_RECONCILIATION_PROSE_VERSION,
        "scenes": _SCENES,
        "questions": _QUESTIONS,
        "criteria": _CRITERIA,
        "minutes": _MINUTES,
        "quarters": _QUARTERS,
    }
    return sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


def database_reconciliation_selection_schema(
    contract: DatabaseReconciliationContract,
) -> dict:
    if contract.to_dict()["task_ids"] != list(_IDS):
        raise ValueError("Incompatible incident-reconciliation contract")

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


def validate_database_reconciliation_selection(
    contract: DatabaseReconciliationContract, selection: dict
) -> None:
    schema = database_reconciliation_selection_schema(contract)
    if not isinstance(selection, dict) or set(selection) != set(schema["properties"]):
        raise ValueError("Incident-reconciliation selection outside schema")
    if (
        not isinstance(selection["scene_id"], str)
        or selection["scene_id"] not in _SCENES
    ):
        raise ValueError("Unknown incident-reconciliation scene")
    for field in ("question_forms", "rubric_forms"):
        chosen = selection[field]
        rules = schema["properties"][field]["properties"]
        if not isinstance(chosen, dict) or set(chosen) != set(rules):
            raise ValueError("Incident-reconciliation selection fields mismatch")
        if any(chosen[task_id] not in rule["enum"] for task_id, rule in rules.items()):
            raise ValueError("Unknown incident-reconciliation wording ID")


def database_reconciliation_working_materials() -> list[dict]:
    return [
        {
            "kind": "table",
            "id": "recon_jointure",
            "title": "Table de travail — rapport comparé (2c–2e)",
            "columns": ["Incident", "id_cat", "Libellé réel", "Libellé affiché"],
            "rows": [[str(i), "…", "…", "…"] for i in range(101, 109)],
        },
        {
            "kind": "table",
            "id": "recon_effectifs",
            "title": "Table de travail — effectifs (2f)",
            "columns": ["Catégorie", "Effectif de S0", "Catégorie 5 hypothétique"],
            "rows": [[str(i), "…" if i < 5 else "—", "…"] for i in range(1, 6)],
        },
        {
            "kind": "table",
            "id": "recon_etats",
            "title": "Table de travail — états et fonction (2i–2k)",
            "columns": ["État", "Clos au total", "Retour fautif", "Retour corrigé"],
            "rows": [[state, "…", "…", "…"] for state in ("S0", "S1", "S2")],
        },
    ]


def _answer(task_id: str, data: dict) -> str:
    labels = {row[0]: row[1] for row in data["tables"]["categorie"]["rows"]}
    if task_id == "2a":
        return "Clés primaires : agent.id_agent, categorie.id_cat, incident.id_incident. Les deux références incident.id_agent et incident.id_cat interdisent une ligne pointant vers une clé absente."
    if task_id == "2b":
        return "L'agent 999 est absent : la clé étrangère est invalide. id_agent = 1 serait une référence existante ; l'insertion hypothétique de 109 ne change pas S0."
    if task_id == "2c":
        rows = data["tables"]["incident"]["rows"]
        return "; ".join(
            f"{incident} : id_cat={category}, réel={labels[category]}, affiché={labels[agent]}"
            for incident, agent, category, _ in rows
        )
    if task_id == "2d":
        return "Incidents erronés : 101, 102, 103, 104, 105, 106. Les lignes 107 et 108 coïncident car id_agent = id_cat = 4 ; la jointure fautive compare id_agent à categorie.id_cat."
    if task_id == "2e":
        return (
            "Requête corrigée :\n```sql\n"
            + data["correct_sql"]
            + "\n```\nHuit lignes, une par incident de S0."
        )
    if task_id == "2f":
        return (
            "Requête :\n```sql\n" + data["group_sql"] + "\n```\n"
            "Effectifs des catégories 1 à 4 : 2, 2, 2, 2. La catégorie 5 hypothétique vide donne zéro : LEFT JOIN conserve sa ligne et COUNT(incident.id_incident) ignore NULL."
        )
    if task_id == "2g":
        return "La condition fautive emploie id_agent = 2 : elle compte les incidents clos 103 et 105, donc retourne 2 sur S0, alors qu'aucun incident de catégorie 2 n'est clos."
    if task_id == "2h":
        return "Remplacer incident['id_agent'] == id_cat par incident['id_cat'] == id_cat. La fonction corrigée retourne 0 pour la catégorie 2 sur S0."
    if task_id == "2i":
        return (
            "S1 :\n```sql\n" + data["update_sql_1"] + "\n```\n"
            "S2 :\n```sql\n" + data["update_sql_2"] + "\n```\n"
            "Chaque UPDATE modifie exactement une ligne : 101, puis 104."
        )
    if task_id == "2j":
        return "S0, S1, S2 : clos au total = 4, 5, 6 ; fonction fautive = 2, 2, 2 ; fonction corrigée pour la catégorie 2 = 0, 1, 2. Chaque clôture ajoute un incident de catégorie 2."
    if task_id == "2k":
        return "L'accord en S2 est fortuit : la fonction fautive compte les agents 2, non les catégories 2. En S0 elle renvoie 2 au lieu de 0 (en S1, 2 au lieu de 1)."
    if task_id == "2l":
        return "Sur une liste vide, la fonction corrigée renvoie 0 : la boucle ne s'exécute pas et n'accède à aucun élément absent."
    raise ValueError("Unknown incident-reconciliation task")


def render_database_reconciliation_candidate(
    contract: DatabaseReconciliationContract, selection: dict, task_specs: list[dict]
) -> dict:
    validate_database_reconciliation_selection(contract, selection)
    if not isinstance(task_specs, list) or len(task_specs) != len(_IDS):
        raise ValueError("Incident-reconciliation blueprint size mismatch")
    if any(not isinstance(plan, dict) for plan in task_specs):
        raise ValueError("Incident-reconciliation blueprint malformed")
    total = str(
        sum(
            (Decimal(plan.get("points", "0")) for plan in task_specs), Decimal(0)
        ).normalize()
    )
    if (
        [plan.get("id") for plan in task_specs] != list(_IDS)
        or total not in _QUARTERS
        or tuple(int(Decimal(plan.get("points", "0")) * 4) for plan in task_specs)
        != _QUARTERS[total]
        or tuple(plan.get("estimated_minutes") for plan in task_specs) != _MINUTES
        or any(not plan.get("required_curriculum_code") for plan in task_specs)
    ):
        raise ValueError("Incident-reconciliation blueprint credit or order mismatch")
    data = contract.to_dict()
    title, lead = _SCENES[selection["scene_id"]]
    context = (
        lead + " Les tables donnent seulement l'état initial S0. "
        "L'incident 109 et la catégorie 5 sont deux hypothèses distinctes : ni l'un ni l'autre ne figure dans S0. "
        "S1 et S2 sont des copies successives obtenues uniquement par les mises à jour demandées en 2i. "
        "Sauf indication contraire, partez de S0. Le rapport suivant utilise une jointure fautive :\n\n```sql\n"
        + data["faulty_sql"]
        + "\n```"
    )
    questions = []
    for task_id, plan in zip(_IDS, task_specs, strict=True):
        variant = int(selection["question_forms"][task_id][-1]) - 1
        rubric_variant = int(selection["rubric_forms"][task_id][-1])
        criteria = _CRITERIA[task_id]
        quarters = int(Decimal(plan["points"]) * 4)
        if quarters < 1 or quarters > len(criteria):
            raise ValueError(
                "Incident-reconciliation rubric cannot allocate quarter-points"
            )
        prefix = "Points pour " if rubric_variant == 1 else "Vérifier "
        marking = [
            {"points": "0.25", "criterion": prefix + criterion}
            for criterion in criteria[: quarters - 1]
        ]
        marking.append(
            {
                "points": "0.25",
                "criterion": prefix + " ".join(criteria[quarters - 1 :]),
            }
        )
        questions.append(
            {
                "id": task_id,
                "prompt": _QUESTIONS[task_id][variant].replace(
                    "{faulty_python}", data["faulty_python"]
                ),
                "points": plan["points"],
                "answer": _answer(task_id, data),
                "marking": marking,
                "material_ids": _MATERIAL_IDS[task_id],
                "curriculum_codes": [plan["required_curriculum_code"]],
                "operation": plan["operation"],
                "difficulty": plan["difficulty"],
                "estimated_minutes": plan["estimated_minutes"],
                "verification": {
                    "kind": "database_reconciliation_contract",
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
        "materials": database_materials(contract)
        + database_reconciliation_working_materials(),
        "questions": questions,
    }
    NSIExercise.model_validate(candidate)
    return candidate
