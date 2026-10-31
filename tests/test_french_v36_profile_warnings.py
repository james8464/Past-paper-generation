"""Subjective labels warn in V36; objective admission checks remain mandatory."""

from copy import deepcopy

import pytest
from jsonschema.exceptions import ValidationError as SchemaValidationError

from Backend.Core.france import llm_pipeline as subject
from Backend.Core.france.nsi import (
    NSIExercise,
    authoring_schema,
    require_authoring_fields,
)
from tests.test_french_llm_pipeline import Client, generate, raw_exercise


def low_labels(raw):
    for question in raw["questions"]:
        question.update(operation="recall", difficulty=1)


def material_free(raw):
    raw["materials"] = []
    for question in raw["questions"]:
        question["material_ids"] = []


def test_low_cognitive_self_labels_warn_in_v36_but_historical_default_stays_strict(
    tmp_path,
):
    raw = raw_exercise()
    low_labels(raw)
    with pytest.raises(ValueError, match="Progression"):
        NSIExercise.model_validate(raw)
    assert subject.validate_authored_exercise(raw, "1")
    package = generate(tmp_path, Client(mutate=low_labels))
    warnings = [
        item for item in package["warnings"] if item["state"] == "profile_warning"
    ]
    assert len(warnings) == 3
    assert all(item["code"] == "self_reported_cognitive_profile" for item in warnings)
    assert all(
        item["question_id"] == "1" and "étiquettes" in item["reason"]
        for item in warnings
    )
    assert len(subject.validate_package(package)) == 3


def test_repeated_broad_topic_is_a_profile_warning_not_a_question_rewrite(tmp_path):
    def repeat(raw):
        raw["topics"] = ["structures-donnees"]
        for question in raw["questions"]:
            question["curriculum_codes"] = ["SD-LINEAIRE"]

    exercises = []
    for identifier in ("1", "2", "3"):
        raw = raw_exercise(identifier)
        repeat(raw)
        exercises.append(subject.validate_authored_exercise(raw, identifier))
    _, evidence_warnings = subject._verification_evidence(exercises)
    warnings = [
        item
        for item in evidence_warnings
        if item.get("code") == "repeated_broad_topics"
    ]
    assert [item["exercise_id"] for item in warnings] == ["2", "3"]
    assert all(item["question_id"] == "1" for item in warnings)
    assert [list(item.topics) for item in exercises] == [["structures-donnees"]] * 3
    # Current source scoping additionally requires each assigned primary domain.
    with pytest.raises(ValueError, match="domaine principal"):
        generate(tmp_path, Client(mutate=repeat))


def test_explicit_material_free_v36_is_valid_but_missing_field_and_legacy_generation_refuse(
    tmp_path,
):
    raw = raw_exercise()
    material_free(raw)
    assert subject.validate_authored_exercise(raw, "1").materials == ()
    with pytest.raises(ValueError, match="materials"):
        require_authoring_fields(raw)
    assert authoring_schema()["properties"]["materials"]["minItems"] == 1
    omitted = deepcopy(raw)
    omitted.pop("materials")
    with pytest.raises((ValueError, SchemaValidationError)):
        subject.validate_authored_exercise(omitted, "1")
    package = generate(tmp_path, Client(mutate=material_free))
    assert all(not item["materials"] for item in package["exercises"])
    assert len(subject.validate_package(package)) == 3


@pytest.mark.parametrize(
    "change",
    [
        lambda raw: raw["questions"][0].update(points="2"),
        lambda raw: raw["questions"][0].update(answer=""),
        lambda raw: raw["questions"][0].update(answer="   "),
        lambda raw: raw["questions"][0].update(answer="```python\nopen('secret')\n```"),
        lambda raw: raw["questions"][0].update(curriculum_codes=["NON-NSI"]),
    ],
)
def test_v36_profile_context_cannot_skip_objective_rejections(change):
    raw = raw_exercise()
    low_labels(raw)
    change(raw)
    with pytest.raises((ValueError, SchemaValidationError)):
        subject.validate_authored_exercise(raw, "1")


def test_profile_warnings_cannot_be_removed_from_rehashed_package(tmp_path):
    package = generate(tmp_path, Client(mutate=low_labels))
    package["warnings"] = [
        item for item in package["warnings"] if item["state"] != "profile_warning"
    ]
    package["identity"]["content_sha256"] = subject._digest(
        {key: value for key, value in package.items() if key != "identity"}
    )
    with pytest.raises(ValueError, match="limites"):
        subject.validate_package(package)


@pytest.mark.parametrize("review_field", ["answer_complete", "curriculum_aligned"])
def test_low_labels_do_not_override_negative_answer_review(tmp_path, review_field):
    class Negative(Client):
        def generate_request(self, request):
            result = super().generate_request(request)
            if "1" in result:
                result["1"][review_field] = False
            return result

    client = Negative(mutate=low_labels)
    with pytest.raises(ValueError, match="refuse"):
        generate(tmp_path, client)
    assert len(client.requests) == 6


@pytest.mark.parametrize(
    "mode", ["objective_domain_omitted", "declared_domain_uncovered"]
)
def test_domain_label_mismatch_warns_only_in_v36_and_preserves_model_fields(
    tmp_path, mode
):
    def mismatch(raw):
        if mode == "objective_domain_omitted":
            raw["questions"][0]["curriculum_codes"] = ["ALG-GRAPHES"]
        else:
            raw["topics"].append("algorithmique")

    raw = raw_exercise()
    primary_topic = subject.curriculum_plan(42)[0]
    raw["topics"] = [primary_topic]
    primary_code = next(
        code
        for code, (topic, _) in subject.CURRICULUM_OBJECTIVES.items()
        if topic == primary_topic
    )
    for question in raw["questions"]:
        question["curriculum_codes"] = [primary_code]
    mismatch(raw)
    with pytest.raises(ValueError, match=r"Capacité incompatible|thème annoncé"):
        NSIExercise.model_validate(raw)
    assert (
        subject.validate_authored_exercise(raw, "1").model_dump(mode="json")["topics"]
        == raw["topics"]
    )
    package = generate(tmp_path, Client(mutate=mismatch))
    warnings = [
        item
        for item in package["warnings"]
        if item.get("code") == "declared_domain_profile"
    ]
    assert len(warnings) == 3
    assert all(
        item["state"] == "profile_warning" and item["question_id"] == "1"
        for item in warnings
    )
    assert package["exercises"][0]["topics"] == raw["topics"]
    assert (
        package["exercises"][0]["questions"][0]["curriculum_codes"]
        == raw["questions"][0]["curriculum_codes"]
    )
    assert len(subject.validate_package(package)) == 3


@pytest.mark.parametrize(
    "change",
    [
        lambda raw: raw.update(topics=["comptabilité"]),
        lambda raw: raw["questions"][0].update(curriculum_codes=["UK-AO1"]),
        lambda raw: raw["questions"][0].update(material_ids=["document_absent"]),
    ],
)
def test_domain_warning_context_still_refuses_unknown_taxonomy_and_missing_documents(
    change,
):
    raw = raw_exercise()
    raw["questions"][0]["curriculum_codes"] = ["ALG-GRAPHES"]
    change(raw)
    with pytest.raises((ValueError, SchemaValidationError)):
        subject.validate_authored_exercise(raw, "1")


def test_indicative_question_time_sum_warns_without_changing_official_duration(
    tmp_path,
):
    def mismatch(raw):
        for question in raw["questions"]:
            question["estimated_minutes"] = 10

    raw = raw_exercise()
    mismatch(raw)
    with pytest.raises(ValueError, match="temps des questions"):
        NSIExercise.model_validate(raw)
    assert subject.validate_authored_exercise(raw, "1").minutes == 70
    package = generate(tmp_path, Client(mutate=mismatch))
    warnings = [
        item
        for item in package["warnings"]
        if item.get("code") == "indicative_time_sum"
    ]
    assert len(warnings) == 3
    assert all(
        item["question_estimated_minutes"] == 60
        and item["exercise_allocated_minutes"] == 70
        for item in warnings
    )
    assert package["minutes"] == 210
    assert all(exercise["minutes"] == 70 for exercise in package["exercises"])
    assert all(
        sum(question["estimated_minutes"] for question in exercise["questions"]) == 60
        for exercise in package["exercises"]
    )
    assert len(subject.validate_package(package)) == 3
