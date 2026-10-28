"""Small calibration operations with explicit, versioned content identities."""

from __future__ import annotations

import hashlib
import json
import statistics
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any, TypedDict

CALIBRATION_CONTENT_POLICY = "public-candidate-content-v2"


class IntegerBand(TypedDict):
    minimum: int
    median: int | float
    maximum: int


class SequenceFrequency(TypedDict):
    sequence: list[int]
    documents: int


def integer_band(values: Sequence[int]) -> IntegerBand:
    return {
        "minimum": min(values),
        "median": statistics.median(values),
        "maximum": max(values),
    }


def mark_sequence_inventory(
    sequences: Iterable[Sequence[int]],
) -> list[SequenceFrequency]:
    counts = Counter(tuple(sequence) for sequence in sequences)
    return [
        {"sequence": list(sequence), "documents": count}
        for sequence, count in sorted(counts.items())
    ]


def ordered_document_fingerprint(paths: Iterable[Path]) -> str:
    # Preserve the legacy byte contract: basename then raw content digest, in
    # caller order. Sorting or adding directory names changes retained evidence.
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode())
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def render_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


# Scoped source containers supply candidate case tables. This is not a full
# renderer projection. Derived working and solved ledger placements are excluded.
_PUBLIC_INPUT_FIELDS = frozenset(
    {
        "candidate_source",
        "source_data",
        "opening_balances",
        "transactions_at_start_of_year",
        "depreciation_policy",
        "adjustment_source_data",
        "adjustment_policy",
        "referenced_question_data",
        "cs_input_contract",
    }
)


def public_candidate_content(
    paper: Any, *, source_only: bool = False
) -> dict[str, Any]:
    # Import lazily: standalone tools must still support --help before generator
    # roots have been added to sys.path by their generation entry points.
    from Backend.Core.answer_projection import (
        without_private_answer_keys as _without_answer_key,
    )
    from Backend.Core.shared_source_scope import (
        owns_shared_source,
        uses_shared_option_source,
    )

    if hasattr(paper, "model_dump"):
        paper = paper.model_dump(mode="json")
    if not isinstance(paper, Mapping):
        raise TypeError("calibration candidate must be a paper mapping")
    sections = []
    for section in paper["sections"]:
        options = []
        for option in section["options"]:
            parts = []
            for question in option["questions"]:
                context = question.get("authoring_context") or {}
                owned = _without_answer_key(
                    {
                        key: context[key]
                        for key in _PUBLIC_INPUT_FIELDS
                        if key in context
                    }
                )
                selected = context.get("selected_response_contract")
                if isinstance(selected, Mapping):
                    # Renderers use these operands for printed tables/geometry;
                    # operation/format policy and solved-choice metadata do not
                    # themselves establish a new public input.
                    visible = {
                        key: selected[key]
                        for key in ("inputs", "rows")
                        if selected.get(key)
                    }
                    if visible:
                        owned["selected_response_inputs"] = _without_answer_key(visible)
                shared = {}
                if not owns_shared_source(question) and uses_shared_option_source(
                    question, option
                ):
                    shared = {
                        key: option[key]
                        for key in (
                            "title",
                            "stimulus",
                            "chart_title",
                            "chart_labels",
                            "chart_values",
                        )
                        if key in option
                    }
                part: dict[str, Any] = {"owned_source": owned, "shared_source": shared}
                if not source_only:
                    part.update(
                        {
                            key: question.get(key)
                            for key in (
                                "number",
                                "prompt",
                                "marks",
                                "choices",
                                "response_slots",
                            )
                        }
                    )
                elif question.get("kind") == "multiple_choice" or not (owned or shared):
                    # A standalone stem is itself the candidate's public source.
                    part["stem"] = question["prompt"]
                parts.append(part)
            options.append({"parts": parts})
        sections.append({"options": options})
    return {"policy": CALIBRATION_CONTENT_POLICY, "sections": sections}


def paper_content_fingerprint(paper: Any, *, source_only: bool = False) -> str:
    content = public_candidate_content(paper, source_only=source_only)
    return hashlib.sha256(
        json.dumps(
            content, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode()
    ).hexdigest()
