from __future__ import annotations

import ast
import itertools
import re
from typing import Any

from Backend.Core.subject_plugins import SubjectValidation

_PSEUDOCODE_TOKEN = re.compile(
    r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"|<=|>=|<>|!=|==|←|[A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?|\S"
)
_PRACTICAL_LANGUAGES = {"java", "python", "visual basic"}


def normalise_pseudocode(value: str) -> tuple[str, ...]:
    tokens = _PSEUDOCODE_TOKEN.findall(value.replace("←", "="))
    return tuple(token.casefold() for token in tokens)


def pseudocode_equivalent(left: str, right: str) -> bool:
    return normalise_pseudocode(left) == normalise_pseudocode(right)


def truth_table(
    expression: str,
    *,
    variables: tuple[str, ...],
) -> tuple[dict[str, bool], ...]:
    if not variables or len(set(variables)) != len(variables):
        raise ValueError("truth table variables must be unique and non-empty")
    if any(not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", value) for value in variables):
        raise ValueError("truth table variable has an invalid name")
    normalized = re.sub(r"\bAND\b", "and", expression, flags=re.IGNORECASE)
    normalized = re.sub(r"\bOR\b", "or", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bNOT\b", "not", normalized, flags=re.IGNORECASE)
    tree = ast.parse(normalized, mode="eval")
    _validate_boolean_tree(tree, set(variables))
    rows: list[dict[str, bool]] = []
    for values in itertools.product((False, True), repeat=len(variables)):
        environment = dict(zip(variables, values, strict=True))
        rows.append({**environment, "result": _evaluate_boolean(tree.body, environment)})
    return tuple(rows)


class ComputerSciencePlugin:
    id = "computer-science"

    def validate_item(self, item: Any) -> SubjectValidation:
        if not isinstance(item, dict):
            return SubjectValidation(False, ("item must be an object",))
        diagnostics: list[str] = []
        if not str(item.get("question", "")).strip():
            diagnostics.append("question text is required")
        marks = item.get("marks")
        if not isinstance(marks, int) or isinstance(marks, bool) or marks <= 0:
            diagnostics.append("marks must be a positive integer")
        if not str(item.get("answer", "")).strip():
            diagnostics.append("a canonical answer is required")
        if item.get("item_kind") == "practical-programming":
            language = str(item.get("language", "")).strip().casefold()
            if language not in _PRACTICAL_LANGUAGES:
                diagnostics.append("practical language must be Java, Python, or Visual Basic")
            evidence = item.get("test_evidence")
            if not isinstance(evidence, list) or len(evidence) < 3:
                diagnostics.append("practical items require normal, boundary, and invalid test evidence")
        if item.get("item_kind") == "trace-table" and not item.get("trace_states"):
            diagnostics.append("trace-table items require recomputed states")
        if item.get("answer_kind") == "pseudocode" and not normalise_pseudocode(
            str(item.get("answer", ""))
        ):
            diagnostics.append("pseudocode answer is empty")
        return SubjectValidation(not diagnostics, tuple(diagnostics))

    def solve(self, item: Any) -> Any:
        validation = self.validate_item(item)
        if not validation.passed:
            raise ValueError("; ".join(validation.diagnostics))
        if item.get("answer_kind") == "logic-expression":
            return truth_table(
                str(item["answer"]),
                variables=tuple(str(value) for value in item.get("variables", ())),
            )
        return item["answer"]

    def render_visual(self, specification: Any) -> Any:
        if not isinstance(specification, dict) or specification.get("kind") not in {
            "data-structure",
            "flowchart",
            "logic-circuit",
            "program-listing",
            "trace-table",
        }:
            raise ValueError("unsupported computer-science visual kind")
        return specification

    def validate_scheme(self, item: Any, scheme: Any) -> SubjectValidation:
        if not isinstance(scheme, dict) or not scheme.get("mark_points"):
            return SubjectValidation(False, ("mark scheme requires mark points",))
        alternatives = scheme.get("accepted_alternatives", [])
        if item.get("answer_kind") == "pseudocode" and not isinstance(alternatives, list):
            return SubjectValidation(False, ("pseudocode alternatives must be a list",))
        return SubjectValidation(True)

    def calibration_features(self, item: Any) -> dict[str, float | str]:
        payload = item if isinstance(item, dict) else {}
        return {
            "subject": self.id,
            "marks": float(payload.get("marks", 0)),
            "topic": str(payload.get("topic", "unknown")),
            "answer_kind": str(payload.get("answer_kind", "text")),
        }


def _validate_boolean_tree(tree: ast.AST, variables: set[str]) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id not in variables:
            raise ValueError(f"undeclared truth-table variable: {node.id}")
        if not isinstance(
            node,
            (
                ast.Expression,
                ast.BoolOp,
                ast.UnaryOp,
                ast.Name,
                ast.Load,
                ast.And,
                ast.Or,
                ast.Not,
            ),
        ):
            raise ValueError("logic expression contains an unsupported operation")


def _evaluate_boolean(node: ast.AST, environment: dict[str, bool]) -> bool:
    if isinstance(node, ast.Name):
        return environment[node.id]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return not _evaluate_boolean(node.operand, environment)
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
        return all(_evaluate_boolean(value, environment) for value in node.values)
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
        return any(_evaluate_boolean(value, environment) for value in node.values)
    raise ValueError("logic expression contains an unsupported operation")
