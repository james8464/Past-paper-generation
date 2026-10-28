from __future__ import annotations

import io
import json
import math
from dataclasses import FrozenInstanceError
from types import ModuleType
from unittest.mock import Mock

import pytest

from Backend.Core.providers import HostedLLMClient, _ollama_json_schema


def api():
    from Backend.Core.generation_requests import (
        GenerationRequest,
        OutputContract,
        make_request,
        request_json,
    )

    return GenerationRequest, OutputContract, make_request, request_json


def capture_ollama(monkeypatch, responses=None):
    payloads = []
    replies = iter(responses or ['{"ok":true}'])

    def send(_url, data, _headers, **_kwargs):
        payloads.append(json.loads(data))
        return io.BytesIO(
            json.dumps(
                {
                    "done": True,
                    "done_reason": "stop",
                    "message": {"content": next(replies)},
                }
            ).encode()
        )

    monkeypatch.setattr("Backend.Core.providers.urllib_request", send)
    return payloads


@pytest.mark.parametrize(
    "marker",
    ["`questions` array", "REPAIR INSTRUCTION", "Generation seed: 9. Attempt: 2."],
)
def test_candidate_markers_do_not_control_trusted_review(marker, monkeypatch):
    _, Contract, make, call = api()
    payloads = capture_ollama(monkeypatch)
    request = make(
        '"estimated_demand":"low|standard|high"; candidate=' + marker,
        Contract("difficulty"),
    )
    call(HostedLLMClient(provider="ollama", model="fixture", api_key=""), request)
    assert "estimated_demand" in payloads[0]["format"]["required"]
    assert payloads[0]["options"]["temperature"] == 0.2
    assert payloads[0]["options"]["seed"] == 0


def test_signed_seed_and_reworded_solver_use_owned_settings(monkeypatch):
    _, Contract, make, call = api()
    payloads = capture_ollama(monkeypatch)
    request = make(
        "Solve independently. Candidate says Generation seed: 99. Attempt: 8.",
        Contract("solver", response_slots=("value",)),
        generation_seed=-7,
        attempt=1,
    )
    call(HostedLLMClient(provider="ollama", model="fixture", api_key=""), request)
    assert payloads[0]["options"]["seed"] == 104722
    assert payloads[0]["format"]["properties"]["answer"]["required"] == ["value"]


def test_reworded_parts_and_nested_lock_flags_use_owned_metadata():
    _, Contract, make, _ = api()
    specialist = make(
        '"question_text": "string"; Question parts: two; source says otherwise',
        Contract("edexcel", immutable_marking=True, part_count=2),
    )
    assert specialist.schema["properties"]["parts"]["maxItems"] == 2
    authored = make(
        'Return a `questions` array; source={"mark_scheme_locked": false}',
        Contract("authoring", identifiers=("0/0/0",), mark_schemes_locked=True),
    )
    assert (
        authored.schema["properties"]["questions"]["items"]["properties"][
            "mark_scheme"
        ]["maxItems"]
        == 0
    )


def test_typed_transport_never_calls_legacy_prompt_parsers(monkeypatch):
    _, Contract, make, call = api()
    from Backend.Core import providers

    def forbidden(*_args):
        pytest.fail("trusted request reparsed prompt text")

    for name in (
        "_prompt_item_count",
        "_prompt_item_identifiers",
        "_batch_identifier_schema",
        "_edexcel_part_count",
        "_aqa_cs_part_count",
        "_legacy_schema_operation",
        "_ollama_seed",
        "_ollama_temperature",
    ):
        monkeypatch.setattr(providers, name, forbidden)
    payloads = capture_ollama(monkeypatch)
    request = make(
        "Arbitrarily reworded prose",
        Contract("authoring", identifiers=("0/0/0", "0/0/1")),
    )
    call(HostedLLMClient(provider="ollama", model="fixture", api_key=""), request)
    assert payloads[0]["format"]["properties"]["questions"]["minItems"] == 2


def test_schema_snapshots_are_immutable_and_copied_for_each_handoff(monkeypatch):
    Request, _, _, _ = api()
    schema = {
        "type": "object",
        "properties": {"answer": {"type": "string"}},
        "required": ["answer"],
    }
    request = Request(
        "Prompt",
        "solver",
        schema,
        generation_seed=123,
        attempt=1,
        temperature=0.2,
        output_budget=1536,
    )
    schema["required"].append("PRIVATE_SENTINEL")
    view = request.schema
    view["properties"]["answer"]["type"] = "number"
    assert request.schema["required"] == ["answer"]
    assert request.version == "trusted-generation-request-v1"
    assert request.schema["properties"]["answer"]["type"] == "string"
    with pytest.raises(FrozenInstanceError):
        request.prompt = "changed"


@pytest.mark.parametrize(
    "field,value",
    [
        ("generation_seed", True),
        ("generation_seed", "123"),
        ("attempt", False),
        ("attempt", 0),
        ("temperature", True),
        ("temperature", math.nan),
        ("temperature", math.inf),
        ("output_budget", False),
        ("output_budget", 0),
    ],
)
def test_request_rejects_malformed_trusted_settings(field, value):
    Request, _, _, _ = api()
    settings = dict(generation_seed=123, attempt=1, temperature=0.2, output_budget=1536)
    settings[field] = value
    with pytest.raises((TypeError, ValueError)):
        Request("Prompt", "solver", {"type": "object"}, **settings)


def test_unknown_contract_private_fields_and_duplicate_identifiers_refuse():
    _, Contract, _, _ = api()
    with pytest.raises(ValueError):
        Contract("unknown")
    with pytest.raises(ValueError):
        Contract("authoring", identifiers=("0/0/0", "0/0/0"))
    with pytest.raises(TypeError):
        Contract("solver", correct_choice="PRIVATE_SENTINEL")


def test_minimal_fake_mock_and_legacy_subclass_overrides_keep_exact_calls():
    _, Contract, make, call = api()
    request = make("Exact original prompt", Contract("review"))
    fake = Mock()
    fake.generate_json.return_value = {"fake": True}
    assert call(fake, request) == {"fake": True}
    fake.generate_json.assert_called_once_with(request.prompt)
    assert "generate_request" not in fake._mock_children

    class Override(HostedLLMClient):
        def generate_json(self, prompt, retries=2):
            assert prompt == request.prompt
            return {"override": True}

    assert call(Override(provider="ollama", model="fixture", api_key=""), request) == {
        "override": True
    }
    instance = HostedLLMClient(provider="ollama", model="fixture", api_key="")
    instance.generate_json = Mock(return_value={"mocked": True})
    assert call(instance, request) == {"mocked": True}
    instance.generate_json.assert_called_once_with(request.prompt)


def test_client_internal_type_error_is_not_retried_as_another_signature():
    _, Contract, make, call = api()
    client = Mock()
    client.generate_json.side_effect = TypeError("internal client failure")
    with pytest.raises(TypeError, match="internal client failure"):
        call(client, make("Exact prompt", Contract("review")))
    assert client.generate_json.call_count == 1


def test_ordinary_positive_authoring_payload_and_repair_settings_match_legacy(
    monkeypatch,
):
    _, Contract, make, call = api()
    prompt = 'Return a `questions` array\nGeneration seed: 123. Attempt: 1.\nBLUEPRINT_DATA=[{"id":"0/0/0","mark_scheme_locked": true}]'
    payloads = capture_ollama(monkeypatch, ['{"ok":true}', '{"ok":true}'])
    client = HostedLLMClient(provider="ollama", model="fixture", api_key="")
    client.generate_json(prompt)
    request = make(
        prompt,
        Contract("authoring", identifiers=("0/0/0",), mark_schemes_locked=True),
        generation_seed=123,
        attempt=1,
    )
    call(client, request)
    assert payloads[0] == payloads[1]

    repaired = capture_ollama(monkeypatch, ["not JSON", '{"ok":true}'])
    call(client, request)
    assert len(repaired) == 2
    assert repaired[0]["format"] == repaired[1]["format"]
    assert repaired[0]["options"]["seed"] == repaired[1]["options"]["seed"]
    assert repaired[0]["options"]["temperature"] == 0.25
    assert repaired[1]["options"]["temperature"] == 0


@pytest.mark.parametrize(
    "provider,response",
    [
        ("openai", {"status": "completed", "output_text": '{"ok":true}'}),
        (
            "anthropic",
            {
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": '{"ok":true}'}],
            },
        ),
    ],
)
def test_hosted_api_payloads_remain_identical(provider, response, monkeypatch):
    _, Contract, make, call = api()
    captured = []

    def send(url, data, headers, **kwargs):
        captured.append((url, json.loads(data), headers, kwargs))
        return io.BytesIO(json.dumps(response).encode())

    monkeypatch.setattr("Backend.Core.providers.urllib_request", send)
    client = HostedLLMClient(
        provider=provider, model="fixture", api_key="fixture-only-not-a-real-key"
    )
    client.generate_json("Exact prompt")
    call(client, make("Exact prompt", Contract("review")))
    assert captured[0] == captured[1]


def test_legacy_negative_seed_and_prompt_entrypoint_are_retained():
    from Backend.Core.providers import _ollama_seed

    assert _ollama_seed("Generation seed: -7. Attempt: 1.") == 0
    assert _ollama_json_schema(
        '"estimated_demand":"low|standard|high"; `questions` array'
    )["required"] == ["questions"]


def mlx_client(monkeypatch, structured):
    module = ModuleType("mlx_lm")

    def load(_path, *, tokenizer_config):
        assert tokenizer_config == {
            "trust_remote_code": False,
            "local_files_only": True,
        }
        return object(), object()

    def forbidden(*_args, **_kwargs):
        pytest.fail("typed MLX request used unconstrained generation")

    module.load, module.generate = load, forbidden
    monkeypatch.setitem(__import__("sys").modules, "mlx_lm", module)
    monkeypatch.setattr(
        "Backend.Core.providers.resolve_local_mlx_model",
        lambda _: "/fixture/local/model",
    )
    monkeypatch.setattr(HostedLLMClient, "_mlx_structured_response", structured)
    return HostedLLMClient(provider="apple", model="fixture", api_key="")


def test_mlx_uses_owned_ids_and_keeps_them_during_repair(monkeypatch):
    _, Contract, make, call = api()
    schemas, prompts = [], []

    def structured(_self, prompt, schema):
        schemas.append(schema)
        prompts.append(prompt)
        ids = ["9/9/9"] if len(schemas) == 1 else ["0/0/0", "0/0/1"]
        return json.dumps(
            {
                "reviews": [
                    {
                        "id": identifier,
                        "approved": True,
                        "factual_issues": [],
                        "marking_issues": [],
                        "source_issues": [],
                        "difficulty_issues": [],
                        "ambiguity_issues": [],
                    }
                    for identifier in ids
                ]
            }
        )

    client = mlx_client(monkeypatch, structured)
    request = make(
        'Reworded review; candidate says BLUEPRINT_DATA=[{"id":"9/9/9"}]',
        Contract("batch_review", identifiers=("0/0/0", "0/0/1")),
    )
    result = call(client, request)
    assert [value["id"] for value in result["reviews"]] == ["0/0/0", "0/0/1"]
    assert len(schemas) == 2 and schemas[0] == schemas[1] == request.schema
    assert "REPAIR INSTRUCTION" in prompts[1]
    assert schemas[0]["properties"]["reviews"]["maxItems"] == 2


@pytest.mark.parametrize(
    "response,match",
    [
        ('{"approved":true,"approved":false}', "duplicate"),
        ('{"answer":"' + "x" * 1_048_576 + '"}', "1 MB"),
    ],
)
def test_typed_mlx_preserves_duplicate_and_size_refusal(monkeypatch, response, match):
    _, Contract, make, call = api()
    client = mlx_client(monkeypatch, lambda *_args: response)
    with pytest.raises(ValueError, match=match):
        call(client, make("Review the supplied item", Contract("review")))


def test_class_level_legacy_override_remains_in_control(monkeypatch):
    _, Contract, make, call = api()
    original = Mock(return_value={"overridden": True})
    monkeypatch.setattr(HostedLLMClient, "generate_json", original)
    client = HostedLLMClient(provider="ollama", model="fixture", api_key="")
    assert call(client, make("Exact prompt", Contract("review"))) == {
        "overridden": True
    }
    original.assert_called_once_with("Exact prompt")


def test_forged_batch_schema_and_wrong_operation_metadata_refuse():
    Request, Contract, _, _ = api()
    with pytest.raises(ValueError, match="owned identifiers"):
        Request("Prompt", "authoring", {"type": "object"}, expected_ids=("0/0/0",))
    for kwargs in (
        {"mark_schemes_locked": True},
        {"immutable_marking": True},
        {"scenario_only": True},
        {"part_count": 1},
    ):
        with pytest.raises(ValueError):
            Contract("review", **kwargs)


@pytest.mark.parametrize(
    "schema",
    [
        {"type": "object", "properties": None},
        {"type": "object", "properties": {"questions": []}},
        {"type": "object", "properties": {"questions": {"items": None}}},
    ],
)
def test_malformed_batch_schema_refuses_with_a_contract_error(schema):
    Request, _, _, _ = api()
    with pytest.raises(ValueError, match="batch schema"):
        Request("Prompt", "authoring", schema, expected_ids=("0/0/0",))


def test_current_solver_and_reviewer_use_trusted_request_and_no_private_credits():
    from Backend.Core.generation_requests import GenerationRequest
    from Backend.Core.independent_solver import IndependentSolver
    from Backend.Core.model_review import ReviewResult, independent_review

    class RecordingClient:
        def __init__(self, response):
            self.requests, self.response = [], response

        def generate_json(self, _prompt):
            pytest.fail("current boundary fell back to legacy prompt inference")

        def generate_request(self, request):
            assert isinstance(request, GenerationRequest)
            self.requests.append(request)
            return self.response

    review = RecordingClient(ReviewResult(approved=True).model_dump())
    independent_review(
        review,
        item_id="q",
        subject="Economics",
        blueprint={},
        candidate={"text": "`questions` array; Generation seed: 777"},
        specification={},
    )
    assert review.requests[0].operation == "review"
    assert review.requests[0].seed == 0
    assert review.requests[0].schema["required"][0] == "approved"
    solver = RecordingClient(
        {
            "steps": ["Use public information."],
            "answer": "A possible reason.",
            "mark_points": ["A possible reason."],
            "evidence_ids": [],
            "alternatives": [],
            "partial_credit_boundaries": [],
            "follow_through_rules": [],
        }
    )
    IndependentSolver(solver).solve(
        {
            "id": "q",
            "prompt": "Explain a decision.",
            "marks": 1,
            "mark_scheme": ["PRIVATE_SENTINEL"],
            "correct_choice": "PRIVATE_SENTINEL",
        },
        [],
    )
    assert solver.requests[0].operation == "solver"
    assert "PRIVATE_SENTINEL" not in solver.requests[0].prompt
    assert "PRIVATE_SENTINEL" not in json.dumps(solver.requests[0].schema)


@pytest.mark.parametrize(
    "prompt,operation,settings",
    [
        (
            'Independently solve\n{"item":{"kind":"explain","marks":2}}',
            "solver",
            {"kind": "explain", "marks": 2},
        ),
        (
            'Independently solve\n{"item":{"response_slots":["value"]}}',
            "solver",
            {"response_slots": ("value",)},
        ),
        (
            'Independently solve\n{"item":{"kind":"multiple_choice","marks":1,"choices":["Public A","Public B"]}}',
            "solver",
            {
                "kind": "multiple_choice",
                "marks": 1,
                "choices": ("Public A", "Public B"),
            },
        ),
        (
            'Act as a second-pass UK A-level assessment editor. `reviews` must contain\nREVIEW_DATA=[{"id":"0/0/0"}]',
            "batch_review",
            {"identifiers": ("0/0/0",)},
        ),
        (
            'Act as a second-pass UK A-level assessment editor. "approved":true|false',
            "review",
            {},
        ),
        ('"estimated_demand":"low|standard|high"', "difficulty", {}),
        (
            '"question_text": "string"; VERIFIED MARKING IS IMMUTABLE\nParts: (a) 4 marks (b) 6 marks',
            "edexcel",
            {"immutable_marking": True, "part_count": 2},
        ),
        (
            '"stem": "string"; "parts": [; VERIFIED MARKING IS IMMUTABLE\n- Part a: 4 marks\n- Part b: 6 marks',
            "aqa_cs",
            {"immutable_marking": True, "part_count": 2},
        ),
        (
            '"stem": "string"; "parts": [; Do not repeat, rewrite or answer the parts',
            "aqa_cs",
            {"scenario_only": True},
        ),
    ],
)
def test_ordinary_operation_payloads_match_legacy(
    prompt, operation, settings, monkeypatch
):
    _, Contract, make, call = api()
    payloads = capture_ollama(monkeypatch, ['{"ok":true}', '{"ok":true}'])
    client = HostedLLMClient(provider="ollama", model="fixture", api_key="")
    client.generate_json(prompt)
    call(client, make(prompt, Contract(operation, **settings)))
    assert payloads[0] == payloads[1]


def test_each_provider_attempt_gets_an_unmodified_schema_copy(monkeypatch):
    _, Contract, make, call = api()
    request = make("Prompt", Contract("authoring", identifiers=("0/0/0",)))
    client = HostedLLMClient(provider="ollama", model="fixture", api_key="")
    observed = []

    def transport(_prompt, **settings):
        observed.append(settings["schema"])
        if len(observed) == 1:
            settings["schema"]["required"].append("INTERNAL_MUTATION")
            raise ValueError("retry with a fresh schema")
        assert "INTERNAL_MUTATION" not in settings["schema"]["required"]
        return {"ok": True}

    monkeypatch.setattr(client, "_ollama", transport)
    assert call(client, request) == {"ok": True}
    assert len(observed) == 2
    assert "INTERNAL_MUTATION" not in request.schema["required"]


def test_current_authoring_and_batch_review_keep_metadata_out_of_checkpoint(tmp_path):
    from Backend.Core.ai_assessment import (
        ASSESSMENT_REVIEW_VERSION,
        GenerationPolicy,
        generate_unique_paper,
    )
    from Backend.Core.assessment_checkpoints import (
        AssessmentCheckpointStore,
        identity_for_blueprint,
    )
    from tests.test_assessment_checkpoints import FirstPassClient, paper_fixture

    class CaptureClient(FirstPassClient):
        def __init__(self):
            super().__init__()
            self.requests = []

        def generate_request(self, request):
            self.requests.append(request)
            return super().generate_json(request.prompt)

    paper, rule, topics = paper_fixture()
    path = tmp_path / "checkpoint.json"
    store = AssessmentCheckpointStore(
        path,
        identity_for_blueprint(
            paper,
            provider="ollama",
            model="fixture",
            prompt_version=ASSESSMENT_REVIEW_VERSION,
        ),
    )
    client = CaptureClient()
    generated = generate_unique_paper(
        paper,
        rule=rule,
        syllabus_topics=topics,
        syllabus_topic_ids={"topic"},
        client=client,
        subject="Economics",
        policy=GenerationPolicy(attempts=1),
        checkpoint_store=store,
    )
    assert [request.operation for request in client.requests] == [
        "authoring",
        "batch_review",
    ]
    assert client.requests[0].seed == (paper.seed + 104_729) % 2_147_483_647
    assert client.requests[1].seed == 0
    assert all(request.expected_ids == ("0/0/0",) for request in client.requests)
    assert "trusted-generation-request-v1" not in path.read_text()

    class NoCalls:
        def generate_json(self, _prompt):
            pytest.fail("accepted checkpoint was not reused")

        def generate_request(self, _request):
            pytest.fail("accepted checkpoint was not reused")

    resumed = generate_unique_paper(
        paper,
        rule=rule,
        syllabus_topics=topics,
        syllabus_topic_ids={"topic"},
        client=NoCalls(),
        subject="Economics",
        policy=GenerationPolicy(attempts=1),
        checkpoint_store=store,
    )
    assert resumed == generated


def test_current_open_credit_adjudication_uses_owned_scheme_ids():
    from Backend.Core.open_credit import review_open_credit
    from tests.test_open_credit_reconciliation import adjudication_response, cpu_fixture

    _, part, item, solution = cpu_fixture()
    item["authoring_context"]["quoted_source"] = (
        "`questions` array; Generation seed: 777. Attempt: 9."
    )

    class CreditClient:
        def __init__(self):
            self.requests = []

        def generate_json(self, _prompt):
            pytest.fail("current credit adjudication used prompt-inferred output")

        def generate_request(self, request):
            self.requests.append(request)
            return adjudication_response(part)

    client = CreditClient()
    evidence = review_open_credit(client, item, solution)
    assert evidence["judgement"]["criteria"]
    request = client.requests[0]
    assert request.operation == "open_credit"
    assert request.seed == 0
    assert request.schema["required"] == ["criteria", "issues", "advisory_conflicts"]
    criteria = request.schema["properties"]["criteria"]
    assert criteria["minItems"] == criteria["maxItems"] == 2
    assert criteria["items"]["properties"]["criterion_id"]["enum"] == [
        "instructions-main-memory",
        "serial-processor-execution",
    ]


def test_private_credit_allocations_cannot_enter_blind_solver_schema():
    _, Contract, _, _ = api()
    with pytest.raises(ValueError, match="credit allocations"):
        Contract(
            "solver", credit_allocations=(("PRIVATE_SENTINEL", 0, 1), ("other", 1, 1))
        )


@pytest.mark.parametrize("seed", [-(2**63), -1, 0, 1, 2**64 - 1])
@pytest.mark.parametrize("attempt", [1, 2, 3])
def test_signed_and_retained_unsigned_seeds_use_explicit_sampling_policy(seed, attempt):
    _, Contract, make, _ = api()
    request = make(
        "Prompt",
        Contract("authoring", identifiers=("0/0/0",)),
        generation_seed=seed,
        attempt=attempt,
    )
    assert request.seed == (seed + 104_729 * attempt) % 2_147_483_647
    assert request.temperature == min(0.4, 0.15 + 0.1 * attempt)


def test_structured_client_internal_type_error_is_never_legacy_fallback():
    _, Contract, make, call = api()

    class Client:
        calls = 0

        def generate_json(self, _prompt):
            pytest.fail("internal typed-client error triggered legacy retry")

        def generate_request(self, _request):
            self.calls += 1
            raise TypeError("typed client failed internally")

    client = Client()
    with pytest.raises(TypeError, match="failed internally"):
        call(client, make("Prompt", Contract("review")))
    assert client.calls == 1


@pytest.mark.parametrize("operation", ["solver", "review", "difficulty"])
def test_mutable_credit_container_cannot_enter_any_contract(operation):
    _, Contract, _, _ = api()
    caller_rows = []
    with pytest.raises(ValueError, match="credit allocations"):
        Contract(operation, credit_allocations=caller_rows)
    caller_rows.append(("PRIVATE_SENTINEL", 0, 1))


@pytest.mark.parametrize("operation", [[], {}, None, True, 1.0])
def test_nonstring_operations_refuse_with_a_contract_error(operation):
    Request, Contract, _, _ = api()
    with pytest.raises(ValueError, match="operation"):
        Contract(operation)
    with pytest.raises(ValueError, match="operation"):
        Request("Prompt", operation, {"type": "object"})


@pytest.mark.parametrize("field", ["minItems", "maxItems"])
def test_boolean_batch_cardinality_is_not_an_integer(field):
    Request, Contract, make, _ = api()
    request = make("Prompt", Contract("authoring", identifiers=("0/0/0",)))
    schema = request.schema
    schema["properties"]["questions"][field] = True
    with pytest.raises(ValueError, match="integer"):
        Request("Prompt", "authoring", schema, expected_ids=("0/0/0",))
