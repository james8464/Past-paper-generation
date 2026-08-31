"""CS component policy audit over candidate-answerable paths, not printed totals."""
from __future__ import annotations

from collections import Counter
from itertools import combinations, product
from math import isclose, prod
from typing import Any

from Backend.Core.assessment_objectives import objective_policy_for
from Backend.Core.subjects.computer_science_contracts import CS_INPUTS, SumTrace


def audit_computer_science_blueprint(blueprint: dict[str, Any]) -> dict[str, Any]:
    policy = objective_policy_for("computer science")
    policy.validate(blueprint)
    marks = blueprint.get("total_marks")
    duration = blueprint.get("duration_minutes")
    if not isinstance(marks, int) or marks <= 0 or not isinstance(duration, (int, float)) or duration <= 0:
        raise ValueError("CS needs a declared candidate mark total and allotted time")
    sections = blueprint.get("sections")
    if sections:
        choices = []
        for section in sections:
            options = section["options"]
            for option in options:
                for question in option["questions"]:
                    raw_source = (question.get("authoring_context") or {}).get("cs_input_contract")
                    if raw_source is None:
                        continue
                    source = CS_INPUTS.validate_python(raw_source)
                    if isinstance(source, SumTrace) and (
                        option.get("chart_values") != source.values
                        or source.code() not in option.get("stimulus", [])
                        or f"Trace all {len(source.values)} iterations" not in question.get("prompt", "")
                        or "single final output" not in question.get("prompt", "")
                    ):
                        raise ValueError("CS trace source differs from its typed candidate-input contract")
            count = section.get("answer_options", 1 if len(options) == 1 else None)
            if not isinstance(count, int) or not 1 <= count <= len(options):
                raise ValueError("CS optional sections need an explicit candidate selection count")
            choices.append(list(combinations(options, count)))
        if prod(map(len, choices)) > 64:
            raise ValueError("CS candidate path audit exceeds its bounded path contract")
        paths = [[q for group in selection for option in group for q in option["questions"]]
                 for selection in product(*choices)]
    else:
        paths = [blueprint.get("questions", [])]
    code = str(blueprint.get("paper_code", ""))
    bank = blueprint.get("assessment_kind") == "question-bank"
    expected = None if bank else {
        "7517/1": {"AO1": 20, "AO2": 30, "AO3": 50},
        "7517/2": {"AO1": 56, "AO2": 40, "AO3": 4},
        "H446/01": {"AO1": 74, "AO2": 31, "AO3": 35},
        "H446/02": {"AO1": 53, "AO2": 63, "AO3": 24},
    }.get(code)
    if not bank and expected is None:
        raise ValueError("CS component has no calibrated objective budget")
    reports = []
    for questions in paths:
        parts = [part for question in questions for part in question.get("parts", [question])]
        totals: Counter[str] = Counter()
        candidate_marks, minutes = 0, 0.0
        for part in parts:
            allocation = part.get("assessment_objectives")
            tariff = part.get("marks")
            if not isinstance(allocation, dict) or not allocation or any(
                not isinstance(value, int) or value <= 0 for value in allocation.values()
            ) or sum(allocation.values()) != tariff:
                raise ValueError("CS requires explicit per-item objective credit")
            time = part.get("expected_minutes")
            if not isinstance(time, (int, float)) or not isclose(time, duration * tariff / marks):
                raise ValueError("CS item timing differs from its declared allowance")
            totals.update(allocation)
            candidate_marks += tariff
            minutes += time
        if candidate_marks != marks or not isclose(minutes, duration):
            raise ValueError("CS candidate-path marks or allotted time do not reconcile")
        if expected is not None and dict(totals) != expected:
            raise ValueError("CS candidate-path objective budget differs from the calibrated task plan")
        reports.append({"marks": candidate_marks, "allotted_minutes": round(minutes, 6),
                        "assessment_objectives": dict(totals)})
    return {
        "policy_version": policy.version, "candidate_paths": reports,
        "allocation_basis": "task-based inferred OCR allocations" if code.startswith("H446") else
            "task-based focused-practice allocations" if bank else
            "original tasks calibrated to published AQA June 2025 component totals",
        "whole_paper_percentage_target_applied": not bank,
        "reference_scope": "pooled whole-paper proxy; insufficient topic-specific evidence" if bank else "component",
        "timing_basis": "pro-rata declared allowance including reading and checking; not observed student completion time",
        "empirical_equivalence_claimed": False,
    }
