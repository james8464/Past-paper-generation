#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from Backend.Core.calibration_store import (
    CalibrationMetadata,
    CalibrationStore,
    ConsentRecord,
)
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
    parser.add_argument("responses", type=Path, nargs="?")
    parser.add_argument("--family")
    parser.add_argument("--paper")
    parser.add_argument("--form-id")
    parser.add_argument("--review", type=Path)
    parser.add_argument(
        "--policy",
        type=Path,
        help=(
            "Versioned assessment-specialist threshold policy. The bundled "
            "draft policy reports diagnostics but cannot promote readiness."
        ),
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--secure-store",
        type=Path,
        help="Encrypt row-level data in this local store before aggregation.",
    )
    parser.add_argument(
        "--key-file",
        type=Path,
        help="Fernet key file; otherwise PAPER_CREATOR_CALIBRATION_KEY is used.",
    )
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--consents", type=Path)
    parser.add_argument("--dataset-id")
    parser.add_argument("--export-encrypted", type=Path)
    parser.add_argument("--delete", action="store_true")
    args = parser.parse_args()

    review = (
        json.loads(args.review.read_text(encoding="utf-8"))
        if args.review
        else None
    )
    if args.secure_store:
        return _run_secure(args, review=review, parser=parser)

    required = {
        "responses": args.responses,
        "family": args.family,
        "paper": args.paper,
        "form-id": args.form_id,
        "output": args.output,
    }
    if missing := [name for name, value in required.items() if value is None]:
        parser.error("legacy aggregation requires " + ", ".join(missing))
    payload = calibrate_responses(
        load_responses(args.responses),
        family=args.family,
        paper=args.paper,
        form_id=args.form_id,
        review=review,
        policy_path=args.policy,
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


def _run_secure(
    args: argparse.Namespace,
    *,
    review: dict[str, object] | None,
    parser: argparse.ArgumentParser,
) -> int:
    key = _load_key(args.key_file, parser=parser)
    store = CalibrationStore(args.secure_store, key=key)
    dataset_id = args.dataset_id
    if dataset_id:
        if args.delete:
            deleted = store.delete(dataset_id)
            print(json.dumps({"dataset_id": dataset_id, "deleted": deleted}))
            return 0 if deleted else 1
        if args.export_encrypted:
            exported = store.export_encrypted(dataset_id, args.export_encrypted)
            print(json.dumps({"dataset_id": dataset_id, "export": str(exported)}))
            return 0
    else:
        if not all((args.responses, args.metadata, args.consents)):
            parser.error(
                "secure import requires responses, --metadata, and --consents"
            )
        metadata = CalibrationMetadata(
            **json.loads(args.metadata.read_text(encoding="utf-8"))
        )
        raw_consents = json.loads(args.consents.read_text(encoding="utf-8"))
        if not isinstance(raw_consents, list):
            parser.error("--consents must contain a JSON array")
        dataset_id = store.import_csv(
            args.responses,
            metadata=metadata,
            consents=[ConsentRecord(**value) for value in raw_consents],
        )

    payload = store.aggregate(
        dataset_id,
        review=review,
        policy_path=args.policy,
    )
    if args.output:
        write_calibration(payload, args.output)
    print(
        json.dumps(
            {
                "dataset_id": dataset_id,
                "output": str(args.output) if args.output else None,
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


def _load_key(
    key_file: Path | None,
    *,
    parser: argparse.ArgumentParser,
) -> bytes:
    if key_file:
        return key_file.read_bytes().strip()
    value = os.environ.get("PAPER_CREATOR_CALIBRATION_KEY", "").strip()
    if not value:
        parser.error(
            "secure storage needs --key-file or PAPER_CREATOR_CALIBRATION_KEY; "
            "the macOS app should keep this key in Keychain"
        )
    return value.encode("ascii")


if __name__ == "__main__":
    raise SystemExit(main())
