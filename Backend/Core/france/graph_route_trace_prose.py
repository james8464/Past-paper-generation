"""Finite V22 French wording for staged graph route and debugging work."""

from __future__ import annotations

import json
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
from itertools import pairwise

from Backend.Core.france.graph_resilience_contract import (
    build_graph_resilience_contract,
)
from Backend.Core.france.graph_resilience_prose import (
    graph_resilience_catalogue_digest,
    graph_resilience_selection_schema,
    render_graph_resilience_candidate,
    validate_graph_resilience_selection,
)
from Backend.Core.france.graph_route_trace_contract import GraphRouteTraceContract

GRAPH_ROUTE_TRACE_PROSE_VERSION = "fr-nsi-route-trace-prose-v1"
_IDS = tuple(f"1{letter}" for letter in "abcdefghij")
_QUESTION_1C = (
    "Complétez le tableau de Dijkstra avant fermeture : pour les deux premières "
    "fixations depuis A, indiquez le sommet fixé, les distances provisoires "
    "vers A à F et les prédécesseurs connus. Écrivez ∞ pour un sommet non atteint."
)
_QUESTION_1E = (
    "Le programme ci-dessous échoue avant de terminer. Nommez l'exception "
    "et indiquez par quel nom remplacer le nom non défini."
)
_QUESTION_1F = (
    "Après correction, donnez l'ordre complet du parcours en largeur et "
    "la file après le retrait de A."
)
_QUESTION_1G = (
    "La liaison {closed} est fermée. Complétez le second tableau de Dijkstra "
    "pour les deux premières fixations sans cette liaison : distances "
    "provisoires et prédécesseurs. Déduisez un nouveau trajet minimal de A à F, "
    "calculez son poids et comparez-le au poids initial."
)
_CRITERIA_1G = (
    "les distances provisoires des deux fixations après fermeture",
    "les prédécesseurs correspondants",
    "le nouveau trajet minimal et son poids",
    "la comparaison avec le poids initial",
)


def graph_route_trace_catalogue_digest() -> str:
    payload = {
        "version": GRAPH_ROUTE_TRACE_PROSE_VERSION,
        "base_catalogue_digest": graph_resilience_catalogue_digest(),
        "questions": (_QUESTION_1C, _QUESTION_1E, _QUESTION_1F, _QUESTION_1G),
        "criteria_1g": _CRITERIA_1G,
        "table_columns": ("Fixation / donnée", *"ABCDEF"),
        "table_rows": ("1re distance (fixé : ___)", "1re préd.",
                       "2e distance (fixé : ___)", "2e préd."),
    }
    return sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def graph_route_trace_selection_schema(contract: GraphRouteTraceContract) -> dict:
    return graph_resilience_selection_schema(contract)


def validate_graph_route_trace_selection(
    contract: GraphRouteTraceContract, selection: dict
) -> dict:
    return validate_graph_resilience_selection(contract, selection)


def _working_table(identifier: str, title: str) -> dict:
    return {
        "kind": "table",
        "id": identifier,
        "title": title,
        "columns": ["Fixation / donnée", *"ABCDEF"],
        "rows": [
            ["1re distance (fixé : ___)", *(["_____"] * 6)],
            ["1re préd.", *(["_____"] * 6)],
            ["2e distance (fixé : ___)", *(["_____"] * 6)],
            ["2e préd.", *(["_____"] * 6)],
        ],
    }


def _trace_answer(steps: list[dict]) -> str:
    rows = []
    for index, step in enumerate(steps, start=1):
        distances = ", ".join(
            f"{node}={value if value is not None else '∞'}"
            for node, value in step["tentative"].items()
        )
        predecessors = ", ".join(
            f"{node}←{parent}" for node, parent in step["predecessors"].items()
        )
        rows.append(
            f"Fixation {index} : {step['settled']} ; distances {distances} ; "
            f"prédécesseurs {predecessors or 'aucun'}"
        )
    return ". ".join(rows) + "."


def _quarter_marks(criteria: tuple[str, ...]) -> list[dict]:
    return [
        {"points": "0.25", "criterion": "Accorder pour " + criterion + "."}
        for criterion in criteria
    ]


def render_graph_route_trace_candidate(
    contract: GraphRouteTraceContract, selection: dict, task_specs: list[dict]
) -> dict:
    validate_graph_route_trace_selection(contract, selection)
    facts = contract.to_dict()
    old = build_graph_resilience_contract(facts["seed"])
    candidate = deepcopy(render_graph_resilience_candidate(old, selection, task_specs))
    context, separator, _old_code = candidate["context"].partition(
        "\n\nLe programme suivant comporte une faute :"
    )
    if not separator:
        raise ValueError("Graph route-trace context cannot stage the fixed program")
    candidate["context"] = context
    candidate["materials"].extend(
        [
            _working_table("trace_initial", "Trace de Dijkstra avant fermeture"),
            _working_table(
                "trace_fermeture",
                "Trace de Dijkstra après fermeture de "
                + "–".join(facts["closed_edge"]),
            ),
        ]
    )
    questions = {question["id"]: question for question in candidate["questions"]}
    questions["1c"]["prompt"] = _QUESTION_1C
    questions["1c"]["material_ids"] = ["reseau", "trace_initial"]
    questions["1c"]["answer"] = _trace_answer(facts["expected"]["1c"]["steps"])

    q1e = questions["1e"]
    q1e["prompt"] = (
        _QUESTION_1E
        + (
            " Expliquez pourquoi ce nom provoque l'échec et écrivez la ligne corrigée."
            if q1e["points"] == "1"
            else ""
        )
        + "\n\n```python\n"
        + facts["debug_case"]["faulty_code"]
        + "\n```"
    )
    q1e["answer"] = (
        "NameError : le nom `visin` n'est pas défini dans la boucle. "
        "Le nom itéré est `voisin` ; remplacer la condition par "
        "`if voisin not in visites:`."
    )
    q1e["marking"] = _quarter_marks(
        (
            "l'exception NameError",
            "le remplacement de `visin` par `voisin`",
        )
        if q1e["points"] == "0.5"
        else (
            "l'exception NameError",
            "le nom non défini `visin`",
            "l'explication du nom `voisin` défini par la boucle",
            "la ligne corrigée `if voisin not in visites:`",
        )
    )

    q1f = questions["1f"]
    q1f["prompt"] = _QUESTION_1F
    states = facts["expected"]["1f"]["states"]
    q1f["answer"] = (
        "Après correction, l'ordre est "
        + " → ".join(facts["expected"]["1f"]["order"])
        + " ; la file après A est "
        + ", ".join(states[0]["queue"])
        + "."
    )
    q1f["marking"] = _quarter_marks(
        ("l'ordre complet du parcours", "la file après le retrait de A")
    )

    q1g = questions["1g"]
    result = facts["expected"]["1g"]
    q1g["prompt"] = _QUESTION_1G.format(closed="–".join(facts["closed_edge"]))
    q1g["material_ids"] = ["reseau", "trace_fermeture"]
    weights = {
        frozenset((left, right)): weight
        for left, right, weight in facts["graph"]["edges"]
    }
    addition = " + ".join(
        str(weights[frozenset((left, right))])
        for left, right in pairwise(result["route_after"])
    )
    q1g["answer"] = (
        _trace_answer(result["steps"])
        + " Le nouveau trajet minimal est "
        + " → ".join(result["route_after"])
        + f", de poids {addition} = {result['cost_after']} ; ce poids est {result['comparison']} "
        + f"au poids initial {result['cost_before']}."
    )
    q1g["marking"] = _quarter_marks(_CRITERIA_1G)

    for question in candidate["questions"]:
        question["verification"] = {
            "kind": "graph_route_trace_contract",
            "contract": facts,
            "task_id": question["id"],
            "expected": facts["expected"][question["id"]],
        }
        if sum(Decimal(item["points"]) for item in question["marking"]) != Decimal(
            question["points"]
        ):
            raise ValueError("Graph route-trace criterion and credit disagree")
    return candidate
