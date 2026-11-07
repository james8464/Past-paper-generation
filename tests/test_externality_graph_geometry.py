"""Externality labels, equilibria and welfare areas share the plotted market."""

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


def capture(monkeypatch, params):
    captured = {}

    def inspect():
        ax = plt.gca()
        captured["curves"] = {
            line.get_label(): line.get_xydata().copy()
            for line in ax.lines
            if line.get_label() in {"MPB", "MSB", "MPC", "MSC"}
        }
        captured["markers"] = [
            line.get_xydata()[0].copy() for line in ax.lines if line.get_marker() == "o"
        ]
        captured["dwl"] = next(
            patch.get_xy().copy() for patch in ax.patches if patch.get_label() == "DWL"
        )
        captured["limits"] = (ax.get_xlim(), ax.get_ylim())
        captured["legend_y"] = (
            ax.get_legend().get_bbox_to_anchor().transformed(ax.transAxes.inverted()).y0
        )
        plt.close()
        return "owned-externality.png"

    monkeypatch.setattr(graphs, "_save", inspect)
    before = copy.deepcopy(params)
    assert render_pdf._GRAPH_FUNCS["externality_diagram"](params=params) == (
        "owned-externality.png"
    )
    assert params == before
    return captured


@pytest.mark.parametrize("kind", ["negative", "positive"])
def test_all_named_curves_and_markers_use_the_same_market(monkeypatch, kind):
    data = capture(monkeypatch, {"kind": kind})
    curves = data["curves"]
    assert set(curves) == {"MPB", "MSB", "MPC", "MSC"}
    q_private = 88 / 1.08
    q_social = (68 if kind == "negative" else 110) / 1.08
    p_private = 100 - 0.6 * q_private
    p_social = (100 if kind == "negative" else 122) - 0.6 * q_social
    assert data["markers"][0] == pytest.approx([q_private, p_private])
    assert data["markers"][1] == pytest.approx([q_social, p_social])
    for label, intercept, slope in [
        ("MPB", 100, -0.6),
        ("MSB", 100 if kind == "negative" else 122, -0.6),
        ("MPC", 12, 0.48),
        ("MSC", 32 if kind == "negative" else 12, 0.48),
    ]:
        points = curves[label]
        assert points[:, 1] == pytest.approx(intercept + slope * points[:, 0])
    for marker, labels in zip(
        data["markers"], [("MPB", "MPC"), ("MSB", "MSC")], strict=True
    ):
        for label in labels:
            points = curves[label]
            assert np.interp(marker[0], points[:, 0], points[:, 1]) == pytest.approx(
                marker[1]
            )
        for coordinate, bounds in zip(marker, data["limits"], strict=True):
            assert bounds[0] < coordinate < bounds[1]


@pytest.mark.parametrize("kind,wedge", [("negative", 20), ("positive", 22)])
def test_deadweight_triangle_uses_both_benefit_cost_values_at_private_output(
    monkeypatch, kind, wedge
):
    data = capture(monkeypatch, {"kind": kind})
    private, social = data["markers"]
    expected = [social, private, [private[0], private[1] + wedge]]
    vertices = data["dwl"][:-1]
    assert np.array(sorted(map(tuple, vertices))) == pytest.approx(
        np.array(sorted(map(tuple, expected)))
    )
    xs, ys = vertices[:, 0], vertices[:, 1]
    area = abs(np.dot(xs, np.roll(ys, 1)) - np.dot(ys, np.roll(xs, 1))) / 2
    assert area == pytest.approx(0.5 * wedge * abs(private[0] - social[0]))
    assert area > 0


@pytest.mark.parametrize("kind", [None, "externality", "externality_diagram"])
def test_generic_public_kind_preserves_negative_default(monkeypatch, kind):
    params = {} if kind is None else {"kind": kind}
    data = capture(monkeypatch, params)
    assert data["markers"][1][0] < data["markers"][0][0]


def test_unknown_externality_kind_refuses_before_axes(monkeypatch):
    monkeypatch.setattr(graphs, "_ax", lambda: pytest.fail("invalid kind reached axes"))
    with pytest.raises(ValueError, match="externality kind"):
        render_pdf._GRAPH_FUNCS["externality_diagram"](params={"kind": "typo"})


@pytest.mark.parametrize("kind", ["negative", "positive"])
def test_externality_legend_cannot_cross_cost_or_benefit_curves(monkeypatch, kind):
    assert capture(monkeypatch, {"kind": kind})["legend_y"] > 1
