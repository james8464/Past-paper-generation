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
from Backend.Core.model_review import ReviewResult

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
    return hashlib.sha256(json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


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
            validate_question_review(question, required=required)
