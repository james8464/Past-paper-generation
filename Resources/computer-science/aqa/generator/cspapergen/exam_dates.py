from __future__ import annotations

from datetime import date, timedelta


def paper2_exam_date(today: date | None = None) -> date:
    year = (today or date.today()).year
    first_june = date(year, 6, 1)
    first_wednesday_offset = (2 - first_june.weekday()) % 7
    return first_june + timedelta(days=first_wednesday_offset + 14)


def formatted_paper2_exam_date(today: date | None = None) -> str:
    exam_date = paper2_exam_date(today)
    return f"{exam_date:%A} {exam_date.day} {exam_date:%B %Y}"


def paper1_exam_date(today: date | None = None) -> date:
    year = (today or date.today()).year
    first_june = date(year, 6, 1)
    first_monday_offset = (0 - first_june.weekday()) % 7
    return first_june + timedelta(days=first_monday_offset)


def formatted_paper1_exam_date(today: date | None = None) -> str:
    exam_date = paper1_exam_date(today)
    return f"{exam_date:%A} {exam_date.day} {exam_date:%B %Y}"
