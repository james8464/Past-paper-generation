from __future__ import annotations

import itertools
import json
from queue import Queue
from threading import Event, RLock, Thread, current_thread

from Backend.Core import events


def test_emit_serializes_event_ids_and_complete_json_lines(monkeypatch):
    """Pause a partial write, then deterministically attempt a second event."""
    first_write = Event()
    release_first = Event()
    second_attempt: Queue[str] = Queue()
    errors: Queue[BaseException] = Queue()
    chunks: list[str] = []
    flushes: list[str] = []

    class ObservedLock:
        def __init__(self):
            self.lock = RLock()

        def __enter__(self):
            if current_thread().name == "second-emitter":
                second_attempt.put("lock")
            self.lock.acquire()
            return self

        def __exit__(self, *_args):
            self.lock.release()

    class SlowOutput:
        def write(self, value):
            name = current_thread().name
            if name == "first-emitter" and value != "\n":
                midpoint = len(value) // 2
                chunks.append(value[:midpoint])
                first_write.set()
                if not release_first.wait(timeout=3):
                    raise AssertionError("first output was not released")
                chunks.append(value[midpoint:])
            else:
                chunks.append(value)
                if name == "second-emitter" and value != "\n":
                    second_attempt.put("write")
            return len(value)

        def flush(self):
            flushes.append(current_thread().name)

    def send(message):
        try:
            events.emit_progress(message, stage="checkpoint", progress=0.5)
        except BaseException as error:
            errors.put(error)

    with monkeypatch.context() as patch:
        patch.setattr(events, "_EVENT_IDS", itertools.count(1))
        patch.setattr(events, "_EMIT_LOCK", ObservedLock(), raising=False)
        patch.setattr(events, "environment_value", lambda *_args: "fixture-job")
        patch.setattr("sys.stdout", SlowOutput())
        first = Thread(target=send, args=("Premier résultat",), name="first-emitter")
        second = Thread(target=send, args=("Second result",), name="second-emitter")
        first.start()
        try:
            assert first_write.wait(timeout=3)
            second.start()
            # A protected emitter attempts its lock; an unprotected emitter
            # writes into the first one's half-finished JSON instead. Neither
            # path relies on a sleep or a probabilistic scheduling window.
            assert second_attempt.get(timeout=3) in {"lock", "write"}
        finally:
            release_first.set()
            first.join(timeout=3)
            if second.ident is not None:
                second.join(timeout=3)

    assert not first.is_alive() and not second.is_alive()
    assert errors.empty()
    lines = "".join(chunks).splitlines()
    records = [json.loads(line) for line in lines]
    assert [record["event_id"] for record in records] == [1, 2]
    assert [record["message"] for record in records] == [
        "Premier résultat",
        "Second result",
    ]
    assert all(record["protocol"] == events.PROTOCOL_VERSION for record in records)
    assert all(record["type"] == "progress" for record in records)
    assert all(record["job_id"] == "fixture-job" for record in records)
    assert all(record["stage"] == "checkpoint" for record in records)
    assert all(record["progress"] == 0.5 for record in records)
    assert all(record["timestamp"] for record in records)
    assert flushes == ["first-emitter", "second-emitter"]
