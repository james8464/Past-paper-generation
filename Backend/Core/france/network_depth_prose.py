"""Finite, original French wording for the version-two NSI network case."""

from __future__ import annotations

import json
from decimal import Decimal
from hashlib import sha256

from Backend.Core.france.network_depth_contract import NetworkDepthContract

NETWORK_DEPTH_PROSE_VERSION = "fr-nsi-network-prose-v2"
_TASK_IDS = tuple(f"3{letter}" for letter in "abcdef")
_POINT_PROFILES = {
    ("0.5", "1.5", "0.5", "1", "1", "1"),
    ("0.5", "1.5", "0.5", "1", "1", "1.5"),
    ("0.5", "1.5", "1", "1", "1", "1.5"),
}
_SCENES = {
    "campus": ("Réseau d'un campus", "Un campus échange des mesures avec sa station."),
    "terrain": (
        "Liaisons d'une station",
        "Une station de terrain reçoit des mesures d'un centre.",
    ),
}
_QUESTIONS = {
    "3a": (
        "Après la première étape de Dijkstra depuis Central, donnez les coûts provisoires de R1 et R2.",
        "À partir de Central, quelles sont les premières distances provisoires vers R1 et R2 ?",
    ),
    "3b": (
        "Trouvez la route initiale de coût minimal. Après la hausse de R1–R3, tracez les distances provisoires à chaque fixation de Dijkstra, puis donnez la nouvelle route et son coût.",
        "Calculez le meilleur trajet initial. Reprenez Dijkstra après la modification : consignez les distances provisoires à chaque étape et justifiez le nouveau trajet minimal.",
    ),
    "3c": (
        "Montrez, à partir des ressources détenues et attendues, pourquoi les deux processus sont bloqués.",
        "Décrivez le cycle d'attente entre P1 et P2 qui empêche toute progression.",
    ),
    "3d": (
        "Décrivez une reprise immédiate après l'arrêt de P2, puis expliquez pourquoi l'ordre commun A avant B évite ce cycle.",
        "Après l'arrêt de P2 et la libération de B, donnez la suite de la reprise et une règle d'acquisition empêchant ce cycle.",
    ),
    "3e": (
        "Décrivez la création, le transport et l'utilisation d'une clé de session avec la clé publique authentifiée de la station.",
        "Proposez les étapes de partage d'une clé de session sans secret préalable, puis son emploi pour les messages.",
    ),
    "3f": (
        "Expliquez ce que protège ce protocole contre l'observateur passif et ce qu'il ne garantit pas sur l'identité de l'émetteur et les métadonnées.",
        "Distinguez confidentialité des messages, authentification de l'émetteur et visibilité des métadonnées dans le cas donné.",
    ),
}


def network_depth_catalogue_digest() -> str:
    return sha256(
        json.dumps(
            {
                "version": NETWORK_DEPTH_PROSE_VERSION,
                "scenes": _SCENES,
                "questions": _QUESTIONS,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def network_depth_selection_schema(contract: NetworkDepthContract) -> dict:
    if contract.to_dict()["task_ids"] != list(_TASK_IDS):
        raise ValueError("Incompatible network depth contract")

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


def validate_network_depth_selection(
    contract: NetworkDepthContract, selection: dict
) -> dict:
    rules = network_depth_selection_schema(contract)["properties"]
    if not isinstance(selection, dict) or set(selection) != set(rules):
        raise ValueError("Network depth selection outside schema")
    if type(selection["scene_id"]) is not str or selection["scene_id"] not in _SCENES:
        raise ValueError("Unknown network depth scene")
    for field in ("question_forms", "rubric_forms"):
        values = selection[field]
        allowed = rules[field]["properties"]
        if not isinstance(values, dict) or set(values) != set(allowed):
            raise ValueError("Network depth wording fields mismatch")
        if any(
            type(values[key]) is not str or values[key] not in rule["enum"]
            for key, rule in allowed.items()
        ):
            raise ValueError("Unknown network depth wording ID")
    return selection


def _answer(task_id: str, facts: dict) -> str:
    before, after = facts["expected"]["before"], facts["expected"]["after"]
    first = facts["links"]
    if task_id == "3a":
        return f"Central–R1 : {first[0][2]} ; Central–R2 : {first[1][2]}."
    if task_id == "3b":
        trace = "; ".join(
            row["settled"]
            + f"({row['distance']}): "
            + ", ".join(
                f"{node}={value if value is not None else '∞'}"
                for node, value in row["tentative"].items()
            )
            for row in after["trace"]
        )
        return (
            "Initialement, "
            + "–".join(before["path"])
            + f" coûte {before['cost']}. "
            + "Après le changement, trace de Dijkstra (sommet fixé et distances provisoires) : "
            + trace
            + ". Le nouveau trajet "
            + "–".join(after["path"])
            + f" coûte {after['cost']} ; l'ancien trajet devient plus coûteux."
        )
    if task_id == "3c":
        return "P1 détient A et attend B ; P2 détient B et attend A. Le cycle d'attente bloque les deux processus."
    if task_id == "3d":
        return (
            "On arrête P2, qui libère B. P1 obtient B, termine puis libère A et B. "
            "P2 peut redémarrer et acquérir A puis B. Imposer A avant B aux deux processus "
            "empêche le cycle d'attente."
        )
    if task_id == "3e":
        return (
            "Le capteur vérifie la clé publique authentifiée de la station, crée une clé "
            "de session aléatoire et la chiffre pour la station. Celle-ci la déchiffre "
            "avec sa clé privée ; les messages utilisent ensuite un chiffrement symétrique."
        )
    if task_id == "3f":
        return (
            "Si les primitives sont sûres, l'observateur passif ne lit pas la clé de "
            "session chiffrée ni les messages. La clé publique authentifie la station "
            "mais, sans signature du capteur, n'authentifie pas l'émetteur auprès de la "
            "station. Les métadonnées restent visibles ; un terminal compromis reste hors protection."
        )
    raise ValueError("Unknown network depth task")


def _rubric(task_id: str, points: str, variant: int) -> list[dict]:
    criteria = {
        "3a": ("les deux distances provisoires calculées depuis Central",),
        "3b": (
            "la route initiale et son coût",
            "la trace des distances provisoires après modification",
            "la nouvelle route, son coût et la comparaison",
        ),
        "3c": ("les ressources détenues et attendues", "le cycle d'attente bloquant"),
        "3d": (
            "l'arrêt de P2 et la reprise de P1",
            "l'ordre A avant B empêchant le cycle",
        ),
        "3e": (
            "la clé publique authentifiée et le transport de la clé de session",
            "le déchiffrement et l'emploi symétrique",
        ),
        "3f": (
            "la confidentialité face à l'observateur passif",
            "l'absence d'authentification de l'émetteur",
            "les métadonnées visibles et la limite du terminal compromis",
        ),
    }[task_id]
    if task_id == "3c" and points == "0.5":
        criteria = (" ; ".join(criteria),)
    elif task_id == "3f" and points == "1":
        criteria = (criteria[0], criteria[1] + " ; " + criteria[2])
    if len(criteria) != int(Decimal(points) * 2):
        raise ValueError("Network depth rubric and credit disagree")
    prefix = "Vérifier " if variant == 2 else "Accorder pour "
    return [{"points": "0.5", "criterion": prefix + item} for item in criteria]


def render_network_depth_candidate(
    contract: NetworkDepthContract, selection: dict, task_specs: list[dict]
) -> dict:
    validate_network_depth_selection(contract, selection)
    if (
        not isinstance(task_specs, list)
        or len(task_specs) != 6
        or any(not isinstance(plan, dict) for plan in task_specs)
        or [plan.get("id") for plan in task_specs] != list(_TASK_IDS)
        or tuple(plan.get("points") for plan in task_specs) not in _POINT_PROFILES
        or [plan.get("part_id") for plan in task_specs] != list("AABBCC")
        or sum(plan.get("estimated_minutes", 0) for plan in task_specs) != 70
    ):
        raise ValueError("Network depth blueprint credit or structure mismatch")
    facts = contract.to_dict()
    title, lead = _SCENES[selection["scene_id"]]
    context = (
        lead
        + " Le tableau des liaisons donne les sept coûts bidirectionnels initiaux. "
        + "Pour 3b, R1–R3 passe de "
        + str(facts["links"][2][2])
        + " à "
        + str(facts["change"]["new_cost"])
        + "; les autres coûts restent inchangés. "
        + "Le tableau des processus décrit un état simultané. La reprise prévue arrête P2, "
        + "qui libère B ; la prévention impose A avant B. Aucun secret n'est partagé au départ. "
        + "La clé publique de la station est authentifiée, la clé de session est chiffrée "
        + "pour elle, le capteur n'appose pas de signature et l'observateur est passif."
    )
    materials = [
        {
            "kind": "table",
            "id": "links",
            "title": "Sept liaisons bidirectionnelles et coûts initiaux",
            "columns": ["Extrémité 1", "Extrémité 2", "Coût"],
            "rows": [[left, right, str(cost)] for left, right, cost in facts["links"]],
        },
        {
            "kind": "table",
            "id": "processes",
            "title": "État simultané des processus",
            "columns": ["Processus", "Ressource détenue", "Ressource attendue"],
            "rows": [
                [
                    name,
                    facts["processes"][name]["holds"],
                    facts["processes"][name]["waits_for"],
                ]
                for name in ("P1", "P2")
            ],
        },
    ]
    questions = []
    for task_id, plan in zip(_TASK_IDS, task_specs, strict=True):
        form = int(selection["question_forms"][task_id][-1]) - 1
        rubric_form = int(selection["rubric_forms"][task_id][-1])
        questions.append(
            {
                "id": task_id,
                "prompt": _QUESTIONS[task_id][form],
                "points": plan["points"],
                "answer": _answer(task_id, facts),
                "marking": _rubric(task_id, plan["points"], rubric_form),
                "material_ids": ["links"]
                if task_id in {"3a", "3b"}
                else ["processes"]
                if task_id in {"3c", "3d"}
                else [],
                "curriculum_codes": [plan["required_curriculum_code"]],
                "operation": plan["operation"],
                "difficulty": plan["difficulty"],
                "estimated_minutes": plan["estimated_minutes"],
                "verification": {
                    "kind": "network_depth_contract",
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
