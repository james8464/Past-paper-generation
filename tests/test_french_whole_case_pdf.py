"""Whole-case publication must validate what was actually printed."""

from copy import deepcopy

import pymupdf
import pytest


@pytest.fixture(scope="module", params=range(270100, 270103))
def whole_package(request, tmp_path_factory):
    from Backend.Core.france.pipeline import generate_assessment
    from tests.test_nsi_pipeline import ControlledTwoOutageFrenchClient, make_index

    root = tmp_path_factory.mktemp(f"whole-{request.param}")
    index = root / "references.sqlite"
    make_index(index)
    return generate_assessment(
        index_path=index,
        client=ControlledTwoOutageFrenchClient(),
        seed=request.param,
        checkpoint=root / "checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v32",
    )


def render(path, package, correction, large_print=False):
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.rendering import render_assessment
    from Backend.Core.render_transaction import render_pdf_atomically

    render_pdf_atomically(
        path,
        lambda destination: render_assessment(
            destination,
            [NSIExercise.model_validate(e) for e in package["exercises"]],
            correction=correction,
            large_print=large_print,
            human_readable_graph_titles=True,
            coherent_material_flow=True,
        ),
        role="mark_scheme" if correction else "question_paper",
        language="fr-FR",
    )


@pytest.mark.parametrize("correction", [False, True])
@pytest.mark.parametrize("large_print", [False, True])
def test_full_whole_case_pdf_matches_verified_package(
    tmp_path, whole_package, correction, large_print
):
    from Backend.Core.france.whole_case_pdf import validate_whole_case_pdf

    path = tmp_path / "paper.pdf"
    render(path, whole_package, correction, large_print)
    validate_whole_case_pdf(path, whole_package, correction=correction)
    with pytest.raises(ValueError):
        validate_whole_case_pdf(path, whole_package, correction=not correction)


@pytest.mark.parametrize("correction", [False, True])
def test_whole_case_gate_rejects_missing_or_extra_printed_content(
    tmp_path, whole_package, correction
):
    from Backend.Core.france.whole_case_pdf import validate_whole_case_pdf

    source = tmp_path / "paper.pdf"
    render(source, whole_package, correction)
    for mutation in (
        "remove_question",
        "extra_content",
        "remove_source",
        "extra_cover",
    ):
        target = tmp_path / f"{mutation}.pdf"
        with pymupdf.open(source) as pdf:
            page = next(p for p in pdf if p.search_for("1a."))
            if mutation == "extra_cover":
                pdf[0].insert_text((80, 780), "UNEXPECTED ANSWER")
            elif mutation == "extra_content":
                page.insert_text((80, page.rect.height - 60), "UNEXPECTED ANSWER")
            else:
                needle = "1a." if mutation == "remove_question" else "Identifiant"
                matches = page.search_for(needle)
                assert matches
                page.add_redact_annot(matches[0], fill=(1, 1, 1))
                page.apply_redactions()
            pdf.save(target)
        with pytest.raises(ValueError):
            validate_whole_case_pdf(target, whole_package, correction=correction)


def test_whole_case_gate_revalidates_package_not_only_pdf(tmp_path, whole_package):
    from Backend.Core.france.whole_case_pdf import validate_whole_case_pdf

    source = tmp_path / "paper.pdf"
    render(source, whole_package, False)
    altered = deepcopy(whole_package)
    altered["exercises"][0]["questions"][0]["answer"] = "wrong"
    with pytest.raises(ValueError):
        validate_whole_case_pdf(source, altered, correction=False)


def test_whole_case_gate_requires_a4_pages(tmp_path, whole_package):
    from Backend.Core.france.whole_case_pdf import validate_whole_case_pdf

    source, altered = tmp_path / "source.pdf", tmp_path / "wrong-size.pdf"
    render(source, whole_package, False)
    with pymupdf.open(source) as pdf:
        pdf[0].set_mediabox(pymupdf.Rect(0, 0, 650, 900))
        pdf.save(altered)
    with pytest.raises(ValueError, match="A4"):
        validate_whole_case_pdf(altered, whole_package, correction=False)


@pytest.mark.parametrize("fail_correction", [False, True])
def test_runtime_does_not_publish_when_printed_content_gate_fails(
    tmp_path, monkeypatch, fail_correction
):
    from argparse import Namespace

    from Backend.Core.france import runtime, whole_case_pdf
    from tests.test_nsi_pipeline import ControlledTwoOutageFrenchClient, make_index

    index = tmp_path / "references.sqlite"
    output = tmp_path / "output"
    make_index(index)
    monkeypatch.setattr(runtime, "model_identity", lambda *_: "fixture-digest")
    monkeypatch.setattr(
        runtime, "FrenchOllamaClient", lambda **_: ControlledTwoOutageFrenchClient()
    )
    checked = []
    original = whole_case_pdf.validate_whole_case_pdf

    def reject(path, package, *, correction):
        checked.append(correction)
        if correction == fail_correction:
            raise ValueError("Printed content mismatch")
        original(path, package, correction=correction)

    monkeypatch.setattr(whole_case_pdf, "validate_whole_case_pdf", reject)
    events = []
    monkeypatch.setattr(runtime, "emit", lambda kind, **payload: events.append(kind))
    args = Namespace(
        assessment="fr-bac-general-nsi-written-2027",
        reference_index=index,
        output=str(output),
        seed=270100,
        model="fixture",
        ollama_url="http://localhost:11434",
        allow_remote=False,
        large_print=False,
    )
    assert runtime.handle_generate_assessment(args) == 1
    assert checked == ([False, True] if fail_correction else [False])
    assert "file" not in events and "done" not in events
    assert events[-1] == "error"
    assert not list(output.glob("nsi-*")) and not list(output.glob(".nsi-*"))
    assert list((output / ".papercreator-checkpoints").glob("*.json"))
