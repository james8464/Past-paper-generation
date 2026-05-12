from cspapergen.cli import generate_package
from cspapergen.generator import build_paper2_blueprint
from cspapergen.render_pdf import render_question_paper
from cspapergen.syllabus import load_syllabus


def test_question_paper_contains_aqa_style_cover_and_rail(tmp_path):
    paths = generate_package(output_dir=tmp_path, seed=3, dry_run=True)
    data = paths["question_paper"].read_bytes()

    assert b"A-level" in data
    assert b"COMPUTER SCIENCE" in data
    assert b"Paper 2" in data
    assert b"Do not write" in data
    assert b"outside the" in data
    assert b"cs-paper-2-source-booklet" not in data


def test_mark_scheme_contains_aqa_style_table_headings(tmp_path):
    paths = generate_package(output_dir=tmp_path, seed=3, dry_run=True)
    data = paths["mark_scheme"].read_bytes()

    assert b"Mark scheme" in data
    assert b"Qu" in data
    assert b"Pt" in data
    assert b"Marking guidance" in data
    assert b"Total" in data
    assert b"marks" in data


def test_single_part_questions_do_not_render_duplicate_subquestion_number(tmp_path):
    blueprint = build_paper2_blueprint(load_syllabus(), seed=968382730775149540)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    text = _pdf_text(output)

    assert "0 1 . 1" not in text


def test_question_paper_page_two_has_aqa_answer_all_questions_header(tmp_path):
    blueprint = build_paper2_blueprint(load_syllabus(), seed=968382730775149540)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    text = _pdf_text(output)

    assert "Answer all questions." in text


def _pdf_text(path):
    import subprocess

    return subprocess.run(["pdftotext", "-layout", str(path), "-"], check=True, capture_output=True, text=True).stdout
