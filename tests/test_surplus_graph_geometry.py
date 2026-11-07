"""Public surplus source parameters must describe the displayed welfare areas."""

import copy
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest
from pastpapergen import render_pdf

from Backend.Core.overlay import graphs

ROOT = Path(__file__).resolve().parents[1]
for module, source_path, bundle_path in (
    (graphs, "Backend/Core/overlay/graphs.py", "Backend/Core/overlay/graphs.py"),
    (
        render_pdf,
        "Resources/economics/edexcel-a/generator/pastpapergen/render_pdf.py",
        "pastpapergen/render_pdf.py",
    ),
):
    origin = module.__spec__.origin
    if getattr(sys, "frozen", False):
        expected = Path(sys._MEIPASS) / bundle_path
        assert Path(origin).resolve() == expected.resolve()
        assert Path(module.__file__).resolve() == expected.resolve()
    elif "!PYZ/" in origin:
        archive_path, name = origin.split("!PYZ/", 1)
        assert name == module.__name__
        assert Path(archive_path).is_absolute() and Path(archive_path).is_file()
        assert Path(archive_path).name == "KeldinBackend"
        assert module.__loader__ is module.__spec__.loader
        assert type(module.__loader__).__name__ == "ArchivedOwnedImports"
    else:
        assert Path(origin).resolve() == ROOT / source_path
        assert Path(module.__file__).resolve() == ROOT / source_path


def capture(monkeypatch, kind, params, **kwargs):
    captured = {}

    def inspect():
        ax = plt.gca()
        captured["curves"] = {
            line.get_label(): line.get_xydata().copy()
            for line in ax.lines
            if line.get_label() in {"D", "S"}
        }
        captured["marker"] = next(
            line.get_xydata()[0].copy() for line in ax.lines if line.get_marker() == "o"
        )
        captured["areas"] = {
            collection.get_label(): collection.get_paths()[0].vertices.copy()
            for collection in ax.collections
        }
        captured["limits"] = (ax.get_xlim(), ax.get_ylim())
        captured["legend_y"] = (
            ax.get_legend().get_bbox_to_anchor().transformed(ax.transAxes.inverted()).y0
        )
        ax.figure.canvas.draw()
        renderer = ax.figure.canvas.get_renderer()
        captured["labels_inside_figure"] = all(
            ax.figure.bbox.contains(*point)
            for text in ax.texts
            for point in text.get_window_extent(renderer).get_points()
        )
        plt.close()
        return "owned-surplus.png"

    monkeypatch.setattr(graphs, "_save", inspect)
    before = copy.deepcopy(params)
    assert render_pdf._GRAPH_FUNCS[kind](params=params, **kwargs) == "owned-surplus.png"
    assert params == before
    return captured


@pytest.mark.parametrize(
    "kind", ["consumer_surplus_diagram", "producer_surplus_diagram"]
)
@pytest.mark.parametrize("price,quantity", [(55, 70), (80, 120), (20, 300)])
def test_public_equilibrium_and_surplus_share_curves(
    monkeypatch, kind, price, quantity
):
    data = capture(monkeypatch, kind, {"eq_price": price, "eq_quantity": quantity})
    assert data["marker"] == pytest.approx([quantity, price])
    for points in data["curves"].values():
        assert np.interp(quantity, points[:, 0], points[:, 1]) == pytest.approx(price)
    for name, vertices in data["areas"].items():
        assert name in {"CS", "PS"}
        assert min(vertices[:, 0]) == 0
        assert max(vertices[:, 0]) == pytest.approx(quantity)
        assert min(vertices[:, 1]) >= 0
        xs, ys = vertices[:, 0], vertices[:, 1]
        area = abs(np.dot(xs, np.roll(ys, 1)) - np.dot(ys, np.roll(xs, 1))) / 2
        curve = data["curves"]["D" if name == "CS" else "S"]
        height = abs(curve[0, 1] - price)
        assert area == pytest.approx(0.5 * quantity * height)
        assert area > 0
    for coordinate, bounds in zip(data["marker"], data["limits"], strict=True):
        assert bounds[0] < coordinate < bounds[1]
    assert data["labels_inside_figure"]


def test_default_surplus_marker_lies_on_both_curves(monkeypatch):
    data = capture(monkeypatch, "consumer_surplus_diagram", None)
    quantity, price = data["marker"]
    assert [quantity, price] == pytest.approx([70, 55])
    for points in data["curves"].values():
        assert np.interp(quantity, points[:, 0], points[:, 1]) == pytest.approx(price)


@pytest.mark.parametrize("key", ["eq_price", "eq_quantity", "price", "quantity"])
@pytest.mark.parametrize(
    "value", [0, -1, True, float("nan"), float("inf"), 1e308, 1e-320, "bad"]
)
def test_invalid_or_nonrepresentable_scales_refuse_before_axes(monkeypatch, key, value):
    monkeypatch.setattr(
        graphs, "_ax", lambda: pytest.fail("invalid market reached axes")
    )
    with pytest.raises(ValueError):
        render_pdf._GRAPH_FUNCS["consumer_surplus_diagram"](params={key: value})


@pytest.mark.parametrize(
    "params",
    [
        {"price": 80, "quantity": 120},
        {"price": "80", "quantity": 120, "eq_price": 80, "eq_quantity": "120"},
    ],
)
def test_legacy_parameter_aliases_match_public_names(monkeypatch, params):
    data = capture(monkeypatch, "producer_surplus_diagram", params)
    assert data["marker"] == pytest.approx([120, 80])


@pytest.mark.parametrize(
    "params",
    [{"price": 80, "eq_price": 81}, {"quantity": 120, "eq_quantity": 121}],
)
def test_conflicting_aliases_refuse_before_axes(monkeypatch, params):
    monkeypatch.setattr(
        graphs, "_ax", lambda: pytest.fail("conflicting market reached axes")
    )
    with pytest.raises(ValueError, match="Conflicting"):
        render_pdf._GRAPH_FUNCS["producer_surplus_diagram"](params=params)


def test_direct_keyword_and_partial_public_parameters_remain_supported(monkeypatch):
    data = capture(
        monkeypatch, "producer_surplus_diagram", None, price=80, quantity=120
    )
    assert data["marker"] == pytest.approx([120, 80])
    data = capture(monkeypatch, "producer_surplus_diagram", {"eq_price": 80})
    assert data["marker"] == pytest.approx([70, 80])


def test_surplus_legend_cannot_cross_supply_curve(monkeypatch):
    assert capture(monkeypatch, "consumer_surplus_diagram", None)["legend_y"] > 1
