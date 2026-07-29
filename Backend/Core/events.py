from __future__ import annotations

import json
import itertools
import os
import re
import subprocess
from datetime import datetime, timezone
from typing import Any, Callable


PROTOCOL_VERSION = 2
BACKEND_VERSION = "2.0.0"
_EVENT_IDS = itertools.count(1)


def emit(event_type: str, **payload: Any) -> None:
    envelope = {
        "protocol": PROTOCOL_VERSION,
        "type": event_type,
        "event_id": next(_EVENT_IDS),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "job_id": os.environ.get("PAPER_CREATOR_JOB_ID", ""),
        **payload,
    }
    print(json.dumps(envelope, ensure_ascii=False), flush=True)


def emit_progress(message: str, *, stage: str | None = None, progress: float | None = None) -> None:
    payload: dict[str, Any] = {"stage": stage or message, "message": message}
    if progress is not None:
        payload["progress"] = max(0.0, min(1.0, progress))
    emit("progress", **payload)


def run_subprocess_json(command: list[str], *, stage: str) -> int:
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    except OSError as error:
        emit("error", message=f"Could not start {' '.join(command)}: {error}")
        return 127
    assert process.stdout is not None
    for line in process.stdout:
        text = line.strip()
        if text:
            emit_progress(text, stage=stage)
    return process.wait()


def progress_emitter() -> Callable[[str], None]:
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

    def callback(message: str) -> None:
        nonlocal last_progress
        progress = render_progress.get(message)
        question_match = re.search(r"Generating question\s+(\d+)/(\d+)", message)
        generated_match = re.search(r"Generated question\s+(\d+)/(\d+)", message)
        if question_match:
            index, total = map(int, question_match.groups())
            progress = 0.08 + ((index - 1) / max(total, 1)) * 0.70
        elif generated_match:
            index, total = map(int, generated_match.groups())
            progress = 0.08 + (index / max(total, 1)) * 0.70
        if progress is None:
            progress = last_progress
        else:
            last_progress = progress
        emit_progress(message, progress=progress)

    return callback
