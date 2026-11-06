"""Reference distribution normalization must not silently discard mass."""

import json
from copy import deepcopy
from hashlib import sha256

import pytest
from pydantic import ValidationError

from Backend.Core.reference_demand import (
    PROFILES_PATH,
    ReferenceDemandDocument,
    ReferenceDemandProfile,
)
from tests.test_reference_demand import profile_payload

DISTRIBUTIONS = (
    "mark_band_distribution",
    "command_word_distribution",
    "demand_distribution",
    "mark_weighted_demand_distribution",
    "response_mode_distribution",
    "cognitive_operation_distribution",
)


@pytest.mark.parametrize("field", DISTRIBUTIONS)
def test_casefold_colliding_keys_refuse_instead_of_losing_probability_mass(field):
    payload = profile_payload()
    payload[field] = {"HIGH": 0.5, "high": 0.5}
    original = deepcopy(payload)
    with pytest.raises(ValidationError, match="distinct normalized keys"):
        ReferenceDemandProfile.model_validate(payload)
    assert payload == original


@pytest.mark.parametrize("field", DISTRIBUTIONS)
def test_one_mixed_case_key_still_normalizes_without_changing_its_mass(field):
    payload = profile_payload()
    payload[field] = {"MiXeD": 1.0}
    original = deepcopy(payload)
    profile = ReferenceDemandProfile.model_validate(payload)
    assert getattr(profile, field) == {"mixed": 1.0}
    assert payload == original


@pytest.mark.parametrize("field", DISTRIBUTIONS)
@pytest.mark.parametrize("value", [None, ["high"], {"high": "1.0"}, {" ": 1.0}])
def test_existing_distribution_type_and_empty_key_refusals_remain(field, value):
    payload = profile_payload()
    payload[field] = value
    with pytest.raises(ValidationError):
        ReferenceDemandProfile.model_validate(payload)


def test_unknown_profile_fields_still_refuse():
    payload = profile_payload()
    payload["unowned_distribution"] = {"high": 1.0}
    with pytest.raises(ValidationError, match="Extra inputs"):
        ReferenceDemandProfile.model_validate(payload)


def test_checked_in_profile_values_and_serialization_are_unchanged():
    original_bytes = PROFILES_PATH.read_bytes()
    original = json.loads(original_bytes)
    document = ReferenceDemandDocument.model_validate(original)
    assert (
        sha256(document.model_dump_json().encode()).hexdigest()
        == "1841185823e63a401af1137fb684f4b2b713edd95b1ecb9d0d484d390abb07d1"
    )
    serialized = document.model_dump(mode="json")
    for source, profile in zip(
        original["profiles"], serialized["profiles"], strict=True
    ):
        for field in DISTRIBUTIONS:
            assert profile[field] == source[field]
        assert profile["source_fingerprint"] == source["source_fingerprint"]
    assert (
        ReferenceDemandDocument.model_validate(serialized).model_dump(mode="json")
        == serialized
    )
    assert PROFILES_PATH.read_bytes() == original_bytes
