"""Strict, deterministic task contracts for AQA CS topic-reference evidence."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

TOPIC_CONTRACT_POLICY_ID = "aqa-cs-topic-evidence-v1"
TaskOperation = Literal[
    "retrieve",
    "describe",
    "explain",
    "analyse",
    "represent",
    "trace",
    "program",
    "complete-code",
    "judge",
]
ResponseMode = Literal[
    "prose",
    "table",
    "diagram",
    "code",
    "query",
    "selected",
    "multi-selected",
    "result",
    "sequence",
]


class ReferenceTaskContract(BaseModel):
    """The serialised summary is valid only when it agrees with the question."""

    model_config = ConfigDict(extra="forbid", strict=True)

    policy_id: Literal["aqa-cs-topic-evidence-v1"]
    topic_id: Literal["4.2", "4.10", "4.12"]
    style_id: str = Field(min_length=1)
    operation: TaskOperation
    response_mode: ResponseMode
    source_dependency: Literal["self-contained", "task-context"]


def derive_task_semantics(
    *,
    task_operation: Any,
    prompt: Any,
    options: Any = (),
    response_slots: Any = (),
) -> tuple[TaskOperation, ResponseMode] | None:
    """Derive the comparison form from printed question data, never its hint."""
    operation = str(task_operation).casefold().strip()
    text = str(prompt).casefold().strip()
    has_options = isinstance(options, list) and bool(options)
    slots = response_slots if isinstance(response_slots, list) else []

    if has_options and operation in {
        "retrieve",
        "describe",
        "explain",
        "analyse",
        "represent",
        "trace",
        "program",
        "complete-code",
        "judge",
    }:
        return (
            operation,  # type: ignore[return-value]
            "multi-selected"
            if " all " in f" {text} " or " two " in f" {text} "
            else "selected",
        )
    if text.startswith(("draw ", "construct ", "complete ")):
        if "adjacency matrix" in text:
            return "represent", "table"
        if any(word in text for word in ("tree", "diagram", "relationship")):
            return "represent", "diagram"
    if operation == "trace" and "table" in text:
        return "trace", "table"
    if slots and operation in {
        "retrieve",
        "describe",
        "explain",
        "analyse",
        "represent",
        "trace",
        "program",
        "complete-code",
        "judge",
    }:
        return operation, "sequence" if len(slots) > 1 else "result"  # type: ignore[return-value]
    if operation == "program":
        return "program", "query" if "select" in text else "code"
    if operation in {"retrieve", "describe", "explain", "analyse", "judge"}:
        return operation, "prose"  # type: ignore[return-value]
    return None
