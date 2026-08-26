from __future__ import annotations

from Backend.Core.response_simulation import ResponseSimulator


def test_response_simulator_produces_monotonic_candidate_evidence() -> None:
    item = {
        "id": "q1",
        "prompt": "Evaluate the policy.",
        "mark_scheme": ["private drafting content"],
        "authoring_context": {
            "observable_mark_points": [
                "defines the policy",
                "develops a causal chain",
                "uses the source",
                "reaches a supported judgement",
            ],
            "misconception_targets": ["assumes correlation proves causation"],
        },
    }

    responses = ResponseSimulator().responses(item)

    assert [response.band for response in responses] == [
        "weak",
        "average",
        "excellent",
    ]
    assert [len(response.demonstrated_mark_points) for response in responses] == [
        1,
        2,
        4,
    ]
    assert responses[0].misconceptions
    assert not responses[-1].misconceptions
    assert all(
        "private drafting content" not in response.text for response in responses
    )


def test_model_simulation_context_excludes_the_draft_mark_scheme() -> None:
    class Client:
        prompt = ""

        def generate_json(self, prompt: str) -> dict[str, object]:
            self.prompt = prompt
            return {
                "responses": [
                    {
                        "band": band,
                        "text": f"{band} response",
                        "demonstrated_mark_points": [],
                        "evidence_ids": [],
                        "misconceptions": [],
                    }
                    for band in ("weak", "average", "excellent")
                ]
            }

    client = Client()
    ResponseSimulator(client).responses(
        {
            "id": "q2",
            "prompt": "Assess the evidence.",
            "mark_scheme": ["secret answer"],
        }
    )

    assert "secret answer" not in client.prompt
