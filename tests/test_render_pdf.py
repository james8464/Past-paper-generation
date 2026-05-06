from pathlib import Path
import re

from pastpapergen.generator import build_paper_blueprint
from pastpapergen.paper_configs import load_builtin_paper_config
from pastpapergen.render_pdf import (
    ANSWER_LINE_GAP_PT,
    BODY_FONT_SIZE_PT,
    SECTION_A_INSTRUCTION_LINES,
    _cost_revenue_geometry,
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


def test_cover_includes_exam_date(tmp_path):
    from datetime import date

    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    first_page = _pdf_text(output).split("\f")[0]
    expected_date = f"{date.today():%A} {date.today().day} {date.today():%B %Y}"

    assert expected_date in first_page
    assert "Morning (Time: 2 hours)" in first_page


def test_cover_inner_boxes_stay_inside_outer_panel(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    first_stream = next(stream for stream in _pdf_streams(output) if b"Please check" in stream)
    move_commands = re.findall(rb"\n(?:135|457) ([0-9.]+) m", first_stream)
    bottom_edges = [float(y) for y in move_commands if 430 <= float(y) <= 490]

    assert bottom_edges
    assert min(bottom_edges) >= 452


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

    assert "Seravek" in fonts
    assert "HelveticaNeue" not in fonts


def test_answer_line_style_matches_reference_dotted_lines():
    from pastpapergen.render_pdf import ANSWER_LINE_COLOR_HEX, ANSWER_LINE_DASH

    assert ANSWER_LINE_COLOR_HEX == "#505050"
    assert ANSWER_LINE_DASH == (0.6, 1.6)


def test_section_a_instruction_lines_fit_question_frame():
    assert max(len(line) for line in SECTION_A_INSTRUCTION_LINES) <= 78


def test_paper_1_render_uses_question_specific_pages(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)

    assert _pdf_page_count(output) == 33


def test_paper_1_section_b_starts_near_reference_page(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)

    assert _first_page_containing(output, "SECTION B") == 11


def test_paper_1_25_mark_questions_get_multiple_answer_pages():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    question_7 = next(question for question in blueprint.questions if question.number == "7")

    assert _extra_answer_pages("paper_1", question_7) >= 3


def test_paper_1_section_c_lists_both_choices_before_single_answer_space(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    text = _pdf_text(output)
    section_c = text.split("SECTION C", 1)[1]

    assert section_c.index("7 ") < section_c.index("OR")
    assert section_c.index("8 ") < section_c.index("Chosen question number")
    assert section_c.count("Chosen question number") == 1
    assert "Write your answer here:" in section_c


def test_paper_1_section_b_intro_matches_reference_wording(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    pages = _pdf_text(output).split("\f")
    section_b_page = pages[_first_page_containing(output, "SECTION B") - 1]

    assert "Read the following extracts (A to D) before answering Question 6" in section_b_page
    assert "Write your answers in the spaces provided." in section_b_page
    assert "You are advised to spend 1 hour on this section." in section_b_page
    assert "Extract A" in section_b_page


def test_paper_1_section_b_embeds_extracts_before_question_page(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    text = _pdf_text(output)

    assert "Source Booklet (enclosed)" not in text
    assert text.index("SECTION B") < text.index("Extract A") < text.index("Extract D")
    question_6_match = re.search(r"\b6\s+\(a\)", text)
    assert question_6_match
    assert text.index("Extract D") < question_6_match.start()


def test_paper_1_section_b_prompt_page_lists_subquestions_with_marks(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    section_b_page = next(page for page in _pdf_text(output).split("\f") if re.search(r"\b6\s+\(a\)", page))

    for mark in ["(5)", "(8)", "(12)", "(10)", "(15)"]:
        assert mark in section_b_page


def test_section_a_question_splits_written_answer_before_mcq(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    text = _pdf_text(output)

    assert text.index("(a)") < text.index("Total for Question 1 = 5 marks")
    assert text.index("(b)") < text.index("Total for Question 1 = 5 marks")


def test_section_a_pages_include_graph_labels(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = next(
        build_paper_blueprint(config, syllabus, seed=seed)
        for seed in range(100)
        if any(
            question.section == "A"
            and question.stimulus_kind == "cost_revenue_graph"
            and question.parts[0].command_word != "draw"
            for question in build_paper_blueprint(config, syllabus, seed=seed).questions
        )
    )
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    text = _pdf_text(output)

    assert "Costs/revenues" in text
    assert "Price" in text
    assert "Quantity" in text


def test_market_share_chart_uses_reference_style_labels(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = next(
        build_paper_blueprint(config, syllabus, seed=seed)
        for seed in range(100)
        if any(question.section == "A" and question.stimulus_kind == "market_share_bar_chart" for question in build_paper_blueprint(config, syllabus, seed=seed).questions)
    )
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    text = _pdf_text(output)

    assert "26.6%" in text
    assert "Lloyds" in text


def test_cost_revenue_geometry_is_aligned_inside_axes():
    geometry = _cost_revenue_geometry(100, 500)
    axis = geometry["axis"]

    assert geometry["ar"][0] == geometry["mr"][0]
    assert axis["left"] <= geometry["mr"][1][0] <= axis["right"]
    assert axis["bottom"] <= geometry["mr"][1][1] <= axis["top"]
    assert axis["bottom"] <= geometry["ar"][1][1] <= axis["top"]


def test_section_a_question_3_not_rotated_or_garbled(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=4)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    pages = _pdf_text(output).split("\f")
    page_with_q3_a = next(page for page in pages if re.search(r"\b3\s{2,}", page))
    page_with_q3_b = next(page for page in pages if "Total for Question 3 = 5 marks" in page)

    assert re.search(r"\b3\s{2,}", page_with_q3_a)
    assert "(a)" in page_with_q3_a or "Calculate" in page_with_q3_a or "Which one" in page_with_q3_a
    assert "(b)" in page_with_q3_b
    assert page_with_q3_a.count("DO NOT WRITE IN THIS AREA") <= 6


def test_section_a_draw_question_moves_mcq_to_next_page_when_spacing_is_tight(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=4)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    pages = _pdf_text(output).split("\f")
    draw_page = next(page for page in pages if "draw a" in page.lower())
    next_page = pages[pages.index(draw_page) + 1]

    assert "draw a" in draw_page.lower()
    assert "which one of the following" not in draw_page.lower()
    assert "which one of the following" in next_page.lower()
    assert "Total for Question 1 = 5 marks" in next_page
    assert "TOTAL FOR SECTION A = 25 MARKS" in _pdf_text(output)
    assert "Read the following extracts (A to D) before answering Question 6" in _pdf_text(output)
    assert "QUESTION 6 BEGINS ON THE NEXT PAGE" not in _pdf_text(output)


def test_section_a_calculate_question_moves_mcq_to_next_page_when_spacing_is_tight(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=0)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    pages = _pdf_text(output).split("\f")
    calculate_page = next(page for page in pages if "calculate the percentage change" in page.lower())
    next_page = pages[pages.index(calculate_page) + 1]

    assert "which one of the following" not in calculate_page.lower()
    assert "which one of the following" in next_page.lower()
    assert "Total for Question 1 = 5 marks" in next_page


def test_section_a_context_uses_specific_source_text(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=0)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    text = _pdf_text(output)

    assert "National Minimum Wage" in text
    assert "A short item of economic context" not in text


def test_paper_2_three_part_section_a_questions_render_all_parts(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_2")
    blueprint = build_paper_blueprint(config, syllabus, seed=0)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    text = _pdf_text(output)
    three_part_question = next(question for question in blueprint.questions if question.section == "A" and len(question.parts) == 3)

    assert f"Total for Question {three_part_question.number} = 5 marks" in text
    assert all(f"({part.label})" in text for part in three_part_question.parts)


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


def _pdf_streams(path: Path) -> list[bytes]:
    return re.findall(rb"stream\r?\n(.*?)endstream", path.read_bytes(), re.S)


def _first_page_containing(path: Path, text: str) -> int | None:
    for page_no, page in enumerate(_pdf_text(path).split("\f"), start=1):
        if text in page:
            return page_no
    return None
