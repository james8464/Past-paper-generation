"""Characterise public selected-response behavior before a dispatch-only refactor."""

from copy import deepcopy
from typing import get_args

import pytest

from Backend.Core.subjects import selected_response as solver


def test_dispatch_registry_names_every_declared_operation_once():
    assert set(solver._OPERATION_HANDLERS) == set(get_args(solver.SelectedOperation))
    assert set(solver._OPERATION_HANDLERS) == set(solver._OPERATION_FORMAT_POLICY)
    assert (
        len({handler.__name__ for handler in solver._OPERATION_HANDLERS.values()}) == 15
    )


STEPS = {
    "index_percentage_increase": "Multiply the candidate-visible base index by one plus the percentage rate.",
    "index_percentage_decrease": "Multiply the candidate-visible base index by one minus the percentage rate.",
    "index_percentage_change": "Divide the change in the candidate-visible index by its initial value.",
    "economic_shift": "Infer the new equilibrium from the candidate-visible curve shift.",
    "opportunity_cost_change": "Read the candidate-visible fall in product Y as the opportunity cost.",
    "elastic_revenue_change": "Compare price multiplied by quantity before and after the change.",
    "income_distribution_change": "Compare the candidate-visible gap between the richest and poorest shares.",
    "interest_rate_demand_change": "Relate the candidate-visible interest-rate movement to borrowing costs.",
    "trade_elasticity_effect": "Add the candidate-visible export and import elasticities and compare with one.",
    "gross_profit": "Subtract the candidate-visible costs from revenue in the requested order.",
    "after_tax_profit": "Subtract the candidate-visible costs from revenue in the requested order.",
    "highest_productivity": "Divide each candidate-visible output by its employee count and compare.",
    "performance_statements": "Compare each actual value with its target using the declared desirable direction.",
    "break_even_change": "Compute fixed cost divided by contribution before and after the changes.",
    "strategic_drift": "Identify the concept where strategy changes more slowly than the environment.",
}

CASES = [
    (
        "index_percentage_increase",
        {"base": "100", "rate_percent": "0.05"},
        [],
        ["100.0", "100.1", "101.0", "99.9"],
        "100.1",
        {"selected_value": 100.1},
    ),
    (
        "index_percentage_decrease",
        {"base": "100", "rate_percent": "0.05"},
        [],
        ["99.9", "100.0", "100.1", "101.0"],
        "100.0",
        {"selected_value": 100.0},
    ),
    (
        "index_percentage_change",
        {"initial": "80", "final": "81"},
        [],
        ["1.2%", "1.3%", "1.4%", "1.5%"],
        "1.3%",
        {"selected_value": 1.3},
    ),
    (
        "economic_shift",
        {
            "curve": "D",
            "direction": "right",
            "scope": "market",
            "x_axis": "Quantity",
            "y_axis": "Price",
        },
        [],
        [
            "Equilibrium price rises and equilibrium quantity rises",
            "wrong 1",
            "wrong 2",
            "wrong 3",
        ],
        "Equilibrium price rises and equilibrium quantity rises",
        {},
    ),
    (
        "opportunity_cost_change",
        {
            "primary_before": "0",
            "secondary_before": "80",
            "primary_after": "10",
            "secondary_after": "60",
        },
        [],
        [
            "10 units of product Y",
            "20 units of product Y",
            "30 units of product Y",
            "40 units of product Y",
        ],
        "20 units of product Y",
        {"opportunity_cost": 20.0},
    ),
    (
        "elastic_revenue_change",
        {
            "price_before": "10",
            "quantity_before": "10",
            "price_after": "20",
            "quantity_after": "10",
        },
        [],
        [
            "Total expenditure rises",
            "Total expenditure falls",
            "Total expenditure is unchanged",
            "wrong",
        ],
        "Total expenditure rises",
        {"expenditure_before": 100.0, "expenditure_after": 200.0},
    ),
    (
        "income_distribution_change",
        {
            "poorest_share_before": "10",
            "richest_share_before": "50",
            "poorest_share_after": "20",
            "richest_share_after": "50",
        },
        [],
        [
            "Income inequality falls",
            "Income inequality rises",
            "Income inequality is unchanged",
            "wrong",
        ],
        "Income inequality falls",
        {},
    ),
    (
        "interest_rate_demand_change",
        {
            "interest_rate_before": "2",
            "interest_rate_after": "3",
            "credit_share_percent": "50",
        },
        [],
        [
            "Credit-financed consumption and investment weaken",
            "Credit-financed consumption and investment strengthen",
            "Credit-financed consumption and investment are unchanged",
            "wrong",
        ],
        "Credit-financed consumption and investment weaken",
        {},
    ),
    (
        "trade_elasticity_effect",
        {
            "exchange_rate_direction": "depreciation",
            "export_elasticity": "0.8",
            "import_elasticity": "0.5",
        },
        [],
        [
            "The trade balance is more likely to improve",
            "The trade balance is more likely to worsen",
            "The trade balance is unlikely to change from the elasticity condition alone",
            "wrong",
        ],
        "The trade balance is more likely to improve",
        {},
    ),
    (
        "gross_profit",
        {"revenue": "10.5", "cost_of_sales": "0"},
        [],
        ["£10m", "£11m", "£12m", "£13m"],
        "£11m",
        {"selected_value": 10.5},
    ),
    (
        "after_tax_profit",
        {
            "revenue": "100",
            "cost_of_sales": "40",
            "operating_expenses": "10",
            "taxation": "5",
        },
        [],
        ["£40m", "£45m", "£50m", "£55m"],
        "£45m",
        {"selected_value": 45.0},
    ),
    (
        "highest_productivity",
        {},
        [
            {"label": "A", "output": "100", "employees": "10"},
            {"label": "B", "output": "150", "employees": "10"},
        ],
        ["A", "B", "C", "D"],
        "B",
        {"A": 10.0, "B": 15.0},
    ),
    (
        "performance_statements",
        {},
        [
            {
                "label": "Labour turnover",
                "target": "10",
                "actual": "20",
                "better_when": "lower",
            },
            {
                "label": "Capacity utilisation",
                "target": "80",
                "actual": "90",
                "better_when": "higher",
            },
        ],
        [
            "Both statements are true",
            "Statement 1 is true, Statement 2 is false",
            "Statement 1 is false, Statement 2 is true",
            "Both statements are false",
        ],
        "Both statements are true",
        {},
    ),
    (
        "break_even_change",
        {
            "fixed_cost_before": "100",
            "price_before": "10",
            "variable_cost_before": "5",
            "fixed_cost_after": "100",
            "price_after": "12",
            "variable_cost_after": "3",
        },
        [],
        [
            "A rise in selling price and a fall in variable cost per unit",
            "wrong 1",
            "wrong 2",
            "wrong 3",
        ],
        "A rise in selling price and a fall in variable cost per unit",
        {"before_output": 20.0, "after_output": 100 / 9},
    ),
    (
        "strategic_drift",
        {"external_change": "high", "strategic_change": "low"},
        [],
        ["Strategic drift", "Strategic fit", "wrong 1", "wrong 2"],
        "Strategic drift",
        {},
    ),
]


def task(case):
    operation, inputs, rows, choices, _, _ = case
    return {
        "kind": "multiple_choice",
        "marks": 1,
        "prompt": "Compare product X and product Y using the public information.",
        "choices": deepcopy(choices),
        "authoring_context": {
            "selected_response_contract": solver.selected_response_contract(
                operation, inputs=inputs, rows=rows
            )
        },
    }


def expected(case):
    operation, _, _, _, answer, numeric = case
    return {
        "steps": [STEPS[operation]],
        "answer": answer,
        "mark_points": [answer],
        "evidence_ids": [],
        "alternatives": [],
        "partial_credit_boundaries": [],
        "follow_through_rules": [],
        "numeric_results": numeric,
    }


@pytest.mark.parametrize("case", CASES, ids=lambda case: case[0])
def test_all_operations_preserve_the_complete_public_solution(case):
    item = task(case)
    before = deepcopy(item)
    assert solver.solve_selected_response(item) == expected(case)
    assert item == before


@pytest.mark.parametrize("case", CASES, ids=lambda case: case[0])
def test_every_operation_rejects_changed_shape_and_output_format(case):
    item = task(case)
    contract = item["authoring_context"]["selected_response_contract"]
    contract["inputs"]["unexpected"] = "1"
    with pytest.raises(ValueError, match="invalid public inputs"):
        solver.solve_selected_response(item)
    item = task(case)
    item["authoring_context"]["selected_response_contract"]["decimal_places"] = 4
    with pytest.raises(ValueError, match="violates selected response format policy"):
        solver.solve_selected_response(item)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case[0])
def test_every_operation_requires_one_correct_distinct_option(case):
    item = task(case)
    item["choices"] = ["A", " A ", "C", "D"]
    with pytest.raises(ValueError, match="four distinct choices"):
        solver.solve_selected_response(item)
    item = task(case)
    item["choices"] = ["wrong A", "wrong B", "wrong C", "wrong D"]
    with pytest.raises(ValueError):
        solver.solve_selected_response(item)


@pytest.mark.parametrize(
    "index,inputs,error",
    [
        (0, {"base": "0"}, "finite and positive"),
        (1, {"rate_percent": "100"}, "finite and positive"),
        (2, {"initial": "0"}, "finite and positive"),
        (3, {"x_axis": "Wrong"}, "invalid public axes"),
        (3, {"curve": "Wrong"}, "invalid public inputs"),
        (4, {"primary_after": "0"}, "invalid public values"),
        (5, {"quantity_before": "0"}, "invalid public values"),
        (6, {"poorest_share_after": "101"}, "invalid public shares"),
        (7, {"credit_share_percent": "0"}, "invalid public credit share"),
        (8, {"exchange_rate_direction": "appreciation"}, "requires a depreciation"),
        (8, {"export_elasticity": "-1"}, "invalid public elasticities"),
        (9, {"cost_of_sales": "11"}, "invalid public numeric domain"),
        (10, {"taxation": "-1"}, "invalid public numeric domain"),
        (13, {"variable_cost_after": "12"}, "positive contribution"),
        (13, {"fixed_cost_after": "200"}, "contradict the declared movement"),
        (
            14,
            {"external_change": "low", "strategic_change": "high"},
            "unsupported strategic-change classification",
        ),
    ],
)
def test_domain_guards_keep_their_existing_errors(index, inputs, error):
    item = task(CASES[index])
    item["authoring_context"]["selected_response_contract"]["inputs"].update(inputs)
    with pytest.raises(ValueError, match=error):
        solver.solve_selected_response(item)


@pytest.mark.parametrize("index", [0, 2, 4, 9])
def test_numeric_choice_units_and_precision_are_not_relaxed(index):
    item = task(CASES[index])
    item["choices"][0] = "100.00"
    with pytest.raises(ValueError):
        solver.solve_selected_response(item)


def test_public_row_ambiguity_and_missing_fields_are_rejected():
    for index in [11, 12]:
        item = task(CASES[index])
        rows = item["authoring_context"]["selected_response_contract"]["rows"]
        rows[1]["label"] = rows[0]["label"].upper()
        with pytest.raises(ValueError, match="distinct row labels"):
            solver.solve_selected_response(item)
    item = task(CASES[11])
    rows = item["authoring_context"]["selected_response_contract"]["rows"]
    rows[1]["output"] = "100"
    with pytest.raises(ValueError, match="one highest row"):
        solver.solve_selected_response(item)
    rows[1]["output"] = None
    with pytest.raises(ValueError, match="invalid public rows"):
        solver.solve_selected_response(item)
    item = task(CASES[12])
    item["authoring_context"]["selected_response_contract"]["rows"][0]["label"] = (
        "Other"
    )
    with pytest.raises(ValueError, match="missing required rows"):
        solver.solve_selected_response(item)


def test_unmarked_tasks_and_accounting_version_keep_the_narrow_boundary(monkeypatch):
    assert solver.solve_selected_response({"kind": "essay", "marks": 25}) is None
    result = {"accounting": "owned result"}
    calls = []
    monkeypatch.setattr(
        solver,
        "solve_accounting_selected_response",
        lambda item: calls.append(item) or result,
    )
    item = {
        "authoring_context": {
            "selected_response_contract": {
                "version": solver.ACCOUNTING_SELECTED_RESPONSE_VERSION
            }
        }
    }
    assert solver.solve_selected_response(item) is result
    assert calls == [item]


@pytest.mark.parametrize("kind,marks", [("essay", 1), ("multiple_choice", 2)])
def test_marked_tasks_require_one_mark_choices(kind, marks):
    item = task(CASES[0])
    item.update(kind=kind, marks=marks)
    with pytest.raises(ValueError, match="one-mark choice item"):
        solver.solve_selected_response(item)


@pytest.mark.parametrize(
    "curve,direction,scope,answer",
    [
        (
            "D",
            "right",
            "market",
            "Equilibrium price rises and equilibrium quantity rises",
        ),
        (
            "D",
            "left",
            "market",
            "Equilibrium price falls and equilibrium quantity falls",
        ),
        (
            "S",
            "right",
            "market",
            "Equilibrium price falls and equilibrium quantity rises",
        ),
        (
            "S",
            "left",
            "market",
            "Equilibrium price rises and equilibrium quantity falls",
        ),
        ("AD", "right", "aggregate", "The price level rises and real output rises"),
        ("AD", "left", "aggregate", "The price level falls and real output falls"),
        ("SRAS", "right", "aggregate", "The price level falls and real output rises"),
        ("SRAS", "left", "aggregate", "The price level rises and real output falls"),
        ("LRAS", "right", "aggregate", "The price level falls and real output rises"),
        ("LRAS", "left", "aggregate", "The price level rises and real output falls"),
    ],
)
def test_all_economic_shift_directions(curve, direction, scope, answer):
    item = task(CASES[3])
    item["authoring_context"]["selected_response_contract"]["inputs"] = {
        "curve": curve,
        "direction": direction,
        "scope": scope,
        "x_axis": "Quantity" if scope == "market" else "Real output",
        "y_axis": "Price" if scope == "market" else "Price level",
    }
    item["choices"] = ["wrong 1", answer, "wrong 2", "wrong 3"]
    assert solver.solve_selected_response(item) == {
        **expected(CASES[3]),
        "answer": answer,
        "mark_points": [answer],
    }


@pytest.mark.parametrize(
    "index,updates,answer",
    [
        (5, {"price_after": "5"}, "Total expenditure falls"),
        (5, {"price_after": "10"}, "Total expenditure is unchanged"),
        (6, {"richest_share_after": "80"}, "Income inequality rises"),
        (6, {"poorest_share_after": "10"}, "Income inequality is unchanged"),
        (
            7,
            {"interest_rate_after": "1"},
            "Credit-financed consumption and investment strengthen",
        ),
        (
            7,
            {"interest_rate_after": "2"},
            "Credit-financed consumption and investment are unchanged",
        ),
        (
            8,
            {"export_elasticity": "0.2", "import_elasticity": "0.3"},
            "The trade balance is more likely to worsen",
        ),
        (
            8,
            {"export_elasticity": "0.5", "import_elasticity": "0.5"},
            "The trade balance is unlikely to change from the elasticity condition alone",
        ),
        (14, {"strategic_change": "high"}, "Strategic fit"),
        (14, {"external_change": "low"}, "Strategic fit"),
    ],
)
def test_remaining_categorical_outcomes(index, updates, answer):
    item = task(CASES[index])
    item["authoring_context"]["selected_response_contract"]["inputs"].update(updates)
    result = solver.solve_selected_response(item)
    assert result["answer"] == answer
    assert result["mark_points"] == [answer]
    assert result["steps"] == [STEPS[CASES[index][0]]]
    if index == 5:
        assert result["numeric_results"] == {
            "expenditure_before": 100.0,
            "expenditure_after": float(updates["price_after"]) * 10,
        }


@pytest.mark.parametrize(
    "turnover,capacity,answer",
    [
        ("20", "90", "Both statements are true"),
        ("20", "70", "Statement 1 is true, Statement 2 is false"),
        ("5", "90", "Statement 1 is false, Statement 2 is true"),
        ("5", "70", "Both statements are false"),
    ],
)
def test_all_performance_statement_combinations(turnover, capacity, answer):
    item = task(CASES[12])
    rows = item["authoring_context"]["selected_response_contract"]["rows"]
    rows[0]["actual"] = turnover
    rows[1]["actual"] = capacity
    assert solver.solve_selected_response(item) == {
        **expected(CASES[12]),
        "answer": answer,
        "mark_points": [answer],
    }


@pytest.mark.parametrize(
    "value,error",
    [("NaN", "non-finite numeric input"), ("nonnumeric", "invalid numeric input")],
)
def test_numeric_input_failures_are_not_coerced(value, error):
    item = task(CASES[0])
    item["authoring_context"]["selected_response_contract"]["inputs"]["base"] = value
    with pytest.raises(ValueError, match=error):
        solver.solve_selected_response(item)


def test_negative_half_up_percentage_change_and_numeric_ambiguity():
    item = task(CASES[2])
    item["authoring_context"]["selected_response_contract"]["inputs"]["final"] = "79"
    item["choices"] = ["-1.2%", "-1.3%", "-1.4%", "-1.5%"]
    assert solver.solve_selected_response(item)["numeric_results"] == {
        "selected_value": -1.3
    }
    item = task(CASES[0])
    item["choices"] = ["100.1", "0100.1", "101.0", "99.9"]
    with pytest.raises(
        ValueError, match="exact precision and exactly one semantic option"
    ):
        solver.solve_selected_response(item)


def test_opportunity_cost_requires_the_public_product_labels():
    item = task(CASES[4])
    item["prompt"] = "Compare the two products."
    with pytest.raises(
        ValueError, match="product labels must match product X and product Y"
    ):
        solver.solve_selected_response(item)
