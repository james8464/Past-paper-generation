from cspapergen.cli import generate_package
from cspapergen.generator import build_paper2_blueprint
from cspapergen.render_pdf import render_question_paper
from cspapergen.syllabus import load_syllabus

from Backend.Core.pdf_text import extract_pdf_text


def test_question_paper_contains_aqa_style_cover_and_rail(tmp_path):
    paths = generate_package(output_dir=tmp_path, seed=3, dry_run=True)
    data = extract_pdf_text(paths["question_paper"])

    assert "A-level" in data
    assert "COMPUTER SCIENCE" in data
    assert "Paper 2" in data
    assert "Do not write" in data
    assert "outside the" in data
    assert "cs-paper-2-source-booklet" not in data


def test_mark_scheme_contains_aqa_style_table_headings(tmp_path):
    paths = generate_package(output_dir=tmp_path, seed=3, dry_run=True)
    data = extract_pdf_text(paths["mark_scheme"])

    assert "Mark scheme" in data
    assert "Qu" in data
    assert "Pt" in data
    assert "Marking guidance" in data
    assert "Total" in data
    assert "marks" in data


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
    return extract_pdf_text(path)
