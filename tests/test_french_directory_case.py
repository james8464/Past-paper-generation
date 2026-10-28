# Independent expected traces for a shared, cyclic directory-object graph.

from copy import deepcopy

import pytest


def source():
    from Backend.Core.france.directory_case import build_case

    return build_case(270104)


def test_case_has_an_isolated_node_a_shared_child_and_a_cycle():
    case = source()
    assert case["nodes"] == [
        ["r", "Accueil"],
        ["a", "Archives"],
        ["b", "Archives"],
        ["c", "Plans"],
        ["d", "Tests"],
        ["e", "Notes"],
    ]
    assert case["links"] == [
        ["r", "a"],
        ["r", "b"],
        ["a", "c"],
        ["b", "c"],
        ["c", "d"],
        ["d", "a"],
    ]


def test_objects_share_identity_and_do_not_share_unrelated_child_lists():
    from Backend.Core.france.directory_case import build_objects

    case = source()
    before = deepcopy(case)
    nodes = build_objects(case)
    assert nodes["a"].enfants[0] is nodes["b"].enfants[0]
    assert nodes["d"].enfants[0] is nodes["a"]
    assert nodes["a"].nom == nodes["b"].nom
    assert nodes["a"].identifiant != nodes["b"].identifiant
    assert nodes["e"].enfants == []
    assert nodes["e"].enfants is not nodes["a"].enfants
    assert case == before


def test_recursive_traversal_terminates_on_the_cycle_and_visits_shared_child_once():
    from Backend.Core.france.directory_case import build_objects, explorer

    nodes = build_objects(source())
    seen = []
    explorer(nodes["r"], seen)
    assert seen == ["r", "a", "c", "d", "b"]
    assert "e" not in seen
    again = []
    explorer(nodes["r"], again)
    assert again == seen


@pytest.mark.parametrize(
    "start,target,expected",
    [
        ("r", "r", 0),
        ("r", "b", 1),
        ("r", "d", 3),
        ("r", "e", None),
        ("a", "b", None),
        ("d", "c", 2),
    ],
)
def test_shortest_link_count_is_not_recursive_visit_position(start, target, expected):
    from Backend.Core.france.directory_case import build_objects, distance_minimale

    nodes = build_objects(source())
    assert distance_minimale(nodes[start], target) == expected


def test_new_link_changes_reachability_without_rewriting_existing_objects():
    from Backend.Core.france.directory_case import build_objects, distance_minimale

    nodes = build_objects(source())
    nodes["d"].relier(nodes["e"])
    assert distance_minimale(nodes["r"], "e") == 4
    nodes["r"].relier(nodes["e"])
    assert distance_minimale(nodes["r"], "e") == 1
    assert [node.identifiant for node in nodes["a"].enfants] == ["c"]


def test_linking_the_same_object_twice_does_not_duplicate_an_arc():
    from Backend.Core.france.directory_case import build_objects

    nodes = build_objects(source())
    nodes["r"].relier(nodes["a"])
    assert [node.identifiant for node in nodes["r"].enfants] == ["a", "b"]


def test_every_shortest_distance_agrees_with_independent_matrix_relaxation():
    from Backend.Core.france.directory_case import build_objects, distance_minimale

    case = source()
    ids = [row[0] for row in case["nodes"]]
    distances = {(a, b): (0 if a == b else 100) for a in ids for b in ids}
    for a, b in case["links"]:
        distances[a, b] = 1
    for middle in ids:
        for a in ids:
            for b in ids:
                distances[a, b] = min(
                    distances[a, b], distances[a, middle] + distances[middle, b]
                )
    nodes = build_objects(case)
    for a in ids:
        for b in ids:
            expected = distances[a, b] if distances[a, b] < 100 else None
            assert distance_minimale(nodes[a], b) == expected


def test_cases_do_not_leak_mutations_or_claim_seed_based_variety():
    first = source()
    first["nodes"][0][1] = "Changed"
    assert source()["nodes"][0][1] == "Accueil"
    from Backend.Core.france.directory_case import build_case

    assert build_case(-(2**63)) == build_case(2**63 - 1) == source()


@pytest.mark.parametrize("seed", [True, 1.5, "270104", -(2**63) - 1, 2**63])
def test_case_refuses_invalid_seed_types_and_out_of_range_values(seed):
    from Backend.Core.france.directory_case import build_case

    with pytest.raises(ValueError):
        build_case(seed)
