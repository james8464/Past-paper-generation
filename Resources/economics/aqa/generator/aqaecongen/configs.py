from __future__ import annotations

from Backend.Core.exam_blueprints import PaperRule, QuestionRule, SectionRule

MICRO_TOPICS = {f"4.1.{index}" for index in range(1, 9)}
MACRO_TOPICS = {f"4.2.{index}" for index in range(1, 7)}
PAPER3_MCQ_PAGE_COUNTS = (
    1, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 1,
    1, 1, 2, 1, 1, 1, 2, 1, 1, 2, 2, 1,
)
PAPER3_VISUAL_QUESTION_NUMBERS = frozenset(
    {2, 4, 9, 10, 13, 14, 19, 20, 24, 25}
)


def _q(
    id: str,
    marks: int,
    kind: str,
    command: str,
    ao: dict[str, int],
    operation: str,
    source: str,
) -> QuestionRule:
    return QuestionRule(
        id=id,
        marks=marks,
        kind=kind,
        command_word=command,
        assessment_objectives=ao,
        task_operation=operation,
        source_dependency=source,
    )


def _mcq_rule(ao: str, operation: str, source: str) -> QuestionRule:
    return _q("mcq", 1, "multiple_choice", "Select", {ao: 1}, operation, source)


_AQA_VISUAL = {2, 4, 9, 10, 13, 14, 19, 20, 24, 25}
_AQA_VISUAL_ANALYSIS = {9, 14, 20, 25}
_AQA_INDEX = {5, 15, 30}
_AQA_APPLIED = {1, 3, 7, 11, 17}
_AQA_MCQ_OVERRIDES = {
    number: [
        _mcq_rule(
            "AO3" if number in _AQA_VISUAL_ANALYSIS else "AO2",
            "analyse",
            "figure",
        )
    ]
    if number in _AQA_VISUAL
    else [_mcq_rule("AO2", "transform", "stem")]
    if number in _AQA_INDEX
    else [_mcq_rule("AO2", "analyse", "stem")]
    if number in _AQA_APPLIED
    else [_mcq_rule("AO1", "retrieve", "none")]
    for number in range(1, 31)
}


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
                    _q("calculation", 2, "calculation", "Calculate", {"AO2": 2}, "transform", "external"),
                    _q("data_analysis", 4, "data_response", "Explain", {"AO1": 2, "AO2": 2}, "explain", "external"),
                    _q("diagram_analysis", 9, "diagram_analysis", "Explain", {"AO1": 2, "AO2": 3, "AO3": 4}, "analyse", "external"),
                    _q("evaluation", 25, "extended_response", "Discuss", {"AO1": 4, "AO2": 5, "AO3": 7, "AO4": 9}, "judge", "external"),
                ],
            ),
            SectionRule(
                id="B",
                title="Essays",
                option_count=3,
                answer_options=1,
                option_marks=40,
                questions=[
                    _q("analysis", 15, "essay", "Explain", {"AO1": 3, "AO2": 5, "AO3": 7}, "analyse", "none"),
                    _q("evaluation", 25, "essay", "Evaluate", {"AO1": 4, "AO2": 5, "AO3": 7, "AO4": 9}, "judge", "none"),
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
                    _q("calculation", 2, "calculation", "Calculate", {"AO2": 2}, "transform", "external"),
                    _q("data_analysis", 4, "data_response", "Explain", {"AO1": 2, "AO2": 2}, "explain", "external"),
                    _q("diagram_analysis", 9, "diagram_analysis", "Explain", {"AO1": 2, "AO2": 3, "AO3": 4}, "analyse", "external"),
                    _q("evaluation", 25, "extended_response", "Discuss", {"AO1": 4, "AO2": 5, "AO3": 7, "AO4": 9}, "judge", "external"),
                ],
            ),
            SectionRule(
                id="B",
                title="Essays",
                option_count=3,
                answer_options=1,
                option_marks=40,
                questions=[
                    _q("analysis", 15, "essay", "Explain", {"AO1": 3, "AO2": 5, "AO3": 7}, "analyse", "none"),
                    _q("evaluation", 25, "essay", "Evaluate", {"AO1": 4, "AO2": 5, "AO3": 7, "AO4": 9}, "judge", "none"),
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
                questions=[_mcq_rule("AO1", "retrieve", "none")],
                question_overrides=_AQA_MCQ_OVERRIDES,
            ),
            SectionRule(
                id="B",
                title="Case study",
                option_count=1,
                answer_options=1,
                option_marks=50,
                questions=[
                    _q("data_judgement", 10, "data_interpretation", "Assess", {"AO1": 2, "AO2": 2, "AO3": 3, "AO4": 3}, "judge", "external"),
                    _q("analysis", 15, "essay", "Explain", {"AO1": 3, "AO2": 3, "AO3": 9}, "analyse", "external"),
                    _q("recommendation", 25, "extended_response", "Recommend", {"AO1": 5, "AO2": 5, "AO3": 3, "AO4": 12}, "judge", "external"),
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
