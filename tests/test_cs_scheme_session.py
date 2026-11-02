"""Mark-scheme headers share the cover's generation series, not a fixed June."""

from copy import deepcopy

import pymupdf
import pytest
from cspapergen.generator import (
    build_paper1_blueprint,
    build_paper2_blueprint,
    build_topic_question_bank,
)
from cspapergen.render_pdf import render_mark_scheme
from cspapergen.syllabus import load_syllabus

from Backend.Core.generation_date import GENERATION_DATE_ENV


@pytest.mark.parametrize("paper", ["1", "2", "4.2", "4.10", "4.12"])
def test_scheme_cover_and_every_header_share_generation_series(
    tmp_path, monkeypatch, paper
):
    syllabus = load_syllabus()
    if paper == "1":
        blueprint, _ = build_paper1_blueprint(syllabus, seed=270100)
    elif paper == "2":
        blueprint = build_paper2_blueprint(syllabus, seed=270100)
    else:
        blueprint = build_topic_question_bank(syllabus, topic_id=paper, seed=270100)
    original = deepcopy(blueprint.model_dump(mode="json"))
    bodies = []
    for month, series in (("06", "June"), ("11", "November"), ("09", "September")):
        monkeypatch.setenv(GENERATION_DATE_ENV, f"2026-{month}-02")
        path = tmp_path / f"scheme-{paper}-{month}.pdf"
        render_mark_scheme(blueprint, path)
        with pymupdf.open(path) as pdf:
            assert f"{series} 2026" in pdf[0].get_text()
            body = []
            for page in list(pdf)[1:]:
                expected = (
                    "MARK SCHEME – A-LEVEL COMPUTER SCIENCE – "
                    f"{blueprint.paper_code} – {series.upper()} 2026"
                )
                assert expected in page.get_text()
                bounds = page.search_for(expected)
                assert len(bounds) == 1
                assert 0 <= bounds[0].x0 < bounds[0].x1 <= page.rect.width
                assert 0 <= bounds[0].y0 < bounds[0].y1 < 65
                # Exclude only the header. All marking text/positions, page
                # counters and vector geometry must remain unchanged.
                body.append(
                    (
                        [word for word in page.get_text("words") if word[1] >= 65],
                        page.get_drawings(),
                    )
                )
            bodies.append(body)
    assert bodies[0] == bodies[1] == bodies[2]
    assert blueprint.model_dump(mode="json") == original
