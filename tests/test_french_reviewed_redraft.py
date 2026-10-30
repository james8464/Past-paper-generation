"""Private red specifications; bounded semantic re-drafting is not implemented."""

from copy import deepcopy

import pytest
from jsonschema.exceptions import ValidationError

from Backend.Core.france import llm_pipeline as subject
from Backend.Core.generation_diagnostics import GenerationEvidenceError
from tests.test_french_llm_pipeline import Client, generate

POLICY = "fr-nsi-v36-whole-exercise-redraft-v1"


class ReviewedClient(Client):
    def __init__(self, *, refuse_exercise="1", refuse_rounds=(1,), failure=None):
        super().__init__()
        self.refuse_exercise = refuse_exercise
        self.refuse_rounds = refuse_rounds
        self.failure = failure
        self.authors = {}
        self.author_objects = []
        self.blind_objects = []
        self.review_objects = []
        self.active = ""

    def generate_request(self, request):
        properties = request.schema["properties"]
        response = super().generate_request(request)
        if "id" in properties:
            self.active = response["id"]
            self.authors[self.active] = self.authors.get(self.active, 0) + 1
            number = self.authors[self.active]
            response["title"] += f" : rédaction {number}"
            for question in response["questions"]:
                question["answer"] += f" Proposition complète {number}."
            if self.failure == "unsafe":
                response["context"] += "\n```python\nopen('secret')\n```"
            self.author_objects.append(deepcopy(response))
        elif "answers" in properties:
            self.blind_objects.append(deepcopy(response))
        else:
            if self.failure == "transport":
                raise RuntimeError("transport")
            if self.failure == "cancel":
                raise KeyboardInterrupt()
            if self.failure == "malformed":
                response["1"]["correct"] = "false"
            elif (
                self.active == self.refuse_exercise
                and self.authors[self.active] in self.refuse_rounds
            ):
                response["1"]["correct"] = False
                response["1"]["issues"] = [
                    "La réponse contredit les données de la question."
                ]
            self.review_objects.append(deepcopy(response))
        return response


def test_semantic_refusal_gets_one_fresh_complete_cycle_with_intact_evidence(tmp_path):
    client = ReviewedClient()
    package = generate(tmp_path, client)
    assert len(client.requests) == 12
    assert client.authors == {"1": 2, "2": 1, "3": 1}
    assert package["identity"]["review_recovery_policy"] == POLICY
    record = package["exercise_attempts"][0]
    assert record["accepted_round"] == 2
    assert [round_["outcome"] for round_ in record["rounds"]] == [
        "rejected",
        "accepted",
    ]
    for index, round_ in enumerate(record["rounds"]):
        assert round_["author_response"] == client.author_objects[index]
        assert round_["blind_response"] == client.blind_objects[index]
        assert round_["review_response"] == client.review_objects[index]
        for field in ("author_response", "blind_response", "review_response"):
            assert round_[field + "_sha256"] == subject._digest(round_[field])
    assert (
        package["exercises"][0]["questions"][0]["answer"]
        == client.author_objects[1]["questions"][0]["answer"]
    )
    assert package["reviews"][0]["question_review"] == client.review_objects[1]
    assert package["teacher_review"] == package["empirical_calibration"] == "not_run"
    assert subject.validate_package(package)


def test_second_semantic_refusal_stops_and_retains_both_rounds(tmp_path):
    client = ReviewedClient(refuse_rounds=(1, 2))
    with pytest.raises(GenerationEvidenceError) as caught:
        generate(tmp_path, client)
    assert len(client.requests) == 6
    assert client.authors == {"1": 2}
    rounds = caught.value.details["exercise_attempts"][0]["rounds"]
    assert [round_["outcome"] for round_ in rounds] == ["rejected", "rejected"]
    assert [round_["author_response"] for round_ in rounds] == client.author_objects
    assert [round_["review_response"] for round_ in rounds] == client.review_objects
    assert not list(tmp_path.rglob("*.pdf"))


def test_later_refusal_does_not_regenerate_earlier_accepted_exercises(tmp_path):
    client = ReviewedClient(refuse_exercise="3")
    package = generate(tmp_path, client)
    assert client.authors == {"1": 1, "2": 1, "3": 2}
    assert len(client.requests) == 12
    for index in (0, 1):
        assert (
            package["exercises"][index]["title"]
            == client.author_objects[index]["title"]
        )


@pytest.mark.parametrize(
    "failure,error,calls",
    [
        ("unsafe", ValueError, 1),
        ("malformed", ValidationError, 3),
        ("transport", RuntimeError, 3),
        ("cancel", KeyboardInterrupt, 3),
    ],
)
def test_nonsemantic_failures_never_get_an_extra_author_cycle(
    tmp_path, failure, error, calls
):
    client = ReviewedClient(failure=failure)
    with pytest.raises(error):
        generate(tmp_path, client)
    assert len(client.requests) == calls
    assert client.authors == {"1": 1}
