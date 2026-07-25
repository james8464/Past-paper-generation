from __future__ import annotations

from Backend.Core.exam_blueprints import PaperRule, QuestionRule, SectionRule


MICRO_TOPICS = {f"4.1.{index}" for index in range(1, 9)}
MACRO_TOPICS = {f"4.2.{index}" for index in range(1, 7)}


def _q(id: str, marks: int, kind: str, command: str) -> QuestionRule:
    return QuestionRule(id=id, marks=marks, kind=kind, command_word=command)


RULES = {
    "paper_1": PaperRule(
        id="paper_1",
        code="7136/1",
        title="Markets and market failure",
        duration_minutes=120,
        total_marks=80,
        allowed_topic_ids=MICRO_TOPICS,
        sections=[
            SectionRule(
                id="A",
                title="Data response",
                option_count=2,
                answer_options=1,
                option_marks=40,
                questions=[
                    _q("calculation", 2, "calculation", "Calculate"),
                    _q("data_analysis", 4, "data_response", "Explain"),
                    _q("diagram_analysis", 9, "diagram_analysis", "Explain"),
                    _q("evaluation", 25, "extended_response", "Discuss"),
                ],
            ),
            SectionRule(
                id="B",
                title="Essays",
                option_count=3,
                answer_options=1,
                option_marks=40,
                questions=[
                    _q("analysis", 15, "essay", "Explain"),
                    _q("evaluation", 25, "essay", "Evaluate"),
                ],
            ),
        ],
    ),
    "paper_2": PaperRule(
        id="paper_2",
        code="7136/2",
        title="National and international economy",
        duration_minutes=120,
        total_marks=80,
        allowed_topic_ids=MACRO_TOPICS,
        sections=[
            SectionRule(
                id="A",
                title="Data response",
                option_count=2,
                answer_options=1,
                option_marks=40,
                questions=[
                    _q("calculation", 2, "calculation", "Calculate"),
                    _q("data_analysis", 4, "data_response", "Explain"),
                    _q("diagram_analysis", 9, "diagram_analysis", "Explain"),
                    _q("evaluation", 25, "extended_response", "Discuss"),
                ],
            ),
            SectionRule(
                id="B",
                title="Essays",
                option_count=3,
                answer_options=1,
                option_marks=40,
                questions=[
                    _q("analysis", 15, "essay", "Explain"),
                    _q("evaluation", 25, "essay", "Evaluate"),
                ],
            ),
        ],
    ),
    "paper_3": PaperRule(
        id="paper_3",
        code="7136/3",
        title="Economic principles and issues",
        duration_minutes=120,
        total_marks=80,
        allowed_topic_ids=MICRO_TOPICS | MACRO_TOPICS,
        sections=[
            SectionRule(
                id="A",
                title="Multiple-choice questions",
                option_count=30,
                answer_options=30,
                option_marks=1,
                questions=[_q("mcq", 1, "multiple_choice", "Select")],
            ),
            SectionRule(
                id="B",
                title="Case study",
                option_count=1,
                answer_options=1,
                option_marks=50,
                questions=[
                    _q("data_judgement", 10, "data_interpretation", "Assess"),
                    _q("analysis", 15, "essay", "Explain"),
                    _q("recommendation", 25, "extended_response", "Recommend"),
                ],
            ),
        ],
    ),
}


def load_rule(value: str) -> PaperRule:
    key = value.strip().lower().replace("-", "_").replace(" ", "")
    aliases = {
        "1": "paper_1",
        "2": "paper_2",
        "3": "paper_3",
        "paper1": "paper_1",
        "paper2": "paper_2",
        "paper3": "paper_3",
        "paper_1": "paper_1",
        "paper_2": "paper_2",
        "paper_3": "paper_3",
    }
    try:
        return RULES[aliases[key]].model_copy(deep=True)
    except KeyError as error:
        raise ValueError("paper must be 1, 2 or 3") from error
