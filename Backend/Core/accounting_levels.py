"""Bind Accounting's printed mark bands to its exported response policy."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from Backend.Core.level_of_response import BoardLevelPolicy, load_level_policies
from Backend.Core.paths import REPO_ROOT


@lru_cache(maxsize=1)
def _policies() -> dict[str, BoardLevelPolicy]:
    return load_level_policies(REPO_ROOT / "Resources/level-of-response-policies.json")


def accounting_level_policy(marks: int) -> BoardLevelPolicy:
    policy_id = f"aqa-accounting-{marks}-mark"
    try:
        return _policies()[policy_id]
    except KeyError as error:
        raise ValueError("Accounting level tariff has no canonical policy") from error


def validate_accounting_level_contract(
    raw: dict[str, Any], contract: dict[str, Any]
) -> None:
    if raw.get("scheme_mode") != "levels":
        return
    context = raw.get("authoring_context") or {}
    # The separately validated two-reason policy has two independent grids.
    if contract.get("level_policy_id") == "aqa-accounting-two-reasons-v1" and (
        "grouped_level_policy" in contract or "grouped_level_policy" in context
    ):
        return
    policy = accounting_level_policy(raw.get("marks"))
    if contract.get("level_policy_id") != policy.id or (
        "level_policy_id" in context and context["level_policy_id"] != policy.id
    ):
        raise ValueError("Accounting level policy is stale or differs from its tariff")
    actual = []
    for text in raw.get("mark_scheme", []):
        match = re.fullmatch(
            r"Level (\d+) \((\d+)(?:[–-](\d+))?\):\s*(.+)", text, re.DOTALL
        )
        if match:
            actual.append((int(match[1]), int(match[2]), int(match[3] or match[2])))
    expected = [
        (level.level, level.minimum_mark, level.maximum_mark)
        for level in reversed(policy.levels)
    ]
    if actual != expected:
        raise ValueError(
            "Accounting printed level grid differs from its canonical policy"
        )
