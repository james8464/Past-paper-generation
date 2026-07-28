from datetime import date

import pytest

from Backend.Core.generation_date import (
    GENERATION_DATE_ENV,
    formatted_generation_date,
    generation_date,
)


def test_generation_date_defaults_to_today(monkeypatch):
    monkeypatch.delenv(GENERATION_DATE_ENV, raising=False)

    assert generation_date() == date.today()


def test_generation_date_accepts_iso_override(monkeypatch):
    monkeypatch.setenv(GENERATION_DATE_ENV, "2026-07-28")

    assert generation_date() == date(2026, 7, 28)
    assert formatted_generation_date() == "Tuesday 28 July 2026"


def test_generation_date_rejects_invalid_override(monkeypatch):
    monkeypatch.setenv(GENERATION_DATE_ENV, "28/07/2026")

    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        generation_date()
