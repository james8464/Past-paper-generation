from pathlib import Path

from pastpapergen.generator import build_paper_blueprint
from pastpapergen.ollama_client import generate_questions_with_ollama
from pastpapergen.paper_configs import load_builtin_paper_config
from pastpapergen.syllabus import load_syllabus


class FakeOllamaClient:
    def generate_json(self, prompt: str) -> dict[str, object]:
        return {
            "question_text": "Analyse the impact of externalities in this market.",
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


def test_generate_questions_with_ollama_keeps_source_and_mark_scheme():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=5)

    enriched = generate_questions_with_ollama(FakeOllamaClient(), blueprint, syllabus)

    assert enriched.questions[0].prompt == "Analyse the impact of externalities in this market."
    assert enriched.questions[0].source_text == "A market creates external costs for third parties."
    assert enriched.questions[0].source_reference == "Extract A"
    assert enriched.questions[0].mark_breakdown == "Knowledge 1, Application 2, Analysis 2"
    assert enriched.questions[0].indicative_content == ["external costs", "third parties"]
    assert enriched.questions[0].mark_scheme == ["Defines external costs", "Applies to context"]
    assert enriched.questions[0].parts[1].correct_option == "A"
    assert enriched.questions[0].parts[1].options[0].text == "External costs affect third parties"


def test_generate_questions_with_ollama_reports_question_progress():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=5)
    events = []

    generate_questions_with_ollama(FakeOllamaClient(), blueprint, syllabus, progress=events.append)

    assert events[0].startswith("Generating question 1/12: 1 ")
    assert events[-1].startswith("Generated question 12/12: 8 ")
