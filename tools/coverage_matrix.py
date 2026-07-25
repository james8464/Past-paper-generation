from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "Resources"
LAYOUT_PROFILES = RESOURCES / "layout-profiles.json"
GENERATOR_REGISTRY = RESOURCES / "generator-registry.json"
COVERAGE_MATRIX = RESOURCES / "coverage-matrix.json"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def build_matrix(
    layout_profiles: dict[str, Any],
    generator_registry: dict[str, Any],
    *,
    resources_root: Path = RESOURCES,
) -> dict[str, Any]:
    if layout_profiles.get("qualification") != "a-level":
        raise ValueError("layout profiles must describe A-level papers")
    if generator_registry.get("qualification") != "a-level":
        raise ValueError("generator registry must describe A-level papers")

    gates = generator_registry.get("readiness_gates")
    if not isinstance(gates, list) or not gates or not all(isinstance(gate, str) for gate in gates):
        raise ValueError("readiness_gates must be a non-empty string list")
    if len(gates) != len(set(gates)):
        raise ValueError("readiness_gates contains duplicates")

    profiles = layout_profiles.get("profiles")
    families = generator_registry.get("families")
    if not isinstance(profiles, list) or not isinstance(families, list):
        raise ValueError("profiles and families must be lists")

    implementations: dict[str, dict[str, Any]] = {}
    for implementation in families:
        _validate_implementation(implementation, gates, resources_root)
        family_id = str(implementation["id"])
        if family_id in implementations:
            raise ValueError(f"duplicate generator family: {family_id}")
        implementations[family_id] = implementation

    matrix_families: list[dict[str, Any]] = []
    seen_profile_ids: set[str] = set()
    for profile in profiles:
        board = str(profile["board"])
        subject = str(profile["subject"])
        family_id = f"{board}/{subject}"
        if family_id in seen_profile_ids:
            raise ValueError(f"duplicate layout profile: {family_id}")
        seen_profile_ids.add(family_id)

        implementation = implementations.pop(family_id, None)
        papers = _paper_rows(implementation, gates) if implementation else []
        declared_papers = list(implementation["declared_papers"]) if implementation else []
        supported_papers = [paper["id"] for paper in papers]
        verified_papers = [paper["id"] for paper in papers if paper["status"] == "verified"]
        if not implementation:
            status = "reference-profiled"
        elif set(supported_papers) != set(declared_papers):
            status = "partial"
        elif len(verified_papers) == len(declared_papers):
            status = "verified"
        else:
            status = "implemented"

        row: dict[str, Any] = {
            "id": family_id,
            "board": board,
            "subject": subject,
            "status": status,
            "reference": {
                "question_papers_profiled": profile["question_papers_profiled"],
                "page_count": profile["page_count"],
                "primary_page_size": profile["primary_page_size"],
                "median_text_margins": profile["median_text_margins"],
            },
            "declared_papers": declared_papers,
            "supported_papers": supported_papers,
            "verified_papers": verified_papers,
            "papers": papers,
        }
        if implementation:
            row["implementation"] = {
                key: implementation[key]
                for key in (
                    "app_subject",
                    "app_board",
                    "backend_subject",
                    "resource_path",
                    "advertised",
                )
            }
        matrix_families.append(row)

    if implementations:
        unknown = ", ".join(sorted(implementations))
        raise ValueError(f"generator families have no matching layout profile: {unknown}")

    counts = {
        status: sum(family["status"] == status for family in matrix_families)
        for status in ("reference-profiled", "partial", "implemented", "verified")
    }
    return {
        "schema_version": 1,
        "qualification": "a-level",
        "derived_reference_data_only": True,
        "readiness_gates": gates,
        "summary": {
            "families": len(matrix_families),
            "boards": len({family["board"] for family in matrix_families}),
            "advertised_families": sum(
                bool(family.get("implementation", {}).get("advertised"))
                for family in matrix_families
            ),
            **counts,
        },
        "families": matrix_families,
    }


def _validate_implementation(
    implementation: Any,
    readiness_gates: list[str],
    resources_root: Path,
) -> None:
    if not isinstance(implementation, dict):
        raise ValueError("each generator family must be an object")
    required = {
        "id",
        "board",
        "subject",
        "app_subject",
        "app_board",
        "backend_subject",
        "resource_path",
        "advertised",
        "declared_papers",
        "papers",
    }
    missing = sorted(required - implementation.keys())
    if missing:
        raise ValueError(f"generator family missing fields: {', '.join(missing)}")
    expected_id = f"{implementation['board']}/{implementation['subject']}"
    if implementation["id"] != expected_id:
        raise ValueError(f"generator family id must be {expected_id}")
    resource_path = resources_root / str(implementation["resource_path"])
    if not resource_path.is_dir():
        raise ValueError(f"generator resource path does not exist: {resource_path}")
    declared = implementation["declared_papers"]
    papers = implementation["papers"]
    if not isinstance(declared, list) or not declared:
        raise ValueError(f"{expected_id} must declare its complete paper inventory")
    if len(declared) != len(set(declared)):
        raise ValueError(f"{expected_id} declares duplicate papers")
    if not isinstance(papers, list):
        raise ValueError(f"{expected_id} papers must be a list")
    paper_ids: set[str] = set()
    for paper in papers:
        if not isinstance(paper, dict):
            raise ValueError(f"{expected_id} paper must be an object")
        paper_id = str(paper.get("id", ""))
        if not paper_id or paper_id not in declared:
            raise ValueError(f"{expected_id} has an undeclared paper: {paper_id}")
        if paper_id in paper_ids:
            raise ValueError(f"{expected_id} has duplicate paper implementation: {paper_id}")
        paper_ids.add(paper_id)
        paper_gates = paper.get("gates")
        if not isinstance(paper_gates, dict):
            raise ValueError(f"{expected_id} paper {paper_id} has no gate object")
        if set(paper_gates) != set(readiness_gates):
            raise ValueError(f"{expected_id} paper {paper_id} gates do not match registry")
        if not all(isinstance(value, bool) for value in paper_gates.values()):
            raise ValueError(f"{expected_id} paper {paper_id} gates must be booleans")


def _paper_rows(
    implementation: dict[str, Any],
    readiness_gates: list[str],
) -> list[dict[str, Any]]:
    rows = []
    for paper in implementation["papers"]:
        gate_values = {gate: paper["gates"][gate] for gate in readiness_gates}
        rows.append(
            {
                "id": str(paper["id"]),
                "title": str(paper["title"]),
                "detail": str(paper["detail"]),
                "status": "verified" if all(gate_values.values()) else "implemented",
                "gates": gate_values,
            }
        )
    return rows


def render_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the A-level generator coverage matrix.")
    parser.add_argument("--write", action="store_true", help="write Resources/coverage-matrix.json")
    parser.add_argument("--check", action="store_true", help="fail if the checked-in matrix is stale")
    args = parser.parse_args(argv)
    if args.write and args.check:
        parser.error("--write and --check are mutually exclusive")

    matrix = build_matrix(load_json(LAYOUT_PROFILES), load_json(GENERATOR_REGISTRY))
    rendered = render_json(matrix)
    if args.write:
        COVERAGE_MATRIX.write_text(rendered, encoding="utf-8")
        return 0
    if args.check:
        if not COVERAGE_MATRIX.exists() or COVERAGE_MATRIX.read_text(encoding="utf-8") != rendered:
            raise SystemExit("Resources/coverage-matrix.json is stale; run tools/coverage_matrix.py --write")
        return 0
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
