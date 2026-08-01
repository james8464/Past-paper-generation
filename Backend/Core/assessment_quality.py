from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


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
        if historic_path.resolve() == package_path.resolve():
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
