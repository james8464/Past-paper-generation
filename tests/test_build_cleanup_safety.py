from __future__ import annotations

import json
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILD_ROOTS = ("DerivedData", "logs", "cache", "tmp", "home")


def _fake_executable(path: Path, calls: Path, kind: str) -> None:
    program = (
        "import json,sys; "
        f"handle=open({str(calls)!r}, 'a', encoding='utf-8'); "
        f"handle.write(json.dumps({{'kind': {kind!r}, 'arguments': sys.argv[1:]}}) + '\\n'); "
        "handle.close()"
    )
    path.write_text(
        f"#!/bin/bash\nexec {shlex.quote(sys.executable)} -c "
        f'{shlex.quote(program)} "$@"\n',
        encoding="utf-8",
    )
    path.chmod(0o700)


def _harness(tmp_path: Path, *, fallback: bool = False):
    macos = tmp_path / "checkout/macOS"
    scripts = macos / "scripts"
    scripts.mkdir(parents=True)
    binaries = tmp_path / "fake-bin"
    binaries.mkdir()
    calls = tmp_path / "fake-calls.jsonl"
    # Only these inert/read-only utilities and fixture mkdir are discoverable.
    # Neither the user's trash utility nor real osascript can enter this PATH.
    for name, real in {
        "bash": "/bin/bash",
        "dirname": "/usr/bin/dirname",
        "basename": "/usr/bin/basename",
        "tr": "/usr/bin/tr",
        "mkdir": "/bin/mkdir",
        "readlink": "/usr/bin/readlink",
        "realpath": "/usr/bin/realpath",
    }.items():
        if Path(real).exists():
            (binaries / name).symlink_to(real)
    _fake_executable(binaries / "osascript", calls, "osascript")
    if not fallback:
        _fake_executable(binaries / "trash", calls, "trash")
    for name in ("clean.sh", "move_to_trash.sh", "resolve_agent_name.sh"):
        source = (ROOT / "macOS/scripts" / name).read_text(encoding="utf-8")
        # Redirect the current hardcoded absolute command IN THE COPY ONLY.
        # This prevents the RED fallback case from ever reaching Finder.
        source = source.replace(
            "/usr/bin/osascript", shlex.quote(str(binaries / "osascript"))
        )
        target = scripts / name
        target.write_text(source, encoding="utf-8")
        target.chmod(0o700)
    return macos, calls, {"PATH": str(binaries)}


def _calls(path: Path):
    return (
        [json.loads(line) for line in path.read_text().splitlines()]
        if path.exists()
        else []
    )


def _run(macos: Path, environment: dict[str, str], *arguments: str, cwd=None):
    return subprocess.run(
        ["/bin/bash", str(macos / "scripts/clean.sh"), *arguments],
        cwd=cwd or macos,
        env=environment,
        capture_output=True,
        text=True,
        timeout=5,
    )


def _owned_directories(macos: Path, agent="worker"):
    for name in BUILD_ROOTS:
        (macos / "build" / name / agent).mkdir(parents=True)


@pytest.mark.parametrize("from_resolver", [False, True])
def test_cleanup_refuses_agent_traversal_before_any_trash_call(tmp_path, from_resolver):
    macos, calls, environment = _harness(tmp_path)
    _owned_directories(macos)
    sentinel = macos.parent / "preserve.txt"
    sentinel.write_text("retained checkout")
    if from_resolver:
        current = macos / "agents/current_name.txt"
        current.parent.mkdir()
        current.write_text("../../..\n")
    else:
        environment["AGENT_NAME"] = "../../.."
    result = _run(macos, environment)
    assert result.returncode != 0
    assert _calls(calls) == []
    assert sentinel.read_text() == "retained checkout"


def test_cleanup_refuses_unexpected_working_directory(tmp_path):
    macos, calls, environment = _harness(tmp_path)
    foreign = tmp_path / "unrelated"
    _owned_directories(foreign)
    environment["AGENT_NAME"] = "worker"
    result = _run(macos, environment, cwd=foreign)
    assert result.returncode != 0
    assert _calls(calls) == []


@pytest.mark.parametrize("symlink_at", ["build", "ancestor", "agent"])
def test_cleanup_refuses_symlinked_build_ownership(tmp_path, symlink_at):
    macos, calls, environment = _harness(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "preserve.txt"
    sentinel.write_text("outside scope")
    if symlink_at == "build":
        (macos / "build").symlink_to(outside, target_is_directory=True)
        _owned_directories(macos)
    else:
        (macos / "build").mkdir()
        if symlink_at == "ancestor":
            (macos / "build/DerivedData").symlink_to(outside, target_is_directory=True)
            _owned_directories(macos)
        else:
            (macos / "build/DerivedData").mkdir()
            (macos / "build/DerivedData/worker").symlink_to(
                outside, target_is_directory=True
            )
            for name in BUILD_ROOTS[1:]:
                (macos / "build" / name / "worker").mkdir(parents=True)
    environment["AGENT_NAME"] = "worker"
    result = _run(macos, environment)
    assert result.returncode != 0
    assert _calls(calls) == []
    assert sentinel.read_text() == "outside scope"


@pytest.mark.parametrize("all_agents", [False, True])
def test_valid_cleanup_passes_only_absolute_owned_targets(tmp_path, all_agents):
    macos, calls, environment = _harness(tmp_path)
    _owned_directories(macos)
    environment["AGENT_NAME"] = "worker"
    result = _run(macos, environment, *(["--all"] if all_agents else []))
    assert result.returncode == 0, result.stderr
    expected = [str(macos / "build" / name) for name in BUILD_ROOTS]
    if not all_agents:
        expected = [str(Path(path) / "worker") for path in expected]
    assert _calls(calls) == [{"kind": "trash", "arguments": expected}]
    assert all(Path(path).exists() for path in expected)


@pytest.mark.parametrize(
    "filename", ["plain file.txt", 'a "quote".txt', "O'Brien; $(not-run).txt"]
)
def test_finder_fallback_uses_fixed_script_and_absolute_argv_not_interpolation(
    tmp_path, filename
):
    macos, calls, environment = _harness(tmp_path, fallback=True)
    directory = macos / "build/DerivedData/worker"
    directory.mkdir(parents=True)
    target = directory / filename
    target.write_text("retained fixture")
    result = subprocess.run(
        ["/bin/bash", str(macos / "scripts/move_to_trash.sh"), str(target)],
        cwd=macos,
        env=environment,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr
    (recorded,) = _calls(calls)
    assert recorded["kind"] == "osascript"
    arguments = recorded["arguments"]
    assert arguments[:1] == ["-e"]
    assert "on run" in arguments[1] and "argv" in arguments[1]
    assert str(target) not in arguments[1]
    assert arguments[2:] == ["--", str(target)]
    assert target.read_text() == "retained fixture"
