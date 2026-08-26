from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from Backend.Core.assessment_contracts import (
    AssessmentContract,
    EvidenceRecord,
    GeneratedNumericField,
    GraphContract,
    NumericRole,
    NumericValueContract,
    contract_for_question,
)
from Backend.Core.assessment_quality import (
    validate_candidate_contract,
    validate_economics_causal_direction,
    validate_package_novelty,
)
from Backend.Core.exam_blueprints import GeneratedQuestion


def test_legacy_question_hydrates_a_contract_without_mutation() -> None:
    question = GeneratedQuestion(
        rule_id="q1",
        number="01",
        marks=4,
        kind="calculation",
        command_word="calculate",
        topic_id="accounting",
        prompt=(
            "Calculate contribution when revenue is £225 and variable cost "
            "is £169."
        ),
        mark_scheme=["£56"],
        assessment_objectives={"AO2": 4},
    )

    contract = contract_for_question(question)

    assert contract.item_id == "q1"
    assert contract.marks == 4
    assert [value.text for value in contract.numeric_values] == ["£225", "£169"]
    assert all(
        value.role is NumericRole.ASSESSMENT_DATA
        for value in contract.numeric_values
    )
    assert question.contract is None


def test_generated_numeric_field_rejects_values_outside_its_closed_range() -> None:
    field = GeneratedNumericField(
        name="equilibrium_price",
        minimum=10,
        maximum=80,
    )

    assert field.validate_value(10) == 10
    assert field.validate_value(45) == 45
    assert field.validate_value(80) == 80
    with pytest.raises(ValueError, match="equilibrium_price"):
        field.validate_value(95)


def test_contract_rejects_unknown_evidence_reference() -> None:
    contract = AssessmentContract(
        item_id="q1",
        marks=4,
        assessment_objectives={"AO2": 4},
        evidence=[EvidenceRecord(id="extract-a", text="Exports rose by 4%.")],
        allowed_evidence_ids={"extract-a"},
    )

    contract.validate_evidence_ids(["extract-a"])
    with pytest.raises(ValueError, match="unknown evidence"):
        contract.validate_evidence_ids(["extract-b"])


def test_contract_rejects_ao_marks_that_do_not_match_item_marks() -> None:
    with pytest.raises(ValidationError, match="assessment objective marks"):
        AssessmentContract(
            item_id="q1",
            marks=4,
            assessment_objectives={"AO1": 1, "AO2": 2},
        )


def test_graph_contract_requires_matching_labels_and_values() -> None:
    with pytest.raises(ValidationError, match="labels and values"):
        GraphContract(
            title="Demand",
            labels=["2024", "2025"],
            values=[42],
        )


def test_explicit_contract_is_returned_unchanged() -> None:
    explicit = AssessmentContract(
        item_id="q1",
        marks=1,
        assessment_objectives={"AO1": 1},
        numeric_values=[
            NumericValueContract(
                text="01",
                role=NumericRole.CODE_LINE_LABEL,
            )
        ],
    )
    question = GeneratedQuestion(
        rule_id="q1",
        number="01",
        marks=1,
        kind="multiple_choice",
        command_word="select",
        topic_id="programming",
        prompt="Select the value printed on line 01.",
        mark_scheme=["A"],
        assessment_objectives={"AO1": 1},
        contract=explicit,
    )

    assert contract_for_question(question) is explicit


def test_unordered_assessment_values_compare_as_a_multiset() -> None:
    contract = AssessmentContract(
        item_id="q1",
        marks=2,
        assessment_objectives={"AO2": 2},
        numeric_values=[
            NumericValueContract(text="55"),
            NumericValueContract(text="5%"),
        ],
    )

    validate_candidate_contract("55 then 5%", "5% follows 55", contract)


def test_code_line_labels_are_not_assessment_values() -> None:
    contract = AssessmentContract(
        item_id="q1",
        marks=2,
        assessment_objectives={"AO2": 2},
        numeric_values=[
            NumericValueContract(
                text="01",
                role=NumericRole.CODE_LINE_LABEL,
            ),
            NumericValueContract(text="225"),
        ],
    )

    validate_candidate_contract("01 total = 225", "07 total = 225", contract)


def test_leading_context_year_is_not_immutable_assessment_data() -> None:
    question = GeneratedQuestion(
        rule_id="mcq",
        number="18",
        marks=1,
        kind="multiple_choice",
        command_word="Select",
        topic_id="economics",
        prompt=(
            "In 2013, output exceeded its sustainable level. Which statement "
            "describes a positive output gap?"
        ),
        mark_scheme=["Actual output exceeds sustainable output."],
        assessment_objectives={"AO1": 1},
    )

    contract = contract_for_question(question)

    assert contract.numeric_values[0].role is NumericRole.DATE
    validate_candidate_contract(
        question.prompt,
        "Which statement describes a positive output gap?",
        contract,
    )


def test_changed_immutable_value_is_rejected() -> None:
    contract = AssessmentContract(
        item_id="q1",
        marks=2,
        assessment_objectives={"AO2": 2},
        numeric_values=[NumericValueContract(text="225")],
    )

    with pytest.raises(ValueError, match="immutable numeric"):
        validate_candidate_contract("Value 225", "Value 169", contract)


def test_equivalent_precision_wording_is_not_treated_as_new_data() -> None:
    contract = AssessmentContract(
        item_id="q1",
        marks=2,
        assessment_objectives={"AO2": 2},
        numeric_values=[
            NumericValueContract(text="2024"),
            NumericValueContract(text="2028"),
        ],
    )

    validate_candidate_contract(
        "Calculate the change from 2024 to 2028 to one decimal place.",
        "Calculate the change from 2024 to 2028 to 1 decimal place.",
        contract,
    )

    with pytest.raises(ValueError, match="precision instruction"):
        validate_candidate_contract(
            "Calculate the change from 2024 to 2028 to one decimal place.",
            "Calculate the change from 2024 to 2028 to 3 decimal places.",
            contract,
        )


def test_novelty_check_ignores_the_package_being_atomically_replaced(
    tmp_path,
) -> None:
    history = tmp_path / "published"
    staging = tmp_path / "transaction"
    history.mkdir()
    staging.mkdir()
    name = "economics-paper-3-assessment.json"
    document = {
        "schema_version": 1,
        "items": [
            {
                "id": "1",
                "subject": "economics",
                "paper": "3",
                "prompt": "Assess the effect of a change in aggregate demand.",
            }
        ],
    }
    (history / name).write_text(json.dumps(document), encoding="utf-8")
    current = staging / name
    current.write_text(json.dumps(document), encoding="utf-8")

    report = validate_package_novelty(current, history_root=history)

    assert report["historic_comparisons"] == 0


def test_declared_generated_graph_value_is_range_checked() -> None:
    contract = AssessmentContract(
        item_id="q1",
        marks=2,
        assessment_objectives={"AO2": 2},
        generated_numeric_fields=[
            GeneratedNumericField(name="year", minimum=2024, maximum=2030)
        ],
    )

    validate_candidate_contract(
        "Plot the result",
        "Plot the result for 2027",
        contract,
        generated_values={"year": 2027},
    )
    with pytest.raises(ValueError, match="year"):
        validate_candidate_contract(
            "Plot the result",
            "Plot the result for 2038",
            contract,
            generated_values={"year": 2038},
        )


def test_undeclared_generated_quantity_is_rejected() -> None:
    contract = AssessmentContract(
        item_id="q1",
        marks=2,
        assessment_objectives={"AO2": 2},
    )

    with pytest.raises(ValueError, match="immutable numeric"):
        validate_candidate_contract("Plot the result", "Plot the result for 2027", contract)


@pytest.mark.parametrize(
    "text",
    [
        "An appreciation raises the domestic-currency cost of imports.",
        "A depreciation lowers import prices in domestic currency.",
    ],
)
def test_economics_direction_validator_rejects_reversed_import_effects(
    text: str,
) -> None:
    with pytest.raises(ValueError, match="exchange-rate direction"):
        validate_economics_causal_direction(text)


def test_economics_direction_validator_accepts_correct_import_effect() -> None:
    validate_economics_causal_direction(
        "An appreciation lowers import prices in domestic currency, all else equal."
    )
