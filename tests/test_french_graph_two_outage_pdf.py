# V25 printed facts must be bound to the two-outage contract

import pytest


@pytest.mark.parametrize("seed", [270100, 270102])
@pytest.mark.parametrize("large_print", [False, True])
@pytest.mark.parametrize("human_readable_titles", [False, True])
def test_v25_two_outage_pdf_stages_work_and_rejects_mutations(
    tmp_path, monkeypatch, large_print, seed, human_readable_titles
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
        seed=seed,
        checkpoint=tmp_path / "checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v25",
    )
    exercises = [NSIExercise.model_validate(raw) for raw in package["exercises"]]
    contract = build_graph_two_outage_contract(seed)
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
            path,
            exercises,
            correction=correction,
            large_print=large_print,
            human_readable_graph_titles=human_readable_titles,
            coherent_material_flow=human_readable_titles,
        )
        runtime.validate_graph_two_outage_pdf(
            path,
            contract,
            correction=correction,
            exercise=exercises[0],
            human_readable_titles=human_readable_titles,
            coherent_material_flow=human_readable_titles and not large_print,
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
        assert (" — route_double_fermeture" in raw) == (not human_readable_titles)
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
        if not correction or (human_readable_titles and not large_print):
            assert any(
                "Trace de Dijkstra après fermeture" in page and "1f." in page
                for page in pages
            )
            assert any(
                f"Trajet après fermeture de {second}" in page and "1g." in page
                for page in pages
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
                        path,
                        contract,
                        correction=correction,
                        exercise=exercises[0],
                        human_readable_titles=human_readable_titles,
                    )
        if not correction:
            winning_route = " → ".join(
                contract.to_dict()["expected"]["1g"]["route_after"]
            )
            winning_cost = contract.to_dict()["expected"]["1g"]["cost_after"]
            for leaked in (
                f"Trajet gagnant : {winning_route}",
                f"Coût gagnant = {winning_cost}",
                f"Le trajet minimal restant est {'-'.join(contract.to_dict()['expected']['1g']['route_after'])}, de coût total {winning_cost}.",
            ):
                altered = [
                    page + "\n" + leaked if "1g." in page else page for page in pages
                ]
                with monkeypatch.context() as patch:
                    patch.setattr(
                        runtime.pymupdf,
                        "open",
                        lambda _, values=altered: ExtractedDocument(values),
                    )
                    with pytest.raises(ValueError):
                        runtime.validate_graph_two_outage_pdf(
                            path,
                            contract,
                            correction=False,
                            exercise=exercises[0],
                            human_readable_titles=human_readable_titles,
                        )
            for leaked in (
                "Trajet gagnant : " + winning_route,
                f"Le coût total est de {winning_cost}.",
            ):
                altered = [
                    page + "\n" + leaked if "Exercice 2 (" in page else page
                    for page in pages
                ]
                with monkeypatch.context() as patch:
                    patch.setattr(
                        runtime.pymupdf,
                        "open",
                        lambda _, values=altered: ExtractedDocument(values),
                    )
                    with pytest.raises(ValueError):
                        runtime.validate_graph_two_outage_pdf(
                            path,
                            contract,
                            correction=False,
                            exercise=exercises[0],
                            human_readable_titles=human_readable_titles,
                        )
            for task_id in ("1f", "1g"):
                altered = []
                for page in pages:
                    if task_id + "." in page:
                        before, after = page.split(task_id + ".", 1)
                        altered.extend((before, task_id + "." + after))
                    else:
                        altered.append(page)
                with monkeypatch.context() as patch:
                    patch.setattr(
                        runtime.pymupdf,
                        "open",
                        lambda _, values=altered: ExtractedDocument(values),
                    )
                    with pytest.raises(ValueError):
                        runtime.validate_graph_two_outage_pdf(
                            path,
                            contract,
                            correction=False,
                            exercise=exercises[0],
                            human_readable_titles=human_readable_titles,
                        )
