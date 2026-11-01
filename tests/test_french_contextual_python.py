"""Conditional display clauses are audited in context, never executed or rewritten."""

from copy import deepcopy

import pymupdf
import pytest

from Backend.Core.france import llm_pipeline as subject
from Backend.Core.france.code_layout import code_blocks
from Backend.Core.france.llm_pdf import validate_llm_pdf
from Backend.Core.france.verification import _trace
from tests.test_french_llm_pdf import exercises, render
from tests.test_french_llm_pipeline import generate
from tests.test_french_reviewed_redraft import ReviewedClient
from tests.test_french_v36_code_format import Client, draft

CLAUSES = [
    "elif valeur == 0:\n    return 1\n",
    "else:\n    return 2\n",
    "elif valeur < 0:\n    return -1\nelif valeur == 0:\n    return 0\nelse:\n    return 1\n",
]


def answer(code):
    return (
        "Remplacez la fin du test if présenté dans la question.\n```python\n"
        + code
        + "```"
    )


@pytest.mark.parametrize("code", CLAUSES)
@pytest.mark.parametrize("indent", ["", "    "])
def test_contextual_clause_is_accepted_without_regeneration_or_source_changes(
    code, indent
):
    printed = "".join(indent + line for line in code.splitlines(keepends=True))
    raw = draft(answer(printed))
    original = deepcopy(raw)
    client = Client(raw)
    exercise, record = subject._author(
        client, subject.exercise_request("1", 42, []), "1"
    )
    assert len(client.requests) == record["attempts"] == 1
    assert raw == original
    assert exercise.questions[0].answer == answer(printed)
    assert list(code_blocks(exercise.questions[0].answer)) == [printed.rstrip("\n")]


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
@pytest.mark.parametrize("indent", ["", "    "])
def test_leading_blank_and_comment_lines_preserve_contextual_clause(newline, indent):
    code = "\n# replacement\n# conditional continuation\nelif valeur:\n    return 1\n"
    printed = "".join(
        indent + line if line.strip() else line
        for line in code.splitlines(keepends=True)
    ).replace("\n", newline)
    raw = draft(answer(printed))
    original = deepcopy(raw)
    exercise = subject.validate_authored_exercise(raw, "1")
    assert exercise.questions[0].answer == answer(printed)
    assert raw == original


@pytest.mark.parametrize("prefix", ["# replacement\n", "    # replacement\r\n"])
def test_comment_prefix_cannot_hide_unsafe_conditional_branch(prefix):
    indent = "    " if prefix.startswith(" ") else ""
    code = prefix + indent + "elif valeur:\n" + indent + "    return open('secret')\n"
    client = Client(draft(answer(code)))
    with pytest.raises(ValueError, match="non autorisé") as caught:
        subject._author(client, subject.exercise_request("1", 42, []), "1")
    assert not isinstance(caught.value, subject.PythonCodeFormatError)
    assert len(client.requests) == 1


@pytest.mark.parametrize(
    "prefix", ["valeur = 1\n# replacement\n", "# replacement\nvaleur = 1\n"]
)
def test_comment_detection_does_not_admit_executable_prefix(prefix):
    with pytest.raises(subject.PythonCodeFormatError):
        subject.validate_authored_exercise(draft(answer(prefix + CLAUSES[0])), "1")


@pytest.mark.parametrize(
    "unsafe", ["import os", "open('secret')", "eval('1')", "objet.__class__"]
)
@pytest.mark.parametrize("placement", ["branch", "later-field"])
def test_contextual_clause_cannot_hide_unsafe_code_or_get_a_retry(unsafe, placement):
    code = "    else:\n        " + unsafe + "\n"
    raw = draft(answer(code if placement == "branch" else CLAUSES[0]))
    if placement == "later-field":
        raw["questions"][1]["answer"] = answer(code)
    client = Client(raw)
    with pytest.raises(ValueError, match="non autorisé") as caught:
        subject._author(client, subject.exercise_request("1", 42, []), "1")
    assert not isinstance(caught.value, subject.PythonCodeFormatError)
    assert len(client.requests) == 1


@pytest.mark.parametrize(
    "code",
    [
        "elif open('secret'):\n    return 1\n",
        "else:\n    return 1\nopen('secret')\n",
        "else:\n    if valeur:\n        import os\n",
    ],
)
def test_contextual_conditions_nested_branches_and_disallowed_tails_are_audited(code):
    client = Client(draft(answer(code)))
    with pytest.raises(ValueError, match="non autorisé") as caught:
        subject._author(client, subject.exercise_request("1", 42, []), "1")
    assert not isinstance(caught.value, subject.PythonCodeFormatError)
    assert len(client.requests) == 1


@pytest.mark.parametrize(
    "code",
    [
        "elif valeur == 0\n    return 1\n",
        "else:\n",
        "else:\n    return 1\nelse:\n    return 2\n",
        "    else:\n        return 1\n      autre = 2\n",
        "else:\n    return 1\nautre = 2\n",
        "    def calculer():\n        return 1\n",
    ],
)
def test_contextual_fallback_does_not_repair_unrelated_or_malformed_fragments(code):
    with pytest.raises((subject.PythonCodeFormatError, ValueError)):
        subject.validate_authored_exercise(draft(answer(code)), "1")


def test_unclosed_conditional_fence_still_refuses():
    with pytest.raises(subject.PythonCodeFormatError):
        subject.validate_authored_exercise(draft("```python\n" + CLAUSES[0]), "1")


@pytest.mark.parametrize("code", CLAUSES)
def test_contextual_display_permission_does_not_reach_machine_trace(code):
    with pytest.raises(SyntaxError):
        _trace(code, "valeur")
    assert (
        _trace(
            "valeur = 2\nif valeur < 0:\n    valeur = 0\nelse:\n    valeur = valeur + 1",
            "valeur",
        )
        == 3
    )


@pytest.mark.parametrize("large_print", [False, True])
@pytest.mark.parametrize("correction", [False, True])
def test_pdf_and_raw_answer_preserve_indented_contextual_clause(
    tmp_path, large_print, correction
):
    printed = "    else:\n        return valeur + 1\n"
    source = exercises()
    field = "answer" if correction else "prompt"
    source[0] = source[0].model_copy(
        update={
            "questions": (
                source[0].questions[0].model_copy(update={field: answer(printed)}),
                *source[0].questions[1:],
            )
        }
    )
    original = [exercise.model_dump(mode="json") for exercise in source]
    path = tmp_path / "contextual-clause.pdf"
    render(path, source, large_print=large_print, correction=correction)
    validate_llm_pdf(path, source, large_print=large_print, correction=correction)
    assert [exercise.model_dump(mode="json") for exercise in source] == original
    with pymupdf.open(path) as pdf:
        text = "\n".join(page.get_text() for page in pdf)
    assert "else:" in text and "return valeur + 1" in text
    assert "if False" not in text and "pass" not in text


def test_general_guidance_reaches_initial_author_redraft_and_reviewer(tmp_path):
    client = ReviewedClient()
    generate(tmp_path, client)
    authors = [
        request for request in client.requests if "id" in request.schema["properties"]
    ]
    assert len(authors) == 4 and "NOUVELLE_RÉDACTION" in authors[1].prompt
    for request in authors:
        assert (
            "aucune méthode, contrainte ou gestion de cas hors du domaine demandé"
            in request.prompt
        )
        assert (
            "toute solution correcte respectant les contraintes explicites"
            in request.prompt
        )
        assert "elif/else" in request.prompt and "contexte" in request.prompt
    reviews = client.requests[2::3]
    for request in reviews:
        assert "correct et answer_complete" in request.prompt
        assert "rubric_consistent à false" in request.prompt
        assert (
            "exigence" in request.prompt and "contraintes explicites" in request.prompt
        )
        assert "elif/else" in request.prompt and "contexte" in request.prompt


def test_correct_answer_with_rubric_only_mismatch_remains_blocking(tmp_path):
    class RubricMismatch(ReviewedClient):
        def generate_request(self, request):
            response = super().generate_request(request)
            if "1" in request.schema["properties"]:
                response["1"]["rubric_consistent"] = False
                response["1"]["issues"] = [
                    "Le barème exige une méthode absente de la question."
                ]
            return response

    client = RubricMismatch(refuse_rounds=())
    with pytest.raises(subject.SemanticReviewRefusal) as caught:
        generate(tmp_path, client)
    assert len(client.requests) == 6
    checks = caught.value.details["question_reviews"][0]
    assert checks["failed_flags"] == ["rubric_consistent"]
    assert all(
        review["1"]["correct"] and review["1"]["answer_complete"]
        for review in client.review_objects
    )
