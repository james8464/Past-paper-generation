"""Current graph clearance must not change retained V36 print policies."""

import pymupdf
import pytest

from Backend.Core.france import llm_pdf, rendering
from Backend.Core.france.llm_pipeline import PRINT_POLICY
from Backend.Core.france.print_policy import V36_PRINT_POLICIES
from Backend.Core.render_transaction import render_pdf_atomically
from tests.test_french_llm_pdf import exercises


@pytest.mark.parametrize(
    "policy", ["fr-nsi-v36-model-review-v3", "fr-nsi-v36-model-review-v4"]
)
def test_inline_prose_survives_both_current_and_retained_policy(tmp_path, policy):
    assert PRINT_POLICY == "fr-nsi-v36-model-review-v4"
    assert policy in V36_PRINT_POLICIES
    source = exercises()
    source[0] = source[0].model_copy(update={"context": "Une <u>clé</u> et `valeur`."})
    target = tmp_path / "inline.pdf"
    render_pdf_atomically(
        target,
        lambda destination: rendering.render_assessment(
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
    llm_pdf.validate_llm_pdf(target, source, correction=False, print_policy=policy)
    with pymupdf.open(target) as document:
        text = "\n".join(page.get_text() for page in document)
    assert "<u>clé</u>" not in text and "`valeur`" not in text
    assert "clé" in text and "valeur" in text


@pytest.mark.parametrize(
    "policy,expected",
    [
        ("fr-nsi-v36-model-review-v2", False),
        ("fr-nsi-v36-model-review-v3", False),
        ("fr-nsi-v36-model-review-v4", True),
    ],
)
def test_renderer_and_validator_select_the_same_geometry_policy(
    tmp_path, monkeypatch, policy, expected
):
    calls = {"renderer": [], "validator": []}
    for module, name in ((rendering, "renderer"), (llm_pdf, "validator")):
        original = module.graph_layout

        def record(*args, _original=original, _name=name, **kwargs):
            calls[_name].append(kwargs.get("avoid_foreign_edges", False))
            return _original(*args, **kwargs)

        monkeypatch.setattr(module, "graph_layout", record)
    source = exercises(graphs=True)
    target = tmp_path / "graph.pdf"
    render_pdf_atomically(
        target,
        lambda destination: rendering.render_assessment(
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
    llm_pdf.validate_llm_pdf(target, source, correction=False, print_policy=policy)
    assert calls["renderer"] and calls["validator"]
    assert set(calls["renderer"]) == set(calls["validator"]) == {expected}
