# load the Edexcel Economics syllabus records used to select topics

from __future__ import annotations

import json
from pathlib import Path

from keldin_edexcel.models import Syllabus


def load_syllabus(path: Path) -> Syllabus:
    with path.open("r", encoding="utf-8") as handle:
        return Syllabus.model_validate(json.load(handle))
