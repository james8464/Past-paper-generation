from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "macOS" / "scripts"


def _executable(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    path.chmod(0o755)


@pytest.fixture
def fingerprint_environment(tmp_path: Path) -> dict[str, str]:
    root = tmp_path / "fixture-repository"
    inputs = (
        "bridge.py",
        "requirements-build.txt",
        "macOS/Keldin/KeldinBackend.entitlements",
        "macOS/scripts/build_backend.sh",
        "Resources/backend-protocol.schema.json",
        "Resources/generator-capability.schema.json",
        "Resources/empirical-calibration.schema.json",
        "Resources/empirical-calibration-policy.json",
        "Resources/reference-demand-profiles.json",
        "Resources/level-of-response-policies.json",
        "Resources/generator-registry.json",
        "Resources/layout-master-runtime.json",
        "Resources/layout-profiles.json",
        "Resources/ollama-model-recommendations.json",
        "Resources/board-profiles/fixture.json",
        "Resources/france/fixture.json",
        "Resources/fixture/generator/module.py",
        "Resources/fixture-syllabus.json",
    )
    for relative in inputs:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")
    registry = root / "Backend/Core/generator_registry.py"
    registry.parent.mkdir(parents=True)
    registry.write_text(
        "from types import SimpleNamespace\n"
        "def generator_capabilities():\n"
        "    return {'fixture': SimpleNamespace(syllabus_path='fixture-syllabus.json')}\n",
        encoding="utf-8",
    )
    (root / "PyInstaller.py").write_text("__version__ = '6.17.0'\n", encoding="utf-8")
    python = tmp_path / "fixture-python"
    # Run the real fingerprint with controlled distribution metadata. No package
    # installation, application packaging or signing occurs in these tests.
    interpreter_stub = (
        "import importlib.metadata, json, os, sys\n"
        "from types import SimpleNamespace\n"
        "def distributions():\n"
        "    if os.environ.get('DISTRIBUTIONS_ERROR') == '1':\n"
        "        raise RuntimeError('distribution metadata unavailable')\n"
        "    return [SimpleNamespace(metadata={'Name': name}, version=version)\n"
        "            for name, version in json.loads(os.environ['DISTRIBUTIONS'])]\n"
        "importlib.metadata.distributions = distributions\n"
        "if sys.argv[1:] == ['--version']:\n"
        "    print('Python fixture')\n"
        "elif len(sys.argv) == 3 and sys.argv[1] == '-c':\n"
        "    exec(sys.argv[2])\n"
        "else:\n"
        "    raise RuntimeError('unexpected interpreter arguments')\n"
    )
    _executable(
        python,
        f'#!/bin/bash\nexec {shlex.quote(sys.executable)} -c {shlex.quote(interpreter_stub)} "$@"\n',
    )
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "ROOT_DIR": str(root),
        "PYTHON": str(python),
        "PYTHONPATH": str(root),
        "DISTRIBUTIONS": json.dumps([["ReportLab", "4.4.0"], ["pydantic", "2.12.0"]]),
    }


def _fingerprint(environment: dict[str, str]) -> subprocess.CompletedProcess[str]:
    source = (SCRIPTS / "build_backend.sh").read_text(encoding="utf-8")
    function = source.split("build_fingerprint() {", 1)[1].split(
        '\nCURRENT_FINGERPRINT="$(build_fingerprint)"', 1
    )[0]
    return subprocess.run(
        [
            "/bin/bash",
            "-c",
            "set -euo pipefail\nbuild_fingerprint() {"
            + function
            + '\nCURRENT_FINGERPRINT="$(build_fingerprint)"\n'
            + 'printf "%s\\n" "$CURRENT_FINGERPRINT"',
        ],
        env=environment,
        cwd=environment["ROOT_DIR"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def test_backend_fingerprint_changes_when_installed_dependency_changes(
    fingerprint_environment: dict[str, str],
) -> None:
    previous = _fingerprint(fingerprint_environment)
    upgraded = _fingerprint(
        {
            **fingerprint_environment,
            "DISTRIBUTIONS": json.dumps(
                [["ReportLab", "4.5.0"], ["pydantic", "2.12.0"]]
            ),
        }
    )
    assert previous.returncode == upgraded.returncode == 0
    assert previous.stdout != upgraded.stdout


def test_backend_fingerprint_is_stable_across_metadata_enumeration_order(
    fingerprint_environment: dict[str, str],
) -> None:
    first = _fingerprint(fingerprint_environment)
    repeated = _fingerprint(fingerprint_environment)
    reordered = _fingerprint(
        {
            **fingerprint_environment,
            "DISTRIBUTIONS": json.dumps(
                [["pydantic", "2.12.0"], ["ReportLab", "4.4.0"]]
            ),
        }
    )
    assert first.returncode == repeated.returncode == reordered.returncode == 0
    assert first.stdout == repeated.stdout == reordered.stdout


def test_backend_fingerprint_cannot_succeed_without_distribution_metadata(
    fingerprint_environment: dict[str, str],
) -> None:
    result = _fingerprint({**fingerprint_environment, "DISTRIBUTIONS_ERROR": "1"})
    assert result.returncode != 0
    assert "distribution metadata unavailable" in result.stderr


@pytest.mark.parametrize(
    ("build_status", "log_status", "filter_status", "expected_status"),
    [(0, 0, 0, 0), (0, 74, 0, 74), (65, 74, 0, 65), (0, 0, 9, 0)],
)
def test_build_wrapper_preserves_build_failure_and_rejects_log_capture_failure(
    tmp_path: Path,
    build_status: int,
    log_status: int,
    filter_status: int,
    expected_status: int,
) -> None:
    binaries = tmp_path / "bin"
    _executable(
        binaries / "xcodebuild",
        '#!/bin/bash\nprintf "fixture build output\\n"\nexit "$FIXTURE_BUILD_STATUS"\n',
    )
    _executable(
        binaries / "tee",
        '#!/bin/bash\n/usr/bin/tee "$@"\nexit "$FIXTURE_LOG_STATUS"\n',
    )
    _executable(
        binaries / "xcbeautify",
        '#!/bin/bash\n/bin/cat\nexit "$FIXTURE_FILTER_STATUS"\n',
    )
    logs = tmp_path / "logs"
    result = subprocess.run(
        ["/bin/bash", str(SCRIPTS / "xcbuild.sh"), "--label", "fixture", "--", "build"],
        cwd=tmp_path,
        env={
            **os.environ,
            "PATH": str(binaries) + os.pathsep + "/usr/bin:/bin",
            "LOG_DIR": str(logs),
            "CACHE_ROOT": str(tmp_path / "cache"),
            "HOME_PATH": str(tmp_path / "home"),
            "CFFIXED_USER_HOME": str(tmp_path / "home"),
            "TMPDIR": str(tmp_path / "temporary"),
            "FIXTURE_BUILD_STATUS": str(build_status),
            "FIXTURE_LOG_STATUS": str(log_status),
            "FIXTURE_FILTER_STATUS": str(filter_status),
        },
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == expected_status, result.stdout + result.stderr
    if expected_status == 0:
        assert (logs / "build.log").read_text(
            encoding="utf-8"
        ) == "fixture build output\n"
    else:
        assert "xcodebuild succeeded" not in result.stdout
