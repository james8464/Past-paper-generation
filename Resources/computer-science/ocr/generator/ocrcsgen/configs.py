from __future__ import annotations

from Backend.Core.exam_blueprints import PaperRule, QuestionRule, SectionRule


PAPER_1_MARKS = [
    [4, 1, 3, 3, 4, 3, 2, 3],
    [2, 4, 3, 2, 4, 5, 9],
    [5, 1, 3, 2, 2],
    [1, 1, 2, 3, 4, 2],
    [4, 1, 1, 2],
    [12, 4, 2, 6],
    [9],
    [2, 4, 4],
    [5, 3, 3],
]
PAPER_2_MARKS = [
    [2, 1, 2, 4],
    [12],
    [7, 4, 9],
    [2, 2, 2],
    [4, 4, 4],
    [3, 1, 5, 2, 2, 1, 1],
    [2, 2, 1, 5, 3],
    [4, 3, 3, 1, 2],
    [3, 2, 3, 3, 5, 5, 6, 4, 9],
]
PAPER_1_KINDS = [
    ["analysis", "short_answer", "analysis", "trace", "programming", "analysis", "short_answer", "analysis"],
    ["short_answer", "analysis", "analysis", "short_answer", "analysis", "table", "extended_response"],
    ["table", "short_answer", "analysis", "short_answer", "short_answer"],
    ["calculation", "short_answer", "calculation", "calculation", "calculation", "calculation"],
    ["diagram", "calculation", "calculation", "calculation"],
    ["extended_response", "analysis", "short_answer", "programming"],
    ["extended_response"],
    ["short_answer", "trace", "analysis"],
    ["programming", "analysis", "analysis"],
]
PAPER_2_KINDS = [
    ["short_answer", "short_answer", "analysis", "programming"],
    ["extended_response"],
    ["programming", "analysis", "extended_response"],
    ["short_answer", "short_answer", "short_answer"],
    ["programming", "programming", "programming"],
    ["analysis", "short_answer", "programming", "short_answer", "short_answer", "short_answer", "short_answer"],
    ["short_answer", "short_answer", "short_answer", "programming", "analysis"],
    ["programming", "analysis", "analysis", "short_answer", "short_answer"],
    ["analysis", "short_answer", "analysis", "analysis", "programming", "programming", "programming", "programming", "extended_response"],
]
SECTION_TOPICS = {
    "paper_1": [
        "systems-1", "systems-1", "systems-2", "systems-4", "systems-5",
        "systems-3", "systems-6", "systems-4", "systems-3",
    ],
    "paper_2": [
        "algorithms-2", "algorithms-3", "algorithms-4", "algorithms-5",
        "algorithms-5", "algorithms-4", "algorithms-2", "algorithms-1",
        "algorithms-2",
    ],
}


COMMANDS = {
    "analysis": "Explain",
    "calculation": "Calculate",
    "diagram": "Draw",
    "extended_response": "Discuss",
    "programming": "Develop",
    "short_answer": "State",
    "table": "Complete",
    "trace": "Trace",
}


def _question(index: int, marks: int, kind: str) -> QuestionRule:
    return QuestionRule(
        id=f"q{index}", marks=marks, kind=kind, command_word=COMMANDS[kind]
    )


def _sections(
    paper_id: str, marks: list[list[int]], kinds: list[list[str]]
) -> list[SectionRule]:
    return [
        SectionRule(
            id=str(index),
            title=f"Question {index}",
            option_count=1,
            answer_options=1,
            option_marks=sum(sequence),
            questions=[
                _question(question_index, value, kind)
                for question_index, (value, kind) in enumerate(
                    zip(sequence, kinds[index - 1], strict=True), start=1
                )
            ],
        )
        for index, sequence in enumerate(marks, start=1)
    ]


RULES = {
    "paper_1": PaperRule(
        id="paper_1",
        code="H446/01",
        title="Computer systems",
        duration_minutes=150,
        total_marks=140,
        allowed_topic_ids={f"systems-{index}" for index in range(1, 7)},
        sections=_sections("paper_1", PAPER_1_MARKS, PAPER_1_KINDS),
    ),
    "paper_2": PaperRule(
        id="paper_2",
        code="H446/02",
        title="Algorithms and programming",
        duration_minutes=150,
        total_marks=140,
        allowed_topic_ids={f"algorithms-{index}" for index in range(1, 6)},
        sections=_sections("paper_2", PAPER_2_MARKS, PAPER_2_KINDS),
    ),
}


def load_rule(value: str) -> PaperRule:
    key = value.strip().lower().replace("-", "_").replace(" ", "")
    aliases = {
        "1": "paper_1", "2": "paper_2",
        "paper1": "paper_1", "paper2": "paper_2",
        "paper_1": "paper_1", "paper_2": "paper_2",
    }
    try:
        return RULES[aliases[key]].model_copy(deep=True)
    except KeyError as error:
        raise ValueError("paper must be 1 or 2") from error
