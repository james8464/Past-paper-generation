"""Experimental authoring replay binds the entire exercise, not just answers."""

from copy import deepcopy

import pytest

from Backend.Core.france.synthesized_authoring import author, replay


@pytest.mark.parametrize("family", ["recursive", "postfix"])
def test_replay_preserves_complete_candidate_and_provenance(family):
    raw, evidence = author(family, 713, references=[{"id": "fr-reference"}])
    assert evidence["origin"] == "application_owned"
    assert evidence["model_used"] is False
    assert replay(family, 713, [{"id": "fr-reference"}], raw, evidence) == raw
    for field in ("prompt", "answer", "marking", "verification", "points"):
        changed = deepcopy(raw)
        changed["questions"][0][field] = "forged"
        with pytest.raises(ValueError):
            replay(family, 713, [{"id": "fr-reference"}], changed, evidence)


@pytest.mark.parametrize("family", ["recursive", "postfix"])
def test_rehashed_tampering_is_not_replay(family):
    from Backend.Core.france.database_depth_authoring import _hash

    raw, evidence = author(family, 713, references=[])
    raw["questions"][0]["answer"] = "Untrusted answer"
    evidence["candidate_sha256"] = _hash(raw)
    with pytest.raises(ValueError):
        replay(family, 713, [], raw, evidence)


def test_extra_evidence_fields_and_relabelled_origin_are_rejected():
    raw, evidence = author("postfix", 713, references=[])
    for changed in (
        {**evidence, "origin": "model_authored"},
        {**evidence, "approved": True},
        {**evidence, "model_used": True},
    ):
        with pytest.raises(ValueError):
            replay("postfix", 713, [], raw, changed)


def test_replay_does_not_mutate_caller_data():
    references = [{"id": "fr", "metadata": {"split": "reference"}}]
    raw, evidence = author("recursive", 713, references=references)
    before = deepcopy((references, raw, evidence))
    restored = replay("recursive", 713, references, raw, evidence)
    assert (references, raw, evidence) == before
    restored["questions"][0]["answer"] = "changed outside replay"
    assert raw == before[1]


def test_seed_family_reference_and_source_are_bound(monkeypatch):
    import Backend.Core.france.synthesized_authoring as module

    raw, evidence = author("postfix", 713, references=[])
    for family, seed, references in [
        ("recursive", 713, []),
        ("postfix", 714, []),
        ("postfix", 713, [{"id": "other"}]),
    ]:
        with pytest.raises(ValueError):
            replay(family, seed, references, raw, evidence)
    monkeypatch.setattr(module, "catalogue_digest", lambda: "changed-source")
    with pytest.raises(ValueError):
        replay("postfix", 713, [], raw, evidence)


@pytest.mark.parametrize(
    "family,seed,references",
    [
        ("unknown", 713, []),
        ("postfix", True, []),
        ("postfix", 713, None),
        ("postfix", 713, ["invalid"]),
    ],
)
def test_invalid_authoring_inputs_fail_closed(family, seed, references):
    with pytest.raises(ValueError):
        author(family, seed, references=references)
