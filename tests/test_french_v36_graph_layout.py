"""Small real-PDF regressions for generic French presentation boundaries."""

import pymupdf
import pytest

from Backend.Core.france import rendering
from Backend.Core.france.graph_layout import graph_layout
from Backend.Core.france.llm_pdf import validate_llm_pdf
from Backend.Core.france.nsi import NSIWeightedGraphMaterial
from Backend.Core.france.print_policy import V36_LEGACY_PRINT_POLICY
from Backend.Core.render_transaction import render_pdf_atomically
from tests.test_french_llm_pdf import exercises, render
from tests.test_french_llm_pipeline import Client, generate


def with_graph():
    source = exercises()
    graph = NSIWeightedGraphMaterial(
        kind="weighted_graph",
        id="test_net",
        title="Graphe de contrôle",
        nodes=("GX", "GY", "GZ"),
        edges=(("GX", "GY", 137), ("GY", "GX", 251), ("GY", "GZ", 389)),
        directed=True,
    )
    source[0] = source[0].model_copy(
        update={"materials": (*source[0].materials, graph)}
    )
    return source


def spans(pdf, labels):
    return [
        span
        for page in pdf
        for span in page.get_texttrace()
        if "".join(chr(char[0]) for char in span["chars"]) in labels
    ]


def test_reciprocal_weight_labels_remain_visibly_separate(tmp_path):
    from Backend.Core.france.llm_pdf import validate_llm_pdf

    path = tmp_path / "reciprocal-before-fix.pdf"
    source = with_graph()
    render(path, source)
    # Baseline vector/text validation alone is not a visible-label guarantee.
    validate_llm_pdf(path, source, correction=False)
    with pymupdf.open(path) as pdf:
        weights = spans(pdf, {"137", "251"})
        assert len(weights) == 2
        first, second = (pymupdf.Rect(span["bbox"]) for span in weights)
        assert not first.intersects(second), (
            "reciprocal labels occupy the same position"
        )


def test_enlarged_graph_nodes_and_weights_actually_enlarge(tmp_path):
    sizes = []
    for large_print in (False, True):
        path = tmp_path / f"graph-size-{large_print}-before-fix.pdf"
        render(path, with_graph(), large_print=large_print)
        with pymupdf.open(path) as pdf:
            nodes = spans(pdf, {"GX", "GY", "GZ"})
            weights = spans(pdf, {"137", "251", "389"})
            assert len(nodes) == len(weights) == 3
            sizes.append(
                (min(s["size"] for s in nodes), min(s["size"] for s in weights))
            )
    assert sizes[1][0] > sizes[0][0]
    assert sizes[1][1] > sizes[0][1]
    assert min(sizes[1]) >= 14


@pytest.mark.parametrize("large_print", [False, True])
@pytest.mark.parametrize("correction", [False, True])
def test_common_room_names_fit_measured_circles_and_all_source_data(
    tmp_path, large_print, correction
):
    source = with_graph()
    graph = (
        source[0]
        .materials[-1]
        .model_copy(
            update={
                "nodes": ("Accueil", "Analyse", "Reserve"),
                "edges": (
                    ("Accueil", "Analyse", 137),
                    ("Analyse", "Accueil", 251),
                    ("Analyse", "Reserve", 389),
                ),
            }
        )
    )
    source[0] = source[0].model_copy(
        update={"materials": (*source[0].materials[:-1], graph)}
    )
    geometry = graph_layout(graph, large_print)
    assert geometry.height <= 460
    if large_print:
        assert geometry.font_size >= 14 and geometry.radius > 24
    path = tmp_path / f"rooms-{large_print}-v2.pdf"
    render(path, source, large_print=large_print, correction=correction)
    validate_llm_pdf(path, source, correction=correction, large_print=large_print)
    with pymupdf.open(path) as pdf:
        assert len(spans(pdf, {"Accueil", "Analyse", "Reserve"})) == 3
        weights = spans(pdf, {"137", "251"})
        assert not pymupdf.Rect(weights[0]["bbox"]).intersects(
            pymupdf.Rect(weights[1]["bbox"])
        )


def test_unfit_geometry_refuses_before_independent_review(tmp_path):
    def mutate(raw):
        nodes = [f"SalleTresLongueNumero{i:02}" for i in range(12)]
        raw["materials"].append(
            {
                "kind": "weighted_graph",
                "id": "trop_dense",
                "title": "Noms trop longs",
                "nodes": nodes,
                "edges": [[nodes[i], nodes[i + 1], i + 1] for i in range(11)],
                "directed": True,
            }
        )

    client = Client(mutate=mutate)
    with pytest.raises(ValueError, match="deux tentatives"):
        generate(tmp_path, client)
    assert len(client.requests) == 2
    assert all("id" in request.schema["properties"] for request in client.requests)


def test_arbitrary_shifted_edge_is_not_accepted_as_a_valid_route(tmp_path, monkeypatch):
    original = rendering.Line
    monkeypatch.setattr(
        rendering,
        "Line",
        lambda x1, y1, x2, y2, **kwargs: original(x1 + 2, y1, x2, y2, **kwargs),
    )
    source = with_graph()
    path = tmp_path / "wrong-edge.pdf"
    render(path, source)
    with pytest.raises(ValueError, match="arcs"):
        validate_llm_pdf(path, source, correction=False)


def test_wrong_label_position_cannot_hide_behind_correct_text(tmp_path, monkeypatch):
    original = rendering.String

    def shifted(x, y, text, **kwargs):
        return original(x + (2 if text == "137" else 0), y, text, **kwargs)

    monkeypatch.setattr(rendering, "String", shifted)
    source = with_graph()
    path = tmp_path / "wrong-label.pdf"
    render(path, source)
    with pytest.raises(ValueError, match="Poids"):
        validate_llm_pdf(path, source, correction=False)


@pytest.mark.parametrize("large_print", [False, True])
def test_retained_v1_graph_geometry_and_type_sizes_are_unchanged(tmp_path, large_print):
    source = with_graph()
    path = tmp_path / "legacy-v1.pdf"
    render_pdf_atomically(
        path,
        lambda target: rendering.render_assessment(
            target,
            source,
            correction=False,
            large_print=large_print,
            human_readable_graph_titles=True,
            coherent_material_flow=True,
            print_policy=V36_LEGACY_PRINT_POLICY,
        ),
        role="question_paper",
        language="fr-FR",
    )
    validate_llm_pdf(
        path,
        source,
        correction=False,
        large_print=large_print,
        print_policy=V36_LEGACY_PRINT_POLICY,
    )
    with pymupdf.open(path) as pdf:
        assert {span["size"] for span in spans(pdf, {"GX", "GY", "GZ"})} == {8}
        weights = spans(pdf, {"137", "251"})
        assert {span["size"] for span in weights} == {9}
        # Historical rendering is replayed, not silently retrofitted as v2.
        assert weights[0]["bbox"] == weights[1]["bbox"]


def test_small_room_names_with_spaces_are_measured_and_matched(tmp_path):
    source = with_graph()
    graph = (
        source[0]
        .materials[-1]
        .model_copy(
            update={
                "nodes": ("Le Port", "Analyse", "Reserve"),
                "edges": (
                    ("Le Port", "Analyse", 137),
                    ("Analyse", "Le Port", 251),
                    ("Analyse", "Reserve", 389),
                ),
            }
        )
    )
    source[0] = source[0].model_copy(
        update={"materials": (*source[0].materials[:-1], graph)}
    )
    path = tmp_path / "room-name-spaces.pdf"
    render(path, source, large_print=True)
    validate_llm_pdf(path, source, correction=False, large_print=True)


def test_bounded_taller_figure_admits_common_seven_room_graph(tmp_path):
    names = (
        "Accueil",
        "Analyse",
        "Reserve",
        "Cuisine",
        "Atelier",
        "Bureau",
        "Archives",
    )
    graph = NSIWeightedGraphMaterial(
        kind="weighted_graph",
        id="rooms_test",
        title="Circulation des salles",
        nodes=names,
        edges=tuple(
            (names[a], names[b], i + 1)
            for i, (a, b) in enumerate(
                ((0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (0, 3), (1, 4), (2, 6))
            )
        ),
        directed=False,
    )
    geometry = graph_layout(graph, True)
    assert 340 < geometry.height <= 460
    assert geometry.font_size == 14
    source = with_graph()
    source[0] = source[0].model_copy(
        update={"materials": (*source[0].materials[:-1], graph)}
    )
    path = tmp_path / "seven-room-enlarged.pdf"
    render(path, source, large_print=True)
    validate_llm_pdf(path, source, correction=False, large_print=True)


def test_real_route_never_passes_through_unrelated_named_node(tmp_path):
    from math import hypot

    names = tuple(f"Accueil{letter}" for letter in "ABCDEFGH")
    graph = NSIWeightedGraphMaterial(
        kind="weighted_graph",
        id="skip_room",
        title="Saut de salle",
        nodes=names,
        edges=((names[0], names[2], 137),),
        directed=False,
    )
    geometry = graph_layout(graph, True)
    source = with_graph()
    source[0] = source[0].model_copy(
        update={"materials": (*source[0].materials[:-1], graph)}
    )
    path = tmp_path / "unrelated-node-route.pdf"
    render(path, source, large_print=True)
    validate_llm_pdf(path, source, correction=False, large_print=True)
    start, end = geometry.routes[0].start, geometry.routes[0].end
    point = geometry.positions[names[1]]
    vx, vy = end[0] - start[0], end[1] - start[1]
    t = max(
        0,
        min(
            1,
            ((point[0] - start[0]) * vx + (point[1] - start[1]) * vy)
            / (vx * vx + vy * vy),
        ),
    )
    distance = hypot(point[0] - start[0] - t * vx, point[1] - start[1] - t * vy)
    assert distance >= geometry.radius + 2, "edge crosses an unrelated node"


@pytest.mark.parametrize(
    "point,start,end,expected",
    [
        ((5, 2), (0, 0), (10, 0), 2),
        ((-3, 4), (0, 0), (10, 0), 5),
        ((13, 4), (0, 0), (10, 0), 5),
        ((5, 5), (0, 0), (10, 10), 0),
    ],
)
def test_segment_clearance_uses_clamped_actual_route(point, start, end, expected):
    from Backend.Core.france.graph_layout import _segment_distance

    assert _segment_distance(point, start, end) == pytest.approx(expected)
    assert _segment_distance(point, end, start) == pytest.approx(expected)


def test_reciprocal_offset_that_cannot_clear_neighbour_refuses():
    from Backend.Core.france.code_layout import CodeLayoutError

    names = tuple(f"Accueil{letter}" for letter in "ABCDEFGH")
    graph = NSIWeightedGraphMaterial(
        kind="weighted_graph",
        id="no_clearance",
        title="Arcs réciproques trop proches",
        nodes=names,
        edges=((names[0], names[2], 137), (names[2], names[0], 251)),
        directed=True,
    )
    with pytest.raises(CodeLayoutError, match="arc traverse"):
        graph_layout(graph, True)
