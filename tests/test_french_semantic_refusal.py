"""Typed refusal foundation only; automatic semantic recovery stays disabled."""

import pytest
from jsonschema.exceptions import ValidationError

from Backend.Core.france import llm_pipeline as subject
from Backend.Core.generation_diagnostics import GenerationEvidenceError
from tests.test_french_llm_pipeline import generate
from tests.test_french_reviewed_redraft import ReviewedClient


def test_negative_verdict_is_typed_and_preserves_untruncated_returned_objects(tmp_path):
    client = ReviewedClient()
    with pytest.raises(subject.SemanticReviewRefusal) as caught:
        generate(tmp_path, client)
    error = caught.value
    assert isinstance(error, GenerationEvidenceError)
    assert "Le contrôle refuse le brouillon" in str(error)
    assert len(client.requests) == 3  # No recovery is activated by this foundation.
    evidence = error.review_evidence
    assert evidence["blind_response"] == client.blind_objects[0]
    assert evidence["review_response"] == client.review_objects[0]
    for name in ("exercise", "blind_response", "review_response"):
        assert evidence[name + "_sha256"] == subject._digest(evidence[name])
    evidence["review_response"].clear()
    assert error.review_evidence["review_response"] == client.review_objects[0]
    assert "review_response" not in error.details
    assert not list(tmp_path.rglob("*.pdf"))


@pytest.mark.parametrize(
    "failure,error",
    [
        ("malformed", ValidationError),
        ("transport", RuntimeError),
        ("cancel", KeyboardInterrupt),
        ("unsafe", ValueError),
    ],
)
def test_nonsemantic_failure_is_not_typed_as_recoverable(tmp_path, failure, error):
    with pytest.raises(error) as caught:
        generate(tmp_path, ReviewedClient(failure=failure))
    assert not isinstance(caught.value, subject.SemanticReviewRefusal)
