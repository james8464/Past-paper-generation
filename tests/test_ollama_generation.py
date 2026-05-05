from pathlib import Path

from pastpapergen.generator import build_paper_blueprint
from pastpapergen.ollama_client import generate_questions_with_ollama
from pastpapergen.paper_configs import load_builtin_paper_config
from pastpapergen.syllabus import load_syllabus


class FakeOllamaClient:
    def generate_json(self, prompt: str) -> dict[str, object]:
        return {
            "question_text": "With reference to Extract A, explain one likely impact of externalities in this market.",
            "source_text": "A market creates external costs for third parties.",
            "source_reference": "Extract A",
            "mark_breakdown": "Knowledge 1, Application 2, Analysis 2",
            "indicative_content": ["external costs", "third parties"],
            "mark_scheme": ["Defines external costs", "Applies to context"],
            "parts": [
                {
                    "label": "a",
                    "prompt": "Explain one external cost.",
                    "mark_scheme": ["Identifies external cost"],
                },
                {
                    "label": "b",
                    "prompt": "Which one of the following is correct?",
                    "options": [
                        {"label": "A", "text": "External costs affect third parties"},
                        {"label": "B", "text": "External costs are private benefits"},
                        {"label": "C", "text": "External costs remove scarcity"},
                        {"label": "D", "text": "External costs only affect suppliers"},
                    ],
                    "correct_option": "A",
                    "mark_scheme": ["The only correct answer is A"],
                },
            ],
        }


class NoisyOllamaClient:
    def generate_json(self, prompt: str) -> dict[str, object]:
        return {
            "question_text": "Explain one effect of market failure. [5 marks]",
            "source_text": "This source concerns labour market. It may include evidence on demand for labour.",
            "parts": [
                {"label": "a", "prompt": "Explain one effect of market failure. [4 marks]"},
                {"label": "b", "prompt": "Which one of the following is correct? [1 mark]"},
            ],
        }


class DriftedPartsOllamaClient:
    def generate_json(self, prompt: str) -> dict[str, object]:
        return {
            "question_text": "Evaluate whether the benefits of the labour market outweigh the costs, considering both positive and negative impacts.",
            "mark_scheme": [],
            "parts": [
                {"label": "a", "prompt": "Draw a diagram and explain your answer.", "mark_scheme": []},
                {"label": "b", "prompt": "Which one of the following is correct?", "mark_scheme": []},
            ],
        }


class OverlongSectionASourceClient:
    def generate_json(self, prompt: str) -> dict[str, object]:
        return {
            "source_text": (
                "In an online marketplace, consumers see many conflicting claims about product quality, "
                "side effects, delivery times and prices. Some reviews are paid for by sellers, some are "
                "out of date, and some compare products that are not close substitutes, which means the "
                "source text is too long for a Section A context box."
            )
        }


def test_generate_questions_with_ollama_keeps_source_and_mark_scheme():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=5)

    enriched = generate_questions_with_ollama(FakeOllamaClient(), blueprint, syllabus)

    assert enriched.questions[0].prompt == blueprint.questions[0].prompt
    assert enriched.questions[5].prompt == "With reference to Extract A, explain one likely impact of externalities in this market."
    assert enriched.questions[0].source_text == "A market creates external costs for third parties."
    assert enriched.questions[0].source_reference == "Extract A"
    assert enriched.questions[0].mark_breakdown == "Knowledge 1, Application 2, Analysis 2"
    assert enriched.questions[0].indicative_content == ["external costs", "third parties"]
    assert enriched.questions[0].mark_scheme == ["Defines external costs", "Applies to context"]
    assert enriched.questions[0].parts[1].correct_option == "A"
    assert enriched.questions[0].parts[1].options[0].text == "External costs affect third parties"


def test_generate_questions_with_ollama_strips_bracketed_marks_and_keeps_better_sources():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=8464)

    enriched = generate_questions_with_ollama(NoisyOllamaClient(), blueprint, syllabus)
    first = enriched.questions[0]

    assert first.prompt == blueprint.questions[0].prompt
    assert "[5 marks]" not in first.prompt
    assert "[4 marks]" not in first.parts[0].prompt
    assert first.source_text == blueprint.questions[0].source_text


def test_generate_questions_with_ollama_rejects_overlong_section_a_sources():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=8464)

    enriched = generate_questions_with_ollama(OverlongSectionASourceClient(), blueprint, syllabus)

    assert enriched.questions[0].source_text == blueprint.questions[0].source_text


def test_generate_questions_with_ollama_rejects_drifted_section_b_wording():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=8464)

    enriched = generate_questions_with_ollama(NoisyOllamaClient(), blueprint, syllabus)

    assert enriched.questions[5].prompt == blueprint.questions[5].prompt


def test_generate_questions_with_ollama_cleans_essay_and_draw_prompt_drift():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=8464)

    enriched = generate_questions_with_ollama(DriftedPartsOllamaClient(), blueprint, syllabus)
    q5 = next(question for question in enriched.questions if question.number == "5")
    q7 = next(question for question in enriched.questions if question.number == "7")

    assert "explain your answer" not in q5.parts[0].prompt.lower()
    assert "positive and negative" not in q7.prompt.lower()


def test_generate_questions_with_ollama_preserves_fallback_mark_schemes_when_llm_returns_empty_lists():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=8464)

    enriched = generate_questions_with_ollama(DriftedPartsOllamaClient(), blueprint, syllabus)
    first = enriched.questions[0]

    assert first.mark_scheme == blueprint.questions[0].mark_scheme
    assert first.parts[0].mark_scheme == blueprint.questions[0].parts[0].mark_scheme
    assert first.parts[1].mark_scheme == blueprint.questions[0].parts[1].mark_scheme


def test_generate_questions_with_ollama_reports_question_progress():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=5)
    events = []

    generate_questions_with_ollama(FakeOllamaClient(), blueprint, syllabus, progress=events.append)

    assert events[0].startswith("Generating question 1/12: 1 ")
    assert events[-1].startswith("Generated question 12/12: 8 ")
