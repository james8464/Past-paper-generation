"""Run a qualification backend with durable progress and bounded cleanup."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BackendRun:
    return_code: int
    timed_out: bool
    stdout: str
    stderr: str
    peak_backend_rss_bytes: int | None


@contextmanager
def _handle_termination():
    """Route SIGTERM through the same cleanup as a keyboard interrupt."""
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    previous = signal.getsignal(signal.SIGTERM)

    def terminate(signum, _frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, terminate)
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, previous)


def run_backend(
    command: list[str], *, cwd: Path, run_dir: Path, timeout_seconds: float
) -> BackendRun:
    """Stream directly to files; wait4 measures this child, not earlier jobs.

    The memory figure is backend peak resident memory, not Ollama's separate
    server/GPU allocation. A separate process group permits timeout cleanup.
    """
    output_path = run_dir / "events.jsonl"
    error_path = run_dir / "stderr.log"
    peak_rss = None
    timed_out = False
    with (
        output_path.open("w", encoding="utf-8") as output,
        error_path.open("w", encoding="utf-8") as errors,
        _handle_termination(),
    ):
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=output,
                stderr=errors,
                start_new_session=True,
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
            )
        except OSError as error:
            errors.write(str(error))
            return_code = 127
        else:
            deadline = time.monotonic() + timeout_seconds
            try:
                while True:
                    pid, status, usage = os.wait4(process.pid, os.WNOHANG)
                    if pid:
                        process.returncode = os.waitstatus_to_exitcode(status)
                        peak_rss = int(
                            usage.ru_maxrss * (1 if sys.platform == "darwin" else 1024)
                        )
                        with suppress(ProcessLookupError):
                            os.killpg(process.pid, signal.SIGKILL)
                        break
                    if time.monotonic() >= deadline and not timed_out:
                        timed_out = True
                        with suppress(ProcessLookupError):
                            os.killpg(process.pid, signal.SIGKILL)
                    time.sleep(0.05)
            except BaseException:
                # Ctrl-C must not leave a live backend consuming the local model.
                with suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                raise
            return_code = 124 if timed_out else process.returncode
    return BackendRun(
        return_code=return_code,
        timed_out=timed_out,
        stdout=output_path.read_text(encoding="utf-8", errors="replace"),
        stderr=error_path.read_text(encoding="utf-8", errors="replace"),
        peak_backend_rss_bytes=peak_rss,
    )
