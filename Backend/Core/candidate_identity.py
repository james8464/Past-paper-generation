"""Canonical, evidence-free identity for difficulty-review candidates."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CANDIDATE_PROJECTION_VERSION = "difficulty-candidate-v1"

# Review results and host-computed identities are evidence about content, not
# candidate content. Every other field, including authoring_context contracts,
# remains identity-bearing. The overloaded ``provenance`` key is handled by its
# candidate-source role below.
EVIDENCE_FREE_EXCLUDED_FIELDS = frozenset(
    {
        "candidate_content_identity",
        "content_review",
        "difficulty_evidence",
        "open_credit_review",
        "reviewed_blueprint_sha256",
        "reviewed_content_sha256",
    }
)

# ``provenance`` is overloaded: question/authoring provenance is review metadata,
# while these typed candidate-source containers use it as public source content.
_SOURCE_PROVENANCE_ROLES = frozenset(
    {"rendered_stimulus", "source_instance", "stimulus"}
)


class DifficultyCandidateProjection(BaseModel):
    """Host projection with separate model-visible and identity-bearing views."""

    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal[1] = 1
    route: str = Field(min_length=1)
    review_content: dict[str, Any]
    identity_content: dict[str, Any]


class CandidateContentIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal[1] = 1
    projection_version: Literal["difficulty-candidate-v1"] = (
        CANDIDATE_PROJECTION_VERSION
    )
    route: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


def difficulty_candidate_projection(
    *,
    route: str,
    review_content: Any,
    identity_content: Any | None = None,
) -> DifficultyCandidateProjection:
    review = _mapping(review_content)
    identity = review if identity_content is None else _mapping(identity_content)
    return DifficultyCandidateProjection(
        route=route,
        review_content=_without_evidence(review),
        identity_content=_without_evidence(identity),
    )


def shared_difficulty_candidate_projection(
    *,
    question: Any,
    option: Any,
) -> DifficultyCandidateProjection:
    """Project a shared-route item with its candidate-visible parent source."""

    parent = _mapping(option)
    parent.pop("questions", None)
    content = {
        "part": _mapping(question),
        "parent_source": parent,
    }
    return difficulty_candidate_projection(
        route="shared",
        review_content=content,
    )


def edexcel_difficulty_candidate_projection(
    *,
    question: Any,
    part: Any,
    review_content: Any,
) -> DifficultyCandidateProjection:
    """Bind Edexcel source and selected part without duplicate parent credit."""

    parent = _mapping(question)
    selected_part = _mapping(part)
    if parent.get("parts"):
        parent.pop("parts", None)
        for duplicate_credit in (
            "assessment_contract",
            "indicative_content",
            "mark_breakdown",
            "mark_scheme",
            "scheme_mode",
        ):
            parent.pop(duplicate_credit, None)
        identity = {"parent_source": parent, "part": selected_part}
    else:
        identity = {"question": parent}
    return difficulty_candidate_projection(
        route="edexcel-economics",
        review_content=review_content,
        identity_content=identity,
    )


def ensure_difficulty_candidate_projection(
    candidate: Any,
) -> DifficultyCandidateProjection:
    if isinstance(candidate, DifficultyCandidateProjection):
        return candidate
    if isinstance(candidate, dict) and {
        "schema_version",
        "route",
        "review_content",
        "identity_content",
    } <= candidate.keys():
        return DifficultyCandidateProjection.model_validate(candidate, strict=True)
    return difficulty_candidate_projection(
        route="shared-generic",
        review_content=candidate,
    )


def candidate_content_identity(candidate: Any) -> CandidateContentIdentity:
    projection = ensure_difficulty_candidate_projection(candidate)
    canonical = {
        "projection_version": CANDIDATE_PROJECTION_VERSION,
        "route": projection.route,
        "content": _without_evidence(projection.identity_content),
    }
    digest = hashlib.sha256(
        json.dumps(
            canonical,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    return CandidateContentIdentity(route=projection.route, sha256=digest)


def candidate_review_content(candidate: Any) -> dict[str, Any]:
    return ensure_difficulty_candidate_projection(candidate).review_content


def _mapping(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    if not isinstance(value, dict):
        raise TypeError("difficulty candidate projection requires a mapping")
    return deepcopy(value)


def _without_evidence(value: Any, *, path: tuple[str, ...] = ()) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _without_evidence(child, path=(*path, str(key)))
            for key, child in value.items()
            if str(key) not in EVIDENCE_FREE_EXCLUDED_FIELDS
            and not (
                str(key) == "provenance"
                and (not path or path[-1] not in _SOURCE_PROVENANCE_ROLES)
            )
        }
    if isinstance(value, list):
        return [_without_evidence(child, path=path) for child in value]
    if isinstance(value, tuple):
        return [_without_evidence(child, path=path) for child in value]
    return value
