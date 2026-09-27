from __future__ import annotations

import itertools
import re
from typing import Any

from Backend.Core.subject_contracts import SubjectValidation

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
    normalized_expression = re.sub(
        r"([A-Za-z][A-Za-z0-9_]*)\u0305",
        r"¬\1",
        expression,
    )
    tree = _BooleanParser(normalized_expression, set(variables)).parse()
    rows: list[dict[str, bool]] = []
    for values in itertools.product((False, True), repeat=len(variables)):
        environment = dict(zip(variables, values, strict=True))
        rows.append({**environment, "result": _evaluate_boolean(tree, environment)})
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


_BOOLEAN_TOKEN = re.compile(
    r"\s*(?:(AND|OR|NOT|XOR|NAND|NOR)|([A-Za-z][A-Za-z0-9_]*)|([()+·.¬⊕⊼⊽]))",
    re.IGNORECASE,
)
BooleanNode = tuple[str, object] | tuple[str, object, object]


class _BooleanParser:
    def __init__(self, expression: str, variables: set[str]) -> None:
        self.variables = variables
        self.tokens = self._tokens(expression)
        self.index = 0

    @staticmethod
    def _tokens(expression: str) -> list[str]:
        tokens: list[str] = []
        cursor = 0
        while cursor < len(expression):
            match = _BOOLEAN_TOKEN.match(expression, cursor)
            if match is None:
                raise ValueError("logic expression contains an unsupported operation")
            tokens.append(next(value for value in match.groups() if value is not None))
            cursor = match.end()
        return tokens

    def parse(self) -> BooleanNode:
        if not self.tokens:
            raise ValueError("logic expression is empty")
        result = self._or_expression()
        if self.index != len(self.tokens):
            raise ValueError("logic expression contains an unexpected token")
        return result

    def _or_expression(self) -> BooleanNode:
        node = self._xor_expression()
        while self._peek() in {"OR", "+", "NOR", "⊽"}:
            operator = self._take().upper()
            node = (operator, node, self._xor_expression())
        return node

    def _xor_expression(self) -> BooleanNode:
        node = self._and_expression()
        while self._peek() in {"XOR", "⊕"}:
            operator = self._take().upper()
            node = (operator, node, self._and_expression())
        return node

    def _and_expression(self) -> BooleanNode:
        node = self._unary_expression()
        while self._peek() in {"AND", "·", ".", "NAND", "⊼"}:
            operator = self._take().upper()
            node = (operator, node, self._unary_expression())
        return node

    def _unary_expression(self) -> BooleanNode:
        if self._peek() in {"NOT", "¬"}:
            self._take()
            return ("NOT", self._unary_expression())
        if self._peek() == "(":
            self._take()
            node = self._or_expression()
            if self._take() != ")":
                raise ValueError("logic expression has unmatched parentheses")
            return node
        name = self._take()
        if name not in self.variables:
            raise ValueError(f"undeclared truth-table variable: {name}")
        return ("VARIABLE", name)

    def _peek(self) -> str:
        return self.tokens[self.index].upper() if self.index < len(self.tokens) else ""

    def _take(self) -> str:
        if self.index >= len(self.tokens):
            raise ValueError("logic expression ended unexpectedly")
        value = self.tokens[self.index]
        self.index += 1
        return value


def _evaluate_boolean(node: BooleanNode, environment: dict[str, bool]) -> bool:
    operator = node[0]
    if operator == "VARIABLE":
        return environment[str(node[1])]
    if operator == "NOT":
        return not _evaluate_boolean(node[1], environment)  # type: ignore[arg-type]
    left = _evaluate_boolean(node[1], environment)  # type: ignore[arg-type]
    right = _evaluate_boolean(node[2], environment)  # type: ignore[arg-type,index]
    if operator in {"AND", "·", "."}:
        return left and right
    if operator in {"OR", "+"}:
        return left or right
    if operator in {"XOR", "⊕"}:
        return left != right
    if operator in {"NAND", "⊼"}:
        return not (left and right)
    if operator in {"NOR", "⊽"}:
        return not (left or right)
    raise ValueError("logic expression contains an unsupported operation")
