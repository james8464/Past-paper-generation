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


class ShortSectionBSourceClient:
    def generate_json(self, prompt: str) -> dict[str, object]:
        return {
            "question_text": "With reference to Extract A, explain one likely impact of externalities in this market.",
            "source_text": (
                "A short extract gives some context about market failure and possible government intervention. "
                "It mentions costs, consumers and firms, but it is too brief to look like a full data-response source."
                " The regulator is considering a tax, a subsidy or direct rules to change incentives, while firms "
                "argue that higher costs could be passed on to consumers. The final effect depends on elasticity, "
                "information and whether the intervention is targeted accurately."
            ),
        }


class LabelledVaguePartsClient:
    def generate_json(self, prompt: str) -> dict[str, object]:
        return {
            "parts": [
                {"label": "a", "prompt": "(a) Draw a vague diagram and explain your answer."},
                {"label": "b", "prompt": "(b) Which one of the following is correct?"},
            ]
        }


class FigureReferencePartsClient:
    def generate_json(self, prompt: str) -> dict[str, object]:
        return {
            "parts": [
                {"label": "a", "prompt": "Explain one reason why the firm in Figure 1 may earn supernormal profit."},
                {"label": "b", "prompt": "Which one of the following is correct?"},
            ]
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


def test_generate_questions_with_ollama_rejects_short_section_b_sources():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)

    enriched = generate_questions_with_ollama(ShortSectionBSourceClient(), blueprint, syllabus)
    section_b = [question for question in enriched.questions if question.section == "B"]

    assert min(len(question.source_text) for question in section_b) >= 700


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
    q3 = next(question for question in enriched.questions if question.number == "3")
    q7 = next(question for question in enriched.questions if question.number == "7")

    assert "explain your answer" not in q3.parts[0].prompt.lower()
    assert "positive and negative" not in q7.prompt.lower()


def test_generate_questions_with_ollama_strips_part_labels_and_preserves_layout_safe_draw_prompts():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=8464)

    enriched = generate_questions_with_ollama(LabelledVaguePartsClient(), blueprint, syllabus)

    for question in enriched.questions:
        for part in question.parts:
            assert not part.prompt.lower().startswith(f"({part.label})")
            assert not part.prompt.lower().startswith(f"{part.label})")
            if part.command_word == "draw":
                assert "explain your answer" not in part.prompt.lower()


def test_generate_questions_with_ollama_normalises_unlabelled_figure_references():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=12397218355689870975)

    enriched = generate_questions_with_ollama(FigureReferencePartsClient(), blueprint, syllabus)
    explain_parts = [
        part
        for question in enriched.questions
        for part in question.parts
        if part.command_word == "explain"
    ]

    assert explain_parts
    assert all("Figure 1" not in part.prompt for part in explain_parts)
    assert any("the diagram" in part.prompt.lower() for part in explain_parts)


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
