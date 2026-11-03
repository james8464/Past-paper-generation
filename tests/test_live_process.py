from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
from contextlib import suppress

import pytest


def test_interruption_during_post_spawn_initialization_kills_and_reaps_child(
    tmp_path, monkeypatch
):
    from tools import live_process

    calls = []
    interruption = SystemExit(143)

    class Process:
        pid = 123456789

        def wait(self):
            calls.append("wait")
            return -signal.SIGKILL

    def spawn(*_args, **_kwargs):
        calls.append("spawn")
        return Process()

    def interrupted_clock():
        raise interruption

    monkeypatch.setattr(live_process.subprocess, "Popen", spawn)
    monkeypatch.setattr(live_process.time, "monotonic", interrupted_clock)
    monkeypatch.setattr(
        live_process.os,
        "killpg",
        lambda pid, sent: calls.append(("kill", pid, sent)),
    )
    with pytest.raises(SystemExit) as raised:
        live_process.run_backend(
            ["fake"], cwd=tmp_path, run_dir=tmp_path, timeout_seconds=1
        )
    assert raised.value is interruption
    assert calls == ["spawn", ("kill", Process.pid, signal.SIGKILL), "wait"]


def test_backend_progress_is_written_before_process_finishes(tmp_path):
    from tools.live_process import run_backend

    result = []
    worker = threading.Thread(
        target=lambda: result.append(
            run_backend(
                [
                    sys.executable,
                    "-u",
                    "-c",
                    "import time; print('progress'); time.sleep(1); print('done')",
                ],
                cwd=tmp_path,
                run_dir=tmp_path,
                timeout_seconds=5,
            )
        )
    )
    worker.start()
    deadline = time.monotonic() + 4
    events = tmp_path / "events.jsonl"
    while time.monotonic() < deadline:
        if events.exists() and "progress" in events.read_text():
            break
        time.sleep(0.01)
    assert worker.is_alive(), "progress was buffered until the process exited"
    worker.join(timeout=5)
    assert not worker.is_alive()
    assert result[0].return_code == 0
    assert result[0].stdout == "progress\ndone\n"
    assert result[0].peak_backend_rss_bytes > 0


def _wait_for_started(process, output_path, *, startup_timeout=5):
    try:
        deadline = time.monotonic() + startup_timeout
        while time.monotonic() < deadline:
            if output_path.read_text() == "started\n":
                return process
            if process.poll() is not None:
                raise AssertionError("backend exited before its ready banner")
            time.sleep(0.01)
        raise AssertionError("backend did not emit its ready banner")
    except BaseException:
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        raise


@pytest.mark.parametrize("startup_delay", [0, 0.5])
def test_backend_timeout_keeps_partial_output_and_reaps_process(
    tmp_path, monkeypatch, startup_delay
):
    from tools.live_process import run_backend

    spawn = subprocess.Popen
    children = []

    def spawn_when_ready(*args, **kwargs):
        process = spawn(*args, **kwargs)
        children.append(process)
        return _wait_for_started(process, tmp_path / "events.jsonl")

    monkeypatch.setattr("tools.live_process.subprocess.Popen", spawn_when_ready)
    result = run_backend(
        [
            sys.executable,
            "-u",
            "-c",
            f"import time; time.sleep({startup_delay}); print('started'); time.sleep(60)",
        ],
        cwd=tmp_path,
        run_dir=tmp_path,
        timeout_seconds=0.3,
    )
    assert result.timed_out is True
    assert result.return_code == 124
    assert result.stdout == "started\n"
    assert result.peak_backend_rss_bytes > 0
    assert len(children) == 1
    with pytest.raises(ChildProcessError):
        os.waitpid(children[0].pid, os.WNOHANG)


def test_timeout_fixture_reaps_child_when_readiness_fails(tmp_path):
    output_path = tmp_path / "events.jsonl"
    with output_path.open("w") as output:
        process = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(60)"],
            stdout=output,
            start_new_session=True,
        )
        try:
            with pytest.raises(AssertionError, match="ready banner"):
                _wait_for_started(process, output_path, startup_timeout=0.05)
            with pytest.raises(ChildProcessError):
                os.waitpid(process.pid, os.WNOHANG)
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()


def test_backend_launch_failure_is_recorded(tmp_path):
    from tools.live_process import run_backend

    result = run_backend(
        [str(tmp_path / "missing-backend")],
        cwd=tmp_path,
        run_dir=tmp_path,
        timeout_seconds=1,
    )
    assert result.return_code == 127
    assert result.timed_out is False
    assert "missing-backend" in result.stderr
    assert result.peak_backend_rss_bytes is None


def test_sigterm_of_runner_stops_its_backend(tmp_path):
    marker = tmp_path / "backend-survived"
    backend = f"import os,time; print('ready:' + str(os.getpid()), flush=True); time.sleep(1); open({str(marker)!r}, 'w').write('orphan'); time.sleep(60)"
    script = (
        "from pathlib import Path; from tools.live_process import run_backend; "
        f"run_backend([{sys.executable!r}, '-u', '-c', {backend!r}], "
        f"cwd=Path({str(tmp_path)!r}), run_dir=Path({str(tmp_path)!r}), timeout_seconds=60)"
    )
    runner = subprocess.Popen([sys.executable, "-c", script])
    backend_pid = None
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            path = tmp_path / "events.jsonl"
            if path.exists() and "ready" in path.read_text():
                backend_pid = int(path.read_text().strip().split(":")[1])
                break
            time.sleep(0.01)
        else:
            raise AssertionError("backend did not start")
        runner.send_signal(signal.SIGTERM)
        runner.wait(timeout=3)
        time.sleep(1.2)
        assert not marker.exists(), (
            "backend outlived the terminated qualification runner"
        )
    finally:
        if backend_pid is not None:
            with suppress(ProcessLookupError):
                os.kill(backend_pid, signal.SIGKILL)
        if runner.poll() is None:
            runner.kill()
            runner.wait()


def test_exited_backend_does_not_leave_children_running(tmp_path):
    from tools.live_process import run_backend

    marker = tmp_path / "child-survived"
    child = f"import time; time.sleep(1); open({str(marker)!r}, 'w').write('orphan')"
    parent = f"import subprocess,sys; subprocess.Popen([sys.executable, '-c', {child!r}]); print('done')"
    result = run_backend(
        [sys.executable, "-u", "-c", parent],
        cwd=tmp_path,
        run_dir=tmp_path,
        timeout_seconds=5,
    )
    assert result.return_code == 0
    time.sleep(1.2)
    assert not marker.exists(), "an owned backend descendant escaped cleanup"
