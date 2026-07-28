from pathlib import Path
import re

from Backend.Core.generation_date import formatted_generation_date
from pastpapergen.generator import build_paper_blueprint
from pastpapergen.paper_configs import load_builtin_paper_config
from pastpapergen.render_pdf import (
    ANSWER_FRAME_H,
    ANSWER_FRAME_Y,
    ANSWER_LINE_GAP_PT,
    ANSWER_PAGE_START_Y,
    BLANK_AXIS_HEIGHT_PT,
    BLANK_AXIS_WIDTH_PT,
    BODY_FONT_SIZE_PT,
    CROSS_BOX_TOKEN,
    EDEXCEL_CROP_BOX,
    EDEXCEL_MEDIA_BOX,
    RAIL_H,
    RAIL_Y,
    SECTION_A_INSTRUCTION_LINES,
    SECTION_A_FOOTER_SAFE_Y,
    _draw_answer_lines,
    _extra_answer_pages,
    _table_rows,
    render_question_paper,
)
from pastpapergen.syllabus import load_syllabus


def _blueprint_with_section_a_question(config, syllabus, predicate):
    for seed in range(500):
        blueprint = build_paper_blueprint(config, syllabus, seed=seed)
        for question in blueprint.questions:
            if question.section == "A" and predicate(question):
                return blueprint, question
    raise AssertionError("No matching Section A question generated")


def _normalised(text: str) -> str:
    return " ".join(text.split()).lower()


def test_render_question_paper_writes_pdf(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)

    assert output.read_bytes().startswith(b"%PDF")


def test_new_section_a_visual_stimuli_have_renderer_rows():
    assert _table_rows("marginal_utility_table")[0] == ["Units consumed", "Total utility", "Marginal utility"]
    assert _table_rows("opportunity_cost_ppc_table")[0] == ["Consumer goods", "100", "85", "60", "20"]
    assert _table_rows("income_tax_schedule_table")[0] == ["Band", "Taxable income", "Marginal rate"]


def test_render_question_paper_uses_exam_style_strings(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    pdf_text = _pdf_text(output)

    assert "Level 3 GCE" in pdf_text
    assert "You do not need any other materials." in pdf_text
    assert "Total Marks" in pdf_text
    assert "Candidate surname" in pdf_text
    assert "Paper" in pdf_text
    assert "reference" in pdf_text
    assert "DO NOT WRITE IN THIS AREA" in pdf_text
    assert "9EC001" in pdf_text


def test_cover_includes_exam_date(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    first_page = _pdf_text(output).split("\f")[0]

    assert formatted_generation_date() in first_page
    assert "Morning (Time: 2 hours)" in first_page


def test_paper_2_cover_uses_official_afternoon_session(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_2")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    first_page = _pdf_text(output).split("\f")[0]

    assert formatted_generation_date() in first_page
    assert "Afternoon (Time: 2 hours)" in first_page


def test_cover_uses_date_panel_not_mock_examination_label(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    first_page = _pdf_text(output).split("\f")[0]

    assert "Mock Examination" not in first_page


def test_even_answer_pages_have_two_right_do_not_write_rails(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)

    assert _dark_pixels(output, page_index=1, rect=(543, 180, 557, 700)) > 100
    assert _dark_pixels(output, page_index=1, rect=(567, 180, 590, 700)) > 100


def test_cover_inner_boxes_stay_inside_outer_panel(tmp_path):
    import fitz

    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    doc = fitz.open(output)
    try:
        first_page_words = doc[0].get_text("words")
        visible_labels = {word[4] for word in first_page_words if 45 <= word[1] <= 430}

        assert {"Candidate", "surname", "Number", "reference"}.issubset(visible_labels)
    finally:
        doc.close()


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

    assert "HelveticaNeue" in fonts
    assert "ArialMT" not in fonts


def test_answer_line_style_matches_reference_dotted_lines():
    from pastpapergen.render_pdf import ANSWER_LINE_COLOR_HEX, ANSWER_LINE_DASH

    assert ANSWER_LINE_COLOR_HEX == "#a8a8a8"
    assert ANSWER_LINE_DASH == (0.6, 1.6)


def test_question_paper_uses_reference_bleed_and_crop_boxes(tmp_path):
    import fitz

    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    doc = fitz.open(output)
    try:
        page = doc[0]
        assert round(page.mediabox.width, 2) == round(EDEXCEL_MEDIA_BOX[2], 2)
        assert round(page.mediabox.height, 2) == round(EDEXCEL_MEDIA_BOX[3], 2)
        assert round(page.cropbox.width, 2) == round(EDEXCEL_CROP_BOX[2] - EDEXCEL_CROP_BOX[0], 2)
        assert round(page.cropbox.height, 2) == round(EDEXCEL_CROP_BOX[3] - EDEXCEL_CROP_BOX[1], 2)
    finally:
        doc.close()


def test_answer_frame_geometry_matches_reference_page():
    assert ANSWER_FRAME_Y == 48
    assert ANSWER_FRAME_Y + ANSWER_FRAME_H == 808
    assert ANSWER_PAGE_START_Y == 772
    assert RAIL_Y == 50
    assert RAIL_H == 760
    assert any(CROSS_BOX_TOKEN in line for line in SECTION_A_INSTRUCTION_LINES)


def test_answer_lines_honor_footer_safe_area():
    class Recorder:
        def __init__(self):
            self.lines = []

        def setStrokeColor(self, _color):
            pass

        def setLineWidth(self, _width):
            pass

        def setDash(self, *_dash):
            pass

        def line(self, x1, y1, x2, y2):
            self.lines.append((x1, y1, x2, y2))

    pdf = Recorder()

    _draw_answer_lines(pdf, 70, SECTION_A_FOOTER_SAFE_Y + 18, 520, 4, bottom_y=SECTION_A_FOOTER_SAFE_Y)

    assert pdf.lines
    assert all(line[1] >= SECTION_A_FOOTER_SAFE_Y for line in pdf.lines)


def test_section_a_instruction_lines_fit_question_frame():
    assert max(len(line.replace(CROSS_BOX_TOKEN, "X")) for line in SECTION_A_INSTRUCTION_LINES) <= 78


def test_paper_1_render_uses_question_specific_pages(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)

    assert _pdf_page_count(output) == 32


def test_papers_2_and_3_match_current_reference_page_counts(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    for paper_id in ("paper_2", "paper_3"):
        blueprint = build_paper_blueprint(
            load_builtin_paper_config(paper_id),
            syllabus,
            seed=42,
        )
        output = tmp_path / f"{paper_id}.pdf"

        render_question_paper(blueprint, output)

        assert _pdf_page_count(output) == 36


def test_paper_3_ends_with_three_labelled_blank_pages(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_3"),
        syllabus,
        seed=42,
    )
    output = tmp_path / "paper-3.pdf"

    render_question_paper(blueprint, output)

    assert all(
        "BLANK PAGE" in page
        for page in _pdf_text(output).split("\f")[33:36]
    )


def test_paper_3_embeds_sources_and_matches_reference_page_sequence(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_3"),
        syllabus,
        seed=42,
    )
    output = tmp_path / "paper-3.pdf"

    render_question_paper(blueprint, output)
    pages = _pdf_text(output).split("\f")

    assert "SECTION A" in pages[1]
    assert "Figure 1" in pages[1]
    assert "Extract A" in pages[2]
    assert all(mark in pages[4] for mark in ("(5)", "(8)", "(12)", "(25)"))
    assert "(a)" in pages[5] and "(5)" in pages[5]
    assert "(b)" in pages[6] and "(8)" in pages[6]
    assert "(c)" in pages[8] and "(12)" in pages[8]
    assert "Chosen question number" in pages[11]

    assert "SECTION B" in pages[17]
    assert "Figure 3" in pages[17]
    assert "Extract D" in pages[17]
    assert all(mark in pages[20] for mark in ("(5)", "(8)", "(12)", "(25)"))
    assert "(a)" in pages[21] and "(5)" in pages[21]
    assert "(b)" in pages[22] and "(8)" in pages[22]
    assert "(c)" in pages[24] and "(12)" in pages[24]
    assert "Chosen question number" in pages[27]
    assert sum("Chosen question number" in page for page in pages) == 2


def test_paper_3_prints_each_mark_once_on_summary_and_once_on_answer_page(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_3"),
        syllabus,
        seed=42,
    )
    output = tmp_path / "paper-3.pdf"

    render_question_paper(blueprint, output)
    text = _pdf_text(output)

    assert text.count("(5)") == 4
    assert text.count("(8)") == 4
    assert text.count("(12)") == 4
    assert text.count("(25)") == 8


def test_paper_1_section_b_starts_near_reference_page(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)

    assert _first_page_containing(output, "SECTION B") == 10


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
    config.sections[0].stimulus_slots[3] = ["cost_revenue_graph"]
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
    import fitz
    doc = fitz.open(output)
    image_count = sum(len(page.get_images()) for page in doc)
    doc.close()
    assert image_count >= 1, "Expected at least one graph image"


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


def test_section_a_draw_question_and_mcq_share_reference_page(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=4)
    output = tmp_path / "paper.pdf"
    draw_question = next(
        question
        for question in blueprint.questions
        if any(part.command_word == "draw" for part in question.parts)
    )

    render_question_paper(blueprint, output)
    pages = _pdf_text(output).split("\f")
    draw_page = next(page for page in pages if "draw a" in page.lower())
    assert "draw a" in draw_page.lower()
    assert "which one of the following" in draw_page.lower()
    assert f"Total for Question {draw_question.number} = 5 marks" in draw_page
    assert "TOTAL FOR SECTION A = 25 MARKS" in _pdf_text(output)
    assert "Read the following extracts (A to D) before answering Question 6" in _pdf_text(output)
    assert "QUESTION 6 BEGINS ON THE NEXT PAGE" not in _pdf_text(output)


def test_section_a_cost_revenue_draw_axes_have_labels(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint, question = _blueprint_with_section_a_question(
        config,
        syllabus,
        lambda candidate: any("Draw a cost and revenue diagram" in part.prompt for part in candidate.parts),
    )
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    prompt_text = _normalised(next(part.prompt for part in question.parts if "Draw a cost and revenue diagram" in part.prompt))
    draw_page = next(page for page in _pdf_text(output).split("\f") if prompt_text in _normalised(page))

    assert "Costs/revenues" in draw_page
    assert "Output" in draw_page


def test_section_a_blank_draw_axes_match_reference_scale(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint, _question = _blueprint_with_section_a_question(
        config,
        syllabus,
        lambda candidate: any(part.command_word == "draw" for part in candidate.parts),
    )
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    axis_lines = _blank_axis_lines(output)

    assert max(axis_lines["horizontal"]) >= BLANK_AXIS_WIDTH_PT - 5
    assert max(axis_lines["vertical"]) >= BLANK_AXIS_HEIGHT_PT - 5


def test_section_a_calculate_question_moves_mcq_to_next_page_when_spacing_is_tight(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    config.sections[0].part_command_words[0] = ["calculate", "mcq"]
    blueprint, question = _blueprint_with_section_a_question(
        config,
        syllabus,
        lambda candidate: len(candidate.parts) > 1 and candidate.parts[0].command_word == "calculate" and candidate.parts[1].command_word == "mcq",
    )
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    pages = _pdf_text(output).split("\f")
    prompt_text = _normalised(question.parts[0].prompt)
    calculate_page = next(page for page in pages if prompt_text in _normalised(page))
    next_page = pages[pages.index(calculate_page) + 1]

    assert "which one of the following" not in calculate_page.lower()
    assert "which one of the following" in next_page.lower()
    assert f"Total for Question {question.number} = 5 marks" in next_page


def test_section_a_calculate_page_fills_remaining_answer_space(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    config.sections[0].part_command_words[0] = ["calculate", "mcq"]
    blueprint, question = _blueprint_with_section_a_question(
        config,
        syllabus,
        lambda candidate: len(candidate.parts) > 1 and candidate.parts[0].command_word == "calculate" and candidate.parts[1].command_word == "mcq",
    )
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    pages = _pdf_text(output).split("\f")
    prompt_text = _normalised(question.parts[0].prompt)
    page_number = next(index + 1 for index, page in enumerate(pages) if prompt_text in _normalised(page))

    assert _long_horizontal_line_count(output, page_number) >= 12


def test_section_a_generic_data_table_uses_economic_labels(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint, _question = _blueprint_with_section_a_question(config, syllabus, lambda candidate: candidate.stimulus_kind == "data_table")
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    text = _pdf_text(output)

    assert "Value A" not in text
    assert "Value B" not in text
    assert "Quantity demanded index" in text
    assert "Average price index" in text


def test_section_a_context_uses_specific_source_text(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint, _question = _blueprint_with_section_a_question(config, syllabus, lambda candidate: candidate.stimulus_kind == "minimum_wage_context")
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    text = _pdf_text(output)

    assert "national minimum wage" in _normalised(text)
    assert "A short item of economic context" not in text


def test_section_a_surplus_diagrams_label_shaded_area(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    config.sections[0].stimulus_slots[3] = ["consumer_surplus_diagram"]
    blueprint, question = _blueprint_with_section_a_question(config, syllabus, lambda candidate: candidate.stimulus_kind == "consumer_surplus_diagram")
    output = tmp_path / "paper.pdf"

    render_question_paper(blueprint, output)
    text = _pdf_text(output)

    assert f"Total for Question {question.number}" in text
    import fitz
    doc = fitz.open(output)
    image_count = sum(len(page.get_images()) for page in doc)
    doc.close()
    assert image_count >= 1, "Expected at least one graph image"


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


def _first_page_containing(path: Path, text: str) -> int | None:
    for page_no, page in enumerate(_pdf_text(path).split("\f"), start=1):
        if text in page:
            return page_no
    return None


def _long_horizontal_line_count(path: Path, page_number: int) -> int:
    import fitz

    doc = fitz.open(path)
    try:
        page = doc[page_number - 1]
        count = 0
        for drawing in page.get_drawings():
            for item in drawing["items"]:
                if item[0] != "l":
                    continue
                start, end = item[1], item[2]
                if abs(start.y - end.y) < 0.5 and abs(end.x - start.x) > 250 and 100 < start.y < 760:
                    count += 1
        return count
    finally:
        doc.close()


def _blank_axis_lines(path: Path) -> dict[str, list[float]]:
    import fitz

    horizontal: list[float] = []
    vertical: list[float] = []
    doc = fitz.open(path)
    try:
        for page in doc:
            text = page.get_text()
            if "Draw a" not in text and "diagram to show" not in text and "diagram to identify" not in text:
                continue
            for drawing in page.get_drawings():
                for item in drawing["items"]:
                    if item[0] != "l":
                        continue
                    start, end = item[1], item[2]
                    width = abs(end.x - start.x)
                    height = abs(end.y - start.y)
                    if height < 0.5 and width > 250:
                        horizontal.append(width)
                    if width < 0.5 and height > 180:
                        vertical.append(height)
        return {"horizontal": horizontal, "vertical": vertical}
    finally:
        doc.close()


def _dark_pixels(path: Path, *, page_index: int, rect: tuple[int, int, int, int]) -> int:
    import fitz

    doc = fitz.open(path)
    try:
        pixmap = doc[page_index].get_pixmap(matrix=fitz.Matrix(3, 3), clip=fitz.Rect(*rect), colorspace=fitz.csGRAY)
        return sum(1 for value in pixmap.samples if value < 160)
    finally:
        doc.close()
