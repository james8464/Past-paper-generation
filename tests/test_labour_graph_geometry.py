"""The requested labour equilibrium must lie on both displayed curves."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest

from Backend.Core.overlay.graphs import labour_market_diagram


@pytest.mark.parametrize(
    "wage,employment", [(14, 100), (24, 240), (0.5, 8), (1e200, 1e200)]
)
def test_labour_curves_intersect_at_the_requested_equilibrium(
    monkeypatch, wage, employment
):
    captured = {}

    def inspect(*args, **kwargs):
        ax = plt.gca()
        captured.update(
            {line.get_label(): line.get_xydata().copy() for line in ax.lines}
        )
        captured["limits"] = (ax.get_xlim(), ax.get_ylim())

    monkeypatch.setattr(plt, "savefig", inspect)
    path = Path(labour_market_diagram(params={"wage": wage, "employment": employment}))
    try:
        for label in ("DL", "SL"):
            points = captured[label]
            assert np.interp(employment, points[:, 0], points[:, 1]) == pytest.approx(
                wage
            )
        assert captured["limits"][0][1] > employment
        assert captured["limits"][1][1] > wage
    finally:
        path.unlink(missing_ok=True)


@pytest.mark.parametrize("key", ["wage", "employment"])
@pytest.mark.parametrize(
    "value", [0, -1, float("nan"), float("inf"), True, "not a number"]
)
def test_invalid_labour_equilibrium_refuses_before_render(monkeypatch, key, value):
    monkeypatch.setattr(
        plt, "savefig", lambda *a, **k: pytest.fail("invalid geometry rendered")
    )
    with pytest.raises(ValueError, match="finite and positive"):
        labour_market_diagram(params={key: value})


def test_labour_symbolic_labels_do_not_cross_curves_or_numeric_ticks(monkeypatch):
    captured = {}

    def inspect(*args, **kwargs):
        figure = plt.gcf()
        figure.canvas.draw()
        renderer = figure.canvas.get_renderer()
        ax = plt.gca()
        for text in ax.texts:
            if text.get_text() not in {"We", "Le"}:
                continue
            bounds = text.get_window_extent(renderer)
            captured[text.get_text()] = any(
                line.get_path()
                .transformed(line.get_transform())
                .intersects_bbox(bounds, filled=False)
                for line in ax.lines
                if line.get_label() in {"DL", "SL"}
            ) or any(
                bounds.overlaps(tick.get_window_extent(renderer))
                for tick in [*ax.get_xticklabels(), *ax.get_yticklabels()]
            )

    monkeypatch.setattr(plt, "savefig", inspect)
    path = Path(labour_market_diagram(params={"wage": 24, "employment": 120}))
    path.unlink(missing_ok=True)
    assert captured == {"We": False, "Le": False}


def test_nonrepresentable_labour_slope_refuses_before_axes(monkeypatch):
    from Backend.Core.overlay import graphs

    monkeypatch.setattr(
        graphs, "_ax", lambda: pytest.fail("invalid slope reached Matplotlib")
    )
    with pytest.raises(ValueError, match="finite and positive"):
        labour_market_diagram(params={"wage": 1e100, "employment": 1e-300})
