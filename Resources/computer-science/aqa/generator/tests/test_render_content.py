from cspapergen.cli import generate_package
from cspapergen.generator import build_paper2_blueprint
from cspapergen.render_pdf import (
    _logic_gate_names,
    render_mark_scheme,
    render_question_paper,
)
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


def test_mark_scheme_uses_reference_header_and_table_insets(tmp_path):
    import pymupdf as fitz

    blueprint = build_paper2_blueprint(load_syllabus(), seed=42)
    output = tmp_path / "scheme.pdf"
    render_mark_scheme(blueprint, output)

    with fitz.open(output) as document:
        page = document[5]
        header = page.search_for("MARK SCHEME")[0]
        guidance = page.search_for("Marking guidance")[0]
        question = page.search_for("01")[0]
        assert 175 <= header.x0 <= 185
        assert 37 <= header.y0 <= 42
        assert 85 <= guidance.y0 <= 102
        assert 43 <= question.x0 <= 53
        assert 110 <= question.y0 <= 130
        assert any(
            drawing["rect"].x0 <= 44 and drawing["rect"].x1 >= 555
            for drawing in page.get_drawings()
        )


def test_mark_scheme_guidance_uses_available_column_width_without_spilling(tmp_path):
    import pymupdf as fitz

    blueprint = build_paper2_blueprint(load_syllabus(), seed=42)
    output = tmp_path / "scheme.pdf"
    render_mark_scheme(blueprint, output)

    with fitz.open(output) as document:
        lines = [
            (line["bbox"], "".join(span["text"] for span in line["spans"]))
            for page in list(document)[5:]
            for block in page.get_text("dict")["blocks"]
            if "lines" in block
            for line in block["lines"]
        ]
    assert any(
        "A. Blank 1 must name application software; blank 2 must name utility software."
        in text
        for _bbox, text in lines
    )
    assert all(bbox[2] <= 511 for bbox, text in lines if text.startswith(("A.", "R.")))


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


def test_logic_renderer_recognises_all_six_aqa_boolean_operations():
    assert _logic_gate_names("A·B + C̅ ⊕ (D ⊼ E) ⊽ F") == [
        "AND",
        "OR",
        "NOT",
        "XOR",
        "NAND",
        "NOR",
    ]


def _pdf_text(path):
    return extract_pdf_text(path)
