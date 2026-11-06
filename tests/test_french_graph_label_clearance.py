"""Owned graph geometry controls, not complete-paper qualification."""

from dataclasses import asdict
from math import hypot

import pytest

from Backend.Core.france import graph_layout as subject
from Backend.Core.france.nsi import NSIWeightedGraphMaterial


def crossing_graph():
    return NSIWeightedGraphMaterial(
        kind="weighted_graph",
        id="owned",
        title="Owned crossing edges",
        nodes=("A", "B", "C", "D"),
        edges=(("A", "C", 11), ("B", "D", 22)),
        directed=True,
    )


def horizontal_route_crosses_box(route, box):
    assert route.start[1] == pytest.approx(route.end[1])
    left, right = sorted((route.start[0], route.end[0]))
    return left < box[2] and right > box[0] and box[1] <= route.start[1] <= box[3]


@pytest.mark.parametrize("large_print", [False, True])
def test_owned_fixture_reproduces_legacy_opaque_label_occlusion(large_print):
    layout = subject.graph_layout(crossing_graph(), large_print)
    assert horizontal_route_crosses_box(layout.routes[1], layout.routes[0].label_box)


@pytest.mark.parametrize("large_print", [False, True])
def test_opaque_weight_box_never_hides_foreign_crossing_edge(large_print):
    layout = subject.graph_layout(
        crossing_graph(), large_print, avoid_foreign_edges=True
    )
    assert not horizontal_route_crosses_box(
        layout.routes[1], layout.routes[0].label_box
    )


@pytest.mark.parametrize(
    ("large_print", "legacy_box"),
    [
        (False, (199.876953125, 81.4140625, 217.0, 98.5859375)),
        (True, (195.427734375, 99.1796875, 217.0, 120.8203125)),
    ],
)
def test_legacy_default_preserves_prior_graph_and_label_geometry(
    large_print, legacy_box
):
    material = crossing_graph()
    default = subject.graph_layout(material, large_print)
    legacy = subject.graph_layout(material, large_print, avoid_foreign_edges=False)
    assert asdict(default) == asdict(legacy)
    assert legacy.routes[0].label_box == pytest.approx(legacy_box)
    assert horizontal_route_crosses_box(legacy.routes[1], legacy.routes[0].label_box)


@pytest.mark.parametrize("large_print", [False, True])
def test_new_layout_moves_only_labels_not_source_connections(large_print):
    material = crossing_graph()
    old = subject.graph_layout(material, large_print)
    new = subject.graph_layout(material, large_print, avoid_foreign_edges=True)
    assert (new.width, new.height, new.radius, new.positions) == (
        old.width,
        old.height,
        old.radius,
        old.positions,
    )
    for first, second in zip(old.routes, new.routes, strict=True):
        assert (first.start, first.end, first.arrow, first.label) == (
            second.start,
            second.end,
            second.arrow,
            second.label,
        )
    for index, route in enumerate(new.routes):
        left, bottom, right, top = route.label_box
        centre = ((left + right) / 2, (bottom + top) / 2)
        dx, dy = route.end[0] - route.start[0], route.end[1] - route.start[1]
        length = hypot(dx, dy)
        fraction = (
            (centre[0] - route.start[0]) * dx + (centre[1] - route.start[1]) * dy
        ) / length**2
        assert (
            min(abs(fraction - anchor) for anchor in (0.5, 0.33, 0.67, 0.2, 0.8)) < 1e-9
        )
        clearance = abs(dy / length) * (right - left) / 2
        clearance += abs(dx / length) * (top - bottom) / 2 + 3
        distance = subject._segment_distance(centre, route.start, route.end)
        assert distance == pytest.approx(clearance)
        # This crossing fixture's weights remain closer to their own edges,
        # rather than being visually reassigned to the other connection.
        assert all(
            distance < subject._segment_distance(centre, other.start, other.end)
            for other_index, other in enumerate(new.routes)
            if other_index != index
        )


@pytest.mark.parametrize("large_print", [False, True])
def test_uncongested_control_keeps_existing_placement(large_print):
    material = crossing_graph().model_copy(
        update={"edges": (("A", "B", 11), ("B", "C", 22))}
    )
    assert asdict(subject.graph_layout(material, large_print)) == asdict(
        subject.graph_layout(material, large_print, avoid_foreign_edges=True)
    )


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        ((-5, 5), (15, 5), True),
        ((5, -5), (5, 15), True),
        ((-5, -5), (15, 15), True),
        ((-5, 0), (15, 0), True),
        ((-5, -5), (0, 0), True),
        ((-5, -1), (15, -1), False),
        ((-5, 5), (-1, 5), False),
        ((5, 5), (5, 5), True),
        ((-1, -1), (-1, -1), False),
    ],
)
def test_segment_box_check_uses_actual_finite_segment(start, end, expected):
    assert subject._segment_hits_box(start, end, (0, 0, 10, 10), gap=0) is expected
    assert subject._segment_hits_box(end, start, (0, 0, 10, 10), gap=0) is expected


def test_segment_clearance_includes_the_edge_stroke():
    box = (0, 0, 10, 10)
    assert subject._segment_hits_box((-5, 12.5), (15, 12.5), box)
    assert not subject._segment_hits_box((-5, 12.7), (15, 12.7), box)


@pytest.mark.parametrize(
    ("box", "expected"),
    [
        ((1, 1, 2, 2), True),
        ((-1, -1, 11, 11), True),
        ((9, 9, 10, 10), False),
        ((11, 11, 12, 12), False),
        ((10, 0, 11, 1), True),
    ],
)
def test_arrow_clearance_uses_triangle_not_just_its_bounding_box(box, expected):
    arrow = ((0, 0), (10, 0), (0, 10))
    assert subject._arrow_hits_box(arrow, box, gap=0) is expected
    assert subject._arrow_hits_box(tuple(reversed(arrow)), box, gap=0) is expected


def test_undirected_edge_has_no_arrow_to_occlude():
    assert subject._arrow_hits_box((), (0, 0, 10, 10)) is False


@pytest.mark.parametrize("flag", [0, 1, "true", None])
def test_new_layout_policy_flag_is_strictly_boolean(flag):
    with pytest.raises(ValueError, match="booléenne"):
        subject.graph_layout(crossing_graph(), False, avoid_foreign_edges=flag)
