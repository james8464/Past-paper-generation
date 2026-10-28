# V27 credits every requested security limit without changing historical V26

from decimal import Decimal

import pytest

from Backend.Core.france.network_incident_timeline_contract import (
    build_network_incident_timeline_contract,
)
from Backend.Core.france.network_incident_timeline_prose import (
    render_network_incident_timeline_candidate,
)
from Backend.Core.france.pipeline import _tasks_for_seed_v26


@pytest.mark.parametrize("seed", [270100, 270101, 270102])
@pytest.mark.parametrize("form", [1, 2])
def test_revision_two_credits_deadlines_and_terminal_without_repeating_metadata(
    seed, form
):
    selection = {
        "scene_id": "station",
        "question_forms": {f"3{x}": f"3{x}-q{form}" for x in "abcdefghijkl"},
        "rubric_forms": {f"3{x}": f"3{x}-r{form}" for x in "abcdefghijkl"},
    }
    contract = build_network_incident_timeline_contract(seed)
    specs = _tasks_for_seed_v26(seed)[2]["question_blueprint"]
    old = render_network_incident_timeline_candidate(contract, selection, specs)
    new = render_network_incident_timeline_candidate(
        contract, selection, specs, revision=2
    )
    question = new["questions"][-1]
    criteria = " ".join(mark["criterion"] for mark in question["marking"])
    assert "échéance" in criteria
    assert "métadonnées" not in criteria
    assert "métadonnées" not in question["prompt"]
    assert "terminal compromis" in criteria
    assert sum(Decimal(mark["points"]) for mark in question["marking"]) == Decimal(
        question["points"]
    )
    assert new["questions"][:-1] == old["questions"][:-1]
    assert criteria.count("terminal compromis") == 1
    if question["points"] == "0.5":
        assert "terminal compromis" not in " ".join(
            mark["criterion"] for mark in old["questions"][-1]["marking"]
        )
