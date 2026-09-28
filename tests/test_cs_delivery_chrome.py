import pymupdf
import pytest
from cspapergen.generator import build_paper1_blueprint, build_paper2_blueprint
from cspapergen.render_pdf import render_question_paper
from cspapergen.syllabus import load_syllabus


def test_written_cs_cover_barcode_caption_sits_below_bars(tmp_path):
    blueprint = build_paper2_blueprint(load_syllabus(), seed=123)
    path = tmp_path / "cover-barcode.pdf"
    render_question_paper(blueprint, path)
    with pymupdf.open(path) as document:
        page = document[0]
        bars = [
            d["rect"]
            for d in page.get_drawings()
            if d["type"] == "f"
            and d["rect"].y0 > 780
            and d["rect"].width < 5
            and d["rect"].height > 10
        ]
        spans = [
            s
            for b in page.get_text("dict")["blocks"]
            for line in b.get("lines", [])
            for s in line["spans"]
        ]
        footer = [s for s in spans if s["bbox"][1] > 780]
        assert bars
        assert "PRACTICE7517201" in "".join(s["text"].replace(" ", "") for s in footer)
        assert not any(
            pymupdf.Rect(s["bbox"]).intersects(bar) for s in footer for bar in bars
        )
        caption = [s for s in footer if s["bbox"][0] < 250]
        assert min(s["bbox"][1] for s in caption) > max(bar.y1 for bar in bars)
        assert max(s["bbox"][3] for s in caption) < page.rect.height - 5 * 72 / 25.4


@pytest.mark.parametrize("paper", ["1", "2"])
def test_candidate_paper_chrome_matches_delivery_mode(tmp_path, paper):
    build = build_paper1_blueprint if paper == "1" else build_paper2_blueprint
    blueprint = build(load_syllabus(), seed=123)
    if paper == "1":
        blueprint, _ = blueprint
    path = tmp_path / "paper.pdf"
    render_question_paper(blueprint, path)
    with pymupdf.open(path) as document:
        body = document[1]
        text = body.get_text()
        frames = [
            d
            for d in body.get_drawings()
            if d["rect"].width > 490 and d["rect"].height > 700
        ]
        if paper == "2":
            assert "Do not write" in text
            assert frames
            return
        assert "Do not write" not in text
        assert not frames
        assert any(
            d["rect"].y0 == pytest.approx(53.25, abs=0.1)
            and d["rect"].width == pytest.approx(493.25, abs=0.1)
            for d in body.get_drawings()
        )
        for page in document:
            drawings = page.get_drawings()
            if "There are no questions printed" in page.get_text():
                assert "Turn over" not in page.get_text()
            assert not any(
                d["type"] == "f"
                and d["rect"].y0 > 780
                and 0.1 < d["rect"].width < 5
                and d["rect"].height > 10
                for d in drawings
            )
            assert not any(
                d["rect"].x0 == pytest.approx(547, abs=0.1)
                and d["rect"].width == pytest.approx(32, abs=0.1)
                and d["rect"].height == pytest.approx(42, abs=0.1)
                for d in drawings
            )
        assert any(
            d["rect"].y0 == pytest.approx(773.95, abs=0.1) and d["rect"].width > 500
            for d in document[0].get_drawings()
        )
