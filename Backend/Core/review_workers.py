"""Bounded parallelism for independent, side-effect-free review jobs."""

from __future__ import annotations

from collections.abc import Callable
from queue import Empty, Queue
from threading import Event, Thread
from typing import cast


def map_reviews[T, R](
    items: list[T],
    review: Callable[[T], R],
    *,
    workers: int,
    progress: Callable[[int, int], None] | None = None,
) -> list[R]:
    if type(workers) is not int or workers not in (1, 2):
        raise ValueError("Reviews support one or two workers.")
    if workers == 1:
        values = []
        for index, item in enumerate(items):
            values.append(review(item))
            if progress is not None:
                progress(index, len(values))
        return values
    if not items:
        return []
    pending: Queue[tuple[int, T]] = Queue()
    finished: Queue[tuple[int, R | None, BaseException | None]] = Queue()
    stopped = Event()
    for index, item in enumerate(items):
        pending.put((index, item))

    def work() -> None:
        while not stopped.is_set():
            try:
                index, item = pending.get_nowait()
            except Empty:
                return
            try:
                value = review(item)
            except BaseException as error:
                stopped.set()
                finished.put((index, None, error))
                return
            finished.put((index, value, None))

    # Jobs must not write checkpoints or mutate shared assessment state.
    # Daemon workers let SIGTERM end the helper without waiting on model sockets.
    for index in range(min(workers, len(items))):
        Thread(target=work, daemon=True, name=f"question-review-{index}").start()
    results: dict[int, R] = {}
    try:
        while len(results) < len(items):
            try:
                index, value, error = finished.get(timeout=0.1)
            except Empty:
                continue
            if error is not None:
                raise error
            results[index] = cast(R, value)
            if progress is not None:
                progress(index, len(results))
    finally:
        stopped.set()
    return [results[index] for index in range(len(items))]
