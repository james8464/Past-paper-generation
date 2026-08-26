import subprocess

import pymupdf as fitz
from cspapergen.cli import generate_package


def test_generate_package_writes_rendered_and_assessment_outputs(tmp_path):
    paths = generate_package(output_dir=tmp_path, seed=42, dry_run=True)

    assert sorted(paths) == [
        "assessment_package",
        "mark_scheme",
        "question_paper",
    ]
    assert paths["question_paper"].name == "cs-paper-2-question-paper.pdf"
    assert paths["mark_scheme"].name == "cs-paper-2-mark-scheme.pdf"
    assert paths["question_paper"].exists()
    assert paths["mark_scheme"].exists()
    assert not (tmp_path / "cs-paper-2-source-booklet.pdf").exists()
    assert not list(tmp_path.glob("*audit*"))


def test_generated_pdfs_are_a4(tmp_path):
    paths = generate_package(output_dir=tmp_path, seed=42, dry_run=True)

    for path in (value for value in paths.values() if value.suffix == ".pdf"):
        output = subprocess.check_output(["pdfinfo", str(path)], text=True)
        assert "Page size:       595.32 x 841.92 pts (A4)" in output


def test_question_paper_uses_realistic_aqa_page_count(tmp_path):
    paths = generate_package(output_dir=tmp_path, seed=42, dry_run=True)

    output = subprocess.check_output(["pdfinfo", str(paths["question_paper"])], text=True)

    assert "Pages:" in output
    pages = int(next(line.split()[1] for line in output.splitlines() if line.startswith("Pages:")))
    assert pages == 40


def test_final_additional_answer_page_reserves_independent_notice(tmp_path):
    paths = generate_package(output_dir=tmp_path, seed=42, dry_run=True)

    document = fitz.open(paths["question_paper"])
    try:
        assert "Independent practice material" in document[-1].get_text()
    finally:
        document.close()


def test_question_cover_includes_the_independent_wordmark(tmp_path):
    paths = generate_package(output_dir=tmp_path, seed=42, dry_run=True)

    document = fitz.open(paths["question_paper"])
    try:
        page = document[0]
        cover = page.get_text()
        assert "PAPER" in cover
        assert "CREATOR" in cover
        assert abs(page.search_for("A-level")[0].x0 - 40) < 1
        candidate_frames = [
            item[1]
            for drawing in page.get_drawings()
            for item in drawing["items"]
            if item[0] == "re"
            and abs(item[1].x0 - 40) < 1
            and abs(item[1].width - 504) < 2
        ]
        assert any(
            abs(frame.y0 - 112) < 3 and abs(frame.height - 166) < 3
            for frame in candidate_frames
        )
        time_box = page.search_for("Time allowed")[0]
        examiner_box = page.search_for("For Examiner's Use")[0]
        assert examiner_box.y0 > time_box.y1 + 5
        final_advice = page.search_for("now wish to select")[0]
        assert 730 < final_advice.y1 < 765
        content_top = min(
            block[1]
            for block in page.get_text("blocks")
            if str(block[4]).strip()
        )
        content_bottom = max(
            block[3]
            for block in page.get_text("blocks")
            if str(block[4]).strip()
        )
        assert content_top >= 12
        assert content_bottom <= page.rect.height - 14.2
    finally:
        document.close()


def test_paper_two_transition_leaf_uses_do_not_write_diagonal(tmp_path):
    paths = generate_package(output_dir=tmp_path, seed=42, dry_run=True)

    document = fitz.open(paths["question_paper"])
    try:
        assert "DO NOT WRITE ON THIS PAGE" in document[36].get_text()
    finally:
        document.close()
