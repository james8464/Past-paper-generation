import json
from copy import deepcopy

import pytest
from jsonschema.exceptions import ValidationError

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


@pytest.mark.parametrize(
    "failure,error,calls,returned",
    [
        ("unsafe", ValueError, 1, {"author_response"}),
        ("transport", RuntimeError, 3, {"author_response", "blind_response"}),
        (
            "malformed",
            ValidationError,
            3,
            {"author_response", "blind_response", "review_response"},
        ),
    ],
)
def test_partial_nonsemantic_failure_keeps_returned_objects_without_retry(
    tmp_path, monkeypatch, failure, error, calls, returned
):
    snapshots = []
    original = subject.generate
    monkeypatch.setattr(
        subject,
        "generate",
        lambda **kwargs: original(**kwargs, record_round=snapshots.append),
    )
    client = ReviewedClient(failure=failure)
    with pytest.raises(error):
        generate(tmp_path, client)
    assert len(client.requests) == calls
    assert snapshots[-1]["state"] == "stopped"
    captured = snapshots[-1]["partial_round"]["returned"]
    assert {key for key in captured if key.endswith("_response")} == returned
    assert snapshots[-1]["exercise_attempts"][0]["accepted_round"] is None


def test_partial_storage_failure_keeps_the_original_error_type(tmp_path, monkeypatch):
    original = subject.generate

    def fail(snapshot):
        raise OSError("storage unavailable")

    monkeypatch.setattr(
        subject, "generate", lambda **kwargs: original(**kwargs, record_round=fail)
    )
    client = ReviewedClient(failure="malformed")
    with pytest.raises(ValidationError):
        generate(tmp_path, client)
    assert len(client.requests) == 3


def test_cancellation_does_not_wait_for_a_partial_snapshot(tmp_path, monkeypatch):
    original = subject.generate
    snapshots = []
    monkeypatch.setattr(
        subject,
        "generate",
        lambda **kwargs: original(**kwargs, record_round=snapshots.append),
    )
    with pytest.raises(KeyboardInterrupt):
        generate(tmp_path, ReviewedClient(failure="cancel"))
    assert snapshots == []


def test_later_transport_failure_retains_accepted_rounds_on_disk(tmp_path, monkeypatch):
    from Backend.Core.france.recovery_evidence import RecoveryEvidenceRecorder

    recorder = RecoveryEvidenceRecorder(tmp_path)
    original = subject.generate
    monkeypatch.setattr(
        subject, "generate", lambda **kwargs: original(**kwargs, record_round=recorder)
    )

    class Client(ReviewedClient):
        def generate_request(self, request):
            if self.active == "3" and "answers" in request.schema["properties"]:
                self.failure = "transport"
            return super().generate_request(request)

    client = Client(refuse_rounds=())
    with pytest.raises(RuntimeError, match="transport"):
        generate(tmp_path, client)
    assert len(client.requests) == 9
    paths = list((tmp_path / ".keldin-recovery").glob("*.json"))
    assert len(paths) == 1
    snapshot = json.loads(paths[0].read_text())["snapshot"]
    assert snapshot["state"] == "stopped"
    assert [history["accepted_round"] for history in snapshot["exercise_attempts"]] == [
        1,
        1,
        None,
    ]
    assert snapshot["partial_round"]["exercise_id"] == "3"
    assert recorder.retention_warning is None
