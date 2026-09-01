from __future__ import annotations

from copy import deepcopy

import pytest

from Backend.Core.assessment_package import _extract_items
from Backend.Core.exam_blueprints import (
    GeneratedOption,
    GeneratedPaper,
    GeneratedQuestion,
    GeneratedSection,
    PaperRule,
    QuestionRule,
    SectionRule,
    resolve_question_rules,
    validate_generated_paper,
)
from Backend.Core.independent_solver import IndependentSolver
from Backend.Core.providers import _ollama_json_schema
from Backend.Core.reference_demand import (
    ReferenceDemandProfile,
    build_item_demand_target,
)
from Backend.Core.subjects.selected_response import solve_selected_response


def _complete_solver_response(**updates: object) -> dict[str, object]:
    response: dict[str, object] = {
        "steps": ["Use the candidate-visible information."],
        "answer": "A complete answer",
        "mark_points": ["A complete answer"],
        "evidence_ids": [],
        "alternatives": [],
        "partial_credit_boundaries": [],
        "follow_through_rules": [],
    }
    response.update(updates)
    return response


class _SolverClient:
    def __init__(self, response: dict[str, object]) -> None:
        self.response = response
        self.prompt = ""

    def generate_json(self, prompt: str) -> dict[str, object]:
        self.prompt = prompt
        return deepcopy(self.response)


def _profile() -> ReferenceDemandProfile:
    distribution = {"low": 1.0}
    return ReferenceDemandProfile(
        family_id="economics-aqa",
        paper_id="3",
        comparison_basis="task-source-demand-test",
        source_document_count=1,
        source_fingerprint="a" * 64,
        mark_band_distribution={"1": 1.0},
        command_word_distribution={"select": 1.0},
        demand_distribution=distribution,
        mark_weighted_demand_distribution=distribution,
        response_mode_distribution={"selected-response": 1.0},
        cognitive_operation_distribution={"transform": 1.0},
        extraction_coverage=1.0,
        metric_tolerances={
            "mark_band_distribution": 1.0,
            "command_family_distribution": 1.0,
            "mark_weighted_demand_distribution": 1.0,
            "response_mode_distribution": 1.0,
            "cognitive_operation_distribution": 1.0,
        },
    )


SELECTED_OPERATION_EXAMPLES = {
    "index_percentage_increase": {
        "inputs": {"base": "100", "rate_percent": "8"},
        "choices": ["108.0", "92.0", "113.0", "8.0"],
        "unit": "index", "decimal_places": 1,
    },
    "index_percentage_decrease": {
        "inputs": {"base": "100", "rate_percent": "8"},
        "choices": ["92.0", "108.0", "87.0", "8.0"],
        "unit": "index", "decimal_places": 1,
    },
    "index_percentage_change": {
        "inputs": {"initial": "100", "final": "120"},
        "choices": ["20.0%", "16.7%", "120.0%", "-20.0%"],
        "unit": "percent", "decimal_places": 1,
    },
    "economic_shift": {
        "inputs": {"curve": "D", "direction": "right", "scope": "market", "x_axis": "Quantity", "y_axis": "Price"},
        "choices": ["Equilibrium price rises and equilibrium quantity rises", "Equilibrium price rises and equilibrium quantity falls", "Equilibrium price falls and equilibrium quantity rises", "Equilibrium price falls and equilibrium quantity falls"],
        "unit": "effect", "decimal_places": 0,
    },
    "opportunity_cost_change": {
        "inputs": {"primary_before": "20", "secondary_before": "80", "primary_after": "30", "secondary_after": "68"},
        "choices": ["12 units of product Y", "20 units of product Y", "10 units of product Y", "68 units of product Y"],
        "unit": "quantity", "decimal_places": 0,
    },
    "elastic_revenue_change": {
        "inputs": {"price_before": "10", "quantity_before": "100", "price_after": "12", "quantity_after": "88"},
        "choices": ["Total expenditure rises", "Total expenditure falls", "Total expenditure is unchanged", "The effect cannot be calculated"],
        "unit": "effect", "decimal_places": 0,
    },
    "income_distribution_change": {
        "inputs": {"poorest_share_before": "20", "richest_share_before": "45", "poorest_share_after": "25", "richest_share_after": "38"},
        "choices": ["Income inequality falls", "Income inequality rises", "Income inequality is unchanged", "Nominal GDP must fall"],
        "unit": "effect", "decimal_places": 0,
    },
    "interest_rate_demand_change": {
        "inputs": {"interest_rate_before": "4", "interest_rate_after": "6", "credit_share_percent": "60"},
        "choices": ["Credit-financed consumption and investment weaken", "Credit-financed consumption and investment strengthen", "Credit-financed consumption and investment are unchanged", "All saving must cease"],
        "unit": "effect", "decimal_places": 0,
    },
    "trade_elasticity_effect": {
        "inputs": {"exchange_rate_direction": "depreciation", "export_elasticity": "0.9", "import_elasticity": "0.6"},
        "choices": ["The trade balance is more likely to improve", "The trade balance is more likely to worsen", "The trade balance is unlikely to change from the elasticity condition alone", "Domestic output must become zero"],
        "unit": "effect", "decimal_places": 0,
    },
    "gross_profit": {
        "inputs": {"revenue": "20", "cost_of_sales": "6"},
        "choices": ["£14m", "£20m", "£6m", "£10m"],
        "unit": "GBPm", "decimal_places": 0,
    },
    "after_tax_profit": {
        "inputs": {"revenue": "20", "cost_of_sales": "6", "operating_expenses": "4", "taxation": "7"},
        "choices": ["£3m", "£7m", "£10m", "£14m"],
        "unit": "GBPm", "decimal_places": 0,
    },
    "highest_productivity": {
        "inputs": {},
        "rows": [{"label": "Factory A", "output": "900", "employees": "60"}, {"label": "Factory B", "output": "840", "employees": "40"}],
        "choices": ["Factory B", "Factory A", "Factory C", "Factory D"],
        "unit": "classification", "decimal_places": 0,
    },
    "performance_statements": {
        "inputs": {},
        "rows": [{"label": "Capacity utilisation", "target": "90", "actual": "88", "better_when": "higher"}, {"label": "Labour turnover", "target": "12", "actual": "17", "better_when": "lower"}],
        "choices": ["Statement 1 is true, Statement 2 is false", "Statement 1 is false, Statement 2 is true", "Both statements are true", "Both statements are false"],
        "unit": "classification", "decimal_places": 0,
    },
    "break_even_change": {
        "inputs": {"fixed_cost_before": "60", "price_before": "5", "variable_cost_before": "3", "fixed_cost_after": "60", "price_after": "6", "variable_cost_after": "2"},
        "choices": ["A rise in selling price and a fall in variable cost per unit", "A fall in selling price and a rise in variable cost per unit", "A rise in fixed costs and a fall in output", "A fall in capacity and a rise in fixed costs"],
        "unit": "effect", "decimal_places": 0,
    },
    "strategic_drift": {
        "inputs": {"external_change": "high", "strategic_change": "low"},
        "choices": ["Strategic drift", "Strategic fit", "Market penetration", "Retrenchment"],
        "unit": "classification", "decimal_places": 0,
    },
}


def _selected_operation_item(operation: str) -> dict[str, object]:
    example = deepcopy(SELECTED_OPERATION_EXAMPLES[operation])
    choices = example.pop("choices")
    return {
        "id": operation,
        "marks": 1,
        "kind": "multiple_choice",
        "choices": choices,
        "authoring_context": {
            "selected_response_contract": {
                "version": "selected-response-v1",
                "operation": operation,
                **example,
            }
        },
    }


def test_per_option_rule_resolver_hydrates_task_source_and_objectives() -> None:
    default = QuestionRule(
        id="mcq",
        marks=1,
        kind="multiple_choice",
        command_word="Select",
        assessment_objectives={"AO1": 1},
        task_operation="retrieve",
        source_dependency="none",
    )
    applied = default.model_copy(
        update={
            "assessment_objectives": {"AO2": 1},
            "task_operation": "transform",
            "source_dependency": "stem",
        }
    )
    section = SectionRule(
        id="A",
        title="Selected response",
        option_count=2,
        answer_options=2,
        option_marks=1,
        questions=[default],
        question_overrides={2: [applied]},
    )
    rule = PaperRule(
        id="paper_3",
        code="TEST/3",
        title="Test",
        duration_minutes=2,
        total_marks=2,
        allowed_topic_ids={"topic"},
        sections=[section],
    )
    options = []
    for option_index in (1, 2):
        resolved = resolve_question_rules(section, option_index)[0]
        options.append(
            GeneratedOption(
                id=f"A{option_index}",
                title=f"Question {option_index}",
                questions=[
                    GeneratedQuestion(
                        rule_id="mcq",
                        number=str(option_index),
                        marks=1,
                        kind="multiple_choice",
                        command_word="Select",
                        topic_id="topic",
                        prompt=f"Select answer {option_index}.",
                        choices=["one", "two", "three", "four"],
                        correct_choice=0,
                        mark_scheme=["Option A: one."],
                        assessment_objectives=deepcopy(resolved.assessment_objectives),
                        task_operation=resolved.task_operation,
                        source_dependency=resolved.source_dependency,
                    )
                ],
            )
        )
    paper = GeneratedPaper(
        paper_id="paper_3",
        paper_code="TEST/3",
        title="Test",
        duration_minutes=2,
        total_marks=2,
        seed=1,
        sections=[GeneratedSection(id="A", title="Selected response", instructions="Answer all.", options=options)],
    )

    validate_generated_paper(paper, rule, {"topic"})
    assert paper.sections[0].options[0].questions[0].assessment_objectives == {"AO1": 1}
    assert paper.sections[0].options[1].questions[0].assessment_objectives == {"AO2": 1}
    assert paper.sections[0].options[1].questions[0].task_operation == "transform"
    assert paper.sections[0].options[1].questions[0].source_dependency == "stem"


def test_rule_override_cannot_change_slot_identity_or_tariff() -> None:
    base = QuestionRule(id="mcq", marks=1, kind="multiple_choice", command_word="Select")
    with pytest.raises(ValueError, match="identity and tariff"):
        SectionRule(
            id="A",
            title="Selected response",
            option_count=2,
            answer_options=2,
            option_marks=1,
            questions=[base],
            question_overrides={2: [base.model_copy(update={"marks": 2})]},
        )


def test_export_preserves_explicit_task_and_source_metadata() -> None:
    item = _extract_items(
        {
            "questions": [{
                "number": "1", "marks": 1, "kind": "multiple_choice",
                "prompt": "Use Figure 1 to select the change.",
                "task_operation": "analyse", "source_dependency": "figure",
            }]
        },
        subject="Economics", paper_number="3",
    )[0]
    assert item["task_operation"] == "analyse"
    assert item["source_dependency"] == "figure"


@pytest.mark.parametrize(
    ("item", "operation", "requires_context", "transformation"),
    [
        (
            {
                "id": "definition-under-shared-source",
                "marks": 1,
                "kind": "multiple_choice",
                "command_word": "Select",
                "prompt": "Select the definition of opportunity cost.",
                "context": ["A shared extract is printed above."],
                "assessment_objectives": {"AO1": 1},
                "task_operation": "retrieve",
                "source_dependency": "none",
            },
            "retrieve",
            False,
            False,
        ),
        (
            {
                "id": "index-transform",
                "marks": 1,
                "kind": "multiple_choice",
                "command_word": "Select",
                "prompt": "An index of 100 rises by 8%. Select the new value.",
                "assessment_objectives": {"AO2": 1},
                "task_operation": "transform",
                "source_dependency": "stem",
            },
            "transform",
            True,
            True,
        ),
        (
            {
                "id": "diagram-recognition",
                "marks": 1,
                "kind": "multiple_choice",
                "command_word": "Select",
                "prompt": "Use Figure 1 to select the shifted curve.",
                "assessment_objectives": {"AO1": 1},
                "task_operation": "analyse",
                "source_dependency": "figure",
                "source_references": ["Figure 1"],
            },
            "analyse",
            True,
            False,
        ),
    ],
)
def test_declared_task_work_not_tariff_or_source_presence_drives_target(
    item: dict[str, object],
    operation: str,
    requires_context: bool,
    transformation: bool,
) -> None:
    target = build_item_demand_target(item, _profile())

    assert target.response_mode == "selected-response"
    assert target.required_cognitive_operations[0] == operation
    assert target.requires_context is requires_context
    assert target.requires_data_transformation is transformation


def test_selected_response_index_is_derived_from_public_inputs_not_key() -> None:
    item = {
        "id": "index",
        "marks": 1,
        "kind": "multiple_choice",
        "choices": ["92.0", "108.0", "113.0", "8.0"],
        "correct_choice": 1,
        "authoring_context": {
            "selected_response_contract": {
                "version": "selected-response-v1",
                "operation": "index_percentage_increase",
                "inputs": {"base": "100", "rate_percent": "8"},
                "unit": "index",
                "decimal_places": 1,
            }
        },
    }

    result = solve_selected_response(item)
    assert result is not None
    assert result["answer"] == "108.0"
    assert result["mark_points"] == ["108.0"]
    mutated = deepcopy(item)
    mutated["correct_choice"] = 0
    assert solve_selected_response(mutated)["answer"] == "108.0"


@pytest.mark.parametrize("operation", sorted(SELECTED_OPERATION_EXAMPLES))
def test_every_selected_response_operation_enforces_its_unit_and_precision_policy(
    operation: str,
) -> None:
    item = _selected_operation_item(operation)
    assert solve_selected_response(item) is not None

    contract = item["authoring_context"]["selected_response_contract"]
    wrong_unit = deepcopy(item)
    wrong_unit_contract = wrong_unit["authoring_context"]["selected_response_contract"]
    wrong_unit_contract["unit"] = (
        "effect" if contract["unit"] != "effect" else "classification"
    )
    with pytest.raises(ValueError, match="format policy"):
        solve_selected_response(wrong_unit)

    wrong_precision = deepcopy(item)
    wrong_precision_contract = wrong_precision["authoring_context"][
        "selected_response_contract"
    ]
    wrong_precision_contract["decimal_places"] = (
        1 if contract["decimal_places"] == 0 else 0
    )
    with pytest.raises(ValueError, match="format policy"):
        solve_selected_response(wrong_precision)


@pytest.mark.parametrize(
    ("operation", "bad_choice"),
    [
        ("index_percentage_increase", "108"),
        ("index_percentage_decrease", "92"),
        ("index_percentage_change", "20%"),
        ("opportunity_cost_change", "12.0 units of product Y"),
        ("gross_profit", "£14.0m"),
        ("after_tax_profit", "£3.0m"),
    ],
)
def test_numeric_selected_responses_require_exact_displayed_precision(
    operation: str, bad_choice: str
) -> None:
    item = _selected_operation_item(operation)
    expected = solve_selected_response(item)["answer"]
    item["choices"][item["choices"].index(expected)] = bad_choice

    with pytest.raises(ValueError, match=r"precision|units|semantic option"):
        solve_selected_response(item)


@pytest.mark.parametrize(
    ("operation", "field", "value"),
    [
        ("index_percentage_increase", "rate_percent", "-8"),
        ("index_percentage_increase", "rate_percent", "0"),
        ("index_percentage_decrease", "rate_percent", "0"),
        ("index_percentage_decrease", "rate_percent", "100"),
        ("index_percentage_change", "final", "-50"),
    ],
)
def test_index_operations_reject_wrong_direction_or_invalid_endpoints(
    operation: str, field: str, value: str
) -> None:
    item = _selected_operation_item(operation)
    item["authoring_context"]["selected_response_contract"]["inputs"][field] = value
    with pytest.raises(ValueError, match="index selected response"):
        solve_selected_response(item)


@pytest.mark.parametrize(
    ("operation", "updates"),
    [
        ("gross_profit", {"revenue": "5", "cost_of_sales": "10"}),
        (
            "after_tax_profit",
            {
                "revenue": "5",
                "cost_of_sales": "4",
                "operating_expenses": "3",
                "taxation": "2",
            },
        ),
    ],
)
def test_profit_operations_reject_negative_numeric_outputs(
    operation: str, updates: dict[str, str]
) -> None:
    item = _selected_operation_item(operation)
    item["authoring_context"]["selected_response_contract"]["inputs"].update(updates)
    with pytest.raises(ValueError, match="profit source"):
        solve_selected_response(item)


def test_interest_rate_operation_rejects_negative_public_rates() -> None:
    item = _selected_operation_item("interest_rate_demand_change")
    item["authoring_context"]["selected_response_contract"]["inputs"][
        "interest_rate_before"
    ] = "-1"
    with pytest.raises(ValueError, match="invalid public credit share"):
        solve_selected_response(item)


@pytest.mark.parametrize(
    ("operation", "field"),
    [("highest_productivity", "output"), ("performance_statements", "actual")],
)
def test_row_operations_reject_negative_public_measurements(
    operation: str, field: str
) -> None:
    item = _selected_operation_item(operation)
    item["authoring_context"]["selected_response_contract"]["rows"][0][field] = "-1"
    with pytest.raises(ValueError, match="invalid public rows"):
        solve_selected_response(item)


def test_break_even_operation_rejects_negative_public_costs() -> None:
    item = _selected_operation_item("break_even_change")
    item["authoring_context"]["selected_response_contract"]["inputs"][
        "fixed_cost_before"
    ] = "-60"
    with pytest.raises(ValueError, match="invalid public values"):
        solve_selected_response(item)


def test_selected_response_rejects_semantically_duplicate_numeric_options() -> None:
    item = {
        "id": "index",
        "marks": 1,
        "kind": "multiple_choice",
        "choices": ["92.0", "108.0", "108", "113.0"],
        "correct_choice": 1,
        "authoring_context": {
            "selected_response_contract": {
                "version": "selected-response-v1",
                "operation": "index_percentage_increase",
                "inputs": {"base": "100", "rate_percent": "8"},
                "unit": "index",
                "decimal_places": 1,
            }
        },
    }

    with pytest.raises(ValueError, match="exactly one semantic option"):
        solve_selected_response(item)


def test_money_selected_response_rejects_a_malformed_distractor() -> None:
    item = {
        "id": "profit",
        "marks": 1,
        "kind": "multiple_choice",
        "choices": ["£3m", "£10m", "£14m", "£7m or £8m"],
        "correct_choice": 0,
        "authoring_context": {
            "selected_response_contract": {
                "version": "selected-response-v1",
                "operation": "after_tax_profit",
                "inputs": {
                    "revenue": "20",
                    "cost_of_sales": "6",
                    "operating_expenses": "4",
                    "taxation": "7",
                },
                "unit": "GBPm",
                "decimal_places": 0,
            }
        },
    }

    with pytest.raises(ValueError, match="exactly one semantic option"):
        solve_selected_response(item)


@pytest.mark.parametrize(
    "mutation",
    [
        ("missing", "evidence_ids", None),
        ("extra", "confidence", 0.9),
        ("wrong_type", "mark_points", {"point": "A complete answer"}),
        ("wrong_type", "alternatives", "none"),
    ],
)
def test_open_solver_requires_the_literal_raw_response_envelope(mutation) -> None:
    action, field, value = mutation
    response = _complete_solver_response()
    if action == "missing":
        del response[field]
    else:
        response[field] = value
    with pytest.raises(ValueError, match="invalid solver response envelope"):
        IndependentSolver(_SolverClient(response)).solve(
            {"id": "open", "marks": 2, "prompt": "Explain the effect."}, []
        )


@pytest.mark.parametrize(
    ("field", "member"),
    [
        (field, member)
        for field in (
            "alternatives",
            "partial_credit_boundaries",
            "follow_through_rules",
        )
        for member in ({"text": "structured"}, 7, None)
    ],
)
def test_open_solver_rejects_non_string_array_members_at_raw_boundary(
    field: str,
    member: object,
) -> None:
    response = _complete_solver_response()
    response[field] = [member]

    with pytest.raises(ValueError, match="invalid solver response envelope"):
        IndependentSolver(_SolverClient(response)).solve(
            {"id": "open", "marks": 2, "prompt": "Explain the effect."}, []
        )


def test_provider_solver_schema_requires_string_array_members() -> None:
    schema = _ollama_json_schema(
        "Independently solve this item without seeing its draft mark scheme.\n{}"
    )

    for field in (
        "alternatives",
        "partial_credit_boundaries",
        "follow_through_rules",
    ):
        assert schema["properties"][field]["items"]["type"] == "string"


@pytest.mark.parametrize(
    "mutation",
    [
        {"correct_effect": "PRIVATE"},
        {"unexpected": "residue"},
    ],
)
def test_economic_shift_rejects_unknown_or_private_public_inputs(
    mutation: dict[str, str],
) -> None:
    item = {
        "id": "shift",
        "marks": 1,
        "kind": "multiple_choice",
        "choices": [
            "Equilibrium price rises and equilibrium quantity rises",
            "Equilibrium price rises and equilibrium quantity falls",
            "Equilibrium price falls and equilibrium quantity rises",
            "Equilibrium price falls and equilibrium quantity falls",
        ],
        "authoring_context": {
            "selected_response_contract": {
                "version": "selected-response-v1",
                "operation": "economic_shift",
                "inputs": {
                    "curve": "D",
                    "direction": "right",
                    "scope": "market",
                    "x_axis": "Quantity",
                    "y_axis": "Price",
                    **mutation,
                },
                "unit": "effect",
                "decimal_places": 0,
            }
        },
    }

    with pytest.raises(ValueError, match="invalid public inputs"):
        solve_selected_response(item)


def test_selected_response_rejects_normalized_duplicate_choices() -> None:
    item = {
        "id": "classification",
        "marks": 1,
        "kind": "multiple_choice",
        "choices": [
            "Strategic drift",
            "Strategic fit",
            " strategic FIT ",
            "Retrenchment",
        ],
        "authoring_context": {
            "selected_response_contract": {
                "version": "selected-response-v1",
                "operation": "strategic_drift",
                "inputs": {"external_change": "high", "strategic_change": "low"},
                "unit": "classification",
                "decimal_places": 0,
            }
        },
    }

    with pytest.raises(ValueError, match="four distinct choices"):
        solve_selected_response(item)


@pytest.mark.parametrize("operation", ["highest_productivity", "performance_statements"])
def test_selected_response_rejects_duplicate_normalized_row_labels(
    operation: str,
) -> None:
    rows = (
        [
            {"label": "Factory A", "output": "900", "employees": "60"},
            {"label": " factory a ", "output": "840", "employees": "40"},
        ]
        if operation == "highest_productivity"
        else [
            {
                "label": "Labour turnover",
                "target": "12",
                "actual": "17",
                "better_when": "lower",
            },
            {
                "label": " labour turnover ",
                "target": "90",
                "actual": "88",
                "better_when": "higher",
            },
        ]
    )
    item = {
        "id": "rows",
        "marks": 1,
        "kind": "multiple_choice",
        "choices": ["Factory A", "Factory B", "Factory C", "Factory D"]
        if operation == "highest_productivity"
        else [
            "Both statements are true",
            "Both statements are false",
            "Statement 1 is true, Statement 2 is false",
            "Statement 1 is false, Statement 2 is true",
        ],
        "authoring_context": {
            "selected_response_contract": {
                "version": "selected-response-v1",
                "operation": operation,
                "inputs": {},
                "rows": rows,
                "unit": "classification",
                "decimal_places": 0,
            }
        },
    }

    with pytest.raises(ValueError, match="distinct row labels"):
        solve_selected_response(item)


@pytest.mark.parametrize(
    ("operation", "inputs", "choices"),
    [
        (
            "opportunity_cost_change",
            {
                "primary_before": "-20",
                "secondary_before": "80",
                "primary_after": "30",
                "secondary_after": "68",
            },
            ["12 units of product Y", "20 units of product Y", "10 units of product Y", "68 units of product Y"],
        ),
        (
            "elastic_revenue_change",
            {"price_before": "0", "quantity_before": "100", "price_after": "12", "quantity_after": "88"},
            ["Total expenditure rises", "Total expenditure falls", "Total expenditure is unchanged", "The effect cannot be calculated"],
        ),
        (
            "income_distribution_change",
            {"poorest_share_before": "120", "richest_share_before": "45", "poorest_share_after": "25", "richest_share_after": "38"},
            ["Income inequality falls", "Income inequality rises", "Income inequality is unchanged", "Nominal GDP must fall"],
        ),
        (
            "interest_rate_demand_change",
            {"interest_rate_before": "4", "interest_rate_after": "6", "credit_share_percent": "101"},
            ["Credit-financed consumption and investment weaken", "Credit-financed consumption and investment strengthen", "Credit-financed consumption and investment are unchanged", "All saving must cease"],
        ),
        (
            "trade_elasticity_effect",
            {"exchange_rate_direction": "depreciation", "export_elasticity": "-0.1", "import_elasticity": "0.6"},
            ["The trade balance is more likely to improve", "The trade balance is more likely to worsen", "The trade balance must be unchanged", "Domestic output must become zero"],
        ),
    ],
)
def test_new_economic_selected_responses_reject_invalid_public_domains(
    operation: str,
    inputs: dict[str, str],
    choices: list[str],
) -> None:
    units = {
        "opportunity_cost_change": ("quantity", 0),
        "elastic_revenue_change": ("effect", 0),
        "income_distribution_change": ("effect", 0),
        "interest_rate_demand_change": ("effect", 0),
        "trade_elasticity_effect": ("effect", 0),
    }
    unit, decimal_places = units[operation]
    item = {
        "id": operation,
        "marks": 1,
        "kind": "multiple_choice",
        "choices": choices,
        "authoring_context": {
            "selected_response_contract": {
                "version": "selected-response-v1",
                "operation": operation,
                "inputs": inputs,
                "unit": unit,
                "decimal_places": decimal_places,
            }
        },
    }

    with pytest.raises(ValueError, match="invalid public"):
        solve_selected_response(item)


@pytest.mark.parametrize(
    ("operation", "row", "choices"),
    [
        (
            "highest_productivity",
            {"label": "Factory A", "output": "900", "employees": "60", "target": "10"},
            ["Factory A", "Factory B", "Factory C", "Factory D"],
        ),
        (
            "performance_statements",
            {"label": "Labour turnover", "target": "12", "actual": "17", "better_when": "lower", "output": "900"},
            ["Both statements are true", "Both statements are false", "Statement 1 is true, Statement 2 is false", "Statement 1 is false, Statement 2 is true"],
        ),
    ],
)
def test_row_selected_responses_reject_fields_from_other_operations(
    operation: str,
    row: dict[str, str],
    choices: list[str],
) -> None:
    rows = [row]
    if operation == "highest_productivity":
        rows.append({"label": "Factory B", "output": "840", "employees": "40"})
    else:
        rows.append({"label": "Capacity utilisation", "target": "90", "actual": "88", "better_when": "higher"})
    item = {
        "id": operation,
        "marks": 1,
        "kind": "multiple_choice",
        "choices": choices,
        "authoring_context": {
            "selected_response_contract": {
                "version": "selected-response-v1",
                "operation": operation,
                "inputs": {},
                "rows": rows,
                "unit": "classification",
                "decimal_places": 0,
            }
        },
    }

    with pytest.raises(ValueError, match="invalid public rows"):
        solve_selected_response(item)


def test_economic_shift_rejects_axes_that_conflict_with_scope() -> None:
    item = {
        "id": "shift",
        "marks": 1,
        "kind": "multiple_choice",
        "choices": [
            "The price level rises and real output rises",
            "The price level rises and real output falls",
            "The price level falls and real output rises",
            "The price level falls and real output falls",
        ],
        "authoring_context": {
            "selected_response_contract": {
                "version": "selected-response-v1",
                "operation": "economic_shift",
                "inputs": {
                    "curve": "AD",
                    "direction": "right",
                    "scope": "aggregate",
                    "x_axis": "Quantity",
                    "y_axis": "Price",
                },
                "unit": "effect",
                "decimal_places": 0,
            }
        },
    }

    with pytest.raises(ValueError, match="invalid public axes"):
        solve_selected_response(item)


def test_solver_prompt_declares_all_raw_fields_and_blind_payload() -> None:
    client = _SolverClient(_complete_solver_response())
    IndependentSolver(client).solve(
        {
            "id": "open",
            "marks": 2,
            "prompt": "Explain the effect of the public input.",
            "correct_choice": 3,
            "mark_scheme": ["PRIVATE KEY"],
            "candidate_source": {
                "selected_response_contract": {
                    "version": "selected-response-v1",
                    "operation": "index_percentage_increase",
                    "inputs": {"base": "100", "rate_percent": "8"},
                    "unit": "index",
                    "decimal_places": 1,
                },
            },
            "authoring_context": {
                "verified_answers": {"answer": "PRIVATE ANSWER"},
            },
        },
        [],
    )
    for field in (
        "steps", "answer", "mark_points", "evidence_ids", "alternatives",
        "partial_credit_boundaries", "follow_through_rules",
    ):
        assert f'"{field}"' in client.prompt
    assert "selected_response_contract" in client.prompt
    assert '"base": "100"' in client.prompt
    assert "PRIVATE KEY" not in client.prompt
    assert "PRIVATE ANSWER" not in client.prompt
    assert '"correct_choice"' not in client.prompt
