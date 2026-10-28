# Source-scope rules shared by item review and assessment export.

from __future__ import annotations

import re
from typing import Any

from Backend.Core.assessment_quality import numeric_tokens

_OWNED_SOURCE_KEYS = frozenset(
    {
        "candidate_source",
        "referenced_question_data",
        "source_data",
        "numeric_input_contract",
        "selected_response_contract",
        "cs_input_contract",
        "sql_answer_contract",
        "calculation_variables",
        "opening_balances",
        "transactions_at_start_of_year",
        "adjustment_source_data",
    }
)

_OPTION_SOURCE_CUE = re.compile(
    r"\b(?:appendix|appendices|cases?|charts?|extracts?|figures?|sources?|tables?)"
    r"\s+(?:\d+[a-z]?|(?-i:[A-Z]))\b"
    r"|\b(?:(?:the|this|that|these|following|provided|supplied)\s+"
    r"|(?:use|using|from|according to|based on)\s+(?:(?:the|this|that)\s+)?)"
    r"(?:appendix|appendices|cases?|charts?|data|evidence|extracts?|figures?|information|sources?|tables?)\b"
    r"(?!\s+(?:structures?|types?|protection|security|codes?|documents?|technology|of\s+(?:finance|funding|income))\b)"
    r"|\b(?:charts?|data|evidence|extracts?|figures?|information|sources?|tables?)"
    r"\s+(?:above|below|provided|supplied|shown)\b",
    flags=re.IGNORECASE,
)


def owns_shared_source(question: dict[str, Any]) -> bool:
    return bool(
        _OWNED_SOURCE_KEYS.intersection(question.get("authoring_context") or {})
    )


# Specific material cues refer to extracts; topic nouns alone do not.
def uses_shared_option_source(question: dict[str, Any], option: dict[str, Any]) -> bool:
    if question.get("source_references"):
        return True
    prompt = str(question.get("prompt", ""))
    if _OPTION_SOURCE_CUE.search(prompt):
        return True
    return (
        question.get("kind") != "multiple_choice"
        and not numeric_tokens(prompt)
        and str(option.get("title", "")).casefold() in prompt.casefold()
    )


def shared_source_requires_context(
    question: dict[str, Any], option: dict[str, Any]
) -> bool:
    context = question.get("authoring_context") or {}
    explicit = question.get("contract")
    contract = explicit if explicit is not None else context.get("assessment_contract")
    evidence = contract.get("evidence", []) if isinstance(contract, dict) else []
    return bool(
        evidence
        or owns_shared_source(question)
        or uses_shared_option_source(question, option)
    )
