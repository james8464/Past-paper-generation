import random
import threading
import time

import pytest
from cspapergen.generator import (
    PAPER2_QUESTION_PLAN,
    QUESTION_TOTALS,
    build_paper1_blueprint,
    build_paper2_blueprint,
    build_topic_question_bank,
)
from cspapergen.ollama_client import (
    _merge_question,
    _prompt,
    improve_questions_with_ollama,
)
from cspapergen.question_bank import QUESTION_STYLES, STYLE_IDS, build_question
from cspapergen.syllabus import load_syllabus


def test_blueprint_is_deterministic_for_seed():
    syllabus = load_syllabus()

    first = build_paper2_blueprint(syllabus, seed=123)
    second = build_paper2_blueprint(syllabus, seed=123)

    assert first.model_dump() == second.model_dump()


def test_all_supported_assessments_keep_code_inside_the_renderable_width() -> None:
    syllabus = load_syllabus()
    paper_one, _ = build_paper1_blueprint(syllabus, seed=26080116)
    assessments = [
        paper_one,
        build_paper2_blueprint(syllabus, seed=26080116),
        *(build_topic_question_bank(syllabus, topic_id=topic, seed=26080116)
          for topic in ("4.2", "4.10", "4.12")),
    ]

    assert all(
        len(line) <= 58
        for assessment in assessments
        for question in assessment.questions
        if question.stimulus
        for line in question.stimulus.code.splitlines()
    )


def test_blueprint_totals_100_marks_and_uses_paper2_topics_only():
    syllabus = load_syllabus()
    blueprint = build_paper2_blueprint(syllabus, seed=7)

    assert blueprint.total_marks == 100
    assert sum(part.marks for question in blueprint.questions for part in question.parts) == 100
    assert [question.total_marks for question in blueprint.questions] == QUESTION_TOTALS
    assert len(blueprint.questions) == 14
    assert {question.topic_id for question in blueprint.questions} <= syllabus.topic_ids
    assert all(question.topic_id.startswith(("4.5", "4.6", "4.7", "4.8", "4.9", "4.10", "4.11", "4.12")) for question in blueprint.questions)


def test_paper_one_binary_search_uses_a_separate_identifier_index() -> None:
    blueprint, _ = build_paper1_blueprint(load_syllabus(), seed=26080115)
    question = blueprint.questions[7]

    assert "separate identifier index" in question.stem
    assert "identifier index" in question.parts[0].prompt
    assert question.parts[0].answer_lines == 1
    assert question.parts[0].marking.points == [
        "The index must be ordered by identifier;"
    ]


def test_paper_two_uses_specification_aligned_bitmap_storage() -> None:
    blueprint = build_paper2_blueprint(load_syllabus(), seed=26080116)
    question = blueprint.questions[2]

    assert question.style_id == "bitmap_storage"
    assert question.title == "Bitmap storage"
    assert question.stimulus is not None
    assert question.stimulus.kind == "table"
    assert "uncompressed file size" in question.parts[0].prompt
    assert any("MiB" in point for point in question.parts[0].marking.points)


def test_blueprint_varies_between_unseeded_runs():
    syllabus = load_syllabus()

    first = build_paper2_blueprint(syllabus)
    second = build_paper2_blueprint(syllabus)

    assert first.model_dump() != second.model_dump()


def test_seeded_runs_keep_reference_question_styles_and_vary_content():
    syllabus = load_syllabus()

    blueprints = [build_paper2_blueprint(syllabus, seed=seed) for seed in range(40)]

    expected_styles = [style_id for style_id, _marks in PAPER2_QUESTION_PLAN]
    assert all(
        [question.style_id for question in paper.questions] == expected_styles
        for paper in blueprints
    )
    assert len({paper.model_dump_json() for paper in blueprints}) > 1


def test_paper_2_uses_reference_part_mark_pattern():
    blueprint = build_paper2_blueprint(load_syllabus(), seed=7)

    assert [
        tuple(part.marks for part in question.parts)
        for question in blueprint.questions
    ] == [marks for _style_id, marks in PAPER2_QUESTION_PLAN]


def test_all_question_styles_are_specific_to_the_aqa_specification():
    syllabus = load_syllabus()

    assert {style.topic_id for style in QUESTION_STYLES} <= syllabus.topic_ids
    styles = {style.id: style for style in QUESTION_STYLES}
    assert all(
        styles[style_id].topic_id.startswith(
            ("4.5", "4.6", "4.7", "4.8", "4.9", "4.10", "4.11", "4.12")
        )
        for style_id, _marks in PAPER2_QUESTION_PLAN
    )


def test_question_bank_covers_expected_aqa_paper2_styles():
    expected = {
        "bitmap_size",
        "sound_sampling",
        "rle_compression",
        "floating_point",
        "logic_truth_table",
        "truth_table_completion",
        "boolean_algebra",
        "processor_buses",
        "packet_switching",
        "network_topology",
        "sql_normalisation",
        "big_data",
        "functional_programming",
        "ethics_extended",
    }

    assert expected <= STYLE_IDS


@pytest.mark.parametrize(
    ("topic_id", "expected_styles"),
    [
        (
            "4.2",
            {
                "data_structures_stack_queue",
                "data_structures_hash",
                "data_structures_tree",
                "data_structures_graph",
                "data_structures_choice",
            },
        ),
        ("4.10", {"sql_normalisation", "erd_keys", "database_extended"}),
        (
            "4.12",
            {
                "functional_programming",
                "functional_recursion",
                "functional_type_short",
                "functional_extended",
            },
        ),
    ],
)
def test_topic_question_banks_are_focused_and_mark_complete(
    topic_id: str,
    expected_styles: set[str],
) -> None:
    bank = build_topic_question_bank(load_syllabus(), topic_id=topic_id, seed=42)

    assert bank.assessment_kind == "question-bank"
    assert bank.focus_topic_id == topic_id
    assert bank.paper_code == "7517/QB"
    assert bank.paper_number == "QB"
    assert bank.total_marks == 30
    assert sum(question.total_marks for question in bank.questions) == 30
    assert {question.topic_id for question in bank.questions} == {topic_id}
    assert {question.style_id for question in bank.questions} == expected_styles


def test_topic_question_bank_rejects_an_unsupported_topic() -> None:
    with pytest.raises(ValueError, match="No question bank is available"):
        build_topic_question_bank(load_syllabus(), topic_id="4.99", seed=42)


def test_packet_stimulus_is_introduced_as_figure_context():
    style = next(style for style in QUESTION_STYLES if style.id == "packet_switching")

    question = build_question(style, number=6, total=10, rng=random.Random(1))

    assert "Figure 1" in question.stem
    assert "packet" in question.stem.lower()


def test_software_classification_stimulus_contains_only_consistent_categories() -> None:
    style = next(
        style for style in QUESTION_STYLES if style.id == "software_classification"
    )
    question = build_question(style, number=1, total=8, rng=random.Random(1))

    assert question.stimulus is not None
    assert question.stimulus.diagram.endswith("Utility software|Translators")
    comparison = question.parts[2]
    assert all("1 mark" in point for point in comparison.marking.points)


def test_functional_type_stimulus_uses_renderable_exam_notation():
    style = next(style for style in QUESTION_STYLES if style.id == "functional_type_short")

    question = build_question(style, number=1, total=4, rng=random.Random(1))

    assert question.stimulus is not None
    assert question.stimulus.code == "f: Natural -> Real"


def test_new_visual_styles_have_renderable_stimuli():
    truth_style = next(style for style in QUESTION_STYLES if style.id == "truth_table_completion")
    network_style = next(style for style in QUESTION_STYLES if style.id == "network_topology")

    truth_question = build_question(truth_style, number=4, total=8, rng=random.Random(2))
    network_question = build_question(network_style, number=5, total=8, rng=random.Random(3))

    assert truth_question.stimulus is not None
    assert truth_question.stimulus.kind == "truth_table"
    assert truth_question.stimulus.headers == ["A", "B", "C", "X"]
    assert network_question.stimulus is not None
    assert network_question.stimulus.kind == "network"


def test_hosted_question_generation_runs_independent_prompts_concurrently():
    class HostedTestClient:
        supports_parallel_generation = True

        def __init__(self) -> None:
            self.active = 0
            self.maximum_active = 0
            self.lock = threading.Lock()

        def generate_json(self, _prompt: str) -> dict[str, object]:
            with self.lock:
                self.active += 1
                self.maximum_active = max(self.maximum_active, self.active)
            time.sleep(0.01)
            with self.lock:
                self.active -= 1
            return {}

    syllabus = load_syllabus()
    blueprint = build_paper2_blueprint(syllabus, seed=7)
    client = HostedTestClient()

    with pytest.raises(ValueError, match="only a paraphrase"):
        improve_questions_with_ollama(client, blueprint, syllabus)

    assert client.maximum_active == 4


def test_local_generation_retries_only_the_rejected_question():
    syllabus = load_syllabus()
    full_blueprint = build_paper2_blueprint(syllabus, seed=7)
    blueprint = full_blueprint.model_copy(
        update={"questions": full_blueprint.questions[2:3]}
    )
    original = blueprint.questions[0]

    class FlakyClient:
        supports_parallel_generation = False

        def __init__(self) -> None:
            self.authoring_calls = 0

        def generate_json(self, prompt: str) -> dict[str, object]:
            if "second-pass UK A-level assessment editor" in prompt:
                return {
                    "approved": True,
                    "factual_issues": [],
                    "marking_issues": [],
                    "source_issues": [],
                    "difficulty_issues": [],
                    "ambiguity_issues": [],
                }
            self.authoring_calls += 1
            if self.authoring_calls == 1:
                return {}
            return {
                "stem": "A coastal research service is planning a new software system.",
                "parts": [
                    {
                        "label": part.label,
                        "prompt": f"{part.prompt} Apply the answer to the coastal research service.",
                        "marking_points": ["One valid model-authored technical point;"],
                        "accept": [],
                        "reject": [],
                    }
                    for part in original.parts
                ],
            }

    client = FlakyClient()
    improved = improve_questions_with_ollama(client, blueprint, syllabus)

    assert client.authoring_calls == 3
    assert improved.questions[0] == original


def test_local_generation_stops_before_queued_question_after_failure() -> None:
    syllabus = load_syllabus()
    full_blueprint = build_paper2_blueprint(syllabus, seed=7)
    blueprint = full_blueprint.model_copy(
        update={"questions": full_blueprint.questions[2:4]}
    )

    class RejectingClient:
        supports_parallel_generation = False

        def __init__(self) -> None:
            self.authoring_calls = 0

        def generate_json(self, prompt: str) -> dict[str, object]:
            if "second-pass UK A-level assessment editor" in prompt:
                return {}
            self.authoring_calls += 1
            return {}

    client = RejectingClient()
    with pytest.raises(ValueError, match="failed after 3 reviewed attempts"):
        improve_questions_with_ollama(client, blueprint, syllabus)

    assert client.authoring_calls == 3


def test_local_generation_uses_reviewed_seeded_fallback_after_paraphrases() -> None:
    syllabus = load_syllabus()
    full_blueprint = build_paper1_blueprint(syllabus, seed=26080115)[0]
    question = full_blueprint.questions[8]
    blueprint = full_blueprint.model_copy(update={"questions": [question]})

    class ParaphrasingClient:
        supports_parallel_generation = False

        def __init__(self) -> None:
            self.authoring_calls = 0

        def generate_json(self, prompt: str) -> dict[str, object]:
            if "second-pass UK A-level assessment editor" in prompt:
                return {
                    "approved": True,
                    "factual_issues": [],
                    "marking_issues": [],
                    "source_issues": [],
                    "difficulty_issues": [],
                    "ambiguity_issues": [],
                }
            self.authoring_calls += 1
            return {
                "stem": question.stem,
                "parts": [
                    {"label": part.label, "prompt": part.prompt}
                    for part in question.parts
                ],
            }

    client = ParaphrasingClient()
    generated = improve_questions_with_ollama(client, blueprint, syllabus)

    assert client.authoring_calls == 3
    assert generated.questions == [question]


def test_paper_one_boundary_test_has_one_mark_of_evidence() -> None:
    blueprint, _ = build_paper1_blueprint(load_syllabus(), seed=26080115)
    boundary = blueprint.questions[8].parts[1]

    assert boundary.marks == 1
    assert boundary.marking.points == [
        "Use 0 or 100 and expect the value to be accepted;"
    ]


def test_paper_one_safe_value_function_matches_displayed_code() -> None:
    blueprint, _ = build_paper1_blueprint(load_syllabus(), seed=26080115)
    question = blueprint.questions[9]
    part = question.parts[0]

    assert question.stimulus is not None
    assert "def adjusted_value(raw_value):" in question.stimulus.code
    assert "Return None" in question.stimulus.code
    assert "Convert raw_value to an integer" in part.prompt
    assert "converted integer value" in part.prompt
    assert len(part.marking.points) == 7
    assert all(point.startswith("1 mark:") for point in part.marking.points)
    assert any("ValueError" in point for point in part.marking.points)
    assert any("None is returned" in point for point in part.marking.points)


def test_paper_one_report_task_has_objective_partial_credit() -> None:
    blueprint, context = build_paper1_blueprint(load_syllabus(), seed=26080115)
    question = blueprint.questions[11]
    implementation, tie_test, _explanation = question.parts

    assert "descending adjusted-total order" in context.skeleton_program
    assert "descending adjusted-total order" in implementation.prompt
    assert implementation.marks == len(implementation.marking.points) == 11
    assert all(point.startswith("1 mark:") for point in implementation.marking.points)
    assert not any("readable" in point for point in implementation.marking.points)
    assert "record.identifier" in implementation.prompt
    assert any("leaves the records list" in point for point in implementation.marking.points)
    assert "input data set" in tie_test.prompt
    assert "expected output order" in tie_test.prompt


def test_skeleton_program_task_is_reviewed_without_rewriting_its_contract() -> None:
    syllabus = load_syllabus()
    full_blueprint = build_paper1_blueprint(syllabus, seed=26080115)[0]
    question = full_blueprint.questions[11]
    blueprint = full_blueprint.model_copy(update={"questions": [question]})

    class ReviewClient:
        supports_parallel_generation = False
        authoring_calls = 0

        def generate_json(self, prompt: str) -> dict[str, object]:
            if "second-pass UK A-level assessment editor" not in prompt:
                self.authoring_calls += 1
            return {
                "approved": True,
                "factual_issues": [],
                "marking_issues": [],
                "source_issues": [],
                "difficulty_issues": [],
                "ambiguity_issues": [],
            }

    client = ReviewClient()
    generated = improve_questions_with_ollama(client, blueprint, syllabus)

    assert client.authoring_calls == 0
    assert generated.questions == [question]


def test_paper_two_floating_point_convention_and_marks_are_unambiguous() -> None:
    blueprint = build_paper2_blueprint(load_syllabus(), seed=26080116)
    question = blueprint.questions[11]

    assert [part.marks for part in question.parts] == [1, 1, 1, 2, 3, 1]
    assert "State whether the binary point" in question.parts[0].prompt
    assert "copied" not in " ".join(question.parts[0].marking.points).casefold()
    assert "binary point is immediately after the mantissa sign bit" in question.parts[1].prompt
    conversion = question.parts[1].marking.points[0]
    assert "-1 + 1/4 + 1/16 = -0.6875" in conversion
    assert "-0.6875 × 2² = -2.75" in conversion
    assert "starts 01 when positive or 10 when negative" in question.parts[2].marking.points[0]
    scoring_points = question.parts[4].marking.points[:3]
    assert len(scoring_points) == 3
    assert all(point.startswith("1 mark:") for point in scoring_points)
    assert "range" in " ".join(question.parts[4].marking.points).casefold()
    assert "precision" in " ".join(question.parts[4].marking.points).casefold()
    assert question.parts[5].marking.points[0] == "1 mark: underflow;"


def test_paper_two_assembly_program_defines_isa_and_six_distinct_marks() -> None:
    blueprint = build_paper2_blueprint(load_syllabus(), seed=26080116)
    question = blueprint.questions[13]
    part = question.parts[0]

    assert "STR R0, [100]" in question.stimulus.code
    assert "LSR performs a zero-fill logical right shift" in part.prompt
    assert part.marks == len(part.marking.points[:6]) == 6
    assert sum(point.startswith("Purpose — 1 mark:") for point in part.marking.points) == 3
    assert sum(point.startswith("Implementation — 1 mark:") for point in part.marking.points) == 3
    assert any("binary bit length" in point for point in part.marking.points)


def test_ai_cannot_detach_wording_from_immutable_stimulus() -> None:
    blueprint = build_paper2_blueprint(load_syllabus(), seed=26080116)
    question = blueprint.questions[5]
    candidate = _merge_question(
        question,
        {
            "stem": "An unrelated inventory system stores stock values.",
            "parts": [
                {"label": part.label, "prompt": "Answer an unrelated question."}
                for part in question.parts
            ],
        },
    )

    assert candidate.stem == question.stem
    assert [part.prompt for part in candidate.parts] == [
        part.prompt for part in question.parts
    ]


def test_database_question_has_exact_command_and_mark_coverage() -> None:
    blueprint = build_paper2_blueprint(load_syllabus(), seed=26080116)
    question = blueprint.questions[5]

    assert [part.marks for part in question.parts] == [2, 3, 2, 3, 2]
    assert question.stimulus is not None
    assert "fitness centre" in question.stem
    assert all(name in question.stimulus.code for name in ("MEMBER", "SESSION", "BOOKING"))
    assert all(len(line) <= 58 for line in question.stimulus.code.splitlines())
    prompts = " ".join(part.prompt for part in question.parts).upper()
    assert all(command in prompts for command in ("SELECT", "INSERT", "UPDATE", "DELETE"))
    assert "ERROR" in prompts
    assert all(part.marking.points for part in question.parts)
    assert all(part.marking.ao == "AO3 (programming)" for part in question.parts)


def test_boolean_questions_use_exam_notation_instead_of_programming_punctuation() -> None:
    blueprint = build_paper2_blueprint(load_syllabus(), seed=26080116)
    boolean_questions = (blueprint.questions[8], blueprint.questions[12])

    for question in boolean_questions:
        assert question.stimulus is not None
        visible_notation = " ".join(
            [question.stimulus.code, *(part.prompt for part in question.parts)]
        )
        assert not any(token in visible_notation for token in ("A.B", "A.C", ").("))
        assert any(symbol in visible_notation for symbol in ("·", "+", "⊕", "⊼", "⊽", "̅"))


def test_stored_program_question_has_exact_command_and_mark_coverage() -> None:
    blueprint = build_paper2_blueprint(load_syllabus(), seed=26080116)
    question = blueprint.questions[6]

    assert [part.marks for part in question.parts] == [2, 6, 1, 1]
    assert question.parts[1].prompt.startswith("Describe how one instruction")
    cycle_guidance = " ".join(question.parts[1].marking.points).casefold()
    assert all(bus in cycle_guidance for bus in ("address bus", "data bus", "control bus"))
    assert len(question.parts[1].marking.points) == 6
    assert question.parts[2].prompt.startswith("State the role")
    assert question.parts[3].prompt.startswith("State one benefit")


def test_truth_table_question_has_row_specific_marking() -> None:
    blueprint = build_paper2_blueprint(load_syllabus(), seed=26080116)
    question = blueprint.questions[8]

    assert [part.marks for part in question.parts] == [4, 2, 1]
    assert question.parts[0].marking.points[:4] == [
        "Row 1: X = 1;",
        "Row 2: X = 1;",
        "Row 3: X = 0;",
        "Row 4: X = 0;",
    ]
    assert "1 mark for A and B" in question.parts[1].marking.points[0]
    assert question.parts[2].prompt.startswith("Explain one reason")
    expression = question.parts[0].prompt
    assert not any(word in expression for word in (" AND ", " OR ", " NOT ", " XOR "))
    assert any(symbol in expression for symbol in ("·", "+", "⊕", "¬"))


def test_paper_two_question_eleven_is_unmistakably_functional() -> None:
    blueprint = build_paper2_blueprint(load_syllabus(), seed=26080116)
    question = blueprint.questions[10]

    assert question.topic_id == "4.12"
    assert question.stimulus is not None
    functional_content = " ".join(
        [question.title, question.stem, question.stimulus.code]
        + [part.prompt for part in question.parts]
        + [point for part in question.parts for point in part.marking.points]
    ).casefold()
    assert "pattern matching" in functional_content
    assert "immutable" in functional_content
    assert "pure function" in functional_content


def test_sound_calculation_scheme_includes_the_canonical_final_answer() -> None:
    blueprint = build_paper2_blueprint(load_syllabus(), seed=26080116)
    part = blueprint.questions[1].parts[0]

    assert any("mib" in point.casefold() and "=" in point for point in part.marking.points)


def test_contextual_compression_scheme_names_the_scenario_consequence() -> None:
    blueprint = build_paper2_blueprint(load_syllabus(), seed=26080116)
    question = blueprint.questions[9]
    scenario = question.stem.casefold()
    guidance = " ".join(question.parts[1].marking.points).casefold()

    assert any(
        term in guidance
        for term in ("diagnos", "executable", "backup", "archive", "financial")
    )
    assert any(term in scenario for term in ("medical", "software", "financial"))


def test_repetitive_examiner_guidance_is_not_attached_to_every_part() -> None:
    blueprint = build_paper2_blueprint(load_syllabus(), seed=26080116)
    repeated = (
        "credit precise technical terminology",
        "do not award the same technical point twice",
        "apply the guidance specifically",
    )

    assert not any(
        phrase in point.casefold()
        for question in blueprint.questions
        for part in question.parts
        for point in part.marking.points
        for phrase in repeated
    )


def test_generated_part_with_new_quantity_keeps_verified_prompt() -> None:
    syllabus = load_syllabus()
    blueprint, _ = build_paper1_blueprint(syllabus, seed=26080115)
    question = blueprint.questions[3]
    original_part = question.parts[0]

    merged = _merge_question(
        question,
        {
            "stem": "A benchmark compares 10 alternative implementations.",
            "parts": [
                {
                    "label": original_part.label,
                    "prompt": f"{original_part.prompt} Repeat the trial 10 times.",
                    "marking_points": original_part.marking.points,
                }
            ],
        },
    )

    assert merged.stem == question.stem
    assert merged.parts[0].prompt == original_part.prompt


def test_numeric_heavy_multipart_prompt_requests_only_a_new_scenario() -> None:
    syllabus = load_syllabus()
    blueprint = build_paper2_blueprint(syllabus, seed=7)
    question = next(
        question
        for question in blueprint.questions
        if len(question.parts) >= 4
        and any(character.isdigit() for part in question.parts for character in part.prompt)
    )
    topic = syllabus.get_topic(question.topic_id)

    prompt = _prompt(question, topic.title, "notes", blueprint)

    assert '"parts": []' in prompt
    assert "Do not repeat, rewrite or answer the parts" in prompt

    paper_one = build_paper1_blueprint(syllabus, seed=26080115)[0]
    finite_state = paper_one.questions[5]
    finite_state_prompt = _prompt(
        finite_state,
        syllabus.get_topic(finite_state.topic_id).title,
        "notes",
        paper_one,
    )
    assert "Preserve these numeric tokens from the draft stem exactly: 1, 0" in (
        finite_state_prompt
    )

    optical = blueprint.questions[2]
    optical_prompt = _prompt(
        optical,
        syllabus.get_topic(optical.topic_id).title,
        "notes",
        blueprint,
    )
    assert (
        f"Immutable assessment focus: {optical.title} "
        f"({optical.style_id})" in optical_prompt
    )
    assert "Do not substitute another subtopic" in optical_prompt


def test_scenario_only_generation_uses_deterministic_subpart_review() -> None:
    syllabus = load_syllabus()
    full_blueprint = build_paper1_blueprint(syllabus, seed=26080115)[0]
    question = full_blueprint.questions[2]
    blueprint = full_blueprint.model_copy(update={"questions": [question]})

    class ScenarioClient:
        supports_parallel_generation = False

        def __init__(self) -> None:
            self.authoring_calls = 0

        def generate_json(self, prompt: str) -> dict[str, object]:
            if "second-pass UK A-level assessment editor" in prompt:
                return {
                    "approved": True,
                    "factual_issues": [],
                    "marking_issues": [],
                    "source_issues": [],
                    "difficulty_issues": [],
                    "ambiguity_issues": [],
                }
            self.authoring_calls += 1
            return {
                "stem": (
                    "A rescue coordination service stores route connections as an "
                    "adjacency list and searches them recursively."
                ),
                "parts": [],
            }

    client = ScenarioClient()
    generated = improve_questions_with_ollama(
        client,
        blueprint,
        syllabus,
    )

    assert generated.questions[0].parts == question.parts
    assert generated.questions[0].stem == question.stem
    assert client.authoring_calls == 3


def test_scenario_only_generation_restores_immutable_stem_numbers() -> None:
    syllabus = load_syllabus()
    full_blueprint = build_paper1_blueprint(syllabus, seed=26080115)[0]
    question = full_blueprint.questions[5]
    blueprint = full_blueprint.model_copy(update={"questions": [question]})

    class ScenarioClient:
        supports_parallel_generation = False

        def generate_json(self, prompt: str) -> dict[str, object]:
            if "second-pass UK A-level assessment editor" in prompt:
                return {
                    "approved": True,
                    "factual_issues": [],
                    "marking_issues": [],
                    "source_issues": [],
                    "difficulty_issues": [],
                    "ambiguity_issues": [],
                }
            return {
                "stem": "A museum validates compact binary access codes.",
                "parts": [],
            }

    generated = improve_questions_with_ollama(
        ScenarioClient(),
        blueprint,
        syllabus,
    ).questions[0]

    assert generated.stem == question.stem
