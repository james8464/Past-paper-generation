"""Versioned V26 recovery chronology layered on replayable V23 prose."""

from __future__ import annotations

import json
from copy import deepcopy
from hashlib import sha256

from Backend.Core.france.network_incident_contract import (
    build_network_incident_contract,
)
from Backend.Core.france.network_incident_prose import (
    _IDS,
    _QUESTIONS,
    _SCENES,
    network_incident_catalogue_digest,
    render_network_incident_candidate,
    validate_network_incident_selection,
)
from Backend.Core.france.network_incident_timeline_contract import (
    NetworkIncidentTimelineContract,
)

NETWORK_INCIDENT_TIMELINE_PROSE_VERSION = "fr-nsi-network-incident-timeline-prose-v1"
_TIMED_QUESTIONS = {
    "3g": (
        "Complétez la chronologie après l'arrivée de M-27 : date de libération de B, fin du traitement et livraison du compte rendu sécurisé ; indiquez quand P2 redémarre.",
        "À partir de l'arrivée calculée, trouvez les trois dates de reprise et de livraison du compte rendu, puis situez le redémarrage de P2.",
    ),
    "3l": (
        "Comparez séparément l'échéance d'arrivée de M-27 et celle du compte rendu sécurisé ; expliquez ensuite les limites du chiffrement face aux métadonnées et à un terminal compromis.",
        "M-27 arrive-t-il à temps, et son compte rendu chiffré est-il livré à temps ? Justifiez aussi ce que le chiffrement ne protège pas.",
    ),
}


def network_incident_timeline_catalogue_digest() -> str:
    return sha256(
        json.dumps(
            {
                "version": NETWORK_INCIDENT_TIMELINE_PROSE_VERSION,
                "base": network_incident_catalogue_digest(),
                "questions": _TIMED_QUESTIONS,
                "credit": {
                    "3g": ("libération", "traitement", "livraison"),
                    "3j": ("confidentialité et métadonnées",),
                },
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def _legacy_specs(task_specs: list[dict]) -> list[dict]:
    if (
        not isinstance(task_specs, list)
        or len(task_specs) != len(_IDS)
        or [item.get("id") for item in task_specs] != list(_IDS)
        or task_specs[6].get("points") != "0.75"
        or task_specs[6].get("estimated_minutes") != 8
        or task_specs[6].get("difficulty") != 4
        or task_specs[9].get("points") != "0.25"
        or task_specs[9].get("estimated_minutes") != 3
    ):
        raise ValueError("Network incident timeline blueprint mismatch")
    original = deepcopy(task_specs)
    original[6].update(points="0.5", estimated_minutes=6, difficulty=2)
    original[9].update(points="0.5", estimated_minutes=5)
    return original


def _rubric(points: str, criteria: tuple[str, ...], form: int) -> list[dict]:
    count = int(float(points) * 4)
    if count > len(criteria):
        raise ValueError("Network incident timeline credit mismatch")
    prefix = "Vérifier " if form == 2 else "Accorder pour "
    return [{"points": "0.25", "criterion": prefix + item} for item in criteria[:count]]


def render_network_incident_timeline_candidate(
    contract: NetworkIncidentTimelineContract,
    selection: dict,
    task_specs: list[dict],
) -> dict:
    legacy = build_network_incident_contract(contract.to_dict()["seed"])
    validate_network_incident_selection(legacy, selection)
    raw = render_network_incident_candidate(
        legacy, selection, _legacy_specs(task_specs)
    )
    facts = contract.to_dict()
    timeline = facts["timeline"]
    events = facts["expected"]["timeline"]
    raw["context"] += (
        " Pour cette seconde échéance indépendante, l'arrêt de P2 et la libération de B prennent "
        f"{timeline['stop_and_release_minutes']} min après l'arrivée effective de M-27 ; le traitement par P1 prend ensuite "
        f"{timeline['processing_minutes']} min. P2 redémarre à la fin du traitement. "
        f"L'échange sécurisé et la transmission du compte rendu prennent encore {timeline['secure_report_minutes']} min ; "
        f"ce compte rendu est attendu à t={timeline['report_deadline']} min, soit 9 minutes après l'arrivée effective. "
        "Chaque étape commence à la fin de la précédente."
    )
    packet_card = next(item for item in raw["materials"] if item["id"] == "packet_card")
    packet_card.update(
        title="Échéances et chronologie de l'incident à compléter",
        columns=["Événement", "Durée depuis l'étape précédente (min)", "Date t (min)"],
        rows=[
            ["Départ de M-27", "—", "t=0"],
            ["Échéance d'arrivée de M-27", "—", f"t={facts['packet']['deadline']}"],
            ["Arrivée avant/après hausse", "—", "à calculer / à calculer"],
            [
                "P2 arrêté et B libérée",
                str(timeline["stop_and_release_minutes"]),
                "à compléter",
            ],
            [
                "M-27 traité ; P2 redémarre",
                str(timeline["processing_minutes"]),
                "à compléter",
            ],
            [
                "Compte rendu sécurisé livré",
                str(timeline["secure_report_minutes"]),
                "à compléter",
            ],
            ["Échéance du compte rendu", "—", f"t={timeline['report_deadline']}"],
        ],
    )
    for index, question in enumerate(raw["questions"]):
        task_id = question["id"]
        plan = task_specs[index]
        question["points"] = plan["points"]
        question["estimated_minutes"] = plan["estimated_minutes"]
        question["difficulty"] = plan["difficulty"]
        if task_id in _TIMED_QUESTIONS:
            form = int(selection["question_forms"][task_id][-1]) - 1
            question["prompt"] = _TIMED_QUESTIONS[task_id][form]
        if task_id == "3g":
            question["answer"] = (
                f"M-27 arrive à t={events['packet_arrival']} ; P2 est arrêté et B libérée à t={events['resource_released']} ; "
                f"P1 termine le traitement à t={events['packet_processed']} et P2 redémarre ; "
                f"le compte rendu sécurisé est livré à t={events['report_delivered']}."
            )
            question["marking"] = _rubric(
                plan["points"],
                (
                    "la libération de B calculée après l'arrivée effective",
                    "la fin du traitement et le redémarrage de P2",
                    "la date de livraison du compte rendu sécurisé",
                ),
                int(selection["rubric_forms"][task_id][-1]),
            )
        elif task_id == "3j":
            question["marking"] = _rubric(
                plan["points"],
                (
                    "la confidentialité du contenu et de la clé distinguée des métadonnées visibles",
                ),
                int(selection["rubric_forms"][task_id][-1]),
            )
        elif task_id == "3l":
            question["answer"] = (
                f"M-27 arrive à t={events['packet_arrival']} après son échéance t={facts['packet']['deadline']} : "
                f"{facts['expected']['packet']['late_by']} min de retard. Le compte rendu chiffré est livré à "
                f"t={events['report_delivered']} avant sa propre échéance t={timeline['report_deadline']} "
                f"(marge de {events['report_margin']} min). Le chiffrement ne répare pas le retard du paquet ; "
                "adresses, horaires et tailles restent visibles et un terminal compromis peut lire les données."
            )
            question["marking"] = _rubric(
                plan["points"],
                (
                    "les deux échéances distinctes, avec M-27 tardif et compte rendu à l'heure",
                    "les métadonnées visibles malgré le chiffrement",
                    "le terminal compromis hors de la protection du transport",
                ),
                int(selection["rubric_forms"][task_id][-1]),
            )
        question["verification"] = {
            "kind": "network_incident_timeline_contract",
            "contract": facts,
            "task_id": task_id,
            "expected": facts["expected"],
        }
    return raw


def validate_network_incident_timeline_exercise(
    contract: NetworkIncidentTimelineContract, exercise, task_specs: list[dict]
) -> None:
    """Reject altered timeline premises, working tables, answers and credits."""
    raw = exercise.model_dump(mode="json")
    scene = next(
        (key for key, (title, _) in _SCENES.items() if title == raw.get("title")),
        None,
    )
    if scene is None or len(raw.get("questions", [])) != len(_IDS):
        raise ValueError("Network incident timeline scene or questions differ")
    forms = {}
    rubrics = {}
    for question in raw["questions"]:
        task_id = question.get("id")
        if task_id not in _IDS:
            raise ValueError("Network incident timeline question ID differs")
        prompts = _TIMED_QUESTIONS.get(task_id, _QUESTIONS.get(task_id))
        if question.get("prompt") not in prompts:
            raise ValueError("Network incident timeline wording differs")
        forms[task_id] = f"{task_id}-q{prompts.index(question['prompt']) + 1}"
        marking = question.get("marking")
        if not isinstance(marking, list) or not marking:
            raise ValueError("Network incident timeline marking differs")
        criterion = marking[0].get("criterion", "")
        rubrics[task_id] = f"{task_id}-r{2 if criterion.startswith('Vérifier ') else 1}"
    if set(forms) != set(_IDS):
        raise ValueError("Network incident timeline question set differs")
    expected = render_network_incident_timeline_candidate(
        contract,
        {"scene_id": scene, "question_forms": forms, "rubric_forms": rubrics},
        task_specs,
    )
    if raw != expected:
        raise ValueError("Network incident timeline candidate differs from catalogue")
