import ast
from decimal import Decimal
from io import BytesIO
from pathlib import Path

import pymupdf
import pytest
from pastpapergen.generator import build_paper_blueprint
from pastpapergen.ollama_client import _question_solver_item, _review_specification
from pastpapergen.paper_configs import load_builtin_paper_config
from pastpapergen.render_pdf import (
    _draw_paper_3_source_page,
    _draw_stimulus,
    _mark_scheme_rows,
    candidate_stimulus_data,
)
from pastpapergen.syllabus import load_syllabus
from reportlab.pdfgen.canvas import Canvas

from Backend.Core.independent_solver import (
    IndependentSolver,
    require_solution_matches_scheme,
)
from tests.support.edexcel import forced_part


def paper(number, seed):
    return build_paper_blueprint(
        load_builtin_paper_config(f"paper_{number}"),
        load_syllabus(Path(__file__).parents[1] / "data/syllabus_seed.json"),
        seed,
    )


def test_contestability_credit_is_specific_and_has_one_consistent_budget():
    q = paper(1, 26083049).questions[0]
    part = q.parts[0]
    assert q.stimulus_kind == "contestability_barrier_table"
    assert part.assessment_objectives == {"AO1": 2, "AO2": 1, "AO3": 1}
    text = " ".join(part.mark_scheme + part.indicative_content).lower()
    assert "sunk" in text and "entry" in text
    assert "tesco" not in text and "defines market structures" not in text
    assert q.parts[1].marks == 1
    assert q.mark_scheme == []  # parent summaries cannot create duplicate credit


@pytest.mark.parametrize("seed", [26083122, 26083123, 26083124, 26083159])
def test_live_calculation_has_source_bound_independent_solution(seed):
    q = paper(2, seed).questions[0]
    part = next(p for p in q.parts if p.command_word == "calculate")
    solution = IndependentSolver().solve(_question_solver_item(q, part), [])
    require_solution_matches_scheme(solution, _question_solver_item(q, part))
    assert solution.verified_scope == "declared-numeric-outputs-only"
    assert solution.numeric_checks
    assert candidate_stimulus_data(q)["values"] == [
        float(x) for x in q.source_instance.values
    ]


def test_seeded_sources_are_instances_not_style_constants():
    a = paper(2, 26083122).questions[0]
    b = paper(2, 26083159).questions[0]
    assert a.stimulus_kind == b.stimulus_kind == "household_savings_line_chart"
    assert a.source_instance.values != b.source_instance.values
    assert a.source_instance == paper(2, 26083122).questions[0].source_instance


def test_line_source_numbers_and_time_labels_are_printed():
    q = paper(2, 26083122).questions[0]
    source = q.source_instance.model_copy(
        update={
            "values": [Decimal("-4.3"), Decimal("0"), Decimal("2.1")],
            "labels": ["Year 1", "Year 2", "Year 3"],
        }
    )
    data = BytesIO()
    canvas = Canvas(data)
    _draw_stimulus(canvas, q.stimulus_kind, 104, 700, source_instance=source)
    canvas.save()
    with pymupdf.open(stream=data.getvalue(), filetype="pdf") as document:
        text = " ".join(document[0].get_text().split())
    for label in ["-4.3", "0", "2.1", "Year 1", "Year 2", "Year 3"]:
        assert label in text


def test_review_does_not_claim_hidden_context_is_printed():
    q = paper(2, 26083122).questions[0]
    specification = _review_specification(
        load_syllabus(Path(__file__).parents[1] / "data/syllabus_seed.json").get_topic(
            q.topic_id
        ),
        q,
    )
    assert (
        specification["rendered_stimulus"]["source_text"] == q.source_instance.context
    )
    assert (
        "complete stimulus/source text is rendered"
        not in specification["rendered_stimulus"]["placement"]
    )


def test_candidate_context_renderer_never_silently_elides_source_ending():
    from pastpapergen.render_pdf import _draw_context_box, _draw_inline_context

    text = (
        " ".join(["A producer has spare capacity and delayed contracts."] * 8)
        + " The tax is wholly absorbed by overseas suppliers."
    )
    for draw in (_draw_context_box, _draw_inline_context):
        output = BytesIO()
        canvas = Canvas(output)
        if draw is _draw_context_box:
            draw(canvas, 82, 760, text)
        else:
            draw(canvas, text, 80, 760)
        canvas.save()
        with pymupdf.open(stream=output.getvalue(), filetype="pdf") as document:
            printed = " ".join(document[0].get_text().split())
        assert "The tax is wholly absorbed by overseas suppliers." in printed


def test_section_heading_and_instructions_clear_the_answer_frame():
    from pastpapergen.render_pdf import (
        ANSWER_FRAME_H,
        ANSWER_FRAME_Y,
        _draw_section_intro,
        _prepare_answer_page,
    )

    output = BytesIO()
    canvas = Canvas(output)
    blueprint = paper(2, 26083031)
    y = _prepare_answer_page(canvas, blueprint, 2)
    _draw_section_intro(canvas, blueprint, "A", y)
    canvas.save()
    with pymupdf.open(stream=output.getvalue(), filetype="pdf") as document:
        page = document[0]
        frame_top = page.rect.height - ANSWER_FRAME_Y - ANSWER_FRAME_H
        assert page.search_for("SECTION A")[0].y0 >= frame_top + 26


@pytest.mark.parametrize("number", [1, 2, 3])
def test_all_seeded_styles_have_contract_credit_not_topic_note_filler(number):
    for seed in range(20):
        for q in paper(number, seed).questions:
            for part in q.parts or [q]:
                contract = part.assessment_contract
                assert sum(part.assessment_objectives.values()) == part.marks
                assert contract["credit"]
                assert contract["assessment_objectives"] == part.assessment_objectives
                text = " ".join(part.mark_scheme + part.indicative_content)
                for filler in [
                    "Correctly identifies or defines",
                    "Connects the analysis back to the syllabus framework",
                    "syllabus alignment",
                    "Tesco",
                ]:
                    assert filler not in text
                if part.marks in {10, 12, 15, 25}:
                    assert contract["scheme_mode"] == "levels"
                    assert (
                        contract["evaluation_marks"]
                        == part.assessment_objectives["AO4"]
                    )
                    assert "not additive" in text


@pytest.mark.parametrize("mutation", ["prompt", "visible_source", "unit", "marks"])
def test_numeric_contract_rejects_changed_candidate_request_or_source(mutation):
    q = paper(2, 26083122).questions[0]
    item = _question_solver_item(q, q.parts[1])
    if mutation == "prompt":
        item["prompt"] = "Calculate the mean saving rate."
    elif mutation == "visible_source":
        item["stimulus"]["values"][0] = 999
    elif mutation == "unit":
        item["authoring_context"]["economics_input_contract"]["source"]["unit"] = (
            "index"
        )
    else:
        item["marks"] = 4
    with pytest.raises(ValueError):
        IndependentSolver().solve(item, [])


def test_extended_instance_never_credits_another_instances_numbers():
    q = paper(3, 1).questions[0]
    assert "17%" in q.source_text
    text = " ".join(q.mark_scheme)
    assert "15% price" not in text and "6% output" not in text
    assert "17%" in text
    knowledge = [point for point in q.mark_scheme if point.startswith("AO1")]
    assert len(knowledge) == 2
    assert "responsiveness" in knowledge[0]
    assert "less than" in knowledge[1] and "proportional" in knowledge[1]
    assert not any(point.startswith("AO1 (1 mark): Identify ") for point in knowledge)


def test_eight_mark_credit_is_two_point_routes_with_separate_evaluation():
    q = paper(3, 1).questions[1]
    assert q.marks == 8
    assert q.assessment_contract["scheme_mode"] == "points"
    text = " ".join(q.mark_scheme)
    assert "KAA band" not in text
    assert "AO4" in text and "two distinct" in text and "developed" in text
    for objective in ("AO1", "AO2", "AO3"):
        assert sum(f"{objective} (1 mark)" in line for line in q.mark_scheme) == 2
    assert "diagram" not in text.casefold()


@pytest.mark.parametrize("marks", [10, 12, 15, 25])
def test_actual_level_tariffs_have_distinct_usable_band_descriptors(marks):
    q = next(
        q for p in [paper(1, 1), paper(3, 1)] for q in p.questions if q.marks == marks
    )
    for name in ("kaa", "evaluation"):
        bands = q.assessment_contract[name + "_bands"]
        descriptors = q.assessment_contract[name + "_descriptors"]
        assert len(descriptors) == len(bands)
        assert len(set(descriptors)) == len(descriptors)
        assert all(len(descriptor.split()) >= 12 for descriptor in descriptors)
        assert all(descriptor in " ".join(q.mark_scheme) for descriptor in descriptors)


def test_fallback_credit_addresses_requested_cause_not_a_different_topic_chain():
    q = paper(1, 1).questions[5]
    assert "own-brand" in q.prompt
    text = " ".join(q.mark_scheme).casefold()
    assert "own-brand" in text
    assert "real income" in text or "substitute" in text
    assert "investment spending" not in text


def test_paper_three_regional_sources_identify_markets_and_do_not_copy_answer_conclusions():
    blueprint = paper(3, 1)
    for q in blueprint.questions:
        assert "regional economy" in q.source_title
    food, labour = blueprint.questions[5:7]
    assert "Household food purchases" in food.source_text
    assert "own-brand" in food.prompt
    assert "hospitality" in labour.source_text
    assert "professional registration" not in labour.source_text
    assert "healthcare" not in " ".join(labour.mark_scheme)
    assert "treatment capacity" not in " ".join(labour.mark_scheme)
    assert "later twelve-month period" in blueprint.questions[2].source_text
    assert "The policy and market debate" not in blueprint.questions[3].source_text
    assert (
        "average real GDP growth need not improve every household's welfare"
        not in blueprint.questions[3].source_text
    )


@pytest.mark.parametrize("seed", [1, 26083031, 26083032, 26083033])
def test_every_paper_three_source_path_requires_inference(seed):
    for q in paper(3, seed).questions:
        for shortcut in (
            "Economists linked",
            "shift short-run aggregate supply",
            "could increase long-run aggregate supply",
            "The scale of the effect depended",
            "The final welfare effect depended",
        ):
            assert shortcut not in q.source_text
        assert q.source_text.count("eligible households do not claim") <= 1


def test_hdi_difference_uses_higher_minus_lower_even_when_rows_are_reversed():
    from Backend.Core.subjects.economics_contracts import (
        calculation,
        calculation_working,
    )

    source = forced_part(
        "development_data_table", "calculate", 2
    ).source_instance.model_copy(deep=True)
    source.rows[1][1], source.rows[2][1] = source.rows[2][1], source.rows[1][1]
    assert next(iter(calculation(source, 2)["answer"].values())) == "0.139"
    assert calculation_working(source, 2).startswith(str(source.rows[2][1].number))


def test_five_mark_monetary_application_uses_two_actual_source_details():
    q = next(
        q
        for seed in range(60)
        for q in paper(2, seed).questions
        if q.marks == 5 and q.topic_id == "2.6" and not q.parts
    )
    assert q.marks == 5 and q.topic_id == "2.6"
    applications = [p for p in q.mark_scheme if p.startswith("AO2")]
    assert "5.25%" in applications[0]
    assert "mortgage" in applications[1].lower() and "mortgage" in q.source_text.lower()
    assert "borrowing or debt-servicing costs" not in applications[1]


def test_five_mark_trade_barrier_credit_does_not_reward_unrequested_exchange_rates():
    q = paper(2, 0).questions[5]
    assert "trade barriers" in q.prompt
    knowledge = " ".join(p for p in q.mark_scheme if p.startswith("AO1"))
    assert "appreciation" not in knowledge.casefold()
    assert "tariff" in knowledge.casefold() and "trade barrier" in knowledge.casefold()


def test_unreviewed_blueprint_does_not_claim_reviewed_provenance():
    for q in paper(2, 1).questions:
        assert q.provenance == "deterministic-contract"
        assert all(p.provenance == "deterministic-contract" for p in q.parts)


def test_export_retains_instance_credit_and_passes_shared_marking_checks():
    from Backend.Core.assessment_package import _extract_items
    from Backend.Core.mark_scheme_quality import validate_mark_scheme_item

    for n in (1, 2, 3):
        blueprint = paper(n, 26083049)
        items = _extract_items(
            blueprint.model_dump(mode="json"), subject="economics", paper_number=str(n)
        )
        assert items
        for item in items:
            assert item["assessment_contract"]["version"] == "edexcel-instance-v1"
            assert (
                item["assessment_contract"]["published_scheme"] == item["mark_scheme"]
            )
            validate_mark_scheme_item(item)


@pytest.mark.parametrize("number", [1, 2, 3])
def test_generated_scheme_pagination_checks_content_not_official_page_count(
    tmp_path, number
):
    import json

    from pastpapergen.render_pdf import render_mark_scheme

    from Backend.Core.assessment_package import _extract_items
    from Backend.Core.layout_conformance import conform_generated_documents

    blueprint = paper(number, 26083122)
    raw = blueprint.model_dump(mode="json")
    scheme = tmp_path / "scheme.pdf"
    assessment = tmp_path / "assessment.json"
    assessment.write_text(
        json.dumps(
            {
                "subject": "economics",
                "paper": str(number),
                "blueprint": raw,
                "items": _extract_items(
                    raw, subject="economics", paper_number=str(number)
                ),
            }
        ),
        encoding="utf-8",
    )
    render_mark_scheme(
        blueprint,
        load_syllabus(Path(__file__).parents[1] / "data/syllabus_seed.json"),
        scheme,
    )
    result = conform_generated_documents(
        "economics",
        str(number),
        {"mark_scheme": scheme, "assessment_package": assessment},
    )
    policy = result["mark_scheme"]
    assert policy["policy"] == "generated-edexcel-mark-scheme-content-v1"
    assert policy["reference_page_count"] == {1: 29, 2: 36, 3: 31}[number]
    assert policy["checked_parts"] == sum(
        len(q.parts) or 1 for q in blueprint.questions
    )
    assert policy["complete_printed_credit"] is True


@pytest.mark.parametrize(
    "mutation", ["omit_part", "omit_credit", "truncate_credit", "blank_padding"]
)
def test_content_driven_scheme_policy_rejects_missing_printed_assessment(
    tmp_path, mutation
):
    import json

    from pastpapergen.render_pdf import render_mark_scheme

    from Backend.Core.assessment_package import _extract_items
    from Backend.Core.layout_conformance import conform_generated_documents
    from Backend.Core.layout_master import LayoutConformanceError

    blueprint = paper(2, 26083122)
    raw = blueprint.model_dump(mode="json")
    scheme, assessment = tmp_path / "scheme.pdf", tmp_path / "assessment.json"
    assessment.write_text(
        json.dumps(
            {
                "subject": "economics",
                "paper": "2",
                "blueprint": raw,
                "items": _extract_items(raw, subject="economics", paper_number="2"),
            }
        ),
        encoding="utf-8",
    )
    changed = blueprint.model_copy(deep=True)
    if mutation == "omit_part":
        changed.questions[0].parts.pop(1)
    elif mutation == "omit_credit":
        changed.questions[0].parts[1].mark_scheme.pop(2)
    elif mutation == "truncate_credit":
        changed.questions[0].parts[1].mark_scheme[2] = (
            changed.questions[0].parts[1].mark_scheme[2][:-3]
        )
    render_mark_scheme(
        changed,
        load_syllabus(Path(__file__).parents[1] / "data/syllabus_seed.json"),
        scheme,
    )
    if mutation == "blank_padding":
        with pymupdf.open(scheme) as document:
            document.new_page(pno=4)
            document.saveIncr()
    with pytest.raises(
        LayoutConformanceError, match=r"blank padding|omits or truncates"
    ):
        conform_generated_documents(
            "economics", "2", {"mark_scheme": scheme, "assessment_package": assessment}
        )


def test_content_driven_policy_is_reproducible_and_does_not_reclassify_other_documents():
    import json

    from Backend.Core.layout_conformance import REGISTRY_PATH, runtime_page_count_policy

    registry = json.loads(REGISTRY_PATH.read_text())
    for number in (1, 2, 3):
        record = registry["papers"][f"economics:{number}"]
        scheme = record["mark-scheme"]
        assert scheme["page_count_policy"] == runtime_page_count_policy(
            record["family"], "mark-scheme", scheme["page_count"]
        )
        assert record["question-paper"]["page_count_policy"]["kind"] == "exact"
    assert runtime_page_count_policy("aqa-accounting", "mark-scheme", 12) == {
        "kind": "exact",
        "minimum": 12,
        "maximum": 12,
    }


@pytest.mark.parametrize("number", [1, 2, 3])
def test_printed_scheme_is_the_contract_not_renderer_reconstructed_credit(number):
    blueprint = paper(number, 26083122)
    syllabus = load_syllabus(Path(__file__).parents[1] / "data/syllabus_seed.json")
    rows = _mark_scheme_rows(blueprint, syllabus)
    printed = " ".join(line for row in rows for line in row["answer_lines"])
    for q in blueprint.questions:
        for item in q.parts or [q]:
            for point in item.mark_scheme:
                assert point in printed


def test_paper_three_figure_prints_its_source_values_not_hash_noise():
    questions = [q for q in paper(3, 1).questions if q.section == "A"]
    data = BytesIO()
    canvas = Canvas(data)
    _draw_paper_3_source_page(canvas, questions, "A", 0, 787)
    canvas.save()
    with pymupdf.open(stream=data.getvalue(), filetype="pdf") as document:
        text = " ".join(document[0].get_text().split())
    assert "17%" in text
    assert "8%" in text
    assert "Quantity supplied" in text


@pytest.mark.parametrize(
    "field",
    ["source_instance", "assessment_objectives", "assessment_contract", "scheme_mode"],
)
def test_resume_guards_new_source_and_credit_fields(field):
    from pastpapergen.ollama_client import _validate_ai_question

    q = paper(2, 1).questions[5]
    change = None if field == "source_instance" else {}
    candidate = q.model_copy(
        update={
            field: change,
            "prompt": "Explain how economic growth increases living standards.",
        }
    )
    with pytest.raises(ValueError, match="verified assessment data"):
        _validate_ai_question(q, candidate)


def test_fixed_review_uses_printed_multipart_projection_and_truthful_provenance(
    monkeypatch,
):
    from pastpapergen import ollama_client

    full = paper(2, 26083122)
    q = full.questions[0].model_copy(
        update={"mark_scheme": ["Not printed parent summary"]}
    )
    seen = []
    monkeypatch.setattr(
        ollama_client,
        "require_independent_review",
        lambda *args, **kwargs: seen.append(kwargs),
    )
    result = ollama_client.generate_questions_with_ollama(
        object(),
        full.model_copy(update={"questions": [q]}),
        load_syllabus(Path(__file__).parents[1] / "data/syllabus_seed.json"),
    )
    assert seen[0]["candidate"].mark_scheme == []
    assert seen[0]["candidate"].parts == q.parts
    assert result.questions[0].provenance == "reviewed-deterministic-contract"


@pytest.mark.parametrize(
    "kind,expected",
    [
        ("market_share_bar_chart", "26.6%"),
        ("opportunity_cost_ppc_table", "25 consumer goods"),
        ("business_objective_context", "MR = 0"),
        ("investment_line_chart", "3.4 percentage points"),
    ],
)
def test_source_reading_keys_are_derived_from_actual_task(kind, expected):
    q = forced_part(kind, "mcq", 1)
    part = q.parts[0]
    answer = next(o.text for o in part.options if o.label == part.correct_option)
    assert expected in answer


@pytest.mark.parametrize(
    "kind,marks,expected",
    [
        ("pes_data_table", 4, "2.0%"),
        ("data_table", 2, "12.8 index points"),
        ("data_table", 4, "18.6%"),
        ("elasticity_data_table", 4, "7.0%"),
        ("concentration_ratio_table", 4, "58.8%"),
        ("opportunity_cost_ppc_table", 4, "25 consumer units"),
        ("shutdown_cost_table", 4, "−£2,000.00"),
        ("wage_rate_table", 4, "16.7%"),
        ("inflation_index_table", 2, "16.0 index points"),
        ("inflation_index_table", 4, "16.0%"),
        ("development_data_table", 2, "0.139"),
        ("income_tax_schedule_table", 2, "£80.00"),
        ("public_spending_pie_table", 2, "11.0 percentage points"),
        ("gdp_growth_bar_chart", 2, "−0.3 percentage points"),
        ("inequality_line_chart", 2, "0.09"),
        ("inequality_line_chart", 4, "21.4%"),
    ],
)
def test_complete_declared_numeric_operations_have_literal_answers(
    kind, marks, expected
):
    q = forced_part(kind, "calculate", marks)
    item = _question_solver_item(q, q.parts[0])
    solution = IndependentSolver().solve(item, [])
    require_solution_matches_scheme(solution, item)
    assert list(ast.literal_eval(solution.answer).values()) == [expected]


def test_declared_calculation_inventory_is_exhaustive_and_latent_gaps_fail_closed():
    from pastpapergen.generator import _STIMULUS_PART_PROMPTS

    from Backend.Core.subjects.economics_contracts import (
        SUPPORTED_CALCULATIONS,
        UNSUPPORTED_CALCULATIONS,
    )

    declared = {
        (style, marks)
        for style, entries in _STIMULUS_PART_PROMPTS.items()
        for (_, command, marks) in entries
        if command == "calculate"
    }
    assert len(declared) == 31  # 32 keys, with two equivalent inactivity keys
    assert declared == SUPPORTED_CALCULATIONS | UNSUPPORTED_CALCULATIONS.keys()
    for style, marks in UNSUPPORTED_CALCULATIONS:
        with pytest.raises(ValueError, match="unsupported Edexcel calculation"):
            forced_part(style, "calculate", marks)


@pytest.mark.parametrize(
    "kind,row,column,replacement",
    [
        ("data_table", 0, 1, "Household income index"),
        ("pes_data_table", 2, 0, "Coastal"),
        ("elasticity_data_table", 0, 1, "YED"),
        ("shutdown_cost_table", 0, 3, "Total cost"),
    ],
)
def test_numeric_roles_are_not_inferred_from_unlabelled_column_positions(
    kind, row, column, replacement
):
    from Backend.Core.subjects.economics_contracts import SourceCell, calculation

    q = forced_part(kind, "calculate", 4)
    source = q.source_instance.model_copy(deep=True)
    source.rows[row][column] = SourceCell(text=replacement)
    with pytest.raises(ValueError, match=r"source.*role"):
        calculation(source, 4)


@pytest.mark.parametrize(
    "suffix",
    [
        "%",
        "index points",
        "percentage points million",
        "percentage points e6",
        "percentage points to 999",
    ],
)
def test_percentage_point_answer_rejects_wrong_units_scale_or_extra_endpoint(suffix):
    q = forced_part("public_spending_pie_table", "calculate", 2)
    item = _question_solver_item(q, q.parts[0])
    solution = IndependentSolver().solve(item, [])
    item["mark_scheme"] = [
        line.replace("11.0 percentage points", "11.0 " + suffix)
        for line in item["mark_scheme"]
    ]
    with pytest.raises(ValueError):
        require_solution_matches_scheme(solution, item)
