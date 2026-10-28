"""Build blind solver prompt text and its public output-shape contract."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from Backend.Core.assessment_contracts import EvidenceRecord
from Backend.Core.generation_requests import OutputContract


def build_solver_prompt(
    solver_item: dict[str, Any],
    sources: Sequence[EvidenceRecord],
    response_slots: list[str],
    *,
    correction_findings: Sequence[dict[str, Any]] | None = None,
    sql_contract_present: bool = False,
) -> str:
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
    correction = ""
    if correction_findings:
        if not sql_contract_present:
            raise ValueError("solver correction findings require a public SQL contract")
        correction = (
            " This is the single permitted correction of a prior SQL response. "
            "Correct every structured verifier finding using only the same public "
            "schema, intent and supported syntax. Do not ask for or infer a private "
            "worked query. SQL_VALIDATION_FINDINGS="
            + json.dumps(list(correction_findings), ensure_ascii=False, sort_keys=True)
        )
    return (
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


def solver_output_contract(
    solver_item: dict[str, Any], response_slots: list[str]
) -> OutputContract:
    return OutputContract(
        "solver",
        response_slots=tuple(response_slots),
        choices=tuple(solver_item["choices"])
        if isinstance(solver_item.get("choices"), list)
        and all(
            isinstance(choice, str) and choice.strip()
            for choice in solver_item["choices"]
        )
        else (),
        kind=solver_item.get("kind"),
        marks=solver_item.get("marks"),
    )
