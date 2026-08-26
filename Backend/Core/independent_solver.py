from __future__ import annotations

import ast
import json
import math
import operator
import re
from collections import Counter
from collections.abc import Sequence
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from Backend.Core.assessment_contracts import EvidenceRecord
from Backend.Core.assessment_quality import content_similarity


class SolverClient(Protocol):
    def generate_json(self, prompt: str) -> dict[str, object]: ...


class CanonicalSolution(BaseModel):
    model_config = ConfigDict(frozen=True)

    item_id: str
    answer: str
    steps: list[str] = Field(default_factory=list)
    mark_points: list[str] = Field(default_factory=list)
    assessment_objectives: dict[str, int] = Field(default_factory=dict)
    alternatives: list[str] = Field(default_factory=list)
    partial_credit_boundaries: list[str] = Field(default_factory=list)
    follow_through_rules: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    numeric_results: dict[str, float] = Field(default_factory=dict)
    solver_context_fields: list[str] = Field(default_factory=list)


class ReconciliationIssue(BaseModel):
    model_config = ConfigDict(frozen=True)

    field: str
    message: str


class ReconciliationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    passed: bool
    issues: list[ReconciliationIssue] = Field(default_factory=list)


class IndependentSolver:
    """Solve an item in a context that deliberately excludes its draft scheme."""

    def __init__(self, client: SolverClient | None = None) -> None:
        self.client = client

    def solve(
        self,
        item: Any,
        sources: Sequence[EvidenceRecord],
    ) -> CanonicalSolution:
        raw_item = _as_mapping(item)
        item_id = str(
            raw_item.get("id")
            or raw_item.get("rule_id")
            or raw_item.get("number")
            or "unknown"
        )
        context = dict(raw_item.get("authoring_context") or {})
        allowed_source_ids = {source.id for source in sources}
        solver_item = {
            key: value
            for key, value in raw_item.items()
            if key
            not in {
                "mark_scheme",
                "structured_mark_scheme",
                "marking",
                "indicative_content",
            }
        }
        result: dict[str, Any] = {}
        if self.client is not None:
            result = dict(
                self.client.generate_json(
                    "Independently solve this UK A-level assessment item. Do not "
                    "infer or reproduce a draft mark scheme. Recompute every numeric "
                    "result and cite only the supplied evidence IDs. Return JSON with "
                    "answer, steps, mark_points, evidence_ids, alternatives, "
                    "partial_credit_boundaries and follow_through_rules.\n"
                    + json.dumps(
                        {
                            "item": solver_item,
                            "sources": [source.model_dump() for source in sources],
                        },
                        ensure_ascii=False,
                    )
                )
            )

        numeric_results: dict[str, float] = {}
        expression = context.get("calculation_expression")
        variables = context.get("calculation_variables")
        if isinstance(expression, str) and isinstance(variables, dict):
            numeric = _safe_calculate(expression, variables)
            numeric_results["result"] = numeric
            result["answer"] = _format_number(numeric)

        evidence_ids = _string_list(result.get("evidence_ids"))
        unavailable = set(evidence_ids) - allowed_source_ids
        if unavailable:
            raise ValueError(
                f"{item_id} canonical solution cites unavailable evidence: "
                f"{sorted(unavailable)}"
            )

        answer = str(result.get("answer", "")).strip()
        if not answer:
            choices = raw_item.get("choices")
            correct = raw_item.get("correct_choice")
            if (
                isinstance(choices, list)
                and isinstance(correct, int)
                and 0 <= correct < len(choices)
            ):
                answer = str(choices[correct]).strip()
        if not answer:
            raise ValueError(f"{item_id} independent solver returned no answer")

        observable = _string_list(
            context.get("observable_mark_points") or result.get("mark_points")
        )
        return CanonicalSolution(
            item_id=item_id,
            answer=answer,
            steps=_string_list(result.get("steps")),
            mark_points=observable,
            assessment_objectives={
                str(key): int(value)
                for key, value in dict(
                    raw_item.get("assessment_objectives") or {}
                ).items()
            },
            alternatives=_string_list(
                context.get("valid_alternatives") or result.get("alternatives")
            ),
            partial_credit_boundaries=_string_list(
                context.get("partial_credit_boundaries")
                or result.get("partial_credit_boundaries")
            ),
            follow_through_rules=_string_list(
                context.get("follow_through_rules")
                or result.get("follow_through_rules")
            ),
            evidence_ids=evidence_ids,
            numeric_results=numeric_results,
            solver_context_fields=sorted(solver_item),
        )


def reconcile_solution(
    solution: CanonicalSolution,
    scheme: Any,
) -> ReconciliationResult:
    raw = _as_mapping(scheme)
    points = raw.get("points") or raw.get("structured_mark_scheme") or []
    if not isinstance(points, list):
        points = []
    if not points and isinstance(raw.get("mark_scheme"), list):
        points = [
            {"text": str(text), "marks": 0, "assessment_objective": None}
            for text in raw["mark_scheme"]
        ]
    text = "\n".join(
        str(point.get("text", "")) if isinstance(point, dict) else str(point)
        for point in points
    )
    normalised_text = _normalise(text)
    issues: list[ReconciliationIssue] = []

    expected_numbers = _numbers(solution.answer)
    scheme_numbers = _numbers(text)
    if expected_numbers:
        if not all(
            any(
                math.isclose(expected, actual, rel_tol=1e-7, abs_tol=1e-7)
                for actual in scheme_numbers
            )
            for expected in expected_numbers
        ):
            issues.append(
                ReconciliationIssue(
                    field="answer",
                    message=f"scheme does not contain canonical answer {solution.answer}",
                )
            )
    elif solution.answer and content_similarity(solution.answer, text) < 0.2:
        issues.append(
            ReconciliationIssue(
                field="answer",
                message="scheme does not substantively match the canonical answer",
            )
        )

    for field, requirements in (
        ("alternatives", solution.alternatives),
        ("partial_credit_boundaries", solution.partial_credit_boundaries),
        ("follow_through_rules", solution.follow_through_rules),
    ):
        missing = [
            requirement
            for requirement in requirements
            if _normalise(requirement) not in normalised_text
            and content_similarity(requirement, text) < 0.25
        ]
        if missing:
            issues.append(
                ReconciliationIssue(
                    field=field,
                    message=f"scheme omits: {missing}",
                )
            )

    allocation: Counter[str] = Counter()
    total_marks = 0
    for point in points:
        if not isinstance(point, dict):
            continue
        marks = int(point.get("marks", 0) or 0)
        total_marks += marks
        objective = point.get("assessment_objective")
        if objective and marks:
            allocation[str(objective)] += marks
    if (
        solution.assessment_objectives
        and dict(allocation) != solution.assessment_objectives
    ):
        issues.append(
            ReconciliationIssue(
                field="assessment_objectives",
                message=(
                    f"scheme allocation {dict(allocation)} does not match "
                    f"{solution.assessment_objectives}"
                ),
            )
        )
    declared_marks = raw.get("marks")
    if (
        isinstance(declared_marks, int)
        and total_marks
        and total_marks != declared_marks
    ):
        issues.append(
            ReconciliationIssue(
                field="marks",
                message=f"scheme awards {total_marks} marks, expected {declared_marks}",
            )
        )
    for mark_point in solution.mark_points:
        if (
            _normalise(mark_point) not in normalised_text
            and content_similarity(mark_point, text) < 0.2
        ):
            issues.append(
                ReconciliationIssue(
                    field="mark_points",
                    message=f"scheme omits observable mark point: {mark_point}",
                )
            )
    return ReconciliationResult(passed=not issues, issues=issues)


_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_calculate(expression: str, variables: dict[str, Any]) -> float:
    numeric_variables = {
        str(name): float(value)
        for name, value in variables.items()
        if isinstance(value, (int, float)) and math.isfinite(float(value))
    }

    def evaluate(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Name) and node.id in numeric_variables:
            return numeric_variables[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
            return float(
                _OPERATORS[type(node.op)](evaluate(node.left), evaluate(node.right))
            )
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
            return float(_OPERATORS[type(node.op)](evaluate(node.operand)))
        raise ValueError("calculation expression contains an unsupported operation")

    result = evaluate(ast.parse(expression, mode="eval"))
    if not math.isfinite(result):
        raise ValueError("calculation expression returned a non-finite result")
    return result


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "model_dump"):
        raw = value.model_dump(mode="json")
        if isinstance(raw, dict):
            return raw
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    raise TypeError("assessment value must be an object")


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple, set)):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _numbers(value: str) -> list[float]:
    return [
        float(token.replace(",", ""))
        for token in re.findall(r"-?\d[\d,]*(?:\.\d+)?", value)
    ]


def _normalise(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


def _format_number(value: float) -> str:
    return str(int(value)) if value.is_integer() else f"{value:.12g}"
