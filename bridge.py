from __future__ import annotations

from Backend.Core.cli import main
from Backend.Core.providers import parse_json_object

__all__ = ["main", "parse_json_object"]

if __name__ == "__main__":
    raise SystemExit(main())

