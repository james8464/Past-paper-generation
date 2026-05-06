from __future__ import annotations

import re
import shutil
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, TextIO

PROCESS_STEPS = (
    "Loading syllabus",
    "Using seed",
    "Building paper blueprint",
    "Generating questions with Ollama model",
    "Using built-in draft questions",
    "Validating paper",
    "Rendering question paper",
    "Rendering source booklet",
    "Rendering mark scheme",
    "Done",
)


@dataclass(frozen=True)
class ProgressSnapshot:
    current_stage: str
    seed: str
    question_current: int
    question_total: int
    questions_done: int
    completed_steps: int
    total_steps: int
    recent: tuple[str, ...]
    elapsed_seconds: float


@dataclass
class ProgressState:
    current_stage: str = "Starting"
    seed: str = ""
    question_current: int = 0
    question_total: int = 0
    questions_done: int = 0
    started_at: float = field(default_factory=time.monotonic)
    recent: deque[str] = field(default_factory=lambda: deque(maxlen=7))
    completed_step_keys: set[str] = field(default_factory=set)

    def update(self, message: str) -> None:
        self.current_stage = message
        self.recent.append(message)
        if seed_match := re.search(r"\bUsing seed (\d+)\b", message):
            self.seed = seed_match.group(1)
        if question_match := re.search(r"\bGenerating question (\d+)/(\d+):", message):
            self.question_current = int(question_match.group(1))
            self.question_total = int(question_match.group(2))
        if question_match := re.search(r"\bGenerated question (\d+)/(\d+):", message):
            self.questions_done = max(self.questions_done, int(question_match.group(1)))
            self.question_total = int(question_match.group(2))
        for step in PROCESS_STEPS:
            if message.startswith(step):
                self.completed_step_keys.add(step)
                break

    def snapshot(self) -> ProgressSnapshot:
        return ProgressSnapshot(
            current_stage=self.current_stage,
            seed=self.seed,
            question_current=self.question_current,
            question_total=self.question_total,
            questions_done=self.questions_done,
            completed_steps=len(self.completed_step_keys),
            total_steps=len(PROCESS_STEPS),
            recent=tuple(self.recent),
            elapsed_seconds=time.monotonic() - self.started_at,
        )


class PlainProgressReporter:
    def __init__(self, stream: TextIO | None = None) -> None:
        self.stream = stream or sys.stdout

    def __enter__(self) -> Callable[[str], None]:
        return self.update

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stream.flush()

    def update(self, message: str) -> None:
        print(f"[progress] {message}", file=self.stream, flush=True)


class TerminalProgressReporter:
    def __init__(self, stream: TextIO | None = None, fps: int = 10) -> None:
        self.stream = stream or sys.stdout
        self.fps = max(1, fps)
        self.state = ProgressState()
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._frames = ("|", "/", "-", "\\")
        self._frame_index = 0

    def __enter__(self) -> Callable[[str], None]:
        self.start()
        return self.update

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

    def start(self) -> None:
        self.stream.write("\x1b[?25l")
        self.stream.flush()
        self._thread = threading.Thread(target=self._render_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)
        self.render_once(final=True)
        self.stream.write("\x1b[?25h\n")
        self.stream.flush()

    def update(self, message: str) -> None:
        with self._lock:
            self.state.update(message)

    def render_once(self, final: bool = False) -> None:
        with self._lock:
            snapshot = self.state.snapshot()
        self.stream.write("\x1b[H\x1b[J")
        self.stream.write(self._render(snapshot, final=final))
        self.stream.flush()

    def _render_loop(self) -> None:
        interval = 1 / self.fps
        while not self._stop.wait(interval):
            self.render_once()

    def _render(self, snapshot: ProgressSnapshot, final: bool = False) -> str:
        width = max(72, min(shutil.get_terminal_size((96, 24)).columns, 120))
        spinner = "done" if final else self._next_spinner()
        progress = _progress_bar(snapshot.questions_done, snapshot.question_total, width=28)
        elapsed = _format_elapsed(snapshot.elapsed_seconds)
        lines = [
            "A-Level Economics Paper Generator".ljust(width),
            f"{spinner}  FPS {self.fps}   Elapsed {elapsed}".ljust(width),
            f"Seed: {snapshot.seed or '-'}".ljust(width),
            f"Steps: {snapshot.completed_steps}/{snapshot.total_steps}  {_progress_bar(snapshot.completed_steps, snapshot.total_steps, width=28)}".ljust(width),
            f"Stage: {snapshot.current_stage}".ljust(width),
            f"Question: {_question_label(snapshot)}  {progress}".ljust(width),
            "-" * width,
            "Recent".ljust(width),
        ]
        for item in snapshot.recent[-6:]:
            lines.append(f"  {item}"[:width].ljust(width))
        return "\n".join(lines) + "\n"

    def _next_spinner(self) -> str:
        value = self._frames[self._frame_index % len(self._frames)]
        self._frame_index += 1
        return value


def progress_reporter(stream: TextIO | None = None, fps: int = 10):
    stream = stream or sys.stdout
    if stream.isatty():
        return TerminalProgressReporter(stream=stream, fps=fps)
    return PlainProgressReporter(stream=stream)


def _question_label(snapshot: ProgressSnapshot) -> str:
    if not snapshot.question_total:
        return "-"
    return f"{snapshot.question_current}/{snapshot.question_total}"


def _progress_bar(done: int, total: int, width: int) -> str:
    if total <= 0:
        return "[" + ("-" * width) + "]"
    filled = round(width * min(done, total) / total)
    return "[" + ("#" * filled) + ("-" * (width - filled)) + f"] {done}/{total}"


def _format_elapsed(seconds: float) -> str:
    whole = int(seconds)
    minutes, secs = divmod(whole, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"
