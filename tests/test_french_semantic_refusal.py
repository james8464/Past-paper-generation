"""Typed refusals remain distinct from errors during bounded semantic recovery."""

import pytest
from jsonschema.exceptions import ValidationError

from Backend.Core.france import llm_pipeline as subject
from Backend.Core.generation_diagnostics import GenerationEvidenceError
from tests.test_french_llm_pipeline import generate
from tests.test_french_reviewed_redraft import ReviewedClient


class RetainedResponseClient(ReviewedClient):
    def generate_request(self, request):
        response = super().generate_request(request)
        properties = request.schema["properties"]
        if "answers" in properties:
            self.returned_blind = response
        elif "id" not in properties:
            self.returned_review = response
        return response


def test_negative_verdict_is_typed_and_preserves_untruncated_returned_objects(tmp_path):
    client = ReviewedClient(refuse_rounds=(1, 2))
    with pytest.raises(subject.SemanticReviewRefusal) as caught:
        generate(tmp_path, client)
    error = caught.value
    assert isinstance(error, GenerationEvidenceError)
    assert "Le contrôle refuse le brouillon" in str(error)
    assert len(client.requests) == 6
    evidence = error.review_evidence
    assert evidence["blind_response"] == client.blind_objects[1]
    assert evidence["review_response"] == client.review_objects[1]
    for name in ("exercise", "blind_response", "review_response"):
        assert evidence[name + "_sha256"] == subject._digest(evidence[name])
    evidence["review_response"].clear()
    assert error.review_evidence["review_response"] == client.review_objects[1]
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


def test_captured_evidence_does_not_alias_returned_provider_objects(tmp_path):
    client = RetainedResponseClient(refuse_rounds=(1, 2))
    with pytest.raises(subject.SemanticReviewRefusal) as caught:
        generate(tmp_path, client)
    snapshot = caught.value.review_evidence
    client.returned_blind.clear()
    client.returned_review.clear()
    assert caught.value.review_evidence == snapshot


def test_negative_first_question_does_not_hide_a_malformed_later_verdict(tmp_path):
    class MixedReviewClient(ReviewedClient):
        def generate_request(self, request):
            response = super().generate_request(request)
            properties = request.schema["properties"]
            if "id" not in properties and "answers" not in properties:
                assert response["1"]["correct"] is False
                response["2"]["correct"] = "false"
            return response

    client = MixedReviewClient()
    with pytest.raises(ValidationError) as caught:
        generate(tmp_path, client)
    assert not isinstance(caught.value, subject.SemanticReviewRefusal)
    assert len(client.requests) == 3
