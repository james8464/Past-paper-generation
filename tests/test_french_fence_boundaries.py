"""Literal fence mentions must not consume actual printed code blocks."""

from copy import deepcopy

import pymupdf
import pytest

from Backend.Core.france import llm_pipeline as subject
from Backend.Core.france.code_fences import CodeFenceError, fenced_parts, printed_text
from Backend.Core.france.code_layout import code_blocks
from Backend.Core.france.llm_pdf import validate_llm_pdf
from Backend.Core.france.print_policy import (
    V36_LEGACY_PRINT_POLICY,
    V36_READABLE_PRINT_POLICY,
)
from Backend.Core.france.rendering import _content_parts, render_assessment
from Backend.Core.render_transaction import render_pdf_atomically
from tests.test_french_llm_pdf import exercises, render
from tests.test_french_llm_pipeline import Client as PackageClient
from tests.test_french_llm_pipeline import generate
from tests.test_french_v36_code_format import Client, draft

CODE = "def calculer(valeur):\n    return valeur + 1\n"
PROMPT = (
    "Recopiez le programme dans un bloc ```python.\n\n```python\n"
    + CODE
    + "```\nExpliquez le résultat."
)


def test_inline_mention_does_not_steal_the_real_opening_fence():
    parts = fenced_parts(PROMPT)
    assert [part.text for part in parts if part.language == "python"] == [CODE]
    assert "```python." in parts[0].text
    assert list(code_blocks(PROMPT)) == [CODE.rstrip("\n")]
    # The retained path demonstrates the original defect without changing it.
    assert [
        text
        for is_code, text in _content_parts(PROMPT, V36_READABLE_PRINT_POLICY)
        if is_code
    ] != [CODE]
    raw = draft("Une réponse en prose.")
    raw["questions"][0]["prompt"] = PROMPT
    original = deepcopy(raw)
    assert subject.validate_authored_exercise(raw, "1").questions[0].prompt == PROMPT
    assert raw == original


def test_multiple_empty_indented_and_crlf_blocks_preserve_source():
    text = "Avant\r\n  ```python\r\n    x = 1\r\n  ```\r\nMilieu\r\n```sql\r\nSELECT 1;\r\n```\r\n```python\r\n```\r\nAprès"
    blocks = [part for part in fenced_parts(text) if part.language is not None]
    assert [(part.language, part.text, part.closed) for part in blocks] == [
        ("python", "    x = 1\r\n", True),
        ("sql", "SELECT 1;\r\n", True),
        ("python", "", True),
    ]
    assert list(code_blocks(text)) == ["    x = 1", "SELECT 1;"]


@pytest.mark.parametrize(
    "label", ["text", "plaintext", "console", "unknown extra-info"]
)
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_unsupported_fence_is_paired_plaintext_without_consuming_supported_blocks(
    label, newline
):
    trace = "étape 1 : [4, 2]\nétape 2 : [2, 4]\n"
    text = (
        f"Avant\n```{label}\n{trace}```\n"
        + "```python\n"
        + CODE
        + "```\n```sql\nSELECT 1;\n```\nAprès"
    ).replace("\n", newline)
    parts = fenced_parts(text)
    assert [
        part.text.replace("\r\n", "\n") for part in parts if part.language is None
    ] == ["Avant\n", trace, "", "", "Après"]
    assert [block.replace("\r\n", "\n") for block in code_blocks(text)] == [
        CODE.rstrip("\n"),
        "SELECT 1;",
    ]
    assert (
        printed_text(text).replace("\r\n", "\n")
        == "Avant\n" + trace + CODE + "SELECT 1;\nAprès"
    )
    assert (False, trace.replace("\n", newline)) in _content_parts(
        text, subject.V36_PRINT_POLICY
    )
    raw = draft(text)
    original = deepcopy(raw)
    assert subject.validate_authored_exercise(raw, "1").questions[0].answer == text
    assert raw == original


def test_supported_language_info_still_receives_python_audit():
    text = "```PyThOn display-info\n" + CODE + "```\n```unknown\ntrace\n```"
    assert list(code_blocks(text)) == [CODE.rstrip("\n")]
    unsafe = draft(text.replace("return valeur + 1", "return open('secret')"))
    with pytest.raises(ValueError, match="non autorisé"):
        subject.validate_authored_exercise(unsafe, "1")


def test_plaintext_does_not_make_a_bare_python_suite_format_safe():
    text = "```text\ndef calculer(valeur):\n    return valeur + 1\n```"
    with pytest.raises(subject.PythonCodeFormatError, match="délimité"):
        subject.validate_authored_exercise(draft(text), "1")


@pytest.mark.parametrize("label", ["python", "sql", "text"])
def test_unclosed_supported_or_unsupported_fence_remains_a_format_refusal(label):
    text = f"```{label}\ncontenu\n"
    with pytest.raises(CodeFenceError):
        fenced_parts(text)
    assert fenced_parts(text, require_closed=False)[1].closed is False
    with pytest.raises(subject.PythonCodeFormatError):
        subject.validate_authored_exercise(draft(text), "1")


@pytest.mark.parametrize(
    "answer",
    [
        "```text\ntrace : 1\n```\n```python\nopen('secret')\n```",
        "```python\nimport os\n```\n```text\ntrace : 1\n```",
        "```text\nimport os\n```",
        "```unknown\ndef charger():\n    return open('secret')\n```",
    ],
)
def test_unsupported_fences_do_not_hide_unsafe_python_or_turn_it_into_a_retry(answer):
    client = Client(draft(answer))
    with pytest.raises(ValueError, match="non autorisé"):
        subject._author(client, subject.exercise_request("1", 42, []), "1")
    assert len(client.requests) == 1


@pytest.mark.parametrize("large_print", [False, True])
@pytest.mark.parametrize("correction", [False, True])
def test_real_pdf_preserves_plaintext_trace_and_following_python(
    tmp_path, large_print, correction
):
    text = (
        "Trace :\n```text\nétape 1 : [4, 2]\nétape 2 : [2, 4]\n```\n```python\n"
        + CODE
        + "```"
    )
    source = exercises()
    source[0] = source[0].model_copy(
        update={
            "questions": (
                source[0].questions[0].model_copy(update={"prompt": text}),
                *source[0].questions[1:],
            )
        }
    )
    original = [exercise.model_dump(mode="json") for exercise in source]
    path = tmp_path / "plaintext-trace.pdf"
    render(path, source, large_print=large_print, correction=correction)
    validate_llm_pdf(path, source, large_print=large_print, correction=correction)
    assert [exercise.model_dump(mode="json") for exercise in source] == original
    with pymupdf.open(path) as pdf:
        printed = "\n".join(page.get_text() for page in pdf)
    assert (
        printed.index("étape 1")
        < printed.index("étape 2")
        < printed.index("def calculer")
    )
    assert "[4, 2]" in printed and "[2, 4]" in printed


def test_unclosed_fence_refuses_but_does_not_hide_later_unsafe_fields():
    text = "```python\nx = 1\n"
    with pytest.raises(CodeFenceError):
        fenced_parts(text)
    assert fenced_parts(text, require_closed=False)[1].closed is False
    first = draft(text)
    client = Client(first, draft("Réponse développée."))
    _, record = subject._author(client, subject.exercise_request("1", 42, []), "1")
    assert record["attempts"] == 2
    first["questions"][1]["answer"] = "```python\nimport os\n```"
    client = Client(first)
    with pytest.raises(ValueError, match="non autorisé"):
        subject._author(client, subject.exercise_request("1", 42, []), "1")
    assert len(client.requests) == 1


def test_later_unsafe_fence_is_still_audited_after_literal_mentions():
    raw = draft(PROMPT + "\n```python\nopen('secret')\n```")
    with pytest.raises(ValueError, match="non autorisé"):
        subject.validate_authored_exercise(raw, "1")


def test_display_fragment_completeness_policy_is_not_relaxed():
    raw = draft("```python\n    elif valeur\n        return 1\n```")
    with pytest.raises(subject.PythonCodeFormatError):
        subject.validate_authored_exercise(raw, "1")


@pytest.mark.parametrize("large_print", [False, True])
@pytest.mark.parametrize("correction", [False, True])
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_real_pdf_preserves_inline_fence_prose_and_code_order(
    tmp_path, large_print, correction, newline
):
    source = exercises()
    source[0] = source[0].model_copy(
        update={
            "questions": (
                source[0]
                .questions[0]
                .model_copy(update={"prompt": PROMPT.replace("\n", newline)}),
                *source[0].questions[1:],
            )
        }
    )
    before = [exercise.model_dump(mode="json") for exercise in source]
    path = tmp_path / "literal-fence.pdf"
    render(path, source, large_print=large_print, correction=correction)
    validate_llm_pdf(path, source, large_print=large_print, correction=correction)
    assert [exercise.model_dump(mode="json") for exercise in source] == before
    with pymupdf.open(path) as pdf:
        text = "\n".join(page.get_text() for page in pdf)
        assert "```python." in text
        assert text.index("```python.") < text.index("def calculer(valeur):")


@pytest.mark.parametrize("policy", [V36_LEGACY_PRINT_POLICY, V36_READABLE_PRINT_POLICY])
def test_retained_v36_render_does_not_use_new_fence_tokenizer(
    monkeypatch, tmp_path, policy
):
    def unexpected(_text):
        pytest.fail("Retained V36 rendering must keep its original fence behavior")

    monkeypatch.setattr("Backend.Core.france.rendering.fenced_parts", unexpected)
    source = exercises()
    source[0] = source[0].model_copy(
        update={
            "questions": (
                source[0]
                .questions[0]
                .model_copy(update={"prompt": "Analysez.\n```python\n" + CODE + "```"}),
                *source[0].questions[1:],
            )
        }
    )
    path = tmp_path / "retained-v2.pdf"
    render_pdf_atomically(
        path,
        lambda destination: render_assessment(
            destination,
            source,
            correction=False,
            print_policy=policy,
            human_readable_graph_titles=True,
            coherent_material_flow=True,
        ),
        role="question_paper",
        language="fr-FR",
    )
    validate_llm_pdf(path, source, correction=False, print_policy=policy)


def test_current_package_requires_its_versioned_fence_print_policy(tmp_path):
    package = generate(tmp_path, PackageClient())
    assert package["identity"]["print_policy"] == "fr-nsi-v36-model-review-v3"
    for value in [
        None,
        True,
        V36_LEGACY_PRINT_POLICY,
        V36_READABLE_PRINT_POLICY,
        "unknown",
    ]:
        changed = deepcopy(package)
        if value is None:
            changed["identity"].pop("print_policy")
        else:
            changed["identity"]["print_policy"] = value
        with pytest.raises(ValueError, match="Identité"):
            subject.validate_package(changed)
