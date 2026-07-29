from __future__ import annotations

from pathlib import Path

from reportlab.graphics.shapes import Drawing, Ellipse, Line, PolyLine, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from Backend.Core.exam_blueprints import (
    GeneratedOption,
    GeneratedPaper,
    GeneratedQuestion,
)
from Backend.Core.exam_cover import (
    CoverProfile,
    aqa_question_cover,
    mark_scheme_cover,
)
from Backend.Core.fonts import register_fonts
from Backend.Core.generation_date import formatted_generation_date
from Backend.Core.reportlab_theme import themed_table_class
from Backend.Core.mark_scheme_front_matter import aqa_front_matter_pages


AQA_A4 = (595.32, 841.92)
PAGE_WIDTH, PAGE_HEIGHT = AQA_A4
INK = colors.HexColor("#181818")
GREY = colors.HexColor("#eeeeee")
FONT = "AQAArial"
FONT_BOLD = "AQAArial-Bold"
register_fonts(FONT, FONT_BOLD)
Table = themed_table_class(Table, FONT)


def render_question_paper(paper: GeneratedPaper, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = _document(path, paper, "Question paper")
    story: list[Flowable] = _cover(paper)
    pages = _paper_pages(paper)
    assert len(pages) == 35
    for page in pages:
        story.append(PageBreak())
        story.extend(page)
    doc.build(story)


def render_mark_scheme(paper: GeneratedPaper, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = _document(path, paper, "Mark scheme")
    story: list[Flowable] = mark_scheme_cover(
        _cover_profile(paper),
        FONT,
        FONT_BOLD,
    )
    if paper.paper_id == "paper_1":
        pages = _paper_one_mark_scheme_pages(paper)
        assert len(pages) == 25
        for page in pages:
            story.append(PageBreak())
            story.extend(page)
        doc.build(story)
        return

    story.extend(
        [
            PageBreak(),
            *aqa_front_matter_pages(
                "accounting",
                heading_style=STYLES["kicker"],
                body_style=STYLES["body"],
            ),
        ]
    )
    for section in paper.sections:
        story.extend([_banner(f"Section {section.id}"), Spacer(1, 4 * mm)])
        for question in section.options[0].questions:
            story.extend(_scheme_block(question))
        story.append(PageBreak())
    story.pop()
    story.extend(_mark_scheme_extension_pages(paper))
    doc.build(story)


def _paper_one_mark_scheme_pages(paper: GeneratedPaper) -> list[list[Flowable]]:
    questions = {
        question.number: question
        for section in paper.sections
        for question in section.options[0].questions
    }
    option = paper.sections[1].options[0]
    pages = [
        *_accounting_marking_guidance_pages(),
        _objective_test_answers([questions[f"{number:02d}"] for number in range(1, 11)]),
        _short_answer_scheme_page(questions["11"]),
        _statement_of_financial_position_scheme(questions["12"], option),
        _completed_ledger_scheme(questions["13.1"], option),
        _completed_sales_account_scheme(questions["13.2"], option),
        _completed_income_statement_scheme(questions["14.1"], option),
        _income_statement_workings_scheme(questions["14.1"], option),
        _income_statement_finishing_scheme(questions["14.1"], option),
        _levels_scheme_page(questions["14.2"], "Employees and financial statements"),
        _indicative_content_page(questions["14.2"], "Question 14.2"),
        _completed_capital_accounts_scheme(questions["15.1"], option),
        _completed_appropriation_scheme(questions["15.2"], option),
        _levels_with_indicative_scheme_page(
            questions["15.3"],
            "The partnership agreement",
        ),
        _levels_scheme_page(questions["16"], "Improving the accounting records"),
        _extended_indicative_content_page(questions["16"], "Question 16"),
        _extended_judgement_page(questions["16"], "Question 16"),
        _levels_scheme_page(questions["17"], "The shareholder's decision"),
        _extended_indicative_content_page(questions["17"], "Question 17"),
        _extended_judgement_page(questions["17"], "Question 17"),
    ]
    return pages


def _accounting_marking_guidance_pages() -> list[list[Flowable]]:
    return [
        [
            Paragraph("Mark schemes", STYLES["kicker"]),
            Paragraph("General marking guidance", STYLES["heading"]),
            Spacer(1, 3 * mm),
            _guidance_table(
                [
                    (
                        "1",
                        "Apply the mark scheme positively. Credit what the student has "
                        "shown they know, understand and can do.",
                    ),
                    (
                        "2",
                        "Mark the response as a whole. Do not deduct marks for an error "
                        "more than once unless the mark scheme says otherwise.",
                    ),
                    (
                        "3",
                        "Accept a correct accounting treatment expressed in equivalent "
                        "terminology. Figures must follow the stated method.",
                    ),
                    (
                        "4",
                        "Where a student has used an alternative valid method, award the "
                        "available method and accuracy marks.",
                    ),
                    (
                        "5",
                        "Use the full mark range. A response does not need to be perfect "
                        "to receive full marks.",
                    ),
                    (
                        "6",
                        "Do not award marks where contradictory statements invalidate an "
                        "otherwise correct point.",
                    ),
                    (
                        "7",
                        "If a response is crossed out and not replaced, mark the crossed-out "
                        "work unless it is clearly presented as a draft.",
                    ),
                    (
                        "8",
                        "Record a mark for every part and check that question totals agree "
                        "with the assessment-objective grid.",
                    ),
                ]
            ),
            Spacer(1, 5 * mm),
            Paragraph(
                "The indicative content is not exhaustive. Reward other valid accounting "
                "arguments when they are applied to the information in the question.",
                STYLES["small"],
            ),
        ],
        [
            Paragraph("Level of response marking", STYLES["kicker"]),
            Paragraph(
                "Use the following process for every levels-based question.",
                STYLES["body"],
            ),
            Spacer(1, 3 * mm),
            _guidance_table(
                [
                    ("Step 1", "Read the whole response and identify the best-fit level."),
                    (
                        "Step 2",
                        "Match the response to the level descriptor. The response need not "
                        "meet every feature in a descriptor.",
                    ),
                    (
                        "Step 3",
                        "Use the quality, balance and development of the response to select "
                        "a mark within the level.",
                    ),
                    (
                        "Step 4",
                        "Where a response has features of two levels, place it in the level "
                        "that best represents the response overall.",
                    ),
                    (
                        "Step 5",
                        "Reserve zero for a response that contains nothing worthy of credit.",
                    ),
                ]
            ),
            Spacer(1, 5 * mm),
            _scheme_grid(
                ["Position in level", "Characteristics"],
                [
                    ["Top", "Consistently precise, well-developed and fully applied."],
                    ["Middle", "Clear and generally developed, with minor omissions."],
                    ["Bottom", "Meets the level threshold but is uneven or partially developed."],
                ],
                [38 * mm, 129 * mm],
            ),
            Spacer(1, 5 * mm),
            Paragraph(
                "Extended responses should contain a supported judgement. The judgement "
                "may appear anywhere in the response and need not be in a separate conclusion.",
                STYLES["small"],
            ),
        ],
        [
            Paragraph("Question-specific marking", STYLES["kicker"]),
            _scheme_grid(
                ["Type of mark", "Application"],
                [
                    ["Knowledge", "Credit accurate accounting principles, definitions and treatments."],
                    ["Application", "Credit use of figures, business circumstances and named stakeholders."],
                    ["Analysis", "Credit developed cause-and-effect links and supported calculations."],
                    ["Evaluation", "Credit balanced comparison and a judgement supported by the evidence."],
                    ["Calculation", "Award method marks where a valid approach is shown, even if an earlier figure is wrong."],
                    ["Narrative", "Do not reward repetition of the stem unless it is used to develop an accounting point."],
                ],
                [38 * mm, 129 * mm],
            ),
            Spacer(1, 5 * mm),
            Paragraph("Questions 14.2 and 15.3", STYLES["heading"]),
            Paragraph(
                "Award marks by level. A list of undeveloped points cannot reach the top "
                "level. The strongest responses use the case information to develop both "
                "benefits and limitations before reaching a supported conclusion.",
                STYLES["small"],
            ),
            Spacer(1, 4 * mm),
            Paragraph("Questions 16 and 17", STYLES["heading"]),
            Paragraph(
                "The 25-mark questions assess all four objectives. Calculation or ratio "
                "evidence should be interpreted, not merely stated. A decision must follow "
                "from the student's analysis of the alternatives.",
                STYLES["small"],
            ),
        ],
        [
            Paragraph("Marking conventions", STYLES["kicker"]),
            _scheme_grid(
                ["Abbreviation", "Meaning"],
                [
                    ["AO1", "Knowledge and understanding"],
                    ["AO2", "Application"],
                    ["AO3", "Analysis"],
                    ["AO4", "Evaluation"],
                    ["OF", "Own figure"],
                    ["W", "Working mark"],
                    ["CAO", "Correct answer only"],
                    ["FT", "Follow through"],
                    ["NE", "No evaluation"],
                    ["NAQ", "Not answering the question"],
                    ["Max", "Maximum mark available after a specified error or omission"],
                ],
                [35 * mm, 132 * mm],
            ),
            Spacer(1, 5 * mm),
            Paragraph("Presentation of accounts", STYLES["heading"]),
            Paragraph(
                "Accept conventional account layouts and clearly labelled alternatives. "
                "Do not penalise the omission of currency signs where the unit is stated. "
                "Figures shown in brackets may be accepted as negatives.",
                STYLES["small"],
            ),
        ],
        [
            Paragraph("Assessment objectives", STYLES["kicker"]),
            _scheme_grid(
                ["Objective", "What is assessed"],
                [
                    ["AO1", "Demonstrate knowledge and understanding of accounting principles, concepts and techniques."],
                    ["AO2", "Apply knowledge and understanding to familiar and unfamiliar accounting situations."],
                    ["AO3", "Analyse accounting information, issues and evidence to support reasoned conclusions."],
                    ["AO4", "Evaluate accounting information to make judgements, decisions and recommendations."],
                ],
                [28 * mm, 139 * mm],
            ),
            Spacer(1, 5 * mm),
            _scheme_grid(
                ["Response", "Principal objective emphasis"],
                [
                    ["Objective test", "AO1 and AO2"],
                    ["Preparation and calculation", "AO1, AO2 and AO3"],
                    ["Six-mark assessment", "AO2 and AO3"],
                    ["Twenty-five-mark advice", "AO1, AO2, AO3 and AO4"],
                ],
                [54 * mm, 113 * mm],
            ),
            Spacer(1, 5 * mm),
            Paragraph(
                "The assessment-objective labels guide the examiner; they do not replace "
                "the question-specific mark instructions.",
                STYLES["small"],
            ),
        ],
        [
            Paragraph("Workings and own figures", STYLES["kicker"]),
            _guidance_table(
                [
                    (
                        "OF",
                        "Follow through a student's own figure when it results from a "
                        "previously identifiable accounting error and is used consistently.",
                    ),
                    (
                        "W",
                        "Award a working mark when the correct accounting process is shown, "
                        "even if the final figure is arithmetically incorrect.",
                    ),
                    (
                        "Rounding",
                        "Accept sensible rounding unless the question specifies a required "
                        "degree of accuracy.",
                    ),
                    (
                        "Labels",
                        "A figure with no label may be credited where its purpose is clear "
                        "from its position in a conventional statement or account.",
                    ),
                    (
                        "Balances",
                        "Accept balance c/d and balance b/d in the conventional positions. "
                        "Do not award a separate mark twice for the same balance.",
                    ),
                    (
                        "Narrative",
                        "Where a calculation supports a narrative response, reward the "
                        "interpretation of the figure as well as the method.",
                    ),
                ]
            ),
            Spacer(1, 5 * mm),
            _scheme_grid(
                ["Example", "Marking treatment"],
                [
                    ["Correct method, one arithmetic slip", "Award method marks and follow through the result."],
                    ["Correct answer without workings", "Award full marks unless workings are explicitly required."],
                    ["Two alternative answers", "Credit only where the final intended answer is clear."],
                ],
                [60 * mm, 107 * mm],
            ),
        ],
    ]


def _objective_test_answers(questions: list[GeneratedQuestion]) -> list[Flowable]:
    rows = []
    for question in questions:
        answer = question.mark_scheme[0].removesuffix(".")
        rows.append([question.number.lstrip("0") or "0", answer, "1"])
    return [
        Paragraph("Section A", STYLES["kicker"]),
        Paragraph("Objective test answers", STYLES["heading"]),
        Spacer(1, 4 * mm),
        _scheme_grid(["Question", "Answer", "Mark"], rows, [25 * mm, 117 * mm, 25 * mm]),
        Spacer(1, 6 * mm),
        Paragraph(
            "Award one mark for the correct option. No mark is awarded for selecting "
            "more than one option.",
            STYLES["small"],
        ),
    ]


def _short_answer_scheme_page(question: GeneratedQuestion) -> list[Flowable]:
    examples = [
        "Encourage a larger order, increasing sales volume and the contribution earned.",
        "Reward repeat purchases, strengthening customer loyalty and future revenue.",
        "Attract a new customer who might otherwise buy from a competitor.",
        "Reduce the unit selling price while preserving total profit through higher volume.",
    ]
    return [
        _scheme_question_heading(question),
        Spacer(1, 3 * mm),
        Paragraph("AO1 — 6 marks", STYLES["heading"]),
        Paragraph(
            "Apply the levels of response mark scheme to each reason. Award a maximum "
            "of 3 marks for each reason.",
            STYLES["small"],
        ),
        Spacer(1, 4 * mm),
        _scheme_grid(
            ["Level", "Marks", "Descriptor"],
            [
                ["3", "3", "A clear and thorough explanation showing a benefit to the business."],
                ["2", "2", "A partial explanation showing a relevant benefit."],
                ["1", "1", "A fragmented or identified point."],
                ["0", "0", "Nothing worthy of credit."],
            ],
            [20 * mm, 25 * mm, 122 * mm],
        ),
        Spacer(1, 5 * mm),
        Paragraph("Answers may include:", STYLES["body"]),
        *[
            Paragraph(f"• {example}", STYLES["small"])
            for example in examples
        ],
        Spacer(1, 3 * mm),
        Paragraph("Reward other valid answers.", STYLES["small"]),
    ]


def _statement_of_financial_position_scheme(
    question: GeneratedQuestion,
    option: GeneratedOption,
) -> list[Flowable]:
    values = [int(value * 1000) for value in option.chart_values]
    rows = [
        ["Non-current assets", "Cost\n£", "Accumulated\ndepreciation\n£", "Carrying\namount\n£", "Marks"],
        ["Premises", f"{values[4]:,}", f"({values[1] // 2:,})", f"{values[4] - values[1] // 2:,}", "1"],
        ["Plant and machinery", f"{values[3]:,}", f"({values[0] // 3:,})", f"{values[3] - values[0] // 3:,}", "2"],
        ["Motor vehicles", f"{values[2]:,}", f"({values[1] // 4:,})", f"{values[2] - values[1] // 4:,}", "2"],
        ["Total non-current assets", "", "", f"{values[4] + values[3] + values[2] - values[1] * 3 // 4 - values[0] // 3:,}", "1 OF"],
    ]
    return [
        _scheme_question_heading(question),
        Paragraph(
            f"<b>{option.title}</b><br/>Statement of financial position (extract)",
            STYLES["centre_bold"],
        ),
        Spacer(1, 3 * mm),
        _scheme_grid(rows[0], rows[1:], [50 * mm, 27 * mm, 38 * mm, 32 * mm, 20 * mm]),
        Spacer(1, 5 * mm),
        _scheme_grid(
            ["Working", "Mark"],
            [
                [f"Premises depreciation: {values[1]:,} × 50% = {values[1] // 2:,}", "1"],
                [f"Plant disposal adjustment: {values[0]:,} ÷ 3 = {values[0] // 3:,}", "1"],
                [f"Vehicle depreciation: {values[1]:,} × 25% = {values[1] // 4:,}", "1"],
            ],
            [145 * mm, 22 * mm],
        ),
        Spacer(1, 4 * mm),
        Paragraph(
            "Award one mark for the correct presentation of cost and accumulated "
            "depreciation. Accept the student's own figure for the total carrying amount.",
            STYLES["small"],
        ),
    ]


def _completed_ledger_scheme(
    question: GeneratedQuestion,
    option: GeneratedOption,
) -> list[Flowable]:
    values = [int(value * 145) for value in option.chart_values]
    data = [
        ["Date", "Details", "£", "Date", "Details", "£"],
        ["1 Jan", "Balance b/d", f"{values[4]:,}", "31 Dec", "Bank", f"{values[2]:,}"],
        ["31 Dec", "Sales", f"{values[3]:,}", "31 Dec", "Sales returns", f"{values[0]:,}"],
        ["", "", "", "31 Dec", "Discount allowed", f"{values[1] // 5:,}"],
        ["", "", "", "31 Dec", "Balance c/d", f"{values[4] + values[3] - values[2] - values[0] - values[1] // 5:,}"],
        ["", "", f"{values[4] + values[3]:,}", "", "", f"{values[4] + values[3]:,}"],
        ["1 Jan", "Balance b/d", f"{values[4] + values[3] - values[2] - values[0] - values[1] // 5:,}", "", "", ""],
    ]
    return [
        _scheme_question_heading(question),
        Paragraph(f"<b>{option.title}</b> — Sales Ledger Control Account", STYLES["centre_bold"]),
        Spacer(1, 3 * mm),
        _scheme_grid(data[0], data[1:], [19 * mm, 38 * mm, 25 * mm, 19 * mm, 41 * mm, 25 * mm]),
        Spacer(1, 5 * mm),
        Paragraph(
            "One mark each for opening balance, credit sales, bank and returns/discount. "
            "Award the final mark for a correctly balanced account (own figure).",
            STYLES["small"],
        ),
    ]


def _completed_sales_account_scheme(
    question: GeneratedQuestion,
    option: GeneratedOption,
) -> list[Flowable]:
    values = [int(value * 145) for value in option.chart_values]
    net_sales = values[3] - values[0]
    rows = [
        ["31 Dec", "Sales returns", f"{values[0]:,}", "31 Dec", "Sales journal", f"{values[3]:,}"],
        ["31 Dec", "Income statement", f"{net_sales:,}", "", "", ""],
        ["", "", f"{values[3]:,}", "", "", f"{values[3]:,}"],
    ]
    return [
        _scheme_question_heading(question),
        Paragraph(f"<b>{option.title}</b> — Sales Account", STYLES["centre_bold"]),
        Spacer(1, 3 * mm),
        _scheme_grid(
            ["Date", "Details", "£", "Date", "Details", "£"],
            rows,
            [19 * mm, 38 * mm, 25 * mm, 19 * mm, 41 * mm, 25 * mm],
        ),
        Spacer(1, 7 * mm),
        _scheme_grid(
            ["Mark", "Requirement"],
            [
                ["1", "Credit sales entered on the credit side."],
                ["1", "Sales returns deducted and net sales transferred to the income statement."],
            ],
            [25 * mm, 142 * mm],
        ),
    ]


def _completed_income_statement_scheme(
    question: GeneratedQuestion,
    option: GeneratedOption,
) -> list[Flowable]:
    values = [int(value * 1000) for value in option.chart_values]
    revenue = values[4] + values[2]
    cost = values[3] + values[1]
    rows = [
        ["Revenue", f"{revenue:,}", "", "2"],
        ["Opening inventory", f"{values[1]:,}", "", ""],
        ["Purchases and carriage", f"{values[3]:,}", "", "3"],
        ["Less closing inventory", f"({values[0]:,})", f"{cost - values[0]:,}", "2"],
        ["Gross profit", "", f"{revenue - cost + values[0]:,}", "1 OF"],
        ["Distribution and administration expenses", "", f"({values[2] // 2:,})", "3"],
        ["Finance costs", "", f"({values[1] // 4:,})", "1"],
        ["Profit for the year", "", f"{revenue - cost + values[0] - values[2] // 2 - values[1] // 4:,}", "2 OF"],
    ]
    return [
        _scheme_question_heading(question),
        Paragraph(f"<b>{option.title}</b><br/>Income statement for the year ended", STYLES["centre_bold"]),
        Spacer(1, 3 * mm),
        _scheme_grid(
            ["", "£", "£", "Marks"],
            rows,
            [76 * mm, 31 * mm, 35 * mm, 25 * mm],
        ),
    ]


def _income_statement_workings_scheme(
    question: GeneratedQuestion,
    option: GeneratedOption,
) -> list[Flowable]:
    values = [int(value * 1000) for value in option.chart_values]
    return [
        Paragraph(f"Question {question.number} continued", STYLES["kicker"]),
        Paragraph("Workings and adjustments", STYLES["heading"]),
        Spacer(1, 3 * mm),
        _scheme_grid(
            ["Adjustment", "Treatment", "Marks"],
            [
                ["Damaged inventory", f"Value at the lower of cost and NRV: £{values[0]:,}.", "2"],
                ["Irrecoverable debt", f"Remove £{values[1] // 5:,} from receivables and charge expense.", "2"],
                ["Supplier invoice", f"Accrue £{values[2] // 4:,} and include in purchases/expenses.", "2"],
                ["Depreciation", f"Charge £{values[3] // 10:,} using the stated policy.", "2"],
                ["Presentation", "Clear income-statement layout with appropriate labels and subtotals.", "2"],
            ],
            [49 * mm, 93 * mm, 25 * mm],
        ),
        Spacer(1, 5 * mm),
        Paragraph(
            "Where an incorrect adjustment is used consistently, award subsequent own-figure "
            "marks. Do not award a mark twice for the same calculation.",
            STYLES["small"],
        ),
    ]


def _income_statement_finishing_scheme(
    question: GeneratedQuestion,
    option: GeneratedOption,
) -> list[Flowable]:
    values = [int(value * 1000) for value in option.chart_values]
    return [
        Paragraph(f"Question {question.number} continued", STYLES["kicker"]),
        Paragraph("Further workings", STYLES["heading"]),
        Spacer(1, 3 * mm),
        _scheme_grid(
            ["Item", "Calculation", "Result £", "Mark"],
            [
                ["Taxation", f"{values[4]:,} × 19%", f"{values[4] * 19 // 100:,}", "1"],
                ["Accrued expense", f"{values[2]:,} × 3/12", f"{values[2] // 4:,}", "1"],
                ["Irrecoverable debt", f"{values[1]:,} × 20%", f"{values[1] // 5:,}", "1"],
                ["Depreciation", f"{values[3]:,} × 10%", f"{values[3] // 10:,}", "1"],
            ],
            [48 * mm, 58 * mm, 38 * mm, 23 * mm],
        ),
        Spacer(1, 6 * mm),
        Paragraph("Marker notes", STYLES["heading"]),
        _guidance_table(
            [
                ("OF", "Follow through the student's gross-profit figure into profit for the year."),
                ("Tax", "Credit a tax charge calculated consistently from the student's profit figure."),
                ("Format", "Accept alternative conventional labels and ordering."),
                ("Total", "Do not award more than 14 marks across Question 14.1."),
            ]
        ),
    ]


def _levels_scheme_page(
    question: GeneratedQuestion,
    context: str,
) -> list[Flowable]:
    if question.marks == 6:
        levels = [
            ["3", "5–6", "A well-developed assessment. Uses relevant accounting evidence, analyses effects and reaches a supported judgement."],
            ["2", "3–4", "A reasonable response with some application and developed analysis. Judgement may be partial or uneven."],
            ["1", "1–2", "Limited knowledge or application. Points are asserted with little development."],
            ["0", "0", "Nothing worthy of credit."],
        ]
    else:
        levels = [
            ["5", "21–25", "Thorough knowledge and precise application. Sustained analysis leads to a balanced, fully supported recommendation."],
            ["4", "16–20", "Good knowledge and effective application. Analysis is developed and the judgement is supported."],
            ["3", "11–15", "Reasonable knowledge and some relevant application. Analysis supports a partially developed judgement."],
            ["2", "6–10", "Some knowledge and limited application. Analysis is incomplete and evaluation is weak."],
            ["1", "1–5", "Fragmented knowledge with little application or development."],
            ["0", "0", "Nothing worthy of credit."],
        ]
    return [
        _scheme_question_heading(question),
        Paragraph(context, STYLES["heading"]),
        Spacer(1, 3 * mm),
        _scheme_grid(
            ["Level", "Marks", "Descriptor"],
            levels,
            [20 * mm, 25 * mm, 122 * mm],
        ),
        Spacer(1, 5 * mm),
        Paragraph(
            "Use a best-fit approach. The indicative content on the following page "
            "illustrates material that may be credited; it is not a model answer.",
            STYLES["small"],
        ),
    ]


def _levels_with_indicative_scheme_page(
    question: GeneratedQuestion,
    context: str,
) -> list[Flowable]:
    return [
        _scheme_question_heading(question),
        Paragraph(context, STYLES["heading"]),
        Spacer(1, 3 * mm),
        _scheme_grid(
            ["Level", "Marks", "Descriptor"],
            [
                ["3", "5–6", "A well-developed assessment with relevant application, analysis and a supported judgement."],
                ["2", "3–4", "A reasonable response with some application and development; judgement may be partial."],
                ["1", "1–2", "Limited knowledge or application with little development."],
                ["0", "0", "Nothing worthy of credit."],
            ],
            [20 * mm, 25 * mm, 122 * mm],
        ),
        Spacer(1, 4 * mm),
        Paragraph("Indicative content", STYLES["heading"]),
        _scheme_grid(
            ["Possible content", "AO"],
            [
                [point, "AO2/AO3"]
                for point in question.mark_scheme[:5]
            ],
            [137 * mm, 30 * mm],
        ),
    ]


def _indicative_content_page(
    question: GeneratedQuestion,
    title: str,
) -> list[Flowable]:
    rows = [
        [Paragraph(point, STYLES["scheme_small"]), "AO2/AO3"]
        for point in question.mark_scheme
    ]
    return [
        Paragraph(f"{title} continued", STYLES["kicker"]),
        Paragraph("Indicative content", STYLES["heading"]),
        Spacer(1, 3 * mm),
        _scheme_grid(
            ["Possible content", "Assessment objective"],
            rows,
            [132 * mm, 35 * mm],
        ),
        Spacer(1, 5 * mm),
        Paragraph(
            "Credit a different conclusion where it follows from valid accounting "
            "analysis and is supported by the circumstances in the question.",
            STYLES["small"],
        ),
    ]


def _extended_indicative_content_page(
    question: GeneratedQuestion,
    title: str,
) -> list[Flowable]:
    # The generator also carries reusable level descriptors and marker checks.
    # Those are printed on the preceding page; this page mirrors the concise
    # question-specific indicative-content page used in the reference scheme.
    points = [
        *question.mark_scheme[:5],
        *[
            point
            for point in question.mark_scheme
            if point.startswith(("AO1:", "AO2:", "AO3:"))
        ][:7],
    ]
    rows = [
        [
            Paragraph(point, STYLES["scheme_small"]),
            "AO2/AO3" if index < max(1, len(points) - 2) else "AO4",
        ]
        for index, point in enumerate(points)
    ]
    return [
        Paragraph(f"{title} continued", STYLES["kicker"]),
        Paragraph("Indicative content and judgement", STYLES["heading"]),
        Spacer(1, 3 * mm),
        _scheme_grid(
            ["Possible content", "AO"],
            rows,
            [137 * mm, 30 * mm],
        ),
        Spacer(1, 4 * mm),
        Paragraph("Judgement", STYLES["heading"]),
        Paragraph(
            "The recommendation should weigh the alternatives, recognise the limitations "
            "of the evidence and explain why the selected course is preferable in context. "
            "A conclusion without supporting analysis cannot reach the highest level.",
            STYLES["small"],
        ),
    ]


def _extended_judgement_page(
    question: GeneratedQuestion,
    title: str,
) -> list[Flowable]:
    applied_points = [
        point
        for point in question.mark_scheme
        if point.startswith(("AO2:", "AO3:"))
    ][7:]
    return [
        Paragraph(f"{title} continued", STYLES["kicker"]),
        Paragraph("Analysis and evaluation", STYLES["heading"]),
        Spacer(1, 3 * mm),
        _scheme_grid(
            ["Further guidance", "AO"],
            [
                [point, "AO3"]
                for point in applied_points[:5]
            ],
            [137 * mm, 30 * mm],
        ),
        Spacer(1, 5 * mm),
        Paragraph("Judgement", STYLES["heading"]),
        _guidance_table(
            [
                ("Balance", "Weigh the principal financial and non-financial evidence."),
                ("Limits", "Recognise uncertainty, assumptions and information that is unavailable."),
                ("Decision", "Make a clear recommendation that follows from the preceding analysis."),
                ("Context", "Use the named organisation, stakeholder objectives and supplied figures."),
            ]
        ),
        Spacer(1, 4 * mm),
        Paragraph(
            "Credit a different recommendation where it is supported by valid accounting "
            "analysis. The indicative content is not exhaustive.",
            STYLES["small"],
        ),
    ]


def _completed_capital_accounts_scheme(
    question: GeneratedQuestion,
    option: GeneratedOption,
) -> list[Flowable]:
    values = [int(value * 210) for value in option.chart_values[:3]]
    rows = [
        ["1 Jan", "Balance b/d", f"{values[0]:,}", f"{values[1]:,}", "Retirement", "Goodwill", f"{values[2] // 3:,}", f"{values[2] // 4:,}"],
        ["Retirement", "Goodwill", f"{values[2] // 2:,}", f"{values[2] // 3:,}", "Retirement", "Bank", f"{values[0] // 5:,}", f"{values[1] // 6:,}"],
        ["", "Bank", f"{values[0] // 5:,}", f"{values[1] // 6:,}", "31 Dec", "Balance c/d", f"{values[0] + values[2] // 2 - values[2] // 3 - values[0] // 5:,}", f"{values[1] + values[2] // 3 - values[2] // 4 - values[1] // 6:,}"],
    ]
    return [
        _scheme_question_heading(question),
        Paragraph("Partners' Capital Accounts", STYLES["centre_bold"]),
        Spacer(1, 3 * mm),
        _scheme_grid(
            ["Date", "Details", "Alex £", "Morgan £", "Date", "Details", "Alex £", "Morgan £"],
            rows,
            [16 * mm, 27 * mm, 20 * mm, 20 * mm, 16 * mm, 27 * mm, 20 * mm, 21 * mm],
        ),
        Spacer(1, 5 * mm),
        Paragraph(
            "Award marks for opening balances, goodwill in the correct ratio, cash "
            "introduced or withdrawn, and closing balances (own figure).",
            STYLES["small"],
        ),
    ]


def _completed_appropriation_scheme(
    question: GeneratedQuestion,
    option: GeneratedOption,
) -> list[Flowable]:
    values = [int(value * 145) for value in option.chart_values]
    profit_1, profit_2 = values[4], values[3]
    rows = [
        ["Profit for the period", f"{profit_1:,}", f"{profit_2:,}", "1"],
        ["Interest on drawings", f"{values[0] // 12:,}", f"{values[1] // 12:,}", "1"],
        ["Interest on capital", f"({values[1] // 5:,})", f"({values[2] // 5:,})", "2"],
        ["Partner salaries", f"({values[0] // 3:,})", f"({values[0] // 2:,})", "1"],
        ["Residual profit", f"{profit_1 - values[1] // 5 - values[0] // 3:,}", f"{profit_2 - values[2] // 5 - values[0] // 2:,}", "1"],
        ["Share of residual profit", "Agreed ratio", "Revised ratio", "2"],
    ]
    return [
        _scheme_question_heading(question),
        Paragraph("Profit and loss appropriation account", STYLES["centre_bold"]),
        Spacer(1, 3 * mm),
        _scheme_grid(
            ["", "First period £", "Second period £", "Marks"],
            rows,
            [75 * mm, 35 * mm, 35 * mm, 22 * mm],
        ),
        Spacer(1, 5 * mm),
        Paragraph(
            "Accept a combined account or two clearly labelled calculations. Follow "
            "through an incorrect residual profit if the profit-sharing ratios are applied correctly.",
            STYLES["small"],
        ),
    ]


def _scheme_question_heading(question: GeneratedQuestion) -> Table:
    number, _, part = question.number.partition(".")
    return Table(
        [
            [
                Paragraph("Qu", STYLES["scheme_small"]),
                Paragraph("Part", STYLES["scheme_small"]),
                Paragraph("Marking guidance", STYLES["scheme_small"]),
                Paragraph("Total<br/>marks", STYLES["scheme_small"]),
            ],
            [
                Paragraph(number.lstrip("0") or "0", STYLES["scheme_small"]),
                Paragraph(part, STYLES["scheme_small"]),
                Paragraph(question.prompt, STYLES["scheme_small"]),
                Paragraph(f"<b>{question.marks}</b>", STYLES["answer"]),
            ],
        ],
        colWidths=[13 * mm, 13 * mm, 119 * mm, 22 * mm],
        style=TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#666666")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        ),
    )


def _guidance_table(rows: list[tuple[str, str]]) -> Table:
    return _scheme_grid(
        ["", "Guidance"],
        [[label, text] for label, text in rows],
        [28 * mm, 139 * mm],
    )


def _scheme_grid(
    headings: list[str],
    rows: list[list[object]],
    widths: list[float],
) -> Table:
    data = [
        [Paragraph(f"<b>{heading}</b>", STYLES["scheme_small"]) for heading in headings]
    ]
    for row in rows:
        data.append(
            [
                cell
                if isinstance(cell, Flowable)
                else Paragraph(str(cell), STYLES["scheme_small"])
                for cell in row
            ]
        )
    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#888888")),
                ("BACKGROUND", (0, 0), (-1, 0), GREY),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


MARK_SCHEME_EXTENSION_PAGE_COUNTS = {
    "paper_1": 7,
    "paper_2": 8,
}


def _mark_scheme_extension_pages(paper: GeneratedPaper) -> list[Flowable]:
    count = MARK_SCHEME_EXTENSION_PAGE_COUNTS[paper.paper_id]
    questions = [
        question
        for section in paper.sections
        for question in section.options[0].questions
    ]
    extended = [question for question in questions if question.marks >= 6]
    pages: list[Flowable] = []
    for index in range(count):
        pages.append(PageBreak())
        if index == count - 2:
            pages.extend(_assessment_objectives_page(paper, questions))
        elif index == count - 1:
            pages.extend(_independent_practice_page())
        else:
            question = extended[index % len(extended)]
            pages.extend(_continued_marking_guidance(question, index))
    return pages


def _continued_marking_guidance(
    question: GeneratedQuestion,
    page_index: int,
) -> list[Flowable]:
    points = question.mark_scheme
    chunk_size = 9
    start = (page_index * chunk_size) % max(len(points), 1)
    chunk = (points + points)[start : start + chunk_size]
    rows = [["Indicative marking guidance", ""]]
    rows.extend(
        [[Paragraph(f"• {point}", STYLES["small"]), ""] for point in chunk]
    )
    table = Table(rows, colWidths=[155 * mm, 12 * mm])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), GREY),
                ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return [
        Paragraph(f"Question {question.number} guidance continued", STYLES["heading"]),
        Spacer(1, 3 * mm),
        Paragraph(question.prompt, STYLES["body"]),
        Spacer(1, 4 * mm),
        table,
        Spacer(1, 5 * mm),
        Paragraph(
            "Credit a valid alternative accounting treatment when the method is applied "
            "consistently, the workings are shown and the resulting figures follow from it.",
            STYLES["body"],
        ),
    ]


def _assessment_objectives_page(
    paper: GeneratedPaper,
    questions: list[GeneratedQuestion],
) -> list[Flowable]:
    rows = [["Question", "Marks", "Assessment focus"]]
    for question in questions:
        focus = (
            "AO1, AO2 and AO3"
            if question.marks >= 6
            else "AO1 and AO2"
        )
        rows.append([question.number, str(question.marks), focus])
    table = Table(rows, colWidths=[38 * mm, 25 * mm, 104 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), GREY),
                ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return [
        Paragraph("Assessment objectives grid", STYLES["heading"]),
        Spacer(1, 4 * mm),
        table,
        Spacer(1, 5 * mm),
        Paragraph(
            f"The candidate paper maximum is {paper.total_marks}. Verify each subtotal "
            "against the marks printed beside the corresponding question.",
            STYLES["body"],
        ),
    ]


def _independent_practice_page() -> list[Flowable]:
    return [
        Spacer(1, 205 * mm),
        Paragraph("Independent practice material", STYLES["heading"]),
        Spacer(1, 3 * mm),
        Paragraph(
            "Created by Paper Creator for private revision. This mark scheme is not "
            "produced, endorsed or approved by AQA or any examination board.",
            STYLES["small"],
        ),
    ]


def _paper_pages(paper: GeneratedPaper) -> list[list[Flowable]]:
    section_a, section_b, section_c = paper.sections
    a_option = section_a.options[0]
    pages: list[list[Flowable]] = []
    for start, stop in ((0, 2), (2, 5), (5, 8), (8, 10)):
        content: list[Flowable] = []
        if start == 0:
            content.extend(_intro(section_a))
        for question in a_option.questions[start:stop]:
            content.extend(_mcq_block(question))
        pages.append(content)
    if paper.paper_id == "paper_1":
        pages.extend(_paper_one_section_a_case_pages(a_option))
    else:
        for index, question in enumerate(a_option.questions[10:]):
            content = []
            if index == 0:
                content.extend(
                    [
                        Paragraph(a_option.title, STYLES["option"]),
                        Paragraph(a_option.stimulus[0], STYLES["extract"]),
                        Spacer(1, 4 * mm),
                    ]
                )
            content.extend(_question_page(question, a_option, lines=18))
            pages.append(content)
            if index == 0:
                pages.append(
                    [Paragraph("Turn over for the next question", STYLES["centre_bold"])]
                )
        pages.append(
            [
                Paragraph("Section A answer continued", STYLES["centre_bold"]),
                AnswerLines(34),
            ]
        )
    assert len(pages) == 10

    b_option = section_b.options[0]
    if paper.paper_id == "paper_1":
        pages.extend(_paper_one_section_b_pages(section_b, b_option))
    else:
        for index, question in enumerate(b_option.questions):
            content = [*_intro(section_b)] if index == 0 else []
            if index == 0:
                content.extend(
                    [
                        Paragraph(b_option.title, STYLES["option"]),
                        Paragraph(b_option.stimulus[0], STYLES["extract"]),
                        Spacer(1, 3 * mm),
                    ]
                )
            content.extend(_question_page(question, b_option, lines=18))
            pages.append(content)
    expected_before_c = 20 if paper.paper_id == "paper_1" else 18
    assert len(pages) == expected_before_c

    c_option = section_c.options[0]
    if paper.paper_id == "paper_1":
        pages.extend(_paper_one_section_c_pages(section_c, c_option))
        return pages

    allocation = 8
    for index, question in enumerate(c_option.questions):
        content: list[Flowable] = []
        if index == 0:
            content.extend(
                [
                    *_intro(section_c),
                    Paragraph(c_option.title, STYLES["option"]),
                    Paragraph(c_option.stimulus[index], STYLES["extract"]),
                    Spacer(1, 3 * mm),
                ]
            )
        else:
            content.extend(
                [
                    Paragraph(c_option.stimulus[index], STYLES["extract"]),
                    Spacer(1, 4 * mm),
                ]
            )
        content.extend(_question_page(question, c_option, lines=17))
        pages.append(content)
        pages.extend(
            [
                [
                    Paragraph(
                        f"Question {question.number} continued",
                        STYLES["centre_bold"],
                    ),
                    AnswerLines(34),
                ]
                for _ in range(allocation - 1)
            ]
        )
    pages.append(
        [Paragraph("Additional page, if required", STYLES["centre_bold"]), AnswerLines(34)]
    )
    return pages


def _paper_one_section_c_pages(
    section,
    option: GeneratedOption,
) -> list[list[Flowable]]:
    question_16, question_17 = option.questions
    return [
        [*_intro(section), _accounting_system_case(option)],
        [
            _question_table(question_16),
            Spacer(1, 4 * mm),
            AnswerLines(29),
        ],
        [AnswerLines(34)],
        [
            Paragraph("Extra space", STYLES["small"]),
            AnswerLines(33),
        ],
        [AnswerLines(34)],
        _do_not_write_page(),
        [_shareholder_case(option)],
        [
            _question_table(question_17),
            Spacer(1, 4 * mm),
            AnswerLines(29),
        ],
        [AnswerLines(34)],
        [
            Paragraph("Extra space", STYLES["small"]),
            AnswerLines(33),
        ],
        [AnswerLines(34)],
        _no_questions_page(),
        _additional_answer_page(),
        _additional_answer_page(),
        _additional_answer_page(include_legal_notice=True),
    ]


def _accounting_system_case(option: GeneratedOption) -> Table:
    values = [int(round(value * 1000)) for value in option.chart_values]
    annual_salary = int(values[0] * 0.32)
    software_cost = int(values[1] * 0.24)
    training_cost = int(values[2] * 0.09)
    accountant_fee = int(values[3] * 0.08)
    lost_profit = int(values[4] * 0.14)
    paragraphs = [
        (
            f"<b>{option.title}</b> is a growing business owned by a sole trader. "
            "Its accounting records are currently maintained by the owner using "
            "spreadsheets, a cash book and paper invoices. Two family members work in "
            "the business, but neither has received formal accounting training."
        ),
        (
            "The owner spends two days each week recording transactions, preparing "
            "customer statements and following up late payments. The latest trial "
            "balance contained several errors and the year-end accounts were delayed. "
            f"An external accountant charges £{accountant_fee:,} each year to correct "
            "the records and prepare the financial statements."
        ),
        (
            "The current system has caused the business to lose money. Several "
            "irrecoverable debts were not identified promptly, inventory records do not "
            "agree with the physical count, and the owner cannot determine the profit "
            "earned on individual contracts."
        ),
        (
            f"During the last year, inaccurate cost information contributed to a contract "
            f"being quoted too low. The owner estimates that £{lost_profit:,} of profit "
            "was lost. Monthly bank reconciliations are also several weeks in arrears."
        ),
        (
            f"A qualified bookkeeper would cost £{annual_salary:,} each year. The owner "
            "expects the bookkeeper to improve credit control, provide monthly management "
            "information and allow more time to develop the business. The bookkeeper "
            "would use double-entry records and prepare draft financial statements."
        ),
        (
            f"Alternatively, cloud accounting software would cost £{software_cost:,} "
            f"with initial staff training of £{training_cost:,}. It would automate bank "
            "reconciliation and invoicing, but the owner is concerned about data security, "
            "subscription increases and the reliability of internet access."
        ),
        (
            "The external accountant has offered to introduce the system and provide "
            "quarterly management information. One family member opposes the change "
            "because the existing procedures are familiar and customers have not "
            "complained about the invoices."
        ),
        (
            "The owner must decide whether to employ a bookkeeper, introduce the cloud "
            "system, or continue with the present arrangements."
        ),
    ]
    content: list[Flowable] = []
    for paragraph in paragraphs:
        content.extend([Paragraph(paragraph, STYLES["body"]), Spacer(1, 3 * mm)])
    case = Table(
        [[content]],
        colWidths=[153 * mm],
        style=TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.65, INK),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        ),
    )
    return Table(
        [[_question_reference("16"), case]],
        colWidths=[14 * mm, 153 * mm],
        style=TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        ),
    )


def _shareholder_case(option: GeneratedOption) -> Table:
    values = [int(round(value * 1000)) for value in option.chart_values]
    ordinary_opening = int(values[4] * 1.0)
    premium_opening = int(values[1] * 0.22)
    retained_opening = int(values[3] * 0.45)
    share_issue = int(ordinary_opening * 0.2)
    revaluation = int(values[0] * 0.24)
    profit = int(values[3] * 0.30)
    dividends = int(profit * 0.1)
    retained_closing = retained_opening + profit - dividends
    statement = Table(
        [
            [
                "",
                "Ordinary\nshares\n£000",
                "Share\npremium\n£000",
                "Revaluation\nreserve\n£000",
                "Retained\nearnings\n£000",
            ],
            [
                "At start of year",
                f"{ordinary_opening:,}",
                f"{premium_opening:,}",
                "–",
                f"{retained_opening:,}",
            ],
            ["Revaluation", "", "", f"{revaluation:,}", ""],
            [
                "Issue of shares",
                f"{share_issue:,}",
                f"({share_issue:,})",
                "",
                "",
            ],
            ["Dividends", "", "", "", f"({dividends:,})"],
            ["Profit for the year", "", "", "", f"{profit:,}"],
            [
                "At end of year",
                f"{ordinary_opening + share_issue:,}",
                f"{premium_opening - share_issue:,}",
                f"{revaluation:,}",
                f"{retained_closing:,}",
            ],
        ],
        colWidths=[47 * mm, 22.25 * mm, 22.25 * mm, 22.25 * mm, 22.25 * mm],
        style=TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.45, INK),
                ("FONT", (0, 0), (-1, 0), FONT_BOLD),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        ),
    )
    content: list[Flowable] = [
        Paragraph(
            f"An investor owns shares in <b>{option.title}</b>. The company operates "
            "in a competitive market and has recently increased its borrowing to finance "
            "new production equipment. Since acquiring the shares, the investor has "
            "received only one dividend and is considering selling the investment.",
            STYLES["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph(
            f"Share price at the start of the year: {values[0]:.0f}p<br/>"
            f"Share price at the end of the year: {values[2]:.0f}p<br/>"
            f"Earnings per share at the end of the year: {values[1] / 4:.1f}p",
            STYLES["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph(
            f"<b>{option.title}</b><br/>"
            "<b>Statement of changes in equity for the year (extract)</b>",
            STYLES["centre_bold"],
        ),
        Spacer(1, 2 * mm),
        statement,
        Spacer(1, 4 * mm),
        Paragraph(
            "Note 1: Non-current assets were revalued following the discovery of "
            "additional productive capacity.<br/><br/>"
            "Note 2: Bonus shares were issued to existing shareholders during the year.",
            STYLES["body"],
        ),
        Spacer(1, 4 * mm),
        Paragraph(
            "Directors intend to retain more profit to fund expansion. The investor is "
            "concerned about the dividend policy, gearing, higher interest rates and the "
            "environmental effect of the new equipment. A comparable company has a higher "
            "dividend yield but a lower price earnings ratio.",
            STYLES["body"],
        ),
    ]
    case = Table(
        [[content]],
        colWidths=[153 * mm],
        style=TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.65, INK),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        ),
    )
    return Table(
        [[_question_reference("17"), case]],
        colWidths=[14 * mm, 153 * mm],
        style=TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        ),
    )


def _no_questions_page() -> list[Flowable]:
    page = _do_not_write_page()
    page[0] = Paragraph(
        "There are no questions printed on this page",
        STYLES["centre_bold"],
    )
    return page


def _additional_answer_page(
    *,
    include_legal_notice: bool = False,
) -> list[Flowable]:
    row_count = 18 if include_legal_notice else 25
    rows: list[list[object]] = [
        [
            Paragraph("Question<br/>number", STYLES["marks"]),
            Paragraph(
                "<b>Additional page, if required</b><br/>"
                "Write the question numbers in the left-hand margin.",
                STYLES["centre_bold"],
            ),
        ],
        *[["", ""] for _ in range(row_count)],
    ]
    table = Table(
        rows,
        colWidths=[14 * mm, 153 * mm],
        rowHeights=[10 * mm, *([8.2 * mm] * row_count)],
    )
    style = [
        ("BOX", (0, 0), (-1, -1), 0.65, INK),
        ("LINEAFTER", (0, 0), (0, -1), 0.5, INK),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, INK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 2),
    ]
    for row in range(1, row_count + 1):
        style.append(("LINEBELOW", (1, row), (1, row), 0.35, colors.grey))
    table.setStyle(TableStyle(style))
    content: list[Flowable] = [table]
    if include_legal_notice:
        content.extend(
            [
                Spacer(1, 8 * mm),
                Paragraph("Independent practice material", STYLES["small"]),
                Paragraph(
                    "Created by Paper Creator for private revision. This paper is not "
                    "produced, endorsed or approved by AQA or any examination board.",
                    STYLES["small"],
                ),
            ]
        )
    return content


def _paper_one_section_b_pages(
    section,
    option: GeneratedOption,
) -> list[list[Flowable]]:
    question_14_1, question_14_2, question_15_1, question_15_2, question_15_3 = (
        option.questions
    )
    return [
        [*_intro(section), _company_statement_case(option)],
        [
            _question_table(question_14_1),
            Spacer(1, 3 * mm),
            Paragraph(
                f"<b>{option.title}</b><br/>Income statement for the year ended",
                STYLES["centre_bold"],
            ),
            AnswerLines(25),
        ],
        [AnswerLines(34)],
        [
            _question_table(question_14_2),
            Spacer(1, 4 * mm),
            AnswerLines(29),
        ],
        [
            _partnership_case(option),
            Spacer(1, 4 * mm),
            _question_table(question_15_1),
            Spacer(1, 3 * mm),
            _partners_capital_table(),
        ],
        [
            Paragraph("Workings", STYLES["small"]),
            AnswerLines(12),
            Spacer(1, 14 * mm),
            Paragraph("Question 15 continues on the next page", STYLES["centre_bold"]),
        ],
        [_partnership_drawings_case(option)],
        [
            _question_table(question_15_2),
            Spacer(1, 3 * mm),
            _appropriation_answer_table(),
        ],
        [
            Paragraph("Workings", STYLES["small"]),
            AnswerLines(20),
        ],
        [
            _question_table(question_15_3),
            Spacer(1, 4 * mm),
            AnswerLines(29),
        ],
    ]


def _company_statement_case(option: GeneratedOption) -> Table:
    values = option.chart_values
    damaged_cost = int(values[0] * 760)
    damaged_sale = int(damaged_cost * 0.72)
    damaged_repair = int(damaged_cost * 0.14)
    roof_repair = int(values[1] * 84)
    insurance_claim = int(roof_repair * 0.88)
    receivable = int(values[4] * 1_980)
    supplier_invoice = int(values[2] * 31)
    debenture = int(values[4] * 21_000)
    earlier_debenture = int(values[3] * 13_000)
    tax_opening = int(values[0] * 36)
    tax_paid = int(values[1] * 88)
    rows = [
        ["Administration expenses", f"{int(values[0] * 4_000):,}"],
        ["Cost of sales", f"{int(values[4] * 34_000):,}"],
        ["Marketing expenses", f"{int(values[1] * 8_000):,}"],
        ["Revenue", f"{int(values[4] * 58_000):,}"],
        ["Warehouse expenses", f"{int(values[2] * 9_000):,}"],
    ]
    figures = Table(
        [["", "£"], *rows],
        colWidths=[72 * mm, 30 * mm],
        rowHeights=[10 * mm] * 6,
        style=TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, INK),
                ("FONT", (0, 0), (-1, 0), FONT_BOLD),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        ),
    )
    figures.hAlign = "CENTER"
    adjustments = [
        (
            f"Closing inventory includes damaged items which cost £{damaged_cost:,}. "
            f"They can be sold for £{damaged_sale:,} after repairs costing £{damaged_repair:,}. "
            "The closing inventory figure has not been adjusted for this information."
        ),
        (
            f"Warehouse expenses include a roof repair costing £{roof_repair:,}. "
            f"The insurer has agreed to pay £{insurance_claim:,} of the claim. No entry "
            "has been made for the insurance proceeds."
        ),
        (
            f"A credit customer owing £{receivable:,} was declared bankrupt before "
            "the year end. The company expects to receive 10p for every £1 due. "
            "Irrecoverable debts are charged to administration expenses."
        ),
        (
            f"After the year end, an invoice for £{supplier_invoice:,} was received "
            "for marketing services supplied during this accounting year. It was dated "
            "before the reporting date but has not been entered in the accounting records."
        ),
    ]
    additional = [
        (
            f"A £{debenture:,}, 6% debenture was issued four months before the year end. "
            "No finance cost has yet been recorded."
        ),
        (
            f"An earlier £{earlier_debenture:,}, 8% debenture was repaid in full "
            "two months before the year end. The annual interest had been paid in advance."
        ),
        (
            f"At the start of the year, tax owed was £{tax_opening:,}. During the year "
            f"£{tax_paid:,} was paid. The current-year tax charge is still to be recorded."
        ),
    ]
    case = Table(
        [
            [
                Paragraph(
                    f"The accountant for {option.title} has provided information for "
                    "the preparation of the income statement for the year.",
                    STYLES["body"],
                )
            ],
            [figures],
            [
                Paragraph(
                    "<b>The following have not yet been accounted for:</b><br/>"
                    + "<br/>".join(f"• {item}" for item in adjustments),
                    STYLES["body"],
                )
            ],
            [
                Paragraph(
                    "<b>Additional information</b><br/>"
                    + "<br/>".join(f"{index}. {item}" for index, item in enumerate(additional, 1)),
                    STYLES["body"],
                )
            ],
        ],
        colWidths=[153 * mm],
        style=TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.65, INK),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        ),
    )
    return Table(
        [[_question_reference("14"), case]],
        colWidths=[14 * mm, 153 * mm],
        style=TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        ),
    )


def _partnership_case(option: GeneratedOption) -> Table:
    capital = [int(value * 210) for value in option.chart_values[:3]]
    text = (
        f"Alex, Morgan and Riley have been in partnership for several years. During the "
        f"accounting year Riley retired because the partners found decision-making difficult.<br/><br/>"
        f"The partners kept separate capital and current accounts. Their capital balances "
        f"were Alex £{capital[0]:,}, Morgan £{capital[1]:,} and Riley £{capital[2]:,}.<br/><br/>"
        "On retirement, goodwill was valued but was not to remain in the books. Alex and "
        "Morgan agreed target capital balances and withdrew the required cash. Profits and "
        "losses were shared in the agreed ratio."
    )
    case = Table(
        [[Paragraph(text, STYLES["small"])]],
        colWidths=[153 * mm],
        style=TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.65, INK),
                ("PADDING", (0, 0), (-1, -1), 7),
            ]
        ),
    )
    return Table(
        [[_question_reference("15"), case]],
        colWidths=[14 * mm, 153 * mm],
        style=TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        ),
    )


def _partners_capital_table() -> Table:
    headers = ["Date", "Details", "Alex\n£", "Morgan\n£", "Date", "Details", "Alex\n£", "Morgan\n£"]
    data = [headers, *[[""] * 8 for _ in range(6)]]
    table = Table(
        data,
        colWidths=[18 * mm, 30 * mm, 18 * mm, 18 * mm, 18 * mm, 30 * mm, 18 * mm, 18 * mm],
        rowHeights=[10 * mm, *([9 * mm] * 6)],
    )
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.45, INK),
                ("FONT", (0, 0), (-1, 0), FONT_BOLD, 7.5),
                ("ALIGN", (2, 0), (3, -1), "CENTER"),
                ("ALIGN", (6, 0), (7, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return Table(
        [
            [Paragraph("<b>Dr</b>", STYLES["small"]), Paragraph("<b>Capital Accounts</b>", STYLES["centre_bold"]), Paragraph("<b>Cr</b>", STYLES["marks"])],
            [table, "", ""],
        ],
        colWidths=[8 * mm, 151 * mm, 8 * mm],
        style=TableStyle(
            [
                ("SPAN", (0, 1), (-1, 1)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 0),
            ]
        ),
    )


def _partnership_drawings_case(option: GeneratedOption) -> Table:
    values = [int(value * 145) for value in option.chart_values[:3]]
    drawings = Table(
        [
            ["", "Alex\n£", "Morgan\n£", "Riley\n£"],
            ["First period", f"{values[0]:,}", f"{values[1]:,}", f"{values[2]:,}"],
            ["Second period", f"{values[0] // 3:,}", f"{values[1] // 2:,}", "—"],
        ],
        colWidths=[70 * mm, 27 * mm, 27 * mm, 27 * mm],
        style=TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, INK),
                ("FONT", (0, 0), (-1, 0), FONT_BOLD),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        ),
    )
    case = Table(
        [
            [
                Paragraph(
                    "The partnership agreement states that Morgan receives an annual salary, "
                    "interest is allowed on capital and charged on drawings, and remaining "
                    "profit is shared in the agreed ratio.",
                    STYLES["body"],
                )
            ],
            [Paragraph("<b>Drawings for the year were:</b>", STYLES["small"])],
            [drawings],
            [
                Paragraph(
                    "Profit accrues evenly throughout the year. Use the relevant time "
                    "apportionment when preparing the appropriation account.",
                    STYLES["small"],
                )
            ],
        ],
        colWidths=[153 * mm],
        style=TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.65, INK),
                ("PADDING", (0, 0), (-1, -1), 7),
            ]
        ),
    )
    return Table(
        [[_question_reference("15.2"), case]],
        colWidths=[14 * mm, 153 * mm],
        style=TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        ),
    )


def _appropriation_answer_table() -> Table:
    data = [
        [
            Paragraph("<b>Profit and loss appropriation account</b>", STYLES["centre_bold"]),
            Paragraph("<b>First period<br/>£</b>", STYLES["marks"]),
            Paragraph("<b>Second period<br/>£</b>", STYLES["marks"]),
        ],
        *( [["", "", ""] for _ in range(15)] ),
    ]
    table = Table(
        data,
        colWidths=[70 * mm, 48.5 * mm, 48.5 * mm],
        rowHeights=[12 * mm, *([9 * mm] * 15)],
    )
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.45, INK),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def _paper_one_section_a_case_pages(
    option: GeneratedOption,
) -> list[list[Flowable]]:
    question_11, question_12, question_13_1, question_13_2 = option.questions[10:]
    return [
        _question_page(question_11, option, lines=18),
        _do_not_write_page(),
        [_non_current_asset_case(option)],
        [
            _question_table(question_12),
            Spacer(1, 4 * mm),
            Paragraph(
                f"<b>{option.title}</b><br/>Statement of financial position "
                "(extract) at the year end",
                STYLES["centre_bold"],
            ),
            Spacer(1, 3 * mm),
            AnswerLines(12),
            Paragraph("Workings", STYLES["small"]),
            AnswerLines(16),
        ],
        [_sales_ledger_case(option)],
        [
            _question_table(question_13_1),
            Spacer(1, 3 * mm),
            _ledger_answer_table("Sales Ledger Control Account", 8),
            Spacer(1, 5 * mm),
            _question_table(question_13_2),
            Spacer(1, 3 * mm),
            _ledger_answer_table("Sales Account", 4),
        ],
    ]


def _do_not_write_page() -> list[Flowable]:
    drawing = Drawing(167 * mm, 226 * mm)
    drawing.add(
        Line(
            0,
            0,
            167 * mm,
            226 * mm,
            strokeColor=INK,
            strokeWidth=0.7,
        )
    )
    drawing.add(
        String(
            83.5 * mm,
            113 * mm,
            "DO NOT WRITE ON THIS PAGE",
            fontName=FONT_BOLD,
            fontSize=11,
            textAnchor="middle",
        )
    )
    drawing.add(
        String(
            83.5 * mm,
            107 * mm,
            "ANSWER IN THE SPACES PROVIDED",
            fontName=FONT_BOLD,
            fontSize=11,
            textAnchor="middle",
        )
    )
    return [
        Paragraph("Turn over for the next question", STYLES["centre_bold"]),
        Spacer(1, 3 * mm),
        drawing,
    ]


def _non_current_asset_case(option: GeneratedOption) -> Table:
    values = [int(round(value * 1000)) for value in option.chart_values]
    plant_cost = values[4]
    plant_depreciation = int(round(values[1] * 0.48))
    vehicle_cost = int(round(values[3] * 1.55))
    vehicle_depreciation = int(round(values[0] * 0.62))
    case_rows: list[list[object]] = [
        [
            Paragraph(
                f"<b>{option.title}</b>, a sole trader, provided the following information.",
                STYLES["body"],
            ),
            "",
        ],
        [
            Paragraph("<b>Non-current assets</b>", STYLES["small"]),
            Paragraph("<b>At the start of the year<br/>£</b>", STYLES["marks"]),
        ],
        ["Plant and machinery — cost", f"{plant_cost:,}"],
        ["Less: accumulated depreciation", f"{plant_depreciation:,}"],
        ["Motor vehicles — cost", f"{vehicle_cost:,}"],
        ["Less: accumulated depreciation", f"{vehicle_depreciation:,}"],
    ]
    information = [
        f"1. A machine costing £{int(values[2] * 0.18):,} was purchased during the year.",
        f"2. A motor vehicle costing £{int(values[1] * 0.22):,} was sold during the year.",
        "3. Plant and machinery is depreciated using the straight-line method.",
        "4. Motor vehicles are depreciated using the reducing-balance method.",
        "5. A full year's depreciation is charged in the year of purchase.",
    ]
    case_rows.append(
        [
            Paragraph(
                "<b>Additional information</b><br/><br/>"
                + "<br/>".join(information),
                STYLES["small"],
            ),
            "",
        ]
    )
    table = Table(case_rows, colWidths=[142 * mm, 25 * mm])
    table.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (-1, 0)),
                ("SPAN", (0, -1), (-1, -1)),
                ("GRID", (0, 1), (-1, -2), 0.5, INK),
                ("BOX", (0, 0), (-1, -1), 0.65, INK),
                ("BACKGROUND", (0, 1), (-1, 1), GREY),
                ("ALIGN", (1, 2), (1, -2), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return Table(
        [[_question_reference("12"), table]],
        colWidths=[14 * mm, 153 * mm],
        style=TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        ),
    )


def _sales_ledger_case(option: GeneratedOption) -> Table:
    values = [int(round(value * 1000)) for value in option.chart_values]
    sales = int(values[4] * 1.9)
    returns = max(100, int(values[0] * 0.006))
    receipts = int(sales * 0.86)
    discount = max(100, int(sales * 0.006))
    journal_style = TableStyle(
        [
            ("GRID", (0, 0), (-1, -1), 0.5, INK),
            ("BACKGROUND", (0, 0), (-1, 0), GREY),
            ("FONT", (0, 0), (-1, 0), FONT_BOLD),
            ("ALIGN", (2, 1), (2, -1), "RIGHT"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]
    )
    sales_table = Table(
        [["Date", "Detail", "£"], ["Year end", "Total for year", f"{sales:,}"]],
        colWidths=[38 * mm, 48 * mm, 26 * mm],
        style=journal_style,
    )
    returns_table = Table(
        [["Date", "Detail", "£"], ["Year end", "Total for year", f"{returns:,}"]],
        colWidths=[38 * mm, 48 * mm, 26 * mm],
        style=journal_style,
    )
    case = Table(
        [
            [
                Paragraph(
                    f"<b>{option.title}</b>, a sole trader, provided the following extracts "
                    "from the books of prime entry for the year.",
                    STYLES["body"],
                )
            ],
            [Paragraph("<b>Sales journal</b>", STYLES["centre_bold"])],
            [sales_table],
            [Paragraph("<b>Sales returns journal</b>", STYLES["centre_bold"])],
            [returns_table],
            [
                Paragraph(
                    f"During the year {option.title} received £{receipts:,} from credit "
                    f"customers after allowing cash discount of £{discount:,}.",
                    STYLES["small"],
                )
            ],
        ],
        colWidths=[153 * mm],
        style=TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.65, INK),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 7),
            ]
        ),
    )
    return Table(
        [[_question_reference("13"), case]],
        colWidths=[14 * mm, 153 * mm],
        style=TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        ),
    )


def _ledger_answer_table(title: str, rows: int) -> Table:
    data = [
        [
            Paragraph("<b>Dr</b>", STYLES["small"]),
            Paragraph(f"<b>{title}</b>", STYLES["centre_bold"]),
            "",
            "",
            "",
            Paragraph("<b>Cr</b>", STYLES["marks"]),
        ],
        ["Date", "Details", "£", "Date", "Details", "£"],
    ]
    data.extend([["", "", "", "", "", ""] for _ in range(rows)])
    table = Table(
        data,
        colWidths=[20 * mm, 45 * mm, 18.5 * mm, 20 * mm, 45 * mm, 18.5 * mm],
        rowHeights=[7 * mm, *([8 * mm] * (rows + 1))],
    )
    table.setStyle(
        TableStyle(
            [
                ("SPAN", (1, 0), (4, 0)),
                ("GRID", (0, 1), (-1, -1), 0.45, INK),
                ("FONT", (0, 1), (-1, 1), FONT_BOLD, 8.5),
                ("ALIGN", (2, 1), (2, -1), "RIGHT"),
                ("ALIGN", (5, 1), (5, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def _question_page(
    question: GeneratedQuestion, option: GeneratedOption, lines: int
) -> list[Flowable]:
    content: list[Flowable] = [
        _question_table(question),
        Spacer(1, 4 * mm),
    ]
    if question.kind == "calculation":
        content.extend([_accounting_table(option), Spacer(1, 4 * mm)])
    content.append(AnswerLines(lines))
    return content


def _mcq_block(question: GeneratedQuestion) -> list[Flowable]:
    choices = Table(
        [
            [
                Paragraph(f"<b>{'ABCD'[index]}</b>", STYLES["choices"]),
                Paragraph(text, STYLES["choices"]),
                _lozenge(),
            ]
            for index, text in enumerate(question.choices)
        ],
        colWidths=[9 * mm, 119 * mm, 12 * mm],
        style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]),
    )
    return [
        KeepTogether(
            [
                _question_table(question),
                Spacer(1, 2 * mm),
                choices,
                Spacer(1, 6 * mm),
            ]
        )
    ]


def _question_table(question: GeneratedQuestion) -> Table:
    label = "mark" if question.marks == 1 else "marks"
    return Table(
        [[
            _question_reference(question.number),
            Paragraph(question.prompt, STYLES["body"]),
            Paragraph(f"[{question.marks} {label}]", STYLES["marks"]),
        ]],
        colWidths=[14 * mm, 134 * mm, 19 * mm],
        style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]),
    )


def _question_reference(number: str) -> Table:
    compact = "".join(character for character in number if character.isdigit())
    cells = list(compact.zfill(2)) if len(compact) <= 2 else [number]
    return Table(
        [cells],
        colWidths=[5.5 * mm] * len(cells),
        rowHeights=[5.5 * mm],
        style=TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.55, INK),
            ("FONT", (0, 0), (-1, -1), FONT_BOLD, 9),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 0),
        ]),
    )


def _lozenge() -> Drawing:
    drawing = Drawing(25, 15)
    drawing.add(Rect(1, 1, 22, 13, strokeColor=INK, fillColor=None, strokeWidth=0.7))
    drawing.add(Ellipse(12, 7.5, 4, 2.2, strokeColor=INK, fillColor=None, strokeWidth=0.6))
    return drawing


def _accounting_table(option: GeneratedOption) -> Table:
    values = option.chart_values
    rows = [
        ["Accounting information", "£000"],
        ["Revenue / activity index", f"{values[4]:.1f}"],
        ["Variable-cost index", f"{values[2]:.1f}"],
        ["Fixed-cost index", f"{values[1]:.1f}"],
        ["Comparative figure", f"{values[0]:.1f}"],
    ]
    table = Table(rows, colWidths=[110 * mm, 45 * mm])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, INK),
        ("BACKGROUND", (0, 0), (-1, 0), GREY),
        ("FONT", (0, 0), (-1, 0), FONT_BOLD),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def _scheme_block(question: GeneratedQuestion) -> list[Flowable]:
    rows = [[
        Paragraph(f"<b>{question.number}</b> {question.prompt}", STYLES["body"]),
        str(question.marks),
    ]]
    rows.extend(
        [[Paragraph(f"• {point}", STYLES["small"]), ""] for point in question.mark_scheme]
    )
    table = Table(rows, colWidths=[155 * mm, 12 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), GREY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    return [table, Spacer(1, 4 * mm)]


def _intro(section) -> list[Flowable]:
    return [
        Table(
            [
                [Paragraph(f"<b>Section {section.id}</b>", STYLES["centre_bold"])],
                [Paragraph(section.instructions, STYLES["instruction"])],
            ],
            colWidths=[167 * mm],
            style=TableStyle(
                [
                    ("LINEBELOW", (0, -1), (-1, -1), 0.65, INK),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            ),
        ),
        Spacer(1, 4 * mm),
    ]


def _cover(paper: GeneratedPaper) -> list[Flowable]:
    return aqa_question_cover(_cover_profile(paper), FONT, FONT_BOLD)


def _cover_profile(paper: GeneratedPaper) -> CoverProfile:
    return CoverProfile(
        board="aqa",
        subject="Accounting",
        code=paper.paper_code,
        paper_title=f"Paper {paper.paper_id[-1]}  {paper.title}",
        duration="3 hours",
        total_marks=paper.total_marks,
        materials=(
            "For this paper you must have a calculator.",
        ),
        instructions=(
            "Use black ink or black ball-point pen.",
            "Fill in the boxes at the top of this page.",
            "Answer all questions.",
            "Answer in the spaces provided. Do not write outside the box around each page or on blank pages.",
            "Use the lined pages at the end if you need extra space and write the question number against your answer.",
            "Cross through any rough work you do not want to be marked.",
        ),
        information=(
            "The marks for questions are shown in brackets.",
        ),
        mark_rows=tuple(
            (
                section.id,
                sum(question.marks for question in section.options[0].questions),
            )
            for section in paper.sections
        ),
    )


def _document(path: Path, paper: GeneratedPaper, kind: str) -> BaseDocTemplate:
    doc = BaseDocTemplate(
        str(path),
        pagesize=AQA_A4,
        leftMargin=18 * mm,
        rightMargin=17 * mm,
        topMargin=19 * mm,
        bottomMargin=18 * mm,
        title=f"{paper.paper_code} {paper.title} — {kind}",
        author="Paper creator",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")
    doc.addPageTemplates(
        PageTemplate(
            id="aqa-accounting-practice",
            frames=[frame],
            onPage=lambda canvas, value: _chrome(
                canvas, value, paper.paper_code, kind
            ),
        )
    )
    return doc


def _chrome(canvas, doc, code: str, kind: str) -> None:
    canvas.saveState()
    if kind == "Question paper" and doc.page > 1:
        canvas.setStrokeColor(colors.HexColor("#666666"))
        canvas.setLineWidth(0.45)
        canvas.rect(14 * mm, 15 * mm, 184 * mm, 267 * mm, stroke=1, fill=0)
        canvas.setFillColor(INK)
        canvas.setFont(FONT, 9)
        canvas.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 10 * mm, str(doc.page))
        canvas.setFont(FONT, 5.8)
        canvas.drawString(198.5 * mm, PAGE_HEIGHT - 19 * mm, "Do not write")
        canvas.drawString(198.5 * mm, PAGE_HEIGHT - 22 * mm, "outside the")
        canvas.drawString(198.5 * mm, PAGE_HEIGHT - 25 * mm, "box")
        canvas.setFont(FONT_BOLD, 9)
        if code == "7127/1" and doc.page == 32:
            canvas.drawCentredString(PAGE_WIDTH / 2, 17 * mm, "END OF QUESTIONS")
        elif code != "7127/1" or doc.page < 32:
            canvas.drawRightString(PAGE_WIDTH - 13 * mm, 11 * mm, "Turn over >")
        canvas.setFont(FONT, 6.5)
        canvas.drawString(14 * mm, 9 * mm, f"PRACTICE/{code}")
        canvas.restoreState()
        return
    canvas.setStrokeColor(colors.HexColor("#aaaaaa"))
    canvas.line(
        18 * mm, PAGE_HEIGHT - 13 * mm, PAGE_WIDTH - 17 * mm, PAGE_HEIGHT - 13 * mm
    )
    canvas.setFont(FONT, 7.5)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(18 * mm, PAGE_HEIGHT - 10 * mm, f"{code} · {kind}")
    canvas.drawRightString(PAGE_WIDTH - 17 * mm, 9 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _banner(text: str) -> Table:
    return Table(
        [[Paragraph(text, STYLES["banner"])]],
        colWidths=[167 * mm],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), INK),
            ("PADDING", (0, 0), (-1, -1), 7),
        ]),
    )


def _box(text: str) -> Table:
    return Table(
        [[Paragraph(text, STYLES["body"])]],
        colWidths=[150 * mm],
        style=TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.6, INK),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f7f7f7")),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]),
    )


class AnswerLines(Flowable):
    def __init__(self, count: int) -> None:
        super().__init__()
        self.width = 167 * mm
        self.height = count * 6.0 * mm
        self.count = count

    def draw(self) -> None:
        self.canv.setStrokeColor(colors.HexColor("#b5b5b5"))
        self.canv.setLineWidth(0.35)
        for index in range(self.count):
            y = self.height - (index + 1) * 6.0 * mm
            self.canv.line(0, y, self.width, y)


_base = getSampleStyleSheet()
STYLES = {
    "body": ParagraphStyle("body", parent=_base["BodyText"], fontName=FONT, fontSize=11, leading=14),
    "small": ParagraphStyle("small", parent=_base["BodyText"], fontName=FONT, fontSize=9.0, leading=12),
    "scheme_small": ParagraphStyle("scheme_small", parent=_base["BodyText"], fontName=FONT, fontSize=8.1, leading=9.7),
    "heading": ParagraphStyle("heading", parent=_base["Heading3"], fontName=FONT_BOLD, fontSize=11, leading=14),
    "kicker": ParagraphStyle("kicker", parent=_base["Heading2"], fontName=FONT_BOLD, fontSize=15, leading=18),
    "title": ParagraphStyle("title", parent=_base["Title"], fontName=FONT_BOLD, fontSize=23, leading=27),
    "subtitle": ParagraphStyle("subtitle", parent=_base["Heading2"], fontName=FONT, fontSize=14, leading=18),
    "banner": ParagraphStyle("banner", parent=_base["Heading2"], fontName=FONT_BOLD, fontSize=12, leading=15, textColor=colors.white),
    "instruction": ParagraphStyle("instruction", parent=_base["BodyText"], fontName=FONT_BOLD, fontSize=10.5, leading=14),
    "option": ParagraphStyle("option", parent=_base["Heading3"], fontName=FONT_BOLD, fontSize=11.5, leading=15),
    "extract": ParagraphStyle("extract", parent=_base["BodyText"], fontName=FONT, fontSize=9.3, leading=12, borderWidth=0.4, borderColor=colors.grey, borderPadding=5),
    "marks": ParagraphStyle("marks", parent=_base["BodyText"], fontName=FONT_BOLD, fontSize=9.5, leading=13, alignment=TA_RIGHT),
    "choices": ParagraphStyle("choices", parent=_base["BodyText"], fontName=FONT, fontSize=11, leading=17, leftIndent=22),
    "answer": ParagraphStyle("answer", parent=_base["BodyText"], fontName=FONT_BOLD, fontSize=9.5, leading=12, alignment=TA_RIGHT),
    "centre_bold": ParagraphStyle("centre", parent=_base["Heading3"], fontName=FONT_BOLD, fontSize=10.5, leading=14, alignment=TA_CENTER),
}
