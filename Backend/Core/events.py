# Send JSON-line progress events between backend tasks and the macOS app.

from __future__ import annotations

import itertools
import json
import re
import signal
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock
from typing import Any

from Backend.Core.legacy_migration import environment_value

PROTOCOL_VERSION = 2
BACKEND_VERSION = "2.0.0"
_EVENT_IDS = itertools.count(1)
_EMIT_LOCK = RLock()


@dataclass(frozen=True)
class GenerationUpdate:
    stage: str
    message: str
    item_id: str | None = None
    completed_units: int = 0
    total_units: int = 1
    attempt: int = 1

    @property
    def progress(self) -> float:
        return max(
            0.0,
            min(1.0, self.completed_units / max(self.total_units, 1)),
        )


def emit(event_type: str, **payload: Any) -> None:
    # One event owns its ID and the whole JSON line, including newline/flush.
    with _EMIT_LOCK:
        envelope = {
            "protocol": PROTOCOL_VERSION,
            "type": event_type,
            "event_id": next(_EVENT_IDS),
            "timestamp": datetime.now(UTC).isoformat(),
            "job_id": environment_value("KELDIN_JOB_ID", ""),
            **payload,
        }
        print(json.dumps(envelope, ensure_ascii=False), flush=True)


def emit_progress(
    message: str, *, stage: str | None = None, progress: float | None = None
) -> None:
    payload: dict[str, Any] = {"stage": stage or message, "message": message}
    if progress is not None:
        payload["progress"] = max(0.0, min(1.0, progress))
    emit("progress", **payload)


def run_subprocess_json(command: list[str], *, stage: str) -> int:
    """Stream a CLI child and release it before the native shutdown deadline."""
    process: subprocess.Popen[str] | None = None
    cancelled = False
    cleaning_up = False

    def cancel(signum: int, _frame: Any) -> None:
        nonlocal cancelled
        cancelled = True
        # A signal arriving during Popen must not abandon an unregistered child.
        if process is not None and not cleaning_up:
            raise SystemExit(128 + signum)

    previous_handler = signal.signal(signal.SIGTERM, cancel)
    try:
        try:
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
        except OSError as error:
            emit("error", message=f"Could not start the model setup process: {error}")
            return 127
        if cancelled:
            raise SystemExit(128 + signal.SIGTERM)
        assert process.stdout is not None
        for line in process.stdout:
            text = line.strip()
            if text:
                emit_progress(text, stage=stage)
        return process.wait()
    finally:
        cleaning_up = True
        try:
            if process is not None:
                try:
                    if process.poll() is None:
                        # Only this Popen belongs to setup. Never signal a group,
                        # a discovered PID or the shared Ollama service.
                        process.terminate()
                        try:
                            process.wait(timeout=0.35)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=0.35)
                finally:
                    if process.stdout is not None:
                        process.stdout.close()
        finally:
            signal.signal(signal.SIGTERM, previous_handler)


def progress_emitter() -> Callable[[str | GenerationUpdate], None]:
    last_progress = 0.02
    render_progress = {
        "Loading syllabus": 0.04,
        "Building paper blueprint": 0.06,
        "Using built-in draft questions": 0.10,
        "Validating paper": 0.82,
        "Rendering question paper": 0.88,
        "Rendering source booklet": 0.92,
        "Rendering mark scheme": 0.96,
        "Done": 1.0,
    }

    def callback(message: str | GenerationUpdate) -> None:
        nonlocal last_progress
        if isinstance(message, GenerationUpdate):
            progress = 0.08 + message.progress * 0.70
            last_progress = max(last_progress, progress)
            emit(
                "progress",
                stage=message.stage,
                message=message.message,
                item_id=message.item_id,
                completed_units=message.completed_units,
                total_units=message.total_units,
                attempt=message.attempt,
                progress=last_progress,
            )
            return
        progress = render_progress.get(message)
        question_match = re.search(r"Generating question\s+(\d+)/(\d+)", message)
        generated_match = re.search(r"Generated question\s+(\d+)/(\d+)", message)
        review_match = re.search(
            r"(?:Calibrating difficulty|Checking reference demand)\s+(\d+)/(\d+)",
            message,
        )
        if question_match:
            index, total = map(int, question_match.groups())
            progress = 0.08 + ((index - 1) / max(total, 1)) * 0.70
        elif generated_match:
            index, total = map(int, generated_match.groups())
            progress = 0.08 + (index / max(total, 1)) * 0.70
        elif review_match:
            index, total = map(int, review_match.groups())
            if 1 <= index <= total:
                # This message starts item i; only its predecessors are complete.
                progress = 0.78 + ((index - 1) / total) * 0.04
        if progress is not None:
            last_progress = max(last_progress, progress)
        emit_progress(message, progress=last_progress)

    return callback
