from __future__ import annotations

import ast
import hashlib
import json
import math
import operator
import re
from collections import Counter
from collections.abc import Sequence
from decimal import Decimal
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from Backend.Core.assessment_contracts import EvidenceRecord
from Backend.Core.assessment_objectives import objective_policy_for
from Backend.Core.assessment_quality import content_similarity
from Backend.Core.credit_policy import (
    CREDIT_POLICY_VERSION,
    CreditRule,
    collect_credit_rules,
    declared_rule_metadata_present,
)
from Backend.Core.generation_diagnostics import GenerationEvidenceError
from Backend.Core.numeric_integrity import (
    NUMERIC_INTEGRITY_VERSION,
    CheckedNumericOutput,
    CheckedTextOutput,
    NumericOutput,
    check_numeric_alternatives,
    check_published_outputs,
    display,
    numeric_result,
)
from Backend.Core.open_credit import validate_open_credit_review
from Backend.Core.subjects.accounting import (
    derive_accounting_open_response_context,
    solve_accounting_calculation,
)
from Backend.Core.subjects.computer_science_contracts import (
    solve_computer_science_contract,
)
from Backend.Core.subjects.economics_contracts import solve_economics_contract
from Backend.Core.subjects.selected_response import solve_selected_response
from Backend.Core.subjects.sql_contracts import SQLValidationResult


class SQLProgramAttemptAudit(BaseModel):
    """Private durable record of one model-presented SQL attempt."""

    model_config = ConfigDict(frozen=True)

    answer: str
    mark_points: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    validation_result: SQLValidationResult


class SolverClient(Protocol):
    def generate_json(self, prompt: str) -> dict[str, object]: ...


class SolverResponseEnvelope(BaseModel):
    """Exact raw-provider shape; semantic validation remains item-specific below."""

    model_config = ConfigDict(extra="forbid", strict=True)

    steps: list[str]
    answer: str | dict[str, str]
    mark_points: list[str] | dict[str, str]
    evidence_ids: list[str]
    alternatives: list[str]
    partial_credit_boundaries: list[str]
    follow_through_rules: list[str]


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
    credit_policy_version: str = "legacy-unverified"
    credit_rules: list[CreditRule] = Field(default_factory=list)
    advisory_issues: list[str] = Field(default_factory=list)
    open_credit_contract: dict[str, Any] = Field(default_factory=dict)
    program_validation_version: str = "legacy-unverified"
    program_validation_scope: str = "none"
    source_intent_sha256: str = ""
    program_first_failure: SQLProgramAttemptAudit | None = None


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
        *,
        correction_findings: Sequence[dict[str, Any]] | None = None,
    ) -> CanonicalSolution:
        raw_item = _as_mapping(item)
        item_id = str(
            raw_item.get("id")
            or raw_item.get("rule_id")
            or raw_item.get("number")
            or "unknown"
        )
        context = dict(raw_item.get("authoring_context") or {})
        policy = objective_policy_for(
            str(raw_item.get("subject", "")), str(context.get("objective_subject", "")),
            "computer science" if context.get("cs_input_contract") else "",
        )
        policy.validate(raw_item)
        allowed_source_ids = {source.id for source in sources}
        solver_item = _without_answer_key(raw_item)
        derived_context = derive_accounting_open_response_context(raw_item)
        if derived_context is not None:
            solver_item.setdefault("authoring_context", {})[
                "independently_derived_context"
            ] = derived_context
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
        if deterministic is None:
            deterministic = solve_computer_science_contract(raw_item)
        if deterministic is None:
            deterministic = solve_economics_contract(raw_item)
        if deterministic is None:
            deterministic = solve_selected_response(raw_item)
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
        if deterministic and isinstance(deterministic.get("answer"), dict):
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
            "In steps, solve each requested slot in turn using that slot's position and "
            "all relevant source evidence. Check that every slot has been considered before "
            "finalising either map; results may coincide only if separately justified by "
            "the item. "
            'Format example only: "answer": {"slot-id": "final value"}, '
            '"mark_points": {"slot-id": "final value"}. Use the actual supplied '
            "slot IDs. Do not put grading prose or nested objects in either mapping."
            if response_slots
            else " For multiple choice, mark_points must contain exactly one string: "
            "the same selected option as answer. Put reasoning in steps."
        )
        if deterministic is None and self.client is not None:
            correction = ""
            if correction_findings:
                if context.get("sql_answer_contract") is None:
                    raise ValueError("solver correction findings require a public SQL contract")
                correction = (
                    " This is the single permitted correction of a prior SQL response. "
                    "Correct every structured verifier finding using only the same public "
                    "schema, intent and supported syntax. Do not ask for or infer a private "
                    "worked query. SQL_VALIDATION_FINDINGS="
                    + json.dumps(list(correction_findings), ensure_ascii=False, sort_keys=True)
                )
            raw_result = self.client.generate_json(
                    "Independently solve this UK A-level assessment item. Do not "
                    "infer or reproduce a draft mark scheme. Recompute every numeric "
                    "result and cite only the supplied evidence IDs; when sources is "
                    "empty, evidence_ids must be an empty array. For multiple choice, "
                    "return the complete option text rather than its number or letter. "
                    "Return exactly one JSON object with these seven top-level fields, "
                    "and no others: steps, answer, mark_points, evidence_ids, alternatives, "
                    "partial_credit_boundaries, follow_through_rules. Every field is required; "
                    "every array must be present explicitly even when empty; do not return null. "
                    "Follow every independent_solver_instructions entry in authoring_context; "
                    "derive its requested facts solely from candidate-visible inputs and show "
                    "those derivations in steps. "
                    "When independently_derived_context is present, treat its numeric results "
                    "as authoritative code-derived facts from the public inputs; use them in "
                    "the answer and do not replace them with new model arithmetic. "
                    'For an open response the literal envelope is: {"steps":["reasoning step"],'
                    '"answer":"complete answer","mark_points":["creditable point"],'
                    '"evidence_ids":[],"alternatives":[],"partial_credit_boundaries":[],'
                    '"follow_through_rules":[]}. '
                    + response_instructions
                    + correction
                    + "\n"
                    + json.dumps(
                        {
                            "item": solver_item,
                            "sources": [source.model_dump() for source in sources],
                        },
                        ensure_ascii=False,
                    )
                )
            try:
                envelope = SolverResponseEnvelope.model_validate(raw_result, strict=True)
            except ValidationError as error:
                raise ValueError(
                    f"{item_id} returned an invalid solver response envelope"
                ) from error
            if response_slots:
                valid_shape = isinstance(envelope.answer, dict) and isinstance(
                    envelope.mark_points, dict
                )
            else:
                valid_shape = isinstance(envelope.answer, str) and isinstance(
                    envelope.mark_points, list
                )
            if not valid_shape:
                raise ValueError(
                    f"{item_id} returned an invalid solver response envelope"
                )
            result = envelope.model_dump()

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
                not _closed_slot_equal(
                    slot, answer_slots[slot], result["mark_points"][slot]
                )
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
        credit_rules, advisory_issues = collect_credit_rules(
            context, result, closed=fixed_answer, marks=int(raw_item.get("marks", 0)))
        def mandatory(field: str) -> list[str]:
            return [rule.text for rule in credit_rules if rule.kind == field and rule.origin != "model-advisory"]
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
            alternatives=mandatory("alternatives"),
            partial_credit_boundaries=mandatory("partial_credit_boundaries"),
            follow_through_rules=mandatory("follow_through_rules"),
            credit_policy_version=CREDIT_POLICY_VERSION,
            credit_rules=credit_rules,
            advisory_issues=advisory_issues,
            open_credit_contract=context.get("open_credit_contract", {}),
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
        # Private instance credit must not enter the blind model context.
        # Keep candidate input contracts and ordinary source fields (including
        # a source's own "credit" column) intact for independent derivation.
        "assessment_contract",
        "open_credit_contract",
        "open_credit_review",
        "credit_allocations",
        "credit_review_item",
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
        "alternative_permission_ids",
        "alternative_permission_version",
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


def solution_failure_evidence(
    solution: CanonicalSolution, issues: Sequence[ReconciliationIssue]
) -> dict[str, Any]:
    """Retain finite route evidence, but fingerprint open text instead of logging it."""
    safe_slots = {}
    for slot, value in solution.answer_slots.items():
        is_route = slot == "route-in-order" and re.fullmatch(
            r"[A-Z](?:\s*(?:,|->|→|-)\s*[A-Z]){1,25}", value
        )
        is_edge_count = slot == "edges" and re.fullmatch(r"\d{1,3}", value)
        is_tree_parent = re.fullmatch(r"node-\d{1,3}-parent", slot) and (
            re.fullmatch(r"\d{1,3}", value) or value.casefold() in {"none", "no parent", "null"}
        )
        is_tree_side = re.fullmatch(r"node-\d{1,3}-side", slot) and value.casefold() in {
            "left", "right", "root", "none", "neither", "null", "n/a"
        }
        if is_route or is_edge_count or is_tree_parent or is_tree_side:
            safe_slots[slot] = value
    return {
        "kind": "solution_reconciliation",
        "item_id": solution.item_id,
        "answer_sha256": hashlib.sha256(solution.answer.encode()).hexdigest(),
        "answer_slots": safe_slots,
        "issues": [
            {
                "field": issue.field,
                "detail_sha256": hashlib.sha256(issue.message.encode()).hexdigest(),
            }
            for issue in issues
        ],
    }


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
        raise GenerationEvidenceError(
            f"{solution.item_id} independent answer disagrees with the keyed option",
            details=solution_failure_evidence(
                solution,
                [ReconciliationIssue(
                    field="choice", message="independent answer disagrees with keyed option"
                )],
            ),
        )
    if expected_choice is not None:
        scheme = {
            **scheme,
            "mark_scheme": [*scheme.get("mark_scheme", []), expected_choice],
        }
    result = reconcile_solution(solution, scheme)
    if not result.passed:
        raise GenerationEvidenceError(
            f"{solution.item_id} failed independent solution reconciliation: "
            + "; ".join(issue.message for issue in result.issues),
            details=solution_failure_evidence(solution, result.issues),
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

    if solution.open_credit_contract:
        try:
            review_item = raw.get("credit_review_item", {})
            marking = review_item.get("marking", {})
            if (review_item.get("authoring_context", {}).get("open_credit_contract") != solution.open_credit_contract
                    or raw.get("mark_scheme") != [*marking.get("points", []), *marking.get("levels", [])]
                    or raw.get("alternatives", []) != marking.get("accept", [])
                    or raw.get("marks") != review_item.get("marks")):
                raise ValueError("semantic credit review does not match the actual scheme")
            validate_open_credit_review(review_item, raw.get("open_credit_review"), solution=solution)
        except (ValueError, TypeError, KeyError) as error:
            issues.append(ReconciliationIssue(field="open_credit_review", message=str(error)))

    requires_free_entry_numeric_contract = raw.get("kind") != "multiple_choice" and (
        _requires_numeric_contract(raw) or bool(solution.numeric_results)
    )
    if requires_free_entry_numeric_contract and not solution.response_slots:
        issues.append(
            ReconciliationIssue(
                field="answer",
                message="closed numeric response is missing its output contract",
            )
        )

    if solution.numeric_checks or solution.text_checks:
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
        checked_outputs = [*solution.numeric_checks, *solution.text_checks]
        alternative_groups = [
            (checked_outputs, raw.get("alternatives", [])),
            (checked_outputs, raw.get("allow", [])),
            (checked_outputs, [rule.text for rule in solution.credit_rules
                               if rule.kind == "alternatives" and rule.content_kind == "answer"
                               and rule.origin != "model-advisory"]
             if solution.credit_policy_version == CREDIT_POLICY_VERSION else solution.alternatives),
        ]
        for point in points:
            if not isinstance(point, dict):
                continue
            associated = [
                check
                for check in checked_outputs
                if re.search(
                    check.scheme_pattern,
                    str(point.get("text", "")),
                    re.IGNORECASE | re.MULTILINE,
                )
            ]
            for field in ("alternatives", "allow"):
                alternatives = point.get(field, [])
                if associated or solution.text_checks or any(
                    re.search(r"\d|[£%]", value) for value in alternatives
                ):
                    alternative_groups.append((associated, alternatives))
        for checks, alternatives in alternative_groups:
            issues.extend(
                ReconciliationIssue(field="alternatives", message=message)
                for message in check_numeric_alternatives(checks, alternatives)
            )
        texts = [[_rubric_text(point) for point in points]]
        if isinstance(raw.get("mark_scheme"), list) and raw.get(
            "structured_mark_scheme"
        ):
            texts.append(raw["mark_scheme"])
        for published in texts:
            issues.extend(
                ReconciliationIssue(field="answer", message=message)
                for message in check_published_outputs(
                    solution.numeric_checks, published
                )
            )
            for check in solution.text_checks:
                selected = [statement for statement in published if re.search(check.scheme_pattern, statement, re.MULTILINE)]
                matches = re.findall(check.scheme_pattern, "\n".join(published), re.MULTILINE)
                complete = not check.whole_statement or all(
                    re.fullmatch(check.scheme_pattern, statement.strip()) for statement in selected
                )
                if (
                    not matches
                    or not complete
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
            if solution.numeric_checks or solution.text_checks
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
                    or not any(
                        _closed_slot_equal(slot, solution.answer_slots[slot], value)
                        for value in alternatives
                    )
                ):
                    issues.append(
                        ReconciliationIssue(
                            field="answer",
                            message=f"closed response disagrees at slot {slot}",
                        )
                    )

            if not solution.numeric_checks and not solution.text_checks:
                concrete = [rule.text for rule in solution.credit_rules
                            if rule.kind == "alternatives" and rule.content_kind == "answer"
                            and rule.origin != "model-advisory"] if solution.credit_policy_version == CREDIT_POLICY_VERSION else solution.alternatives
                for alternative in concrete:
                    slot, value = (solution.response_slots[0], alternative) if len(solution.response_slots) == 1 else ("", alternative)
                    if ":" in alternative:
                        slot, value = (piece.strip() for piece in alternative.split(":", 1))
                    allowed = accepted.get(slot, [])
                    if not isinstance(allowed, list) or not any(
                        _closed_slot_equal(slot, value, str(candidate))
                        for candidate in allowed
                    ):
                        issues.append(ReconciliationIssue(field="alternatives", message=f"unsupported or incorrect closed alternative: {alternative}"))

    expected_numbers = [] if solution.response_slots else _numbers(solution.answer)
    if expected_numbers and solution.mark_points_exhaustive and not solution.is_choice:
        issues.append(
            ReconciliationIssue(
                field="answer",
                message="closed numeric response requires an exhaustive role/value/unit contract",
            )
        )
    elif (
        not solution.open_credit_contract
        and not solution.response_slots
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

    for rule in solution.credit_rules:
        if rule.origin == "source-declared" and not declared_rule_metadata_present(rule, raw, points):
            issues.append(ReconciliationIssue(field=rule.kind, message=f"scheme omits or changes declared score/cap/dependencies: {rule.raw}"))

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
        and (dict(allocation) if total_marks else raw.get("assessment_objectives", {})) != solution.assessment_objectives
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


def _route_vertices(value: str) -> tuple[str, ...] | None:
    """Parse route notation without discarding vertex identity, order or count."""
    value = value.strip().rstrip(".;").rstrip()
    vertices: object
    if value.startswith("[") and value.endswith("]"):
        try:
            vertices = json.loads(value)
        except json.JSONDecodeError:
            vertices = re.split(r"\s*(?:,|->|→|-)\s*", value[1:-1].strip())
    else:
        vertices = re.split(r"\s*(?:,|->|→|-)\s*", value)
    if not isinstance(vertices, list) or not vertices or any(
        not isinstance(vertex, str) or not re.fullmatch(r"[A-Za-z0-9_]+", vertex)
        for vertex in vertices
    ):
        return None
    return tuple(vertices)


def _closed_slot_equal(slot: str, left: str, right: str) -> bool:
    if slot == "route-in-order":
        vertices = _route_vertices(left)
        return vertices is not None and vertices == _route_vertices(right)
    if re.fullmatch(r"node--?\d+-side", slot):
        # The root is neither a left nor a right child. Both encodings describe
        # that same absence of a parent edge; other child sides stay exact.
        root_sides = {"root", "none", "no side", "neither", "n/a"}
        if _closed_normalise(left) in root_sides and _closed_normalise(right) in root_sides:
            return True
    return _closed_normalise(left) == _closed_normalise(right)


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
