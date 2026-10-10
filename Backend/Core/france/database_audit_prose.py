"""Finite French questions and working surfaces for the V21 incident audit."""

from __future__ import annotations

import json
from decimal import Decimal
from hashlib import sha256

from Backend.Core.france.database_audit_contract import DatabaseAuditContract
from Backend.Core.france.database_binding import database_materials
from Backend.Core.france.nsi import NSIExercise

DATABASE_AUDIT_PROSE_VERSION = "fr-nsi-database-audit-prose-v1"
_IDS = tuple(f"2{letter}" for letter in "abcdefghij")
_MINUTES = (6, 6, 7, 7, 8, 8, 7, 7, 7, 7)
_PROFILES = {
    "5.5": ("0.25", "0.5", "0.5", "0.5", "0.75", "1", "0.5", "0.5", "0.75", "0.25"),
    "6": ("0.25", "0.5", "0.75", "0.5", "0.75", "1", "0.75", "0.5", "0.75", "0.25"),
    "6.5": ("0.25", "0.5", "0.75", "0.75", "0.75", "1", "0.75", "0.75", "0.75", "0.25"),
}
_SCENES = {
    "atelier": (
        "Audit d'un registre d'incidents",
        "Un atelier suit les incidents déclarés par ses agents.",
    ),
    "service": (
        "Audit d'un service technique",
        "Un service consigne les incidents signalés par ses agents.",
    ),
}
_QUESTIONS = {
    "2a": (
        "Partie A — intégrité. Nommez les trois clés primaires et les deux clés étrangères de incident ; expliquez la contrainte qu'elles imposent.",
        "Partie A — intégrité. Repérez les clés de chaque table et les deux références de incident ; que garantit une clé étrangère ?",
    ),
    "2b": (
        "On propose, sans l'ajouter à l'état initial, l'incident 109 avec id_agent = 999 et id_cat = 1. Pourquoi l'insertion est-elle refusée ? Proposez une clé d'agent existant qui rendrait cette référence valide.",
        "L'incident hypothétique 109 désigne l'agent 999 et la catégorie 1. Justifiez le refus de cette nouvelle ligne et donnez une clé d'agent existant qui conviendrait.",
    ),
    "2c": (
        "Complétez la table de travail pour 101, 102, 107 et 108 : id_cat, libellé réel, puis libellé obtenu avec la jointure fautive affichée.",
        "Comparez, dans la table de travail, les catégories correctes et fautives des incidents 101, 102, 107 et 108.",
    ),
    "2d": (
        "À partir de deux écarts constatés en 2c, expliquez l'erreur de clé et écrivez la condition de jointure correcte.",
        "Quels contre-exemples de 2c révèlent le défaut ? Corrigez la condition ON en citant les deux attributs liés.",
    ),
    "2e": (
        "Partie B — requêtes. Écrivez une requête donnant identifiant et libellé réel de chacun des huit incidents, triés par identifiant ; justifiez les huit lignes.",
        "Partie B — requêtes. Construisez la jointure corrigée, ordonnée par identifiant d'incident, et expliquez sa cardinalité sur les huit lignes initiales.",
    ),
    "2f": (
        "Écrivez une requête donnant l'effectif par catégorie et calculez les quatre effectifs. Dans une hypothèse séparée, la catégorie 5 sans incident doit aussi figurer avec zéro : justifiez le type de jointure et le COUNT choisi.",
        "Comptez les incidents de chaque catégorie initiale. Si une catégorie 5 vide était créée séparément, comment la conserver dans le résultat avec un effectif nul ?",
    ),
    "2g": (
        "Partie C — états et débogage. Sur une copie de l'état initial S0, clôturez seulement 101 pour former S1, puis seulement 105 pour former S2. Écrivez les deux UPDATE et complétez la table de travail : identifiants modifiés et nombre de clos à chaque état.",
        "Partie C — états et débogage. Construisez S1 en clôturant 101, puis S2 en clôturant 105 sur S1. Donnez chaque UPDATE ciblé, son nombre de lignes modifiées et les trois comptes clos.",
    ),
    "2h": (
        "La fonction ci-dessous est censée compter les incidents clos :\n```python\n{faulty_python}\n```\nComplétez sa trace fautive sur S0, S1 et S2. Quelle assertion sur S0 révèle le défaut ?",
        "Tracez la fonction ci-dessous sur les trois états :\n```python\n{faulty_python}\n```\nÉcrivez une assertion sur S0 qui échoue et expliquez pourquoi.",
    ),
    "2i": (
        "Corrigez la condition de nombre_clos et complétez la trace corrigée sur S0, S1 et S2. Vérifiez que, dans chaque état, clos + ouverts = huit.",
        "Quelle condition faut-il remplacer dans nombre_clos ? Calculez son retour corrigé sur les trois états et justifiez l'invariant de huit incidents.",
    ),
    "2j": (
        "Que renvoie la fonction corrigée sur une liste vide ? Justifiez que la boucle n'accède à aucun élément absent.",
        "Testez la fonction corrigée sans incident : résultat et argument de sûreté de la boucle.",
    ),
}
_CRITERIA = {
    "2a": ("Les clés et leur garantie d'intégrité sont identifiées.",),
    "2b": (
        "La référence à l'agent 999 est refusée.",
        "Une clé d'agent existante est proposée sans modifier S0.",
    ),
    "2c": (
        "Les id_cat des quatre incidents sont exacts.",
        "Les quatre libellés réels sont exacts.",
        "Les quatre libellés fautifs sont exacts.",
    ),
    "2d": (
        "Deux contre-exemples sont cités.",
        "La condition correcte lie les deux id_cat.",
        "La clé fautive id_agent est identifiée.",
    ),
    "2e": (
        "La jointure SQL utilise les id_cat.",
        "Le tri par id_incident est écrit.",
        "Les huit lignes sont justifiées.",
    ),
    "2f": (
        "La jointure gauche est écrite.",
        "COUNT porte sur l'identifiant d'incident.",
        "Les quatre effectifs 2, 3, 2, 1 sont exacts.",
        "Le zéro de la catégorie 5 hypothétique est expliqué.",
    ),
    "2g": (
        "UPDATE cible seulement 101.",
        "UPDATE cible seulement 105 après S1.",
        "Une ligne est modifiée à chaque étape et les comptes clos 3, 4, 5 sont exacts.",
    ),
    "2h": (
        "La trace fautive donne 5, 4, 3.",
        "Une assertion de trois clos sur S0 échoue.",
        "Le défaut est relié au test sur ouvert.",
    ),
    "2i": (
        "La condition est corrigée vers clos.",
        "La trace corrigée donne 3, 4, 5.",
        "L'invariant ouvert + clos = huit est justifié.",
    ),
    "2j": ("Le résultat zéro et la boucle vide sûre sont justifiés.",),
}
_MATERIAL_IDS = {
    "2a": ["agent", "categorie", "incident"],
    "2b": ["agent", "categorie", "incident"],
    "2c": ["audit_jointure"],
    "2d": ["audit_jointure"],
    "2e": ["audit_jointure"],
    "2f": ["categorie", "incident"],
    "2g": ["audit_etats"],
    "2h": ["audit_etats", "audit_trace"],
    "2i": ["audit_trace"],
    "2j": ["audit_trace"],
}


def database_audit_catalogue_digest() -> str:
    payload = {
        "version": DATABASE_AUDIT_PROSE_VERSION,
        "scenes": _SCENES,
        "questions": _QUESTIONS,
        "criteria": _CRITERIA,
        "minutes": _MINUTES,
        "profiles": _PROFILES,
    }
    return sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


def database_audit_selection_schema(contract: DatabaseAuditContract) -> dict:
    if contract.to_dict()["task_ids"] != list(_IDS):
        raise ValueError("Incompatible incident-audit contract")

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


def validate_database_audit_selection(
    contract: DatabaseAuditContract, selection: dict
) -> None:
    schema = database_audit_selection_schema(contract)
    if not isinstance(selection, dict) or set(selection) != set(schema["properties"]):
        raise ValueError("Incident-audit selection outside schema")
    if selection["scene_id"] not in _SCENES:
        raise ValueError("Unknown incident-audit scene")
    for field in ("question_forms", "rubric_forms"):
        chosen = selection[field]
        rules = schema["properties"][field]["properties"]
        if not isinstance(chosen, dict) or set(chosen) != set(rules):
            raise ValueError("Incident-audit selection fields mismatch")
        if any(chosen[task_id] not in rule["enum"] for task_id, rule in rules.items()):
            raise ValueError("Unknown incident-audit wording ID")


def database_audit_working_materials() -> list[dict]:
    return [
        {
            "kind": "table",
            "id": "audit_jointure",
            "title": "Table de travail — jointures (2c–2e)",
            "columns": ["Incident", "id_cat", "Libellé réel", "Libellé fautif"],
            "rows": [[str(i), "…", "…", "…"] for i in (101, 102, 107, 108)],
        },
        {
            "kind": "table",
            "id": "audit_etats",
            "title": "Table de travail — états (2g–2h)",
            "columns": ["État", "ID modifié", "Clos", "Ouverts"],
            "rows": [[state, "…", "…", "…"] for state in ("S0", "S1", "S2")],
        },
        {
            "kind": "table",
            "id": "audit_trace",
            "title": "Table de travail — fonction (2i)",
            "columns": ["État", "Retour fautif", "Retour corrigé"],
            "rows": [[state, "…", "…"] for state in ("S0", "S1", "S2")],
        },
    ]


def _answer(task_id: str, data: dict) -> str:
    labels = {row[0]: row[1] for row in data["tables"]["categorie"]["rows"]}
    if task_id == "2a":
        return "Clés primaires : agent.id_agent, categorie.id_cat, incident.id_incident. Les références incident.id_agent et incident.id_cat empêchent les références absentes."
    if task_id == "2b":
        return "L'agent 999 n'existe pas : sa clé étrangère est invalide. Une référence id_agent = 1 serait valide. L'insertion de 109 est refusée et ne change pas S0."
    if task_id == "2c":
        return "; ".join(
            f"{incident} : id_cat={category}, réel={labels[category]}, fautif={labels[agent]}"
            for incident, agent, category, _ in data["tables"]["incident"]["rows"]
            if incident in (101, 102, 107, 108)
        )
    if task_id == "2d":
        return "Pour 101 et 108, id_agent et id_cat divergent : la jointure fautive utilise id_agent. Corriger par incident.id_cat = categorie.id_cat."
    if task_id == "2e":
        return (
            "Requête corrigée :\n```sql\n"
            + data["correct_sql"]
            + "\n```\nHuit lignes, une par incident initial."
        )
    if task_id == "2f":
        return (
            "Requête :\n```sql\n" + data["group_sql"] + "\n```\n"
            "Effectifs par catégorie : 2, 3, 2, 1. Une catégorie 5 hypothétique sans incident donne 0 : LEFT JOIN la conserve et COUNT(incident.id_incident) ignore NULL."
        )
    if task_id == "2g":
        return (
            "S1 :\n```sql\n" + data["update_sql_1"] + "\n```\n"
            "S2 :\n```sql\n" + data["update_sql_2"] + "\n```\n"
            "Une ligne modifiée par UPDATE : 101 puis 105 ; incidents clos S0, S1, S2 : 3, 4, 5."
        )
    if task_id == "2h":
        return "La fonction fautive compte les incidents ouverts : S0, S1, S2 donnent 5, 4, 3. Sur S0, assert nombre_clos(incidents) == 3 échoue."
    if task_id == "2i":
        return (
            "Remplacer la condition par statut == 'clos' : la fonction corrigée renvoie 3, 4, 5. "
            "Les ouverts sont 5, 4, 3 ; dans chaque état, ouverts + clos = huit."
        )
    if task_id == "2j":
        return "Sur une liste vide, la fonction corrigée renvoie 0 : aucune itération n'accède à un élément absent."
    raise ValueError("Unknown incident-audit task")


def render_database_audit_candidate(
    contract: DatabaseAuditContract, selection: dict, task_specs: list[dict]
) -> dict:
    validate_database_audit_selection(contract, selection)
    if not isinstance(task_specs, list) or len(task_specs) != len(_IDS):
        raise ValueError("Incident-audit blueprint size mismatch")
    if any(not isinstance(plan, dict) for plan in task_specs):
        raise ValueError("Incident-audit blueprint malformed")
    total = str(
        sum(
            (Decimal(plan.get("points", "0")) for plan in task_specs), Decimal(0)
        ).normalize()
    )
    if (
        [plan.get("id") for plan in task_specs] != list(_IDS)
        or total not in _PROFILES
        or tuple(plan.get("points") for plan in task_specs) != _PROFILES[total]
        or tuple(plan.get("estimated_minutes") for plan in task_specs) != _MINUTES
        or any(not plan.get("required_curriculum_code") for plan in task_specs)
    ):
        raise ValueError("Incident-audit blueprint credit or order mismatch")
    data = contract.to_dict()
    title, lead = _SCENES[selection["scene_id"]]
    context = (
        lead + " Les tables affichent uniquement l'état initial S0. "
        "L'incident 109 et la catégorie 5 ne sont que des hypothèses distinctes : ils ne figurent pas dans S0. "
        "S1 et S2 sont deux copies successives, obtenues par les mises à jour demandées en 2g. "
        "Sauf indication contraire, répondez à partir de S0. La requête suivante est fautive :\n\n```sql\n"
        + data["faulty_sql"]
        + "\n```\n\nPour la fonction de la partie C, "
        "incidents désigne une liste reconstruite pour chaque état."
    )
    questions = []
    for task_id, plan in zip(_IDS, task_specs, strict=True):
        question_variant = int(selection["question_forms"][task_id][-1]) - 1
        rubric_variant = int(selection["rubric_forms"][task_id][-1])
        criteria = _CRITERIA[task_id]
        quarters = int(Decimal(plan["points"]) * 4)
        if quarters < 1 or quarters > len(criteria):
            raise ValueError("Incident-audit rubric cannot allocate quarter-points")
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
                "prompt": _QUESTIONS[task_id][question_variant].replace(
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
                    "kind": "database_audit_contract",
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
        "materials": database_materials(contract) + database_audit_working_materials(),
        "questions": questions,
    }
    NSIExercise.model_validate(candidate)
    return candidate
