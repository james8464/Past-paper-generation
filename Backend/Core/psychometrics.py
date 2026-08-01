from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable


MIN_CANDIDATES = 100
MIN_ITEM_RESPONSES = 80
MIN_DOUBLE_MARKED_PAIRS = 30
MIN_GROUP_RESPONSES = 30
MIN_RELIABILITY = 0.70
MIN_DISCRIMINATION = 0.15
MIN_MARKER_AGREEMENT = 0.80
MIN_ACCEPTABLE_FACILITY = 0.20
MAX_ACCEPTABLE_FACILITY = 0.85
MAX_DIF_GAP = 0.15


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
) -> dict[str, Any]:
    """Produce conservative, auditable item and form evidence.

    Multiple marker rows for one candidate/item are averaged for attainment
    statistics and retained separately for inter-rater agreement.
    """

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
        )
        for item_id in item_ids
    ]
    reliability = _cronbach_alpha(candidate_items, candidates, item_ids)
    marker = _marker_agreement(materialised)
    manual_review = _normalise_review(review)

    adequate_items = [
        item
        for item in items
        if item["responses"] >= MIN_ITEM_RESPONSES
        and item["discrimination"] is not None
        and item["discrimination"] >= MIN_DISCRIMINATION
    ]
    facility_items = [
        item
        for item in items
        if MIN_ACCEPTABLE_FACILITY
        <= item["facility"]
        <= MAX_ACCEPTABLE_FACILITY
    ]
    dif_flags = [
        flag
        for item in items
        for flag in item["differential_item_functioning"]
        if flag["flagged"]
    ]
    checks = {
        "candidate_sample": len(candidates) >= MIN_CANDIDATES,
        "item_coverage": len(adequate_items) == len(items),
        "facility_range": (
            bool(items) and len(facility_items) / len(items) >= 0.90
        ),
        "internal_consistency": (
            reliability is not None and reliability >= MIN_RELIABILITY
        ),
        "marker_standardisation": (
            marker["pair_count"] >= MIN_DOUBLE_MARKED_PAIRS
            and marker["agreement"] is not None
            and marker["agreement"] >= MIN_MARKER_AGREEMENT
        ),
        "group_fairness_screen": not dif_flags,
        "independent_manual_review": bool(manual_review["approved"]),
    }
    verified = all(checks.values())
    payload = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
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
        "thresholds": {
            "minimum_candidates": MIN_CANDIDATES,
            "minimum_item_responses": MIN_ITEM_RESPONSES,
            "minimum_discrimination": MIN_DISCRIMINATION,
            "acceptable_facility": [
                MIN_ACCEPTABLE_FACILITY,
                MAX_ACCEPTABLE_FACILITY,
            ],
            "minimum_reliability": MIN_RELIABILITY,
            "minimum_double_marked_pairs": MIN_DOUBLE_MARKED_PAIRS,
            "minimum_marker_agreement": MIN_MARKER_AGREEMENT,
            "minimum_group_responses": MIN_GROUP_RESPONSES,
            "maximum_dif_gap": MAX_DIF_GAP,
        },
        "checks": checks,
        "difficulty_independently_verified": verified,
    }
    payload["evidence_fingerprint"] = _fingerprint(payload)
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
    if supplied != _fingerprint(comparable):
        raise ValueError("response-calibration evidence fingerprint is invalid")
    checks = payload.get("checks")
    if not isinstance(checks, dict) or set(checks) != {
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
        ),
    }


def _dif(
    item_id: str,
    *,
    candidate_items: dict[tuple[str, str], float],
    raw: list[Response],
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
        if min(len(left_values), len(right_values)) < MIN_GROUP_RESPONSES:
            continue
        gap = abs(statistics.fmean(left_values) - statistics.fmean(right_values))
        result.append(
            {
                "groups": [left, right],
                "sample": [len(left_values), len(right_values)],
                "facility_gap": _rounded(gap),
                "flagged": gap > MAX_DIF_GAP,
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


def _fingerprint(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
