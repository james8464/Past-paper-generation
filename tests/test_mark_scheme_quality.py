from __future__ import annotations

import pytest

from Backend.Core.mark_scheme_quality import validate_mark_scheme_item


def _item(**updates: object) -> dict[str, object]:
    item: dict[str, object] = {
        "id": "1",
        "marks": 2,
        "kind": "short_answer",
        "command_word": "State",
        "assessment_objectives": {"AO1": 2},
        "mark_scheme": ["Award one mark for each of two correct features."],
        "structured_mark_scheme": [],
    }
    item.update(updates)
    return item


def test_concise_low_mark_scheme_is_valid() -> None:
    report = validate_mark_scheme_item(_item())

    assert report.points == 1
    assert report.has_levels is False


def test_extended_response_rejects_generic_shallow_guidance() -> None:
    with pytest.raises(ValueError, match="item 1.*too shallow"):
        validate_mark_scheme_item(
            _item(
                marks=20,
                kind="extended_response",
                command_word="Evaluate",
                assessment_objectives={"AO1": 4, "AO2": 4, "AO3": 6, "AO4": 6},
                mark_scheme=["Credit a good answer."],
            )
        )


def test_extended_response_requires_levels_alternatives_and_credit_limits() -> None:
    base = _item(
        marks=12,
        kind="extended_response",
        command_word="Assess",
        assessment_objectives={"AO1": 2, "AO2": 2, "AO3": 4, "AO4": 4},
        mark_scheme=[
            "AO1: explains the relevant concept accurately.",
            "AO2: applies the figures in the supplied context.",
            "AO3: develops a complete causal chain.",
            "AO4: reaches a supported judgement.",
        ],
    )

    with pytest.raises(ValueError, match="levels descriptors"):
        validate_mark_scheme_item(base)

    base["mark_scheme"] = [
        *base["mark_scheme"],
        "Levels-based marking: use best fit across the whole response.",
        "Level 3 (9–12): sustained analysis and supported evaluation.",
        "Level 2 (5–8): some developed analysis with partial evaluation.",
        "Level 1 (1–4): isolated relevant points.",
        "Accept an equivalent valid analytical route.",
        "Do not award the same developed point twice.",
    ]
    report = validate_mark_scheme_item(base)

    assert report.has_levels is True
    assert report.has_alternatives is True
    assert report.has_credit_limits is True
    assert report.covered_objectives == ("AO1", "AO2", "AO3", "AO4")


def test_depth_includes_distinct_structured_level_descriptors() -> None:
    item = _item(
        marks=12,
        kind="extended_response",
        command_word="Assess",
        assessment_objectives={"AO1": 2, "AO2": 2, "AO3": 4, "AO4": 4},
        mark_scheme=[
            "AO1: explains the relevant concept accurately.",
            "AO2: applies the figures in the supplied context.",
            "AO3: develops a complete causal chain.",
            "AO4: reaches a supported judgement.",
        ],
        structured_mark_scheme=[
            {
                "text": f"Level {level}: distinct descriptor for band {level}.",
                "marks": 0,
                "credit_type": "level",
                "alternatives": (
                    ["Accept an equivalent valid analytical route."]
                    if level == 3
                    else []
                ),
                "do_not_accept": (
                    ["Do not award the same developed point twice."]
                    if level == 1
                    else []
                ),
            }
            for level in range(1, 4)
        ],
    )

    report = validate_mark_scheme_item(item)

    assert report.points == 7
    assert report.has_levels is True


def test_calculation_requires_method_or_working() -> None:
    item = _item(
        marks=4,
        kind="calculation",
        command_word="Calculate",
        assessment_objectives={"AO2": 4},
        mark_scheme=[
            "AO2: the correct final answer is £240.",
            "Accept £240 only.",
        ],
    )

    with pytest.raises(ValueError, match="working or method"):
        validate_mark_scheme_item(item)

    item["mark_scheme"] = [
        "AO2: method: contribution = revenue − variable cost.",
        "Working: £600 − £360 = £240.",
        "Accept £240 with a consistent unit.",
    ]
    assert validate_mark_scheme_item(item).has_working is True


def test_declared_ao_allocation_must_be_covered() -> None:
    with pytest.raises(ValueError, match="does not cover AO3"):
        validate_mark_scheme_item(
            _item(
                marks=6,
                kind="analysis",
                command_word="Analyse",
                assessment_objectives={"AO1": 2, "AO2": 2, "AO3": 2},
                mark_scheme=[
                    "AO1: defines the concept.",
                    "AO2: applies the contextual figure.",
                    "Accept equivalent terminology.",
                ],
            )
        )


def test_accounting_follow_through_metadata_counts_as_method_guidance() -> None:
    item = _item(
        marks=6,
        kind="calculation",
        command_word="Calculate",
        assessment_objectives={"AO2": 6},
        mark_scheme=[
            "AO2: contribution is revenue less variable cost.",
            "AO2: profit is contribution less fixed cost.",
        ],
        structured_mark_scheme=[
            {
                "text": "Computes contribution from the supplied figures.",
                "marks": 3,
                "credit_type": "point",
                "assessment_objective": "AO2",
                "allow": ["Accept a consistent own-figure result."],
                "do_not_accept": ["Do not accept revenue less fixed cost."],
                "depends_on": ["revenue", "variable_cost"],
            },
            {
                "text": "Deducts fixed cost to obtain profit.",
                "marks": 3,
                "credit_type": "point",
                "assessment_objective": "AO2",
                "depends_on": ["contribution", "fixed_cost"],
            },
        ],
    )

    report = validate_mark_scheme_item(item)

    assert report.has_working is True
    assert report.has_alternatives is True
    assert report.has_credit_limits is True


def test_source_dependent_scheme_must_bind_its_evidence() -> None:
    item = _item(
        marks=4,
        kind="data",
        command_word="Explain",
        assessment_objectives={"AO2": 4},
        evidence_ids=["Figure 2"],
        mark_scheme=[
            "AO2: identifies the relevant trend.",
            "AO2: explains the likely consequence.",
        ],
    )

    with pytest.raises(ValueError, match="does not bind its required evidence"):
        validate_mark_scheme_item(item)

    item["mark_scheme"] = [
        "AO2: uses Figure 2 to identify the relevant trend.",
        "AO2: explains the likely consequence of that evidence.",
    ]
    assert validate_mark_scheme_item(item).has_evidence_binding is True


def test_structured_computer_science_guidance_covers_equivalent_pseudocode() -> None:
    item = _item(
        marks=5,
        kind="programming",
        command_word="Write",
        assessment_objectives={"AO2": 5},
        mark_scheme=[
            "AO2: initialises the accumulator before the loop.",
            "AO2: iterates over every element exactly once.",
        ],
        structured_mark_scheme=[
            {
                "text": "Updates and returns the accumulator.",
                "marks": 5,
                "credit_type": "point",
                "assessment_objective": "AO2",
                "alternatives": ["Accept equivalent unambiguous pseudocode."],
                "do_not_accept": ["Reject an off-by-one loop."],
            }
        ],
    )

    report = validate_mark_scheme_item(item)

    assert report.has_alternatives is True
    assert report.has_credit_limits is True


def test_contract_alternatives_boundaries_and_follow_through_are_mandatory() -> None:
    item = _item(
        marks=4,
        kind="calculation",
        command_word="Calculate",
        assessment_objectives={"AO2": 4},
        mark_scheme=[
            "AO2: method: subtract variable cost from revenue.",
            "AO2: working gives the correct final answer.",
        ],
        assessment_contract={
            "valid_alternatives": ["accept equivalent graphical method"],
            "partial_credit_boundaries": ["method only: maximum 2 marks"],
            "follow_through_rules": ["allow a consistent own-figure answer"],
        },
    )

    with pytest.raises(ValueError, match="contract guidance"):
        validate_mark_scheme_item(item)

    item["mark_scheme"].extend(
        [
            "Accept equivalent graphical method.",
            "Method only: maximum 2 marks.",
            "Allow a consistent own-figure answer.",
        ]
    )
    assert validate_mark_scheme_item(item).has_alternatives is True
