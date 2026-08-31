"""Shared Edexcel test fixtures, importable in full and family-only runs."""

import random


def forced_part(kind, command, marks, topic_id="1.2.2", part_index=0):
    from pastpapergen.assessment_contracts import bind_question
    from pastpapergen.generator import _build_part
    from pastpapergen.models import QuestionBlueprint, SyllabusTopic

    topic = SyllabusTopic(id=topic_id, theme=int(topic_id[0]), title="Demand")
    part = _build_part("a", marks, command, topic, kind, part_index, random.Random(7))
    q = QuestionBlueprint(
        section="A",
        number="1",
        marks=marks,
        command_word=command,
        topic_id=topic_id,
        prompt="Use the information below.",
        parts=[part],
        stimulus_kind=kind,
    )
    return bind_question(q, 7)
