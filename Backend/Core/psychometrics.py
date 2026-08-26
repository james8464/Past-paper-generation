from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path
from typing import Any

from Backend.Core.paths import REPO_ROOT

DEFAULT_POLICY_PATH = (
    REPO_ROOT / "Resources" / "empirical-calibration-policy.json"
)


@dataclass(frozen=True)
class CalibrationPolicy:
    policy_id: str
    status: str
    approved_by_identity_class: str | None
    approval_evidence: str | None
    thresholds: dict[str, int | float]

    @property
    def approved(self) -> bool:
        return (
            self.status == "approved"
            and self.approved_by_identity_class == "assessment-specialist"
            and bool(self.approval_evidence)
        )

    def summary(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "status": self.status,
            "approved_by_identity_class": self.approved_by_identity_class,
            "approval_evidence": self.approval_evidence,
        }


def load_calibration_policy(path: Path | None = None) -> CalibrationPolicy:
    source = path or DEFAULT_POLICY_PATH
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("unsupported empirical calibration policy")
    status = str(payload.get("status", ""))
    if status not in {"draft", "approved", "retired"}:
        raise ValueError("calibration policy status is invalid")
    raw_thresholds = payload.get("thresholds")
    required = {
        "minimum_candidates",
        "minimum_item_responses",
        "minimum_double_marked_pairs",
        "minimum_group_responses",
        "minimum_reliability",
        "minimum_discrimination",
        "minimum_marker_agreement",
        "minimum_acceptable_facility",
        "maximum_acceptable_facility",
        "minimum_facility_coverage",
        "maximum_dif_gap",
    }
    if not isinstance(raw_thresholds, dict) or set(raw_thresholds) != required:
        raise ValueError("calibration policy thresholds are incomplete")
    thresholds = {
        key: _finite_positive_number(value, name=key)
        for key, value in raw_thresholds.items()
    }
    for key in (
        "minimum_candidates",
        "minimum_item_responses",
        "minimum_double_marked_pairs",
        "minimum_group_responses",
    ):
        if not isinstance(raw_thresholds[key], int) or isinstance(
            raw_thresholds[key], bool
        ):
            raise ValueError(f"calibration threshold {key} must be an integer")
        thresholds[key] = int(raw_thresholds[key])
    bounded = (
        "minimum_reliability",
        "minimum_discrimination",
        "minimum_marker_agreement",
        "minimum_acceptable_facility",
        "maximum_acceptable_facility",
        "minimum_facility_coverage",
        "maximum_dif_gap",
    )
    if any(not 0 < float(thresholds[key]) <= 1 for key in bounded):
        raise ValueError("calibration proportion thresholds must be in (0, 1]")
    if thresholds["minimum_acceptable_facility"] >= thresholds[
        "maximum_acceptable_facility"
    ]:
        raise ValueError("calibration facility bounds are invalid")
    identity = payload.get("approved_by_identity_class")
    evidence = payload.get("approval_evidence")
    policy = CalibrationPolicy(
        policy_id=str(payload.get("policy_id", "")).strip(),
        status=status,
        approved_by_identity_class=(str(identity).strip() if identity else None),
        approval_evidence=(str(evidence).strip() if evidence else None),
        thresholds=thresholds,
    )
    if not policy.policy_id:
        raise ValueError("calibration policy id is required")
    if status == "approved" and not policy.approved:
        raise ValueError(
            "approved calibration policy requires assessment-specialist evidence"
        )
    return policy


@dataclass(frozen=True)
class Response:
    candidate_id: str
    item_id: str
    score: float
    max_score: float
    time_seconds: float | None = None
    group: str | None = None
    marker_id: str | None = None

    @property
    def proportion(self) -> float:
        return self.score / self.max_score


def load_responses(path: Path) -> list[Response]:
    """Load anonymised long-form response data with strict range validation."""

    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        required = {"candidate_id", "item_id", "score", "max_score"}
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(
                "response CSV is missing columns: " + ", ".join(sorted(missing))
            )
        responses = [_parse_response(row, row_number=index) for index, row in enumerate(reader, 2)]
    if not responses:
        raise ValueError("response CSV contains no response rows")
    return responses


def calibrate_responses(
    responses: Iterable[Response],
    *,
    family: str,
    paper: str,
    form_id: str,
    review: dict[str, Any] | None = None,
    policy_path: Path | None = None,
) -> dict[str, Any]:
    """Produce conservative, auditable item and form evidence.

    Multiple marker rows for one candidate/item are averaged for attainment
    statistics and retained separately for inter-rater agreement.
    """

    policy = load_calibration_policy(policy_path)
    thresholds = policy.thresholds
    materialised = list(responses)
    _validate_identity(materialised)
    candidate_items = _candidate_item_means(materialised)
    candidates = sorted({candidate for candidate, _item in candidate_items})
    item_ids = sorted({item for _candidate, item in candidate_items})
    candidate_totals = {
        candidate: sum(
            score
            for (current, _item), score in candidate_items.items()
            if current == candidate
        )
        for candidate in candidates
    }
    items = [
        _item_statistics(
            item_id,
            candidate_items=candidate_items,
            candidate_totals=candidate_totals,
            raw=materialised,
            thresholds=thresholds,
        )
        for item_id in item_ids
    ]
    reliability = _cronbach_alpha(candidate_items, candidates, item_ids)
    marker = _marker_agreement(materialised)
    manual_review = _normalise_review(review)

    adequate_items = [
        item
        for item in items
        if item["responses"] >= thresholds["minimum_item_responses"]
        and item["discrimination"] is not None
        and item["discrimination"] >= thresholds["minimum_discrimination"]
    ]
    facility_items = [
        item
        for item in items
        if thresholds["minimum_acceptable_facility"]
        <= item["facility"]
        <= thresholds["maximum_acceptable_facility"]
    ]
    dif_flags = [
        flag
        for item in items
        for flag in item["differential_item_functioning"]
        if flag["flagged"]
    ]
    checks = {
        "policy_approved": policy.approved,
        "candidate_sample": len(candidates) >= thresholds["minimum_candidates"],
        "item_coverage": len(adequate_items) == len(items),
        "facility_range": (
            bool(items)
            and len(facility_items) / len(items)
            >= thresholds["minimum_facility_coverage"]
        ),
        "internal_consistency": (
            reliability is not None
            and reliability >= thresholds["minimum_reliability"]
        ),
        "marker_standardisation": (
            marker["pair_count"] >= thresholds["minimum_double_marked_pairs"]
            and marker["agreement"] is not None
            and marker["agreement"] >= thresholds["minimum_marker_agreement"]
        ),
        "group_fairness_screen": not dif_flags,
        "independent_manual_review": bool(manual_review["approved"]),
    }
    verified = all(checks.values())
    payload = {
        "schema_version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "family": family,
        "paper": paper,
        "form_id": form_id,
        "purpose": (
            "Student-response calibration for this exact generated form; "
            "it is not transferable to unseen generated questions."
        ),
        "sample": {
            "candidates": len(candidates),
            "items": len(items),
            "response_rows": len(materialised),
            "groups": sorted(
                {
                    response.group
                    for response in materialised
                    if response.group
                }
            ),
        },
        "form": {
            "cronbach_alpha": _rounded(reliability),
            "marker_agreement": marker,
        },
        "items": items,
        "manual_review": manual_review,
        "policy": policy.summary(),
        "thresholds": thresholds,
        "checks": checks,
        "difficulty_independently_verified": verified,
    }
    payload["evidence_fingerprint"] = evidence_fingerprint(payload)
    return payload


def write_calibration(payload: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def validate_calibration(
    path: Path,
    *,
    family: str,
    paper: str,
    form_id: str,
    policy_path: Path | None = None,
) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("unsupported response-calibration evidence")
    if (
        payload.get("family"),
        str(payload.get("paper")),
        payload.get("form_id"),
    ) != (family, paper, form_id):
        raise ValueError("response calibration does not describe this exact form")
    supplied = payload.get("evidence_fingerprint")
    comparable = dict(payload)
    comparable.pop("evidence_fingerprint", None)
    if supplied != evidence_fingerprint(comparable):
        raise ValueError("response-calibration evidence fingerprint is invalid")
    policy = load_calibration_policy(policy_path)
    if payload.get("policy") != policy.summary():
        raise ValueError("response calibration uses a different threshold policy")
    if payload.get("thresholds") != policy.thresholds:
        raise ValueError("response calibration thresholds contradict its policy")
    checks = payload.get("checks")
    if not isinstance(checks, dict) or set(checks) != {
        "policy_approved",
        "candidate_sample",
        "item_coverage",
        "facility_range",
        "internal_consistency",
        "marker_standardisation",
        "group_fairness_screen",
        "independent_manual_review",
    }:
        raise ValueError("response-calibration evidence has invalid checks")
    verified = all(value is True for value in checks.values())
    if payload.get("difficulty_independently_verified") is not verified:
        raise ValueError("response-calibration conclusion contradicts its checks")
    return {
        "schema_version": 1,
        "form_id": form_id,
        "candidates": int(payload.get("sample", {}).get("candidates", 0)),
        "difficulty_independently_verified": verified,
        "checks": checks,
        "evidence_fingerprint": supplied,
    }


def _parse_response(row: dict[str, str], *, row_number: int) -> Response:
    candidate_id = (row.get("candidate_id") or "").strip()
    item_id = (row.get("item_id") or "").strip()
    if not candidate_id or not item_id:
        raise ValueError(f"response row {row_number} has a blank identity")
    try:
        score = float(row["score"])
        max_score = float(row["max_score"])
        time_value = (row.get("time_seconds") or "").strip()
        time_seconds = float(time_value) if time_value else None
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"response row {row_number} contains a non-numeric value"
        ) from error
    if not math.isfinite(score) or not math.isfinite(max_score):
        raise ValueError(f"response row {row_number} has a non-finite score")
    if max_score <= 0 or score < 0 or score > max_score:
        raise ValueError(f"response row {row_number} has an invalid score range")
    if time_seconds is not None and (
        not math.isfinite(time_seconds) or time_seconds <= 0
    ):
        raise ValueError(f"response row {row_number} has invalid timing data")
    return Response(
        candidate_id=candidate_id,
        item_id=item_id,
        score=score,
        max_score=max_score,
        time_seconds=time_seconds,
        group=(row.get("group") or "").strip() or None,
        marker_id=(row.get("marker_id") or "").strip() or None,
    )


def _validate_identity(responses: list[Response]) -> None:
    maxima: dict[str, float] = {}
    groups: dict[str, str] = {}
    for response in responses:
        previous = maxima.setdefault(response.item_id, response.max_score)
        if not math.isclose(previous, response.max_score):
            raise ValueError(
                f"item {response.item_id} has inconsistent maximum marks"
            )
        if response.group:
            candidate_group = groups.setdefault(
                response.candidate_id, response.group
            )
            if candidate_group != response.group:
                raise ValueError(
                    f"candidate {response.candidate_id} has inconsistent groups"
                )


def _candidate_item_means(
    responses: list[Response],
) -> dict[tuple[str, str], float]:
    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    for response in responses:
        grouped[(response.candidate_id, response.item_id)].append(
            response.proportion
        )
    return {
        key: statistics.fmean(values)
        for key, values in grouped.items()
    }


def _item_statistics(
    item_id: str,
    *,
    candidate_items: dict[tuple[str, str], float],
    candidate_totals: dict[str, float],
    raw: list[Response],
    thresholds: dict[str, int | float],
) -> dict[str, Any]:
    observations = [
        (candidate, proportion)
        for (candidate, current_item), proportion in candidate_items.items()
        if current_item == item_id
    ]
    item_values = [value for _candidate, value in observations]
    rest_scores = [
        candidate_totals[candidate] - value
        for candidate, value in observations
    ]
    times = [
        response.time_seconds
        for response in raw
        if response.item_id == item_id and response.time_seconds is not None
    ]
    return {
        "item_id": item_id,
        "responses": len(observations),
        "facility": _rounded(statistics.fmean(item_values)),
        "discrimination": _rounded(_pearson(item_values, rest_scores)),
        "median_time_seconds": _rounded(statistics.median(times) if times else None),
        "differential_item_functioning": _dif(
            item_id,
            candidate_items=candidate_items,
            raw=raw,
            minimum_group_responses=int(thresholds["minimum_group_responses"]),
            maximum_gap=float(thresholds["maximum_dif_gap"]),
        ),
    }


def _dif(
    item_id: str,
    *,
    candidate_items: dict[tuple[str, str], float],
    raw: list[Response],
    minimum_group_responses: int,
    maximum_gap: float,
) -> list[dict[str, Any]]:
    candidate_groups = {
        response.candidate_id: response.group
        for response in raw
        if response.group
    }
    by_group: dict[str, list[float]] = defaultdict(list)
    for (candidate, current_item), score in candidate_items.items():
        group = candidate_groups.get(candidate)
        if current_item == item_id and group:
            by_group[group].append(score)
    result: list[dict[str, Any]] = []
    for left, right in combinations(sorted(by_group), 2):
        left_values = by_group[left]
        right_values = by_group[right]
        if min(len(left_values), len(right_values)) < minimum_group_responses:
            continue
        gap = abs(statistics.fmean(left_values) - statistics.fmean(right_values))
        result.append(
            {
                "groups": [left, right],
                "sample": [len(left_values), len(right_values)],
                "facility_gap": _rounded(gap),
                "flagged": gap > maximum_gap,
                "screen_only": True,
            }
        )
    return result


def _cronbach_alpha(
    candidate_items: dict[tuple[str, str], float],
    candidates: list[str],
    item_ids: list[str],
) -> float | None:
    if len(item_ids) < 2:
        return None
    complete = [
        [candidate_items[(candidate, item)] for item in item_ids]
        for candidate in candidates
        if all((candidate, item) in candidate_items for item in item_ids)
    ]
    if len(complete) < 2:
        return None
    item_variances = [
        statistics.variance(row[index] for row in complete)
        for index in range(len(item_ids))
    ]
    total_variance = statistics.variance(sum(row) for row in complete)
    if total_variance <= 0:
        return None
    count = len(item_ids)
    return count / (count - 1) * (1 - sum(item_variances) / total_variance)


def _marker_agreement(responses: list[Response]) -> dict[str, Any]:
    grouped: dict[tuple[str, str], list[Response]] = defaultdict(list)
    for response in responses:
        if response.marker_id:
            grouped[(response.candidate_id, response.item_id)].append(response)
    agreements: list[float] = []
    for values in grouped.values():
        by_marker = {
            response.marker_id: response
            for response in values
            if response.marker_id
        }
        for left, right in combinations(by_marker.values(), 2):
            agreements.append(
                1 - abs(left.score - right.score) / left.max_score
            )
    return {
        "method": "mean-pairwise-normalised-absolute-agreement",
        "pair_count": len(agreements),
        "agreement": _rounded(statistics.fmean(agreements) if agreements else None),
    }


def _normalise_review(review: dict[str, Any] | None) -> dict[str, Any]:
    raw = review or {}
    approved = raw.get("approved") is True
    reviewer = str(raw.get("reviewer", "")).strip()
    role = str(raw.get("role", "")).strip()
    date = str(raw.get("date", "")).strip()
    if approved and not all((reviewer, role, date)):
        raise ValueError(
            "an approved manual review requires reviewer, role, and date"
        )
    return {
        "approved": approved,
        "reviewer": reviewer or None,
        "role": role or None,
        "date": date or None,
        "notes": str(raw.get("notes", "")).strip() or None,
    }


def _pearson(left: list[float], right: list[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    left_mean = statistics.fmean(left)
    right_mean = statistics.fmean(right)
    numerator = sum(
        (x - left_mean) * (y - right_mean)
        for x, y in zip(left, right, strict=True)
    )
    left_squared = sum((value - left_mean) ** 2 for value in left)
    right_squared = sum((value - right_mean) ** 2 for value in right)
    denominator = math.sqrt(left_squared * right_squared)
    return numerator / denominator if denominator else None


def _rounded(value: float | None) -> float | None:
    return round(value, 4) if value is not None and math.isfinite(value) else None


def evidence_fingerprint(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _finite_positive_number(value: Any, *, name: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"calibration threshold {name} must be numeric")
    if not math.isfinite(float(value)) or value <= 0:
        raise ValueError(f"calibration threshold {name} must be positive")
    return value
