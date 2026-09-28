"""Command-line entry point for the app's scoped French corpus importer."""

from Backend.Core.france.corpus import (
    assign_splits,
    check_download,
    discover_links,
    ingest,
    main,
)

__all__ = ["assign_splits", "check_download", "discover_links", "ingest", "main"]

if __name__ == "__main__":
    raise SystemExit(main())
