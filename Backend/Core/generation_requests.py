"""Keep trusted provider settings separate from candidate and prompt prose."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from typing import Any

from Backend.Core.json_client import JSONGenerationClient

REQUEST_VERSION = "trusted-generation-request-v1"
OPERATIONS = {
    "solver",
    "authoring",
    "batch_review",
    "review",
    "difficulty",
    "edexcel",
    "aqa_cs",
    "open_credit",
}


def _integer(value: object, name: str, *, minimum: int | None = None) -> None:
    if type(value) is not int or (minimum is not None and value < minimum):
        raise ValueError(f"{name} must be an integer within its supported range")


def _strings(values: tuple[str, ...], name: str) -> None:
    if (
        type(values) is not tuple
        or any(not isinstance(value, str) or not value.strip() for value in values)
        or len(set(values)) != len(values)
    ):
        raise ValueError(f"{name} must contain distinct nonempty strings")


def _batch_schema_object(schema: dict[str, Any], *path: str) -> dict[str, Any]:
    value = schema
    for key in path:
        value = value.get(key)
        if not isinstance(value, dict):
            raise ValueError(
                "batch schema must match its owned identifiers and object structure"
            )
    return value


def _batch_schema_identifiers(array: dict[str, Any]) -> object:
    item = _batch_schema_object(array, "items")
    if "anyOf" not in item:
        return _batch_schema_object(item, "properties", "id").get("enum")
    variants = item.get("anyOf")
    if not isinstance(variants, list) or not variants:
        raise ValueError("batch schema must match its owned identifiers")
    identifiers = []
    for variant in variants:
        if not isinstance(variant, dict) or variant.get("type") != "object":
            raise ValueError("batch schema must match its owned identifiers")
        values = _batch_schema_object(variant, "properties", "id").get("enum")
        if not isinstance(values, list) or len(values) != 1:
            raise ValueError("batch schema must match its owned identifiers")
        identifiers.extend(values)
    return identifiers


@dataclass(frozen=True)
class OutputContract:
    operation: str
    identifiers: tuple[str, ...] = ()
    response_slots: tuple[str, ...] = ()
    choices: tuple[str, ...] = ()
    kind: str | None = None
    marks: int | None = None
    mark_schemes_locked: bool = False
    immutable_marking: bool = False
    part_count: int = 0
    scenario_only: bool = False
    credit_allocations: tuple[tuple[str, int, int], ...] = ()
    authoring_shapes: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.operation, str) or self.operation not in OPERATIONS:
            raise ValueError("unsupported generation operation")
        for name in ("identifiers", "response_slots", "choices"):
            _strings(getattr(self, name), name)
        if self.operation in {"authoring", "batch_review"}:
            if not 1 <= len(self.identifiers) <= 6 or any(
                re.fullmatch(r"\d+/\d+/\d+", identifier) is None
                for identifier in self.identifiers
            ):
                raise ValueError("batch contract requires one to six owned identifiers")
        elif self.identifiers:
            raise ValueError("identifiers require a batch operation")
        if type(self.authoring_shapes) is not tuple:
            raise ValueError("authoring shapes must be an immutable tuple")
        if self.authoring_shapes:
            if self.operation != "authoring" or any(
                type(row) is not tuple
                or len(row) != 2
                or not isinstance(row[0], str)
                or not isinstance(row[1], str)
                or row[1] not in {"multiple_choice", "constructed_response"}
                for row in self.authoring_shapes
            ):
                raise ValueError(
                    "authoring shapes require owned IDs and supported response kinds"
                )
            if tuple(row[0] for row in self.authoring_shapes) != self.identifiers:
                raise ValueError(
                    "authoring shapes must match every owned identifier in order"
                )
        for name in ("mark_schemes_locked", "immutable_marking", "scenario_only"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be Boolean")
        _integer(self.part_count, "part_count", minimum=0)
        if self.part_count > (6 if self.operation == "edexcel" else 8):
            raise ValueError("part_count exceeds the supported grammar")
        if self.marks is not None:
            _integer(self.marks, "marks", minimum=0)
        if self.kind is not None and not isinstance(self.kind, str):
            raise ValueError("solver kind must be text")
        if self.operation != "solver" and (
            self.response_slots
            or self.choices
            or self.kind is not None
            or self.marks is not None
        ):
            raise ValueError("public solver fields require a solver operation")
        if self.mark_schemes_locked and self.operation != "authoring":
            raise ValueError("marking locks require an authoring operation")
        if (self.immutable_marking or self.part_count) and self.operation not in {
            "edexcel",
            "aqa_cs",
        }:
            raise ValueError("part metadata requires a specialist operation")
        if self.scenario_only and (self.operation != "aqa_cs" or self.part_count):
            raise ValueError("scenario-only requests must have no generated parts")
        if type(self.credit_allocations) is not tuple:
            raise ValueError("credit allocations must be an immutable tuple")
        if self.credit_allocations and self.operation != "open_credit":
            raise ValueError(
                "credit allocations belong only to post-solver adjudication"
            )
        if self.operation == "open_credit":
            if (
                type(self.credit_allocations) is not tuple
                or len(self.credit_allocations) != 2
            ):
                raise ValueError("credit allocations require the two declared criteria")
            identifiers = []
            for row in self.credit_allocations:
                if (
                    type(row) is not tuple
                    or len(row) != 3
                    or not isinstance(row[0], str)
                    or not row[0].strip()
                ):
                    raise ValueError(
                        "credit allocations require criterion IDs and exact allocations"
                    )
                _integer(row[1], "credit point index", minimum=0)
                _integer(row[2], "credit marks", minimum=0)
                identifiers.append(row[0])
            _strings(tuple(identifiers), "credit criterion IDs")

    @property
    def solver_item(self) -> dict[str, object]:
        if self.operation != "solver":
            return {}
        # Only public response shape enters a provider grammar. This contract
        # deliberately has no slot for expected answers or marking credits.
        return {
            "response_slots": list(self.response_slots),
            "choices": list(self.choices),
            "kind": self.kind,
            "marks": self.marks,
        }


@dataclass(frozen=True, init=False)
class GenerationRequest:
    prompt: str
    operation: str
    generation_seed: int | None
    attempt: int
    temperature: float
    output_budget: int
    expected_ids: tuple[str, ...]
    _schema_json: str = field(repr=False)

    def __init__(
        self,
        prompt: str,
        operation: str,
        schema: dict[str, Any],
        *,
        generation_seed: int | None = None,
        attempt: int = 1,
        temperature: float = 0.2,
        output_budget: int = 1536,
        expected_ids: tuple[str, ...] = (),
    ) -> None:
        if (
            not isinstance(prompt, str)
            or not prompt.strip()
            or not isinstance(operation, str)
            or operation not in OPERATIONS
        ):
            raise ValueError("request requires a prompt and supported operation")
        if generation_seed is not None:
            _integer(generation_seed, "generation_seed")
        _integer(attempt, "attempt", minimum=1)
        _integer(output_budget, "output_budget", minimum=1)
        if (
            type(temperature) not in {int, float}
            or not math.isfinite(temperature)
            or not 0 <= temperature <= 2
        ):
            raise ValueError("temperature must be finite and between zero and two")
        _strings(expected_ids, "expected_ids")
        if not isinstance(schema, dict) or schema.get("type") != "object":
            raise ValueError("request schema must describe a JSON object")
        if operation in {"authoring", "batch_review"}:
            OutputContract(operation, identifiers=expected_ids)
            field_name = "questions" if operation == "authoring" else "reviews"
            array = _batch_schema_object(schema, "properties", field_name)
            identifiers = _batch_schema_identifiers(array)
            _integer(array.get("minItems"), "batch minItems", minimum=1)
            _integer(array.get("maxItems"), "batch maxItems", minimum=1)
            if (
                array.get("minItems") != len(expected_ids)
                or array.get("maxItems") != len(expected_ids)
                or identifiers != list(expected_ids)
            ):
                raise ValueError("batch schema must match its owned identifiers")
        elif expected_ids:
            raise ValueError("expected batch identifiers require a batch operation")
        encoded = json.dumps(schema, allow_nan=False, ensure_ascii=False)
        for name, value in {
            "prompt": prompt,
            "operation": operation,
            "generation_seed": generation_seed,
            "attempt": attempt,
            "temperature": float(temperature),
            "output_budget": output_budget,
            "expected_ids": expected_ids,
            "_schema_json": encoded,
        }.items():
            object.__setattr__(self, name, value)

    @property
    def version(self) -> str:
        return REQUEST_VERSION

    @property
    def schema(self) -> dict[str, Any]:
        # Return a new tree on each handoff, including provider repair attempts.
        return json.loads(self._schema_json)

    @property
    def seed(self) -> int:
        if self.generation_seed is None:
            return 0
        return (self.generation_seed + 104_729 * self.attempt) % 2_147_483_647


def make_request(
    prompt: str,
    contract: OutputContract,
    *,
    generation_seed: int | None = None,
    attempt: int = 1,
) -> GenerationRequest:
    # Share the existing grammar definitions without importing transport modules
    # when loading this dependency-light contract. The explicit contract path
    # never uses the prompt-inference helpers retained for legacy callers.
    from Backend.Core.providers import _ollama_json_schema, _ollama_output_budget

    schema = _ollama_json_schema("", contract=contract)
    temperature = 0 if contract.operation in {"review", "batch_review"} else 0.2
    if contract.operation == "authoring":
        _integer(attempt, "attempt", minimum=1)
        temperature = min(0.4, 0.15 + 0.1 * attempt)
    return GenerationRequest(
        prompt,
        contract.operation,
        schema,
        generation_seed=generation_seed,
        attempt=attempt,
        temperature=temperature,
        output_budget=_ollama_output_budget(schema),
        expected_ids=contract.identifiers,
    )


def request_json(
    client: JSONGenerationClient, request: GenerationRequest
) -> dict[str, object]:
    # A dynamic Mock attribute is not an opt-in to the structured interface.
    declared = getattr(type(client), "generate_request", None)
    if callable(declared):
        return client.generate_request(request)
    return client.generate_json(request.prompt)
