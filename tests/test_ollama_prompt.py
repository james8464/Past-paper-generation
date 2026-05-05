from pastpapergen.models import QuestionBlueprint, SyllabusTopic
from pastpapergen.ollama_client import build_question_prompt


def test_ollama_prompt_limits_generation_to_syllabus_topic():
    topic = SyllabusTopic(
        id="1.3",
        theme=1,
        title="Market failure",
        points=["externalities", "public goods"],
    )
    question = QuestionBlueprint(
        section="B",
        number="7",
        marks=12,
        command_word="discuss",
        topic_id="1.3",
        prompt="Analyse market failure.",
    )

    prompt = build_question_prompt(question, topic)

    assert "Use only this syllabus topic" in prompt
    assert "1.3"
    assert "externalities" in prompt
    assert "Command word: discuss" in prompt
    assert "Parts: none" in prompt
    assert "12-mark questions usually use discuss whether" in prompt
    assert "10-mark questions usually use assess whether" in prompt
    assert "Return JSON only" in prompt
    assert '"parts"' in prompt
    assert '"options"' in prompt
    assert '"correct_option"' in prompt
    assert '"mark_breakdown"' in prompt
    assert "Do not include '(4 marks)' or similar mark text" in prompt
