# Use the supplied generation date when labelling covers and mark schemes.

from __future__ import annotations

from datetime import date

from Backend.Core.legacy_migration import environment_value

GENERATION_DATE_ENV = "KELDIN_GENERATED_ON"


def generation_date() -> date:
    value = environment_value(GENERATION_DATE_ENV).strip()
    if not value:
        return date.today()
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{GENERATION_DATE_ENV} must use YYYY-MM-DD format") from error


def formatted_generation_date() -> str:
    value = generation_date()
    return f"{value:%A} {value.day} {value:%B %Y}"


# Return the month/year form used on mark-scheme covers.
def formatted_generation_series() -> str:
    return generation_date().strftime("%B %Y")
