"""Executable trace evidence must use the candidate's complete printed program."""

from copy import deepcopy
from pathlib import Path

import pytest

from Backend.Core.france import llm_pipeline as subject
from Backend.Core.france import source_identity
from Backend.Core.france.nsi import NSIExercise
from Backend.Core.france.verification import verify_contract
from tests.test_french_llm_pipeline import Client, generate, raw_exercise

CODE = "x = 2 + 3"


def fence(code=CODE, language="python"):
    return f"```{language}\n{code}\n```"


def exercise():
    raw = raw_exercise()
    raw["questions"][0].update(
        prompt=f"Donner x dans ce programme.\n{fence()}",
        answer="La valeur de x est 5.",
        verification={
            "kind": "python_trace",
            "code": CODE,
            "variable": "x",
            "expected": 5,
        },
    )
    return raw


@pytest.mark.parametrize("location", ["absent", "answer", "marking", "other_question"])
def test_private_or_unrelated_code_cannot_supply_trace_evidence(location):
    raw = exercise()
    raw["questions"][0]["prompt"] = "Donner la valeur de x."
    if location == "answer":
        raw["questions"][0]["answer"] += "\n" + fence()
    elif location == "marking":
        raw["questions"][0]["marking"][0]["criterion"] += "\n" + fence()
    elif location == "other_question":
        raw["questions"][1]["prompt"] += "\n" + fence()
    with pytest.raises(ValueError, match="Vérification générique échouée"):
        subject.validate_authored_exercise(raw, "1")


def test_different_private_program_cannot_prove_wrong_printed_answer():
    raw = exercise()
    raw["questions"][0].update(answer="6")
    raw["questions"][0]["verification"].update(code="x = 2 + 4", expected=6)
    assert verify_contract(raw["questions"][0]["verification"])["passed"]
    with pytest.raises(ValueError, match="Vérification générique échouée"):
        subject.validate_authored_exercise(raw, "1")


@pytest.mark.parametrize("location", ["context", "prompt"])
@pytest.mark.parametrize("language", ["python", ""])
def test_complete_printed_context_or_question_program_preserves_originals(
    location, language
):
    raw = exercise()
    raw["questions"][0]["prompt"] = "Donner la valeur de x."
    target = raw if location == "context" else raw["questions"][0]
    target[location] += "\n" + fence(language=language)
    before = deepcopy(raw)
    result = subject.validate_authored_exercise(raw, "1")
    assert raw == before
    assert result.questions[0].verification == before["questions"][0]["verification"]
    assert CODE in str(result.candidate_view())


def test_multiple_blocks_allow_an_exact_whole_program_without_concatenation():
    raw = exercise()
    raw["questions"][0]["prompt"] += "\n" + fence("y = 9")
    assert subject.validate_authored_exercise(raw, "1")
    raw["questions"][0]["verification"].update(code=CODE + "\ny = 9")
    with pytest.raises(ValueError, match="Vérification générique échouée"):
        subject.validate_authored_exercise(raw, "1")


def test_only_line_endings_and_fence_boundary_newlines_are_normalized():
    raw = exercise()
    code = (
        "# Données conservées\nlabel = 'a b'\nx = 0\nfor i in range(3):\n    x = x + i"
    )
    raw["questions"][0].update(
        prompt="Donner x.\r\n" + fence("\n" + code + "\n").replace("\n", "\r\n"),
        answer="3",
        verification={
            "kind": "python_trace",
            "code": code,
            "variable": "x",
            "expected": 3,
        },
    )
    assert subject.validate_authored_exercise(raw, "1")
    for different in [
        code.replace("    x", "  x"),
        code.replace("Données", "Valeurs"),
        code.replace("'a b'", "'ab'"),
    ]:
        changed = deepcopy(raw)
        changed["questions"][0]["verification"]["code"] = different
        with pytest.raises(ValueError, match="Vérification générique échouée"):
            subject.validate_authored_exercise(changed, "1")


@pytest.mark.parametrize("language", ["text", "sql"])
def test_non_python_fences_do_not_bind_a_python_trace(language):
    raw = exercise()
    raw["questions"][0]["prompt"] = "Donner x.\n" + fence(language=language)
    with pytest.raises(ValueError, match="Vérification générique échouée"):
        subject.validate_authored_exercise(raw, "1")


def test_unclosed_matching_fence_is_not_source_evidence_or_a_format_retry():
    raw = exercise()
    raw["questions"][0]["prompt"] = "Donner x dans ce programme.\n```python\n" + CODE
    with pytest.raises(ValueError, match="Vérification générique échouée"):
        subject.validate_authored_exercise(raw, "1")


def test_matching_source_does_not_waive_unsafe_execution_or_wrong_expected_value():
    for code, expected in [("x = open('owned')", 5), (CODE, 6)]:
        raw = exercise()
        raw["questions"][0]["prompt"] = "Donner x.\n" + fence(code)
        raw["questions"][0]["verification"].update(code=code, expected=expected)
        with pytest.raises(ValueError):
            subject.validate_authored_exercise(raw, "1")


def test_recomputed_evidence_rechecks_source_even_after_prior_valid_admission():
    admitted = subject.validate_authored_exercise(exercise(), "1")
    changed = admitted.model_copy(deep=True)
    changed.questions[0].verification.update(code="x = 6", expected=6)
    checks, _ = subject._verification_evidence([changed])
    assert checks[0]["state"] == "failed"
    assert checks[0]["passed"] is False


def test_source_mismatch_is_not_a_formatting_retry():
    class WrongSource(Client):
        def generate_request(self, request):
            self.requests.append(request)
            raw = exercise()
            raw["questions"][0]["verification"].update(code="x = 6", expected=6)
            return raw

    client = WrongSource()
    with pytest.raises(ValueError, match="Vérification générique échouée"):
        subject._author(client, subject.exercise_request("1", 1, []), "1")
    assert len(client.requests) == 1


def test_changed_implementation_refuses_old_package_without_mutating_evidence(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(subject, "implementation_identity", lambda: "a" * 64)
    package = generate(tmp_path, Client())
    before = deepcopy(package)
    monkeypatch.setattr(subject, "implementation_identity", lambda: "b" * 64)
    with pytest.raises(ValueError):
        subject.validate_package(package)
    assert package == before


def test_implementation_identity_hashes_source_binding_bytes(tmp_path, monkeypatch):
    owned = tmp_path / "Backend" / "Core" / "france" / "llm_pipeline.py"
    owned.parent.mkdir(parents=True)
    production = Path(subject.__file__).read_bytes()
    owned.write_bytes(production)
    monkeypatch.setattr(source_identity, "REPO_ROOT", tmp_path)
    before = source_identity.implementation_identity()
    owned.write_bytes(production + b"\n# Owned identity probe only.\n")
    assert source_identity.implementation_identity() != before
    assert Path(subject.__file__).read_bytes() == production


def test_direct_model_validation_does_not_replace_public_source_admission():
    raw = exercise()
    raw["questions"][0]["prompt"] = "Donner la valeur de x."
    typed = NSIExercise.model_validate(raw)
    checks, _ = subject._verification_evidence([typed])
    assert checks[0]["passed"] is False
