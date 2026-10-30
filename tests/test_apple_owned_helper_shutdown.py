"""An owned system-model helper must stop before the app force-stops its parent."""

import os
import signal
import subprocess
import sys
import time
from contextlib import suppress

import pytest


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX termination contract")
def test_cancel_reaps_term_ignoring_helper_before_native_force_deadline(tmp_path):
    pid_file = tmp_path / "owned-helper.pid"
    child_code = """
import os, signal, sys, time
signal.signal(signal.SIGTERM, signal.SIG_IGN)
with open(sys.argv[1], 'w') as stream:
    stream.write(str(os.getpid()))
while True:
    time.sleep(0.1)
"""
    parent_code = """
import signal, subprocess, sys
from pathlib import Path
from Backend.Core import apple_intelligence as service
original_popen = subprocess.Popen
def launch_owned(_command, **kwargs):
    return original_popen([sys.executable, '-c', sys.argv[2], sys.argv[1]], **kwargs)
def cancel(_signal, _frame):
    raise RuntimeError('controlled cancellation')
service.helper_path = lambda: Path(sys.executable)
service.subprocess.Popen = launch_owned
signal.signal(signal.SIGTERM, cancel)
try:
    service.roundtrip({'request_id': 'owned-cancel-test'})
except RuntimeError:
    pass
"""
    parent = subprocess.Popen(
        [sys.executable, "-c", parent_code, str(pid_file), child_code],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    child_pid = None
    child_reaped = False
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if pid_file.exists() and pid_file.read_text():
                child_pid = int(pid_file.read_text())
                break
            if parent.poll() is not None:
                pytest.fail(f"probe parent exited early: {parent.communicate()!r}")
            time.sleep(0.01)
        assert child_pid is not None, "owned helper did not start"
        parent.terminate()
        try:
            # Native shutdown force-stops the backend after two seconds. Keep
            # half a second of margin rather than competing for that deadline.
            parent.wait(timeout=1.5)
        except subprocess.TimeoutExpired:
            pytest.fail("helper cleanup exceeded the native force-stop deadline")
        assert parent.returncode == 0, parent.communicate()
        with pytest.raises(ProcessLookupError):
            os.kill(child_pid, 0)
        child_reaped = True
    finally:
        if parent.poll() is None:
            parent.kill()
        parent.communicate(timeout=5)
        if child_pid is not None and not child_reaped:
            with suppress(ProcessLookupError):
                os.kill(child_pid, signal.SIGKILL)
