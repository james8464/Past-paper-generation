from __future__ import annotations

import argparse
import importlib
import json
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from Backend.Core.board_profiles import board_profile
from Backend.Core.paths import REPO_ROOT
from Backend.Core.subject_plugins import discover_subject_plugin


@dataclass(frozen=True)
class MigrationIssue:
    code: str
    message: str


@dataclass(frozen=True)
class MigrationReport:
    family_id: str
    resource_path: Path
    issues: tuple[MigrationIssue, ...]

    @property
    def passed(self) -> bool:
        return not self.issues


class MigrationValidator:
    def __init__(
        self,
        repository_root: Path = REPO_ROOT,
        *,
        run_preview: bool = True,
    ) -> None:
        self.root = repository_root.resolve()
        self.resources = self.root / "Resources"
        self.run_preview = run_preview

    def validate_all(self) -> tuple[MigrationReport, ...]:
        registry = self._json(self.resources / "generator-registry.json") or {}
        reports: list[MigrationReport] = []
        for family in registry.get("families", []):
            if not family.get("advertised", False):
                continue
            path = self.resources / str(family.get("resource_path", ""))
            reports.append(self._validate_family(path, family, registry))
        return tuple(reports)

    def advertised_capabilities(self) -> tuple[dict[str, Any], ...]:
        registry = self._json(self.resources / "generator-registry.json") or {}
        return tuple(
            family
            for family in registry.get("families", [])
            if family.get("advertised", False)
        )

    def entry_point_source(self, family: dict[str, Any]) -> str:
        python_root = self.resources / str(family["python_path"])
        module = str(family["entry_point"]).partition(":")[0]
        path = python_root.joinpath(*module.split(".")).with_suffix(".py")
        return path.read_text(encoding="utf-8")

    def validate(self, family_path: Path) -> MigrationReport:
        registry = self._json(self.resources / "generator-registry.json") or {}
        resolved = family_path.resolve()
        family = next(
            (
                item
                for item in registry.get("families", [])
                if (self.resources / str(item.get("resource_path", ""))).resolve()
                == resolved
            ),
            None,
        )
        if family is None:
            return MigrationReport(
                "unknown",
                resolved,
                (MigrationIssue("registry", "family is not present in the registry"),),
            )
        return self._validate_family(resolved, family, registry)

    def _validate_family(
        self,
        family_path: Path,
        family: dict[str, Any],
        registry: dict[str, Any],
    ) -> MigrationReport:
        issues: list[MigrationIssue] = []

        def issue(code: str, message: str) -> None:
            issues.append(MigrationIssue(code, message))

        required = {
            "manifest_version",
            "id",
            "board",
            "subject",
            "app_subject",
            "app_board",
            "backend_subject",
            "resource_path",
            "python_path",
            "package",
            "entry_point",
            "syllabus_path",
            "subject_plugin",
            "board_profile",
            "specification_version",
            "blueprint_version",
            "content_mode",
            "supported_providers",
            "outputs_by_paper",
            "advertised",
            "declared_papers",
            "papers",
        }
        papers = family.get("papers", [])
        declared = [str(value) for value in family.get("declared_papers", [])]
        output_map = family.get("outputs_by_paper", {})
        if (
            registry.get("schema_version") != 4
            or family.get("manifest_version") != 1
            or required - set(family)
            or not isinstance(papers, list)
            or not papers
        ):
            issue("schema", "capability does not conform to manifest version 1")

        catalog = self._json(self.resources / "catalog.json")
        catalog_match = False
        if catalog:
            for subject in catalog.get("subjects", []):
                if subject.get("id") != family.get("app_subject"):
                    continue
                catalog_match = any(
                    board.get("id") == family.get("app_board")
                    for board in subject.get("boards", [])
                )
        if not catalog_match:
            issue("catalog", "family is not exposed by the app catalogue")

        python_root = self.resources / str(family.get("python_path", ""))
        package = str(family.get("package", ""))
        entry_module = str(family.get("entry_point", "")).partition(":")[0]
        module_path = python_root.joinpath(*entry_module.split(".")).with_suffix(".py")
        package_path = python_root / package / "__init__.py"
        if not package_path.is_file() or not module_path.is_file():
            issue("package", "package or entry-point module is missing")

        paper_ids = [str(item.get("id", "")) for item in papers]
        if not declared or paper_ids != declared or set(output_map) != set(declared):
            issue("paper-mapping", "paper records, declarations, and outputs disagree")

        syllabus = self.resources / str(family.get("syllabus_path", ""))
        if not isinstance(self._json(syllabus), dict):
            issue("syllabus", "versioned syllabus JSON is missing or invalid")

        blueprint_version = str(family.get("blueprint_version", "")).strip().lower()
        if blueprint_version in {"", "test", "unconfigured"}:
            issue("blueprint", "a versioned blueprint contract is required")

        try:
            discover_subject_plugin(str(family.get("subject_plugin", "")))
        except ValueError as error:
            issue("subject-plugin", str(error))

        try:
            profile = board_profile(str(family.get("board_profile", "")))
        except ValueError as error:
            profile = None
            issue("layout-profile", str(error))

        required_roles = {"question_paper", "mark_scheme", "assessment_package"}
        if any(
            not required_roles <= set(output_map.get(paper, [])) for paper in declared
        ):
            issue("output-role", "each paper needs question, scheme, and package roles")
        if profile is not None and any(
            not set(output_map.get(paper, [])) <= set(profile.output_roles)
            for paper in declared
        ):
            issue("output-role", "output role is not permitted by the board profile")

        layout_payload = self._json(self.resources / "layout-profiles.json") or {}
        layout_keys = {
            (
                str(value.get("board", "")).casefold(),
                str(value.get("subject", "")).casefold(),
            )
            for value in layout_payload.get("profiles", [])
        }
        expected_layout = (
            _layout_board(str(family.get("board", ""))),
            str(family.get("subject", "")).casefold(),
        )
        if expected_layout not in layout_keys:
            issue("layout-profile", "reference-derived layout profile is missing")

        thresholds = self._json(self.resources / "fidelity-thresholds.json") or {}
        threshold_keys = set(thresholds.get("families", {}))
        expected_thresholds = {
            _threshold_key(family, paper) for paper in declared
        }
        if not expected_thresholds or not expected_thresholds <= threshold_keys:
            issue("fidelity-threshold", "per-paper fidelity thresholds are missing")

        if not paper_ids or paper_ids != declared or not family.get("advertised"):
            issue("matrix", "family cannot be discovered as a complete matrix case")

        if self.run_preview:
            preview_problem = self._exercise_preview(family, declared, output_map)
            if preview_problem:
                issue("backend-dispatch", preview_problem)

        bundle_script = self.root / "macOS" / "scripts" / "build_backend.sh"
        if not bundle_script.is_file() or not python_root.is_dir():
            issue("packaging", "registry-driven bundle inputs are incomplete")

        registry_metadata = (catalog or {}).get("generator_registry", {})
        if (
            not catalog_match
            or registry_metadata.get("schema_version") != registry.get("schema_version")
            or registry_metadata.get("path") != "generator-registry.json"
        ):
            issue("swift-decoding", "catalog metadata cannot drive Swift decoding")

        return MigrationReport(
            str(family.get("id", "unknown")),
            family_path,
            tuple(issues),
        )

    def _exercise_preview(
        self,
        family: dict[str, Any],
        papers: list[str],
        output_map: dict[str, Any],
    ) -> str | None:
        if not papers:
            return "deterministic preview has no declared paper"
        python_root = self.resources / str(family.get("python_path", ""))
        syllabus = self.resources / str(family.get("syllabus_path", ""))
        module_name, separator, function_name = str(
            family.get("entry_point", "")
        ).partition(":")
        if (
            not separator
            or not python_root.is_dir()
            or not syllabus.is_file()
        ):
            return "deterministic preview inputs are incomplete"
        try:
            if str(python_root) not in sys.path:
                sys.path.insert(0, str(python_root))
            function = getattr(importlib.import_module(module_name), function_name)
            with tempfile.TemporaryDirectory(prefix="papercreator-migration-") as temporary:
                result = function(
                    paper=papers[0],
                    syllabus_path=syllabus,
                    output_dir=Path(temporary),
                    seed=847_261,
                    model="migration-preview",
                    ollama_url="http://127.0.0.1:11434",
                    dry_run=True,
                )
                expected = set(output_map.get(papers[0], []))
                if not isinstance(result, dict) or set(result) != expected:
                    return "deterministic preview output roles disagree with the manifest"
                if any(not Path(path).is_file() for path in result.values()):
                    return "deterministic preview reported a missing artifact"
        except Exception as error:
            return f"deterministic preview failed: {error}"
        return None

    @staticmethod
    def _json(path: Path) -> Any | None:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None


def _layout_board(board: str) -> str:
    aliases = {
        "aqa": "aqa",
        "ocr": "ocr",
        "pearson-edexcel": "pearson-edexcel",
    }
    return aliases.get(board, board.replace("-", " ")).casefold()


def _threshold_key(family: dict[str, Any], paper: str) -> str:
    board = {
        "pearson-edexcel": "edexcel",
    }.get(str(family.get("board", "")), str(family.get("board", "")))
    subject = {
        "economics-a-2015": "economics",
    }.get(str(family.get("subject", "")), str(family.get("subject", "")))
    return f"{board}-{subject}-paper-{paper}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate generator onboarding")
    parser.add_argument("family", nargs="?", type=Path)
    parser.add_argument("--all", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    validator = MigrationValidator()
    reports = validator.validate_all() if args.all else (validator.validate(args.family),)
    for report in reports:
        state = "passed" if report.passed else "failed"
        print(f"{report.family_id}: {state}")
        for item in report.issues:
            print(f"  {item.code}: {item.message}")
    return 0 if all(report.passed for report in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
