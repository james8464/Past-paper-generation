"""Bound new request admission, without promising remote cancellation or prices."""

import pytest

from Backend.Core.france import generation_budget as subject
from Backend.Core.generation_requests import GenerationRequest


class Client:
    provider = "deepseek"
    model = "fixture"

    def __init__(self):
        self.calls = 0

    def generate_request(self, request):
        self.calls += 1
        return {"ok": True}


def request(tokens=100):
    return GenerationRequest(
        "fixture", "french_nsi_authoring", {"type": "object"}, output_budget=tokens
    )


def test_twenty_fifth_request_is_refused_before_dispatch():
    client = Client()
    budget = subject.FrenchGenerationBudget(client)
    for _ in range(24):
        assert budget.generate_request(request()) == {"ok": True}
    with pytest.raises(subject.GenerationLimitError):
        budget.generate_request(request())
    assert client.calls == budget.snapshot()["started_requests"] == 24
    assert budget.snapshot()["completed_requests"] == 24
    assert budget.provider == "deepseek"


def test_token_reservation_refuses_before_dispatch():
    client = Client()
    budget = subject.FrenchGenerationBudget(client)
    budget.generate_request(request(subject.MAX_RESERVED_OUTPUT_TOKENS))
    with pytest.raises(subject.GenerationLimitError):
        budget.generate_request(request(1))
    assert client.calls == 1


def test_elapsed_limit_prevents_next_request(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(subject.time, "monotonic", lambda: now[0])
    client = Client()
    budget = subject.FrenchGenerationBudget(client)
    now[0] = subject.MAX_ELAPSED_SECONDS
    with pytest.raises(subject.GenerationLimitError):
        budget.generate_request(request())
    assert client.calls == 0


def test_slow_inflight_result_is_not_accepted(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(subject.time, "monotonic", lambda: now[0])

    class SlowClient(Client):
        def generate_request(self, value):
            result = super().generate_request(value)
            now[0] = subject.MAX_ELAPSED_SECONDS + 1
            return result

    client = SlowClient()
    budget = subject.FrenchGenerationBudget(client)
    assert budget.generate_request(request()) == {"ok": True}
    with pytest.raises(subject.GenerationLimitError):
        budget.check()
    assert budget.snapshot()["started_requests"] == 1
    assert budget.snapshot()["completed_requests"] == 1
    assert client.calls == 1


@pytest.mark.parametrize("error", [RuntimeError, InterruptedError, KeyboardInterrupt])
def test_failed_request_is_reserved_and_not_retried(error):
    class Failed(Client):
        def generate_request(self, value):
            self.calls += 1
            raise error("original")

    client = Failed()
    budget = subject.FrenchGenerationBudget(client)
    with pytest.raises(error, match="original"):
        budget.generate_request(request())
    assert client.calls == 1
    assert budget.snapshot()["started_requests"] == 1
    assert budget.snapshot()["completed_requests"] == 0
    assert budget.snapshot()["reserved_output_tokens"] == 100


def test_late_author_is_retained_but_never_reviewed(tmp_path, monkeypatch):
    from Backend.Core.france import llm_pipeline
    from tests.test_french_llm_pipeline import generate
    from tests.test_french_reviewed_redraft import ReviewedClient

    now = [0.0]
    monkeypatch.setattr(subject.time, "monotonic", lambda: now[0])

    class SlowAuthor(ReviewedClient):
        def generate_request(self, value):
            result = super().generate_request(value)
            now[0] = subject.MAX_ELAPSED_SECONDS + 1
            return result

    saved = []
    original = llm_pipeline.generate
    monkeypatch.setattr(
        llm_pipeline,
        "generate",
        lambda **kwargs: original(**kwargs, record_round=saved.append),
    )
    client = SlowAuthor()
    with pytest.raises(subject.GenerationLimitError):
        generate(tmp_path, client)
    assert len(client.requests) == 1
    assert saved[-1]["state"] == "stopped"
    assert (
        saved[-1]["partial_round"]["returned"]["author_response"]
        == client.author_objects[0]
    )
    assert saved[-1]["exercise_attempts"][0]["accepted_round"] is None
