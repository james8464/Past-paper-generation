import json
from collections import Counter
from pathlib import Path

import pytest
from aqaaccountgen.configs import load_rule
from aqaaccountgen.generator import build_paper
from aqaaccountgen.syllabus import load_syllabus

from Backend.Core.ai_assessment import _generation_prompt, _review_prompt, _tasks
from Backend.Core.assessment_package import (
    validate_assessment_package,
    write_assessment_package,
)
from Backend.Core.exam_blueprints import validate_generated_paper, validate_rule
from Backend.Core.model_review import (
    DifficultyReviewResult,
    validate_saved_difficulty_evidence,
)
from Backend.Core.reference_demand import build_item_demand_target, profile_for

ROOT = Path(__file__).resolve().parents[1]
SYLLABUS = load_syllabus(ROOT / "Resources/accounting/aqa/generator/data/syllabus.json")


def paper_for(number="1"):
    return build_paper(load_rule(number), SYLLABUS, 26083121)


@pytest.mark.parametrize(
    "number,section_b",
    [
        (
            "1",
            [
                {"AO2": 14},
                {"AO2": 2, "AO3": 4},
                {"AO2": 6},
                {"AO2": 8},
                {"AO2": 2, "AO3": 4},
            ],
        ),
        (
            "2",
            [
                {"AO2": 4},
                {"AO2": 8},
                {"AO2": 2},
                {"AO2": 2, "AO3": 4},
                {"AO2": 8},
                {"AO2": 1},
                {"AO2": 5},
                {"AO2": 2, "AO3": 4},
            ],
        ),
    ],
)
def test_accounting_uses_official_item_budgets_and_component_totals(number, section_b):
    # Regression: generic fallback classified familiar techniques as AO2 and invented AO4.
    paper = paper_for(number)
    questions = [q for s in paper.sections for o in s.options for q in o.questions]
    assert [
        q.assessment_objectives for q in paper.sections[1].options[0].questions
    ] == section_b
    totals = Counter()
    for question in questions:
        assert set(question.assessment_objectives) <= {"AO1", "AO2", "AO3"}
        assert sum(question.assessment_objectives.values()) == question.marks
        credited = Counter()
        for point in question.structured_mark_scheme:
            if point.marks:
                credited[point.assessment_objective] += point.marks
        assert dict(credited) == question.assessment_objectives
        totals.update(question.assessment_objectives)
    assert dict(totals) == {"AO1": 30, "AO2": 42, "AO3": 48}
    for question in paper.sections[0].options[0].questions:
        assert question.assessment_objectives == {"AO1": question.marks}
    for question in paper.sections[-1].options[0].questions:
        assert question.assessment_objectives == {"AO2": 5, "AO3": 20}
        awarded = [p for p in question.structured_mark_scheme if p.marks]
        assert len(awarded) == 2  # best-fit budgets, not circular per-content marks
        assert all(p.credit_type == "level" for p in awarded)


def test_accounting_does_not_offer_unallocated_objectives_in_guidance():
    for number in ("1", "2"):
        paper = paper_for(number)
        for section in paper.sections:
            for question in section.options[0].questions:
                for point in question.mark_scheme:
                    prefix = point.partition(":")[0]
                    if prefix.startswith("AO"):
                        assert prefix in question.assessment_objectives


@pytest.mark.parametrize("mutation", ["rule", "question", "guidance"])
def test_accounting_rejects_invalid_ao_even_if_marks_still_add_up(mutation):
    rule = load_rule("1")
    paper = build_paper(rule, SYLLABUS, 26083121)
    question = paper.sections[-1].options[0].questions[-1]
    if mutation == "rule":
        rule.sections[-1].questions[-1].assessment_objectives = {"AO2": 5, "AO4": 20}
    elif mutation == "question":
        question.assessment_objectives = {"AO2": 5, "AO4": 20}
    else:
        question.mark_scheme.append("AO4: reach a justified investment decision.")
    with pytest.raises(ValueError, match=r"AO4|objective|metadata"):
        validate_generated_paper(paper, rule, SYLLABUS.topic_ids)


def test_accounting_rule_cannot_fall_back_to_generic_allocation():
    rule = load_rule("1")
    rule.sections[-1].questions[-1].assessment_objectives = {}
    with pytest.raises(ValueError, match=r"explicit|objective"):
        validate_rule(rule, SYLLABUS.topic_ids)


def test_authoring_and_editor_prompts_use_accounting_objective_semantics():
    paper = paper_for()
    task = _tasks(paper, {t.id: t for t in SYLLABUS.topics})[-1]
    task.question.authoring_context["preserve_mark_scheme"] = False
    prompt = _generation_prompt(
        [task], subject="Accounting", seed=1, attempt=1, previous_failure=""
    )
    payload = json.loads(prompt.split("BLUEPRINT_DATA=", 1)[1])[0]
    requirements = {
        row["assessment_objective"]: row["content_requirement"]
        for row in payload["required_awarded_entries"]
    }
    assert "evaluat" in requirements["AO3"].lower()
    assert "AO4" not in prompt
    review = _review_prompt([task], [task.question], subject="Accounting")
    assert "AO3" in review and "evaluation" in review.lower()
    assert "familiar" in prompt.lower()  # calculations may be AO1 techniques


def test_accounting_ao3_short_analysis_does_not_imply_judgement():
    profile = profile_for("aqa/accounting", "2")
    target = build_item_demand_target(
        {
            "marks": 6,
            "kind": "analysis",
            "command_word": "Explain",
            "assessment_objectives": {"AO2": 2, "AO3": 4},
        },
        profile,
    )
    assert target.requires_analysis_chain
    assert not target.requires_judgement
    assert "judge" not in target.required_cognitive_operations
    decision = build_item_demand_target(
        paper_for("2").sections[-1].options[0].questions[0], profile
    )
    assert decision.requires_analysis_chain and decision.requires_judgement


def test_pre_policy_saved_difficulty_review_is_not_current_after_relabel():
    question = paper_for().sections[-1].options[0].questions[-1]
    target = build_item_demand_target(question, profile_for("aqa/accounting", "1"))
    old = DifficultyReviewResult(
        approved=True,
        estimated_demand=target.demand_band,
        reasoning_steps=target.minimum_reasoning_steps,
        tariff_fit=True,
        command_word_fit=True,
        context_fit=True,
        profile_fit=True,
        observed_cognitive_operations=target.required_cognitive_operations,
        estimated_minutes=question.expected_minutes,
        target_profile_fingerprint=target.reference_profile_fingerprint,
        solution_integrity_version="closed-numeric-v2",
    ).model_dump(mode="json")
    old.pop("target_objective_policy_fingerprint", None)
    with pytest.raises(ValueError, match=r"objective|incomplete"):
        validate_saved_difficulty_evidence(old, target, item_id="17")


@pytest.mark.parametrize("field", ["assessment_objectives", "mark_scheme", "blueprint"])
def test_saved_accounting_package_rejects_unsupported_objective(tmp_path, field):
    path = tmp_path / "assessment.json"
    write_assessment_package(
        paper_for(),
        path,
        subject="accounting_aqa",
        paper_number="1",
        preview=True,
        provider=None,
        model=None,
    )
    document = json.loads(path.read_text())
    if field == "assessment_objectives":
        document["items"][-1][field] = {"AO2": 5, "AO4": 20}
    elif field == "mark_scheme":
        document["items"][-1][field].append("AO4: a supported decision.")
    else:
        document[field]["sections"][-1]["options"][0]["questions"][-1][
            "assessment_objectives"
        ] = {"AO2": 5, "AO4": 20}
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match=r"AO4|objective"):
        validate_assessment_package(
            path,
            subject="accounting_aqa",
            paper_number="1",
            preview=True,
            provider=None,
            model=None,
        )


@pytest.mark.parametrize("family", ["aqa/business", "aqa/economics"])
def test_other_subjects_retain_separate_evaluation_objective(family):
    target = build_item_demand_target(
        {
            "marks": 25,
            "kind": "extended_response",
            "command_word": "Discuss",
            "assessment_objectives": {"AO1": 5, "AO2": 5, "AO3": 7, "AO4": 8},
        },
        profile_for(family, "1"),
    )
    assert target.requires_analysis_chain and target.requires_judgement


@pytest.mark.parametrize("number", ["1", "2"])
def test_printed_accounting_scheme_has_three_objectives_and_actual_item_budgets(
    tmp_path, number
):
    import pymupdf
    from aqaaccountgen.render_pdf import render_mark_scheme

    path = tmp_path / "scheme.pdf"
    render_mark_scheme(paper_for(number), path)
    with pymupdf.open(path) as document:
        text = "\n".join(page.get_text() for page in document)
    assert "AO4" not in text
    assert "all four objectives" not in text
    assert "Analysis and evaluation" in text
    assert "AO2: 5" in text and "AO3: 20" in text
    if number == "2":
        # Budget rows must not suppress the substantive best-fit scheme.
        assert "Cheaper material could be lower quality" in text
        assert "Level 5" in text


def test_renderer_rejects_unsupported_indicative_label():
    from aqaaccountgen.render_pdf import _indicative_objective

    with pytest.raises(ValueError, match="AO4"):
        _indicative_objective("AO4: reach a decision")
    assert _indicative_objective("Consider an alternative route.") == "—"


@pytest.mark.parametrize("seed", [26083121, 26083122, 26083123])
def test_variance_followups_use_the_material_price_source_not_the_labour_source(seed):
    paper = build_paper(load_rule("2"), SYLLABUS, seed)
    questions = {q.rule_id: q for q in paper.sections[1].options[0].questions}
    price = questions["variance_1"].authoring_context["source_data"]
    assert price["standard_price_per_kg"] - price["actual_price_per_kg"] == 2
    assert price["actual_quantity_kg"] > 0
    for key in ("variance_3", "variance_4"):
        q = questions[key]
        assert q.authoring_context.get("source_data") == price
        assert q.authoring_context.get("source_question") == "14.1"
        assert "direct-material price variance" in q.prompt
        assert "below" in " ".join(q.mark_scheme)
        assert "adverse" not in " ".join(q.mark_scheme)


def test_current_difficulty_evidence_is_bound_to_the_accounting_budget():
    from Backend.Core.model_review import require_difficulty_review

    question = paper_for().sections[-1].options[0].questions[-1]
    profile = profile_for("aqa/accounting", "1")
    target = build_item_demand_target(question, profile)

    class Client:
        prompt = ""

        def generate_json(self, prompt):
            self.prompt = prompt
            return DifficultyReviewResult(
                approved=True,
                estimated_demand=target.demand_band,
                reasoning_steps=4,
                tariff_fit=True,
                command_word_fit=True,
                context_fit=True,
                profile_fit=True,
                observed_cognitive_operations=target.required_cognitive_operations,
                estimated_minutes=question.expected_minutes,
            ).model_dump(
                mode="json",
                exclude={
                    "public_task_operation_evidence",
                    "candidate_content_identity",
                },
            )

    client = Client()
    result = require_difficulty_review(
        client,
        item_id="17",
        subject="Accounting",
        target=target,
        candidate=question,
        specification={},
    )
    evidence = result.model_dump(mode="json")
    validate_saved_difficulty_evidence(
        evidence, target, item_id="17", candidate=question
    )
    assert "AO3" in client.prompt and "evaluation" in client.prompt
    changed = question.model_copy(
        update={"assessment_objectives": {"AO2": 6, "AO3": 19}}
    )
    with pytest.raises(ValueError, match="objective policy"):
        validate_saved_difficulty_evidence(
            evidence,
            build_item_demand_target(changed, profile),
            item_id="17",
            candidate=question,
        )


@pytest.mark.parametrize(
    "number,followup,source_ids",
    [
        ("1", "company_adjustment", ["company_statement"]),
        ("1", "partnership_3", ["partnership_1", "partnership_2"]),
        ("2", "costing_4", ["costing_1"]),
    ],
)
def test_applied_review_receives_the_visible_prior_question_data(
    number, followup, source_ids
):
    from Backend.Core.ai_assessment import _task_source

    tasks = _tasks(paper_for(number), {t.id: t for t in SYLLABUS.topics})
    by_id = {task.question.rule_id: task for task in tasks}
    context = _task_source(by_id[followup])["question_context"]
    assert set(context.get("referenced_question_data", {})) == set(source_ids)
    for source_id in source_ids:
        reference = context["referenced_question_data"][source_id]
        assert (
            reference["source_data"]
            == by_id[source_id].question.authoring_context["source_data"]
        )
        assert "verified_answers" not in reference
        assert "observable_mark_points" not in reference


@pytest.mark.parametrize("number", ["1", "2"])
def test_exported_quality_totals_follow_accounting_credit(tmp_path, number):
    path = tmp_path / "package.json"
    write_assessment_package(
        paper_for(number),
        path,
        subject="accounting_aqa",
        paper_number=number,
        preview=True,
        provider=None,
        model=None,
    )
    report = validate_assessment_package(
        path,
        subject="accounting_aqa",
        paper_number=number,
        preview=True,
        provider=None,
        model=None,
    )
    assert report["cross_paper_quality"]["assessment_objectives"] == {
        "AO1": 30,
        "AO2": 42,
        "AO3": 48,
    }


def test_activity_cost_working_uses_exact_rates_not_rounded_display_values():
    from aqaaccountgen.generator import _management_calculation

    # Hand-derived: 660000/890*28 = 20764.04; 460000/2040*44 = 9921.57
    # to two decimals. Using 741.57 and 225.49 instead gives different totals.
    _, scheme, context = _management_calculation(
        "costing_1", "Cedar Components", [89.0, 102.0, 115.0, 112.0, 110.0]
    )
    assigned = [point for point in scheme if "overhead assigned:" in point]
    assert assigned == [
        "Set-up overhead assigned: (£660,000 ÷ 890) × 28 = £20,764.04;",
        "Purchase-order overhead assigned: (£460,000 ÷ 2,040) × 44 = £9,921.57;",
    ]
    assert round(context["verified_answers"]["setup_overhead"], 2) == 20764.04
    assert round(context["verified_answers"]["purchase_order_overhead"], 2) == 9921.57


@pytest.mark.parametrize(
    "rule_id,expected_cells",
    [
        (
            "variance_4",
            {
                "AO2 allocation": "2",
                "AO3 allocation": "4",
                "AO3: Cheaper material could be lower quality": "—",
                "Level 3 (5–6)": "—",
                "Level 0 (0): no creditworthy material.": "0",
            },
        ),
        (
            "decision_2",
            {
                "AO2 allocation": "5",
                "AO3 allocation": "20",
                "Level 5 (21–25)": "—",
                "Level 0 (0): no creditworthy material.": "0",
            },
        ),
    ],
)
def test_rendered_award_cells_distinguish_guidance_from_zero_level(
    tmp_path, rule_id, expected_cells
):
    import pymupdf
    from aqaaccountgen.render_pdf import _scheme_block
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate

    question = next(
        q
        for section in paper_for("2").sections
        for q in section.options[0].questions
        if q.rule_id == rule_id
    )
    before = question.model_dump(mode="json")
    path = tmp_path / "award-cells.pdf"
    SimpleDocTemplate(str(path), pagesize=A4).build(_scheme_block(question))
    cells = {}
    with pymupdf.open(path) as document:
        for page in document:
            for text in expected_cells:
                for rect in page.search_for(text):
                    # Read the actual PDF's right-hand award cell on this row,
                    # not a table object's private cells or all occurrences of 0.
                    words = page.get_text("words")
                    cell = [
                        word[4]
                        for word in words
                        if word[0] > page.rect.width * 0.83
                        and rect.y0 <= (word[1] + word[3]) / 2 <= rect.y1
                    ]
                    cells[text] = " ".join(cell)
    assert cells == expected_cells
    assert question.model_dump(mode="json") == before
    assert sum(p.marks for p in question.structured_mark_scheme) == question.marks
    assert any(
        p.marks == 0 and p.text.startswith("Level 3")
        for p in question.structured_mark_scheme
    )
