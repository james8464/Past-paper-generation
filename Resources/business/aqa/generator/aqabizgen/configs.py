from __future__ import annotations

from Backend.Core.exam_blueprints import PaperRule, QuestionRule, SectionRule


ALL_TOPICS = {f"business-{index}" for index in range(1, 11)}


def q(
    id: str,
    marks: int,
    kind: str,
    command: str,
    ao: dict[str, int],
) -> QuestionRule:
    return QuestionRule(
        id=id,
        marks=marks,
        kind=kind,
        command_word=command,
        assessment_objectives=ao,
    )


RULES = {
    "paper_1": PaperRule(
        id="paper_1",
        code="7132/1",
        title="Business 1",
        duration_minutes=120,
        total_marks=100,
        allowed_topic_ids=ALL_TOPICS,
        sections=[
            SectionRule(
                id="A", title="Multiple choice", option_count=15,
                answer_options=15, option_marks=1,
                questions=[
                    q("mcq", 1, "multiple_choice", "Select", {"AO1": 1})
                ],
            ),
            SectionRule(
                id="B", title="Short and extended response", option_count=1,
                answer_options=1, option_marks=35,
                questions=[
                    q(
                        "current_ratio",
                        4,
                        "calculation",
                        "Calculate",
                        {"AO1": 1, "AO2": 3},
                    ),
                    q(
                        "roce_calculation",
                        4,
                        "calculation",
                        "Calculate",
                        {"AO1": 1, "AO2": 3},
                    ),
                    q(
                        "analysis_1",
                        9,
                        "analysis",
                        "Analyse",
                        {"AO1": 2, "AO2": 3, "AO3": 4},
                    ),
                    q(
                        "analysis_2",
                        9,
                        "analysis",
                        "Analyse",
                        {"AO1": 2, "AO2": 3, "AO3": 4},
                    ),
                    q(
                        "analysis_3",
                        9,
                        "analysis",
                        "Analyse",
                        {"AO1": 2, "AO2": 3, "AO3": 4},
                    ),
                ],
            ),
            SectionRule(
                id="C", title="Essay choice", option_count=2,
                answer_options=1, option_marks=25,
                questions=[
                    q(
                        "essay",
                        25,
                        "essay",
                        "Evaluate",
                        {"AO1": 5, "AO2": 4, "AO3": 6, "AO4": 10},
                    )
                ],
            ),
            SectionRule(
                id="D", title="Essay choice", option_count=2,
                answer_options=1, option_marks=25,
                questions=[
                    q(
                        "essay",
                        25,
                        "essay",
                        "Evaluate",
                        {"AO1": 5, "AO2": 4, "AO3": 6, "AO4": 10},
                    )
                ],
            ),
        ],
    ),
    "paper_2": PaperRule(
        id="paper_2",
        code="7132/2",
        title="Business 2",
        duration_minutes=120,
        total_marks=100,
        allowed_topic_ids=ALL_TOPICS,
        sections=[
            SectionRule(
                id="1", title="Case study 1", option_count=1,
                answer_options=1, option_marks=32,
                questions=[
                    q("calculate", 3, "calculation", "Calculate", {"AO1": 2, "AO2": 1}),
                    q("explain", 4, "analysis", "Explain", {"AO1": 2, "AO2": 2}),
                    q("analyse", 9, "analysis", "Analyse", {"AO1": 2, "AO2": 3, "AO3": 4}),
                    q(
                        "evaluate",
                        16,
                        "extended_response",
                        "Evaluate",
                        {"AO1": 2, "AO2": 3, "AO3": 4, "AO4": 7},
                    ),
                ],
            ),
            SectionRule(
                id="2", title="Case study 2", option_count=1,
                answer_options=1, option_marks=34,
                questions=[
                    q("calculate", 3, "calculation", "Calculate", {"AO1": 3}),
                    q("explain", 6, "analysis", "Explain", {"AO1": 3, "AO2": 3}),
                    q("analyse", 9, "analysis", "Analyse", {"AO1": 2, "AO2": 3, "AO3": 4}),
                    q(
                        "evaluate",
                        16,
                        "extended_response",
                        "Evaluate",
                        {"AO1": 2, "AO2": 3, "AO3": 4, "AO4": 7},
                    ),
                ],
            ),
            SectionRule(
                id="3", title="Case study 3", option_count=1,
                answer_options=1, option_marks=34,
                questions=[
                    q("analyse_1", 9, "analysis", "Analyse", {"AO1": 2, "AO2": 3, "AO3": 4}),
                    q("analyse_2", 9, "analysis", "Analyse", {"AO1": 2, "AO2": 3, "AO3": 4}),
                    q(
                        "evaluate",
                        16,
                        "extended_response",
                        "Evaluate",
                        {"AO1": 2, "AO2": 3, "AO3": 4, "AO4": 7},
                    ),
                ],
            ),
        ],
    ),
    "paper_3": PaperRule(
        id="paper_3",
        code="7132/3",
        title="Business 3",
        duration_minutes=120,
        total_marks=100,
        allowed_topic_ids=ALL_TOPICS,
        sections=[
            SectionRule(
                id="A", title="Synoptic case study", option_count=1,
                answer_options=1, option_marks=100,
                questions=[
                    q("analyse_1", 12, "analysis", "Analyse", {"AO1": 3, "AO2": 3, "AO3": 6}),
                    q("analyse_2", 12, "analysis", "Analyse", {"AO1": 3, "AO2": 3, "AO3": 6}),
                    q(
                        "evaluate_1",
                        16,
                        "extended_response",
                        "Evaluate",
                        {"AO1": 2, "AO2": 3, "AO3": 4, "AO4": 7},
                    ),
                    q(
                        "evaluate_2",
                        16,
                        "extended_response",
                        "Evaluate",
                        {"AO1": 2, "AO2": 3, "AO3": 4, "AO4": 7},
                    ),
                    q(
                        "evaluate_3",
                        20,
                        "extended_response",
                        "Evaluate",
                        {"AO1": 4, "AO2": 3, "AO3": 5, "AO4": 8},
                    ),
                    q(
                        "evaluate_4",
                        24,
                        "extended_response",
                        "Evaluate",
                        {"AO1": 5, "AO2": 4, "AO3": 6, "AO4": 9},
                    ),
                ],
            )
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
