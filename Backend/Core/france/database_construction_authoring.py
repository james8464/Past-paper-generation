# V28 app-owned construction task layered over immutable V24 incident facts

import json
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256

from Backend.Core.france.database_reconciliation_prose import (
    DATABASE_RECONCILIATION_PROSE_VERSION,
    database_reconciliation_catalogue_digest,
    render_database_reconciliation_candidate,
)


def database_catalogue_identity(prompt_version):
    if prompt_version in {
        "fr-nsi-written-2027-v28",
        "fr-nsi-written-2027-v29",
        "fr-nsi-written-2027-v30",
        "fr-nsi-written-2027-v31",
    }:
        return (
            DATABASE_CONSTRUCTION_PROSE_VERSION,
            database_construction_catalogue_digest(),
        )
    return (
        DATABASE_RECONCILIATION_PROSE_VERSION,
        database_reconciliation_catalogue_digest(),
    )


DATABASE_CONSTRUCTION_PROSE_VERSION = "fr-nsi-database-construction-prose-v1"
CONSTRUCTION_CODE = """def repartition_clos(incidents, categories):
    effectifs = {}
    for categorie in categories:
        effectifs[categorie] = 0
    for incident in incidents:
        categorie = incident['id_cat']
        if categorie in effectifs:
            if incident['statut'] == 'clos':
                effectifs[categorie] += 1
    return effectifs"""
CONSTRUCTION_PROMPT = (
    "La correction de la fonction précédente remplace id_agent par id_cat. "
    "On veut maintenant un bilan de toutes les catégories demandées. "
    "Écrivez entièrement repartition_clos(incidents, categories), sans appeler "
    "nombre_clos_categorie. incidents est une liste de dictionnaires ayant les clés "
    "id_incident, id_agent, id_cat et statut ; categories est une liste d'entiers distincts. "
    "La fonction doit renvoyer un dictionnaire associant chaque catégorie demandée "
    "à son nombre d'incidents clos, y compris zéro. Ignorez les catégories non demandées, "
    "ne modifiez pas les paramètres et parcourez incidents une seule fois. "
    "Donnez le résultat sur S0 pour categories = [1, 2, 3, 4, 5]."
)
CONSTRUCTION_CRITERIA = (
    "Un dictionnaire initialise chaque catégorie demandée à zéro, même sans incident.",
    "Un seul parcours des incidents utilise id_cat et ignore les catégories non demandées, sans modifier les paramètres.",
    "Seuls les incidents dont le statut vaut 'clos' incrémentent la bonne catégorie.",
    "Le dictionnaire est renvoyé après la boucle ; le résultat S0 est {1: 1, 2: 0, 3: 2, 4: 1, 5: 0}.",
)


INVARIANT_PROMPT = (
    "Reprenez votre fonction repartition_clos de la question 2h. "
    "On note effectifs son dictionnaire résultat. "
    "Pour une catégorie demandée c, précisez ce que représente effectifs[c] après "
    "le traitement des k premiers incidents. Expliquez pourquoi cette propriété "
    "est vraie au départ et reste vraie après un incident supplémentaire. "
    "Déduisez le résultat lorsque incidents est vide et categories vaut [2, 5]."
)
INVARIANT_ANSWER = (
    "Après k incidents, effectifs[c] est le nombre d'incidents clos de catégorie c "
    "parmi les k premiers. Pour k = 0, ce nombre vaut zéro. L'incident suivant "
    "ajoute un exactement s'il est clos et de catégorie c ; sinon le compte ne change pas. "
    "Après toute la liste, le compte demandé est donc exact. Avec une liste vide, "
    "le résultat est {2: 0, 5: 0} : l'initialisation conserve les deux catégories."
)


def database_construction_catalogue_digest() -> str:
    return sha256(
        json.dumps(
            {
                "version": DATABASE_CONSTRUCTION_PROSE_VERSION,
                "base": database_reconciliation_catalogue_digest(),
                "prompt": CONSTRUCTION_PROMPT,
                "code": CONSTRUCTION_CODE,
                "criteria": CONSTRUCTION_CRITERIA,
                "invariant_prompt": INVARIANT_PROMPT,
                "invariant_answer": INVARIANT_ANSWER,
            },
            sort_keys=True,
            ensure_ascii=False,
        ).encode()
    ).hexdigest()


def construction_blueprint(blueprint: list[dict]) -> list[dict]:
    result = deepcopy(blueprint)
    # move credit/time from repeated table tracing to independent construction
    for index in (2, 5):
        result[index]["points"] = str(
            Decimal(result[index]["points"]) - Decimal("0.25")
        )
        result[index]["estimated_minutes"] -= 2
    result[7].update(points="1", estimated_minutes=10, operation="design", difficulty=4)
    result[1].update(points="0.25", estimated_minutes=3)
    result[11].update(
        points="0.5", estimated_minutes=6, operation="justify", difficulty=4
    )
    return result


# count canonical source rows independently; never execute candidate code
def construction_expected(data: dict) -> dict:
    rows = data["tables"]["incident"]["rows"]
    categories = [1, 2, 3, 4, 5]
    prefixes = [
        [
            sum(row[2] == category and row[3] == "clos" for row in rows[:k])
            for category in categories
        ]
        for k in range(len(rows) + 1)
    ]
    return {
        **deepcopy(data["expected"]),
        "construction": {
            "categories": categories,
            "s0_counts": prefixes[-1],
            "prefix_counts": prefixes,
            "empty_categories": [2, 5],
            "empty_counts": [0, 0],
            "app_owned_code_sha256": sha256(CONSTRUCTION_CODE.encode()).hexdigest(),
        },
    }


def render_database_construction_candidate(contract, selection, task_specs):
    from Backend.Core.france.pipeline import _tasks_for_seed_v24

    legacy = _tasks_for_seed_v24(contract.to_dict()["seed"])[1]["question_blueprint"]
    if task_specs != construction_blueprint(legacy):
        raise ValueError("Construction blueprint mismatch")
    raw = render_database_reconciliation_candidate(contract, selection, legacy)
    for question, spec in zip(raw["questions"], task_specs, strict=True):
        for field in ("points", "estimated_minutes", "operation", "difficulty"):
            question[field] = spec[field]
        if question["id"] in {"2b", "2c", "2f"}:
            marking = question["marking"]
            marking[-2]["criterion"] += " " + marking[-1]["criterion"]
            marking.pop()
    question = raw["questions"][7]
    question["prompt"] = CONSTRUCTION_PROMPT
    question["answer"] = (
        "La comparaison corrigée utilise incident['id_cat'] == id_cat.\n```python\n"
        + CONSTRUCTION_CODE
        + "\n```\nSur S0 : {1: 1, 2: 0, 3: 2, 4: 1, 5: 0}. "
        "La catégorie 5 reste présente avec zéro ; aucun paramètre n'est modifié."
    )
    question["marking"] = [
        {"points": "0.25", "criterion": criterion}
        for criterion in CONSTRUCTION_CRITERIA
    ]
    raw["questions"][11].update(
        prompt=INVARIANT_PROMPT,
        answer=INVARIANT_ANSWER,
        marking=[
            {
                "points": "0.25",
                "criterion": "Le compte sur le préfixe de k incidents, son initialisation et sa conservation sont justifiés.",
            },
            {
                "points": "0.25",
                "criterion": "Le dictionnaire {2: 0, 5: 0} est donné et expliqué par l'initialisation sans parcours d'incident.",
            },
        ],
    )
    for index in (7, 11):
        raw["questions"][index]["verification"].update(
            construction_version="v28",
            expected=construction_expected(contract.to_dict()),
        )
    return raw
