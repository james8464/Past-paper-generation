from __future__ import annotations

from Backend.Core.exam_blueprints import PaperRule, QuestionRule, SectionRule

PAPER_1_TOPICS = {
    "accounting-3",
    "accounting-4",
    "accounting-5",
    "accounting-6",
    "accounting-7",
    "accounting-8",
    "accounting-13",
    "accounting-14",
    "accounting-15",
    "accounting-16",
    "accounting-17",
    "accounting-18",
}

PAPER_2_TOPICS = {
    "accounting-1",
    "accounting-3",
    "accounting-5",
    "accounting-6",
    "accounting-8",
    "accounting-9",
    "accounting-10",
    "accounting-11",
    "accounting-12",
    "accounting-13",
    "accounting-16",
    "accounting-17",
    "accounting-18",
}


def q(id: str, marks: int, kind: str, command: str, **objectives: int) -> QuestionRule:
    return QuestionRule(id=id, marks=marks, kind=kind, command_word=command,
                        assessment_objectives=objectives)


def mcqs() -> list[QuestionRule]:
    return [q(f"mcq_{index}", 1, "multiple_choice", "Select", AO1=1) for index in range(1, 11)]


# June 2025 official schemes, P1 pp9-25 / P2 pp9-27; see
# docs/quality/assessment-objective-reference.md. Familiar Section A techniques
# are AO1, contextual Section B application is AO2, decisions include AO3 evaluation.
RULES = {
    "paper_1": PaperRule(
        id="paper_1",
        code="7127/1",
        title="Financial Accounting",
        duration_minutes=180,
        total_marks=120,
        allowed_topic_ids=PAPER_1_TOPICS,
        sections=[
            SectionRule(
                id="A", title="Short questions", option_count=1,
                answer_options=1, option_marks=30,
                questions=[
                    *mcqs(),
                    q("explain_trade", 6, "analysis", "Explain", AO1=6),
                    q("statement_extract", 7, "calculation", "Prepare", AO1=7),
                    q("ledger_calculation", 5, "calculation", "Prepare", AO1=5),
                    q("accounting_concept", 2, "calculation", "Prepare", AO1=2),
                ],
            ),
            SectionRule(
                id="B", title="Financial statements", option_count=1,
                answer_options=1, option_marks=40,
                questions=[
                    q("company_statement", 14, "calculation", "Prepare", AO2=14),
                    q("company_adjustment", 6, "analysis", "Assess", AO2=2, AO3=4),
                    q("partnership_1", 6, "calculation", "Prepare", AO2=6),
                    q("partnership_2", 8, "calculation", "Prepare", AO2=8),
                    q("partnership_3", 6, "analysis", "Assess", AO2=2, AO3=4),
                ],
            ),
            SectionRule(
                id="C", title="Accounting decisions", option_count=1,
                answer_options=1, option_marks=50,
                questions=[
                    q("decision_1", 25, "extended_response", "Advise", AO2=5, AO3=20),
                    q("decision_2", 25, "extended_response", "Advise", AO2=5, AO3=20),
                ],
            ),
        ],
    ),
    "paper_2": PaperRule(
        id="paper_2",
        code="7127/2",
        title="Accounting for Analysis and Decision-making",
        duration_minutes=180,
        total_marks=120,
        allowed_topic_ids=PAPER_2_TOPICS,
        sections=[
            SectionRule(
                id="A", title="Short questions", option_count=1,
                answer_options=1, option_marks=30,
                questions=[
                    *mcqs(),
                    q("frc", 3, "analysis", "Explain", AO1=3),
                    q("contribution", 6, "calculation", "Calculate", AO1=6),
                    q("limitation", 3, "analysis", "Explain", AO1=3),
                    q("budget", 8, "calculation", "Calculate", AO1=8),
                ],
            ),
            SectionRule(
                id="B", title="Management accounting", option_count=1,
                answer_options=1, option_marks=40,
                questions=[
                    q("variance_1", 4, "calculation", "Calculate", AO2=4),
                    q("variance_2", 8, "calculation", "Calculate", AO2=8),
                    q("variance_3", 2, "analysis", "State", AO2=2),
                    q("variance_4", 6, "analysis", "Explain", AO2=2, AO3=4),
                    q("costing_1", 8, "calculation", "Calculate", AO2=8),
                    q("costing_2", 1, "analysis", "State", AO2=1),
                    q("costing_3", 5, "calculation", "Calculate", AO2=5),
                    q("costing_4", 6, "analysis", "Assess", AO2=2, AO3=4),
                ],
            ),
            SectionRule(
                id="C", title="Strategic decision-making", option_count=1,
                answer_options=1, option_marks=50,
                questions=[
                    q("decision_1", 25, "extended_response", "Advise", AO2=5, AO3=20),
                    q("decision_2", 25, "extended_response", "Advise", AO2=5, AO3=20),
                ],
            ),
        ],
    ),
}


def load_rule(value: str) -> PaperRule:
    key = value.strip().lower().replace("-", "_").replace(" ", "")
    aliases = {
        "1": "paper_1", "2": "paper_2", "paper1": "paper_1",
        "paper2": "paper_2", "paper_1": "paper_1", "paper_2": "paper_2",
    }
    try:
        return RULES[aliases[key]].model_copy(deep=True)
    except KeyError as error:
        raise ValueError("paper must be 1 or 2") from error
