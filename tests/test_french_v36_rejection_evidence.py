"""Rejected model reviews keep private evidence, never approved output."""

import json
import stat

import pytest
from jsonschema.exceptions import ValidationError

from Backend.Core.france import llm_pipeline as subject
from Backend.Core.generation_diagnostics import (
    GenerationEvidenceError,
    save_failure_diagnostic,
)
from tests.test_french_llm_pipeline import Client, raw_exercise
from tests.test_french_llm_runtime import publication as publication


class RejectingClient(Client):
    def __init__(self, mode):
        super().__init__()
        self.mode = mode

    def generate_request(self, request):
        properties = request.schema["properties"]
        if "blind_issue_dispositions" in properties:
            self.requests.append(request)
            return {
                "question_review": {
                    identifier: {
                        name: [] if name == "issues" else True
                        for name in item["properties"]
                    }
                    for identifier, item in properties["question_review"][
                        "properties"
                    ].items()
                },
                "blind_issue_dispositions": {
                    index: {
                        "issue_index": int(index),
                        "blocking": True,
                        "rationale": "Une donnée indispensable manque à la résolution.",
                    }
                    for index in properties["blind_issue_dispositions"]["properties"]
                },
            }
        result = super().generate_request(request)
        if "answers" in request.schema["properties"] and self.mode == "blind":
            result["issues"] = ["Donnée absente private-token " + "x" * 20_000]
        elif "1" in result and "correct" in result["1"]:
            if self.mode == "flag":
                result["1"]["correct"] = False
            elif self.mode == "issues":
                result["1"]["issues"] = [
                    "Réponse contradictoire private-token " + "x" * 20_000
                ]
            elif self.mode == "malformed":
                result["1"]["correct"] = "false"
        return result


@pytest.mark.parametrize("mode", ["blind", "flag", "issues"])
def test_review_rejection_retains_bounded_private_evidence(tmp_path, mode):
    exercise = subject.validate_authored_exercise(raw_exercise(), "1")
    client = RejectingClient(mode)
    with pytest.raises(GenerationEvidenceError, match="exercice 1") as caught:
        subject._review(client, exercise, 42, [])
    error = caught.value
    assert error.details["exercise_sha256"] == subject._digest(
        exercise.model_dump(mode="json")
    )
    assert error.details["stage"] == (
        "blind_solution" if mode == "blind" else "question_review"
    )
    assert "answers" not in error.details and "prompt" not in error.details
    assert len(client.requests) == 2
    if mode != "blind":
        assert "question 1" in str(error)
        assert error.details["question_reviews"][0]["question_id"] == "1"
        assert error.details["question_reviews"][0]["failed_flags"] == (
            ["correct"] if mode == "flag" else []
        )
    assert "private-token" not in str(error)
    path = save_failure_diagnostic(tmp_path, error, secrets=("private-token",))
    assert path is not None
    text = path.read_text()
    assert path.stat().st_size < 8_192
    assert "private-token" not in text
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert set(tmp_path.iterdir()) == {path.parent}


def test_malformed_review_is_not_recast_as_valid_review_evidence():
    exercise = subject.validate_authored_exercise(raw_exercise(), "1")
    with pytest.raises(ValidationError):
        subject._review(RejectingClient("malformed"), exercise, 42, [])


@pytest.mark.parametrize(
    ("flag", "label"),
    [
        ("correct", "réponse incorrecte"),
        ("answer_complete", "corrigé incomplet"),
        ("rubric_consistent", "barème incohérent"),
        ("curriculum_aligned", "programme non respecté"),
        ("french", "texte non français"),
        ("self_contained", "données manquantes"),
    ],
)
def test_public_rejection_categories_are_plain_french(flag, label):
    exercise = subject.validate_authored_exercise(raw_exercise(), "1")
    evidence = subject._review(Client(), exercise, 42, [])
    evidence["question_review"]["1"][flag] = False
    with pytest.raises(GenerationEvidenceError) as caught:
        subject._validate_review(exercise, evidence)
    assert label in str(caught.value)
    assert f"({flag})" not in str(caught.value)
    assert caught.value.details["question_reviews"][0]["failed_flags"] == [flag]


def test_unknown_review_flags_fail_schema_before_message_formatting():
    exercise = subject.validate_authored_exercise(raw_exercise(), "1")
    evidence = subject._review(Client(), exercise, 42, [])
    evidence["question_review"]["1"]["invented_flag"] = False
    with pytest.raises(ValidationError):
        subject._validate_review(exercise, evidence)


def test_review_evidence_does_not_copy_successful_solutions_or_full_issue_text():
    exercise = subject.validate_authored_exercise(raw_exercise(), "1")
    client = Client()
    evidence = subject._review(client, exercise, 42, [])
    for item in evidence["question_review"].values():
        item["issues"] = ["x" * 20_000] * 20
    with pytest.raises(GenerationEvidenceError) as caught:
        subject._validate_review(exercise, evidence)
    details = caught.value.details
    assert details["rejected_question_count"] == 6
    assert all(len(item["issues"]) == 3 for item in details["question_reviews"])
    assert all(item["issue_count"] == 20 for item in details["question_reviews"])
    assert len(json.dumps(details).encode()) < 8_192
    assert "Solution indépendante" not in json.dumps(details)


@pytest.mark.parametrize("mode", ["blind", "flag", "issues"])
def test_rejected_review_publishes_no_pdf_package_or_success(
    publication, monkeypatch, mode
):
    runtime, args, events = publication
    args.api_key = "private-token"
    monkeypatch.setattr(
        runtime, "HostedLLMClient", lambda **kwargs: RejectingClient(mode)
    )
    assert runtime.handle_generate_llm_assessment(args) == 1
    assert not any(event["type"] in {"file", "done"} for event in events)
    assert "private-token" not in json.dumps(events)
    assert not list(args.output.rglob("*.pdf"))
    reports = list(args.output.rglob("failure-*.json"))
    assert len(reports) == 1
    assert "private-token" not in reports[0].read_text()
    assert json.loads(reports[0].read_text())["details"]["exercise_id"] == "1"
    assert not [
        path
        for path in args.output.rglob("*.json")
        if ".keldin-diagnostics" not in path.parts
    ]
