from copy import deepcopy

import pytest

from Backend.Core.france import llm_pipeline as subject
from Backend.Core.generation_diagnostics import GenerationEvidenceError
from tests.test_french_llm_pipeline import generate
from tests.test_french_reviewed_redraft import ReviewedClient


def test_rejected_round_is_recorded_before_another_model_call(tmp_path, monkeypatch):
    snapshots = []

    class Client(ReviewedClient):
        def generate_request(self, request):
            if len(self.requests) == 3:
                assert (
                    snapshots[-1]["exercise_attempts"][0]["rounds"][0]["outcome"]
                    == "rejected"
                )
            return super().generate_request(request)

    original = subject.generate

    def recording_generate(**kwargs):
        return original(**kwargs, record_round=snapshots.append)

    monkeypatch.setattr(subject, "generate", recording_generate)
    result = generate(tmp_path, Client())
    assert len(snapshots) == 4
    assert snapshots[-1]["state"] == "review_complete"
    assert snapshots[-1]["exercise_attempts"] == result["exercise_attempts"]
    assert snapshots[0]["exercise_attempts"][0]["accepted_round"] is None
    assert len(snapshots[0]["exercise_attempts"]) == 1
    assert snapshots[0]["teacher_review"] == "not_run"
    assert snapshots[0]["empirical_calibration"] == "not_run"


def test_terminal_refusal_is_recorded_without_approving_it(tmp_path, monkeypatch):
    snapshots = []
    original = subject.generate
    monkeypatch.setattr(
        subject,
        "generate",
        lambda **kwargs: original(**kwargs, record_round=snapshots.append),
    )
    with pytest.raises(subject.SemanticReviewRefusal):
        generate(tmp_path, ReviewedClient(refuse_rounds=(1, 2)))
    assert len(snapshots) == 2
    assert snapshots[-1]["state"] == "refused"
    subject.validate_rejected_rounds(snapshots[-1])
    assert snapshots[-1]["exercise_attempts"][0]["accepted_round"] is None
    assert [
        item["outcome"] for item in snapshots[-1]["exercise_attempts"][0]["rounds"]
    ] == ["rejected", "rejected"]


def test_storage_failure_stops_before_another_model_call(tmp_path, monkeypatch):
    client = ReviewedClient()
    original = subject.generate

    def fail(snapshot):
        raise OSError("storage unavailable")

    monkeypatch.setattr(
        subject, "generate", lambda **kwargs: original(**kwargs, record_round=fail)
    )
    with pytest.raises(GenerationEvidenceError) as caught:
        generate(tmp_path, client)
    assert not isinstance(caught.value, subject.SemanticReviewRefusal)
    assert caught.value.details["snapshot_saved"] is False
    assert len(client.requests) == 3


def test_recorder_cannot_mutate_the_generation_history(tmp_path, monkeypatch):
    original = subject.generate
    saved = []

    def mutate(snapshot):
        saved.append(deepcopy(snapshot))
        snapshot["exercise_attempts"].clear()

    monkeypatch.setattr(
        subject, "generate", lambda **kwargs: original(**kwargs, record_round=mutate)
    )
    result = generate(tmp_path, ReviewedClient())
    assert len(result["exercise_attempts"]) == 3
    assert saved[-1]["exercise_attempts"] == result["exercise_attempts"]
