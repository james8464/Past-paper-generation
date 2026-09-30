"""Reconcile the captured official NSI archive before reference ingestion."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Backend.Core.france.corpus import (  # noqa: E402
    pin_reconciled_hashes,
    reconcile_archive_discovery,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".new")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", required=True, type=Path)
    parser.add_argument("--discovery", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    if bool(args.discovery) == bool(args.manifest):
        parser.error("choose exactly one of --discovery or --manifest")

    current = json.loads(args.register.read_text(encoding="utf-8"))
    if args.discovery:
        discovery = json.loads(args.discovery.read_text(encoding="utf-8"))
        foundational = [
            document
            for document in current.get("documents", [])
            if document.get("category") != "official_paper"
        ]
        payload = reconcile_archive_discovery(discovery, foundational)
    else:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        payload = pin_reconciled_hashes(current, manifest)
    write_json(args.register, payload)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "documents": len(payload["documents"]),
                "archive": payload["archive_reconciliation"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
