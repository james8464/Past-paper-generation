"""Private Python recovery specifications; not native/public release acceptance."""

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
    subject.validate_rejected_rounds(caught.value.details)
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


def rehash(package):
    package["identity"]["content_sha256"] = subject._digest(
        {key: value for key, value in package.items() if key != "identity"}
    )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p["identity"].pop("review_recovery_policy"),
        lambda p: p["identity"].update(review_recovery_policy=True),
        lambda p: p["identity"].update(review_recovery_policy="unknown"),
        lambda p: p.pop("exercise_attempts"),
        lambda p: p["exercise_attempts"][0]["rounds"].pop(0),
        lambda p: p["exercise_attempts"][0]["rounds"].reverse(),
        lambda p: p["exercise_attempts"][0].update(accepted_round=True),
        lambda p: p["exercise_attempts"][0]["rounds"][0].update(outcome="accepted"),
        lambda p: p["exercise_attempts"][0]["rounds"][0].update(refusal=None),
        lambda p: p["exercise_attempts"][0]["rounds"][1]["request"].update(
            generation_seed=42
        ),
        lambda p: p["exercise_attempts"][0]["rounds"][0]["author_response"].update(
            title="modifié"
        ),
        lambda p: p["exercise_attempts"][0]["rounds"][0]["blind_response"][
            "answers"
        ].update({"1": "modifié"}),
        lambda p: p["exercise_attempts"][0]["rounds"][0]["review_response"]["1"].update(
            correct=True
        ),
    ],
)
def test_replay_rejects_round_tampering_even_with_new_outer_hash(tmp_path, mutate):
    package = generate(tmp_path, ReviewedClient())
    mutate(package)
    rehash(package)
    with pytest.raises((ValueError, ValidationError)):
        subject.validate_package(package)


def test_replay_rejects_forged_rejection_even_if_nested_hash_recomputed(tmp_path):
    package = generate(tmp_path, ReviewedClient())
    record = package["exercise_attempts"][0]["rounds"][0]
    record["review_response"]["1"]["correct"] = True
    record["review_response"]["1"]["issues"] = []
    record["review_response_sha256"] = subject._digest(record["review_response"])
    rehash(package)
    with pytest.raises(ValueError):
        subject.validate_package(package)


@pytest.mark.parametrize(
    "field,value",
    [
        ("attempt", True),
        ("attempt", 1.0),
        ("output_budget", 8192.0),
        ("temperature", "0.2"),
    ],
)
def test_replay_requires_strict_request_scalar_types(tmp_path, field, value):
    package = generate(tmp_path, ReviewedClient())
    package["exercise_attempts"][0]["rounds"][0]["request"][field] = value
    rehash(package)
    with pytest.raises(ValueError):
        subject.validate_package(package)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p["exercise_attempts"][0]["rounds"][1]["author_response"].update(
            title="une autre rédaction"
        ),
        lambda p: p["exercise_attempts"][0]["rounds"][0]["review_response"]["1"].update(
            correct="false"
        ),
        lambda p: p["exercise_attempts"][0]["rounds"][0]["author_response"].update(
            context="```python\nopen('secret')\n```"
        ),
    ],
)
def test_replay_rechecks_admission_and_links_after_rehashing_raw_evidence(
    tmp_path, mutate
):
    package = generate(tmp_path, ReviewedClient())
    mutate(package)
    for record in package["exercise_attempts"][0]["rounds"]:
        for name in ("author_response", "blind_response", "review_response"):
            record[name + "_sha256"] = subject._digest(record[name])
    rehash(package)
    with pytest.raises((ValueError, ValidationError)):
        subject.validate_package(package)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.pop("recovery_identity"),
        lambda d: d["recovery_identity"].update(review_recovery_policy=True),
        lambda d: d["exercise_attempts"][-1]["rounds"].pop(),
        lambda d: d["exercise_attempts"][-1]["rounds"].reverse(),
        lambda d: d["exercise_attempts"][-1].update(accepted_round=2),
        lambda d: d.update(stage="invented"),
    ],
)
def test_terminal_refusal_evidence_rejects_missing_or_modified_rounds(tmp_path, mutate):
    with pytest.raises(subject.SemanticReviewRefusal) as caught:
        generate(tmp_path, ReviewedClient(refuse_rounds=(1, 2)))
    details = caught.value.details
    mutate(details)
    with pytest.raises(ValueError):
        subject.validate_rejected_rounds(details)


@pytest.mark.parametrize(
    "failure,error",
    [
        ("unsafe", ValueError),
        ("malformed", ValidationError),
        ("transport", RuntimeError),
        ("cancel", KeyboardInterrupt),
    ],
)
def test_nonsemantic_failure_in_second_cycle_still_hard_exits(tmp_path, failure, error):
    class SecondCycleClient(ReviewedClient):
        def generate_request(self, request):
            if self.authors.get("1", 0) >= 1 and "id" in request.schema["properties"]:
                self.failure = failure
            return super().generate_request(request)

    client = SecondCycleClient()
    with pytest.raises(error) as caught:
        generate(tmp_path, client)
    assert not isinstance(caught.value, subject.SemanticReviewRefusal)
    assert client.authors == {"1": 2}
    assert len(client.requests) == (4 if failure == "unsafe" else 6)


def test_terminal_later_refusal_preserves_and_revalidates_prior_accepted_rounds(
    tmp_path,
):
    client = ReviewedClient(refuse_exercise="3", refuse_rounds=(1, 2))
    with pytest.raises(subject.SemanticReviewRefusal) as caught:
        generate(tmp_path, client)
    details = caught.value.details
    assert len(client.requests) == 12
    assert [h["accepted_round"] for h in details["exercise_attempts"]] == [1, 1, None]
    subject.validate_rejected_rounds(details)
    details["exercise_attempts"][0]["rounds"][0]["author_response"]["title"] = "modifié"
    with pytest.raises(ValueError):
        subject.validate_rejected_rounds(details)


def test_rejected_topics_never_enter_replacement_or_next_scope(tmp_path):
    import json

    class TopicClient(ReviewedClient):
        def generate_request(self, request):
            response = super().generate_request(request)
            if (
                "id" in request.schema["properties"]
                and response["id"] == "1"
                and self.authors["1"] == 1
            ):
                extra = next(
                    t for t in sorted(subject.TOPICS) if t not in response["topics"]
                )
                response["topics"].append(extra)
            return response

    client = TopicClient()
    package = generate(tmp_path, client)
    requests = [r for r in client.requests if "id" in r.schema["properties"]]
    data = [
        json.loads(r.prompt.split("DONNÉES_JSON\n")[1].split("\nOUTPUT_SCHEMA=")[0])
        for r in requests
    ]
    assert data[0]["previous_topics"] == data[1]["previous_topics"] == []
    assert data[2]["previous_topics"] == sorted(package["exercises"][0]["topics"])
    assert "NOUVELLE_RÉDACTION" in requests[1].prompt
    assert "NOUVELLE_RÉDACTION" not in requests[2].prompt


def test_worst_case_is_twenty_four_calls_with_both_format_and_semantic_recovery(
    tmp_path,
):
    class AllRoundsClient(ReviewedClient):
        def __init__(self):
            super().__init__()
            self.physical_authors = {}
            self.semantic = {}

        def generate_request(self, request):
            response = super().generate_request(request)
            props = request.schema["properties"]
            if "id" in props:
                identifier = response["id"]
                self.physical_authors[identifier] = (
                    self.physical_authors.get(identifier, 0) + 1
                )
                count = self.physical_authors[identifier]
                self.semantic[identifier] = 1 if count <= 2 else 2
                if count % 2:
                    response.pop("title")
            elif "answers" not in props:
                response["1"]["correct"] = self.semantic[self.active] == 2
                response["1"]["issues"] = (
                    [] if self.semantic[self.active] == 2 else ["Désaccord de fond."]
                )
            return response

    client = AllRoundsClient()
    package = generate(tmp_path, client)
    assert len(client.requests) == 24
    assert [h["accepted_round"] for h in package["exercise_attempts"]] == [2, 2, 2]
    assert [a["attempts"] for a in package["authoring_attempts"]] == [2, 2, 2]
    assert subject.validate_package(package)


@pytest.mark.parametrize("seed", [-(2**31), 2**31 - 1, 2**31 - 4])
@pytest.mark.parametrize("identifier", ["1", "2", "3"])
@pytest.mark.parametrize("number", [1, 2])
def test_author_and_review_seeds_wrap_deterministically_into_signed_range(
    seed, identifier, number
):
    from types import SimpleNamespace

    scope = {
        "references": [],
        "primary_topic": subject.curriculum_plan(seed)[int(identifier) - 1],
    }
    request, identity = subject._round_request(
        SimpleNamespace(provider="ollama"),
        scope,
        seed,
        identifier,
        number,
        set(),
        False,
        None if number == 1 else {"issue": "Refus indépendant."},
    )
    unwrapped = seed + int(identifier) + (1_000_003 if number == 2 else 0)
    expected = (unwrapped + 2**31) % 2**32 - 2**31
    assert request.generation_seed == identity["generation_seed"] == expected
    assert identity["review_seed"] == (expected + 100 + 2**31) % 2**32 - 2**31
    assert -(2**31) <= request.generation_seed <= 2**31 - 1
    assert -(2**31) <= identity["review_seed"] <= 2**31 - 1
    if number == 1 and -(2**31) <= unwrapped <= 2**31 - 1:
        assert request.generation_seed == unwrapped


@pytest.mark.parametrize("seed", [-(2**31), 2**31 - 1])
def test_edge_seeds_replay_all_three_exercises_and_both_semantic_rounds(tmp_path, seed):
    from tests.test_nsi_pipeline import make_index

    class EveryExerciseClient(ReviewedClient):
        def generate_request(self, request):
            response = super().generate_request(request)
            props = request.schema["properties"]
            if "id" not in props and "answers" not in props:
                first = self.authors[self.active] == 1
                response["1"]["correct"] = not first
                response["1"]["issues"] = ["Désaccord de fond."] if first else []
            return response

    path = tmp_path / "index.sqlite"
    make_index(path)
    client = EveryExerciseClient()
    package = subject.generate(index_path=path, client=client, seed=seed)
    assert len(client.requests) == 18
    assert [h["accepted_round"] for h in package["exercise_attempts"]] == [2, 2, 2]
    assert all(-(2**31) <= r.generation_seed <= 2**31 - 1 for r in client.requests)
    assert subject.validate_package(package)


@pytest.mark.parametrize("value", [True, 1.0, "1", None])
def test_phase_seed_requires_strict_integer(value):
    with pytest.raises(ValueError):
        subject._signed_phase_seed(value)
