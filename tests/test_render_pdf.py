from pathlib import Path

from pastpapergen.generator import build_paper_blueprint
from pastpapergen.paper_configs import load_builtin_paper_config
from pastpapergen.render_pdf import (
    ANSWER_LINE_GAP_PT,
    BODY_FONT_SIZE_PT,
    SECTION_A_INSTRUCTION_LINES,
    _extra_answer_pages,
    render_question_paper,
)
from pastpapergen.syllabus import load_syllabus


def test_render_question_paper_writes_pdf(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)

    assert output.read_bytes().startswith(b"%PDF")


def test_render_question_paper_uses_exam_style_strings(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    pdf_bytes = output.read_bytes()

    assert b"Pearson Edexcel Level 3 GCE" in pdf_bytes
    assert b"Candidate surname" in pdf_bytes
    assert b"Paper" in pdf_bytes
    assert b"reference" in pdf_bytes
    assert b"DO NOT WRITE IN THIS AREA" in pdf_bytes
    assert b"P00000A" in pdf_bytes


def test_answer_line_spacing_matches_measured_reference():
    assert ANSWER_LINE_GAP_PT == 28


def test_question_text_size_matches_reference_body_scale():
    assert BODY_FONT_SIZE_PT == 12


def test_question_paper_uses_closer_reference_font_family(tmp_path):
    import subprocess

    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    fonts = subprocess.run(["pdffonts", str(output)], check=True, capture_output=True, text=True).stdout

    assert "Arial" in fonts
    assert "HelveticaNeue" not in fonts


def test_section_a_instruction_lines_fit_question_frame():
    assert max(len(line) for line in SECTION_A_INSTRUCTION_LINES) <= 78


def test_paper_1_render_uses_question_specific_pages(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)

    assert _pdf_page_count(output) == 40


def test_paper_1_section_b_starts_near_reference_page(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)

    assert _first_page_containing(output, "SECTION B") == 12


def test_paper_1_25_mark_questions_get_multiple_answer_pages():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    question_7 = next(question for question in blueprint.questions if question.number == "7")

    assert _extra_answer_pages("paper_1", question_7) >= 3


def test_paper_1_section_b_intro_matches_reference_wording(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    section_b_page = _pdf_text(output).split("\f")[11]

    assert "Read Figure 1 and the following extracts (A to C)" in section_b_page
    assert "in the Source Booklet before answering Question 6" in section_b_page
    assert "Write your answers in the spaces provided." in section_b_page
    assert "You are advised to spend 1 hour on this section." in section_b_page


def test_paper_1_section_b_prompt_page_lists_subquestions_with_marks(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    section_b_page = _pdf_text(output).split("\f")[11]

    for mark in ["(5)", "(8)", "(12)", "(10)", "(15)"]:
        assert mark in section_b_page


def test_section_a_question_splits_written_answer_before_mcq(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    pages = _pdf_text(output).split("\f")

    assert "(a)" in pages[1]
    assert "(b)" not in pages[1]
    assert "(b)" in pages[2]
    assert "Total for Question 1 = 5 marks" in pages[2]


def test_section_a_pages_include_graph_labels(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    text = _pdf_text(output)

    assert "Costs/revenues" in text
    assert "Price" in text
    assert "Quantity" in text


def test_section_a_question_3_not_rotated_or_garbled(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=4)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    pages = _pdf_text(output).split("\f")
    page_with_q3_a = next(page for page in pages if "3   " in page and "(a)" in page)
    page_with_q3_b = next(page for page in pages if "Total for Question 3 = 5 marks" in page)

    assert page_with_q3_a.index("3") < page_with_q3_a.index("(a)")
    assert "(a)" in page_with_q3_a
    assert "(b)" not in page_with_q3_a
    assert "(b)" in page_with_q3_b
    assert page_with_q3_a.count("DO NOT WRITE IN THIS AREA") <= 6


def test_section_a_draw_question_keeps_mcq_on_same_page_before_section_blank(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=4)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    pages = _pdf_text(output).split("\f")
    draw_page = next(page for page in pages if "Draw a diagram" in page)

    assert "Draw a diagram" in draw_page
    assert "Which one of the following" in draw_page
    assert "TOTAL FOR SECTION A = 25 MARKS" in _pdf_text(output)
    assert "QUESTION 6 BEGINS ON THE NEXT PAGE" in _pdf_text(output)


def test_section_a_context_uses_specific_source_text(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=0)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    text = _pdf_text(output)

    assert "National Minimum Wage" in text
    assert "A short item of economic context" not in text


def _pdf_page_count(path: Path) -> int:
    import subprocess

    result = subprocess.run(["pdfinfo", str(path)], check=True, capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    raise AssertionError("Pages not found")


def _pdf_text(path: Path) -> str:
    import subprocess

    return subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _first_page_containing(path: Path, text: str) -> int | None:
    for page_no, page in enumerate(_pdf_text(path).split("\f"), start=1):
        if text in page:
            return page_no
    return None
