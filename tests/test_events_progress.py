"""Progress follows completed work and never runs backwards during a job."""

import json

import pytest

from Backend.Core.events import GenerationUpdate, progress_emitter


@pytest.mark.parametrize(
    "prefix", ["Calibrating difficulty", "Checking reference demand"]
)
def test_independent_review_advances_at_each_real_item_boundary(capsys, prefix):
    progress = progress_emitter()
    progress("Generated question 10/10")
    capsys.readouterr()
    values = []
    for index in range(1, 4):
        progress(f"{prefix} {index}/3: 1a")
        values.append(json.loads(capsys.readouterr().out)["progress"])
    assert values[0] == pytest.approx(0.78)
    assert values[0] < values[1] < values[2] < 0.82
    progress("Validating paper")
    assert json.loads(capsys.readouterr().out)["progress"] == pytest.approx(0.82)


def test_legacy_status_messages_do_not_move_progress_backwards(capsys):
    progress = progress_emitter()
    progress(
        GenerationUpdate(
            stage="review", message="Reviewed", completed_units=1, total_units=1
        )
    )
    prior = json.loads(capsys.readouterr().out)["progress"]
    progress("Using built-in draft questions")
    assert json.loads(capsys.readouterr().out)["progress"] == prior


@pytest.mark.parametrize("counts", ["0/3", "4/3", "1/0"])
def test_invalid_review_counts_do_not_invent_progress(capsys, counts):
    progress = progress_emitter()
    progress("Generated question 10/10")
    prior = json.loads(capsys.readouterr().out)["progress"]
    progress(f"Calibrating difficulty {counts}: 1a")
    assert json.loads(capsys.readouterr().out)["progress"] == prior
