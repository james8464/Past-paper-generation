"""AQA CS source-coupled review identity, shared by authoring/resume/export.

This is content-integrity evidence, not a cryptographic attestation of model work.
The projection excludes only review metadata and separately checked difficulty.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

from Backend.Core.assessment_quality import numeric_tokens
from Backend.Core.candidate_identity import (
    DifficultyCandidateProjection,
    difficulty_candidate_projection,
)
from Backend.Core.credit_policy import CREDIT_POLICY_VERSION
from Backend.Core.model_review import ReviewResult
from Backend.Core.open_credit import (
    CPU_POINTS,
    validate_open_credit_contract,
    validate_open_credit_review,
)
from Backend.Core.subjects.sql_contracts import (
    SQL_VALIDATION_VERSION,
    SQLSourceContract,
    render_sql_intent_prompt,
    selected_sql_answer_contract,
    sql_source_intent_sha256,
)

REVIEW_FIELDS = {"provenance", "content_review", "reviewed_content_sha256", "reviewed_blueprint_sha256"}


def authoring_route(question: dict[str, Any]) -> str:
    if question.get("stimulus") is not None or question.get("style_id") in {"adapt_program", "extend_program"}:
        return "reviewed-fixed"
    text = " ".join([question.get("stem", ""), *(part["prompt"] for part in question["parts"])])
    return "scenario-only" if len(question["parts"]) >= 3 and numeric_tokens(text) else "authored"


def question_content_sha256(question: dict[str, Any]) -> str:
    content = deepcopy(question)
    for field in REVIEW_FIELDS:
        content.pop(field, None)
    for part in content["parts"]:
        part.pop("difficulty_evidence", None)
        part.pop("open_credit_review", None)
    sql_version = (
        SQL_VALIDATION_VERSION
        if isinstance((content.get("stimulus") or {}).get("sql_contract"), dict)
        else "none"
    )
    return hashlib.sha256(json.dumps({"credit_policy": CREDIT_POLICY_VERSION, "sql_validation": sql_version, "content": content}, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def aqa_cs_difficulty_candidate(
    question: dict[str, Any],
    part: dict[str, Any],
) -> DifficultyCandidateProjection:
    """Bind one AQA part review to the complete evidence-free parent question."""

    public_part = deepcopy(part)
    public_part.pop("open_credit_contract", None)
    public_part.pop("open_credit_review", None)
    marking = public_part.get("marking")
    if isinstance(marking, dict):
        marking.pop("credit_allocations", None)
    public_question = deepcopy(question)
    return difficulty_candidate_projection(
        route="aqa-computer-science",
        review_content={
            "stem": public_question.get("stem", ""),
            "stimulus": public_question.get("stimulus"),
            "part": public_part,
        },
        identity_content={
            "question_content_sha256": question_content_sha256(public_question),
            "part_label": str(part.get("label", "")),
            "question": public_question,
        },
    )


def aqa_cs_solver_item(question: dict[str, Any], part: dict[str, Any], stimulus: dict[str, Any]) -> dict[str, Any]:
    """One adapter/reuse projection; caller supplies candidate-visible figure data.

    The scoped CPU contract has no figure. Its saved review is rebuilt from the
    same projection here; H can reuse this instead of inventing another identity.
    Private marking remains available for reconciliation, removed by the solver.
    """
    authoring_context: dict[str, Any] = {
        "open_credit_contract": part.get("open_credit_contract", {}),
        "expected_answer_form": "numeric" if part["prompt"].split(maxsplit=1)[0].casefold() in {"calculate", "determine"} else "constructed_response",
    }
    intent_id = str(part.get("sql_intent_id", ""))
    if intent_id:
        raw_contract = stimulus.get("sql_contract")
        try:
            contract = SQLSourceContract.model_validate(raw_contract, strict=True)
        except ValueError as error:
            raise ValueError("public SQL contract is invalid or unsupported") from error
        try:
            intent = contract.intents[intent_id]
        except KeyError as error:
            raise ValueError("SQL part refers to an unknown public intent") from error
        try:
            expected_prompt = render_sql_intent_prompt(intent)
        except ValueError as error:
            raise ValueError("public SQL intent cannot be rendered as the candidate prompt") from error
        if part.get("prompt") != expected_prompt:
            raise ValueError("SQL part prompt differs from its public SQL intent")
        if stimulus.get("source_id") != contract.source_id:
            raise ValueError("SQL stimulus source identity differs from its public contract")
        authoring_context.update({
            "sql_answer_contract": selected_sql_answer_contract(contract, intent_id),
            "sql_source_intent_sha256": sql_source_intent_sha256(contract, intent_id),
        })
    return {**part, "subject": "AQA Computer Science", "id": f"question-{question['number']}-{part['label']}",
            "context": question["stem"], "stimulus": stimulus,
            "kind": "multiple_choice" if part.get("options") else question["style_id"],
            "choices": [option["text"] for option in part.get("options", [])],
            "response_slots": ["choice"] if part.get("options") else part.get("response_slots", []),
            "authoring_context": authoring_context}


def reviewed_question_metadata(original: dict[str, Any], candidate: dict[str, Any], review: ReviewResult) -> dict[str, Any]:
    return {
        "provenance": "reviewed-fixed" if authoring_route(original) == "reviewed-fixed" else "ai-authored",
        "content_review": review.model_dump(mode="json"),
        "reviewed_content_sha256": question_content_sha256(candidate),
        "reviewed_blueprint_sha256": question_content_sha256(original),
    }


def validate_question_review(question: dict[str, Any], original: dict[str, Any] | None = None, *, required: bool = False) -> None:
    provenance = question.get("provenance", "built-in")
    if provenance == "built-in" and not required:
        if any(question.get(field) for field in REVIEW_FIELDS - {"provenance"}):
            raise ValueError("unreviewed question has contradictory review metadata")
        return
    expected = "reviewed-fixed" if authoring_route(original or question) == "reviewed-fixed" else "ai-authored"
    if provenance != expected:
        raise ValueError("question provenance disagrees with its source authoring route")
    review = ReviewResult.model_validate(question.get("content_review", {}))
    if not review.approved or review.issues:
        raise ValueError("question has no approved content review")
    digest = question_content_sha256(question)
    blueprint_digest = question.get("reviewed_blueprint_sha256")
    if question.get("reviewed_content_sha256") != digest or not isinstance(blueprint_digest, str) or len(blueprint_digest) != 64:
        raise ValueError("question content review is stale")
    if expected == "reviewed-fixed" and blueprint_digest != digest:
        raise ValueError("immutable question differs from its reviewed source blueprint")
    if original is not None and blueprint_digest != question_content_sha256(original):
        raise ValueError("question review belongs to a different source blueprint")


def validate_aqa_cs_reviews(blueprint: dict[str, Any], *, required: bool = False) -> None:
    if str(blueprint.get("paper_code", "")).startswith("7517/"):
        for question in blueprint.get("questions", []):
            for part in question.get("parts", []):
                if question.get("style_id") == "stored_program" and part.get("label") == "1":
                    item = aqa_cs_solver_item(question, part, question.get("stimulus") or {})
                    validate_open_credit_contract(item)
                    if required or part.get("difficulty_evidence") or part.get("open_credit_review"):
                        validate_open_credit_review(item, part.get("open_credit_review"))
                    elif question.get("provenance", "built-in") == "built-in" and part.get("marking", {}).get("points") != CPU_POINTS:
                        # Exact registered-template integrity only. Paraphrases
                        # require the later semantic review; equality is not a
                        # substitute for entailment on model-authored prose.
                        raise ValueError("built-in CPU credit differs from its registered source template")
            validate_question_review(question, required=required)
