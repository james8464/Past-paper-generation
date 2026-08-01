#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from Backend.Core.psychometrics import (
    calibrate_responses,
    load_responses,
    write_calibration,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Calibrate one exact generated paper from anonymised long-form "
            "student response data."
        )
    )
    parser.add_argument("responses", type=Path)
    parser.add_argument("--family", required=True)
    parser.add_argument("--paper", required=True)
    parser.add_argument("--form-id", required=True)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    review = (
        json.loads(args.review.read_text(encoding="utf-8"))
        if args.review
        else None
    )
    payload = calibrate_responses(
        load_responses(args.responses),
        family=args.family,
        paper=args.paper,
        form_id=args.form_id,
        review=review,
    )
    write_calibration(payload, args.output)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "candidates": payload["sample"]["candidates"],
                "items": payload["sample"]["items"],
                "difficulty_independently_verified": payload[
                    "difficulty_independently_verified"
                ],
                "checks": payload["checks"],
            },
            sort_keys=True,
        )
    )
    return 0 if payload["difficulty_independently_verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
