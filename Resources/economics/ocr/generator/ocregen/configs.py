from __future__ import annotations

from Backend.Core.exam_blueprints import PaperRule, QuestionRule, SectionRule

MICRO = {f"micro-{index}" for index in range(1, 7)}
MACRO = {f"macro-{index}" for index in range(1, 6)}


def q(
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


def mcq(ao: str, operation: str, source: str) -> QuestionRule:
    return q("mcq", 1, "multiple_choice", "Select", {ao: 1}, operation, source)


_OCR_INDEX = {5, 10, 15, 20, 25, 30}
_OCR_APPLIED = {1}
_OCR_ANALYSIS = {3, 7, 9, 13, 17, 19, 23, 28}
_OCR_MCQ_OVERRIDES = {
    number: [mcq("AO2", "transform", "stem")]
    if number in _OCR_INDEX
    else [mcq("AO2", "analyse", "stem")]
    if number in _OCR_APPLIED
    else [mcq("AO3", "analyse", "stem")]
    if number in _OCR_ANALYSIS
    else [mcq("AO1", "retrieve", "none")]
    for number in range(1, 31)
}


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
                    q("definition", 2, "short_answer", "Explain", {"AO1": 2}, "explain", "none"),
                    q("diagram", 4, "diagram_analysis", "Explain", {"AO1": 2, "AO2": 2}, "analyse", "external"),
                    q("calculation", 2, "calculation", "Calculate", {"AO2": 2}, "transform", "external"),
                    q("comparison", 2, "data_response", "Compare", {"AO2": 2}, "analyse", "external"),
                    q("evaluation_8", 8, "extended_response", "Evaluate", {"AO1": 1, "AO2": 1, "AO3": 3, "AO4": 3}, "judge", "external"),
                    q("evaluation_12", 12, "extended_response", "Evaluate", {"AO1": 1, "AO2": 1, "AO3": 5, "AO4": 5}, "judge", "external"),
                ],
            ),
            SectionRule(
                id="B",
                title="Microeconomics essay",
                option_count=2,
                answer_options=1,
                option_marks=25,
                questions=[q("essay", 25, "essay", "Evaluate", {"AO1": 6, "AO2": 6, "AO3": 6, "AO4": 7}, "judge", "none")],
            ),
            SectionRule(
                id="C",
                title="Microeconomics essay",
                option_count=2,
                answer_options=1,
                option_marks=25,
                questions=[q("essay", 25, "essay", "Evaluate", {"AO1": 6, "AO2": 6, "AO3": 6, "AO4": 7}, "judge", "none")],
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
                    q("identification", 2, "short_answer", "Identify", {"AO1": 2}, "retrieve", "none"),
                    q("calculation", 1, "calculation", "Calculate", {"AO2": 1}, "transform", "external"),
                    q("relationship_3", 3, "data_response", "Explain", {"AO1": 1, "AO2": 2}, "explain", "external"),
                    q("relationship_4", 4, "data_response", "Explain", {"AO1": 1, "AO2": 3}, "explain", "external"),
                    q("evaluation_8", 8, "extended_response", "Evaluate", {"AO1": 1, "AO2": 1, "AO3": 3, "AO4": 3}, "judge", "external"),
                    q("evaluation_12", 12, "extended_response", "Evaluate", {"AO1": 1, "AO2": 1, "AO3": 5, "AO4": 5}, "judge", "external"),
                ],
            ),
            SectionRule(
                id="B",
                title="Macroeconomics essay",
                option_count=2,
                answer_options=1,
                option_marks=25,
                questions=[q("essay", 25, "essay", "Evaluate", {"AO1": 6, "AO2": 6, "AO3": 6, "AO4": 7}, "judge", "none")],
            ),
            SectionRule(
                id="C",
                title="Macroeconomics essay",
                option_count=2,
                answer_options=1,
                option_marks=25,
                questions=[q("essay", 25, "essay", "Evaluate", {"AO1": 6, "AO2": 6, "AO3": 6, "AO4": 7}, "judge", "none")],
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
                questions=[mcq("AO1", "retrieve", "none")],
                question_overrides=_OCR_MCQ_OVERRIDES,
            ),
            SectionRule(
                id="B",
                title="Extended data response",
                option_count=1,
                answer_options=1,
                option_marks=50,
                questions=[
                    q("extract_1_calc", 2, "calculation", "Calculate", {"AO2": 2}, "transform", "external"),
                    q("extract_1_explain", 3, "data_response", "Explain", {"AO1": 1, "AO2": 2}, "explain", "external"),
                    q("extract_1_eval", 15, "extended_response", "Evaluate", {"AO1": 2, "AO2": 3, "AO3": 4, "AO4": 6}, "judge", "external"),
                    q("extract_2_compare", 3, "data_response", "Compare", {"AO1": 2, "AO2": 1}, "analyse", "external"),
                    q("extract_2_identify", 2, "short_answer", "Identify", {"AO1": 1, "AO2": 1}, "analyse", "external"),
                    q("extract_2_eval", 15, "extended_response", "Evaluate", {"AO1": 2, "AO2": 3, "AO3": 4, "AO4": 6}, "judge", "external"),
                    q("extract_3_compare", 2, "data_response", "Compare", {"AO2": 2}, "analyse", "external"),
                    q("extract_3_eval", 8, "extended_response", "Evaluate", {"AO1": 1, "AO2": 1, "AO3": 2, "AO4": 4}, "judge", "external"),
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
