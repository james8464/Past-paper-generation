"""Print admission is mode-bound, exact and earlier than model review."""

from copy import deepcopy

import pytest
from reportlab.lib.styles import ParagraphStyle

from Backend.Core.france import llm_pipeline as subject
from Backend.Core.france.code_layout import (
    CODE_LAYOUT_POLICY,
    CodeLayoutError,
    code_layout,
)
from Backend.Core.france.rendering import code_listing
from tests.test_french_llm_pipeline import Client, generate, raw_exercise
from tests.test_nsi_pipeline import make_index

LONG_CONDITION = "            if salle_1 == etapes[i] and salle_2 == etapes[i + 1]:\n                pass"
ENLARGED_ONLY = "def moyenne_pages(genre_cible, liste_livres):\n    return 0"


@pytest.mark.parametrize("large_print", [False, True])
def test_exact_pro10_question_line_is_refused_before_review(large_print):
    raw = raw_exercise()
    # Keep the original deep indentation without an invalid standalone suite.
    raw["questions"][0]["prompt"] = (
        "Analysez ce programme :\n```python\ndef verifier():\n    for i in range(2):\n        for salle_1, salle_2 in []:\n"
        + LONG_CONDITION
        + "\n```"
    )
    with pytest.raises(CodeLayoutError, match="question 1"):
        subject.validate_authored_exercise(raw, "1", large_print=large_print)


def test_normal_fit_does_not_claim_enlarged_fit():
    raw = raw_exercise()
    raw["questions"][0]["prompt"] = (
        f"Analysez ce programme :\n```python\n{ENLARGED_ONLY}\n```"
    )
    assert subject.validate_authored_exercise(raw, "1", large_print=False)
    with pytest.raises(CodeLayoutError):
        subject.validate_authored_exercise(raw, "1", large_print=True)


def test_long_answer_has_only_two_structural_attempts_and_no_blind_calls(tmp_path):
    client = Client(
        mutate=lambda raw: raw["questions"][0].update(
            answer='```python\nmessage = "' + "a" * 100 + '"\n```'
        )
    )
    with pytest.raises(ValueError, match="deux tentatives"):
        generate(tmp_path, client)
    assert len(client.requests) == 2
    assert all("id" in request.schema["properties"] for request in client.requests)


@pytest.mark.parametrize("large_print", [False, True])
def test_generated_mode_is_bound_and_rechecked(tmp_path, large_print):
    index = tmp_path / "index.sqlite"
    make_index(index)
    package = subject.generate(
        index_path=index, client=Client(), seed=42, large_print=large_print
    )
    assert package["identity"]["layout_policy"] == CODE_LAYOUT_POLICY
    assert package["identity"]["large_print"] is large_print
    assert subject.validate_package(package)
    for value in (None, "false", 0):
        altered = deepcopy(package)
        altered["identity"]["large_print"] = value
        with pytest.raises(ValueError):
            subject.validate_package(altered)


def test_source_guard_uses_exact_metrics_and_preserves_tabs():
    layout = code_layout(False)
    style = ParagraphStyle("test", fontName=layout.font_name, fontSize=layout.font_size)
    source = "def calcul():\n\treturn 1"
    listing = code_listing(source, style, layout.question_width)
    assert listing.lines == source.splitlines()
    raw = raw_exercise()
    raw["questions"][0]["answer"] = f"```python\n{source}\n```"
    with pytest.raises(CodeLayoutError):
        subject.validate_authored_exercise(raw, "1", large_print=False)


def test_legacy_package_without_layout_policy_keeps_legacy_reading(tmp_path):
    package = generate(tmp_path, Client())
    package["identity"].pop("layout_policy")
    package["identity"].pop("large_print")
    assert subject.validate_package(package)
    package["identity"]["large_print"] = False
    with pytest.raises(ValueError):
        subject.validate_package(package)


def test_unknown_layout_policy_cannot_replay(tmp_path):
    package = generate(tmp_path, Client())
    package["identity"]["layout_policy"] = "unknown-policy"
    with pytest.raises(ValueError, match="mise en page"):
        subject.validate_package(package)


def test_replay_rechecks_changed_mode_against_actual_lines(tmp_path):
    package = generate(
        tmp_path,
        Client(
            mutate=lambda raw: raw["questions"][0].update(
                prompt=f"Analysez ce programme :\n```python\n{ENLARGED_ONLY}\n```"
            )
        ),
    )
    package["identity"]["large_print"] = True
    with pytest.raises(CodeLayoutError):
        subject.validate_package(package)


def test_unsafe_code_does_not_become_a_layout_regeneration(tmp_path):
    def mutate(raw):
        raw["questions"][0]["answer"] = '```python\ntexte = "' + "a" * 100 + '"\n```'
        raw["questions"][1]["answer"] = "```python\nimport os\n```"

    client = Client(mutate=mutate)
    with pytest.raises(ValueError, match="non autorisé"):
        generate(tmp_path, client)
    assert len(client.requests) == 1


def test_one_full_layout_regeneration_preserves_mode_and_rejected_source(tmp_path):
    class Regenerated(Client):
        def generate_request(self, request):
            value = super().generate_request(request)
            if value.get("id") == "1" and request.attempt == 1:
                value["questions"][0]["answer"] = (
                    '```python\ntexte = "' + "a" * 100 + '"\n```'
                )
            return value

    index = tmp_path / "index.sqlite"
    make_index(index)
    client = Regenerated()
    package = subject.generate(
        index_path=index, client=client, seed=42, large_print=True
    )
    first, second = client.requests[:2]
    assert first.attempt == 1 and second.attempt == 2
    assert first.schema == second.schema
    assert first.generation_seed == second.generation_seed
    assert first.output_budget == second.output_budget
    assert "Mise en page demandée : agrandie" in first.prompt
    assert "Mise en page demandée : agrandie" in second.prompt
    assert package["authoring_attempts"][0]["attempts"] == 2
    rejected = package["authoring_attempts"][0]["rejected"][0]
    assert "a" * 100 in rejected["response"]["questions"][0]["answer"]
    assert rejected["response_sha256"] == subject._digest(rejected["response"])
    assert len(client.requests) == 10


@pytest.mark.parametrize("large_print", [False, True])
def test_exact_layout_width_boundary_keeps_source_unchanged(large_print):
    from reportlab.pdfbase.pdfmetrics import stringWidth

    layout = code_layout(large_print)
    style = ParagraphStyle(
        "boundary", fontName=layout.font_name, fontSize=layout.font_size
    )
    line = "# étiquettes et espaces"
    width = stringWidth(line, layout.font_name, layout.font_size)
    assert code_listing(line, style, width).lines == [line]
    with pytest.raises(CodeLayoutError):
        code_listing(line, style, width - 0.001)
