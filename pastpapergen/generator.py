from __future__ import annotations

import random

from pastpapergen.models import (
    MultipleChoiceOption,
    PaperBlueprint,
    PaperConfig,
    QuestionBlueprint,
    QuestionPart,
    Syllabus,
)


def build_paper_blueprint(
    config: PaperConfig,
    syllabus: Syllabus,
    seed: int | None = None,
) -> PaperBlueprint:
    rng = random.Random(seed)
    topics = syllabus.topics_for_themes(config.allowed_themes)
    if not topics:
        raise ValueError("No syllabus topics available for this paper.")

    questions: list[QuestionBlueprint] = []
    absolute_question_number = 1
    for section in config.sections:
        choice_lookup = _choice_lookup(section.choice_groups)
        choice_group_topics: dict[int, set[str]] = {}
        for index, marks in enumerate(section.question_marks):
            group_index = choice_lookup.get(index)
            topic = _choose_topic(rng, topics, choice_group_topics.get(group_index, set()))
            command_word = section.command_words[index]
            number = _question_number(config.id, section.name, absolute_question_number, index)
            parts = _build_parts(section, index, topic.title)
            if group_index is not None:
                choice_group_topics.setdefault(group_index, set()).add(topic.id)
            questions.append(
                QuestionBlueprint(
                    section=section.name,
                    number=number,
                    marks=marks,
                    command_word=command_word,
                    topic_id=topic.id,
                    prompt=_question_prompt(config.id, section.name, command_word, marks, topic.title, parts),
                    parts=parts,
                    stimulus_kind=_stimulus_kind(section, index),
                    choice_group=_choice_group_name(config.id, section.name, group_index),
                    source_reference=_source_reference(config.id, section.name, index),
                    source_title=_source_title(topic.title, section.name),
                    source_text=_source_text(topic.title, topic.points, section.name, index),
                    mark_breakdown=_mark_breakdown(marks, parts),
                    mark_scheme=_mark_scheme(command_word, marks, topic.title),
                    indicative_content=_indicative_content(topic.title, topic.points),
                )
            )
        absolute_question_number += _section_question_increment(config.id, section.name)

    return PaperBlueprint(
        paper_id=config.id,
        paper_code=config.code,
        title=config.title,
        duration_minutes=config.duration_minutes,
        total_marks=config.total_marks,
        questions=questions,
    )


def _choice_lookup(choice_groups: list[list[int]]) -> dict[int, int]:
    lookup: dict[int, int] = {}
    for group_index, group in enumerate(choice_groups, start=1):
        for question_index in group:
            lookup[question_index] = group_index
    return lookup


def _choose_topic(rng: random.Random, topics, excluded_ids: set[str]):
    available = [topic for topic in topics if topic.id not in excluded_ids]
    return rng.choice(available or topics)


def _choice_group_name(paper_id: str, section_name: str, group_index: int | None) -> str | None:
    if group_index is None:
        return None
    return f"{paper_id}-{section_name}-choice-{group_index}"


def _section_question_increment(paper_id: str, section_name: str) -> int:
    if paper_id in {"paper_1", "paper_2"} and section_name == "A":
        return 5
    return 1


def _question_number(
    paper_id: str,
    section_name: str,
    absolute_question_number: int,
    section_index: int,
) -> str:
    if paper_id in {"paper_1", "paper_2"}:
        if section_name == "A":
            return str(absolute_question_number + section_index)
        if section_name == "B":
            return f"{absolute_question_number}({chr(97 + section_index)})"
        return str(absolute_question_number + section_index)
    section_number = 1 if section_name == "A" else 2
    return f"{section_number}({chr(97 + section_index)})"


def _placeholder_prompt(command_word: str, marks: int, topic_title: str) -> str:
    topic = topic_title.lower()
    if command_word == "mcq":
        return (
            f"Which one of the following is correct about {topic}? "
            "A statement one; B statement two; C statement three; D statement four."
        )
    if command_word == "calculate":
        return f"With reference to the data provided, calculate one relevant value for {topic}."
    if command_word == "draw":
        return f"Draw a diagram to show one likely effect related to {topic}."
    if command_word == "explain":
        return f"Explain one likely effect of {topic}."
    if command_word == "examine":
        return f"Examine two likely factors affecting {topic}."
    if command_word == "discuss":
        if marks == 12:
            return f"Discuss whether the evidence supports one interpretation of {topic}."
        return f"Discuss the likely effects of {topic}."
    if command_word == "assess":
        return f"Assess whether {topic} is significant in this context."
    return f"Evaluate the likely effects of {topic}."


def _build_parts(section, index: int, topic_title: str) -> list[QuestionPart]:
    if not section.part_marks:
        return []
    part_marks = section.part_marks[index]
    part_commands = section.part_command_words[index]
    return [
        _build_part(chr(97 + part_index), marks, command, topic_title, part_index)
        for part_index, (marks, command) in enumerate(zip(part_marks, part_commands, strict=True))
    ]


def _build_part(
    label: str,
    marks: int,
    command: str,
    topic_title: str,
    part_index: int,
) -> QuestionPart:
    if command == "mcq":
        options = _mcq_options(topic_title)
        correct = "A"
        return QuestionPart(
            label=label,
            marks=marks,
            command_word=command,
            prompt=f"Which one of the following is correct about {topic_title.lower()}?",
            options=options,
            correct_option=correct,
            mark_breakdown="1 mark",
            mark_scheme=[
                f"The only correct answer is {correct}",
                *[
                    f"{option.label} is not correct because it does not accurately describe {topic_title.lower()}."
                    for option in options
                    if option.label != correct
                ],
            ],
        )
    return QuestionPart(
        label=label,
        marks=marks,
        command_word=command,
        prompt=_placeholder_prompt(command, marks, topic_title),
        mark_breakdown=_part_mark_breakdown(marks, command),
        mark_scheme=_mark_scheme(command, marks, topic_title),
        indicative_content=_indicative_content(topic_title, []),
    )


def _mcq_options(topic_title: str) -> list[MultipleChoiceOption]:
    topic = topic_title.lower()
    return [
        MultipleChoiceOption(label="A", text=f"A key concept in {topic} affects economic decisions"),
        MultipleChoiceOption(label="B", text=f"{topic.title()} removes the need for opportunity cost"),
        MultipleChoiceOption(label="C", text=f"{topic.title()} only applies to public sector markets"),
        MultipleChoiceOption(label="D", text=f"{topic.title()} has no effect on incentives"),
    ]


def _stimulus_kind(section, index: int) -> str:
    if not section.stimulus_kinds:
        return ""
    return section.stimulus_kinds[index]


def _group_prompt(
    command_word: str,
    marks: int,
    topic_title: str,
    parts: list[QuestionPart],
) -> str:
    if parts:
        return f"The following data relates to {topic_title.lower()}."
    return _placeholder_prompt(command_word, marks, topic_title)


def _question_prompt(
    paper_id: str,
    section_name: str,
    command_word: str,
    marks: int,
    topic_title: str,
    parts: list[QuestionPart],
) -> str:
    topic = topic_title.lower()
    if parts:
        return f"The following data relates to {topic}."
    if section_name in {"A", "B"} and paper_id == "paper_3":
        return _source_question_prompt(command_word, marks, topic, "Extract A")
    if section_name == "B":
        return _source_question_prompt(command_word, marks, topic, "Extract A")
    return _placeholder_prompt(command_word, marks, topic_title)


def _source_question_prompt(command_word: str, marks: int, topic: str, source_reference: str) -> str:
    if marks == 5:
        return f"With reference to {source_reference}, explain one likely effect of {topic}."
    if marks == 8:
        return f"With reference to {source_reference}, examine two likely factors affecting {topic}."
    if marks == 10:
        return f"With reference to {source_reference}, assess whether {topic} is significant in this context."
    if marks == 12:
        return f"With reference to {source_reference}, discuss whether the evidence supports one interpretation of {topic}."
    if marks == 15:
        return f"With reference to the source material, discuss the likely effects of {topic}."
    return f"Evaluate the view that {topic} is the most important issue in this market."


def _source_reference(paper_id: str, section_name: str, index: int) -> str:
    if section_name == "A" and paper_id in {"paper_1", "paper_2"}:
        return "Figure 1"
    if section_name in {"B"} or paper_id == "paper_3":
        return "Extract A" if index % 3 else "Figure 1"
    return ""


def _source_title(topic_title: str, section_name: str) -> str:
    return f"{topic_title}: economic context" if section_name in {"B", "A"} else topic_title


def _source_text(topic_title: str, points: list[str], section_name: str, index: int) -> str:
    if section_name == "C":
        return ""
    focus = ", ".join(points[:3]) if points else topic_title.lower()
    return (
        f"Recent constructed data on {topic_title.lower()} suggests changes in {focus}. "
        f"Firms, households and policy makers may respond differently depending on incentives, "
        f"market conditions and the time period considered."
    )


def _mark_breakdown(marks: int, parts: list[QuestionPart]) -> str:
    if parts:
        return "Knowledge 2, Application 2"
    return _part_mark_breakdown(marks, "")


def _part_mark_breakdown(marks: int, command_word: str) -> str:
    if marks == 1:
        return "1 mark"
    if marks == 4:
        return "Knowledge 2, Application 2"
    if marks == 5:
        return "Knowledge 1, Application 2, Analysis 2"
    if marks == 8:
        return "Knowledge 2, Application 2, Analysis 4"
    if marks == 10:
        return "Knowledge 2, Application 2, Analysis 3, Evaluation 3"
    if marks == 12:
        return "Knowledge 2, Application 2, Analysis 4, Evaluation 4"
    if marks == 15:
        return "Knowledge 3, Application 3, Analysis 4, Evaluation 5"
    if marks == 25:
        return "Knowledge 4, Application 4, Analysis 8, Evaluation 9"
    return f"{marks} marks"


def _mark_scheme(command_word: str, marks: int, topic_title: str) -> list[str]:
    topic = topic_title.lower()
    if marks == 1:
        return ["Award 1 mark for the correct answer."]
    if marks <= 5:
        return [
            f"Knowledge/Understanding: accurate identification or definition linked to {topic}.",
            f"Application: relevant use of the data, figure, extract or example for {topic}.",
            "Analysis: clear chain of reasoning showing cause and effect.",
        ]
    return [
        "Indicative content should be rewarded where it is relevant and developed.",
        f"Knowledge and understanding of {topic}.",
        "Application to the source material or a relevant economic example.",
        "Analysis using logical chains of reasoning.",
        "Evaluation supported by judgement where required by the command word.",
    ]


def _indicative_content(topic_title: str, points: list[str]) -> list[str]:
    content = points[:4] if points else []
    return content or [
        f"Definition and core features of {topic_title.lower()}",
        "Relevant source evidence",
        "Likely short-run and long-run effects",
        "Supported judgement",
    ]
