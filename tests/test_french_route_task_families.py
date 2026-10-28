# check route algorithms against independent results, including boundaries and input preservation

from copy import deepcopy
from itertools import pairwise, permutations

import pytest


def checked_package(tmp_path, seed, version="v31"):
    from decimal import Decimal

    from Backend.Core.france.pipeline import generate_assessment, validate_package
    from tests.test_nsi_pipeline import ControlledTwoOutageFrenchClient, make_index

    index = tmp_path / "references.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=ControlledTwoOutageFrenchClient(),
        seed=seed,
        checkpoint=tmp_path / "checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version=version,
    )
    validate_package(package)
    assert package["identity"]["prompt_version"] == f"fr-nsi-written-2027-{version}"
    questions = package["exercises"][0]["questions"]
    assert questions[6]["verification"]["kind"] == (
        "tree_case_contract" if version == "v32" else "route_family_contract"
    )
    assert sum(q["estimated_minutes"] for q in questions) == 70
    assert (
        sum(Decimal(q["points"]) for e in package["exercises"] for q in e["questions"])
        == 18
    )
    altered = deepcopy(package)
    altered["exercises"][0]["questions"][6]["verification"]["expected"]["family"] = (
        "other"
    )
    with pytest.raises(ValueError):
        validate_package(altered)
    return package


@pytest.mark.parametrize("seed", range(270100, 270103))
def test_v31_package_binds_selected_family_and_rejects_mutation(tmp_path, seed):
    checked_package(tmp_path, seed)


# Historical replay remains readable, not retrospectively qualified
def test_v31_retained_e2_failure_is_not_relabelled_as_v32_success(tmp_path):
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.originality import screen_originality
    from Backend.Core.france.pipeline import exercise_candidate_text

    first_path, next_path = tmp_path / "first", tmp_path / "next"
    first_path.mkdir()
    next_path.mkdir()
    packages = [checked_package(first_path, 270100), checked_package(next_path, 270101)]
    texts = [
        exercise_candidate_text(NSIExercise.model_validate(p["exercises"][1]))
        for p in packages
    ]
    with pytest.raises(ValueError, match="originalité"):
        screen_originality(texts[1], [], previous_texts=texts[:1])


# Release acceptance: all exercises, not only the new construction item
@pytest.mark.parametrize("seed", (270101, 270102))
@pytest.mark.parametrize("exercise_index", (0, 1, 2))
def test_successive_families_are_substantively_distinct(tmp_path, seed, exercise_index):
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.originality import screen_originality
    from Backend.Core.france.pipeline import exercise_candidate_text

    first_path, next_path = tmp_path / "first", tmp_path / "next"
    first_path.mkdir()
    next_path.mkdir()
    first = checked_package(first_path, 270100, version="v32")
    following = checked_package(next_path, seed, version="v32")
    previous = exercise_candidate_text(
        NSIExercise.model_validate(first["exercises"][exercise_index])
    )
    candidate = exercise_candidate_text(
        NSIExercise.model_validate(following["exercises"][exercise_index])
    )
    assert (
        screen_originality(candidate, [], previous_texts=[previous])["state"]
        == "passed_calibrated_screen"
    )


def test_three_successive_packages_pass_with_preserved_history(tmp_path):
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.pipeline import (
        exercise_candidate_text,
        generate_assessment,
        validate_package,
    )
    from tests.test_nsi_pipeline import ControlledTwoOutageFrenchClient, make_index

    index = tmp_path / "references.sqlite"
    make_index(index)
    history = []
    for seed in range(270100, 270103):
        package = generate_assessment(
            index_path=index,
            client=ControlledTwoOutageFrenchClient(),
            seed=seed,
            checkpoint=tmp_path / f"checkpoint-{seed}.json",
            previous_texts=history,
            contract_graph_tree=True,
            contract_authoring_version="v32",
        )
        validate_package(package)
        assert package["originality_history"] == history
        history.extend(
            exercise_candidate_text(NSIExercise.model_validate(e))
            for e in package["exercises"]
        )
    assert len(history) == 9


@pytest.mark.parametrize("seed", range(270100, 270103))
@pytest.mark.parametrize("large_print", [False, True])
def test_family_pdf_preserves_source_answer_and_credit(tmp_path, seed, large_print):
    import pymupdf

    from Backend.Core.france.graph_two_outage_contract import (
        build_graph_two_outage_contract,
    )
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.rendering import render_assessment
    from Backend.Core.france.runtime import validate_graph_two_outage_pdf

    package = checked_package(tmp_path, seed)
    exercises = [NSIExercise.model_validate(e) for e in package["exercises"]]
    for correction in (False, True):
        path = tmp_path / f"{seed}-{large_print}-{correction}.pdf"
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
            build_graph_two_outage_contract(seed),
            exercise=exercises[0],
            correction=correction,
            coherent_material_flow=not large_print,
        )
        with pymupdf.open(path) as pdf:
            for page in pdf:
                for x0, y0, x1, y1, *_ in page.get_text("words"):
                    assert 0 <= x0 < x1 <= page.rect.width
                    assert 0 <= y0 < y1 <= page.rect.height


def test_three_seeds_select_materially_different_algorithms():
    from Backend.Core.france.route_task_families import CODES, family_for_seed

    families = [family_for_seed(seed) for seed in range(270100, 270103)]
    assert families == ["minimum", "budget", "continuity"]
    assert len({CODES[family] for family in families}) == 3
    for seed in (True, 1.0, "270100", None):
        with pytest.raises(ValueError):
            family_for_seed(seed)


def test_budget_selector_inclusive_order_empty_and_preservation():
    from Backend.Core.france.route_task_families import BUDGET_CODE, HELPER_CODE

    namespace = {}
    exec(HELPER_CODE + "\n" + BUDGET_CODE, namespace)
    base = [["A", "B", "D"], ["A", "C", "D"], ["A", "D"]]
    for routes in permutations(base):
        paths = list(routes)
        for costs in ([2, 2, 5], [9, 4, 1]):
            for budget in (0, 1, 2, 4, 5, 9, 10):
                for closed in ([], [["D", "A"]], [["A", "B"], ["C", "D"]]):
                    original = deepcopy((paths, costs, closed))
                    blocked = {frozenset(edge) for edge in closed}
                    expected = [
                        i
                        for i, path in enumerate(paths)
                        if costs[i] <= budget
                        and {frozenset(edge) for edge in pairwise(path)}.isdisjoint(
                            blocked
                        )
                    ]
                    assert (
                        namespace["trajets_admissibles"](paths, costs, closed, budget)
                        == expected
                    )
                    assert (paths, costs, closed) == original
    assert namespace["trajets_admissibles"]([], [], [], 10) == []


def test_continuity_matches_independent_first_intersection_oracle():
    from Backend.Core.france.route_task_families import CONTINUITY_CODE, HELPER_CODE

    namespace = {}
    exec(HELPER_CODE + "\n" + CONTINUITY_CODE, namespace)
    routes = [["A", "B", "D"], ["A", "C", "D"], ["A", "D"]]
    events = [["B", "A"], ["A", "D"], ["D", "C"], ["X", "Y"]]
    for order in permutations(events):
        for size in range(5):
            closures = list(order[:size])
            for paths in (routes, routes[:1], []):
                original = deepcopy((paths, closures))
                # the first event hitting each route independently, then the
                # latest of those events. Different derivation from stage loops
                hits = [
                    next(
                        (
                            i + 1
                            for i, edge in enumerate(closures)
                            if frozenset(edge) in {frozenset(e) for e in pairwise(path)}
                        ),
                        None,
                    )
                    for path in paths
                ]
                expected = 0 if not paths else None if None in hits else max(hits)
                assert namespace["premiere_coupure"](paths, closures) == expected
                assert (paths, closures) == original
    assert namespace["premiere_coupure"](routes, [events[0], events[0]]) is None


@pytest.mark.parametrize("seed", range(270100, 270112))
def test_printed_family_cases_match_fixed_reference_code(seed):
    from Backend.Core.france.graph_two_outage_contract import (
        build_graph_two_outage_contract,
    )
    from Backend.Core.france.route_task_families import (
        CODES,
        HELPER_CODE,
        family_expected,
    )

    data = build_graph_two_outage_contract(seed).to_dict()
    facts = family_expected(data)
    namespace = {}
    exec(HELPER_CODE + "\n" + CODES[facts["family"]], namespace)
    routes, costs = facts["base"]["routes"], facts["base"]["costs"]
    closed = facts["closures"][:2]
    if facts["family"] == "minimum":
        actual = namespace["meilleur_trajet"](routes, costs, closed)
    elif facts["family"] == "budget":
        actual = namespace["trajets_admissibles"](
            routes, costs, closed, facts["budget"]
        )
    else:
        actual = namespace["premiere_coupure"](routes, facts["closures"])
    assert actual == facts["result"]
    assert all(set(b).issubset(a) for a, b in pairwise(facts["survivors_by_stage"]))
