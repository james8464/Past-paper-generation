from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

from Backend.Core.paths import REPO_ROOT


@dataclass(frozen=True)
class ScaffoldRequest:
    subject: str
    board: str
    papers: tuple[str, ...]
    destination: Path = REPO_ROOT / "Resources"

    def __post_init__(self) -> None:
        for name, value in (("subject", self.subject), ("board", self.board)):
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
                raise ValueError(f"{name} must be a lowercase slug")
        if not self.papers or any(not paper.strip() for paper in self.papers):
            raise ValueError("at least one non-empty paper ID is required")


def scaffold_family(request: ScaffoldRequest) -> Path:
    root = request.destination / request.subject / request.board
    if root.exists():
        raise FileExistsError(f"generator family already exists: {root}")

    package = (
        request.subject.replace("-", "") + request.board.replace("-", "") + "gen"
    )
    generator = root / "generator"
    data = generator / "data"
    package_root = generator / package
    tests = generator / "tests"
    for directory in (data, package_root, tests):
        directory.mkdir(parents=True, exist_ok=False)

    capability = {
        "manifest_version": 1,
        "id": f"{request.board}/{request.subject}",
        "board": request.board,
        "subject": request.subject,
        "app_subject": request.subject,
        "app_board": request.board,
        "backend_subject": f"{request.subject.replace('-', '_')}_{request.board.replace('-', '_')}",
        "resource_path": f"{request.subject}/{request.board}",
        "python_path": f"{request.subject}/{request.board}/generator",
        "package": package,
        "entry_point": f"{package}.cli:generate_package",
        "syllabus_path": f"{request.subject}/{request.board}/generator/data/syllabus.json",
        "subject_plugin": request.subject,
        "board_profile": request.board,
        "specification_version": "unconfigured",
        "blueprint_version": "unconfigured",
        "content_mode": "ai-assisted",
        "supported_providers": ["ollama", "openai", "anthropic", "apple"],
        "outputs_by_paper": {
            paper: ["question_paper", "mark_scheme", "assessment_package"]
            for paper in request.papers
        },
        "advertised": False,
        "declared_papers": list(request.papers),
        "papers": [
            {
                "id": paper,
                "title": f"Paper {paper}",
                "detail": "Configure from the authorised specification",
                "qualification": {
                    level: {"state": "not_run", "evidence": []}
                    for level in ("engineering", "visual", "empirical")
                },
                "checks": {},
            }
            for paper in request.papers
        ],
    }
    _write_json(generator / "capability.json", capability)
    _write_json(
        data / "syllabus.json",
        {
            "schema_version": 1,
            "specification_version": "unconfigured",
            "provenance": [],
            "topics": [],
        },
    )
    (generator / "pyproject.toml").write_text(
        "[project]\n"
        f'name = "{package}"\n'
        'version = "0.1.0"\n'
        'requires-python = ">=3.11"\n',
        encoding="utf-8",
    )
    (package_root / "__init__.py").write_text(
        '"""Generated family adapter; not advertised until qualification passes."""\n',
        encoding="utf-8",
    )
    (package_root / "cli.py").write_text(_cli_template(), encoding="utf-8")
    (tests / "test_preview.py").write_text(_test_template(package), encoding="utf-8")
    return root


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _cli_template() -> str:
    return '''from __future__ import annotations

from pathlib import Path
from typing import Any


def generate_package(
    *,
    paper: str,
    syllabus_path: Path,
    output_dir: Path,
    seed: int,
    dry_run: bool,
    **_kwargs: Any,
) -> dict[str, Path]:
    """Fail closed until this family has real contracts and renderers."""

    raise RuntimeError(
        f"Paper {paper} is scaffolded but not qualified for generation."
    )
'''


def _test_template(package: str) -> str:
    return f'''from {package}.cli import generate_package


def test_scaffold_is_fail_closed() -> None:
    assert callable(generate_package)
'''


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scaffold an unadvertised generator family")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--board", required=True)
    parser.add_argument("--papers", required=True)
    parser.add_argument("--destination", type=Path, default=REPO_ROOT / "Resources")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    papers = tuple(value.strip() for value in args.papers.split(",") if value.strip())
    root = scaffold_family(
        ScaffoldRequest(args.subject, args.board, papers, args.destination)
    )
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
