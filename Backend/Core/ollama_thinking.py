"""Choose advertised Ollama controls without changing structured-output contracts."""

from __future__ import annotations

from typing import Any


def structured_thinking_policy(envelope: object) -> dict[str, Any]:
    policy: dict[str, Any] = {
        "version": "ollama-structured-thinking-v1",
        "requested": False,
        "status": "legacy_unknown",
        "metadata": "unavailable" if envelope is None else "absent",
    }
    if not isinstance(envelope, dict) or "thinking" not in envelope:
        return policy
    metadata = envelope["thinking"]
    if not isinstance(metadata, dict):
        raise ValueError("Ollama thinking metadata is malformed.")
    values, default = metadata.get("values"), metadata.get("default")

    def valid(value: object) -> bool:
        return type(value) is bool or (
            isinstance(value, str) and 0 < len(value) <= 64 and value.strip() == value
        )

    if (
        not isinstance(values, list)
        or not 1 <= len(values) <= 16
        or not all(valid(value) for value in values)
        or not valid(default)
        or len({(type(value), value) for value in values}) != len(values)
        or not any(
            type(default) is type(value) and default == value for value in values
        )
    ):
        raise ValueError("Ollama thinking metadata is malformed.")
    requested = default
    status = "reduction_unavailable"
    if any(value is False for value in values):
        requested, status = False, "disabled"
    elif "low" in values:
        requested, status = "low", "reduced"
    policy.update(
        requested=requested,
        status=status,
        metadata="advertised",
        values=list(values),
        default=default,
    )
    return policy
