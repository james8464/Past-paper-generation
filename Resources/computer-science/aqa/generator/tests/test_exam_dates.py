from datetime import date

from cspapergen.exam_dates import formatted_paper2_exam_date, paper2_exam_date


def test_paper2_exam_date_uses_june_exam_season():
    assert paper2_exam_date(date(2026, 5, 12)) == date(2026, 6, 17)
    assert formatted_paper2_exam_date(date(2026, 5, 12)) == "Wednesday 17 June 2026"
