from __future__ import annotations

from Backend.Core.exam_blueprints import PaperRule, QuestionRule, SectionRule

MICRO = {f"micro-{index}" for index in range(1, 7)}
MACRO = {f"macro-{index}" for index in range(1, 6)}


def q(id: str, marks: int, kind: str, command: str) -> QuestionRule:
    return QuestionRule(id=id, marks=marks, kind=kind, command_word=command)


RULES = {
    "paper_1": PaperRule(
        id="paper_1",
        code="H460/01",
        title="Microeconomics",
        duration_minutes=120,
        total_marks=80,
        allowed_topic_ids=MICRO,
        sections=[
            SectionRule(
                id="A",
                title="Data response",
                option_count=1,
                answer_options=1,
                option_marks=30,
                questions=[
                    q("definition", 2, "short_answer", "Explain"),
                    q("diagram", 4, "diagram_analysis", "Explain"),
                    q("calculation", 2, "calculation", "Calculate"),
                    q("comparison", 2, "data_response", "Compare"),
                    q("evaluation_8", 8, "extended_response", "Evaluate"),
                    q("evaluation_12", 12, "extended_response", "Evaluate"),
                ],
            ),
            SectionRule(
                id="B",
                title="Microeconomics essay",
                option_count=2,
                answer_options=1,
                option_marks=25,
                questions=[q("essay", 25, "essay", "Evaluate")],
            ),
            SectionRule(
                id="C",
                title="Microeconomics essay",
                option_count=2,
                answer_options=1,
                option_marks=25,
                questions=[q("essay", 25, "essay", "Evaluate")],
            ),
        ],
    ),
    "paper_2": PaperRule(
        id="paper_2",
        code="H460/02",
        title="Macroeconomics",
        duration_minutes=120,
        total_marks=80,
        allowed_topic_ids=MACRO,
        sections=[
            SectionRule(
                id="A",
                title="Data response",
                option_count=1,
                answer_options=1,
                option_marks=30,
                questions=[
                    q("identification", 2, "short_answer", "Identify"),
                    q("calculation", 1, "calculation", "Calculate"),
                    q("relationship_3", 3, "data_response", "Explain"),
                    q("relationship_4", 4, "data_response", "Explain"),
                    q("evaluation_8", 8, "extended_response", "Evaluate"),
                    q("evaluation_12", 12, "extended_response", "Evaluate"),
                ],
            ),
            SectionRule(
                id="B",
                title="Macroeconomics essay",
                option_count=2,
                answer_options=1,
                option_marks=25,
                questions=[q("essay", 25, "essay", "Evaluate")],
            ),
            SectionRule(
                id="C",
                title="Macroeconomics essay",
                option_count=2,
                answer_options=1,
                option_marks=25,
                questions=[q("essay", 25, "essay", "Evaluate")],
            ),
        ],
    ),
    "paper_3": PaperRule(
        id="paper_3",
        code="H460/03",
        title="Themes in economics",
        duration_minutes=120,
        total_marks=80,
        allowed_topic_ids=MICRO | MACRO,
        sections=[
            SectionRule(
                id="A",
                title="Multiple choice",
                option_count=30,
                answer_options=30,
                option_marks=1,
                questions=[q("mcq", 1, "multiple_choice", "Select")],
            ),
            SectionRule(
                id="B",
                title="Extended data response",
                option_count=1,
                answer_options=1,
                option_marks=50,
                questions=[
                    q("extract_1_calc", 2, "calculation", "Calculate"),
                    q("extract_1_explain", 3, "data_response", "Explain"),
                    q("extract_1_eval", 15, "extended_response", "Evaluate"),
                    q("extract_2_compare", 3, "data_response", "Compare"),
                    q("extract_2_identify", 2, "short_answer", "Identify"),
                    q("extract_2_eval", 15, "extended_response", "Evaluate"),
                    q("extract_3_compare", 2, "data_response", "Compare"),
                    q("extract_3_eval", 8, "extended_response", "Evaluate"),
                ],
            ),
        ],
    ),
}


def load_rule(value: str) -> PaperRule:
    key = value.strip().lower().replace("-", "_").replace(" ", "")
    aliases = {
        "1": "paper_1", "2": "paper_2", "3": "paper_3",
        "paper1": "paper_1", "paper2": "paper_2", "paper3": "paper_3",
        "paper_1": "paper_1", "paper_2": "paper_2", "paper_3": "paper_3",
    }
    try:
        return RULES[aliases[key]].model_copy(deep=True)
    except KeyError as error:
        raise ValueError("paper must be 1, 2 or 3") from error
