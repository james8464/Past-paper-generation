"""Independent answers and prose-only materials retain meaningful evidence."""

from copy import deepcopy

import pymupdf
import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from Backend.Core.france import llm_pdf
from Backend.Core.france import llm_pipeline as subject
from Backend.Core.france.nsi import NSIExercise, authoring_schema
from tests.test_french_llm_pdf import render
from tests.test_french_llm_pipeline import Client, raw_exercise

CODE = "def total(valeurs):\n    return sum(valeurs)"


@pytest.mark.parametrize("answer", ["", " ", "\t\n\r"])
def test_blank_blind_answers_refuse_in_request_and_stored_review(answer):
    exercise = subject.validate_authored_exercise(raw_exercise(), "1")
    review = subject._review(Client(), exercise, 42, [])
    review["blind_solution"]["answers"]["1"] = answer
    with pytest.raises(ValidationError):
        Draft202012Validator(subject._solution_schema(exercise)).validate(
            review["blind_solution"]
        )
    with pytest.raises(ValidationError):
        subject._validate_review(exercise, review)


def test_empty_independent_solution_stops_before_third_review():
    class EmptySolution(Client):
        def generate_request(self, request):
            result = super().generate_request(request)
            if "answers" in result:
                result["answers"]["1"] = "   "
            return result

    client = EmptySolution()
    exercise = subject.validate_authored_exercise(raw_exercise(), "1")
    with pytest.raises(ValidationError):
        subject._review(client, exercise, 42, [])
    assert len(client.requests) == 1


def material_field(raw, field, value):
    material = raw["materials"][0]
    if field == "title":
        material["title"] = value
    elif field == "column":
        material["columns"][0] = value
    else:
        material["rows"][0][0] = value


@pytest.mark.parametrize("field", ["title", "column", "cell"])
@pytest.mark.parametrize("code", [CODE, "```python\n" + CODE + "\n```"])
def test_python_suites_or_fences_refuse_in_prose_only_materials(field, code):
    raw = raw_exercise()
    material_field(raw, field, code)
    with pytest.raises(subject.PythonCodeFormatError, match="document"):
        subject.validate_authored_exercise(raw, "1")


@pytest.mark.parametrize(
    "code",
    [
        "import os\ndef total():\n    return os.listdir('.')",
        "```python\nimport os\n```",
        "def total():\n    return open('secret').read()",
    ],
)
def test_unsafe_material_code_remains_hard_nonretry(code):
    raw = raw_exercise()
    material_field(raw, "cell", code)
    with pytest.raises(ValueError, match="non autorisé") as caught:
        subject.validate_authored_exercise(raw, "1")
    assert not isinstance(caught.value, subject.PythonCodeFormatError)


def test_graph_title_and_labels_are_also_prose_only():
    raw = raw_exercise()
    graph = dict(
        kind="weighted_graph",
        id="graphe",
        title="Petit graphe",
        nodes=["A", "B"],
        edges=[["A", "B", 2]],
        directed=True,
    )
    raw["materials"].append(graph)
    graph["title"] = "```python\n" + CODE + "\n```"
    with pytest.raises(subject.PythonCodeFormatError):
        subject.validate_authored_exercise(raw, "1")
    graph["title"] = "Petit graphe"
    graph["nodes"][0] = "def f():\n    return 1"
    graph["edges"][0][0] = graph["nodes"][0]
    with pytest.raises(subject.PythonCodeFormatError):
        subject.validate_authored_exercise(raw, "1")


def test_material_format_regenerates_once_without_rewriting_the_rejected_draft():
    raw = raw_exercise()
    material_field(raw, "cell", CODE)
    original = deepcopy(raw)

    class Responses:
        def __init__(self):
            self.requests = []

        def generate_request(self, request):
            self.requests.append(request)
            return raw if len(self.requests) == 1 else raw_exercise()

    client = Responses()
    exercise, record = subject._author(
        client, subject.exercise_request("1", 42, []), "1"
    )
    assert len(client.requests) == 2
    assert raw == original == record["rejected"][0]["response"]
    assert exercise.materials[0].rows[0][0] == "Alpha"


def test_earlier_material_format_error_does_not_hide_later_unsafe_material():
    raw = raw_exercise()
    material_field(raw, "column", CODE)
    material_field(raw, "cell", "```python\nimport os\n```")
    with pytest.raises(ValueError, match="non autorisé") as caught:
        subject.validate_authored_exercise(raw, "1")
    assert not isinstance(caught.value, subject.PythonCodeFormatError)


def test_multiline_prose_values_and_historical_model_defaults_are_preserved(tmp_path):
    raw = raw_exercise()
    material_field(raw, "cell", "Première ligne\nDeuxième ligne : 42")
    before = deepcopy(raw)
    source = [subject.validate_authored_exercise(raw, "1")]
    source.extend(
        subject.validate_authored_exercise(raw_exercise(i), i) for i in ("2", "3")
    )
    legacy = NSIExercise.model_validate(before)
    assert source[0].model_dump(mode="json") == legacy.model_dump(mode="json")
    assert raw == before
    assert (
        "pattern" not in authoring_schema()["$defs"]["Credit"]["properties"]["points"]
    )
    path = tmp_path / "ordinary.pdf"
    render(path, source)
    llm_pdf.validate_llm_pdf(path, source, correction=False)
    with pymupdf.open(path) as pdf:
        actual = "\n".join(page.get_text() for page in pdf)
    assert "Première ligne Deuxième ligne : 42" in actual


def test_legacy_table_renderer_reproduces_collapsed_python_indentation(tmp_path):
    # Use the unchanged historical model explicitly to retain the reproduction
    # after V36 authoring admission closes this unsupported surface.
    raw = raw_exercise()
    material_field(raw, "cell", CODE)
    source = [NSIExercise.model_validate(raw)]
    source.extend(NSIExercise.model_validate(raw_exercise(i)) for i in ("2", "3"))
    path = tmp_path / "unsupported-table-code.pdf"
    render(path, source)
    with pymupdf.open(path) as pdf:
        lines = [line for page in pdf for line in page.get_text().splitlines()]
    assert any("return sum(valeurs)" in line for line in lines)
    assert not any(line.startswith("    return sum(valeurs)") for line in lines)
    # The prior compact-content check cannot establish this indentation.
    llm_pdf.validate_llm_pdf(path, source, correction=False)
