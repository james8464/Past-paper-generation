"""Only completely audited malformed display code permits structural regeneration."""

import json
from copy import deepcopy

import pytest

from Backend.Core.france import llm_pipeline as subject
from Backend.Core.generation_diagnostics import GenerationEvidenceError
from tests.test_french_v36_code_format import Client, draft

INDENTED = "    def retirer(self):\n        return self.valeurs.pop(0)\n"
VALID = "class File:\n    def retirer(self):\n        return self.valeurs.pop(0)\n"


def fenced(code):
    return f"```python\n{code}```"


def test_indented_methods_regenerate_entire_exercise_without_dedenting():
    first, second = draft(fenced(INDENTED)), draft(fenced(VALID))
    original = deepcopy(first)
    client = Client(first, second)
    exercise, record = subject._author(
        client, subject.exercise_request("1", 42, []), "1"
    )
    assert len(client.requests) == record["attempts"] == 2
    assert exercise.questions[0].answer == second["questions"][0]["answer"]
    assert first == original
    assert record["rejected"][0]["response"] == original
    assert record["rejected"][0]["response_sha256"] == subject._digest(original)


def test_two_malformed_authors_retain_both_original_responses_and_hashes():
    responses = [draft(fenced(INDENTED)), draft(fenced("    valeur = 2\n"))]
    client = Client(*responses)
    with pytest.raises(GenerationEvidenceError) as caught:
        subject._author(client, subject.exercise_request("1", 42, []), "1")
    assert len(client.requests) == 2
    attempts = caught.value.details["attempts"]
    assert len(attempts) == 2
    for attempt, raw in zip(attempts, responses, strict=True):
        assert json.loads(attempt["raw_response"]) == raw
        assert attempt["response_sha256"] == subject._digest(raw)


@pytest.mark.parametrize("placement", ["same-block", "later-fence", "later-field"])
@pytest.mark.parametrize(
    "unsafe", ["import os", "open('secret')", "objet.__class__", "eval('1')"]
)
def test_malformed_code_cannot_hide_later_unsafe_tokens_or_fields(placement, unsafe):
    raw = draft(fenced(INDENTED))
    if placement == "same-block":
        raw["questions"][0]["answer"] = fenced(INDENTED + "    " + unsafe + "\n")
    elif placement == "later-fence":
        raw["questions"][0]["answer"] += "\n" + fenced(unsafe + "\n")
    else:
        raw["context"] += "\n" + fenced(INDENTED)
        raw["questions"][0]["answer"] = fenced(unsafe + "\n")
    client = Client(raw)
    with pytest.raises(ValueError, match="non autorisé") as caught:
        subject._author(client, subject.exercise_request("1", 42, []), "1")
    assert not isinstance(caught.value, subject.PythonCodeFormatError)
    assert len(client.requests) == 1


def test_strings_and_comments_do_not_become_forbidden_names():
    code = (
        INDENTED
        + '    # import os; eval; __dict__\n    texte = "open eval import os __dict__"\n'
    )
    client = Client(draft(fenced(code)), draft(fenced(VALID)))
    _, record = subject._author(client, subject.exercise_request("1", 42, []), "1")
    assert record["attempts"] == 2


@pytest.mark.parametrize(
    "header",
    [
        "def + __class__",
        "class - __bases__",
        "def\n    __class__",
        "def # unfinished definition\n    __class__",
    ],
)
def test_definition_keyword_does_not_exempt_later_dunder_usage(header):
    client = Client(draft(fenced(f"    {header}\n")))
    with pytest.raises(ValueError, match="non autorisé") as caught:
        subject._author(client, subject.exercise_request("1", 42, []), "1")
    assert not isinstance(caught.value, subject.PythonCodeFormatError)
    assert len(client.requests) == 1


def test_immediate_dunder_method_definition_is_not_a_forbidden_access():
    raw = draft(fenced("    def __init__(self):\n        self.valeurs = []\n"))
    with pytest.raises(subject.PythonCodeFormatError):
        subject.validate_authored_exercise(raw, "1")


@pytest.mark.parametrize(
    "code",
    ['    texte = "unfinished\n', "    valeur = (\n", "    valeur = 1\n  autre = 2\n"],
)
def test_incomplete_tokenisation_is_a_hard_refusal_without_retry(code):
    client = Client(draft(fenced(code)))
    with pytest.raises(ValueError, match="audit") as caught:
        subject._author(client, subject.exercise_request("1", 42, []), "1")
    assert not isinstance(caught.value, subject.PythonCodeFormatError)
    assert len(client.requests) == 1


@pytest.mark.parametrize(
    "failure", [SyntaxError("unrelated"), RuntimeError("unrelated")]
)
def test_unrelated_pipeline_errors_are_not_reclassified_or_retried(
    monkeypatch, failure
):
    def fail(*_args, **_kwargs):
        raise failure

    monkeypatch.setattr(subject, "require_authoring_fields", fail)
    client = Client(draft(fenced(VALID)))
    with pytest.raises(type(failure), match="unrelated"):
        subject._author(client, subject.exercise_request("1", 42, []), "1")
    assert len(client.requests) == 1
