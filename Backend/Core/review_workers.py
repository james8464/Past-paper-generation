"""Bounded local generation/review jobs, with caller-owned result acceptance."""

from __future__ import annotations

from collections.abc import Callable
from queue import Empty, Queue
from threading import Event, Thread
from typing import cast


def local_generation_workers(client: object) -> int:
    provider = getattr(client, "provider", None)
    if provider not in {"ollama", "apple"}:
        return 1
    workers = getattr(
        client,
        "parallel_generation_workers",
        getattr(client, "parallel_review_workers", 1) if provider == "ollama" else 1,
    )
    if type(workers) is not int or workers not in (1, 2):
        raise ValueError("Local generation supports one or two workers.")
    return workers


def map_reviews[T, R](
    items: list[T],
    review: Callable[[T], R],
    *,
    workers: int,
    progress: Callable[[int, int], None] | None = None,
    on_result: Callable[[int, R], None] | None = None,
) -> list[R]:
    if type(workers) is not int or workers not in (1, 2):
        raise ValueError("Reviews support one or two workers.")
    if workers == 1:
        values = []
        for index, item in enumerate(items):
            values.append(review(item))
            if on_result is not None:
                on_result(index, values[-1])
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

    # Jobs must not write real checkpoints or mutate shared assessment state.
    # on_result runs on the caller, where deferred accepted changes can commit.
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
            if on_result is not None:
                on_result(index, results[index])
            if progress is not None:
                progress(index, len(results))
    finally:
        stopped.set()
    return [results[index] for index in range(len(items))]
