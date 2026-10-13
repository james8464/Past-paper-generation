"""Finite French wording and staged working surfaces for V23 Exercise 3."""

from __future__ import annotations

import json
from decimal import Decimal
from hashlib import sha256

from Backend.Core.france.network_incident_contract import NetworkIncidentContract

NETWORK_INCIDENT_PROSE_VERSION = "fr-nsi-network-incident-prose-v1"
_IDS = tuple(f"3{x}" for x in "abcdefghijkl")
_MINUTES = (4, 7, 6, 8, 5, 6, 6, 6, 5, 5, 6, 6)
_PROFILES = {
    tuple("0.25" if q in {"3a", "3e"} else "0.5" for q in _IDS),
    tuple("0.5" for _ in _IDS),
    tuple("0.75" if q in {"3d", "3l"} else "0.5" for q in _IDS),
}
_SCENES = {
    "station": (
        "Incident de la station de mesures",
        "Central transmet le paquet de mesures M-27 à Station.",
    ),
    "observatoire": (
        "Incident de l'observatoire",
        "Central envoie le paquet de mesures M-27 à la station d'observation.",
    ),
}
_QUESTIONS = {
    "3a": (
        "Initialisez Dijkstra depuis Central : donnez les distances directes vers R1 et R2 et le premier sommet fixé.",
        "Quelles sont les deux premières distances depuis Central et quel sommet est fixé en premier dans Dijkstra ?",
    ),
    "3b": (
        "Après fixation de R1, complétez les distances provisoires et les prédécesseurs de R2 et R3.",
        "Poursuivez Dijkstra après R1 : inscrivez les valeurs et prédécesseurs provisoires de R2 et R3.",
    ),
    "3c": (
        "Retrouvez la route initiale jusqu'à Station et justifiez son coût en additionnant les liaisons empruntées.",
        "Quelle route initiale est minimale vers Station ? Montrez le calcul de son coût.",
    ),
    "3d": (
        "Après le changement de coût, complétez la route et son coût ; comparez l'arrivée de M-27 à l'échéance, avant puis après le changement.",
        "Recalculez la route après la hausse ; à partir des coûts avant/après, M-27 respecte-t-il encore l'échéance ? Quantifiez l'écart.",
    ),
    "3e": (
        "À l'arrivée de M-27, donnez pour P1 et P2 la ressource détenue et celle attendue ; indiquez l'état de M-27.",
        "Lisez l'instant d'arrivée : que détient et attend chaque processus, et où se trouve M-27 ?",
    ),
    "3f": (
        "Dessinez les arcs du graphe d'attente et expliquez pourquoi M-27 ne peut pas être traité dans cet état.",
        "Quel cycle d'attente forme P1/P2 et en quoi bloque-t-il le traitement de M-27 ?",
    ),
    "3g": (
        "Complétez les états de reprise après l'arrêt de P2 : libération, traitement de M-27, puis redémarrage.",
        "Tracez la reprise après l'arrêt de P2 jusqu'au traitement de M-27 et au retour de P2.",
    ),
    "3h": (
        "Justifiez une règle d'acquisition A avant B qui empêche ce cycle ; précisez ce qu'elle ne garantit pas pour M-27.",
        "Pourquoi l'ordre commun A avant B casse-t-il ce cycle, sans garantir toute livraison future de M-27 ?",
    ),
    "3i": (
        "Une fois M-27 traité, ordonnez M1, M2 et M3 pour transmettre le compte rendu chiffré à Central ; donnez le rôle de M3.",
        "Après la reprise, dans quel ordre échanger les trois cartes pour chiffrer le compte rendu M-27, et pourquoi M3 est-il nécessaire ?",
    ),
    "3j": (
        "Pour ce compte rendu, distinguez le contenu et la clé illisibles des métadonnées visibles à un observateur passif.",
        "Que voit l'observateur passif après la reprise, et que ne peut-il pas lire sous les hypothèses indiquées ?",
    ),
    "3k": (
        "La clé publique authentifie-t-elle Central, Station ou les deux ? Justifiez avec l'absence de signature.",
        "Distinguez l'authentification de Central de celle de Station dans l'échange indiqué.",
    ),
    "3l": (
        "Analysez séparément l'échéance déjà manquée par M-27, les métadonnées visibles du compte rendu et la compromission d'un terminal : qu'apporte ou non le chiffrement ?",
        "Le chiffrement du compte rendu répare-t-il le retard de M-27 ? Discutez aussi les métadonnées et un terminal compromis.",
    ),
}


def network_incident_catalogue_digest() -> str:
    return sha256(
        json.dumps(
            {
                "version": NETWORK_INCIDENT_PROSE_VERSION,
                "scenes": _SCENES,
                "questions": _QUESTIONS,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def network_incident_selection_schema(contract: NetworkIncidentContract) -> dict:
    if contract.to_dict()["task_ids"] != list(_IDS):
        raise ValueError("Incompatible network incident contract")

    def forms(suffix: str) -> dict:
        return {
            "type": "object",
            "properties": {
                q: {"type": "string", "enum": [f"{q}-{suffix}1", f"{q}-{suffix}2"]}
                for q in _IDS
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


def validate_network_incident_selection(
    contract: NetworkIncidentContract, selection: dict
) -> dict:
    rules = network_incident_selection_schema(contract)["properties"]
    if not isinstance(selection, dict) or set(selection) != set(rules):
        raise ValueError("Network incident selection outside schema")
    if type(selection["scene_id"]) is not str or selection["scene_id"] not in _SCENES:
        raise ValueError("Unknown network incident scene")
    for field in ("question_forms", "rubric_forms"):
        values = selection[field]
        allowed = rules[field]["properties"]
        if not isinstance(values, dict) or set(values) != set(allowed):
            raise ValueError("Network incident wording fields mismatch")
        if any(
            type(values[q]) is not str or values[q] not in rule["enum"]
            for q, rule in allowed.items()
        ):
            raise ValueError("Unknown network incident wording ID")
    return selection


def _answer(q: str, facts: dict) -> str:
    before, after = facts["expected"]["before"], facts["expected"]["after"]
    packet = facts["expected"]["packet"]
    if q == "3a":
        return f"Central est fixé d'abord ; R1={facts['links'][0][2]} et R2={facts['links'][1][2]}."
    if q == "3b":
        row = before["trace"][1]["tentative"]
        pred = before["predecessors"]
        return f"Après R1 : R2={row['R2']} (prédécesseur {pred['R2']}) ; R3={row['R3']} (prédécesseur {pred['R3']})."
    if q == "3c":
        costs = [
            next(
                weight
                for left, right, weight in facts["links"]
                if {left, right} == {start, end}
            )
            for start, end in zip(before["path"], before["path"][1:], strict=False)
        ]
        return (
            "–".join(before["path"])
            + f" : {' + '.join(map(str, costs))} = {before['cost']} minutes."
        )
    if q == "3d":
        return (
            "–".join(after["path"])
            + f" coûte {after['cost']} minutes. M-27 arrivait à {packet['before_arrival']} min "
            f"avant la hausse (à l'heure), puis à {packet['after_arrival']} min : retard de {packet['late_by']} min "
            f"sur l'échéance de {facts['packet']['deadline']} min."
        )
    if q == "3e":
        return "À l'arrivée de M-27, P1 détient A et attend B ; P2 détient B et attend A ; le paquet reste en attente de traitement."
    if q == "3f":
        return "P1→P2 et P2→P1 forment un cycle : aucun ne libère la ressource attendue, donc P1 ne traite pas M-27."
    if q == "3g":
        return "P2 est arrêté et libère B ; P1 prend B, traite M-27 puis libère A et B ; P2 redémarre et prend A puis B."
    if q == "3h":
        return "L'ordre A avant B interdit de détenir B en attendant A et casse ce cycle. Il ne garantit ni la ponctualité ni l'absence de toute panne pour le paquet M-27."
    if q == "3i":
        return "Après traitement : M2 (clé publique authentifiée de Central), M3 (clé de session chiffrée pour Central), puis M1 (compte rendu M-27 chiffré). M3 transmet la clé sans la livrer en clair."
    if q == "3j":
        return "L'observateur passif voit horaires, adresses et tailles, mais ne lit ni la clé de session ni le compte rendu M-27 si les primitives sont sûres."
    if q == "3k":
        return "Central est authentifié par sa clé publique ; Station reste non authentifiée comme émettrice faute de signature."
    if q == "3l":
        return "Le chiffrement ne répare pas le retard déjà subi par M-27 ; adresses, horaires et tailles restent visibles ; un terminal compromis lit les données avant ou après chiffrement."
    raise ValueError("Unknown network incident task")


def _criteria(q: str) -> tuple[str, ...]:
    return {
        "3a": ("les deux coûts et Central fixé", "le premier état de Dijkstra"),
        "3b": ("R2 et son prédécesseur", "R3 et son prédécesseur"),
        "3c": ("la route initiale", "l'addition des coûts"),
        "3d": (
            "la route après la hausse",
            "les deux arrivées comparées à l'échéance et le retard chiffré",
            "l'interprétation du changement pour M-27",
        ),
        "3e": (
            "les ressources détenues/attendues et M-27 en attente",
            "le lien avec son arrivée",
        ),
        "3f": ("les deux arcs et le cycle", "le blocage du traitement de M-27"),
        "3g": (
            "P1 prend B et assure le traitement de M-27",
            "P1 libère A/B, puis P2 reprend dans l'ordre A avant B",
        ),
        "3h": ("l'ordre A avant B cassant ce cycle", "sa portée limitée pour M-27"),
        "3i": ("l'ordre M2–M3–M1", "le rôle de M3"),
        "3j": ("la clé et les mesures illisibles", "les métadonnées visibles"),
        "3k": ("Station authentifiée", "le capteur non authentifié sans signature"),
        "3l": (
            "le retard non réparé",
            "les métadonnées visibles et le terminal compromis hors protection",
            "la distinction entre transport et état des terminaux",
        ),
    }[q]


def _rubric(q: str, points: str, variant: int) -> list[dict]:
    criteria = _criteria(q)
    count = int(Decimal(points) * 4)
    if count > len(criteria):
        raise ValueError("Network incident rubric and credit disagree")
    prefix = "Vérifier " if variant == 2 else "Accorder pour "
    return [{"points": "0.25", "criterion": prefix + item} for item in criteria[:count]]


def render_network_incident_candidate(
    contract: NetworkIncidentContract, selection: dict, task_specs: list[dict]
) -> dict:
    validate_network_incident_selection(contract, selection)
    if (
        not isinstance(task_specs, list)
        or len(task_specs) != 12
        or any(not isinstance(plan, dict) for plan in task_specs)
        or [plan.get("id") for plan in task_specs] != list(_IDS)
        or tuple(plan.get("points") for plan in task_specs) not in _PROFILES
        or tuple(plan.get("estimated_minutes") for plan in task_specs) != _MINUTES
        or [plan.get("part_id") for plan in task_specs] != list("AAAABBBBCCCC")
        or any(
            plan.get("required_curriculum_code")
            != ("ASR-ROUTAGE" if i < 4 else "ASR-PROCESSUS" if i < 8 else "ASR-CRYPTO")
            for i, plan in enumerate(task_specs)
        )
    ):
        raise ValueError("Network incident blueprint credit or structure mismatch")
    facts = contract.to_dict()
    title, lead = _SCENES[selection["scene_id"]]
    deadline = facts["packet"]["deadline"]
    context = (
        lead
        + " Chaque coût de liaison représente une minute de trajet et les sept liaisons sont bidirectionnelles. "
        + f"M-27 part à t=0 et doit arriver au plus tard à t={deadline} min. Le coût de R1–R3 passe de "
        + f"{facts['links'][2][2]} à {facts['change']['new_cost']} ; les autres coûts ne changent pas. "
        + "À son arrivée après la hausse, M-27 rencontre l'état de processus indiqué : ce retard ne cause pas, à lui seul, le cycle d'attente. "
        + "Pour la reprise demandée, P2 est arrêté et libère B ; les étapes suivantes sont à déduire. "
        + "Après traitement, Station renvoie un compte rendu M-27 chiffré à Central ; la clé publique de Central est authentifiée, "
        + "Station ne signe pas et l'observateur est passif. Les primitives de chiffrement sont supposées sûres."
    )
    materials = [
        {
            "kind": "table",
            "id": "links",
            "title": "Liaisons et coûts initiaux",
            "columns": ["Extrémité 1", "Extrémité 2", "Minutes"],
            "rows": [[left, right, str(cost)] for left, right, cost in facts["links"]],
        },
        {
            "kind": "table",
            "id": "route_working",
            "title": "Routes : tableau de travail avant et après la hausse",
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
            "id": "packet_card",
            "title": "Échéance du paquet M-27",
            "columns": ["Départ", "Échéance", "Arrivée avant/après hausse"],
            "rows": [["t=0", f"t={deadline} min", "à calculer / à calculer"]],
        },
        {
            "kind": "table",
            "id": "process_initial",
            "title": "Ressources et reprise à compléter",
            "columns": ["Moment", "P1 : ingestion M-27", "P2 : maintenance"],
            "rows": [
                [
                    "arrivée",
                    "détient A ; attend B ; M-27 en attente",
                    "détient B ; attend A",
                ],
                ["après arrêt P2", "à compléter", "libère B"],
                ["après fin P1", "à compléter", "à compléter"],
                ["après redémarrage", "à compléter", "à compléter"],
            ],
        },
        {
            "kind": "table",
            "id": "message_cards",
            "title": "Cartes après la reprise, à ordonner",
            "columns": ["Carte", "Émetteur", "Contenu"],
            "rows": [list(card) for card in facts["security"]["messages"]],
        },
        {
            "kind": "table",
            "id": "threat_working",
            "title": "Situations à analyser",
            "columns": ["Situation", "Conclusion et justification"],
            "rows": [
                [scenario, "à compléter"]
                for scenario in facts["working_surfaces"]["threat_scenarios"]
            ],
        },
    ]
    questions = []
    for index, (q, plan) in enumerate(zip(_IDS, task_specs, strict=True)):
        form = int(selection["question_forms"][q][-1]) - 1
        rubric_form = int(selection["rubric_forms"][q][-1])
        questions.append(
            {
                "id": q,
                "prompt": _QUESTIONS[q][form],
                "points": plan["points"],
                "answer": _answer(q, facts),
                "marking": _rubric(q, plan["points"], rubric_form),
                "material_ids": ["links", "route_working", "packet_card"]
                if index < 4
                else ["packet_card", "process_initial"]
                if index < 8
                else ["packet_card", "message_cards", "threat_working"],
                "curriculum_codes": [plan["required_curriculum_code"]],
                "operation": plan["operation"],
                "difficulty": plan["difficulty"],
                "estimated_minutes": plan["estimated_minutes"],
                "verification": {
                    "kind": "network_incident_contract",
                    "contract": facts,
                    "task_id": q,
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


def validate_network_incident_exercise(
    contract: NetworkIncidentContract, exercise, task_specs: list[dict]
) -> None:
    """Reject mutated candidate facts, answers or credits before PDF inspection."""
    raw = exercise.model_dump(mode="json")
    scene = next(
        (key for key, (title, _) in _SCENES.items() if title == raw.get("title")),
        None,
    )
    if scene is None:
        raise ValueError("Unknown network incident scene")
    selection = {
        "scene_id": scene,
        "question_forms": {q: f"{q}-q1" for q in _IDS},
        "rubric_forms": {q: f"{q}-r1" for q in _IDS},
    }
    expected = render_network_incident_candidate(contract, selection, task_specs)
    if {key: value for key, value in raw.items() if key != "questions"} != {
        key: value for key, value in expected.items() if key != "questions"
    }:
        raise ValueError("Network incident candidate premise or materials differ")
    if len(raw["questions"]) != len(_IDS):
        raise ValueError("Network incident question count differs")
    for question, canonical in zip(
        raw["questions"], expected["questions"], strict=True
    ):
        q = canonical["id"]
        if (
            {
                key: value
                for key, value in question.items()
                if key not in {"prompt", "marking"}
            }
            != {
                key: value
                for key, value in canonical.items()
                if key not in {"prompt", "marking"}
            }
            or question.get("prompt") not in _QUESTIONS[q]
            or question.get("marking")
            not in (
                _rubric(q, canonical["points"], 1),
                _rubric(q, canonical["points"], 2),
            )
        ):
            raise ValueError(f"Network incident question {q} differs from catalogue")
