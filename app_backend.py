from __future__ import annotations

from app_bridge.cli import main
from app_bridge.providers import parse_json_object

__all__ = ["main", "parse_json_object"]


if __name__ == "__main__":
    raise SystemExit(main())
