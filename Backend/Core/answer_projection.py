"""Remove known private answer keys from nested dictionary/list values.

This is a key filter, not a whitelist of everything printed for a candidate.
"""

from __future__ import annotations

from typing import Any


def without_private_answer_keys(value: Any) -> Any:
    hidden = {
        # Private instance credit must not enter the blind model context.
        # Keep candidate input contracts and ordinary source fields (including
        # a source's own "credit" column) intact for independent derivation.
        "assessment_contract",
        "open_credit_contract",
        "open_credit_review",
        "credit_allocations",
        "credit_review_item",
        "accounting_source_content",
        "accounting_marking_policy",
        "grouped_level_policy",
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
            key: without_private_answer_keys(child)
            for key, child in value.items()
            if key not in hidden
        }
    if isinstance(value, list):
        return [without_private_answer_keys(child) for child in value]
    return value
