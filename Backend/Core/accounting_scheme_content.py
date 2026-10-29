"""Versioned printed-content checks for the compact Accounting Paper 1 scheme."""

from __future__ import annotations

import html
import json
import re
from decimal import Decimal
from pathlib import Path

import pymupdf

from Backend.Core.exam_blueprints import GeneratedPaper, GeneratedQuestion
from Backend.Core.layout_master import LayoutConformanceError
from Backend.Core.subjects.accounting import solve_accounting_calculation

ACCOUNTING_SCHEME_PAGINATION = "generated-aqa-accounting-paper1-credit-v1"
ACCOUNTING_SCHEME_PAGES = 24

# One source-owned case per range; front matter occupies pages 1-8.
_CASE_PAGES = {
    "11": (8, 9),
    "12": (9, 10),
    "13.1": (10, 11),
    "13.2": (11, 12),
    "14.1": (12, 15),
    "14.2": (15, 17),
    "15.1": (17, 18),
    "15.2": (18, 19),
    "15.3": (19, 20),
    "16": (20, 22),
    "17": (22, 24),
}


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", html.unescape(text)).replace("−", "-")


def _require_paper_shape(paper: GeneratedPaper) -> None:
    from aqaaccountgen.configs import RULES
    from aqaaccountgen.generator import _number

    rule = RULES["paper_1"]
    if (
        paper.paper_id != rule.id
        or paper.paper_code != rule.code
        or paper.total_marks != rule.total_marks
        or paper.duration_minutes != rule.duration_minutes
        or [section.id for section in paper.sections]
        != [section.id for section in rule.sections]
    ):
        raise LayoutConformanceError(
            "Accounting scheme has a different paper structure"
        )
    for section, section_rule in zip(paper.sections, rule.sections, strict=True):
        if len(section.options) != 1:
            raise LayoutConformanceError(
                "Accounting scheme requires one option per section"
            )
        actual = [
            (q.number, q.rule_id, q.kind, q.marks, q.assessment_objectives)
            for q in section.options[0].questions
        ]
        expected = [
            (
                _number(rule.id, section_rule.id, index),
                q.id,
                q.kind,
                q.marks,
                q.assessment_objectives,
            )
            for index, q in enumerate(section_rule.questions)
        ]
        if actual != expected:
            raise LayoutConformanceError(
                "Accounting scheme has missing, repeated or reassigned question parts"
            )


def _require_printed_table(
    tables: list[list[list[str | None]]],
    headings: list[str],
    expected: list[list[str]],
    question_number: str,
    *,
    award_columns: bool = False,
) -> None:
    def normalise(row):
        return [_compact(cell or "") for cell in row]

    candidates = [
        table
        for table in tables
        if table and normalise(table[0]) == normalise(headings)
    ]
    if len(candidates) != 1:
        raise LayoutConformanceError(
            f"Accounting scheme omits or repeats the credit table for {question_number}"
        )
    rows = candidates[0][1:]
    if award_columns:
        rows = [[row[0], row[-1]] for row in rows]
    if [normalise(row) for row in rows] != [normalise(row) for row in expected]:
        raise LayoutConformanceError(
            f"Accounting scheme printed awards differ for {question_number}"
        )


def _amount(value: object, *, deduction: bool = False) -> str:
    number = Decimal(str(value))
    if not number.is_finite() or number != number.to_integral_value():
        raise LayoutConformanceError(
            "Accounting printed table needs an exact whole-pound result"
        )
    text = f"{int(number):,}"
    return f"({text})" if deduction else text


def _calculation_table(
    question: GeneratedQuestion, solution: dict
) -> tuple[list[str], list[list[str]]]:
    """Bind printed roles and signs to the independent candidate-input solver.

    These finite display contracts contain no renderer case objects or worked
    formulae. The solver supplies results; the question supplies raw postings.
    """
    from aqaaccountgen.marking_policy import printed_award_rows

    values = solution["numeric_results"]
    context = question.authoring_context
    rule = question.rule_id
    if rule == "statement_extract":
        awards = dict(printed_award_rows(question))
        return (
            [
                "Non-current assets",
                "Cost £",
                "Accumulated depreciation £",
                "Carrying amount £",
                "Marks",
            ],
            [
                [
                    "Plant and machinery",
                    _amount(values["plant_cost"]),
                    _amount(values["plant_accumulated_depreciation"], deduction=True),
                    _amount(values["plant_carrying_amount"]),
                    awards["Plant and machinery"],
                ],
                [
                    "Motor vehicles",
                    _amount(values["motor_cost"]),
                    _amount(values["motor_accumulated_depreciation"], deduction=True),
                    _amount(values["motor_carrying_amount"]),
                    awards["Motor vehicles"],
                ],
                [
                    "Total non-current assets",
                    "",
                    "",
                    _amount(values["total_carrying_amount"]),
                    awards["Total non-current assets"],
                ],
            ],
        )
    if rule in {"ledger_calculation", "accounting_concept"}:
        data = context["source_data"]
        headings = ["Date", "Details", "£", "Date", "Details", "£"]
        if rule == "accounting_concept":
            return headings, [
                [
                    "31 Dec",
                    "Sales returns",
                    _amount(data["sales_returns"]),
                    "31 Dec",
                    "Sales journal",
                    _amount(data["gross_credit_sales"]),
                ],
                [
                    "31 Dec",
                    "Income statement",
                    _amount(values["net_sales_transferred_to_income_statement"]),
                    "",
                    "",
                    "",
                ],
                [
                    "",
                    "",
                    _amount(data["gross_credit_sales"]),
                    "",
                    "",
                    _amount(data["gross_credit_sales"]),
                ],
            ]
        return headings, [
            [
                "1 Jan",
                "Balance b/d",
                _amount(data["opening_trade_receivables"]),
                "31 Dec",
                "Bank",
                _amount(data["cash_received_from_credit_customers"]),
            ],
            [
                "31 Dec",
                "Sales",
                _amount(data["credit_sales"]),
                "31 Dec",
                "Sales returns",
                _amount(data["sales_returns"]),
            ],
            [
                "",
                "",
                "",
                "31 Dec",
                "Discount allowed",
                _amount(data["discount_allowed"]),
            ],
            [
                "",
                "",
                "",
                "31 Dec",
                "Balance c/d",
                _amount(values["closing_trade_receivables"]),
            ],
            [
                "",
                "",
                _amount(values["account_total"]),
                "",
                "",
                _amount(values["account_total"]),
            ],
            [
                "1 Jan",
                "Balance b/d",
                _amount(values["closing_trade_receivables"]),
                "",
                "",
                "",
            ],
        ]
    if rule == "company_statement":
        awards = dict(printed_award_rows(question))
        roles = [
            ("Revenue", "revenue", False, 1),
            ("Cost of sales", "adjusted_cost_of_sales", True, 1),
            ("Gross profit", "gross_profit", False, 2),
            ("Administration expenses", "adjusted_administration_expenses", True, 1),
            ("Marketing expenses", "adjusted_marketing_expenses", True, 1),
            ("Warehouse expenses", "warehouse_expenses", True, 1),
            ("Other income – insurance claim", "insurance_claim", False, 1),
            ("Finance costs", "finance_cost", True, 1),
            ("Profit before tax", "profit_before_tax", False, 2),
            ("Taxation", "taxation", True, 1),
            ("Profit for the year", "profit_for_year", False, 2),
        ]
        rows = []
        for label, role, deduction, column in roles:
            row = [label, "", "", awards.get(label, "")]
            row[column] = _amount(values[role], deduction=deduction)
            rows.append(row)
        return ["", "£", "£", "Marks"], rows
    if rule == "partnership_1":
        data = context["source_data"]
        return [
            "Date",
            "Details",
            "Alex £",
            "Morgan £",
            "Date",
            "Details",
            "Alex £",
            "Morgan £",
        ], [
            [
                "31 Aug",
                "Goodwill written off",
                _amount(values["Alex_goodwill_write_off"]),
                _amount(values["Morgan_goodwill_write_off"]),
                "1 Jan",
                "Balance b/d",
                _amount(data["opening_capital"]["Alex"]),
                _amount(data["opening_capital"]["Morgan"]),
            ],
            [
                "31 Aug",
                "Bank",
                _amount(values["Alex_cash_withdrawn"]),
                _amount(values["Morgan_cash_withdrawn"]),
                "31 Aug",
                "Goodwill",
                _amount(values["Alex_goodwill_credit"]),
                _amount(values["Morgan_goodwill_credit"]),
            ],
            [
                "31 Dec",
                "Balance c/d",
                _amount(values["Alex_closing_capital"]),
                _amount(values["Morgan_closing_capital"]),
                "",
                "",
                "",
                "",
            ],
        ]
    if rule == "partnership_2":
        awards = dict(printed_award_rows(question))
        roles = [
            ("Profit for the period", "profit", False),
            ("Interest on drawings", "drawings_interest", False),
            ("Interest on capital", "capital_interest_total", True),
            ("Morgan's salary", "salary", True),
            ("Residual profit", "residual_profit", False),
            ("Alex's share", "Alex_profit_share", False),
            ("Morgan's share", "Morgan_profit_share", False),
        ]
        rows = []
        for label, role, deduction in roles:
            cells = []
            for period in ("first_period", "second_period"):
                if role == "capital_interest_total":
                    value = sum(
                        Decimal(str(value))
                        for key, value in values.items()
                        if key.startswith(period + "_")
                        and key.endswith("_capital_interest")
                    )
                else:
                    value = values[f"{period}_{role}"]
                cells.append(_amount(value, deduction=deduction))
            rows.append([label, *cells, awards[label]])
        rows.append(
            [
                "Riley's share",
                _amount(values["first_period_Riley_profit_share"]),
                "—",
                awards["Riley's share"],
            ]
        )
        return ["", "First period £", "Second period £", "Marks"], rows
    raise LayoutConformanceError(
        f"Accounting scheme has no printed calculation contract for {rule}"
    )


def verify_accounting_scheme(
    pdf_path: Path,
    assessment_path: Path | None,
    reference_count: int,
) -> dict | None:
    """Return None only for an unmarked legacy package, retaining its old count."""
    if assessment_path is None:
        return None
    from aqaaccountgen.marking_policy import (
        EXPLICIT_RULES,
        MARKING_POLICY_ID,
        explicit_credit_points,
        indicative_content,
        printed_award_rows,
        printed_level_rows,
        printed_mcq_rows,
    )

    from Backend.Core.assessment_package import _extract_items

    package = json.loads(assessment_path.read_text(encoding="utf-8"))
    blueprint = package.get("blueprint") or {}
    paper = GeneratedPaper.model_validate(blueprint)
    questions = [
        q
        for section in paper.sections
        for option in section.options
        for q in option.questions
    ]
    declared = [
        q for q in questions if "accounting_marking_policy" in q.authoring_context
    ]
    if not declared:
        return None
    if (
        package.get("subject") not in {"accounting_aqa", "accounting", "aqa/accounting"}
        or str(package.get("paper")) != "1"
    ):
        raise LayoutConformanceError(
            "Accounting scheme policy cannot apply to this package"
        )
    items = _extract_items(blueprint, subject=package["subject"], paper_number="1")
    if package.get("items") != items or len(questions) != 21:
        raise LayoutConformanceError(
            "Accounting scheme requires its complete matching assessed items"
        )
    _require_paper_shape(paper)
    for question in questions:
        if question.rule_id in EXPLICIT_RULES:
            if (
                question.authoring_context.get("accounting_marking_policy")
                != MARKING_POLICY_ID
            ):
                raise LayoutConformanceError(
                    "Accounting scheme has an unknown or missing credit policy"
                )
            explicit_credit_points(question)
    if {
        q.number for q in questions if q.kind != "multiple_choice"
    } != _CASE_PAGES.keys():
        raise LayoutConformanceError(
            "Accounting scheme has missing or repeated case parts"
        )
    checked_statements = 0
    quiet_tables = getattr(pymupdf, "no_recommend_layout", None)
    if not callable(quiet_tables) or not callable(
        getattr(pymupdf.Page, "find_tables", None)
    ):
        raise LayoutConformanceError(
            "Accounting credit-table validation requires the pinned PyMuPDF build (1.28.2)"
        )
    # Suppress only the optional layout-package advertisement, never diagnostics
    # or the bridge's JSON event stream.
    quiet_tables()
    with pymupdf.open(pdf_path) as document:
        if len(document) != ACCOUNTING_SCHEME_PAGES:
            raise LayoutConformanceError(
                f"Accounting compact scheme requires exactly {ACCOUNTING_SCHEME_PAGES} pages"
            )
        texts = [page.get_text() for page in document]
        tables_by_page: dict[int, list[list[list[str | None]]]] = {}
        _require_printed_table(
            [table.extract() for table in document[7].find_tables().tables],
            ["Question", "Answer", "Mark"],
            printed_mcq_rows([q for q in questions if q.kind == "multiple_choice"]),
            "01–10",
        )
        for text in texts:
            body = re.sub(r"7127/1\s*·\s*Mark scheme|Page\s+\d+", "", text).strip()
            if not body:
                raise LayoutConformanceError(
                    "Accounting scheme contains a body-empty page"
                )
        for question in questions:
            if question.kind == "multiple_choice":
                expected = printed_mcq_rows([question])[0][1]
                if _compact(expected) not in _compact(texts[7]):
                    raise LayoutConformanceError(
                        f"Accounting scheme omits choice credit for {question.number}"
                    )
                checked_statements += 1
                continue
            start, stop = _CASE_PAGES[question.number]
            if start not in tables_by_page:
                tables_by_page[start] = [
                    table.extract() for table in document[start].find_tables().tables
                ]
            tables = tables_by_page[start]
            if question.kind in {"analysis", "extended_response"}:
                _require_printed_table(
                    tables,
                    ["Level", "Marks", "Descriptor"],
                    printed_level_rows(question),
                    question.number,
                )
            elif question.rule_id in EXPLICIT_RULES:
                headings = {
                    "statement_extract": [
                        "Non-current assets",
                        "Cost £",
                        "Accumulated depreciation £",
                        "Carrying amount £",
                        "Marks",
                    ],
                    "company_statement": ["", "£", "£", "Marks"],
                    "partnership_2": ["", "First period £", "Second period £", "Marks"],
                }.get(question.rule_id, ["Requirement", "Mark"])
                awards = printed_award_rows(question)
                if question.rule_id == "company_statement":
                    awards = [*awards, ["Profit for the year", ""]]
                _require_printed_table(
                    tables, headings, awards, question.number, award_columns=True
                )
            text = "\n".join(texts[start:stop])
            compact = _compact(text)
            if _compact(question.prompt) not in compact:
                raise LayoutConformanceError(
                    f"Accounting scheme omits the case heading for {question.number}"
                )
            if (
                question.rule_id not in EXPLICIT_RULES
                or question.rule_id == "explain_trade"
            ):
                for statement in indicative_content(question):
                    if _compact(statement) not in compact:
                        raise LayoutConformanceError(
                            f"Accounting scheme omits source credit for {question.number}"
                        )
                    checked_statements += 1
            else:
                solution = solve_accounting_calculation(
                    question.model_dump(mode="json")
                )
                if solution is None:
                    raise LayoutConformanceError(
                        "Accounting printed calculation has no public-input check"
                    )
                headings, rows = _calculation_table(question, solution)
                _require_printed_table(tables, headings, rows, question.number)
                numbers = {
                    abs(Decimal(token.replace(",", "")))
                    for token in re.findall(r"(?<!\w)-?\d[\d,]*(?:\.\d+)?(?!\w)", text)
                }
                # Parentheses denote expenses in conventional account tables.
                printed_values = dict(solution["numeric_results"])
                if question.rule_id == "partnership_2":
                    # The appropriation account prints the period's aggregate
                    # interest charge, not each partner's intermediate working.
                    for period in ("first_period", "second_period"):
                        roles = [
                            name
                            for name in printed_values
                            if name.startswith(period)
                            and name.endswith("_capital_interest")
                        ]
                        printed_values[f"{period}_capital_interest_total"] = sum(
                            Decimal(str(printed_values.pop(name))) for name in roles
                        )
                for value in printed_values.values():
                    if abs(Decimal(str(value))) not in numbers:
                        raise LayoutConformanceError(
                            f"Accounting scheme omits a derived figure for {question.number}"
                        )
                    checked_statements += 1
    return {
        "policy": ACCOUNTING_SCHEME_PAGINATION,
        "reference_page_count": reference_count,
        "actual_page_count": ACCOUNTING_SCHEME_PAGES,
        "checked_parts": len(questions),
        "checked_credit_statements": checked_statements,
        "qualification": "printed-content consistency, not learner calibration",
    }
