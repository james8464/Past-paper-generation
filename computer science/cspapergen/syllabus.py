from __future__ import annotations

import json
from pathlib import Path

from cspapergen.models import Syllabus

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SYLLABUS_PATH = PROJECT_ROOT / "data" / "syllabus_seed.json"


def load_syllabus(path: Path | None = None) -> Syllabus:
    source = path or DEFAULT_SYLLABUS_PATH
    with source.open("r", encoding="utf-8") as handle:
        return Syllabus.model_validate(json.load(handle))
