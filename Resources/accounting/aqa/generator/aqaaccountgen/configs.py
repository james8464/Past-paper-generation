from __future__ import annotations

from Backend.Core.exam_blueprints import PaperRule, QuestionRule, SectionRule


ALL_TOPICS = {f"accounting-{index}" for index in range(1, 19)}


def q(id: str, marks: int, kind: str, command: str) -> QuestionRule:
    return QuestionRule(id=id, marks=marks, kind=kind, command_word=command)


def mcqs() -> list[QuestionRule]:
    return [q(f"mcq_{index}", 1, "multiple_choice", "Select") for index in range(1, 11)]


RULES = {
    "paper_1": PaperRule(
        id="paper_1",
        code="7127/1",
        title="Financial Accounting",
        duration_minutes=180,
        total_marks=120,
        allowed_topic_ids=ALL_TOPICS,
        sections=[
            SectionRule(
                id="A", title="Short questions", option_count=1,
                answer_options=1, option_marks=30,
                questions=[
                    *mcqs(),
                    q("explain_trade", 6, "analysis", "Explain"),
                    q("statement_extract", 7, "calculation", "Prepare"),
                    q("ledger_calculation", 5, "calculation", "Calculate"),
                    q("accounting_concept", 2, "analysis", "Explain"),
                ],
            ),
            SectionRule(
                id="B", title="Financial statements", option_count=1,
                answer_options=1, option_marks=40,
                questions=[
                    q("company_statement", 14, "calculation", "Prepare"),
                    q("company_adjustment", 6, "analysis", "Explain"),
                    q("partnership_1", 6, "calculation", "Calculate"),
                    q("partnership_2", 8, "calculation", "Prepare"),
                    q("partnership_3", 6, "analysis", "Assess"),
                ],
            ),
            SectionRule(
                id="C", title="Accounting decisions", option_count=1,
                answer_options=1, option_marks=50,
                questions=[
                    q("decision_1", 25, "extended_response", "Advise"),
                    q("decision_2", 25, "extended_response", "Advise"),
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
        allowed_topic_ids=ALL_TOPICS,
        sections=[
            SectionRule(
                id="A", title="Short questions", option_count=1,
                answer_options=1, option_marks=30,
                questions=[
                    *mcqs(),
                    q("frc", 3, "analysis", "Explain"),
                    q("contribution", 6, "calculation", "Calculate"),
                    q("limitation", 3, "analysis", "Explain"),
                    q("budget", 8, "calculation", "Calculate"),
                ],
            ),
            SectionRule(
                id="B", title="Management accounting", option_count=1,
                answer_options=1, option_marks=40,
                questions=[
                    q("variance_1", 4, "calculation", "Calculate"),
                    q("variance_2", 8, "calculation", "Calculate"),
                    q("variance_3", 2, "analysis", "State"),
                    q("variance_4", 6, "analysis", "Explain"),
                    q("costing_1", 8, "calculation", "Calculate"),
                    q("costing_2", 1, "analysis", "State"),
                    q("costing_3", 5, "calculation", "Calculate"),
                    q("costing_4", 6, "analysis", "Assess"),
                ],
            ),
            SectionRule(
                id="C", title="Strategic decision-making", option_count=1,
                answer_options=1, option_marks=50,
                questions=[
                    q("decision_1", 25, "extended_response", "Evaluate"),
                    q("decision_2", 25, "extended_response", "Evaluate"),
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
