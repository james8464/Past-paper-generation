from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
from contextlib import suppress


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


def test_backend_timeout_keeps_partial_output_and_reaps_process(tmp_path):
    from tools.live_process import run_backend

    result = run_backend(
        [sys.executable, "-u", "-c", "import time; print('started'); time.sleep(60)"],
        cwd=tmp_path,
        run_dir=tmp_path,
        timeout_seconds=0.3,
    )
    assert result.timed_out is True
    assert result.return_code == 124
    assert result.stdout == "started\n"
    assert result.peak_backend_rss_bytes > 0


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
