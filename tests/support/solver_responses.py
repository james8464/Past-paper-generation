"""Complete strict solver envelopes for tests exercising later pipeline stages."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def complete_solver_response(response: dict[str, Any]) -> dict[str, Any]:
    completed = {
        "steps": [],
        "evidence_ids": [],
        "alternatives": [],
        "partial_credit_boundaries": [],
        "follow_through_rules": [],
    }
    completed.update(deepcopy(response))
    return completed
