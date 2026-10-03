"""Command-line entry point for the app's scoped French corpus importer."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Backend.Core.france.corpus import (  # noqa: E402
    assign_splits,
    check_download,
    discover_links,
    duplicate_index_policy,
    ingest,
    main,
    pin_reconciled_hashes,
    prune_unregistered_sources,
    reconcile_archive_discovery,
)

__all__ = [
    "assign_splits",
    "check_download",
    "discover_links",
    "duplicate_index_policy",
    "ingest",
    "main",
    "pin_reconciled_hashes",
    "prune_unregistered_sources",
    "reconcile_archive_discovery",
]

if __name__ == "__main__":
    raise SystemExit(main())
