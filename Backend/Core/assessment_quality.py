from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable, Mapping

if TYPE_CHECKING:
    from Backend.Core.assessment_contracts import AssessmentContract


NUMBER_PATTERN = re.compile(
    r"(?<![\w.])[£$€]?[+-]?\d+(?:[,.]\d+)*(?:\s?(?:%|000|m|bn))?",
    flags=re.IGNORECASE,
)
WORD_PATTERN = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")


def normalise_item_text(value: str, *, abstract_numbers: bool = True) -> str:
    """Return a stable comparison form without conflating visible output text."""

    text = unicodedata.normalize("NFKC", value).casefold()
    if abstract_numbers:
        text = NUMBER_PATTERN.sub(" <number> ", text)
    return " ".join(WORD_PATTERN.findall(text))


def numeric_tokens(value: str) -> tuple[str, ...]:
    """Extract quantities exactly enough to catch broken data/source rewrites."""

    return tuple(
        " ".join(match.group(0).casefold().split())
        for match in NUMBER_PATTERN.finditer(value)
    )


def validate_candidate_contract(
    original: str,
    candidate: str,
    contract: AssessmentContract,
    generated_values: Mapping[str, float] | None = None,
) -> None:
    """Validate candidate quantities against their declared semantic roles."""

    original_precision = _precision_instructions(original)
    candidate_precision = _precision_instructions(candidate)
    if original_precision != candidate_precision:
        raise ValueError(
            f"{contract.item_id} changed the required precision instruction"
        )

    expected_values = [
        value
        for value in contract.numeric_values
        if value.role.value == "assessment_data"
    ]
    expected = Counter(_normalise_quantity(value.text) for value in expected_values)
    actual_tokens = list(numeric_tokens(candidate))

    ignored = _ignored_candidate_quantities(candidate)
    ignored.extend(_precision_digit_tokens(candidate))
    _subtract_tokens(actual_tokens, ignored)

    supplied = generated_values or {}
    declared_fields = {field.name: field for field in contract.generated_numeric_fields}
    unknown_fields = set(supplied) - set(declared_fields)
    if unknown_fields:
        raise ValueError(
            f"{contract.item_id} supplied undeclared generated numeric fields: "
            f"{sorted(unknown_fields)}"
        )
    for name, value in supplied.items():
        declared_fields[name].validate_value(float(value))
        _subtract_tokens(actual_tokens, _value_tokens(value))

    actual = Counter(_normalise_quantity(token) for token in actual_tokens)
    numeric_values_match = (
        not (expected - actual)
        if contract.allow_additional_numeric_values
        else actual == expected
    )
    if not numeric_values_match:
        raise ValueError(
            f"{contract.item_id} changed immutable numeric data: "
            f"expected {expected}, got {actual}"
        )

    ordered = [
        _normalise_quantity(value.text)
        for value in expected_values
        if value.ordered
    ]
    if ordered and not _is_subsequence(
        ordered,
        [_normalise_quantity(token) for token in actual_tokens],
    ):
        raise ValueError(
            f"{contract.item_id} changed ordered immutable numeric data"
        )

def validate_economics_causal_direction(value: str) -> None:
    """Reject common exchange-rate reversals before model review."""

    text = " ".join(value.casefold().split())
    import_cost = r"(?:import (?:costs?|prices?)|(?:costs?|prices?) of imports)"
    higher = r"(?:raises?|increases?|higher|more expensive)"
    lower = r"(?:lowers?|reduces?|decreases?|lower|cheaper)"
    reversed_relationships = (
        rf"\bappreciat\w*\b.{{0,100}}{higher}.{{0,50}}{import_cost}",
        rf"\bdepreciat\w*\b.{{0,100}}{lower}.{{0,50}}{import_cost}",
    )
    if any(re.search(pattern, text) for pattern in reversed_relationships):
        raise ValueError("economics item has a reversed exchange-rate direction")


def _normalise_quantity(value: str) -> str:
    return " ".join(value.casefold().split())


def _ignored_candidate_quantities(value: str) -> list[str]:
    ignored: list[str] = []
    patterns = (
        r"(?m)^\s*(\d{1,3})(?=\s+\S)",
        r"\[\s*(\d+)\s+marks?\s*\]",
        r"\b(?:question|extract|figure|table)\s+(\d+)\b",
        r"\bline\s+(\d+)\b",
    )
    for pattern in patterns:
        ignored.extend(
            match.group(1)
            for match in re.finditer(pattern, value, flags=re.IGNORECASE)
        )
    return ignored


def _precision_instructions(value: str) -> tuple[tuple[int, str], ...]:
    words = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
    }
    pattern = re.compile(
        r"\b(one|two|three|four|five|\d+)\s+"
        r"(decimal\s+places?|significant\s+figures?)\b",
        flags=re.IGNORECASE,
    )
    return tuple(
        (
            (
                words[match.group(1).casefold()]
                if match.group(1).casefold() in words
                else int(match.group(1))
            ),
            "decimal" if match.group(2).casefold().startswith("decimal") else "significant",
        )
        for match in pattern.finditer(value)
    )


def _precision_digit_tokens(value: str) -> list[str]:
    return [
        match.group(1)
        for match in re.finditer(
            r"\b(\d+)\s+(?:decimal\s+places?|significant\s+figures?)\b",
            value,
            flags=re.IGNORECASE,
        )
    ]


def _value_tokens(value: float) -> list[str]:
    return [format(float(value), "g")]


def _subtract_tokens(tokens: list[str], values: Iterable[str]) -> None:
    for value in values:
        normalised = _normalise_quantity(value)
        for index, token in enumerate(tokens):
            if _normalise_quantity(token) == normalised:
                tokens.pop(index)
                break


def _is_subsequence(expected: list[str], actual: list[str]) -> bool:
    iterator = iter(actual)
    return all(any(candidate == value for candidate in iterator) for value in expected)


def item_fingerprint(value: str) -> str:
    normalised = normalise_item_text(value)
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def content_similarity(left: str, right: str, *, width: int = 3) -> float:
    """Weighted token-shingle Jaccard similarity in the closed interval 0...1."""

    left_counter = _shingles(normalise_item_text(left), width=width)
    right_counter = _shingles(normalise_item_text(right), width=width)
    if not left_counter and not right_counter:
        return 1.0
    if not left_counter or not right_counter:
        return 0.0
    intersection = sum((left_counter & right_counter).values())
    union = sum((left_counter | right_counter).values())
    return intersection / union if union else 0.0


def assert_distinct_items(
    items: Iterable[dict[str, Any]],
    *,
    threshold: float = 0.84,
    context: str = "paper",
) -> None:
    materialised = list(items)
    for index, item in enumerate(materialised):
        prompt = str(item.get("prompt", "")).strip()
        if not prompt:
            raise ValueError(f"{context} item {item.get('id', index)} has no prompt")
        for previous in materialised[:index]:
            score = content_similarity(prompt, str(previous.get("prompt", "")))
            if score >= threshold:
                raise ValueError(
                    f"{context} items {previous.get('id')} and {item.get('id')} "
                    f"are too similar ({score:.3f})"
                )


def validate_package_novelty(
    package_path: Path,
    *,
    history_root: Path,
    threshold: float = 0.84,
) -> dict[str, Any]:
    """Compare a completed assessment package with earlier published packages."""

    current = _load_package(package_path)
    current_items = _items(current)
    assert_distinct_items(current_items, threshold=threshold)

    comparisons = 0
    nearest: dict[str, Any] | None = None
    for historic_path in sorted(history_root.glob("*-assessment.json")):
        if (
            historic_path.resolve() == package_path.resolve()
            or historic_path.name == package_path.name
        ):
            continue
        try:
            historic = _load_package(historic_path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        for item in current_items:
            for historic_item in _items(historic):
                if (
                    item.get("subject") != historic_item.get("subject")
                    or item.get("paper") != historic_item.get("paper")
                ):
                    continue
                comparisons += 1
                score = content_similarity(
                    str(item.get("prompt", "")),
                    str(historic_item.get("prompt", "")),
                )
                if nearest is None or score > float(nearest["similarity"]):
                    nearest = {
                        "similarity": round(score, 4),
                        "current_item": item.get("id"),
                        "historic_item": historic_item.get("id"),
                        "historic_package": historic_path.name,
                    }
                if score >= threshold:
                    raise ValueError(
                        f"generated item {item.get('id')} is too similar to "
                        f"{historic_path.name}:{historic_item.get('id')} "
                        f"({score:.3f}); choose a new seed or regenerate"
                    )
    return {
        "algorithm": "weighted-token-shingle-jaccard-v1",
        "threshold": threshold,
        "historic_comparisons": comparisons,
        "nearest_match": nearest,
        "passed": True,
    }


def _shingles(value: str, *, width: int) -> Counter[tuple[str, ...]]:
    words = value.split()
    if not words:
        return Counter()
    actual_width = min(width, len(words))
    return Counter(
        tuple(words[index : index + actual_width])
        for index in range(len(words) - actual_width + 1)
    )


def _load_package(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise ValueError(f"unsupported assessment package: {path}")
    return raw


def _items(package: dict[str, Any]) -> list[dict[str, Any]]:
    raw_items = package.get("items", [])
    if not isinstance(raw_items, list):
        raise ValueError("assessment package items must be a list")
    return [item for item in raw_items if isinstance(item, dict)]
