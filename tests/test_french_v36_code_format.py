"""Obvious Python suites need code formatting; unsafe code never gets a retry."""

from copy import deepcopy

import pytest

from Backend.Core.france import llm_pipeline as subject
from Backend.Core.generation_diagnostics import GenerationEvidenceError
from tests.test_french_llm_pipeline import raw_exercise

BARE = "def total(valeurs):\n    resultat = 0\n    for valeur in valeurs:\n        resultat += valeur\n    return resultat"


@pytest.mark.parametrize("field", ["context", "prompt", "answer", "criterion"])
def test_obvious_bare_python_suite_refuses_in_every_printed_prose_field(field):
    raw = raw_exercise()
    if field == "context":
        raw[field] += "\n" + BARE
    elif field == "criterion":
        raw["questions"][0]["marking"][0][field] = BARE
    else:
        raw["questions"][0][field] = BARE
    with pytest.raises(ValueError, match=r"délimité|format"):
        subject.validate_authored_exercise(raw, "1")


@pytest.mark.parametrize(
    "answer",
    [
        "La fonction total calcule une somme.\n    Cette propriété se démontre par récurrence.",
        "Le mot def introduit une fonction; il ne constitue pas ici un programme.",
        "```python\n" + BARE + "\n```",
    ],
)
def test_ordinary_french_prose_and_explicit_python_blocks_remain_valid(answer):
    raw = raw_exercise()
    raw["questions"][0]["answer"] = answer
    assert subject.validate_authored_exercise(raw, "1").questions[0].answer == answer


class Client:
    def __init__(self, *responses):
        self.responses, self.requests = iter(responses), []

    def generate_request(self, request):
        self.requests.append(request)
        return next(self.responses)


def draft(answer):
    raw = raw_exercise()
    raw["questions"][0]["answer"] = answer
    return raw


def test_missing_fence_permits_one_full_regeneration_without_wrapping_or_mutating():
    first, second = draft(BARE), draft("```python\n" + BARE + "\n```")
    original = deepcopy(first)
    client = Client(first, second)
    exercise, record = subject._author(
        client, subject.exercise_request("1", 42, []), "1"
    )
    assert len(client.requests) == 2
    assert client.requests[1].attempt == 2
    assert first == original
    assert exercise.questions[0].answer == second["questions"][0]["answer"]
    assert record["rejected"][0]["response"] == original
    assert "délimité" in record["rejected"][0]["issue"]


def test_repeated_missing_fences_stop_after_two_responses():
    client = Client(draft(BARE), draft(BARE))
    with pytest.raises(GenerationEvidenceError) as caught:
        subject._author(client, subject.exercise_request("1", 42, []), "1")
    assert len(client.requests) == 2
    assert len(caught.value.details["attempts"]) == 2


@pytest.mark.parametrize(
    "answer",
    [
        "def charger():\n    return open('secret').read()",
        "import os\ndef charger():\n    return os.listdir('.')",
        "```python\nimport os\n```",
    ],
)
def test_unsafe_or_import_code_is_hard_nonretry_not_a_missing_fence_repair(answer):
    client = Client(draft(answer))
    with pytest.raises(ValueError, match="non autorisé"):
        subject._author(client, subject.exercise_request("1", 42, []), "1")
    assert len(client.requests) == 1


def test_safe_missing_fence_does_not_hide_unsafe_code_in_a_later_field():
    raw = draft("```python\nimport os\n```")
    raw["context"] += "\n" + BARE
    client = Client(raw)
    with pytest.raises(ValueError, match="non autorisé"):
        subject._author(client, subject.exercise_request("1", 42, []), "1")
    assert len(client.requests) == 1


def test_bare_class_constructor_is_a_format_error_not_an_unsafe_name_error():
    raw = draft(
        "class Noeud:\n    def __init__(self, valeur):\n        self.valeur = valeur"
    )
    with pytest.raises(subject.PythonCodeFormatError):
        subject.validate_authored_exercise(raw, "1")


@pytest.mark.parametrize(
    "code",
    [
        "for valeur in valeurs:\n    total += valeur",
        "if valeur > 0:\n    total = valeur",
        "while valeur > 0:\n    valeur -= 1",
        "try:\n    valeur = 1\nexcept ValueError:\n    valeur = 0",
        "else:\n    valeur = 0",
    ],
)
def test_other_obvious_multiline_suite_headers_need_fences(code):
    with pytest.raises(subject.PythonCodeFormatError):
        subject.validate_authored_exercise(draft(code), "1")
