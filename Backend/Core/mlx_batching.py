"""Two-request MLX coalescing, with one model-owning inference thread."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import CancelledError
from contextlib import suppress
from dataclasses import dataclass, field
from queue import Empty, Queue
from threading import BoundedSemaphore, Event, Lock, Thread
from typing import Any, cast

from Backend.Core.events import emit_progress


class BatchUnavailable(ValueError):
    """Use constrained serial decoding for this model or prompt pair."""


@dataclass
class _Pending[T, R]:
    value: T
    done: Event = field(default_factory=Event)
    result: R | BaseException | None = None


class CoalescingRunner[T, R]:
    def __init__(
        self,
        batch: Callable[[list[T], Event], list[R | BaseException]],
        *,
        wait_seconds: float = 0.025,
    ) -> None:
        self._batch = batch
        self._wait_seconds = wait_seconds
        self._pending: Queue[_Pending[T, R]] = Queue(maxsize=2)
        self._slots = BoundedSemaphore(2)
        self._cancelled = Event()
        self._start_lock = Lock()
        self._started = False

    def call(self, value: T) -> R:
        with self._slots:
            if self._cancelled.is_set():
                raise CancelledError("MLX generation was cancelled.")
            pending = _Pending[T, R](value)
            self._pending.put(pending)
            with self._start_lock:
                if not self._started:
                    Thread(
                        target=self._work, name="mlx-inference-owner", daemon=True
                    ).start()
                    self._started = True
            try:
                while not pending.done.wait(0.1):
                    if self._cancelled.is_set():
                        raise CancelledError("MLX generation was cancelled.")
            except BaseException:
                self.close()
                raise
            if self._cancelled.is_set():
                raise CancelledError("MLX generation was cancelled.")
            result = pending.result
        if isinstance(result, BaseException):
            raise result
        return cast(R, result)

    def close(self) -> None:
        self._cancelled.set()
        while True:
            try:
                pending = self._pending.get_nowait()
            except Empty:
                return
            pending.result = CancelledError("MLX generation was cancelled.")
            pending.done.set()

    def _work(self) -> None:
        while not self._cancelled.is_set():
            try:
                first = self._pending.get(timeout=0.1)
            except Empty:
                continue
            jobs = [first]
            with suppress(Empty):
                jobs.append(self._pending.get(timeout=self._wait_seconds))
            try:
                if self._cancelled.is_set():
                    raise CancelledError("MLX generation was cancelled.")
                values = self._batch([job.value for job in jobs], self._cancelled)
                if len(values) != len(jobs):
                    raise ValueError("MLX batch returned the wrong result count.")
            except BaseException as error:
                values = [error] * len(jobs)
            for job, result in zip(jobs, values, strict=True):
                job.result = result
                job.done.set()


def generate_batch(
    model: Any,
    tokenizer: Any,
    prompts: list[str],
    processors: list[Any],
    cancelled: Event,
    *,
    generator_factory: Callable[..., Any] | None = None,
) -> list[str | BaseException]:
    if len(prompts) != 2 or len(processors) != 2:
        raise ValueError("MLX batching requires two independent prompt/decoder pairs.")
    tokens = [
        tokenizer.encode(
            prompt,
            add_special_tokens=(
                tokenizer.bos_token is None
                or not prompt.startswith(tokenizer.bos_token)
            ),
        )
        for prompt in prompts
    ]
    if sum(map(len, tokens)) > 8192:
        raise BatchUnavailable("The combined prompt context requires serial decoding.")
    if cancelled.is_set():
        raise CancelledError("MLX generation was cancelled.")
    if generator_factory is None:
        try:
            from mlx_lm.generate import BatchGenerator
        except ImportError as error:
            raise BatchUnavailable(
                "This MLX runtime requires serial decoding."
            ) from error

        generator_factory = BatchGenerator
    generator = generator_factory(
        model,
        stop_tokens=set(tokenizer.eos_token_ids),
        max_tokens=4096,
        completion_batch_size=2,
        prefill_batch_size=2,
        prefill_step_size=512,
    )
    try:
        uids = generator.insert(
            tokens,
            max_tokens=4096,
            logits_processors=[[processor] for processor in processors],
        )
        if (
            len(uids) != 2
            or any(type(uid) is not int for uid in uids)
            or len(set(uids)) != 2
        ):
            raise ValueError("MLX batch returned invalid sequence identifiers.")
        output: dict[int, list[int]] = {uid: [] for uid in uids}
        finished: dict[int, str | BaseException] = {}
        announced_batch = False
        while True:
            if cancelled.is_set():
                raise CancelledError("MLX generation was cancelled.")
            responses = generator.next()
            if not responses:
                break
            if len(responses) == 2 and not announced_batch:
                emit_progress(
                    "Apple MLX is decoding two tasks together.", stage="provider_batch"
                )
                announced_batch = True
            for response in responses:
                if response.uid not in output or response.uid in finished:
                    raise ValueError(
                        "MLX batch returned an unexpected sequence identifier."
                    )
                if response.finish_reason != "stop":
                    output[response.uid].append(response.token)
                if response.finish_reason is not None:
                    finished[response.uid] = (
                        tokenizer.decode(output[response.uid])
                        if response.finish_reason == "stop"
                        else ValueError("MLX returned incomplete structured output.")
                    )
        if set(finished) != set(uids):
            raise ValueError("MLX batch ended without completing every sequence.")
        return [finished[uid] for uid in uids]
    except ValueError as error:
        if "does not yet support batching" in str(
            error
        ) or "RotatingKVCache with keep tokens is not supported" in str(error):
            raise BatchUnavailable(
                "This model cache requires serial decoding."
            ) from error
        raise
    finally:
        generator.close()
