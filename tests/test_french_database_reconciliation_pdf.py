# V24 PDF gates retain source facts, working space and correction credit.

from __future__ import annotations

import pytest


class _TextPage:
    def __init__(self, text):
        self.text = text

    def get_text(self):
        return self.text


class _TextDocument:
    def __init__(self, pages):
        self.pages = [_TextPage(page) for page in pages]

    def __enter__(self):
        return self.pages

    def __exit__(self, *_):
        return False


@pytest.mark.parametrize("large_print", [False, True])
def test_v24_pdf_keeps_staged_materials_and_exact_credit(tmp_path, large_print):
    import pymupdf

    from Backend.Core.france.database_reconciliation_contract import (
        build_database_reconciliation_contract,
    )
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.pipeline import generate_assessment
    from Backend.Core.france.rendering import render_assessment
    from Backend.Core.france.runtime import validate_database_reconciliation_pdf
    from tests.test_nsi_pipeline import ControlledReconciliationFrenchClient, make_index

    index = tmp_path / "references.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=ControlledReconciliationFrenchClient(),
        seed=270100,
        checkpoint=tmp_path / "checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v24",
    )
    exercises = [NSIExercise.model_validate(raw) for raw in package["exercises"]]
    contract = build_database_reconciliation_contract(270100)
    for correction in (False, True):
        path = tmp_path / ("correction.pdf" if correction else "subject.pdf")
        render_assessment(
            path, exercises, correction=correction, large_print=large_print
        )
        validate_database_reconciliation_pdf(
            path, contract, correction=correction, exercise=exercises[1]
        )
        with pymupdf.open(path) as pdf:
            pages = [page.get_text() for page in pdf]
            lower, upper = (
                (27, 30)
                if correction and large_print
                else (18, 20)
                if correction
                else (15, 17)
                if large_print
                else (11, 13)
            )
            assert lower <= len(pages) <= upper
            assert all(
                0 <= word[0] <= word[2] <= page.rect.width
                and 0 <= word[1] <= word[3] <= page.rect.height
                for page in pdf
                for word in page.get_text("words")
            )
            raw = "\n".join(pages)
            if large_print and not correction:
                assert any(
                    "def parcours_largeur" in page and "return ordre" in page
                    for page in pages
                ), "A complete candidate code block must stay on one large-print page"
            for title, before, after in (
                ("Table de travail — rapport comparé (2c–2e)", "2b", "2c"),
                ("Table de travail — effectifs (2f)", "2e", "2f"),
                ("Table de travail — états et fonction (2i–2k)", "2h", "2i"),
            ):
                assert raw.index(f"\n{before}.") < raw.index(title)
                assert raw.index(title) < raw.index(f"\n{after}.")


def test_v24_pdf_gate_rejects_mutated_rows_working_surfaces_and_credit(
    tmp_path, monkeypatch
):
    import pymupdf

    from Backend.Core.france import runtime
    from Backend.Core.france.database_reconciliation_contract import (
        build_database_reconciliation_contract,
    )
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.pipeline import generate_assessment
    from Backend.Core.france.rendering import render_assessment
    from tests.test_nsi_pipeline import ControlledReconciliationFrenchClient, make_index

    index = tmp_path / "references.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=ControlledReconciliationFrenchClient(),
        seed=270100,
        checkpoint=tmp_path / "checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v24",
    )
    exercises = [NSIExercise.model_validate(raw) for raw in package["exercises"]]
    contract = build_database_reconciliation_contract(270100)
    subject = tmp_path / "subject.pdf"
    correction = tmp_path / "correction.pdf"
    render_assessment(subject, exercises, correction=False)
    render_assessment(correction, exercises, correction=True)
    with pymupdf.open(subject) as pdf:
        subject_pages = [page.get_text() for page in pdf]
    with pymupdf.open(correction) as pdf:
        correction_pages = [page.get_text() for page in pdf]
    subject_text = "\n".join(subject_pages)
    correction_text = "\n".join(correction_pages)
    working_title = "Table de travail — effectifs (2f)"
    source_title = exercises[1].materials[0].title
    assert working_title in subject_text and source_title in subject_text
    mutations = (
        (subject, False, subject_text.replace(source_title, "Source supprimée", 1)),
        (subject, False, subject_text.replace(working_title, "Table supprimée", 1)),
        (subject, False, subject_text.replace("\n101\n", "\n999\n", 1)),
        (subject, False, subject_text + "\n" + contract.to_dict()["correct_sql"]),
        (
            correction,
            True,
            correction_text.replace(
                "clos au total = 4, 5, 6", "clos au total = 4, 5, 9", 1
            ),
        ),
        (
            correction,
            True,
            correction_text.replace(
                "Barème indicatif — question 2a", "Barème indicatif — question 2b", 1
            ),
        ),
        (
            correction,
            True,
            correction_text.replace(
                "Barème indicatif — question 2a\n",
                "Barème indicatif — question 2a\n0,25 point\nPoints pour Crédit ajouté.\n",
                1,
            ),
        ),
    )
    for index, (path, is_correction, mutated) in enumerate(mutations):
        original = correction_text if is_correction else subject_text
        assert mutated != original
        with monkeypatch.context() as patch:
            patch.setattr(
                runtime.pymupdf, "open", lambda _, text=mutated: _TextDocument([text])
            )
            try:
                runtime.validate_database_reconciliation_pdf(
                    path,
                    contract,
                    correction=is_correction,
                    exercise=exercises[1],
                )
            except ValueError as error:
                assert "Incident-reconciliation" in str(error)
            else:
                pytest.fail(f"V24 PDF mutation {index} passed the gate")
