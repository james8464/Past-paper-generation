"""V25 printed facts must be bound to the two-outage contract."""

import pytest


@pytest.mark.parametrize("large_print", [False, True])
def test_v25_two_outage_pdf_stages_work_and_rejects_mutations(
    tmp_path, monkeypatch, large_print
):
    import pymupdf

    from Backend.Core.france import runtime
    from Backend.Core.france.graph_two_outage_contract import (
        build_graph_two_outage_contract,
    )
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.pipeline import generate_assessment
    from Backend.Core.france.rendering import render_assessment
    from tests.test_nsi_pipeline import ControlledTwoOutageFrenchClient, make_index

    index = tmp_path / "references.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=ControlledTwoOutageFrenchClient(),
        seed=270100,
        checkpoint=tmp_path / "checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v25",
    )
    exercises = [NSIExercise.model_validate(raw) for raw in package["exercises"]]
    contract = build_graph_two_outage_contract(270100)
    first = "–".join(contract.to_dict()["closed_edge"])
    second = "–".join(contract.to_dict()["closed_edge_second"])

    class ExtractedDocument:
        def __init__(self, values):
            self.values = values

        def __enter__(self):
            return [
                type("Page", (), {"get_text": lambda _self, value=text: value})()
                for text in self.values
            ]

        def __exit__(self, *_):
            return False

    for correction in (False, True):
        path = tmp_path / ("correction.pdf" if correction else "subject.pdf")
        render_assessment(
            path, exercises, correction=correction, large_print=large_print
        )
        runtime.validate_graph_two_outage_pdf(
            path, contract, correction=correction, exercise=exercises[0]
        )
        with pymupdf.open(path) as pdf:
            pages = [page.get_text() for page in pdf]
            assert 9 <= len(pdf) <= (32 if correction and large_print else 24)
            assert all(
                0 <= word[0] <= word[2] <= page.rect.width
                and 0 <= word[1] <= word[3] <= page.rect.height
                for page in pdf
                for word in page.get_text("words")
            )
        raw = "\n".join(pages)
        assert (
            raw.index("1e.")
            < raw.index("Trace de Dijkstra après fermeture")
            < raw.index("1f.")
        )
        assert (
            raw.index("1f.")
            < raw.index(f"Trajet après fermeture de {second}")
            < raw.index("1g.")
        )
        for before, after in (
            (f"Trajet après fermeture de {second}", "Trajet absent"),
            (
                f"Trajet après fermeture de {second}",
                f"Trajet après fermeture de {first}",
            ),
            ("_____", "A=0"),
            ("1g.", "1f."),
        ):
            changed = [page.replace(before, after, 1) for page in pages]
            with monkeypatch.context() as patch:
                patch.setattr(
                    runtime.pymupdf,
                    "open",
                    lambda _, values=changed: ExtractedDocument(values),
                )
                with pytest.raises(ValueError):
                    runtime.validate_graph_two_outage_pdf(
                        path, contract, correction=correction, exercise=exercises[0]
                    )
