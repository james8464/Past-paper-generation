from __future__ import annotations

import os
import signal
import tempfile
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pymupdf as fitz

from Backend.Core.pdf_accessibility import add_page_structure_tree


class RenderTransactionError(RuntimeError):
    """A document role could not be rendered safely."""


class RenderTimeout(RenderTransactionError):
    """Rendering exceeded its bounded qualification window."""


class InvalidRenderOutput(RenderTransactionError):
    """A renderer returned without producing a readable PDF."""


@dataclass(frozen=True)
class RenderResult:
    path: Path
    pages: int
    elapsed_seconds: float


def render_pdf_atomically(
    destination: Path,
    renderer: Callable[[Path], None],
    *,
    role: str,
    timeout_seconds: float = 30.0,
) -> RenderResult:
    """Render one PDF role under a deadline and promote it atomically."""
    if not role.strip():
        raise ValueError("render role must not be empty")
    if timeout_seconds <= 0:
        raise ValueError("render timeout must be greater than zero")
    if threading.current_thread() is not threading.main_thread():
        raise RenderTransactionError(
            f"{role} must render on the backend main thread so its deadline can be enforced"
        )

    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".tmp",
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    temporary.unlink()
    started = time.monotonic()
    try:
        with _render_deadline(role, timeout_seconds):
            renderer(temporary)
            _readable_page_count(temporary, role)
            add_page_structure_tree(temporary)
        pages = _readable_page_count(temporary, role)
        _sync_file(temporary)
        os.replace(temporary, destination)
        _sync_directory(destination.parent)
        return RenderResult(
            path=destination,
            pages=pages,
            elapsed_seconds=time.monotonic() - started,
        )
    finally:
        temporary.unlink(missing_ok=True)


class _render_deadline:
    def __init__(self, role: str, timeout_seconds: float) -> None:
        self.role = role
        self.timeout_seconds = timeout_seconds
        self._started = 0.0
        self._previous_handler: signal.Handlers | None = None
        self._previous_timer = (0.0, 0.0)

    def __enter__(self) -> None:
        self._started = time.monotonic()
        self._previous_handler = signal.getsignal(signal.SIGALRM)
        self._previous_timer = signal.getitimer(signal.ITIMER_REAL)
        remaining, _interval = self._previous_timer
        deadline = min(self.timeout_seconds, remaining) if remaining > 0 else self.timeout_seconds

        def timed_out(_signum: int, _frame: object) -> None:
            raise RenderTimeout(
                f"{self.role} did not finish rendering within "
                f"{self.timeout_seconds:g} seconds"
            )

        signal.signal(signal.SIGALRM, timed_out)
        signal.setitimer(signal.ITIMER_REAL, deadline)

    def __exit__(self, _type: object, _value: object, _traceback: object) -> None:
        signal.setitimer(signal.ITIMER_REAL, 0)
        if self._previous_handler is not None:
            signal.signal(signal.SIGALRM, self._previous_handler)
        remaining, interval = self._previous_timer
        if remaining > 0:
            elapsed = time.monotonic() - self._started
            signal.setitimer(signal.ITIMER_REAL, max(remaining - elapsed, 1e-6), interval)


def _readable_page_count(path: Path, role: str) -> int:
    if not path.is_file() or path.stat().st_size == 0:
        raise InvalidRenderOutput(f"{role} renderer produced no PDF")
    try:
        with fitz.open(path) as document:
            if not document.is_pdf or document.page_count < 1:
                raise InvalidRenderOutput(
                    f"{role} renderer produced an empty or non-PDF document"
                )
            return document.page_count
    except InvalidRenderOutput:
        raise
    except Exception as error:
        raise InvalidRenderOutput(
            f"{role} renderer produced an unreadable PDF: {error}"
        ) from error


def _sync_file(path: Path) -> None:
    with path.open("rb") as rendered:
        os.fsync(rendered.fileno())


def _sync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
