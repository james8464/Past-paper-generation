from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from Backend.Core.model_recommendations import (
    MODEL_RECOMMENDATIONS_PATH,
    default_ollama_model,
    parse_model_recommendations,
)


def payload() -> dict[str, object]:
    return json.loads(MODEL_RECOMMENDATIONS_PATH.read_text(encoding="utf-8"))


def test_recommendation_registry_is_contiguous_and_owns_cli_default() -> None:
    recommendations = parse_model_recommendations(payload())

    assert recommendations.default_model == default_ollama_model()
    assert recommendations.tiers[0].minimum_memory_gb == 0
    assert recommendations.tiers[0].maximum_memory_gb == 16
    assert recommendations.tiers[1].minimum_memory_gb == 16
    assert recommendations.tiers[-1].maximum_memory_gb is None
    assert "results" in recommendations.other_model_warning.casefold()


def test_recommendation_registry_rejects_memory_gaps() -> None:
    value = copy.deepcopy(payload())
    value["tiers"][1]["minimum_memory_gb"] = 17

    with pytest.raises(ValueError, match="contiguous"):
        parse_model_recommendations(value)


@pytest.mark.parametrize("version", [True, 1.0, "1"])
def test_schema_version_requires_an_integer(version: object) -> None:
    value = payload()
    value["schema_version"] = version
    with pytest.raises(ValueError, match="schema"):
        parse_model_recommendations(value)


@pytest.mark.parametrize("flag", ["false", "true", 0, 1, None, [], {}])
def test_qualification_flag_is_not_coerced(flag: object) -> None:
    value = payload()
    value["tiers"][0]["validated_for_full_matrix"] = flag
    with pytest.raises(ValueError, match="validated_for_full_matrix"):
        parse_model_recommendations(value)


def test_missing_qualification_flag_is_rejected() -> None:
    value = payload()
    del value["tiers"][0]["validated_for_full_matrix"]
    with pytest.raises(ValueError, match="validated_for_full_matrix"):
        parse_model_recommendations(value)


def test_boolean_memory_is_not_a_zero_gb_boundary() -> None:
    value = payload()
    value["tiers"][0]["minimum_memory_gb"] = False
    with pytest.raises(ValueError, match="minimum_memory_gb"):
        parse_model_recommendations(value)


def test_infinite_memory_boundary_cannot_form_a_valid_partition() -> None:
    value = payload()
    value["tiers"][0]["maximum_memory_gb"] = float("inf")
    value["tiers"][1]["minimum_memory_gb"] = float("inf")
    with pytest.raises(ValueError, match="memory_gb"):
        parse_model_recommendations(value)


@pytest.mark.parametrize("field", ["minimum_memory_gb", "maximum_memory_gb"])
@pytest.mark.parametrize(
    "boundary", [True, float("nan"), float("inf"), -float("inf"), 10**400]
)
def test_memory_boundaries_are_finite_numbers(field: str, boundary: object) -> None:
    value = payload()
    value["tiers"][0][field] = boundary
    with pytest.raises(ValueError, match=field):
        parse_model_recommendations(value)


def test_finite_fractional_memory_boundaries_remain_valid() -> None:
    value = payload()
    value["tiers"][0]["maximum_memory_gb"] = 15.5
    value["tiers"][1]["minimum_memory_gb"] = 15.5
    parsed = parse_model_recommendations(value)
    assert parsed.tiers[0].maximum_memory_gb == 15.5
    assert parsed.tiers[1].minimum_memory_gb == 15.5


@pytest.mark.parametrize("flag", [True, False])
def test_typed_qualification_flags_are_preserved(flag: bool) -> None:
    value = payload()
    value["tiers"][0]["validated_for_full_matrix"] = flag
    assert parse_model_recommendations(value).tiers[0].validated_for_full_matrix is flag


def test_default_model_must_be_a_declared_recommendation() -> None:
    value = copy.deepcopy(payload())
    value["default_model"] = "undeclared:model"

    with pytest.raises(ValueError, match="default_model"):
        parse_model_recommendations(value)


def test_unqualified_tiers_do_not_claim_comparative_quality() -> None:
    document = payload()
    assert all(tier["validated_for_full_matrix"] is False for tier in document["tiers"])
    copy = " ".join(
        f"{tier['title']} {tier['detail']} {tier['quality_note']}"
        for tier in document["tiers"]
    ).casefold()
    assert "best balance" not in copy
    assert "recommended for paper quality" not in copy


def test_warning_separates_memory_from_paper_review() -> None:
    warning = payload()["other_model_warning"].casefold()
    assert "tuned and checked" not in warning
    assert "memory" in warning
    assert "not passed a complete paper-quality review" in warning


def test_model_guide_does_not_promise_output_correctness() -> None:
    root = Path(__file__).resolve().parents[1]
    view = (
        root / "macOS/Keldin/Features/Onboarding/WelcomeHelpViews.swift"
    ).read_text()
    assert "It follows the app’s exact JSON schemas" not in view
    assert "It has enough reasoning capacity" not in view
    assert "for the intended quality level" not in view
    assert "Invalid output can stop generation." in view


def test_resource_backed_guidance_has_french_translations() -> None:
    root = Path(__file__).resolve().parents[1]
    catalogue = json.loads((root / "macOS/Keldin/Localizable.xcstrings").read_text())[
        "strings"
    ]
    document = payload()
    keys = [document["other_model_warning"], "About %@ GB download · %@ app context"]
    for tier in document["tiers"]:
        keys.extend(tier[field] for field in ["title", "detail", "quality_note"])
    for key in keys:
        french = catalogue[key]["localizations"]["fr"]["stringUnit"]
        assert french["state"] == "translated"
        assert french["value"].strip() and french["value"] != key


def test_provider_subtitle_uses_a_localised_resource() -> None:
    root = Path(__file__).resolve().parents[1]
    settings = (root / "macOS/Keldin/Features/Settings/SettingsPane.swift").read_text()
    assert "application.aiProvider.subtitleResource" in settings


def test_help_formats_dynamic_values_from_selected_language() -> None:
    root = Path(__file__).resolve().parents[1]
    help_view = (
        root / "macOS/Keldin/Features/Onboarding/WelcomeHelpViews.swift"
    ).read_text()
    assert "downloadResource(locale: selectedLocale" in help_view
    assert "private var currentMemoryResource: LocalizedStringResource" in help_view
