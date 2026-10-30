"""Display scope declarations do not grant executable verification capabilities."""

import pytest

from Backend.Core.france import llm_pipeline as subject
from tests.test_french_llm_pipeline import raw_exercise

SCOPED_PROGRAMS = (
    "compteur = 0\ndef incrementer():\n    global compteur\n    compteur += 1\n",
    "def compter():\n    total = 0\n    def ajouter():\n        nonlocal total\n        total += 1\n    ajouter()\n    return total\n",
)


@pytest.mark.parametrize("code", SCOPED_PROGRAMS)
def test_harmless_display_scope_is_admitted_without_execution(code, monkeypatch):
    def no_execution(_contract):
        pytest.fail("Human display text must not invoke executable verification")

    monkeypatch.setattr(subject, "verify_contract", no_execution)
    raw = raw_exercise()
    raw["questions"][0]["answer"] = f"```python\n{code}```"
    exercise = subject.validate_authored_exercise(raw, "1")
    assert exercise.questions[0].verification == {"kind": "human"}


@pytest.mark.parametrize("code", SCOPED_PROGRAMS)
def test_harmless_unformatted_scope_is_a_format_error(code):
    raw = raw_exercise()
    raw["questions"][0]["answer"] = code
    with pytest.raises(subject.PythonCodeFormatError):
        subject.validate_authored_exercise(raw, "1")


@pytest.mark.parametrize(
    "declaration", ["global os", "global open", "nonlocal __builtins__"]
)
@pytest.mark.parametrize("fenced", [True, False])
def test_scope_declarations_cannot_hide_forbidden_names(declaration, fenced):
    code = f"def exemple():\n    {declaration}\n    pass\n"
    raw = raw_exercise()
    raw["questions"][0]["answer"] = f"```python\n{code}```" if fenced else code
    with pytest.raises(ValueError, match="non autorisé") as failure:
        subject.validate_authored_exercise(raw, "1")
    assert not isinstance(failure.value, subject.PythonCodeFormatError)


@pytest.mark.parametrize(
    "code",
    [
        "import os\n",
        "open('secret')\n",
        "eval('1')\n",
        "objet.__class__\n",
        "def exemple():\n    global compteur\n    os.system('commande')\n",
    ],
)
def test_display_still_refuses_import_io_dynamic_and_reflective_access(code):
    raw = raw_exercise()
    raw["questions"][0]["answer"] = f"```python\n{code}```"
    with pytest.raises(ValueError, match="non autorisé"):
        subject.validate_authored_exercise(raw, "1")


@pytest.mark.parametrize(
    "code",
    [
        *SCOPED_PROGRAMS,
        "global compteur\ncompteur = 0\n",
        "nonlocal total\ntotal = 0\n",
    ],
)
def test_scope_declarations_stay_unsupported_in_executable_contracts(code):
    raw = raw_exercise()
    raw["questions"][0]["verification"] = {
        "kind": "python_trace",
        "code": code,
        "variable": "compteur",
        "expected": 0,
    }
    with pytest.raises(ValueError, match="Vérification générique échouée"):
        subject.validate_authored_exercise(raw, "1")
