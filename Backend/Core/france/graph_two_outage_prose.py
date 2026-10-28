# finite V25 French wording for a sustained two-outage graph case

from __future__ import annotations

import json
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
from itertools import pairwise

from Backend.Core.france.graph_route_trace_contract import (
    build_graph_route_trace_contract,
)
from Backend.Core.france.graph_route_trace_prose import (
    graph_route_trace_catalogue_digest,
    graph_route_trace_selection_schema,
    render_graph_route_trace_candidate,
    validate_graph_route_trace_selection,
)
from Backend.Core.france.graph_two_outage_contract import GraphTwoOutageContract

GRAPH_TWO_OUTAGE_PROSE_VERSION = "fr-nsi-two-outage-prose-v1"
_MINUTES = (3, 3, 10, 8, 8, 10, 11, 6, 5, 6)
_QUESTION_1G = (
    "Après la fermeture de {first}, la liaison {second} est à son tour fermée. "
    "Déterminez un trajet de poids minimal de A à F avec les deux liaisons "
    "fermées. Écrivez la somme des poids de ses arêtes et comparez son coût "
    "au coût après la première fermeture. Justifiez votre comparaison."
)
_CRITERIA_1G = (
    "un trajet minimal restant avec sa somme d'arêtes et son coût",
    "une comparaison justifiée avec le coût après la première fermeture",
)


def _canonical(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def graph_two_outage_catalogue_digest() -> str:
    return sha256(
        _canonical(
            {
                "version": GRAPH_TWO_OUTAGE_PROSE_VERSION,
                "base": graph_route_trace_catalogue_digest(),
                "question_1g": _QUESTION_1G,
                "criteria_1g": _CRITERIA_1G,
                "minutes": _MINUTES,
                "working_columns": (
                    "Trajet restant",
                    "Somme des poids",
                    "Coût",
                    "Comparaison",
                ),
            }
        ).encode("utf-8")
    ).hexdigest()


def graph_two_outage_selection_schema(contract: GraphTwoOutageContract) -> dict:
    return graph_route_trace_selection_schema(contract)


def validate_graph_two_outage_selection(
    contract: GraphTwoOutageContract, selection: dict
) -> dict:
    return validate_graph_route_trace_selection(contract, selection)


def _validate_specs(task_specs: list[dict]) -> None:
    ids = [f"1{letter}" for letter in "abcdefghij"]
    if [item.get("id") for item in task_specs] != ids:
        raise ValueError("V25 graph task IDs differ")
    totals = {
        "5.5": ("0.25", "0.25", "1", "0.5", "0.5", "1", "0.5", "0.5", "0.5", "0.5"),
        "6": ("0.25", "0.25", "1", "0.5", "1", "1", "0.5", "0.5", "0.5", "0.5"),
        "6.5": ("0.25", "0.25", "1", "0.5", "1", "1", "0.5", "0.5", "0.5", "1"),
    }
    points = tuple(item.get("points") for item in task_specs)
    minutes = tuple(item.get("estimated_minutes") for item in task_specs)
    if (
        points not in totals.values()
        or minutes != _MINUTES
        or task_specs[5].get("operation") != "analyse"
        or task_specs[5].get("difficulty") != 4
        or task_specs[6].get("operation") != "justify"
        or task_specs[6].get("difficulty") != 4
    ):
        raise ValueError("V25 graph credit or timing differs")


def render_graph_two_outage_candidate(
    contract: GraphTwoOutageContract, selection: dict, task_specs: list[dict]
) -> dict:
    validate_graph_two_outage_selection(contract, selection)
    _validate_specs(task_specs)
    facts = contract.to_dict()
    legacy_specs = deepcopy(task_specs)
    legacy_specs[5]["points"] = "0.5"
    legacy_specs[6]["points"] = "1"
    legacy_specs[5]["operation"] = "debug"
    legacy_specs[5]["difficulty"] = 2
    legacy_specs[6]["difficulty"] = 2
    for index, item in enumerate(legacy_specs):
        item["estimated_minutes"] = (6, 6, 8, 7, 8, 7, 7, 7, 7, 7)[index]
    old = build_graph_route_trace_contract(facts["seed"])
    candidate = deepcopy(
        render_graph_route_trace_candidate(old, selection, legacy_specs)
    )
    questions = {question["id"]: question for question in candidate["questions"]}
    first = questions["1f"]
    first_route = questions["1g"]
    first["prompt"] = first_route["prompt"]
    first["answer"] = first_route["answer"]
    first["marking"] = deepcopy(first_route["marking"])
    first["material_ids"] = list(first_route["material_ids"])

    second = questions["1g"]
    result = facts["expected"]["1g"]
    second["prompt"] = _QUESTION_1G.format(
        first="–".join(facts["closed_edge"]),
        second="–".join(facts["closed_edge_second"]),
    )
    second["material_ids"] = ["reseau", "route_double_fermeture"]
    weights = {
        frozenset((left, right)): weight
        for left, right, weight in facts["graph"]["edges"]
    }
    addition = " + ".join(
        str(weights[frozenset((left, right))])
        for left, right in pairwise(result["route_after"])
    )
    second["answer"] = (
        "Après les deux fermetures, le trajet minimal restant est "
        + " → ".join(result["route_after"])
        + f" ; son poids est {addition} = {result['cost_after']}. "
        + f"Ce coût est {result['comparison']} au coût {result['cost_before']} "
        + "après la première fermeture."
    )
    second["marking"] = [
        {"points": "0.25", "criterion": "Accorder pour " + criterion + "."}
        for criterion in _CRITERIA_1G
    ]
    candidate["materials"].append(
        {
            "kind": "table",
            "id": "route_double_fermeture",
            "title": "Trajet après fermeture de "
            + "–".join(facts["closed_edge_second"]),
            "columns": [
                "Trajet restant",
                "Somme des poids",
                "Coût",
                "Comparaison",
            ],
            "rows": [["_____"] * 4],
        }
    )
    for index, question in enumerate(candidate["questions"]):
        question["points"] = task_specs[index]["points"]
        question["estimated_minutes"] = task_specs[index]["estimated_minutes"]
        question["operation"] = task_specs[index]["operation"]
        question["difficulty"] = task_specs[index]["difficulty"]
        question["verification"] = {
            "kind": "graph_two_outage_contract",
            "contract": facts,
            "task_id": question["id"],
            "expected": facts["expected"][question["id"]],
        }
        if sum(Decimal(item["points"]) for item in question["marking"]) != Decimal(
            question["points"]
        ):
            raise ValueError("Graph two-outage criterion and credit disagree")
    return candidate
