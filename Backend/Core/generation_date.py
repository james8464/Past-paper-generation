from __future__ import annotations

import os
from datetime import date


GENERATION_DATE_ENV = "PAPER_CREATOR_GENERATED_ON"


def generation_date() -> date:
    value = os.environ.get(GENERATION_DATE_ENV, "").strip()
    if not value:
        return date.today()
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(
            f"{GENERATION_DATE_ENV} must use YYYY-MM-DD format"
        ) from error


def formatted_generation_date() -> str:
    value = generation_date()
    return f"{value:%A} {value.day} {value:%B %Y}"
