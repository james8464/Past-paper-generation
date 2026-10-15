"""V23 PDF gates bind staged candidate evidence and correction credit."""

from copy import deepcopy

import pymupdf
import pytest

from Backend.Core.france.network_incident_contract import (
    build_network_incident_contract,
)
from Backend.Core.france.network_incident_prose import render_network_incident_candidate
from Backend.Core.france.nsi import NSIExercise
from Backend.Core.france.pipeline import _tasks_for_seed_v22
from Backend.Core.france.rendering import render_assessment


def _selection():
    return {
        "scene_id": "station",
        "question_forms": {f"3{x}": f"3{x}-q1" for x in "abcdefghijkl"},
        "rubric_forms": {f"3{x}": f"3{x}-r1" for x in "abcdefghijkl"},
    }


def _exercise():
    return NSIExercise.model_validate(
        render_network_incident_candidate(
            build_network_incident_contract(270100),
            _selection(),
            _tasks_for_seed_v22(270100)[2]["question_blueprint"],
        )
    )


def test_v23_runtime_dispatch_is_explicit_and_old_versions_stay_pinned():
    from Backend.Core.france.runtime import (
        database_pdf_contract_version,
        network_pdf_contract_version,
    )

    assert network_pdf_contract_version("fr-nsi-written-2027-v23") == "v23"
    assert database_pdf_contract_version("fr-nsi-written-2027-v23") == "v21"
    assert network_pdf_contract_version("fr-nsi-written-2027-v22") == "v18"
    assert network_pdf_contract_version("fr-nsi-written-2027-v25") == "v23"
    with pytest.raises(ValueError):
        network_pdf_contract_version("fr-nsi-written-2027-v26")


@pytest.mark.parametrize("large_print", [False, True])
@pytest.mark.parametrize("correction", [False, True])
def test_v23_pdf_has_bounded_pages_staged_materials_and_exact_roles(
    tmp_path, large_print, correction
):
    from Backend.Core.france.runtime import validate_network_incident_pdf

    exercise = _exercise()
    path = tmp_path / "incident.pdf"
    render_assessment(path, [exercise], correction=correction, large_print=large_print)
    validate_network_incident_pdf(
        path,
        build_network_incident_contract(270100),
        correction=correction,
        exercise=exercise,
    )
    with pymupdf.open(path) as pdf:
        pages = [page.get_text() for page in pdf]
        assert len(pages) <= (12 if large_print else 8)
        for title, question_id in (
            ("Liaisons et coûts initiaux", "3a"),
            ("Ressources et reprise à compléter", "3e"),
            ("Cartes après la reprise, à ordonner", "3i"),
        ):
            material_pages = [i for i, page in enumerate(pages) if title in page]
            question_pages = [
                i for i, page in enumerate(pages) if f"{question_id}." in page
            ]
            assert len(material_pages) == len(question_pages) == 1
            assert 0 <= question_pages[0] - material_pages[0] <= 1


def test_v23_pdf_rejects_changed_packet_evidence_and_subject_answer_leak(tmp_path):
    from Backend.Core.france.runtime import validate_network_incident_pdf

    contract = build_network_incident_contract(270100)
    raw = _exercise().model_dump(mode="json")
    bad = deepcopy(raw)
    bad["materials"][2]["rows"][0][1] = "t=20 min"
    bad_exercise = NSIExercise.model_validate(bad)
    path = tmp_path / "wrong.pdf"
    render_assessment(path, [bad_exercise], correction=False)
    with pytest.raises(ValueError):
        validate_network_incident_pdf(
            path, contract, correction=False, exercise=bad_exercise
        )
    render_assessment(path, [_exercise()], correction=True)
    with pytest.raises(ValueError):
        validate_network_incident_pdf(
            path, contract, correction=False, exercise=_exercise()
        )


@pytest.mark.parametrize("field", ["answer", "criterion", "material_ids"])
def test_v23_pdf_rejects_mutated_candidate_even_when_pdf_matches_it(tmp_path, field):
    from Backend.Core.france.runtime import validate_network_incident_pdf

    raw = _exercise().model_dump(mode="json")
    changed = deepcopy(raw)
    question = changed["questions"][3]
    if field == "answer":
        question["answer"] = "Le paquet arrive à l'heure."
    elif field == "criterion":
        question["marking"][0]["criterion"] = "Accorder pour une route erronée"
    else:
        question["material_ids"] = ["links", "route_working"]
    exercise = NSIExercise.model_validate(changed)
    path = tmp_path / "mutated.pdf"
    render_assessment(path, [exercise], correction=True)
    with pytest.raises(ValueError):
        validate_network_incident_pdf(
            path,
            build_network_incident_contract(270100),
            correction=True,
            exercise=exercise,
        )
