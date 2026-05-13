from datetime import date

from pastpapergen.exam_dates import economics_exam_schedule, formatted_economics_exam_date


def test_edexcel_9ec0_2026_timetable_dates():
    paper_1 = economics_exam_schedule("paper_1")
    paper_2 = economics_exam_schedule("paper_2")
    paper_3 = economics_exam_schedule("paper_3")

    assert paper_1.date == date(2026, 5, 11)
    assert paper_1.session == "Morning"
    assert formatted_economics_exam_date("paper_1", date(2026, 5, 13)) == "Wednesday 13 May 2026"

    assert paper_2.date == date(2026, 5, 18)
    assert paper_2.session == "Afternoon"

    assert paper_3.date == date(2026, 6, 4)
    assert paper_3.session == "Morning"
