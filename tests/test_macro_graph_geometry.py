"""Displayed equilibria and fiscal areas must belong to their plotted curves."""

from pathlib import Path
from types import SimpleNamespace

import matplotlib.pyplot as plt
import numpy as np
import pytest
from pastpapergen import render_pdf
from pastpapergen.models import GraphParams

from Backend.Core.overlay import graphs

ROOT = Path(__file__).resolve().parents[1]
assert Path(graphs.__file__).resolve() == ROOT / "Backend/Core/overlay/graphs.py"
assert Path(render_pdf.__file__).resolve() == (
    ROOT / "Resources/economics/edexcel-a/generator/pastpapergen/render_pdf.py"
)


def capture(monkeypatch, function, **kwargs):
    result = {}

    def inspect(*_args, **_kwargs):
        ax = plt.gca()
        result["lines"] = {
            line.get_label(): line.get_xydata().copy()
            for line in ax.lines
            if not line.get_label().startswith("_")
        }
        result["markers"] = [
            line.get_xydata().copy() for line in ax.lines if line.get_marker() == "o"
        ]
        result["areas"] = {
            patch.get_label(): patch.get_xy().copy()
            for patch in ax.patches
            if hasattr(patch, "get_xy")
        }
        legend = ax.get_legend()
        if legend is not None:
            result["legend_anchor"] = (
                legend.get_bbox_to_anchor().transformed(ax.transAxes.inverted()).bounds
            )

    monkeypatch.setattr(plt, "savefig", inspect)
    path = Path(function(**kwargs))
    path.unlink(missing_ok=True)
    return result


def at(points, quantity):
    return np.interp(quantity, points[:, 0], points[:, 1])


@pytest.mark.parametrize(
    "kind,default_price,default_output,supply",
    [
        ("ad_as_diagram", 100, 100, "AS"),
        ("keynesian_as_diagram", 110, 110, "AS (Keynesian)"),
    ],
)
@pytest.mark.parametrize("custom", [False, True])
def test_macro_marker_is_the_actual_intersection(
    monkeypatch, kind, default_price, default_output, supply, custom
):
    params = {"eq_price": 73, "eq_output": 124} if custom else None
    price, output = (73, 124) if custom else (default_price, default_output)
    data = capture(monkeypatch, render_pdf._GRAPH_FUNCS[kind], params=params)
    assert data["markers"][0][0] == pytest.approx([output, price])
    assert at(data["lines"]["AD"], output) == pytest.approx(price)
    assert at(data["lines"][supply], output) == pytest.approx(price)


@pytest.mark.parametrize(
    "kind", ["ad_as_diagram", "keynesian_as_diagram", "macro_chart"]
)
def test_public_quantity_parameter_is_not_ignored(monkeypatch, kind):
    data = capture(
        monkeypatch,
        render_pdf._GRAPH_FUNCS[kind],
        params={"eq_price": 80, "eq_quantity": 120, "kind": kind},
    )
    assert data["markers"][0][0] == pytest.approx([120, 80])
    for points in data["lines"].values():
        assert at(points, 120) == pytest.approx(80)


def area(vertices):
    xs, ys = vertices[:, 0], vertices[:, 1]
    return abs(np.dot(xs, np.roll(ys, 1)) - np.dot(ys, np.roll(xs, 1))) / 2


@pytest.mark.parametrize("kind", ["tax", "subsidy"])
@pytest.mark.parametrize("custom", [False, True])
def test_fiscal_rectangle_and_deadweight_triangle_match_the_same_market(
    monkeypatch, kind, custom
):
    price, quantity, amount = (80, 120, 12) if custom else (60, 100, 15)
    params = {"eq_price": price, "eq_quantity": quantity, "tax_amount": amount}
    data = capture(monkeypatch, graphs.tax_subsidy_diagram, kind=kind, params=params)
    direction = -1 if kind == "tax" else 1
    # Demand and supply slopes are 2P/(3Q) and 5P/(6Q), respectively.
    new_quantity = quantity + direction * amount / (1.5 * price / quantity)
    consumer_price = price - (new_quantity - quantity) * (2 * price / (3 * quantity))
    producer_price = consumer_price + (amount if kind == "subsidy" else -amount)
    fiscal = data["areas"]["Tax revenue" if kind == "tax" else "Subsidy cost"]
    assert sorted(set(fiscal[:, 0])) == pytest.approx([0, new_quantity])
    assert min(fiscal[:, 1]) == pytest.approx(min(consumer_price, producer_price))
    assert max(fiscal[:, 1]) == pytest.approx(max(consumer_price, producer_price))
    assert area(fiscal) == pytest.approx(amount * new_quantity)
    assert area(data["areas"]["DWL"]) == pytest.approx(
        0.5 * amount * abs(quantity - new_quantity)
    )
    assert data["markers"][0][0] == pytest.approx([new_quantity, consumer_price])
    assert at(data["lines"]["D"], new_quantity) == pytest.approx(consumer_price)
    shifted = "S1 (after tax)" if kind == "tax" else "S1 (after subsidy)"
    assert at(data["lines"][shifted], new_quantity) == pytest.approx(consumer_price)
    assert at(data["lines"]["S0"], quantity) == pytest.approx(price)


def test_ppf_marker_is_on_the_frontier_not_an_unrelated_array_index(monkeypatch):
    data = capture(monkeypatch, graphs.ppf_diagram)
    quantity, marked_y = data["markers"][0][0]
    assert quantity == 30
    assert marked_y == pytest.approx(100 * (1 - (quantity / 100) ** 0.6))


def test_ppf_public_dispatch_accepts_its_declared_kind(monkeypatch):
    data = capture(
        monkeypatch,
        render_pdf._GRAPH_FUNCS["production_possibility_frontier"],
        params={"kind": "ppf"},
    )
    assert data["markers"][0][0][0] == 30


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf"), True])
@pytest.mark.parametrize(
    "kind", ["ad_as_diagram", "keynesian_as_diagram", "tax_subsidy_diagram"]
)
def test_invalid_market_scales_refuse_before_creating_axes(monkeypatch, value, kind):
    monkeypatch.setattr(
        graphs, "_ax", lambda: pytest.fail("invalid geometry reached axes")
    )
    with pytest.raises(ValueError):
        render_pdf._GRAPH_FUNCS[kind](params={"eq_price": value, "eq_quantity": 100})


def test_conflicting_output_aliases_refuse_before_creating_axes(monkeypatch):
    monkeypatch.setattr(
        graphs, "_ax", lambda: pytest.fail("conflicting facts reached axes")
    )
    with pytest.raises(ValueError):
        graphs.ad_as_diagram(params={"eq_output": 90, "eq_quantity": 120})


def test_numeric_source_parameters_survive_an_empty_optional_kind(monkeypatch):
    calls = []
    monkeypatch.setitem(
        render_pdf._GRAPH_FUNCS,
        "ad_as_diagram",
        lambda params=None: calls.append(params) or "owned-placeholder.png",
    )
    monkeypatch.setattr(render_pdf, "_GRAPH_IMG_CACHE", [])
    parameters = GraphParams(eq_price=80, eq_quantity=120)
    render_pdf._draw_economics_graph(
        SimpleNamespace(drawImage=lambda *_args, **_kwargs: None),
        0,
        400,
        "ad_as_diagram",
        parameters,
    )
    expected = {"eq_price": 80, "eq_quantity": 120}
    assert calls == [expected]
    source = SimpleNamespace(
        source_instance=None,
        stimulus_kind="ad_as_diagram",
        source_text="Owned illustrative market",
        graph_params=parameters,
    )
    assert render_pdf.candidate_stimulus_data(source)["graph_params"] == expected


@pytest.mark.parametrize("value", [0, -1, True, float("nan"), float("inf"), 60])
def test_invalid_intervention_refuses_before_axes(monkeypatch, value):
    monkeypatch.setattr(
        graphs, "_ax", lambda: pytest.fail("invalid intervention reached axes")
    )
    with pytest.raises(ValueError):
        graphs.tax_subsidy_diagram(params={"tax_amount": value})


@pytest.mark.parametrize(
    "function",
    [graphs.ad_as_diagram, graphs.keynesian_ad_as_diagram, graphs.tax_subsidy_diagram],
)
def test_curve_legends_do_not_cover_the_plotted_region(monkeypatch, function):
    assert capture(monkeypatch, function)["legend_anchor"][1] > 1
