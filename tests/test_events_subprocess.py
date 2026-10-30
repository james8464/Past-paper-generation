"""Model setup owns its CLI child, never the shared Ollama service."""

import io
import json
import os
import signal
import subprocess
import sys
import time

import pytest

from Backend.Core import events


class FakeChild:
    def __init__(self, *, stream_error=False, ignore_term=False):
        self.calls = []
        self.returncode = None
        self.ignore_term = ignore_term
        if stream_error:

            class BrokenStream(io.StringIO):
                def __next__(self):
                    raise RuntimeError("stream failed")

            self.stdout = BrokenStream()
        else:
            self.stdout = io.StringIO("ready\n\nfinished\n")

    def poll(self):
        return self.returncode

    def terminate(self):
        self.calls.append("terminate")
        if not self.ignore_term:
            self.returncode = -15

    def kill(self):
        self.calls.append("kill")
        self.returncode = -9

    def wait(self, timeout=None):
        self.calls.append(("wait", timeout))
        if timeout is None:
            self.returncode = 7
        elif self.returncode is None:
            raise subprocess.TimeoutExpired("owned fixture", timeout)
        return self.returncode


def test_normal_exit_closes_pipe_preserves_status_and_restores_signal(
    monkeypatch, capsys
):
    child = FakeChild()
    monkeypatch.setattr(events.subprocess, "Popen", lambda *a, **k: child)
    previous = signal.getsignal(signal.SIGTERM)
    assert events.run_subprocess_json(["owned", "pull", "fixture"], stage="setup") == 7
    assert child.stdout.closed
    assert "terminate" not in child.calls and "kill" not in child.calls
    assert signal.getsignal(signal.SIGTERM) is previous
    assert [
        json.loads(line)["message"] for line in capsys.readouterr().out.splitlines()
    ] == ["ready", "finished"]


def test_start_failure_restores_handler_without_logging_command_arguments(
    monkeypatch, capsys
):
    def missing(*args, **kwargs):
        raise FileNotFoundError("missing executable")

    monkeypatch.setattr(events.subprocess, "Popen", missing)
    previous = signal.getsignal(signal.SIGTERM)
    assert (
        events.run_subprocess_json(["owned", "PRIVATE_ARGUMENT"], stage="setup") == 127
    )
    assert signal.getsignal(signal.SIGTERM) is previous
    assert "PRIVATE_ARGUMENT" not in capsys.readouterr().out


@pytest.mark.parametrize("ignore_term", [False, True])
def test_stream_exception_stops_and_reaps_only_owned_child(monkeypatch, ignore_term):
    child = FakeChild(stream_error=True, ignore_term=ignore_term)
    monkeypatch.setattr(events.subprocess, "Popen", lambda *a, **k: child)
    previous = signal.getsignal(signal.SIGTERM)
    with pytest.raises(RuntimeError, match="stream failed"):
        events.run_subprocess_json(["owned"], stage="setup")
    assert child.calls[0] == "terminate"
    assert ("kill" in child.calls) == ignore_term
    assert child.stdout.closed and child.poll() is not None
    assert signal.getsignal(signal.SIGTERM) is previous
    waits = [call[1] for call in child.calls if isinstance(call, tuple)]
    assert all(timeout is not None and 0 < timeout <= 0.5 for timeout in waits)
    assert sum(waits) < 2


def test_term_during_spawn_is_not_lost_and_handler_is_restored(monkeypatch):
    child = FakeChild(ignore_term=True)

    def spawn(*args, **kwargs):
        signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
        return child

    monkeypatch.setattr(events.subprocess, "Popen", spawn)
    previous = signal.getsignal(signal.SIGTERM)
    with pytest.raises(SystemExit) as caught:
        events.run_subprocess_json(["owned"], stage="setup")
    assert caught.value.code == 143
    assert "terminate" in child.calls and "kill" in child.calls
    assert child.stdout.closed and signal.getsignal(signal.SIGTERM) is previous


def test_existing_custom_handler_is_restored(monkeypatch):
    child = FakeChild()
    monkeypatch.setattr(events.subprocess, "Popen", lambda *a, **k: child)

    def previous_handler(_signum, _frame):
        raise AssertionError("must not run during the owned child scope")

    original = signal.signal(signal.SIGTERM, previous_handler)
    try:
        assert events.run_subprocess_json(["owned"], stage="setup") == 7
        assert signal.getsignal(signal.SIGTERM) is previous_handler
    finally:
        signal.signal(signal.SIGTERM, original)


def test_repeated_term_during_cleanup_cannot_abandon_the_child(monkeypatch):
    child = FakeChild(stream_error=True, ignore_term=True)
    original_wait = child.wait

    def wait(timeout=None):
        signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
        return original_wait(timeout)

    child.wait = wait
    monkeypatch.setattr(events.subprocess, "Popen", lambda *a, **k: child)
    previous = signal.getsignal(signal.SIGTERM)
    with pytest.raises(RuntimeError, match="stream failed"):
        events.run_subprocess_json(["owned"], stage="setup")
    assert "kill" in child.calls and child.stdout.closed
    assert signal.getsignal(signal.SIGTERM) is previous


def test_real_sigterm_reaps_owned_term_ignoring_child_within_two_seconds():
    child_code = "import os,signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); print(os.getpid(),flush=True); time.sleep(60)"
    parent_code = (
        "from Backend.Core.events import run_subprocess_json; import sys; run_subprocess_json([sys.executable,'-c',"
        + repr(child_code)
        + "],stage='owned-test')"
    )
    parent = subprocess.Popen(
        [sys.executable, "-c", parent_code], stdout=subprocess.PIPE, text=True
    )
    child_pid = None
    try:
        child_pid = int(json.loads(parent.stdout.readline())["message"])
        started = time.monotonic()
        parent.terminate()
        parent.communicate(timeout=2)
        assert time.monotonic() - started < 2
        assert parent.returncode == 143
        with pytest.raises(ProcessLookupError):
            os.kill(child_pid, 0)
        child_pid = None  # Already reaped; never signal a subsequently reused PID.
    finally:
        if parent.poll() is None:
            parent.kill()
            parent.wait(timeout=2)
        if child_pid:
            try:
                os.kill(child_pid, signal.SIGTERM)
                os.kill(child_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if parent.stdout:
            parent.stdout.close()
