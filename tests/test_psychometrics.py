from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from Backend.Core.psychometrics import (
    Response,
    calibrate_responses,
    load_responses,
    validate_calibration,
    write_calibration,
)


def _responses(*, candidates: int = 120) -> list[Response]:
    randomiser = random.Random(8464)
    result: list[Response] = []
    abilities = [randomiser.random() for _ in range(candidates)]
    for candidate, ability in enumerate(abilities):
        for item, difficulty in enumerate((0.25, 0.35, 0.45, 0.55, 0.65, 0.72)):
            raw = max(0, min(4, round((ability + 0.5 - difficulty) * 4)))
            group = "A" if candidate % 2 else "B"
            for marker, score in (("m1", raw), ("m2", raw)):
                result.append(
                    Response(
                        candidate_id=f"c{candidate}",
                        item_id=f"q{item}",
                        score=score,
                        max_score=4,
                        time_seconds=30 + item * 5,
                        group=group,
                        marker_id=marker,
                    )
                )
    return result


def test_calibration_requires_all_evidence_before_claiming_verified() -> None:
    payload = calibrate_responses(
        _responses(candidates=20),
        family="aqa/economics",
        paper="1",
        form_id="form-a",
    )

    assert payload["difficulty_independently_verified"] is False
    assert payload["checks"]["candidate_sample"] is False
    assert payload["checks"]["independent_manual_review"] is False


def test_calibration_can_validate_a_well_evidenced_exact_form(tmp_path: Path) -> None:
    payload = calibrate_responses(
        _responses(),
        family="aqa/economics",
        paper="1",
        form_id="form-a",
        review={
            "approved": True,
            "reviewer": "Independent assessor",
            "role": "Assessment specialist",
            "date": "2026-07-29",
        },
    )
    path = write_calibration(payload, tmp_path / "calibration.json")

    assert payload["difficulty_independently_verified"] is True
    summary = validate_calibration(
        path,
        family="aqa/economics",
        paper="1",
        form_id="form-a",
    )
    assert summary["difficulty_independently_verified"] is True
    assert summary["candidates"] == 120


def test_calibration_fingerprint_detects_tampering(tmp_path: Path) -> None:
    payload = calibrate_responses(
        _responses(candidates=20),
        family="aqa/economics",
        paper="1",
        form_id="form-a",
    )
    path = write_calibration(payload, tmp_path / "calibration.json")
    changed = json.loads(path.read_text(encoding="utf-8"))
    changed["sample"]["candidates"] = 999
    path.write_text(json.dumps(changed), encoding="utf-8")

    with pytest.raises(ValueError, match="fingerprint"):
        validate_calibration(
            path,
            family="aqa/economics",
            paper="1",
            form_id="form-a",
        )


def test_response_csv_rejects_scores_above_the_item_maximum(
    tmp_path: Path,
) -> None:
    path = tmp_path / "responses.csv"
    path.write_text(
        "candidate_id,item_id,score,max_score\nc1,q1,5,4\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="score range"):
        load_responses(path)
