"""Prospective review advice never overrides a substantive refusal."""

import json
from copy import deepcopy

import pytest
from jsonschema.exceptions import ValidationError

from Backend.Core.france import llm_pipeline as subject
from tests.test_french_llm_pipeline import (
    BlindNoteClient,
    Client,
    generate,
    raw_exercise,
)

ADVICE = "Préférer le mot arc pour désigner un lien orienté."


class AdvisoryClient(Client):
    def generate_request(self, request):
        result = super().generate_request(request)
        if "1" in result and isinstance(result["1"], dict) and "correct" in result["1"]:
            for item in result.values():
                item["advisories"] = []
            result["1"]["advisories"] = [ADVICE]
        return result


def resign(package):
    package["identity"]["content_sha256"] = subject._digest(
        {key: value for key, value in package.items() if key != "identity"}
    )


def test_question_advice_is_a_typed_visible_recomputed_warning(tmp_path):
    client = AdvisoryClient()
    package = generate(tmp_path, client)
    warnings = [
        w for w in package["warnings"] if w.get("code") == "question_review_advisory"
    ]
    assert [(w["exercise_id"], w["question_id"], w["reason"]) for w in warnings] == [
        (identifier, "1", ADVICE) for identifier in ("1", "2", "3")
    ]
    assert all(w["state"] == "model_review_warning" for w in warnings)
    assert len(subject.validate_package(package)) == 3
    schema = client.requests[2].schema["properties"]["1"]
    assert "advisories" in schema["required"]
    assert "issues reste bloquant" in client.requests[2].prompt


@pytest.mark.parametrize(
    "value", [True, "note", [""], [" \t"], ["x" * 601], ["x"] * 4, [1]]
)
def test_malformed_advice_refuses_live_and_on_revalidation(value):
    exercise = subject.validate_authored_exercise(raw_exercise(), "1")

    class Malformed(AdvisoryClient):
        def generate_request(self, request):
            result = super().generate_request(request)
            if "1" in result and "correct" in result["1"]:
                result["1"]["advisories"] = value
            return result

    with pytest.raises(ValidationError):
        subject._review(Malformed(), exercise, 42, [])
    review = subject._review(AdvisoryClient(), exercise, 42, [])
    review["question_review"]["1"]["advisories"] = value
    with pytest.raises(ValidationError):
        subject._validate_review(exercise, review)


@pytest.mark.parametrize(
    "field",
    [
        "correct",
        "answer_complete",
        "rubric_consistent",
        "curriculum_aligned",
        "french",
        "self_contained",
        "issues",
    ],
)
def test_advice_cannot_override_negative_flags_or_original_nonblocking_prose(field):
    exercise = subject.validate_authored_exercise(raw_exercise(), "1")
    review = subject._review(AdvisoryClient(), exercise, 42, [])
    review["question_review"]["1"][field] = (
        ["Non bloquant : simple conseil."] if field == "issues" else False
    )
    with pytest.raises(ValueError, match="refuse"):
        subject._validate_review(exercise, review)


@pytest.mark.parametrize(
    "change",
    ["warning_removed", "warning_changed", "advice_changed", "one_field_omitted"],
)
def test_advisory_package_tampering_refuses_even_with_recomputed_content_digest(
    tmp_path, change
):
    package = generate(tmp_path, AdvisoryClient())
    if change == "warning_removed":
        package["warnings"] = [
            w
            for w in package["warnings"]
            if w.get("code") != "question_review_advisory"
        ]
    elif change == "warning_changed":
        next(
            w
            for w in package["warnings"]
            if w.get("code") == "question_review_advisory"
        )["reason"] = "Remplacé"
    elif change == "advice_changed":
        package["reviews"][0]["question_review"]["1"]["advisories"] = ["Remplacé"]
    else:
        package["reviews"][0]["question_review"]["1"].pop("advisories")
    resign(package)
    with pytest.raises((ValueError, ValidationError)):
        subject.validate_package(package)


def test_live_review_requires_channel_but_legacy_saved_review_shape_still_revalidates(
    tmp_path,
):
    exercise = subject.validate_authored_exercise(raw_exercise(), "1")

    class Missing(Client):
        def generate_request(self, request):
            result = super().generate_request(request)
            if "1" in result and "correct" in result["1"]:
                for item in result.values():
                    item.pop("advisories", None)
            return result

    with pytest.raises(ValidationError):
        subject._review(Missing(), exercise, 42, [])
    package = generate(tmp_path, Client())
    for review in package["reviews"]:
        for item in review["question_review"].values():
            item.pop("advisories")
    resign(package)
    assert len(subject.validate_package(package)) == 3
    assert (
        "advisories"
        not in subject._review_schema(exercise)["properties"]["1"]["properties"]
    )
    package["reviews"][0]["question_review"]["1"]["issues"] = [
        "Non bloquant : ancien conseil."
    ]
    resign(package)
    with pytest.raises(ValueError, match="refuse"):
        subject.validate_package(package)


def test_warning_order_follows_source_questions_not_model_object_key_order(tmp_path):
    class Reordered(AdvisoryClient):
        def generate_request(self, request):
            result = super().generate_request(request)
            if "1" in result and "correct" in result["1"]:
                result["2"]["advisories"] = ["Deuxième conseil facultatif."]
                return dict(reversed(list(result.items())))
            return result

    package = generate(tmp_path, Reordered())
    assert [
        w["question_id"]
        for w in package["warnings"]
        if w.get("code") == "question_review_advisory"
    ] == ["1", "2"] * 3
    assert subject.validate_package(json.loads(json.dumps(package, sort_keys=True)))


@pytest.mark.parametrize("field", ["correct", "issues"])
def test_live_negative_review_still_refuses_without_semantic_retry(field):
    class Rejected(AdvisoryClient):
        def generate_request(self, request):
            result = super().generate_request(request)
            if "1" in result and "correct" in result["1"]:
                result["1"][field] = (
                    ["Non bloquant : conseil dans le mauvais canal."]
                    if field == "issues"
                    else False
                )
            return result

    client = Rejected()
    exercise = subject.validate_authored_exercise(raw_exercise(), "1")
    with pytest.raises(ValueError, match="refuse"):
        subject._review(client, exercise, 42, [])
    assert len(client.requests) == 2


def test_blind_dispositions_and_question_advice_coexist_without_weakening_either(
    tmp_path,
):
    class Both(BlindNoteClient):
        def generate_request(self, request):
            result = super().generate_request(request)
            if "question_review" in result:
                for item in result["question_review"].values():
                    item["advisories"] = []
                result["question_review"]["1"]["advisories"] = [ADVICE]
            return result

    package = generate(tmp_path, Both())
    assert {w["code"] for w in package["warnings"] if "code" in w} >= {
        "blind_issue_nonblocking",
        "question_review_advisory",
    }
    changed = deepcopy(package)
    changed["reviews"][0]["blind_issue_dispositions"]["0"]["blocking"] = True
    resign(changed)
    with pytest.raises(ValueError, match="refuse"):
        subject.validate_package(changed)


def test_legacy_saved_blind_dispositions_without_advisory_fields_still_revalidate(
    tmp_path,
):
    package = generate(tmp_path, BlindNoteClient())
    for review in package["reviews"]:
        for item in review["question_review"].values():
            item.pop("advisories")
    resign(package)
    assert subject.validate_package(package)


def test_installed_mlx_compiles_prospective_review_with_and_without_blind_notes():
    llguidance = pytest.importorskip("llguidance")
    from Backend.Core.providers import _mlx_decoder_schema

    exercise = subject.validate_authored_exercise(raw_exercise(), "1")
    for notes in ([], ["Une convention mérite une précision."]):
        schema = subject._adjudication_schema(exercise, notes, include_advisories=True)
        grammar = llguidance.grammar_from(
            "json", json.dumps(_mlx_decoder_schema(schema))
        )
        assert not llguidance.LLMatcher.validate_grammar(grammar)
