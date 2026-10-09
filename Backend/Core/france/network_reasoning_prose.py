"""Finite original French wording for the V18 written network exercise."""

from __future__ import annotations

import json
from decimal import Decimal
from hashlib import sha256

from Backend.Core.france.network_reasoning_contract import NetworkReasoningContract

NETWORK_REASONING_PROSE_VERSION = "fr-nsi-network-prose-v3"
_TASK_IDS = tuple(f"3{letter}" for letter in "abcdefghijkl")
_MINUTES = (4, 7, 6, 8, 5, 6, 6, 6, 5, 5, 6, 6)
_POINT_PROFILES = {
    tuple("0.25" if task_id in {"3a", "3e"} else "0.5" for task_id in _TASK_IDS),
    tuple("0.5" for _ in _TASK_IDS),
    tuple("0.75" if task_id in {"3d", "3l"} else "0.5" for task_id in _TASK_IDS),
}
_SCENES = {
    "campus": ("Réseau d'un campus", "Un campus transmet ses mesures à une station."),
    "terrain": (
        "Liaisons d'une station",
        "Une station de terrain reçoit les mesures d'un centre.",
    ),
}
_QUESTIONS = {
    "3a": (
        "Relevez les coûts directs de Central vers R1 et R2. Que fixez-vous d'abord dans Dijkstra ?",
        "Depuis Central, donnez les deux distances initiales vers R1 et R2, puis le premier sommet fixé ?",
    ),
    "3b": (
        "Après la fixation de R1, donnez les distances provisoires de R2 et R3 et leurs prédécesseurs ?",
        "Poursuivez Dijkstra jusqu'à R1 : quelles valeurs et quels prédécesseurs obtient-on pour R2 et R3 ?",
    ),
    "3c": (
        "Déduisez le chemin initial de coût minimal vers Station et justifiez son coût par les liaisons empruntées ?",
        "Quelle route initiale mène au moindre coût de Central à Station ? Détaillez l'addition des coûts ?",
    ),
    "3d": (
        "Après la hausse de R1–R3, donnez les distances provisoires de Station après R2 puis R3, et comparez la nouvelle route minimale à la route initiale ?",
        "Reprenez les fixations après le changement de R1–R3 : comment la distance de Station évolue-t-elle et quelle route gagne face à la route initiale ?",
    ),
    "3e": (
        "À l'instant t1, quelle ressource chaque processus détient-il et attend-il ?",
        "Lisez l'état t1 : associez à P1 et P2 la ressource détenue et celle attendue ?",
    ),
    "3f": (
        "Tracez les deux arcs du graphe d'attente et expliquez pourquoi aucun processus ne progresse ?",
        "Construisez le graphe d'attente P1/P2 ; quel cycle bloque leur exécution ?",
    ),
    "3g": (
        "Si P2 est arrêté et libère B, donnez les étapes permettant à P1 de terminer puis à P2 de reprendre ?",
        "Décrivez une reprise après libération de B par P2, jusqu'au redémarrage de P2 ?",
    ),
    "3h": (
        "Justifiez pourquoi imposer A avant B aux deux processus empêche ce cycle, sans prétendre éviter toute panne ?",
        "Quelle règle commune d'acquisition casse ce cycle d'attente ? Expliquez sa portée ?",
    ),
    "3i": (
        "Ordonnez les cartes M1, M2 et M3 pour établir puis employer une clé de session ; expliquez le rôle de M3 ?",
        "Dans quel ordre les trois messages ont-ils lieu, et pourquoi M3 protège-t-il la clé de session ?",
    ),
    "3j": (
        "Sous l'hypothèse de primitives sûres, distinguez ce qu'un observateur passif lit de la clé et des mesures ?",
        "Que peut déduire l'observateur passif du trafic chiffré, et que ne peut-il pas lire ?",
    ),
    "3k": (
        "La clé publique authentifie-t-elle la station, le capteur ou les deux ? Justifiez l'absence de signature ?",
        "Distinguez l'authentification de la station et celle du capteur dans les messages indiqués ?",
    ),
    "3l": (
        "Précisez quelles métadonnées restent visibles et pourquoi un terminal compromis échappe à cette protection ?",
        "Analysez la limite du chiffrement face aux métadonnées et à la compromission d'un terminal ?",
    ),
}


def network_reasoning_catalogue_digest() -> str:
    return sha256(
        json.dumps(
            {
                "version": NETWORK_REASONING_PROSE_VERSION,
                "scenes": _SCENES,
                "questions": _QUESTIONS,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def network_reasoning_selection_schema(contract: NetworkReasoningContract) -> dict:
    if contract.to_dict()["task_ids"] != list(_TASK_IDS):
        raise ValueError("Incompatible network reasoning contract")

    def forms(suffix: str) -> dict:
        return {
            "type": "object",
            "properties": {
                task_id: {
                    "type": "string",
                    "enum": [f"{task_id}-{suffix}1", f"{task_id}-{suffix}2"],
                }
                for task_id in _TASK_IDS
            },
            "required": list(_TASK_IDS),
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


def validate_network_reasoning_selection(
    contract: NetworkReasoningContract, selection: dict
) -> dict:
    rules = network_reasoning_selection_schema(contract)["properties"]
    if not isinstance(selection, dict) or set(selection) != set(rules):
        raise ValueError("Network reasoning selection outside schema")
    if type(selection["scene_id"]) is not str or selection["scene_id"] not in _SCENES:
        raise ValueError("Unknown network reasoning scene")
    for field in ("question_forms", "rubric_forms"):
        values = selection[field]
        allowed = rules[field]["properties"]
        if not isinstance(values, dict) or set(values) != set(allowed):
            raise ValueError("Network reasoning wording fields mismatch")
        if any(
            type(values[key]) is not str or values[key] not in rule["enum"]
            for key, rule in allowed.items()
        ):
            raise ValueError("Unknown network reasoning wording ID")
    return selection


def _answer(task_id: str, facts: dict) -> str:
    before, after = facts["expected"]["before"], facts["expected"]["after"]
    if task_id == "3a":
        return (
            f"R1 vaut {facts['links'][0][2]} et R2 vaut {facts['links'][1][2]} ; "
            "Central est le premier sommet fixé."
        )
    if task_id == "3b":
        row = before["trace"][1]["tentative"]
        predecessor = before["predecessors"]
        return (
            f"Après R1 : R2={row['R2']} (prédécesseur {predecessor['R2']}) ; "
            f"R3={row['R3']} (prédécesseur {predecessor['R3']})."
        )
    if task_id == "3c":
        return (
            "–".join(before["path"])
            + f" coûte {before['cost']} : "
            + " + ".join(
                str(
                    next(
                        cost
                        for left, right, cost in facts["links"]
                        if {left, right} == {start, end}
                    )
                )
                for start, end in zip(before["path"], before["path"][1:], strict=False)
            )
            + f" = {before['cost']}."
        )
    if task_id == "3d":
        station_after_r2 = after["trace"][2]["tentative"]["Station"]
        station_after_r3 = after["trace"][3]["tentative"]["Station"]
        return (
            f"Après R2, Station vaut provisoirement {station_after_r2} ; "
            f"après R3, {station_after_r3}. La nouvelle route "
            + "–".join(after["path"])
            + f" coûte {after['cost']}, contre {before['cost']} initialement."
        )
    if task_id == "3e":
        return "À t1, P1 détient A et attend B ; P2 détient B et attend A."
    if task_id == "3f":
        return "Les arcs P1→P2 et P2→P1 forment un cycle ; chacun attend la ressource détenue par l'autre."
    if task_id == "3g":
        return (
            "P2 est arrêté et libère B ; P1 acquiert B, termine puis libère A et B. "
            "P2 redémarre ensuite, prend A puis B."
        )
    if task_id == "3h":
        return (
            "Si P1 et P2 demandent toujours A avant B, aucun ne peut détenir B "
            "en attendant A : ce cycle est impossible. Cela ne garantit pas "
            "l'absence de toute autre panne."
        )
    if task_id == "3i":
        return (
            "L'ordre est M2 (clé publique authentifiée), M3 (clé de session chiffrée "
            "pour Station), puis M1 (mesures symétriquement chiffrées). M3 ne livre "
            "pas la clé en clair à l'observateur."
        )
    if task_id == "3j":
        return (
            "Un observateur passif voit les messages et leurs métadonnées mais, "
            "si les primitives sont sûres, ne lit ni la clé de session chiffrée "
            "ni les mesures chiffrées."
        )
    if task_id == "3k":
        return (
            "La clé publique authentifiée lie la clé à Station. Sans signature "
            "du capteur, Station n'a pas d'authentification de l'émetteur."
        )
    if task_id == "3l":
        return (
            "Les adresses, horaires et tailles des messages restent des métadonnées "
            "visibles. Un terminal compromis peut accéder aux données avant ou après "
            "chiffrement : cette protection du transport ne le couvre pas."
        )
    raise ValueError("Unknown network reasoning task")


def _criteria(task_id: str, facts: dict) -> tuple[str, ...]:
    before, after = facts["expected"]["before"], facts["expected"]["after"]
    return {
        "3a": ("les deux coûts directs", "Central fixé en premier"),
        "3b": ("R2 et son prédécesseur", "R3 et son prédécesseur"),
        "3c": ("la route initiale", f"l'addition donnant {before['cost']}"),
        "3d": (
            "la distance provisoire après R2",
            "la nouvelle route et son coût",
            f"la comparaison avec le coût initial {before['cost']} et le coût changé {after['cost']}",
        ),
        "3e": (
            "P1 et ses ressources détenue/attendue",
            "P2 et ses ressources détenue/attendue",
        ),
        "3f": ("les deux arcs d'attente", "le cycle bloquant"),
        "3g": (
            "l'arrêt de P2 et la libération de B",
            "la fin de P1 puis la reprise de P2",
        ),
        "3h": ("l'ordre commun A avant B", "sa portée limitée à ce cycle"),
        "3i": ("l'ordre M2–M3–M1", "la clé de session non transmise en clair"),
        "3j": (
            "la clé illisible pour le passif",
            "les mesures illisibles pour le passif",
        ),
        "3k": ("la station authentifiée", "l'émetteur non authentifié sans signature"),
        "3l": (
            "les métadonnées visibles",
            "le terminal compromis hors protection",
            "la limite propre au chiffrement du transport",
        ),
    }[task_id]


def _rubric(task_id: str, points: str, variant: int, facts: dict) -> list[dict]:
    criteria = _criteria(task_id, facts)
    count = int(Decimal(points) * 4)
    if len(criteria) < count:
        raise ValueError("Network reasoning rubric and credit disagree")
    if count == 1 and task_id == "3a":
        criteria = ("les deux coûts directs et Central fixé en premier",)
    if count == 1 and task_id == "3e":
        criteria = ("P1 et P2 avec leurs ressources détenues et attendues",)
    prefix = "Vérifier " if variant == 2 else "Accorder pour "
    return [{"points": "0.25", "criterion": prefix + item} for item in criteria[:count]]


def render_network_reasoning_candidate(
    contract: NetworkReasoningContract, selection: dict, task_specs: list[dict]
) -> dict:
    validate_network_reasoning_selection(contract, selection)
    if (
        not isinstance(task_specs, list)
        or len(task_specs) != 12
        or any(not isinstance(plan, dict) for plan in task_specs)
        or [plan.get("id") for plan in task_specs] != list(_TASK_IDS)
        or tuple(plan.get("points") for plan in task_specs) not in _POINT_PROFILES
        or [plan.get("part_id") for plan in task_specs] != list("AAAABBBBCCCC")
        or tuple(plan.get("estimated_minutes") for plan in task_specs) != _MINUTES
        or any(
            plan.get("required_curriculum_code")
            != (
                "ASR-ROUTAGE"
                if index < 4
                else "ASR-PROCESSUS"
                if index < 8
                else "ASR-CRYPTO"
            )
            for index, plan in enumerate(task_specs)
        )
    ):
        raise ValueError("Network reasoning blueprint credit or structure mismatch")
    facts = contract.to_dict()
    title, lead = _SCENES[selection["scene_id"]]
    context = (
        lead
        + " Les sept liaisons du tableau sont bidirectionnelles. Pour 3d, le coût de "
        + "R1–R3 passe de "
        + str(facts["links"][2][2])
        + " à "
        + str(facts["change"]["new_cost"])
        + "; tous les autres coûts restent inchangés. Les états t0 et t1 sont "
        + "simultanés. Pour 3g, P2 est arrêté et libère B. Une station possède "
        + "une clé publique authentifiée ; le capteur ne signe pas ses messages. "
        + "L'observateur indiqué est passif."
    )
    cards = facts["security_messages"]
    materials = [
        {
            "kind": "table",
            "id": "links",
            "title": "Sept liaisons et coûts initiaux",
            "columns": ["Extrémité 1", "Extrémité 2", "Coût"],
            "rows": [[left, right, str(cost)] for left, right, cost in facts["links"]],
        },
        {
            "kind": "table",
            "id": "route_working",
            "title": "Tableau de travail Dijkstra avant et après la hausse",
            "columns": [
                "Sommet",
                "Avant : coût / prédécesseur",
                "Après : coût / prédécesseur",
            ],
            "rows": [
                [node, "à compléter", "à compléter"]
                for node in facts["working_surfaces"]["route_nodes"]
            ],
        },
        {
            "kind": "table",
            "id": "process_initial",
            "title": "États simultanés et reprise à compléter",
            "columns": ["Moment", "P1", "P2"],
            "rows": [
                [item["step"], item["P1"], item["P2"]]
                for item in facts["process_schedule"][:2]
            ]
            + [
                [step, "à compléter", "à compléter"]
                for step in facts["working_surfaces"]["process_steps"][2:]
            ],
        },
        {
            "kind": "table",
            "id": "message_cards",
            "title": "Cartes de messages à remettre dans l'ordre",
            "columns": ["Carte", "Émetteur", "Contenu"],
            "rows": [
                ["M1", cards[2]["sender"], cards[2]["content"]],
                ["M2", cards[0]["sender"], cards[0]["content"]],
                ["M3", cards[1]["sender"], cards[1]["content"]],
            ],
        },
        {
            "kind": "table",
            "id": "threat_working",
            "title": "Situations de sécurité à analyser",
            "columns": ["Situation", "Conclusion et justification"],
            "rows": [
                [situation, "à compléter"]
                for situation in facts["working_surfaces"]["threat_scenarios"]
            ],
        },
    ]
    questions = []
    for index, (task_id, plan) in enumerate(zip(_TASK_IDS, task_specs, strict=True)):
        form = int(selection["question_forms"][task_id][-1]) - 1
        rubric_form = int(selection["rubric_forms"][task_id][-1])
        questions.append(
            {
                "id": task_id,
                "prompt": _QUESTIONS[task_id][form],
                "points": plan["points"],
                "answer": _answer(task_id, facts),
                "marking": _rubric(task_id, plan["points"], rubric_form, facts),
                "material_ids": ["links", "route_working"]
                if index < 4
                else ["process_initial"]
                if index < 8
                else ["message_cards", "threat_working"],
                "curriculum_codes": [plan["required_curriculum_code"]],
                "operation": plan["operation"],
                "difficulty": plan["difficulty"],
                "estimated_minutes": plan["estimated_minutes"],
                "verification": {
                    "kind": "network_reasoning_contract",
                    "contract": facts,
                    "task_id": task_id,
                    "expected": facts["expected"],
                },
            }
        )
    return {
        "id": "3",
        "title": title,
        "context": context,
        "topics": ["architectures-reseaux"],
        "minutes": 70,
        "target_points": str(
            sum((Decimal(item["points"]) for item in task_specs), Decimal()).normalize()
        ),
        "materials": materials,
        "questions": questions,
    }
