from __future__ import annotations

import subprocess
import sys
from threading import Barrier, Event, Lock

import pytest

from Backend.Core.review_workers import map_reviews


def test_reviews_overlap_but_return_in_paper_order():
    barrier = Barrier(2)
    release = Event()
    progress = []

    def review(value):
        barrier.wait(timeout=2)
        if value == 0:
            assert release.wait(timeout=2)
        else:
            release.set()
        return value * 10

    assert map_reviews(
        [0, 1],
        review,
        workers=2,
        progress=lambda index, count: progress.append((index, count)),
    ) == [0, 10]
    assert sorted(index for index, _ in progress) == [0, 1]
    assert [count for _, count in progress] == [1, 2]


def test_failure_does_not_start_the_remaining_queue():
    calls = []
    lock = Lock()

    def review(value):
        with lock:
            calls.append(value)
        raise ValueError("rejected review")

    with pytest.raises(ValueError, match="rejected review"):
        map_reviews(list(range(20)), review, workers=2)
    assert len(calls) <= 2


@pytest.mark.parametrize("workers", [0, 3, True, "2"])
def test_invalid_worker_counts_refuse(workers):
    with pytest.raises(ValueError):
        map_reviews([1], lambda item: item, workers=workers)


def test_cancelled_main_process_does_not_wait_for_network_workers():
    code = """
import signal, time
from threading import Timer
from Backend.Core.review_workers import map_reviews
def cancel(*_): raise KeyboardInterrupt
signal.signal(signal.SIGTERM, cancel)
timer = Timer(0.1, lambda: signal.raise_signal(signal.SIGTERM))
timer.daemon = True
timer.start()
try: map_reviews([1,2], lambda _: time.sleep(30), workers=2)
except KeyboardInterrupt: pass
"""
    subprocess.run([sys.executable, "-c", code], check=True, timeout=3)
