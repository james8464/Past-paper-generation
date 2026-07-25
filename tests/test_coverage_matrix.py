from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tools.coverage_matrix import (
    COVERAGE_MATRIX,
    GENERATOR_REGISTRY,
    LAYOUT_PROFILES,
    RESOURCES,
    build_matrix,
    load_json,
    render_json,
)


def matrix() -> dict[str, object]:
    return build_matrix(
        load_json(LAYOUT_PROFILES),
        load_json(GENERATOR_REGISTRY),
    )


def family(value: dict[str, object], family_id: str) -> dict[str, object]:
    families = value["families"]
    assert isinstance(families, list)
    return next(item for item in families if item["id"] == family_id)


def test_matrix_exactly_covers_layout_profiles() -> None:
    value = matrix()
    profiles = load_json(LAYOUT_PROFILES)["profiles"]
    assert value["summary"]["families"] == 105
    assert value["summary"]["boards"] == 3
    assert {item["id"] for item in value["families"]} == {
        f"{item['board']}/{item['subject']}" for item in profiles
    }


def test_existing_generators_are_reported_without_false_verification() -> None:
    value = matrix()
    economics = family(value, "pearson-edexcel/economics-a-2015")
    computer_science = family(value, "aqa/computer-science")
    assert economics["status"] == "implemented"
    assert economics["supported_papers"] == ["1", "2", "3"]
    assert economics["verified_papers"] == []
    assert computer_science["status"] == "implemented"
    assert computer_science["declared_papers"] == ["1", "2"]
    assert computer_science["supported_papers"] == ["1", "2"]
    assert computer_science["verified_papers"] == []


def test_unimplemented_family_is_reference_profiled() -> None:
    biology = family(matrix(), "aqa/biology")
    assert biology["status"] == "reference-profiled"
    assert biology["papers"] == []
    assert "implementation" not in biology


def test_checked_in_matrix_is_deterministic_and_current() -> None:
    assert COVERAGE_MATRIX.read_text(encoding="utf-8") == render_json(matrix())


def test_registry_rejects_unknown_layout_family() -> None:
    registry = copy.deepcopy(load_json(GENERATOR_REGISTRY))
    registry["families"][0]["id"] = "aqa/not-a-subject"
    registry["families"][0]["subject"] = "not-a-subject"
    with pytest.raises(ValueError, match="no matching layout profile"):
        build_matrix(load_json(LAYOUT_PROFILES), registry)


def test_registry_rejects_missing_gate() -> None:
    registry = copy.deepcopy(load_json(GENERATOR_REGISTRY))
    del registry["families"][0]["papers"][0]["gates"]["difficulty"]
    with pytest.raises(ValueError, match="gates do not match registry"):
        build_matrix(load_json(LAYOUT_PROFILES), registry)


def test_registry_rejects_missing_resource_pack(tmp_path: Path) -> None:
    registry = copy.deepcopy(load_json(GENERATOR_REGISTRY))
    with pytest.raises(ValueError, match="resource path does not exist"):
        build_matrix(load_json(LAYOUT_PROFILES), registry, resources_root=tmp_path)


def test_no_verified_paper_has_a_failed_gate() -> None:
    for item in matrix()["families"]:
        for paper in item["papers"]:
            assert (paper["status"] == "verified") is all(paper["gates"].values())


def test_reference_corpus_is_not_a_shipped_resource_path() -> None:
    registry_text = json.dumps(load_json(GENERATOR_REGISTRY))
    assert "Reference Corpus" not in registry_text
    for item in matrix()["families"]:
        implementation = item.get("implementation")
        if implementation:
            assert (RESOURCES / implementation["resource_path"]).is_dir()


def test_catalog_availability_is_owned_only_by_registry() -> None:
    catalog = load_json(RESOURCES / "catalog.json")
    registry = load_json(GENERATOR_REGISTRY)
    assert "ready_generators" not in catalog
    assert all("status" not in board for subject in catalog["subjects"] for board in subject["boards"])
    catalog_keys = {
        f"{subject['id']}/{board['id']}"
        for subject in catalog["subjects"]
        for board in subject["boards"]
    }
    advertised_keys = {
        f"{family['app_subject']}/{family['app_board']}"
        for family in registry["families"]
        if family["advertised"]
    }
    assert advertised_keys <= catalog_keys
