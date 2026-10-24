"""V29 complete recursive construction over the immutable printed E1 tree."""

import json
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256

from Backend.Core.france.graph_two_outage_prose import (
    GRAPH_TWO_OUTAGE_PROSE_VERSION,
    graph_two_outage_catalogue_digest,
    render_graph_two_outage_candidate,
)

TREE_CONSTRUCTION_VERSION = "fr-nsi-tree-construction-prose-v1"
INTERVAL_CODE = """def compter_intervalle(
    noeud, borne_min, borne_max
):
    if noeud is None:
        return 0
    if noeud.valeur < borne_min:
        return compter_intervalle(
            noeud.droite, borne_min, borne_max)
    if noeud.valeur > borne_max:
        return compter_intervalle(
            noeud.gauche, borne_min, borne_max)
    gauche = compter_intervalle(
        noeud.gauche, borne_min, borne_max)
    droite = compter_intervalle(
        noeud.droite, borne_min, borne_max)
    return 1 + gauche + droite"""
INTERVAL_PROMPT = (
    "On travaille sur l'ABR après l'insertion de la question 1h. "
    "Un arbre vide est représenté par None ; chaque nœud possède valeur, gauche "
    "et droite. Les clés sont des entiers distincts. "
    "Écrivez entièrement la fonction récursive compter_intervalle(noeud, borne_min, "
    "borne_max), qui renvoie le nombre de clés comprises entre les deux bornes "
    "incluses, avec borne_min <= borne_max. Ne modifiez pas l'arbre. "
    "Si la clé courante est inférieure à borne_min, ne visitez pas son sous-arbre "
    "gauche ; si elle est supérieure à borne_max, ne visitez pas son sous-arbre "
    "droit. Justifiez pourquoi ces deux exclusions sont correctes. "
    "Donnez le résultat pour les bornes {low} et {high}, en indiquant les clés comptées."
)
INTERVAL_CRITERIA = (
    "Le cas de l'arbre vide renvoie zéro, sans accès à ses attributs.",
    "Les deux branches hors intervalle sont récursives et justifiées par l'ordre strict de l'ABR.",
    "Dans l'intervalle inclusif, le résultat ajoute un aux deux comptes récursifs, sans modifier l'arbre.",
    "Le résultat numérique et toutes les clés comptées sur l'arbre après insertion sont exacts.",
)


def tree_blueprint(blueprint: list[dict]) -> list[dict]:
    result = deepcopy(blueprint)
    transfer = Decimal("1") - Decimal(result[9]["points"])
    result[5]["points"] = str(Decimal(result[5]["points"]) - transfer)
    result[6]["estimated_minutes"] -= 4
    result[9].update(points="1", estimated_minutes=10, operation="design", difficulty=4)
    return result


def tree_construction_expected(data: dict) -> dict:
    """Independent flat-key oracle, distinct from the recursive solution."""
    keys = sorted(
        [row[0] for row in data["tree"]["rows"]] + [data["tree"]["insert_key"]]
    )
    low, high = keys[1], keys[-2]
    included = [key for key in keys if low <= key <= high]
    return {
        "bounds": [low, high],
        "included_keys": included,
        "count": len(included),
        "empty_count": 0,
        "boundary_counts": [[key, sum(value == key for value in keys)] for key in keys],
        "app_owned_code_sha256": sha256(INTERVAL_CODE.encode()).hexdigest(),
    }


def graph_catalogue_identity(prompt_version: str) -> tuple[str, str]:
    if prompt_version == "fr-nsi-written-2027-v31":
        from Backend.Core.france.route_task_families import family_catalogue_identity

        return family_catalogue_identity()
    if prompt_version == "fr-nsi-written-2027-v30":
        from Backend.Core.france.route_selection_authoring import (
            route_catalogue_identity,
        )

        return route_catalogue_identity()
    if prompt_version != "fr-nsi-written-2027-v29":
        return GRAPH_TWO_OUTAGE_PROSE_VERSION, graph_two_outage_catalogue_digest()
    payload = {
        "version": TREE_CONSTRUCTION_VERSION,
        "base": graph_two_outage_catalogue_digest(),
        "prompt": INTERVAL_PROMPT,
        "code": INTERVAL_CODE,
        "criteria": INTERVAL_CRITERIA,
    }
    return TREE_CONSTRUCTION_VERSION, sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


def render_graph_candidate(contract, selection, task_specs, prompt_version):
    if prompt_version == "fr-nsi-written-2027-v31":
        from Backend.Core.france.route_task_families import render_family_candidate

        return render_family_candidate(contract, selection, task_specs)
    if prompt_version == "fr-nsi-written-2027-v30":
        from Backend.Core.france.route_selection_authoring import render_route_candidate

        return render_route_candidate(contract, selection, task_specs)
    if prompt_version != "fr-nsi-written-2027-v29":
        return render_graph_two_outage_candidate(contract, selection, task_specs)
    from Backend.Core.france.pipeline import _tasks_for_seed_v25

    data = contract.to_dict()
    legacy = _tasks_for_seed_v25(data["seed"])[0]["question_blueprint"]
    if task_specs != tree_blueprint(legacy):
        raise ValueError("Tree construction blueprint mismatch")
    raw = render_graph_two_outage_candidate(contract, selection, legacy)
    for question, spec in zip(raw["questions"], task_specs, strict=True):
        for field in ("points", "estimated_minutes", "operation", "difficulty"):
            question[field] = spec[field]
    if Decimal(task_specs[5]["points"]) == Decimal("0.5"):
        marks = raw["questions"][5]["marking"]
        raw["questions"][5]["marking"] = [
            {
                "points": "0.25",
                "criterion": marks[0]["criterion"] + " " + marks[1]["criterion"],
            },
            {
                "points": "0.25",
                "criterion": marks[2]["criterion"] + " " + marks[3]["criterion"],
            },
        ]
    expected = tree_construction_expected(data)
    low, high = expected["bounds"]
    raw["questions"][9].update(
        prompt=INTERVAL_PROMPT.format(low=low, high=high),
        answer=(
            "```python\n" + INTERVAL_CODE + "\n```\n"
            "Si la clé courante est trop petite, toutes les clés de son sous-arbre gauche "
            "sont encore plus petites ; symétriquement, un sous-arbre droit ne peut pas "
            "contenir de clé admissible quand la clé courante est trop grande. "
            "Aux bornes, la clé est comptée. Chaque appel porte sur un sous-arbre strict : "
            "la récursion termine sur un arbre fini. "
            f"Après insertion : clés {expected['included_keys']}, résultat {expected['count']}."
        ),
        marking=[{"points": "0.25", "criterion": c} for c in INTERVAL_CRITERIA],
        verification={
            "kind": "tree_construction_contract",
            "contract": data,
            "task_id": "1j",
            "expected": expected,
        },
    )
    return raw
