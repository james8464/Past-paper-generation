# V26 printed recovery chronology stays bound to its contract.

from copy import deepcopy

import pymupdf
import pytest

from Backend.Core.france.network_incident_timeline_contract import (
    build_network_incident_timeline_contract,
)
from Backend.Core.france.network_incident_timeline_prose import (
    render_network_incident_timeline_candidate,
)
from Backend.Core.france.nsi import NSIExercise
from Backend.Core.france.pipeline import _tasks_for_seed_v26
from Backend.Core.france.rendering import render_assessment
from Backend.Core.france.runtime import validate_network_incident_timeline_pdf


def _exercise(revision=1):
    ids = [f"3{x}" for x in "abcdefghijkl"]
    selection = {
        "scene_id": "station",
        "question_forms": {q: f"{q}-q1" for q in ids},
        "rubric_forms": {q: f"{q}-r1" for q in ids},
    }
    return NSIExercise.model_validate(
        render_network_incident_timeline_candidate(
            build_network_incident_timeline_contract(270100),
            selection,
            _tasks_for_seed_v26(270100)[2]["question_blueprint"],
            revision=revision,
        )
    )


@pytest.mark.parametrize("correction", [False, True])
@pytest.mark.parametrize("revision", [1, 2])
def test_v26_pdf_prints_working_chronology_without_subject_answers(
    tmp_path, correction, revision
):
    exercise = _exercise(revision)
    path = tmp_path / "timeline.pdf"
    render_assessment(path, [exercise], correction=correction)
    validate_network_incident_timeline_pdf(
        path,
        build_network_incident_timeline_contract(270100),
        correction=correction,
        exercise=exercise,
        revision=revision,
    )
    with pymupdf.open(path) as pdf:
        text = " ".join(page.get_text() for page in pdf)
        assert "Échéances et chronologie" in text
        assert "t=29" in text
        assert ("t=22" in text) == correction
        if revision == 2 and correction:
            assert "terminal compromis" in " ".join(text.split())
    if revision == 2:
        with pytest.raises(ValueError, match=r"wording|catalogue"):
            validate_network_incident_timeline_pdf(
                path,
                build_network_incident_timeline_contract(270100),
                correction=correction,
                exercise=exercise,
                revision=1,
            )


def test_v26_pdf_rejects_changed_chronology_and_subject_answer_leak(tmp_path):
    contract = build_network_incident_timeline_contract(270100)
    exercise = _exercise()
    bad = deepcopy(exercise.model_dump(mode="json"))
    bad["materials"][2]["rows"][3][1] = "3"
    bad_exercise = NSIExercise.model_validate(bad)
    path = tmp_path / "changed.pdf"
    render_assessment(path, [bad_exercise], correction=False)
    with pytest.raises(ValueError):
        validate_network_incident_timeline_pdf(
            path, contract, correction=False, exercise=bad_exercise
        )
    render_assessment(path, [exercise], correction=True)
    with pytest.raises(ValueError):
        validate_network_incident_timeline_pdf(
            path, contract, correction=False, exercise=exercise
        )
