"""Independent tests for V30 route filtering and complete selection."""

from copy import deepcopy
from itertools import pairwise, permutations

import pytest


def package_for_seed(tmp_path, seed):
    from Backend.Core.france.pipeline import generate_assessment
    from tests.test_nsi_pipeline import ControlledTwoOutageFrenchClient, make_index

    index = tmp_path / "references.sqlite"
    make_index(index)
    return generate_assessment(
        index_path=index,
        client=ControlledTwoOutageFrenchClient(),
        seed=seed,
        checkpoint=tmp_path / "checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v30",
    )


@pytest.mark.parametrize("seed", [270100, 270101, 270102])
def test_v30_package_binds_selection_and_preserves_marks_and_time(tmp_path, seed):
    from decimal import Decimal

    from Backend.Core.france.pipeline import validate_package
    from Backend.Core.france.verification import verify_contract

    package = package_for_seed(tmp_path, seed)
    validate_package(package)
    e1 = package["exercises"][0]
    assert sum(q["estimated_minutes"] for q in e1["questions"]) == 70
    assert (
        sum(Decimal(q["points"]) for e in package["exercises"] for q in e["questions"])
        == 18
    )
    assert e1["questions"][6]["operation"] == "design"
    assert e1["questions"][6]["points"] == "1"
    assert {m["id"] for m in e1["materials"]}.isdisjoint(
        {"trace_fermeture", "route_double_fermeture"}
    )
    for question in e1["questions"][5:7]:
        assert verify_contract(question["verification"])["passed"]
        changed = deepcopy(question["verification"])
        changed["expected"]["selected_index"] = -1
        assert not verify_contract(changed)["passed"]
        changed = deepcopy(question["verification"])
        changed["expected"]["first_available"][0] = int(
            changed["expected"]["first_available"][0]
        )
        assert not verify_contract(changed)["passed"]
        changed = deepcopy(question["verification"])
        changed["task_id"] = "1a"
        assert not verify_contract(changed)["passed"]
    changed = deepcopy(package)
    changed["exercises"][0]["questions"][6]["answer"] = "return 0"
    with pytest.raises(ValueError):
        validate_package(changed)


@pytest.mark.parametrize("large_print", [False, True])
def test_v30_pdf_binds_public_catalogue_and_construction(tmp_path, large_print):
    import pymupdf

    from Backend.Core.france.graph_two_outage_contract import (
        build_graph_two_outage_contract,
    )
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.rendering import render_assessment
    from Backend.Core.france.runtime import validate_graph_two_outage_pdf

    package = package_for_seed(tmp_path, 270100)
    exercises = [NSIExercise.model_validate(e) for e in package["exercises"]]
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
            exercise=exercises[0],
            correction=correction,
            human_readable_titles=True,
            coherent_material_flow=not large_print,
        )
        with pymupdf.open(path) as pdf:
            text = " ".join(page.get_text() for page in pdf)
            assert "def disponible" in text
            assert ("def meilleur_trajet" in text) == correction
            for page in pdf:
                for x0, y0, x1, y1, *_ in page.get_text("words"):
                    assert 0 <= x0 < x1 <= page.rect.width
                    assert 0 <= y0 < y1 <= page.rect.height
        if not correction:
            altered = tmp_path / "altered-helper.pdf"
            with pymupdf.open(path) as pdf:
                removed = 0
                for page in pdf:
                    for rectangle in page.search_for("def disponible"):
                        page.add_redact_annot(rectangle)
                        removed += 1
                    page.apply_redactions()
                assert removed == 1
                pdf.save(altered)
            with pytest.raises(ValueError, match="helper missing"):
                validate_graph_two_outage_pdf(
                    altered,
                    build_graph_two_outage_contract(270100),
                    exercise=exercises[0],
                    correction=False,
                    human_readable_titles=True,
                    coherent_material_flow=not large_print,
                )


def test_route_selector_matches_independent_oracle_and_preserves_inputs():
    from Backend.Core.france.route_selection_authoring import HELPER_CODE, SELECTOR_CODE

    namespace = {}
    exec(HELPER_CODE + "\n\n" + SELECTOR_CODE, namespace)
    routes = [["A", "B", "D"], ["A", "C", "D"], ["A", "D"]]
    for order in permutations(range(3)):
        paths = [routes[i] for i in order]
        for costs in ([5, 2, 2], [1, 1, 1], [9, 4, 6]):
            for closed in (
                [],
                [["B", "A"]],
                [["A", "D"], ["D", "C"]],
                [["A", "B"], ["A", "C"], ["A", "D"]],
            ):
                before = deepcopy((paths, costs, closed))
                blocked = {frozenset(edge) for edge in closed}
                eligible = [
                    i
                    for i, path in enumerate(paths)
                    if not any(frozenset(edge) in blocked for edge in pairwise(path))
                ]
                expected = min(eligible, key=lambda i: costs[i]) if eligible else None
                assert namespace["meilleur_trajet"](paths, costs, closed) == expected
                assert (paths, costs, closed) == before
    assert namespace["meilleur_trajet"]([], [], []) is None


def test_route_catalogue_facts_are_independently_checkable():
    from Backend.Core.france.graph_two_outage_contract import (
        build_graph_two_outage_contract,
    )
    from Backend.Core.france.route_selection_authoring import route_selection_expected

    for seed in (270100, 270101, 270102):
        data = build_graph_two_outage_contract(seed).to_dict()
        facts = route_selection_expected(data)
        assert len(facts["routes"]) == 4
        assert len({tuple(route) for route in facts["routes"]}) == 4
        weights = {frozenset((a, b)): weight for a, b, weight in data["graph"]["edges"]}
        assert facts["costs"] == [
            sum(weights[frozenset(edge)] for edge in pairwise(route))
            for route in facts["routes"]
        ]
        for stage, closures in (
            ("first", [data["closed_edge"]]),
            ("second", [data["closed_edge"], data["closed_edge_second"]]),
        ):
            available = [
                not any(
                    frozenset(edge) == frozenset(closed)
                    for edge in pairwise(route)
                    for closed in closures
                )
                for route in facts["routes"]
            ]
            assert facts[stage + "_available"] == available
        eligible = [
            i for i, available in enumerate(facts["second_available"]) if available
        ]
        assert facts["selected_index"] == min(eligible, key=lambda i: facts["costs"][i])
