"""V30 replaces repeated route traces with filtering and selection construction."""

import itertools
import json
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256

ROUTE_SELECTION_VERSION = "fr-nsi-route-selection-prose-v1"
HELPER_CODE = """def disponible(trajet, fermees):
    for i in range(len(trajet) - 1):
        a, b = trajet[i], trajet[i + 1]
        if (
            [a, b] in fermees
            or [b, a] in fermees
        ):
            return False
    return True"""
SELECTOR_CODE = """def meilleur_trajet(
    trajets, couts, fermees
):
    meilleur = None
    for i in range(len(trajets)):
        if disponible(trajets[i], fermees):
            if (
                meilleur is None
                or couts[i] < couts[meilleur]
            ):
                meilleur = i
    return meilleur"""
SELECTOR_PROMPT = (
    "La fonction fournie ci-dessous teste la disponibilité d'un trajet. "
    "Les liaisons sont non orientées.\n\n```python\n" + HELPER_CODE + "\n```\n"
    "Écrivez entièrement meilleur_trajet(trajets, couts, fermees), en utilisant disponible. "
    "trajets est une liste de trajets valides reliant les mêmes extrémités ; couts contient leurs coûts "
    "dans le même ordre. Les deux listes ont la même longueur et peuvent être vides. "
    "fermees est une liste de paires de sommets. Renvoyez l'indice du trajet disponible "
    "de coût minimal, le premier en cas d'égalité, ou None si aucun ne reste. "
    "Ne modifiez pas les listes. Justifiez ce que représente votre indice après chaque "
    "itération et expliquez le cas sans trajet disponible. Donnez le résultat pour le "
    "catalogue après les deux fermetures. Une sélection limitée à un catalogue "
    "garantit-elle, en général, un optimum sur tous les trajets du graphe ? Justifiez."
)
SELECTOR_CRITERIA = (
    "L'indice est initialisé à None et seuls les trajets disponibles sont examinés.",
    "Le coût minimal est conservé avec une comparaison stricte, donc le premier ex aequo reste choisi.",
    "L'invariant de minimum parmi les indices déjà examinés et le cas sans trajet disponible sont justifiés ; aucune liste n'est modifiée.",
    "L'indice du catalogue après les deux fermetures est exact et la limite à ce catalogue est distinguée d'un optimum global.",
)


def route_blueprint(blueprint):
    result = deepcopy(blueprint)
    result[2]["points"] = "0.5"
    result[5].update(
        estimated_minutes=7,
        goal="Calculer les coûts et filtrer un catalogue après deux fermetures non orientées.",
        response_form="tableau et justification des exclusions",
    )
    result[6].update(
        points="1",
        estimated_minutes=10,
        operation="design",
        difficulty=4,
        goal="Construire un sélecteur de minimum disponible et justifier son invariant et sa portée.",
        response_form="fonction Python complète et justification",
    )
    result[9].update(
        goal="Construire un comptage récursif dans un intervalle et justifier l'élagage de l'ABR.",
        response_form="fonction Python complète, justification et résultat",
    )
    return result


def route_selection_expected(data):
    """Enumerate simple paths independently of the trusted selector."""
    adjacency = {node: [] for node in data["graph"]["nodes"]}
    weights = {}
    for a, b, weight in data["graph"]["edges"]:
        adjacency[a].append(b)
        adjacency[b].append(a)
        weights[frozenset((a, b))] = weight
    paths = []

    def visit(path):
        if path[-1] == "F":
            paths.append(path)
            return
        for neighbour in sorted(adjacency[path[-1]]):
            if neighbour not in path:
                visit([*path, neighbour])

    visit(["A"])
    routes = [
        data["expected"]["1d"]["path"],
        data["expected"]["1f"]["route_after"],
        data["expected"]["1g"]["route_after"],
    ]

    def cost(path):
        return sum(weights[frozenset(edge)] for edge in itertools.pairwise(path))

    routes.append(
        max((path for path in paths if path not in routes), key=lambda p: (cost(p), p))
    )
    costs = [cost(path) for path in routes]
    closures = [frozenset(data["closed_edge"]), frozenset(data["closed_edge_second"])]
    availability = [
        [
            not any(
                frozenset(edge) in closures[:stage] for edge in itertools.pairwise(path)
            )
            for path in routes
        ]
        for stage in (1, 2)
    ]
    eligible = [i for i, valid in enumerate(availability[1]) if valid]
    selected = min(eligible, key=lambda i: costs[i]) if eligible else None
    return {
        "routes": routes,
        "costs": costs,
        "first_available": availability[0],
        "second_available": availability[1],
        "selected_index": selected,
        "empty_index": None,
        "helper_sha256": sha256(HELPER_CODE.encode()).hexdigest(),
        "selector_sha256": sha256(SELECTOR_CODE.encode()).hexdigest(),
    }


def route_catalogue_identity():
    from Backend.Core.france.tree_construction_authoring import graph_catalogue_identity

    payload = {
        "version": ROUTE_SELECTION_VERSION,
        "base": graph_catalogue_identity("fr-nsi-written-2027-v29"),
        "helper": HELPER_CODE,
        "selector": SELECTOR_CODE,
        "prompt": SELECTOR_PROMPT,
        "criteria": SELECTOR_CRITERIA,
    }
    return ROUTE_SELECTION_VERSION, sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


def route_material(data):
    facts = route_selection_expected(data)
    return {
        "kind": "table",
        "id": "catalogue_trajets",
        "title": "Catalogue des trajets à examiner",
        "columns": [
            "Indice",
            "Trajet",
            "Coût",
            "Après 1re fermeture",
            "Après 2e fermeture",
        ],
        "rows": [
            [str(i), " → ".join(path), "_____", "_____", "_____"]
            for i, path in enumerate(facts["routes"])
        ],
    }


def render_route_candidate(contract, selection, task_specs):
    from Backend.Core.france.pipeline import _tasks_for_seed_v29
    from Backend.Core.france.tree_construction_authoring import render_graph_candidate

    data = contract.to_dict()
    legacy = _tasks_for_seed_v29(data["seed"])[0]["question_blueprint"]
    if task_specs != route_blueprint(legacy):
        raise ValueError("Route selection blueprint mismatch")
    raw = render_graph_candidate(contract, selection, legacy, "fr-nsi-written-2027-v29")
    for question, spec in zip(raw["questions"], task_specs, strict=True):
        for field in ("points", "estimated_minutes", "operation", "difficulty"):
            question[field] = spec[field]
    for index in (7, 8):
        raw["questions"][index]["prompt"] = raw["questions"][index]["prompt"].replace(
            "`", ""
        )
    marks = raw["questions"][2]["marking"]
    raw["questions"][2]["marking"] = [
        {
            "points": "0.25",
            "criterion": " ".join(m["criterion"] for m in marks[start : start + 2]),
        }
        for start in (0, 2)
    ]
    raw["materials"] = [
        m
        for m in raw["materials"]
        if m["id"] not in {"trace_fermeture", "route_double_fermeture"}
    ]
    raw["materials"].append(route_material(data))
    facts = route_selection_expected(data)
    first, second = "–".join(data["closed_edge"]), "–".join(data["closed_edge_second"])
    criteria = [
        "Les quatre coûts du catalogue sont exacts.",
        "Les disponibilités après la première fermeture sont exactes.",
        "Les disponibilités après la seconde fermeture sont exactes.",
        "Les liaisons fermées sont exclues dans les deux sens.",
    ]
    if Decimal(task_specs[5]["points"]) == Decimal("0.5"):
        criteria = [" ".join(criteria[:2]), " ".join(criteria[2:])]
    raw["questions"][5].update(
        prompt=f"La liaison {first} est fermée. Puis la liaison {second} est à son tour fermée. "
        "Pour chacun des quatre trajets du catalogue, calculez le coût initial "
        "et indiquez sa disponibilité après chaque fermeture (oui ou non). "
        "Justifiez les exclusions en citant les liaisons concernées.",
        material_ids=["reseau", "catalogue_trajets"],
        answer="\n".join(
            f"Indice {i} : coût {cost} ; après {first} : "
            f"{'oui' if facts['first_available'][i] else 'non'} ; après les deux : "
            f"{'oui' if facts['second_available'][i] else 'non'}."
            for i, cost in enumerate(facts["costs"])
        )
        + f" Un trajet contenant {first} est exclu dès la première fermeture ; "
        f"un trajet contenant {second} l'est après la seconde, dans les deux sens.",
        marking=[{"points": "0.25", "criterion": criterion} for criterion in criteria],
    )
    raw["questions"][6].update(
        prompt=SELECTOR_PROMPT,
        material_ids=["catalogue_trajets"],
        answer="```python\n" + SELECTOR_CODE + "\n```\n"
        "Après les k premiers indices, meilleur est None si aucun trajet "
        "examiné n'est disponible ; sinon il est le premier indice de coût "
        "minimal parmi les trajets disponibles examinés. Initialement k = 0. "
        "Un trajet indisponible ne change rien ; un coût strictement inférieur "
        "remplace le minimum, une égalité conserve le premier. À la fin, tous "
        "les trajets sont examinés ; la liste vide et tous les trajets bloqués "
        "renvoient None. Aucune liste n'est modifiée. "
        f"Pour ce catalogue après les deux fermetures : indice {facts['selected_index']}. "
        "En général, un trajet moins coûteux peut manquer au catalogue : "
        "le minimum sur cette liste ne garantit pas le minimum sur tout le graphe.",
        marking=[
            {"points": "0.25", "criterion": criterion}
            for criterion in SELECTOR_CRITERIA
        ],
    )
    for index in (5, 6):
        raw["questions"][index]["verification"] = {
            "kind": "route_selection_contract",
            "contract": data,
            "task_id": raw["questions"][index]["id"],
            "expected": facts,
        }
    return raw
