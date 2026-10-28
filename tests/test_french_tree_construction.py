# Independent checks for the complete V29 recursive construction task.

from copy import deepcopy
from decimal import Decimal
from types import SimpleNamespace

import pytest


def test_interval_reference_handles_boundaries_empty_trees_and_pruning():
    from Backend.Core.france.tree_construction_authoring import INTERVAL_CODE

    namespace = {}
    exec(INTERVAL_CODE, namespace)  # Fixed app-owned source, never model output.
    count = namespace["compter_intervalle"]

    def node(value, left=None, right=None):
        return SimpleNamespace(valeur=value, gauche=left, droite=right)

    tree = node(10, node(5, node(2), node(7)), node(20, node(15), node(25)))
    for low in range(0, 28):
        for high in range(low, 28):
            before = deepcopy(tree)
            assert count(tree, low, high) == sum(
                low <= value <= high for value in (2, 5, 7, 10, 15, 20, 25)
            )
            assert tree == before
    assert count(None, 0, 1) == 0

    class Forbidden:
        @property
        def valeur(self):
            raise AssertionError("Pruned subtree must not be visited")

    assert count(node(1, Forbidden(), node(5)), 5, 5) == 1
    assert count(node(9, node(5), Forbidden()), 5, 5) == 1


@pytest.mark.parametrize("seed", [270100, 270101, 270102])
def test_v29_construction_has_typed_independent_evidence(tmp_path, seed):
    from Backend.Core.france.pipeline import generate_assessment, validate_package
    from Backend.Core.france.verification import verify_contract
    from tests.test_nsi_pipeline import ControlledTwoOutageFrenchClient, make_index

    index = tmp_path / "references.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=ControlledTwoOutageFrenchClient(),
        seed=seed,
        checkpoint=tmp_path / "checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v29",
    )
    question = package["exercises"][0]["questions"][-1]
    assert "Écrivez entièrement" in question["prompt"]
    assert "def compter_intervalle" not in question["prompt"]
    assert question["points"] == "1"
    assert question["operation"] == "design"
    assert len(question["marking"]) == 4
    assert (
        sum(q["estimated_minutes"] for q in package["exercises"][0]["questions"]) == 70
    )
    assert (
        sum(Decimal(q["points"]) for e in package["exercises"] for q in e["questions"])
        == 18
    )
    assert verify_contract(question["verification"])["passed"]
    expected = question["verification"]["expected"]
    assert expected["count"] == len(expected["included_keys"])
    from Backend.Core.france.tree_construction_authoring import INTERVAL_CODE

    tree = question["verification"]["contract"]["tree"]
    nodes = {row[0]: SimpleNamespace(valeur=row[0]) for row in tree["rows"]}
    for key, left, right in tree["rows"]:
        nodes[key].gauche, nodes[key].droite = nodes.get(left), nodes.get(right)
    current = nodes[tree["root"]]
    while True:
        side = "gauche" if tree["insert_key"] < current.valeur else "droite"
        child = getattr(current, side)
        if child is None:
            setattr(
                current,
                side,
                SimpleNamespace(valeur=tree["insert_key"], gauche=None, droite=None),
            )
            break
        current = child
    namespace = {}
    exec(INTERVAL_CODE, namespace)
    assert (
        namespace["compter_intervalle"](nodes[tree["root"]], *expected["bounds"])
        == expected["count"]
    )
    changed = deepcopy(question["verification"])
    changed["expected"]["count"] += 1
    assert not verify_contract(changed)["passed"]
    validate_package(package)
    changed = deepcopy(package)
    changed["exercises"][0]["questions"][-1]["answer"] = "return 0"
    with pytest.raises(ValueError):
        validate_package(changed)


@pytest.mark.parametrize("large_print", [False, True])
def test_v29_pdf_preserves_tree_task_and_solution(tmp_path, large_print):
    import pymupdf

    from Backend.Core.france.graph_two_outage_contract import (
        build_graph_two_outage_contract,
    )
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.pipeline import generate_assessment
    from Backend.Core.france.rendering import render_assessment
    from Backend.Core.france.runtime import validate_graph_two_outage_pdf
    from tests.test_nsi_pipeline import ControlledTwoOutageFrenchClient, make_index

    index = tmp_path / "references.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=ControlledTwoOutageFrenchClient(),
        seed=270100,
        checkpoint=tmp_path / "checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v29",
    )
    exercises = [NSIExercise.model_validate(raw) for raw in package["exercises"]]
    for correction in (False, True):
        path = tmp_path / f"{correction}.pdf"
        render_assessment(
            path,
            exercises,
            correction=correction,
            large_print=large_print,
            coherent_material_flow=True,
            human_readable_graph_titles=True,
        )
        validate_graph_two_outage_pdf(
            path,
            build_graph_two_outage_contract(270100),
            correction=correction,
            exercise=exercises[0],
            human_readable_titles=True,
            coherent_material_flow=not large_print,
        )
        with pymupdf.open(path) as pdf:
            if correction and not large_print:
                pages = [page.get_text() for page in pdf]
                preceding = next(
                    i
                    for i, text in enumerate(pages)
                    if "Barème indicatif — question 1i" in text
                )
                construction = next(i for i, text in enumerate(pages) if "1j." in text)
                assert construction == preceding, (
                    "Long solution must not push its whole question onto a new page"
                )
                solution = next(
                    text for text in pages if "def compter_intervalle" in text
                )
                assert "Réponse attendue — question 1j" in solution
                assert "Barème indicatif — question 1j" in solution
            for page in pdf:
                for x0, y0, x1, y1, *_ in page.get_text("words"):
                    assert 0 <= x0 < x1 <= page.rect.width
                    assert 0 <= y0 < y1 <= page.rect.height
