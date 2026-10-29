from __future__ import annotations

import copy
import json
from argparse import Namespace

import pytest
from jsonschema import Draft202012Validator

from Backend.Core.generation_requests import make_request
from Backend.Core.independent_solver import IndependentSolver, reconcile_solution
from Backend.Core.providers import HostedLLMClient, _mlx_decoder_schema
from Backend.Core.solver_prompts import build_solver_prompt, solver_output_contract
from tests.support.solver_responses import complete_solver_response


def item():
    return {
        "id": "Q05",
        "kind": "multiple_choice",
        "marks": 1,
        "prompt": "Price is £45 and variable cost is £10. Find contribution.",
        "choices": ["£30", "£40", "£50", "£55"],
        "correct_choice": 0,
        "mark_scheme": ["PRIVATE_SCHEME"],
    }


def response(**changes):
    return complete_solver_response(
        {
            "steps": ["45 - 10 = 35; none of the options equals £35."],
            "answer": "£30",
            "mark_points": ["£30"],
            "has_single_valid_choice": False,
            **changes,
        }
    )


class TypedClient:
    def __init__(self, result):
        self.result = result
        self.requests = []

    def generate_request(self, request):
        self.requests.append(request)
        return copy.deepcopy(self.result)


@pytest.mark.parametrize(
    "steps",
    [
        ["45 - 10 = 35; no option gives £35."],
        ["Both differently worded options express the same correct result."],
    ],
)
def test_no_or_multiple_valid_options_are_rejected(steps):
    with pytest.raises(ValueError, match="no single valid choice"):
        IndependentSolver(TypedClient(response(steps=steps))).solve(item(), [])


@pytest.mark.parametrize("value", [None, 0, 1, "false", "true", [], {}])
def test_choice_validity_is_strict_boolean(value):
    with pytest.raises(ValueError, match="Boolean choice-validity"):
        IndependentSolver(TypedClient(response(has_single_valid_choice=value))).solve(
            item(), []
        )


def test_typed_client_must_supply_choice_validity():
    result = response()
    del result["has_single_valid_choice"]
    with pytest.raises(ValueError, match="Boolean choice-validity"):
        IndependentSolver(TypedClient(result)).solve(item(), [])


def test_inherited_real_provider_interface_does_not_enable_legacy_omission():
    class OverriddenProvider(HostedLLMClient):
        def generate_json(self, prompt, retries=2):
            result = response()
            del result["has_single_valid_choice"]
            return result

    client = OverriddenProvider(provider="ollama", model="fixture", api_key="")
    with pytest.raises(ValueError, match="Boolean choice-validity"):
        IndependentSolver(client).solve(item(), [])


def test_true_signal_cannot_bypass_wrong_key_or_mark_point_checks():
    candidate = item()
    candidate["choices"] = ["£30", "£35", "£40", "£45"]
    candidate["correct_choice"] = 1
    client = TypedClient(response(has_single_valid_choice=True))
    solution = IndependentSolver(client).solve(candidate, [])
    assert not reconcile_solution(solution, candidate).passed
    with pytest.raises(ValueError, match="same single option"):
        IndependentSolver(
            TypedClient(response(has_single_valid_choice=True, mark_points=["£35"]))
        ).solve(candidate, [])


def test_legacy_generate_json_only_response_remains_compatible_but_false_rejects():
    class LegacyClient:
        def __init__(self, result):
            self.result = result

        def generate_json(self, prompt):
            return self.result

    result = response(has_single_valid_choice=True)
    del result["has_single_valid_choice"]
    assert IndependentSolver(LegacyClient(result)).solve(item(), []).answer == "£30"
    with pytest.raises(ValueError, match="no single valid choice"):
        IndependentSolver(LegacyClient(response())).solve(item(), [])


def test_real_mcq_schema_requires_boolean_and_does_not_leak_private_key():
    candidate = item()
    request = make_request(
        "Public solver request", solver_output_contract(candidate, [])
    )
    validator = Draft202012Validator(request.schema)
    assert not list(validator.iter_errors(response()))
    for value in [None, 0, 1, "false"]:
        assert list(validator.iter_errors(response(has_single_valid_choice=value)))
    missing = response()
    del missing["has_single_valid_choice"]
    assert list(validator.iter_errors(missing))
    assert request.schema["properties"]["answer"]["enum"] == candidate["choices"]
    assert "correct_choice" not in json.dumps(request.schema)
    assert "PRIVATE_SCHEME" not in json.dumps(request.schema)


def test_prompt_is_blind_and_non_choice_contract_unchanged():
    client = TypedClient(response(has_single_valid_choice=True))
    IndependentSolver(client).solve(item(), [])
    prompt = client.requests[0].prompt
    assert "has_single_valid_choice" in prompt and "ALL public options" in prompt
    assert "PRIVATE_SCHEME" not in prompt and '"correct_choice"' not in prompt
    candidate = {"id": "open", "prompt": "Explain the effect.", "marks": 2}
    request = make_request(
        build_solver_prompt(candidate, [], []), solver_output_contract(candidate, [])
    )
    assert "has_single_valid_choice" not in request.schema["properties"]
    result = response()
    del result["has_single_valid_choice"]
    assert IndependentSolver(TypedClient(result)).solve(candidate, []).answer == "£30"
    with pytest.raises(ValueError, match="requires a multiple-choice"):
        IndependentSolver(TypedClient(response())).solve(candidate, [])


def test_mlx_choice_validity_grammar_compiles_without_model_loading():
    llguidance = pytest.importorskip("llguidance")
    schema = make_request("Public solver", solver_output_contract(item(), [])).schema
    grammar = llguidance.LLMatcher.grammar_from_json_schema(
        json.dumps(_mlx_decoder_schema(schema))
    )
    assert not llguidance.LLMatcher.validate_grammar(grammar)


def test_closed_slot_solver_does_not_gain_choice_only_field():
    candidate = {**item(), "response_slots": ["value"]}
    schema = make_request(
        "Closed slots", solver_output_contract(candidate, ["value"])
    ).schema
    assert "has_single_valid_choice" not in schema["properties"]
    assert schema["properties"]["answer"]["type"] == "object"


def test_choice_validity_gate_changes_checkpoint_identity(monkeypatch, tmp_path):
    from Backend.Core import generation
    from Backend.Core.ai_assessment import ASSESSMENT_REVIEW_VERSION

    args = Namespace(
        subject="accounting_aqa",
        paper=2,
        seed=270101,
        provider="apple",
        model="fixture",
    )
    assert (
        ASSESSMENT_REVIEW_VERSION
        == "assessment-review-v11-accounting-equal-priority"
    )
    current = generation.checkpoint_path_for_job(args, tmp_path)
    monkeypatch.setattr(
        generation,
        "ASSESSMENT_REVIEW_VERSION",
        "assessment-review-v7-trusted-generation-requests",
    )
    old = generation.checkpoint_path_for_job(args, tmp_path)
    assert current != old
    old.parent.mkdir(parents=True)
    old.write_text("retained historical checkpoint")
    assert old.read_text() == "retained historical checkpoint"
    assert not current.exists()
