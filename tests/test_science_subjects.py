from __future__ import annotations

import pytest

from Backend.Core.subject_plugins import discover_subject_plugin, subject_plugin_ids
from Backend.Core.subjects.biology import BiologyPlugin
from Backend.Core.subjects.chemistry import (
    ChemistryPlugin,
    Formula,
    equation_is_balanced,
)
from Backend.Core.subjects.physics import PhysicsPlugin, compare_physical_answers


def test_science_plugins_are_discoverable() -> None:
    assert {"biology", "chemistry", "physics"} <= set(subject_plugin_ids())
    assert isinstance(discover_subject_plugin("biology"), BiologyPlugin)
    assert isinstance(discover_subject_plugin("chemistry"), ChemistryPlugin)
    assert isinstance(discover_subject_plugin("physics"), PhysicsPlugin)


def test_biology_requires_practical_and_data_provenance_when_declared() -> None:
    plugin = BiologyPlugin()
    invalid = plugin.validate_item(
        {
            "question": "Evaluate this investigation.",
            "marks": 4,
            "item_kind": "required-practical",
            "data": [[1, 2], [2, 3]],
        }
    )
    valid = plugin.validate_item(
        {
            "question": "Evaluate this investigation.",
            "marks": 4,
            "item_kind": "required-practical",
            "required_practical_id": "RP06",
            "data": [[1, 2], [2, 3]],
            "data_provenance": "deterministic-simulation:v1",
            "answer": "Controls, repeats, and an appropriate statistical test",
        }
    )

    assert invalid.passed is False
    assert valid.passed is True


@pytest.mark.parametrize(
    ("value", "elements"),
    [
        ("H2SO4", {"H": 2, "S": 1, "O": 4}),
        ("Ca(OH)2", {"Ca": 1, "O": 2, "H": 2}),
        ("Al2(SO4)3", {"Al": 2, "S": 3, "O": 12}),
    ],
)
def test_chemical_formula_parser_counts_atoms(value: str, elements: dict[str, int]) -> None:
    assert Formula.parse(value).elements == elements


@pytest.mark.parametrize("value", ["", "Ca(OH2", "Na)Cl(", "2H2O", "H2O!"])
def test_chemical_formula_parser_rejects_malformed_formulae(value: str) -> None:
    with pytest.raises(ValueError):
        Formula.parse(value)


def test_chemical_equation_balance_is_verified() -> None:
    assert equation_is_balanced("2H2 + O2 -> 2H2O") is True
    assert equation_is_balanced("H2 + O2 -> H2O") is False


def test_chemistry_rejects_an_unbalanced_canonical_equation() -> None:
    result = ChemistryPlugin().validate_item(
        {
            "question": "Write the equation for the formation of water.",
            "marks": 2,
            "answer_kind": "chemical-equation",
            "answer": "H2 + O2 -> H2O",
        }
    )

    assert result.passed is False
    assert any("balanced" in diagnostic for diagnostic in result.diagnostics)


def test_physics_checks_value_unit_and_significant_figures() -> None:
    assert compare_physical_answers("12.0", "12", "V", "V", significant_figures=3)
    assert not compare_physical_answers("12.0", "12", "A", "V", significant_figures=3)
    assert not compare_physical_answers("12", "12", "V", "V", significant_figures=3)


def test_physics_requires_uncertainty_for_uncertainty_items() -> None:
    invalid = PhysicsPlugin().validate_item(
        {
            "question": "Calculate the result with its uncertainty.",
            "marks": 3,
            "answer": "4.2",
            "unit": "m",
            "answer_kind": "uncertainty",
        }
    )

    assert invalid.passed is False
    assert any("uncertainty" in diagnostic for diagnostic in invalid.diagnostics)
