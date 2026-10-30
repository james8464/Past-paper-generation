from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = """
from collections.abc import Sequence
from pathlib import Path
from Backend.Core.family_contracts import ArtifactSpec, BuildResult, FamilyAdapter

class Syllabus: pass
class Rule: pass
class Assessment: pass
class Context: pass
class Other: pass

def syllabus(path: Path) -> Syllabus:
    return Syllabus()

def rule(paper: str) -> Rule:
    return Rule()

def build(rule: Rule, syllabus: Syllabus, seed: int | None) -> BuildResult[Assessment, Context]:
    return BuildResult(Assessment(), Context())

def artifacts(assessment: Assessment, context: Context | None, syllabus: Syllabus, paper: str) -> Sequence[ArtifactSpec]:
    return ()

def stem(rule: Rule, paper: str) -> str:
    return paper

adapter = FamilyAdapter[Syllabus, Rule, Assessment, Context](
    id="fixture", subject_label="Fixture", backend_subject="fixture",
    load_message="load", build_message="build", prompt_version="fixture-v1",
    load_syllabus=syllabus, load_rule=rule, build=build,
    artifacts=artifacts, stem=stem,
)
"""


def check(tmp_path, source):
    checker = shutil.which("mypy")
    assert checker is not None, "Install requirements-test.txt; mypy is a required gate"
    path = tmp_path / "adapter_contract.py"
    path.write_text(source)
    return subprocess.run(
        [
            checker,
            "--config-file",
            str(ROOT / "tools/typecheck.ini"),
            "--cache-dir",
            str(tmp_path / "cache"),
            str(path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )


def test_generic_adapter_and_wrapped_context_pass_static_checks(tmp_path):
    result = check(tmp_path, FIXTURE)
    assert result.returncode == 0, result.stdout + result.stderr


def test_legacy_direct_assessment_build_passes_static_checks(tmp_path):
    source = FIXTURE.replace(
        "BuildResult[Assessment, Context]:\n    return BuildResult(Assessment(), Context())",
        "Assessment:\n    return Assessment()",
    )
    result = check(tmp_path, source)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "old,new,hook",
    [
        (
            "def syllabus(path: Path) -> Syllabus:\n    return Syllabus()",
            "def syllabus(path: Path) -> Other:\n    return Other()",
            "load_syllabus",
        ),
        (
            "def rule(paper: str) -> Rule:\n    return Rule()",
            "def rule(paper: str) -> Other:\n    return Other()",
            "load_rule",
        ),
        (
            "BuildResult[Assessment, Context]:\n    return BuildResult(Assessment(), Context())",
            "BuildResult[Other, Context]:\n    return BuildResult(Other(), Context())",
            "build",
        ),
        (
            "def artifacts(assessment: Assessment, context: Context | None",
            "def artifacts(assessment: Assessment, context: Other | None",
            "artifacts",
        ),
        (
            "BuildResult[Assessment, Context]:\n    return BuildResult(Assessment(), Context())",
            "BuildResult[Assessment, Other]:\n    return BuildResult(Assessment(), Other())",
            "build",
        ),
    ],
)
def test_mismatched_family_hook_is_rejected_statically(tmp_path, old, new, hook):
    assert old in FIXTURE
    result = check(tmp_path, FIXTURE.replace(old, new))
    assert result.returncode == 1, result.stdout + result.stderr
    assert result.stdout.count("error:") == 1, result.stdout
    assert "[arg-type]" in result.stdout and f'Argument "{hook}"' in result.stdout


def test_legacy_module_reexports_the_same_runtime_contracts():
    from Backend.Core import family_adapter, family_contracts

    for name in ("ArtifactSpec", "BuildResult", "FamilyAdapter", "ProgressCallback"):
        assert getattr(family_adapter, name) is getattr(family_contracts, name)


def test_build_result_serialization_and_nullable_context_are_unchanged():
    from dataclasses import FrozenInstanceError, asdict

    from Backend.Core.family_adapter import BuildResult

    assessment = {"paper_id": "fixture", "seed": -123}
    result = BuildResult(assessment)
    assert asdict(result) == {"assessment": assessment, "context": None}
    with pytest.raises(FrozenInstanceError):
        result.context = "changed"
    contextual = BuildResult(assessment, {"source": "fixture"})
    assert asdict(contextual) == {
        "assessment": assessment,
        "context": {"source": "fixture"},
    }
