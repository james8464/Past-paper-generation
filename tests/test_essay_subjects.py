from __future__ import annotations

import pytest

from Backend.Core.subject_plugins import discover_subject_plugin, subject_plugin_ids


def test_later_wave_subject_plugins_are_discoverable() -> None:
    expected = {
        "english-literature",
        "further-mathematics",
        "geography",
        "history",
        "psychology",
        "sociology",
    }

    assert expected <= set(subject_plugin_ids())
    assert all(discover_subject_plugin(identifier).id == identifier for identifier in expected)


@pytest.mark.parametrize(
    ("subject", "item"),
    [
        (
            "psychology",
            {"question": "Evaluate the study.", "marks": 8, "study": "Example et al."},
        ),
        (
            "geography",
            {"question": "Assess the response.", "marks": 12, "case_study": "Coastal town"},
        ),
        (
            "sociology",
            {"question": "Evaluate this view.", "marks": 20, "theorist": "Example"},
        ),
        (
            "history",
            {"question": "Assess the interpretation.", "marks": 25, "source_extract": "Quoted text"},
        ),
        (
            "english-literature",
            {"question": "Analyse the extract.", "marks": 25, "extract": "Quoted text"},
        ),
    ],
)
def test_essay_subjects_reject_unprovenanced_evidence(
    subject: str,
    item: dict[str, object],
) -> None:
    result = discover_subject_plugin(subject).validate_item(item)

    assert result.passed is False
    assert any("provenance" in diagnostic for diagnostic in result.diagnostics)


def test_authorised_extract_with_option_route_and_level_policy_passes() -> None:
    item = {
        "question": "Compare how the writers present isolation.",
        "marks": 25,
        "extract": "A rights-cleared extract held outside the assessment package.",
        "source_provenance": {
            "source_id": "licensed-edition:work:chapter",
            "rights_basis": "licensed",
            "verification_hash": "sha256:example",
        },
        "option_route": "route-a",
        "level_policy_id": "aqa-essay-v1",
        "answer": "A comparison grounded in methods, context, and the supplied extract.",
    }

    assert discover_subject_plugin("english-literature").validate_item(item).passed is True


def test_history_rejects_an_inverted_chronology() -> None:
    result = discover_subject_plugin("history").validate_item(
        {
            "question": "Explain the development.",
            "marks": 12,
            "answer": "A causal explanation.",
            "chronology": [1918, 1914],
        }
    )

    assert result.passed is False
    assert any("chronological" in diagnostic for diagnostic in result.diagnostics)
