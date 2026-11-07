"""Numeric ownership is fixed before calls; content remains model authored."""

import json
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256

import pytest
from jsonschema import ValidationError as SchemaValidationError
from pydantic import ValidationError

from Backend.Core.france import llm_pipeline as subject
from Backend.Core.france.content_authoring import assemble_exercise
from Backend.Core.france.mark_plan import (
    CONTENT_ASSEMBLY_POLICY,
    MARK_PLAN_AUTHORING_POLICY,
    ExerciseMarkPlan,
    build_mark_plan,
    build_mark_plans,
    mark_plans_digest,
)
from Backend.Core.generation_diagnostics import GenerationEvidenceError
from tests.test_french_llm_pipeline import Client, raw_exercise
from tests.test_nsi_pipeline import make_index


class ContentClient(Client):
    def __init__(self, marker="Contenu inédit", *, malformed=0, semantic_refusal=False):
        super().__init__(marker)
        self.malformed = malformed
        self.semantic_refusal = semantic_refusal
        self.raw_returns = []

    def generate_request(self, request):
        if "DONNÉES_JSON\n" not in request.prompt:
            result = super().generate_request(request)
            if self.semantic_refusal and "answers" not in request.schema["properties"]:
                self.semantic_refusal = False
                first = next(iter(result.values()))
                first["rubric_consistent"] = False
                first["issues"] = ["Un critère exige une méthode non demandée."]
            return result
        self.requests.append(request)
        data = json.loads(
            request.prompt.split("DONNÉES_JSON\n")[1].split("\nOUTPUT_SCHEMA=")[0]
        )
        plan = data["mark_plan"]
        # This is a fake content writer, not production conversion of an old draft.
        template = raw_exercise(plan["exercise_id"], self.marker)
        template.pop("minutes")
        template.pop("target_points")
        topic = data.get("primary_topic", template["topics"][0])
        template["topics"] = [topic]
        code = next(
            code
            for code, (domain, _) in subject.CURRICULUM_OBJECTIVES.items()
            if domain == topic
        )
        questions = {}
        for index, slot in enumerate(plan["questions"]):
            question = deepcopy(template["questions"][index])
            question.pop("points")
            question.pop("id")
            question.update(
                curriculum_codes=[code],
                marking={
                    criterion["id"]: {
                        "criterion": f"Justification originale {index + 1}."
                    }
                    for criterion in slot["criteria"]
                },
            )
            questions[slot["id"]] = question
        template["questions"] = questions
        if self.malformed:
            self.malformed -= 1
            next(iter(template["questions"].values()))["points"] = "999"
        self.raw_returns.append(deepcopy(template))
        return template


def generate(tmp_path, client=None, record_round=None, *, seed=42, large_print=False):
    index = tmp_path / "references.sqlite"
    make_index(index)
    client = client or ContentClient()
    package = subject.generate(
        index_path=index,
        client=client,
        seed=seed,
        large_print=large_print,
        authoring_schema_policy=MARK_PLAN_AUTHORING_POLICY,
        record_round=record_round,
    )
    return package, client


def test_approved_numeric_profiles_are_exact_immutable_and_varied():
    profiles = set()
    for seed in range(24):
        plans = build_mark_plans(seed)
        assert tuple(plan.exercise_id for plan in plans) == ("1", "2", "3")
        for plan in plans:
            assert sum(q.points for q in plan.questions) == Decimal("6")
            profiles.add(tuple(q.points for q in plan.questions))
            for q in plan.questions:
                assert 1 <= len(q.criteria) <= 2
                assert all(
                    isinstance(c.points, Decimal) and c.points > 0 for c in q.criteria
                )
                assert sum(c.points for c in q.criteria) == q.points
            assert ExerciseMarkPlan.model_validate(plan.model_dump(mode="json")) == plan
            with pytest.raises(ValidationError):
                plan.exercise_id = "3"
        assert mark_plans_digest(plans) == mark_plans_digest(build_mark_plans(seed))
    assert profiles == {
        tuple(map(Decimal, values))
        for values in (
            ("1", "1", "2", "2"),
            ("0.5", "1", "1", "1.5", "2"),
            ("0.5", "0.5", "1", "1", "1.5", "1.5"),
        )
    }


@pytest.mark.parametrize(
    "bad", [0, -1, 0.5, "0", "-1", "NaN", "Infinity", "0.50", True]
)
def test_bad_or_noncanonical_allocations_refuse(bad):
    raw = build_mark_plan(42, "1").model_dump(mode="json")
    raw["questions"][0]["criteria"][0]["points"] = bad
    with pytest.raises((ValueError, ValidationError)):
        ExerciseMarkPlan.model_validate(raw)


@pytest.mark.parametrize("seed", [0, 42])
def test_full_opt_in_generation_and_replay_with_initial_plan_saved_before_call(
    tmp_path,
    seed,
):
    client = ContentClient()
    snapshots = []

    def record(snapshot):
        if not snapshots:
            assert client.requests == []
            assert snapshot["state"] == "authoring_in_progress"
            assert len(snapshot["recovery_identity"]["mark_plans"]) == 3
        snapshots.append(deepcopy(snapshot))

    package, _ = generate(tmp_path, client, record, seed=seed)
    identity = package["identity"]
    assert identity["authoring_schema_policy"] == MARK_PLAN_AUTHORING_POLICY
    assert identity["assembly_policy"] == CONTENT_ASSEMBLY_POLICY
    assert identity["mark_plans_sha256"] == mark_plans_digest(build_mark_plans(seed))
    exercises = subject.validate_package(package)
    assert len(exercises) == 3 and sum(e.credit for e in exercises) == Decimal("18")
    assert package["language_points"] == "2" and package["teacher_review"] == "not_run"
    for i, exercise in enumerate(exercises):
        plan = build_mark_plan(seed, str(i + 1))
        assert [q.points for q in exercise.questions] == [
            str(q.points) for q in plan.questions
        ]
        raw = package["exercise_attempts"][i]["rounds"][0]["author_response"]
        assert "target_points" not in raw and all(
            "points" not in q for q in raw["questions"].values()
        )
        assert assemble_exercise(plan, raw).model_dump(
            mode="json"
        ) == exercise.model_dump(mode="json")
    assert all(
        s["recovery_identity"] == snapshots[0]["recovery_identity"] for s in snapshots
    )


@pytest.mark.parametrize("malformed", [1, 2])
def test_numeric_override_is_rejected_never_stripped_or_rescaled(tmp_path, malformed):
    client = ContentClient(malformed=malformed)
    if malformed == 2:
        with pytest.raises(GenerationEvidenceError):
            generate(tmp_path, client)
        assert len(client.requests) == 2
    else:
        package, _ = generate(tmp_path, client)
        subject.validate_package(package)
        requests = [r for r in client.requests if "DONNÉES_JSON\n" in r.prompt][:2]
        assert requests[0].schema == requests[1].schema
        rejected = package["authoring_attempts"][0]["rejected"][0]["response"]
        assert next(iter(rejected["questions"].values()))["points"] == "999"


def test_semantic_whole_exercise_redraft_cannot_change_plan(tmp_path):
    package, client = generate(tmp_path, ContentClient(semantic_refusal=True))
    assert package["exercise_attempts"][0]["accepted_round"] == 2
    requests = [r for r in client.requests if "DONNÉES_JSON\n" in r.prompt][:2]
    assert requests[0].schema == requests[1].schema
    subject.validate_package(package)


@pytest.mark.parametrize(
    "mutation", ["plan", "plan_hash", "assembly", "raw", "canonical", "source"]
)
def test_replay_refuses_plan_wire_canonical_and_source_tampering(tmp_path, mutation):
    package, _ = generate(tmp_path)
    if mutation == "plan":
        package["identity"]["mark_plans"][0]["questions"][0]["criteria"][0][
            "points"
        ] = "2"
    elif mutation == "plan_hash":
        package["identity"]["mark_plans_sha256"] = "0" * 64
    elif mutation == "assembly":
        package["identity"]["assembly_policy"] = "unknown"
    elif mutation == "source":
        package["identity"]["implementation_sha256"] = "0" * 64
    elif mutation == "raw":
        record = package["exercise_attempts"][0]["rounds"][0]
        next(iter(record["author_response"]["questions"].values()))["points"] = "1"
        record["author_response_sha256"] = subject._digest(record["author_response"])
    else:
        package["exercises"][0]["questions"][0]["answer"] = "Autre réponse falsifiée."
    package["identity"]["content_sha256"] = subject._digest(
        {k: v for k, v in package.items() if k != "identity"}
    )
    with pytest.raises((ValueError, ValidationError, SchemaValidationError)):
        subject.validate_package(package)


def test_legacy_full_numeric_draft_is_not_a_content_response():
    with pytest.raises((ValueError, ValidationError)):
        assemble_exercise(build_mark_plan(42, "1"), raw_exercise())


def test_initial_recovery_failure_and_cancellation_start_no_request(tmp_path):
    client = ContentClient()

    def cancelled(_snapshot):
        raise InterruptedError("annulé")

    with pytest.raises(InterruptedError):
        generate(tmp_path, client, cancelled)
    assert client.requests == []


def test_assembly_itself_rejects_wrong_exercise_identity():
    plan = build_mark_plan(42, "1")
    request = subject.exercise_request(
        "1", 42, [], authoring_schema_policy=MARK_PLAN_AUTHORING_POLICY, mark_plan=plan
    )
    raw = ContentClient().generate_request(request)
    raw["id"] = "2"
    with pytest.raises(ValueError):
        assemble_exercise(plan, raw)


def test_schema_itself_rejects_forged_frozen_plan():
    plan = build_mark_plan(42, "1").model_copy(update={"profile_index": 999})
    with pytest.raises(ValueError):
        subject.exercise_request(
            "1",
            42,
            [],
            authoring_schema_policy=MARK_PLAN_AUTHORING_POLICY,
            mark_plan=plan,
        )


@pytest.mark.parametrize(
    "policy,schema_hash,prompt_hash",
    [
        (
            subject.LEGACY_AUTHORING_SCHEMA_POLICY,
            "8b9ee51b2eac59289ce83e43af9232df351512751a76ccbeef1b7edb589f9766",
            "423f449232625fc89e728149d65302f90c80274243b0738e498730aca4561ac5",
        ),
        (
            subject.POSITIVE_POINTS_AUTHORING_SCHEMA_POLICY,
            "185553220e3cf0437a56d1ad136bb68350d77653cba9ed9270045ebd3f15c77d",
            "28ea72769e531913bf33c579a545b9ac3a0d6e5c9a9c17e5e9ba08ff9f1c7531",
        ),
        (
            subject.AUTHORING_SCHEMA_POLICY,
            "b6ffb8ba8690a9cdfb065434e6fcae4b30cc0bf2e0e15207bd8c0042d028deb0",
            "75ebb96ccab002ba7e865e17515d05fd5c1de3955fbd6586cc55f497f2f8de4f",
        ),
    ],
)
def test_all_three_historical_requests_keep_exact_bytes(
    policy, schema_hash, prompt_hash
):
    request = subject.exercise_request("1", 42, [], authoring_schema_policy=policy)
    assert subject._digest(request.schema) == schema_hash
    assert sha256(request.prompt.encode()).hexdigest() == prompt_hash


def test_wire_adaptation_does_not_rewrite_reference_data():
    references = [
        {
            "content": "détaillées et chaque critère du barème. "
            "La somme des points des questions doit valoir 6 et chaque barème doit totaliser les points de sa question."
        }
    ]
    request = subject.exercise_request(
        "1",
        42,
        references,
        authoring_schema_policy=MARK_PLAN_AUTHORING_POLICY,
        mark_plan=build_mark_plan(42, "1"),
    )
    serialized = json.dumps(references, ensure_ascii=False, separators=(",", ":"))
    assert serialized in request.prompt
    assert (
        json.loads(
            request.prompt.split("DONNÉES_JSON\n")[1].split("\nOUTPUT_SCHEMA=")[0]
        )["references"]
        == references
    )


def test_content_key_order_is_irrelevant_and_numeric_metadata_remains_allowed():
    plan = build_mark_plan(42, "1")
    request = subject.exercise_request(
        "1", 42, [], authoring_schema_policy=MARK_PLAN_AUTHORING_POLICY, mark_plan=plan
    )
    raw = ContentClient().generate_request(request)
    expected = assemble_exercise(plan, raw)
    raw["questions"] = dict(reversed(tuple(raw["questions"].items())))
    for value in raw["questions"].values():
        value["marking"] = dict(reversed(tuple(value["marking"].items())))
        assert type(value["estimated_minutes"]) is int
        assert type(value["difficulty"]) is int
    assert assemble_exercise(plan, raw) == expected
    assert (
        subject._read_author_response(
            raw,
            "1",
            large_print=False,
            schema_policy=MARK_PLAN_AUTHORING_POLICY,
            mark_plan=plan,
        )
        == expected
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "question_missing",
        "question_extra",
        "criterion_missing",
        "criterion_extra",
        "criterion_amount",
        "exercise_minutes",
        "exercise_target",
    ],
)
def test_content_contract_refuses_missing_extra_or_numeric_allocation_fields(mutation):
    plan = build_mark_plan(42, "1")
    request = subject.exercise_request(
        "1", 42, [], authoring_schema_policy=MARK_PLAN_AUTHORING_POLICY, mark_plan=plan
    )
    raw = ContentClient().generate_request(request)
    question = next(iter(raw["questions"].values()))
    if mutation == "question_missing":
        raw["questions"].pop(next(iter(raw["questions"])))
    elif mutation == "question_extra":
        raw["questions"]["other"] = deepcopy(question)
    elif mutation == "criterion_missing":
        question["marking"].clear()
    elif mutation == "criterion_extra":
        question["marking"]["other"] = {"criterion": "Autre texte"}
    elif mutation == "criterion_amount":
        next(iter(question["marking"].values()))["points"] = "1"
    elif mutation == "exercise_minutes":
        raw["minutes"] = 70
    else:
        raw["target_points"] = "6"
    with pytest.raises((ValueError, SchemaValidationError)):
        subject._read_author_response(
            raw,
            "1",
            large_print=False,
            schema_policy=MARK_PLAN_AUTHORING_POLICY,
            mark_plan=plan,
        )


@pytest.mark.parametrize("large_print", [False, True])
def test_opt_in_package_replay_has_no_model_calls(tmp_path, large_print):
    package, client = generate(tmp_path, large_print=large_print)
    assert len(client.requests) == 9
    before = deepcopy(package)
    subject.validate_package(package)
    assert package == before and len(client.requests) == 9


def test_terminal_refusal_after_an_accepted_exercise_retains_plan_and_raw_evidence(
    tmp_path,
):
    class RefusingClient(ContentClient):
        def generate_request(self, request):
            result = super().generate_request(request)
            if "2a" in request.schema["properties"]:
                result["2a"]["rubric_consistent"] = False
                result["2a"]["issues"] = [
                    "Le barème ne correspond pas au travail demandé."
                ]
            return result

    snapshots = []
    with pytest.raises(subject.SemanticReviewRefusal) as caught:
        generate(tmp_path, RefusingClient(), snapshots.append)
    details = caught.value.details
    subject.validate_rejected_rounds(details)
    assert snapshots[-1]["state"] == "refused"
    assert snapshots[-1]["recovery_identity"] == snapshots[0]["recovery_identity"]
    assert [h["accepted_round"] for h in details["exercise_attempts"]] == [1, None]
    assert [r["outcome"] for r in details["exercise_attempts"][-1]["rounds"]] == [
        "rejected",
        "rejected",
    ]
    details["recovery_identity"]["mark_plans_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        subject.validate_rejected_rounds(details)


def test_initial_storage_failure_prevents_any_provider_call(tmp_path):
    client = ContentClient()

    def fail(_):
        raise OSError("disk unavailable")

    with pytest.raises(GenerationEvidenceError) as caught:
        generate(tmp_path, client, fail)
    assert caught.value.details["snapshot_saved"] is False
    assert client.requests == []


def test_actual_recovery_recorder_persists_bound_plan_before_first_call(tmp_path):
    from Backend.Core.france.recovery_evidence import RecoveryEvidenceRecorder

    class InspectingClient(ContentClient):
        def generate_request(self, request):
            if not self.requests:
                files = list((tmp_path / ".keldin-recovery").glob("*.json"))
                assert len(files) == 1
                snapshot = json.loads(files[0].read_text())["snapshot"]
                assert snapshot["state"] == "authoring_in_progress"
                assert snapshot["recovery_identity"][
                    "mark_plans_sha256"
                ] == mark_plans_digest(build_mark_plans(42))
            return super().generate_request(request)

    recorder = RecoveryEvidenceRecorder(tmp_path)
    package, _ = generate(tmp_path, InspectingClient(), recorder)
    files = list((tmp_path / ".keldin-recovery").glob("*.json"))
    assert len(files) == 1
    snapshot = json.loads(files[0].read_text())["snapshot"]
    assert snapshot["state"] == "review_complete"
    assert snapshot["exercise_attempts"] == package["exercise_attempts"]


def test_budget_still_stops_without_another_provider_call(tmp_path, monkeypatch):
    from Backend.Core.france import generation_budget

    client = ContentClient()
    snapshots = []
    monkeypatch.setattr(generation_budget, "MAX_REQUESTS", 1)
    with pytest.raises(generation_budget.GenerationLimitError):
        generate(tmp_path, client, snapshots.append)
    assert len(client.requests) == 1
    assert snapshots[-1]["partial_round"]["phase"] == "review"
    assert (
        snapshots[-1]["partial_round"]["returned"]["author_response"]
        == client.raw_returns[0]
    )


def test_provider_cancellation_propagates_without_retry_or_partial_save(tmp_path):
    class CancellingClient(ContentClient):
        def generate_request(self, request):
            self.requests.append(request)
            raise InterruptedError("annulé")

    client = CancellingClient()
    snapshots = []
    with pytest.raises(InterruptedError):
        generate(tmp_path, client, snapshots.append)
    assert len(client.requests) == 1
    assert [s["state"] for s in snapshots] == ["authoring_in_progress"]


def test_shared_schema_is_bounded_for_all_three_numeric_profiles():
    sizes = {}
    for seed in range(24):
        plan = build_mark_plan(seed, "1")
        request = subject.exercise_request(
            "1",
            seed,
            [],
            authoring_schema_policy=MARK_PLAN_AUTHORING_POLICY,
            mark_plan=plan,
        )
        assert all(
            value == {"$ref": "#/$defs/QuestionContent"}
            for value in request.schema["properties"]["questions"][
                "properties"
            ].values()
        )
        text = json.dumps(request.schema, ensure_ascii=False)
        assert text.count("Trace bornée, pas Python général") == 1
        assert (
            len(
                request.schema["$defs"]["QuestionContent"]["properties"][
                    "verification"
                ]["oneOf"]
            )
            == 4
        )
        assert len(text) < 15000
        assert len(request.prompt) < 22000
        sizes[len(plan.questions)] = len(text)
    assert set(sizes) == {4, 5, 6}
    assert max(sizes.values()) - min(sizes.values()) < 1000


def test_host_rejects_other_questions_allowed_criterion_and_retries_same_plan(tmp_path):
    class MisplacedCriterionClient(ContentClient):
        wrong_once = True

        def generate_request(self, request):
            result = super().generate_request(request)
            if self.wrong_once and "DONNÉES_JSON\n" in request.prompt:
                self.wrong_once = False
                values = list(result["questions"].values())
                values[0]["marking"] = deepcopy(values[1]["marking"])
                # Portable shared schema cannot express this cross-field relation.
                from jsonschema import Draft202012Validator

                Draft202012Validator(request.schema).validate(result)
            return result

    package, client = generate(tmp_path, MisplacedCriterionClient())
    assert package["authoring_attempts"][0]["attempts"] == 2
    requests = [r for r in client.requests if "DONNÉES_JSON\n" in r.prompt][:2]
    assert requests[0].schema == requests[1].schema
    rejected = package["authoring_attempts"][0]["rejected"][0]["response"]
    assert (
        rejected["questions"]["1a"]["marking"] == rejected["questions"]["1b"]["marking"]
    )
    subject.validate_package(package)


@pytest.mark.parametrize("kind", ["graph", "sql"])
def test_planned_content_still_requires_machine_evidence_to_match_printed_source(kind):
    plan = build_mark_plan(42, "1")
    request = subject.exercise_request(
        "1", 42, [], authoring_schema_policy=MARK_PLAN_AUTHORING_POLICY, mark_plan=plan
    )
    raw = ContentClient().generate_request(request)
    if kind == "graph":
        from tests.test_french_graph_field_schema import graph

        raw["materials"] = [graph()]
        contract = {
            "kind": "shortest_path",
            "material_id": "graphe",
            "edges": [["A", "B", 1]],
            "start": "A",
            "end": "B",
            "directed": False,
            "expected": 1,
        }
        material_id = "graphe"
    else:
        from tests.test_french_sql_source_binding import contract as sql_contract
        from tests.test_french_sql_source_binding import material

        raw["materials"] = [material()]
        contract = sql_contract()
        material_id = "donnees"
    for question in raw["questions"].values():
        question["material_ids"] = [material_id]
    next(iter(raw["questions"].values()))["verification"] = contract
    before = deepcopy(raw)
    subject._read_author_response(
        raw,
        "1",
        large_print=False,
        schema_policy=MARK_PLAN_AUTHORING_POLICY,
        mark_plan=plan,
    )
    assert raw == before
    if kind == "graph":
        contract["edges"][0][2] = 2
        contract["expected"] = 2
    else:
        contract["schema"] = contract["schema"].replace("Claire", "Bob")
        contract["expected"] = [["Bob"]]
    with pytest.raises(ValueError, match=r"source|imprim|graphe|Vérification"):
        subject._read_author_response(
            raw,
            "1",
            large_print=False,
            schema_policy=MARK_PLAN_AUTHORING_POLICY,
            mark_plan=plan,
        )


def test_old_bad_numeric_draft_remains_invalid_in_every_old_schema_branch():
    raw = raw_exercise()
    raw["questions"][0]["marking"][0]["points"] = "0.5"
    for policy in (
        subject.LEGACY_AUTHORING_SCHEMA_POLICY,
        subject.POSITIVE_POINTS_AUTHORING_SCHEMA_POLICY,
        subject.AUTHORING_SCHEMA_POLICY,
    ):
        with pytest.raises(ValueError):
            subject.validate_authored_exercise(raw, "1", authoring_schema_policy=policy)


def test_published_default_does_not_select_the_new_contract(tmp_path):
    index = tmp_path / "references.sqlite"
    make_index(index)
    client = Client()
    package = subject.generate(index_path=index, client=client, seed=42)
    assert (
        package["identity"]["authoring_schema_policy"]
        == subject.AUTHORING_SCHEMA_POLICY
    )
    assert "mark_plans" not in package["identity"]
    package["identity"]["mark_plans"] = []
    with pytest.raises(ValueError, match="historique"):
        subject.validate_package(package)
