"""V19 finite French reasoning over the unchanged V2 incident facts."""

from __future__ import annotations

import json
import sqlite3
from decimal import Decimal
from hashlib import sha256

from Backend.Core.france.database_binding import database_materials
from Backend.Core.france.database_depth_contract import DatabaseDepthContract
from Backend.Core.france.nsi import NSIExercise

DATABASE_REASONING_PROSE_VERSION = "fr-nsi-database-prose-v3"
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
        "Partie A — intégrité et jointures. Identifiez les trois clés primaires et les deux clés étrangères de incident. Expliquez ce qu'empêche l'une de ces références.",
        "Partie A — intégrité et jointures. Donnez les clés primaires, puis les références de incident vers agent et categorie ; quel défaut évitent-elles ?",
    ),
    "2b": (
        "L'incident 107 doit référencer id_agent = 999 et id_cat = 1. Expliquez le refus de cette insertion et proposez un id_agent existant qui la rendrait valide.",
        "On essaie d'ajouter 107 avec l'agent 999 et la catégorie 1. Pourquoi cette ligne échoue-t-elle ? Remplacez 999 par une clé d'agent recevable.",
    ),
    "2c": (
        "Pour les incidents 101 et 102, retrouvez id_cat et le libellé obtenu par la jointure correcte. Indiquez les attributs rapprochés.",
        "Suivez les lignes 101 et 102 jusqu'à categorie : donnez leurs deux libellés et la condition de jointure utilisée.",
    ),
    "2d": (
        "Exécutez mentalement la condition de jointure fautive pour 101 et 102. Comparez ses deux libellés aux vrais libellés et indiquez la condition à corriger.",
        "La jointure affichée lie le mauvais attribut. Donnez ses libellés pour 101 et 102, puis leurs libellés corrects et la bonne condition.",
    ),
    "2e": (
        "Partie B — construire et vérifier les requêtes. Écrivez la jointure corrigée qui renvoie identifiant et libellé par identifiant croissant ; expliquez pourquoi elle produit six lignes.",
        "Partie B — construire et vérifier les requêtes. Corrigez et triez la requête de jointure ; justifiez le nombre de lignes obtenu sur l'état initial.",
    ),
    "2f": (
        "Écrivez une requête qui compte les incidents pour chaque catégorie, puis donnez les trois effectifs initiaux. Hypothèse distincte : on insère ensuite une catégorie 4 sans incident. Expliquez pourquoi votre requête lui donne zéro.",
        "Calculez en SQL les effectifs de toutes les catégories initiales. Dans une hypothèse séparée, une catégorie 4 sans incident est créée : expliquez son effectif nul et la jointure nécessaire.",
    ),
    "2g": (
        "Partie C — état et débogage. Écrivez la mise à jour qui clôt le seul incident 101 ; comparez le nombre d'incidents clos avant et après cette opération.",
        "Partie C — état et débogage. Clôturez uniquement 101 par SQL, puis indiquez le total clos sur l'état initial et après modification.",
    ),
    "2h": (
        "Sur l'état initial des six incidents, écrivez une assertion qui devrait vérifier nombre_clos. Tracez la valeur renvoyée par la fonction fautive et indiquez si l'assertion passe.",
        "Proposez un test par assertion du nombre initial d'incidents clos ; calculez le retour réel du code affiché et concluez sur ce test.",
    ),
    "2i": (
        "Corrigez la condition de nombre_clos. Donnez son retour sur les six incidents initiaux, puis sur le même ensemble après la mise à jour de 2g.",
        "Quelle comparaison corrige nombre_clos ? Calculez le résultat corrigé avant et après la seule clôture de 101.",
    ),
    "2j": (
        "Quel résultat nombre_clos corrigée renvoie-t-elle sur une liste vide ? Expliquez pourquoi ce test n'a besoin d'accéder à aucun premier élément.",
        "Testez la fonction corrigée sans incident : donnez le résultat attendu et justifiez que la boucle reste sûre sur cette entrée.",
    ),
}
_CRITERIA = {
    "2a": (
        "les clés primaires et les deux références étrangères.",
        "la garantie d'intégrité d'une référence.",
    ),
    "2b": (
        "le refus de l'agent 999 absent.",
        "un id_agent existant et la validité de remplacement.",
    ),
    "2c": (
        "les id_cat et catégories exactes de 101 et 102.",
        "la condition incident.id_cat = categorie.id_cat.",
    ),
    "2d": (
        "les deux résultats de la jointure fautive et leur écart.",
        "la bonne condition et les deux catégories réelles.",
    ),
    "2e": (
        "la jointure corrigée et le tri croissant.",
        "les six lignes, une par incident.",
    ),
    "2f": (
        "la jointure gauche, le groupement et les effectifs initiaux.",
        "la catégorie 4 hypothétique conservée avec le compte 0.",
    ),
    "2g": (
        "la mise à jour limitée à l'incident 101.",
        "deux clos avant et trois après cette mise à jour.",
    ),
    "2h": (
        "l'assertion du résultat initial attendu, deux.",
        "le retour fautif quatre et l'échec de l'assertion.",
    ),
    "2i": (
        "la condition statut == 'clos'.",
        "deux avant et trois après la mise à jour.",
    ),
    "2j": (
        "le retour zéro sur une liste vide.",
        "l'absence d'accès au premier élément de la liste.",
    ),
}


def database_reasoning_catalogue_digest() -> str:
    payload = {
        "version": DATABASE_REASONING_PROSE_VERSION,
        "scenes": _SCENES,
        "questions": _QUESTIONS,
        "criteria": _CRITERIA,
    }
    return sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


def database_reasoning_selection_schema(contract: DatabaseDepthContract) -> dict:
    if contract.to_dict()["task_ids"] != list(_IDS):
        raise ValueError("Incompatible database reasoning contract")

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


def validate_database_reasoning_selection(
    contract: DatabaseDepthContract, selection: dict
) -> None:
    schema = database_reasoning_selection_schema(contract)
    if not isinstance(selection, dict) or set(selection) != set(schema["properties"]):
        raise ValueError("Database reasoning selection outside schema")
    if selection["scene_id"] not in _SCENES:
        raise ValueError("Unknown database reasoning scene")
    for field in ("question_forms", "rubric_forms"):
        chosen = selection[field]
        rules = schema["properties"][field]["properties"]
        if not isinstance(chosen, dict) or set(chosen) != set(rules):
            raise ValueError("Database reasoning selection fields mismatch")
        if any(chosen[task_id] not in rule["enum"] for task_id, rule in rules.items()):
            raise ValueError("Unknown database reasoning wording ID")


def _hypothetical_empty_category_count(data: dict) -> int:
    connection = sqlite3.connect(":memory:")
    try:
        connection.executescript(
            "CREATE TABLE categorie(id_cat INTEGER PRIMARY KEY, libelle TEXT);"
            "CREATE TABLE incident(id_incident INTEGER PRIMARY KEY, id_cat INTEGER);"
        )
        connection.executemany(
            "INSERT INTO categorie VALUES (?, ?)",
            [(row[0], row[1]) for row in data["tables"]["categorie"]["rows"]],
        )
        connection.executemany(
            "INSERT INTO incident VALUES (?, ?)",
            [(row[0], row[2]) for row in data["tables"]["incident"]["rows"]],
        )
        connection.execute("INSERT INTO categorie VALUES (4, 'Nouvelle')")
        rows = connection.execute(data["group_sql"]).fetchall()
        if [row[2] for row in rows[:3]] != [2, 3, 1] or len(rows) != 4:
            raise ValueError("Incompatible database reasoning aggregation")
        return rows[3][2]
    finally:
        connection.close()


def _answer(task_id: str, data: dict) -> str:
    expected = data["expected"]
    labels = {row[0]: row[1] for row in data["tables"]["categorie"]["rows"]}
    if task_id == "2a":
        return "Clés primaires : agent.id_agent, categorie.id_cat, incident.id_incident. incident.id_agent et incident.id_cat référencent les deux autres tables ; une référence absente est interdite."
    if task_id == "2b":
        return "L'agent 999 n'existe pas : l'insertion viole la clé étrangère. Un agent existant, par exemple id_agent = 1, rend cette référence valide."
    if task_id == "2c":
        return (
            "Jointure incident.id_cat = categorie.id_cat : "
            f"101 : {labels[2]} (id_cat = 2) ; "
            f"102 : {labels[3]} (id_cat = 3)."
        )
    if task_id == "2d":
        return (
            f"La condition fautive incident.id_agent = categorie.id_cat donne 101 : {labels[1]} et 102 : {labels[1]}. "
            f"La bonne condition incident.id_cat = categorie.id_cat donne 101 : {labels[2]} et 102 : {labels[3]}."
        )
    if task_id == "2e":
        return (
            "La requête corrigée est :\n```sql\n"
            + data["correct_sql"]
            + "\n```\nElle produit six lignes, une par incident."
        )
    if task_id == "2f":
        counts = ", ".join(
            f"{label} : {count}" for _, label, count in expected["category_counts"]
        )
        empty_count = _hypothetical_empty_category_count(data)
        return (
            "La requête est :\n```sql\n" + data["group_sql"] + "\n```\n"
            f"État initial : {counts}. Dans l'hypothèse séparée, catégorie 4 : {empty_count} ; "
            "LEFT JOIN conserve cette catégorie et COUNT(incident.id_incident) ignore sa ligne sans incident."
        )
    if task_id == "2g":
        return (
            "La mise à jour est :\n```sql\n" + data["update_sql"] + "\n```\n"
            f"Avant : {expected['closed_before']} incidents clos ; après : {expected['closed_after_update']} incidents clos."
        )
    if task_id == "2h":
        return (
            "Sur les six lignes initiales : assert nombre_clos(incidents) == 2. "
            f"La fonction fautive renvoie {expected['faulty_python_count']} ; l'assertion échoue."
        )
    if task_id == "2i":
        return (
            "Remplacer la condition par incident['statut'] == 'clos'. "
            f"La fonction corrigée renvoie {expected['closed_before']} avant la mise à jour "
            f"et renvoie {expected['closed_after_update']} après."
        )
    if task_id == "2j":
        return "Sur une liste vide, la fonction corrigée renvoie 0 : la boucle ne commence pas, et aucun premier élément n'est consulté."
    raise ValueError("Unknown database reasoning task")


def _credit_profile(total: str) -> tuple[str, ...]:
    if total not in {"5.5", "6", "6.5"}:
        raise ValueError("Unsupported database reasoning allocation")
    extras = {"2e"}
    if total in {"6", "6.5"}:
        extras.add("2f")
    if total == "6.5":
        extras.add("2i")
    return tuple("1" if task_id in extras else "0.5" for task_id in _IDS)


def _marking(task_id: str, points: str, variant: int) -> list[dict]:
    prefix = "Points pour " if variant == 1 else "Vérifier "
    half = format((Decimal(points) / 2).normalize(), "f")
    return [
        {"points": half, "criterion": prefix + criterion}
        for criterion in _CRITERIA[task_id]
    ]


def render_database_reasoning_candidate(
    contract: DatabaseDepthContract, selection: dict, task_specs: list[dict]
) -> dict:
    validate_database_reasoning_selection(contract, selection)
    if not isinstance(task_specs, list) or len(task_specs) != len(_IDS):
        raise ValueError("Database reasoning blueprint size mismatch")
    if any(not isinstance(plan, dict) for plan in task_specs):
        raise ValueError("Database reasoning blueprint malformed")
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
        raise ValueError("Database reasoning blueprint credit or order mismatch")
    data = contract.to_dict()
    title, lead = _SCENES[selection["scene_id"]]
    context = (
        lead
        + " Les trois tableaux représentent l'état initial des données. Les contraintes d'intégrité (unicité et références entre relations) sont en vigueur. "
        "Toutes les questions, sauf la mise à jour demandée en 2g et l'hypothèse explicitement séparée en 2f, portent sur cet état initial. "
        "La requête suivante est erronée :\n\n```sql\n"
        + data["faulty_sql"]
        + "\n```\n\nOn note incidents la liste des six lignes de la table incident, chacune sous forme de dictionnaire avec la clé statut ; cette liste est reconstruite après la mise à jour de 2g. La fonction suivante est censée compter les incidents clos :\n\n```python\n"
        + data["faulty_python"]
        + "\n```"
    )
    questions = []
    for task_id, plan in zip(_IDS, task_specs, strict=True):
        question_variant = int(selection["question_forms"][task_id][-1]) - 1
        rubric_variant = int(selection["rubric_forms"][task_id][-1])
        questions.append(
            {
                "id": task_id,
                "prompt": _QUESTIONS[task_id][question_variant],
                "points": plan["points"],
                "answer": _answer(task_id, data),
                "marking": _marking(task_id, plan["points"], rubric_variant),
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
