from __future__ import annotations

import ast
import json
import math
import operator
import re
from collections import Counter
from collections.abc import Sequence
from decimal import Decimal
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from Backend.Core.assessment_contracts import EvidenceRecord
from Backend.Core.assessment_quality import content_similarity
from Backend.Core.numeric_integrity import (
    NUMERIC_INTEGRITY_VERSION,
    CheckedNumericOutput,
    CheckedTextOutput,
    NumericOutput,
    check_published_outputs,
    display,
    numeric_result,
)
from Backend.Core.subjects.accounting import solve_accounting_calculation


class SolverClient(Protocol):
    def generate_json(self, prompt: str) -> dict[str, object]: ...


class CanonicalSolution(BaseModel):
    model_config = ConfigDict(frozen=True)

    item_id: str
    answer: str
    steps: list[str] = Field(default_factory=list)
    mark_points: list[str] = Field(default_factory=list)
    mark_points_exhaustive: bool = True
    assessment_objectives: dict[str, int] = Field(default_factory=dict)
    alternatives: list[str] = Field(default_factory=list)
    partial_credit_boundaries: list[str] = Field(default_factory=list)
    follow_through_rules: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    numeric_results: dict[str, float] = Field(default_factory=dict)
    solver_context_fields: list[str] = Field(default_factory=list)
    response_slots: list[str] = Field(default_factory=list)
    answer_slots: dict[str, str] = Field(default_factory=dict)
    integrity_version: str = "legacy-unverified"
    solution_source: str = "legacy-unverified"
    verified_scope: str = "none"
    examiner_expectations: list[str] = Field(default_factory=list)
    numeric_checks: list[CheckedNumericOutput] = Field(default_factory=list)
    text_checks: list[CheckedTextOutput] = Field(default_factory=list)
    is_choice: bool = False
    unverified_model_working: dict[str, Any] = Field(default_factory=dict)


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
        solver_item = _without_answer_key(raw_item)
        response_slots = raw_item.get("response_slots") or []
        if (
            not isinstance(response_slots, list)
            or any(
                not isinstance(slot, str) or not slot.strip() for slot in response_slots
            )
            or len(set(response_slots)) != len(response_slots)
        ):
            raise ValueError(f"{item_id} invalid closed response slot contract")
        deterministic = solve_accounting_calculation(raw_item)
        expression = context.get("calculation_expression")
        variables = context.get("calculation_variables")
        expressions = context.get("calculation_expressions")
        if expression is not None or variables is not None or expressions is not None:
            if not isinstance(variables, dict):
                raise ValueError(f"{item_id} incomplete numeric expression contract")
            if expressions is None:
                output = NumericOutput.model_validate(context.get("calculation_output"))
                outputs = [output]
                expressions = {output.role: expression}
            else:
                outputs = [
                    NumericOutput.model_validate(raw)
                    for raw in context.get("calculation_outputs", [])
                ]
            if (
                not isinstance(expressions, dict)
                or set(expressions) != {output.role for output in outputs}
                or len(expressions) != len(outputs)
                or not outputs
            ):
                raise ValueError(f"{item_id} incomplete numeric output contract")
            units = context.get("calculation_input_units")
            if (
                not isinstance(units, dict)
                or set(units) != set(variables)
                or not all(
                    isinstance(unit, str) and unit.strip() for unit in units.values()
                )
            ):
                raise ValueError(
                    f"{item_id} numeric input units contract is incomplete"
                )
            values = {}
            steps = []
            for role, expr in expressions.items():
                if not isinstance(expr, str):
                    raise ValueError(f"{item_id} invalid numeric expression contract")
                values[role] = _safe_calculate(expr, {**variables, **values})
                steps.append(f"Evaluate {expr} from candidate inputs for {role}.")
            deterministic = numeric_result(
                values,
                outputs,
                steps,
            )
        if deterministic:
            response_slots = list(deterministic["answer"])
        elif not response_slots and _requires_numeric_contract(raw_item):
            raise ValueError(f"{item_id} unsupported closed numeric output contract")
        result: dict[str, Any] = deterministic or {}
        response_instructions = (
            " For a closed response (response_slots supplied), answer and "
            "mark_points must EACH be a JSON object mapping EVERY supplied "
            "slot ID to the same single final answer string, with no extra "
            "slots or commentary. Work out the solution in steps FIRST, then "
            "write answer, then copy those final values into mark_points. "
            'Format example only: "answer": {"slot-id": "final value"}, '
            '"mark_points": {"slot-id": "final value"}. Use the actual supplied '
            "slot IDs. Do not put grading prose or nested objects in either mapping."
            if response_slots
            else " For multiple choice, mark_points must contain exactly one string: "
            "the same selected option as answer. Put reasoning in steps."
        )
        if deterministic is None and self.client is not None:
            result = dict(
                self.client.generate_json(
                    "Independently solve this UK A-level assessment item. Do not "
                    "infer or reproduce a draft mark scheme. Recompute every numeric "
                    "result and cite only the supplied evidence IDs; when sources is "
                    "empty, evidence_ids must be an empty array. For multiple choice, "
                    "return the complete option text rather than its number or letter. "
                    "Return JSON with "
                    "steps, answer, mark_points, evidence_ids, alternatives, "
                    "partial_credit_boundaries and follow_through_rules."
                    + response_instructions
                    + "\n"
                    + json.dumps(
                        {
                            "item": solver_item,
                            "sources": [source.model_dump() for source in sources],
                        },
                        ensure_ascii=False,
                    )
                )
            )

        numeric_results: dict[str, float] = (
            dict(result.get("numeric_results") or {}) if deterministic else {}
        )

        evidence_ids = [
            evidence_id
            for evidence_id in _string_list(result.get("evidence_ids"))
            if evidence_id != item_id
        ]
        unavailable = set(evidence_ids) - allowed_source_ids
        if unavailable:
            raise ValueError(
                f"{item_id} canonical solution cites unavailable evidence: "
                f"{sorted(unavailable)}"
            )

        answer_slots: dict[str, str] = {}
        if response_slots:
            for field in ("answer", "mark_points"):
                values = result.get(field)
                if (
                    not isinstance(values, dict)
                    or set(values) != set(response_slots)
                    or any(
                        not isinstance(value, str) or not value.strip()
                        for value in values.values()
                    )
                ):
                    raise ValueError(
                        f"{item_id} closed response {field} must fill every slot exactly once"
                    )
            answer_slots = {
                slot: result["answer"][slot].strip() for slot in response_slots
            }
            if any(
                _closed_normalise(answer_slots[slot])
                != _closed_normalise(result["mark_points"][slot])
                for slot in response_slots
            ):
                raise ValueError(
                    f"{item_id} closed response answer and mark_points contradict"
                )
        answer = (
            json.dumps(answer_slots, ensure_ascii=False)
            if response_slots
            else str(result.get("answer", "")).strip()
        )
        choices = raw_item.get("choices")
        if (
            raw_item.get("kind") == "multiple_choice"
            and isinstance(choices, list)
            and not response_slots
        ):
            answer = _normalise_choice_answer(answer, choices)
            points = result.get("mark_points")
            if (
                answer not in choices
                or not isinstance(points, list)
                or len(points) != 1
                or not isinstance(points[0], str)
                or _normalise_choice_answer(points[0], choices) != answer
            ):
                raise ValueError(
                    f"{item_id} closed response choice and mark_points must name the same single option"
                )
        if not answer:
            raise ValueError(f"{item_id} independent solver returned no answer")

        is_single_mark_choice = (
            raw_item.get("kind") == "multiple_choice"
            and raw_item.get("marks") == 1
            and isinstance(raw_item.get("choices"), list)
        )
        declared_observable = _string_list(context.get("observable_mark_points"))
        observable = (
            []
            if response_slots
            else (
                [answer]
                if is_single_mark_choice
                else _string_list(result.get("mark_points"))
            )
        )
        answer_form = str(
            context.get("expected_answer_form", "constructed_response")
        ).casefold()
        fixed_answer = (
            bool(response_slots)
            or is_single_mark_choice
            or bool(numeric_results)
            or any(
                token in answer_form
                for token in ("calculation", "numeric", "exact", "choice", "closed")
            )
        )
        return CanonicalSolution(
            item_id=item_id,
            answer=answer,
            steps=_string_list(result.get("steps")),
            mark_points=observable,
            mark_points_exhaustive=fixed_answer,
            examiner_expectations=declared_observable,
            assessment_objectives={
                str(key): int(value)
                for key, value in dict(
                    raw_item.get("assessment_objectives") or {}
                ).items()
            },
            alternatives=_string_list(result.get("alternatives")),
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
            response_slots=response_slots,
            answer_slots=answer_slots,
            integrity_version=NUMERIC_INTEGRITY_VERSION,
            solution_source="deterministic-candidate-inputs"
            if deterministic
            else "independent-model",
            verified_scope="declared-numeric-outputs-only"
            if deterministic
            else "closed-slots"
            if response_slots
            else "semantic-review-only",
            numeric_checks=result.get("numeric_checks", []) if deterministic else [],
            text_checks=result.get("text_checks", []) if deterministic else [],
            is_choice=raw_item.get("kind") == "multiple_choice",
            unverified_model_working={
                key: result[key]
                for key in ("numeric_results", "calculation_details")
                if key in result
            }
            if not deterministic
            else {},
        )


def _without_answer_key(value: Any) -> Any:
    hidden = {
        "mark_scheme",
        "structured_mark_scheme",
        "marking",
        "mark_breakdown",
        "indicative_content",
        "correct_choice",
        "correct_option",
        "verified_answers",
        "canonical_solution",
        "observable_mark_points",
        "valid_alternatives",
        "partial_credit_boundaries",
        "follow_through_rules",
        "difficulty_evidence",
        "required_mark_scheme_terms",
        "forbidden_mark_scheme_terms",
        "closed_answers",
    }
    if isinstance(value, dict):
        return {
            key: _without_answer_key(child)
            for key, child in value.items()
            if key not in hidden
        }
    if isinstance(value, list):
        return [_without_answer_key(child) for child in value]
    return value


def require_solution_matches_scheme(
    solution: CanonicalSolution,
    scheme: dict[str, Any],
    *,
    expected_choice: str | None = None,
) -> None:
    if expected_choice is not None and solution.response_slots == ["choice"]:
        scheme = {**scheme, "closed_answers": {"choice": [expected_choice]}}
        expected_choice = None
    if expected_choice is not None and _closed_normalise(
        solution.answer
    ) != _closed_normalise(expected_choice):
        raise ValueError(
            f"{solution.item_id} independent answer disagrees with the keyed option"
        )
    if expected_choice is not None:
        scheme = {
            **scheme,
            "mark_scheme": [*scheme.get("mark_scheme", []), expected_choice],
        }
    result = reconcile_solution(solution, scheme)
    if not result.passed:
        raise ValueError(
            f"{solution.item_id} failed independent solution reconciliation: "
            + "; ".join(issue.message for issue in result.issues)
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
    semantic_parts = [
        part
        for part in (
            *(_semantic_text(point) for point in points),
            _semantic_text(raw.get("mark_scheme")),
            _semantic_text(raw.get("alternatives")),
            _semantic_text(raw.get("partial_credit_boundaries")),
            _semantic_text(raw.get("follow_through_rules")),
        )
        if part
    ]
    text = "\n".join(semantic_parts)
    normalised_text = _normalise(text)
    issues: list[ReconciliationIssue] = []

    if (
        _requires_numeric_contract(raw) or solution.numeric_results
    ) and not solution.response_slots:
        issues.append(
            ReconciliationIssue(
                field="answer",
                message="closed numeric response is missing its output contract",
            )
        )

    if solution.numeric_checks:
        if raw.get("authoring_context"):
            try:
                recomputed = IndependentSolver().solve(raw, [])
                if (
                    solution.numeric_checks != recomputed.numeric_checks
                    or solution.text_checks != recomputed.text_checks
                ):
                    issues.append(
                        ReconciliationIssue(
                            field="answer",
                            message="numeric checks disagree with the complete candidate-input contract",
                        )
                    )
            except (ValueError, KeyError, ArithmeticError):
                issues.append(
                    ReconciliationIssue(
                        field="answer",
                        message="numeric candidate-input contract cannot be recomputed",
                    )
                )
        numeric_roles = {check.role for check in solution.numeric_checks}
        required = numeric_roles | {check.role for check in solution.text_checks}
        if (
            solution.integrity_version != NUMERIC_INTEGRITY_VERSION
            or solution.solution_source != "deterministic-candidate-inputs"
            or solution.verified_scope != "declared-numeric-outputs-only"
            or set(solution.answer_slots) != required
            or set(solution.response_slots) != required
            or set(solution.numeric_results) != numeric_roles
        ):
            issues.append(
                ReconciliationIssue(
                    field="answer",
                    message="numeric response has stale or incomplete output contract",
                )
            )
        for check in solution.numeric_checks:
            if solution.answer_slots.get(check.role) != display(
                Decimal(check.value), check
            ):
                issues.append(
                    ReconciliationIssue(
                        field="answer",
                        message=f"numeric answer disagrees at role {check.role}",
                    )
                )
            if solution.numeric_results.get(check.role) != float(check.value):
                issues.append(
                    ReconciliationIssue(
                        field="answer",
                        message=f"numeric result disagrees at role {check.role}",
                    )
                )
        # Check both representations when supplied: neither a stale structured
        # scheme nor the published prose may hide behind the other.
        texts = ["\n".join(_semantic_text(point) for point in points)]
        if isinstance(raw.get("mark_scheme"), list) and raw.get(
            "structured_mark_scheme"
        ):
            texts.append("\n".join(raw["mark_scheme"]))
        for published in texts:
            issues.extend(
                ReconciliationIssue(field="answer", message=message)
                for message in check_published_outputs(
                    solution.numeric_checks, published
                )
            )
            for check in solution.text_checks:
                matches = re.findall(check.scheme_pattern, published, re.MULTILINE)
                if (
                    not matches
                    or any(value != check.value for value in matches)
                    or solution.answer_slots.get(check.role) != check.value
                ):
                    issues.append(
                        ReconciliationIssue(
                            field="answer",
                            message=f"closed response disagrees at role {check.role}",
                        )
                    )

    if raw.get("kind") == "multiple_choice":
        choices, key = raw.get("choices"), raw.get("correct_choice")
        if (
            not isinstance(choices, list)
            or type(key) is not int
            or not 0 <= key < len(choices)
            or _closed_normalise(solution.answer)
            != _closed_normalise(str(choices[key]))
        ):
            issues.append(
                ReconciliationIssue(
                    field="answer",
                    message="independent answer disagrees with the keyed option",
                )
            )
    if raw.get("closed_answers") and not solution.response_slots:
        issues.append(
            ReconciliationIssue(
                field="answer",
                message="closed response is missing its required slot contract",
            )
        )
    if solution.response_slots:
        if solution.answer != json.dumps(solution.answer_slots, ensure_ascii=False):
            issues.append(
                ReconciliationIssue(
                    field="answer",
                    message="closed response answer contradicts its slot values",
                )
            )
        accepted = (
            {
                **{
                    check.role: [display(Decimal(check.value), check)]
                    for check in solution.numeric_checks
                },
                **{check.role: [check.value] for check in solution.text_checks},
            }
            if solution.numeric_checks
            else raw.get("closed_answers")
        )
        if not isinstance(accepted, dict) or set(accepted) != set(
            solution.response_slots
        ):
            issues.append(
                ReconciliationIssue(
                    field="answer",
                    message="scheme lacks the complete closed response slot key",
                )
            )
        elif set(solution.answer_slots) != set(solution.response_slots):
            issues.append(
                ReconciliationIssue(
                    field="answer",
                    message="closed response is missing required answers",
                )
            )
        else:
            for slot in solution.response_slots:
                alternatives = accepted[slot]
                if (
                    not isinstance(alternatives, list)
                    or not alternatives
                    or any(
                        not isinstance(value, str) or not value.strip()
                        for value in alternatives
                    )
                    or _closed_normalise(solution.answer_slots[slot])
                    not in {_closed_normalise(value) for value in alternatives}
                ):
                    issues.append(
                        ReconciliationIssue(
                            field="answer",
                            message=f"closed response disagrees at slot {slot}",
                        )
                    )

    expected_numbers = [] if solution.response_slots else _numbers(solution.answer)
    if expected_numbers and solution.mark_points_exhaustive and not solution.is_choice:
        issues.append(
            ReconciliationIssue(
                field="answer",
                message="closed numeric response requires an exhaustive role/value/unit contract",
            )
        )
    elif (
        not solution.response_slots
        and solution.answer
        and not solution.mark_points
        and content_similarity(solution.answer, text) < 0.2
    ):
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
            if not _requirement_present(
                requirement,
                normalised_text=normalised_text,
                semantic_parts=semantic_parts,
                threshold=0.5,
            )
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
    for mark_point in [
        *solution.examiner_expectations,
        *(solution.mark_points if solution.mark_points_exhaustive else []),
    ]:
        if not _requirement_present(
            mark_point,
            normalised_text=normalised_text,
            semantic_parts=semantic_parts,
            threshold=0.42,
            allow_concept_coverage=True,
        ):
            issues.append(
                ReconciliationIssue(
                    field="mark_points",
                    message=f"scheme omits observable mark point: {mark_point}",
                )
            )
    return ReconciliationResult(passed=not issues, issues=issues)


def _requires_numeric_contract(item: dict[str, Any]) -> bool:
    if item.get("kind") == "multiple_choice":
        return False
    context = item.get("authoring_context") or {}
    form = str(context.get("expected_answer_form", "")).casefold()
    return (
        item.get("kind") in {"calculation", "trace"}
        or any(
            token in form
            for token in ("numeric", "calculation", "closed", "trace_table")
        )
        or str(item.get("command_word", "")).casefold() == "calculate"
    )


def _closed_normalise(value: str) -> str:
    # No fuzzy overlap: preserve signs, decimal points, order and logical operators.
    normalised = " ".join(value.casefold().split()).rstrip(".;")
    normalised = re.sub(r"\s*,\s*", ",", normalised)
    return re.sub(r"(?<=\d)\s+(?=[a-z%])", "", normalised)


_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_calculate(expression: str, variables: dict[str, Any]) -> Decimal:
    numeric_variables = {
        str(name): Decimal(str(value))
        for name, value in variables.items()
        if not isinstance(value, bool)
        and isinstance(value, (int, float, Decimal))
        and Decimal(str(value)).is_finite()
    }
    if set(numeric_variables) != set(variables):
        raise ValueError("numeric variables must be finite numbers, not booleans")

    def evaluate(node: ast.AST) -> Decimal:
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return Decimal(str(node.value))
        if isinstance(node, ast.Name) and node.id in numeric_variables:
            return numeric_variables[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
            return Decimal(
                _OPERATORS[type(node.op)](evaluate(node.left), evaluate(node.right))
            )
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
            return Decimal(_OPERATORS[type(node.op)](evaluate(node.operand)))
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
    return [text for item in value if (text := _rubric_text(item))]


def _rubric_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("point", "text", "condition", "rule", "description", "answer"):
            text = value.get(key)
            if isinstance(text, str) and text.strip():
                return text.strip()
    return ""


def _semantic_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple, set)):
        return "\n".join(filter(None, (_semantic_text(item) for item in value)))
    if not isinstance(value, dict):
        return ""
    fields = (
        "text",
        "answer",
        "point",
        "condition",
        "rule",
        "alternatives",
        "allow",
        "notes",
        "partial_credit_boundaries",
        "follow_through_rules",
    )
    return "\n".join(text for key in fields if (text := _semantic_text(value.get(key))))


def _requirement_present(
    requirement: str,
    *,
    normalised_text: str,
    semantic_parts: list[str],
    threshold: float,
    allow_concept_coverage: bool = False,
) -> bool:
    normalised_requirement = _normalise(requirement)
    if normalised_requirement and normalised_requirement in normalised_text:
        return True
    segments = [
        segment.strip()
        for part in semantic_parts
        for segment in part.splitlines()
        if segment.strip()
    ]
    if any(
        content_similarity(requirement, segment, width=1) >= threshold
        for segment in segments
    ):
        return True
    return allow_concept_coverage and any(
        _concept_coverage(requirement, segment) >= 0.4 for segment in segments
    )


_CONCEPT_STOP_WORDS = {
    "a",
    "an",
    "and",
    "can",
    "for",
    "from",
    "help",
    "in",
    "its",
    "may",
    "of",
    "or",
    "other",
    "per",
    "potentially",
    "the",
    "this",
    "to",
    "with",
}
_CONCEPT_ALIASES = {
    "bought": "purchase",
    "buy": "purchase",
    "buying": "purchase",
    "competed": "compete",
    "competes": "compete",
    "competition": "compete",
    "competitive": "compete",
    "customers": "customer",
    "economies": "economy",
    "encourages": "encourage",
    "improves": "improve",
    "increases": "increase",
    "orders": "order",
    "prices": "price",
    "purchased": "purchase",
    "purchases": "purchase",
    "purchasing": "purchase",
    "retains": "retain",
    "sales": "sale",
    "sold": "sale",
    "suppliers": "supplier",
}


def _concept_coverage(requirement: str, candidate: str) -> float:
    expected = _concept_tokens(requirement)
    actual = _concept_tokens(candidate)
    if not expected or not actual:
        return 0.0
    overlap = len(expected & actual)
    minimum_overlap = 1 if len(expected) == 1 else 2
    return overlap / len(expected) if overlap >= minimum_overlap else 0.0


def _concept_tokens(value: str) -> set[str]:
    value = re.sub(
        r"^\s*(?:reason|explanation|point|step)\s*\d*\s*:\s*",
        "",
        value,
        flags=re.IGNORECASE,
    )
    tokens = set(re.findall(r"[a-z]+", value.casefold())) - _CONCEPT_STOP_WORDS
    return {_CONCEPT_ALIASES.get(token, token) for token in tokens}


def _numbers(value: str) -> list[float]:
    return [
        float(token.replace(",", ""))
        for token in re.findall(r"-?\d[\d,]*(?:\.\d+)?", value)
    ]


def _normalise(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


def _format_number(value: float) -> str:
    return str(int(value)) if value.is_integer() else f"{value:.12g}"


def _normalise_choice_answer(answer: str, choices: list[Any]) -> str:
    options = [str(choice).strip() for choice in choices]
    if not answer or not options or any(not option for option in options):
        return answer
    normalised_answer = _closed_normalise(answer)
    exact = [
        option for option in options if _closed_normalise(option) == normalised_answer
    ]
    if len(exact) == 1:
        return exact[0]
    label = re.fullmatch(r"(?:option\s*)?([a-d])", normalised_answer)
    if label:
        index = ord(label.group(1)) - ord("a")
        if index < len(options):
            return options[index]
    if normalised_answer.isdigit():
        index = int(normalised_answer) - 1
        if 0 <= index < len(options):
            return options[index]
    return answer
