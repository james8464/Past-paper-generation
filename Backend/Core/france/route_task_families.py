# Task-family building blocks checked independently without running candidate code.

import json
from copy import deepcopy
from hashlib import sha256
from itertools import pairwise

from Backend.Core.france.route_selection_authoring import (
    HELPER_CODE,
    SELECTOR_CODE,
    route_selection_expected,
)

FAMILIES = ("minimum", "budget", "continuity")

BUDGET_CODE = """def trajets_admissibles(
    trajets, couts, fermees, budget
):
    indices = []
    for i in range(len(trajets)):
        if couts[i] <= budget:
            if disponible(trajets[i], fermees):
                indices.append(i)
    return indices"""

CONTINUITY_CODE = """def premiere_coupure(trajets, fermetures):
    if len(trajets) == 0:
        return 0
    fermees = []
    for etape in range(len(fermetures)):
        fermees.append(fermetures[etape])
        reste = False
        for trajet in trajets:
            if disponible(trajet, fermees):
                reste = True
        if not reste:
            return etape + 1
    return None"""

CODES = {
    "minimum": SELECTOR_CODE,
    "budget": BUDGET_CODE,
    "continuity": CONTINUITY_CODE,
}

VERSION = "fr-nsi-route-families-prose-v1"
BUDGET_PROMPT = (
    "Écrivez entièrement trajets_admissibles(trajets, couts, fermees, budget), "
    "en utilisant disponible. trajets contient des trajets valides reliant les mêmes "
    "extrémités ; couts contient leurs coûts dans le même ordre. Ces listes ont la "
    "même longueur et peuvent être vides. budget est un coût maximal, bornes incluses. "
    "Renvoyez, dans l'ordre du catalogue, la liste des indices des trajets disponibles "
    "dont le coût ne dépasse pas budget. Ne modifiez aucun paramètre. "
    "Justifiez le contenu de votre résultat après les k premiers trajets, puis "
    "expliquez le cas sans trajet admissible. Pour les deux fermetures de 1f et "
    "budget = {budget}, donnez le résultat. Si cette liste est vide, peut-on conclure "
    "qu'aucun trajet du graphe ne respecte le budget ? Justifiez."
)
CONTINUITY_PROMPT = (
    "Écrivez entièrement premiere_coupure(trajets, fermetures), en utilisant disponible. "
    "trajets contient des trajets valides initialement disponibles, reliant les mêmes "
    "extrémités. fermetures est une liste ordonnée de paires de sommets : à l'étape k "
    "(numérotée à partir de 1), les k premières liaisons sont fermées, sans réouverture. "
    "Une liaison répétée reste fermée mais son événement compte comme une étape. "
    "Renvoyez la première étape où aucun trajet du catalogue ne reste disponible ; "
    "renvoyez 0 si trajets est vide et None si une coupure totale ne survient pas. "
    "Ne modifiez aucun paramètre. Justifiez l'état des fermetures et le test effectué "
    "à chaque étape, puis pourquoi le premier résultat trouvé est le bon. "
    "Pour le catalogue et fermetures = {closures}, donnez les indices encore "
    "disponibles après chaque étape et le résultat. Une coupure totale du catalogue "
    "prouve-t-elle que les extrémités sont déconnectées dans le graphe ? Justifiez."
)

BUDGET_CRITERIA = (
    "Une liste vide est initialisée et les indices sont parcourus dans l'ordre.",
    "Disponibilité et coût inférieur ou égal au budget sont testés avant l'ajout, sans mutation des paramètres.",
    "Le contenu exact du préfixe résultat est justifié ; aucun trajet admissible produit une liste vide.",
    "Le résultat numérique est exact et l'absence dans le catalogue n'est pas confondue avec l'absence dans le graphe.",
)
CONTINUITY_CRITERIA = (
    "La liste vide de trajets renvoie 0 ; les fermetures sont accumulées localement sans modifier les paramètres.",
    "À chaque étape, tous les trajets sont testés avec les fermetures cumulées ; le numéro est compté à partir de 1.",
    "La première étape sans trajet est renvoyée, sinon None ; l'état cumulé et la première détection sont justifiés.",
    "Les survivants et le résultat du cas sont exacts ; la limite au catalogue est distinguée de la déconnexion du graphe.",
)


def family_blueprint(blueprint, seed):
    result = deepcopy(blueprint)
    result[6]["goal"] = {
        "minimum": "Construire un minimum disponible, justifier son invariant et sa portée.",
        "budget": "Construire un filtrage sous budget, justifier le préfixe résultat et sa portée.",
        "continuity": "Construire une détection de première coupure et justifier les états successifs.",
    }[family_for_seed(seed)]
    return result


def family_catalogue_identity():
    from Backend.Core.france.route_selection_authoring import route_catalogue_identity

    payload = {
        "version": VERSION,
        "base": route_catalogue_identity(),
        "families": FAMILIES,
        "codes": CODES,
        "budget_prompt": BUDGET_PROMPT,
        "continuity_prompt": CONTINUITY_PROMPT,
        "budget_criteria": BUDGET_CRITERIA,
        "continuity_criteria": CONTINUITY_CRITERIA,
    }
    return VERSION, sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def render_family_candidate(contract, selection, task_specs):
    from Backend.Core.france.pipeline import _tasks_for_seed_v30
    from Backend.Core.france.route_selection_authoring import render_route_candidate

    data = contract.to_dict()
    legacy = _tasks_for_seed_v30(data["seed"])[0]["question_blueprint"]
    if task_specs != family_blueprint(legacy, data["seed"]):
        raise ValueError("Route family blueprint mismatch")
    raw = render_route_candidate(contract, selection, legacy)
    facts = family_expected(data)
    family = facts["family"]
    question = raw["questions"][6]
    if family != "minimum":
        prefix = (
            "La fonction fournie teste la disponibilité d'un trajet ; les liaisons "
            "sont non orientées.\n\n```python\n" + HELPER_CODE + "\n```\n"
        )
        if family == "budget":
            prompt = BUDGET_PROMPT.format(budget=facts["budget"])
            explanation = (
                "Après k trajets, indices contient exactement, dans l'ordre initial, "
                "les indices admissibles parmi les k premiers. Initialement la liste "
                "est vide ; l'indice suivant n'est ajouté que si les deux conditions "
                "sont remplies. À la fin tous les indices ont été examinés. "
                "Sans trajet admissible, aucun ajout n'a lieu et la liste reste vide. "
                f"Sur le catalogue : {facts['result']}. "
                "Un trajet absent du catalogue pourrait respecter le budget : "
                "on ne peut pas conclure pour tout le graphe."
            )
            criteria = BUDGET_CRITERIA
        else:
            prompt = CONTINUITY_PROMPT.format(closures=facts["closures"])
            explanation = (
                "À l'étape k, fermees contient les k premiers événements, y compris "
                "les répétitions ; disponible teste donc toutes les fermetures effectives. "
                "reste vaut vrai exactement si au moins un trajet survit. Les étapes "
                "sont examinées dans l'ordre : le premier test négatif donne la première "
                "coupure. Sans test négatif, None est renvoyé. Une liste initiale vide "
                "donne 0 avant tout événement. Aucun paramètre n'est modifié. "
                f"Survivants aux étapes 1 à 3 : {facts['survivors_by_stage'][1:]}. "
                f"Résultat : {facts['result']}. "
                "Un trajet absent du catalogue pourrait encore relier les extrémités : "
                "la coupure du catalogue ne prouve pas la déconnexion du graphe."
            )
            criteria = CONTINUITY_CRITERIA
        question.update(
            prompt=prefix + prompt,
            answer="```python\n" + CODES[family] + "\n```\n" + explanation,
            marking=[{"points": "0.25", "criterion": c} for c in criteria],
        )
    for question in raw["questions"][5:7]:
        question["verification"] = {
            "kind": "route_family_contract",
            "contract": data,
            "task_id": question["id"],
            "expected": facts,
        }
    return raw


def family_for_seed(seed):
    if type(seed) is not int:
        raise ValueError("Task-family seed must be an integer")
    return FAMILIES[(seed - 270100) % len(FAMILIES)]


# Derive public cases with edge-set operations independently of the solution algorithms.
def family_expected(data):
    facts = route_selection_expected(data)
    family = family_for_seed(data["seed"])
    routes, costs = facts["routes"], facts["costs"]
    closed = [data["closed_edge"], data["closed_edge_second"]]
    edges = [{frozenset(edge) for edge in pairwise(route)} for route in routes]
    available = [
        i for i, route in enumerate(edges) if route.isdisjoint(map(frozenset, closed))
    ]
    # Inclusive boundary appears in the actual case; a second valid but more
    # expensive route is excluded when present. No hidden numerical input.
    budget = min(costs[i] for i in available)
    selected = min(available, key=lambda i: costs[i])
    third = routes[selected][-2:]
    closures = [*closed, third]
    survivors = [
        [
            i
            for i, route in enumerate(edges)
            if route.isdisjoint(map(frozenset, closures[:stage]))
        ]
        for stage in range(len(closures) + 1)
    ]
    result = {
        "minimum": selected,
        "budget": [i for i in available if costs[i] <= budget],
        "continuity": next(
            (stage for stage, values in enumerate(survivors) if not values), None
        ),
    }[family]
    return {
        "family": family,
        "base": facts,
        "budget": budget,
        "closures": deepcopy(closures),
        "survivors_by_stage": survivors,
        "result": result,
        "helper_sha256": sha256(HELPER_CODE.encode()).hexdigest(),
        "solution_sha256": sha256(CODES[family].encode()).hexdigest(),
    }
