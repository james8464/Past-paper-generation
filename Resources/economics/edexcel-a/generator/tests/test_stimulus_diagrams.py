"""A declared economic stimulus must depict that model, not a spare graph."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest
from pastpapergen import render_pdf
from pastpapergen import stimulus_diagrams as diagrams

from Backend.Core import family_adapter
from Backend.Core.overlay import graphs

assert Path(render_pdf.__file__).resolve() == (
    Path(__file__).resolve().parents[1] / "pastpapergen/render_pdf.py"
)
ROOT = Path(__file__).resolve().parents[5]
assert Path(graphs.__file__).resolve() == ROOT / "Backend/Core/overlay/graphs.py"
assert (
    Path(family_adapter.__file__).resolve() == ROOT / "Backend/Core/family_adapter.py"
)


def _capture(monkeypatch, kind, params=None):
    result = {}

    def inspect(*args, **kwargs):
        ax = plt.gca()
        result["lines"] = {
            line.get_label(): line.get_xydata().copy() for line in ax.lines
        }
        result["text"] = {
            text.get_text(): getattr(text, "xy", text.get_position())
            for text in ax.texts
        }
        result["xticks"] = [text.get_text() for text in ax.get_xticklabels()]
        result["yticks"] = [text.get_text() for text in ax.get_yticklabels()]

    monkeypatch.setattr(plt, "savefig", inspect)
    path = Path(render_pdf._GRAPH_FUNCS[kind](params=params))
    path.unlink(missing_ok=True)
    return result


@pytest.mark.parametrize(
    "minimum,limit,expected",
    [
        (True, 100, "Surplus"),
        (False, 60, "Shortage"),
        (True, 60, "Non-binding limit"),
        (False, 100, "Non-binding limit"),
    ],
)
def test_price_limits_keep_curves_and_distinguish_binding_controls(
    monkeypatch, minimum, limit, expected
):
    data = _capture(
        monkeypatch,
        "minimum_price_diagram" if minimum else "maximum_price_diagram",
        {"eq_price": 80, "eq_quantity": 100, "price_limit": limit},
    )
    assert expected in data["text"]
    if expected != "Non-binding limit":
        assert data["text"]["Qd"][0] == pytest.approx((160 - limit) * 100 / 80)
        assert data["text"]["Qs"][0] == pytest.approx((limit - 40) * 200 / 80)
    for label in ["D", "S"]:
        points = data["lines"][label]
        assert np.interp(100, points[:, 0], points[:, 1]) == pytest.approx(80)


def test_tariff_reduces_import_gap_without_shifting_domestic_supply(monkeypatch):
    data = _capture(
        monkeypatch,
        "tariff_diagram",
        {"eq_price": 80, "eq_quantity": 100, "world_price": 60, "tariff": 10},
    )
    assert data["text"]["Qs0"][0] == pytest.approx(50)
    assert data["text"]["Qd0"][0] == pytest.approx(125)
    assert data["text"]["Qs1"][0] == pytest.approx(75)
    assert data["text"]["Qd1"][0] == pytest.approx(112.5)
    assert "World price: 60; tariff: 10" in data["text"]


def test_monopsonist_hires_at_mcl_mrp_and_pays_acl(monkeypatch):
    data = _capture(
        monkeypatch, "monopsony_diagram", {"eq_price": 24, "eq_quantity": 120}
    )

    def at(label, x):
        return np.interp(x, data["lines"][label][:, 0], data["lines"][label][:, 1])

    assert at("ACL = supply", 120) == pytest.approx(24)
    assert at("MCL", 120) == pytest.approx(36)
    assert at("MRP", 120) == pytest.approx(36)
    assert at("MCL", 60) == pytest.approx(24)
    assert at("ACL = supply", 60) == pytest.approx(18)
    assert data["text"]["Lm"][0] < data["text"]["Lc"][0]


@pytest.mark.parametrize(
    "kind,price,quantity",
    [("money_market_diagram", 4, 120), ("exchange_rate_diagram", 1.2, 80)],
)
def test_supplied_equilibrium_is_honoured_and_printed(
    monkeypatch, kind, price, quantity
):
    data = _capture(monkeypatch, kind, {"eq_price": price, "eq_quantity": quantity})
    assert f"{price:g}" in data["yticks"]
    assert f"{quantity:g}" in data["xticks"]
    if kind == "money_market_diagram":
        assert np.all(data["lines"]["MS"][:, 0] == quantity)
        assert np.interp(
            quantity, data["lines"]["MD"][:, 0], data["lines"]["MD"][:, 1]
        ) == pytest.approx(price)
    else:
        for label in ["D (£)", "S (£)"]:
            assert np.interp(
                quantity, data["lines"][label][:, 0], data["lines"][label][:, 1]
            ) == pytest.approx(price)


@pytest.mark.parametrize(
    "kind,old,new",
    [("demand_shift_graph", "D0", "D1"), ("supply_shift_graph", "S0", "S1")],
)
def test_shifts_are_actual_new_curves_not_relabelled_static_lines(
    monkeypatch, kind, old, new
):
    data = _capture(monkeypatch, kind, {"eq_price": 40, "eq_quantity": 120})
    difference = data["lines"][new][:, 1] - data["lines"][old][:, 1]
    assert np.allclose(difference, 10 if kind == "demand_shift_graph" else -10)


@pytest.mark.parametrize(
    "params",
    [
        {"eq_price": 0},
        {"eq_quantity": -1},
        {"eq_price": True},
        {"eq_price": float("nan")},
        {"eq_quantity": float("inf")},
        {"unknown": 1},
        {"kind": "tax"},
    ],
)
def test_invalid_or_unrelated_parameters_refuse_before_render(monkeypatch, params):
    monkeypatch.setattr(
        plt, "savefig", lambda *a, **k: pytest.fail("invalid figure rendered")
    )
    with pytest.raises(ValueError):
        render_pdf._GRAPH_FUNCS["minimum_price_diagram"](params=params)


def test_poverty_cycle_refuses_unprinted_numeric_axes():
    with pytest.raises(ValueError, match="no numeric axes"):
        diagrams.poverty_trap_diagram(params={"eq_price": 80})


def test_candidate_projection_describes_only_the_printed_diagram_and_keeps_source_immutable():
    import json

    from pastpapergen.generator import build_paper_blueprint
    from pastpapergen.models import GraphParams
    from pastpapergen.paper_configs import load_builtin_paper_config
    from pastpapergen.syllabus import load_syllabus

    syllabus = load_syllabus(
        ROOT / "Resources/economics/edexcel-a/generator/data/syllabus_seed.json"
    )
    paper = build_paper_blueprint(
        load_builtin_paper_config("paper_2"), syllabus, 270100
    )
    question = paper.questions[3]
    before = question.model_dump(mode="json")
    assert question.source_instance.kind == "poverty_trap_diagram"
    projection = render_pdf.candidate_stimulus_data(question)
    assert projection["diagram"]["relationships"] == [
        "Low income -> low savings -> low investment -> low productivity -> low income"
    ]
    assert projection["source_fingerprint"] == question.source_instance.fingerprint()
    private = question.model_copy(update={"mark_scheme": ["PRIVATE_SENTINEL"]})
    assert "PRIVATE_SENTINEL" not in json.dumps(
        render_pdf.candidate_stimulus_data(private)
    )
    money = question.model_copy(
        update={
            "stimulus_kind": "money_market_diagram",
            "source_instance": question.source_instance.model_copy(
                update={"kind": "money_market_diagram"}
            ),
            "graph_params": GraphParams(
                eq_price=4, eq_quantity=120, kind="money_market"
            ),
        }
    )
    assert render_pdf.candidate_stimulus_data(money)["diagram"]["parameters"] == {
        "eq_price": 4,
        "eq_quantity": 120,
        "kind": "money_market",
    }
    assert question.model_dump(mode="json") == before


@pytest.mark.parametrize(
    "old_version",
    [
        "edexcel-economics-v10-solver-source",
        "edexcel-economics-v11-diagram-source",
        "edexcel-economics-v12-macro-geometry",
    ],
)
def test_old_diagram_review_cache_is_not_rebound_or_deleted(tmp_path, old_version):
    from pastpapergen.cli import ADAPTER

    from Backend.Core.assessment_checkpoints import (
        AssessmentCheckpointStore,
        CheckpointMismatch,
        identity_for_blueprint,
    )

    blueprint = {"paper_id": "paper_2", "seed": 270100}
    old = identity_for_blueprint(
        blueprint,
        provider="ollama",
        model="fixture",
        prompt_version=old_version,
    )
    current = identity_for_blueprint(
        blueprint,
        provider="ollama",
        model="fixture",
        prompt_version=ADAPTER.prompt_version,
    )
    assert old.prompt_version != current.prompt_version
    path = tmp_path / "old-review.json"
    store = AssessmentCheckpointStore(path, old)
    store.save_payload("question-4", {"old_figure_review": True})
    original = path.read_bytes()
    with pytest.raises(CheckpointMismatch):
        AssessmentCheckpointStore(path, current)
    assert path.read_bytes() == original
    assert store.load_payload("question-4") == {"old_figure_review": True}


@pytest.mark.parametrize(
    "kind,params",
    [
        ("minimum_price_diagram", None),
        ("tariff_diagram", None),
        ("monopsony_diagram", None),
        (
            "minimum_price_diagram",
            {"eq_price": 80, "eq_quantity": 100, "price_limit": 60},
        ),
        (
            "maximum_price_diagram",
            {"eq_price": 80, "eq_quantity": 100, "price_limit": 100},
        ),
    ],
)
def test_quantity_guides_do_not_overlap_each_other_or_axis_title(
    monkeypatch, kind, params
):
    captured = {}

    def inspect(*args, **kwargs):
        figure = plt.gcf()
        figure.canvas.draw()
        renderer = figure.canvas.get_renderer()
        ax = plt.gca()
        axis_title = ax.xaxis.label.get_window_extent(renderer)
        quantities = [
            text.get_window_extent(renderer)
            for text in ax.texts
            if text.get_text()
            in {"Qe", "Qd", "Qs", "Qs0", "Qd0", "Qs1", "Qd1", "Lm", "Lc"}
        ]
        captured.update(axis_title=axis_title, quantities=quantities)
        captured["ticks"] = [
            tick.get_window_extent(renderer) for tick in ax.get_xticklabels()
        ]

    monkeypatch.setattr(plt, "savefig", inspect)
    path = Path(render_pdf._GRAPH_FUNCS[kind](params=params))
    path.unlink(missing_ok=True)
    for index, bounds in enumerate(captured["quantities"]):
        assert not bounds.overlaps(captured["axis_title"])
        assert all(not bounds.overlaps(tick) for tick in captured["ticks"])
        assert all(
            not bounds.overlaps(other) for other in captured["quantities"][index + 1 :]
        )


@pytest.mark.parametrize(
    "kind,xlabel,ylabel,curves",
    [
        ("minimum_price_diagram", "Quantity", "Price", {"D", "S", "Minimum price"}),
        ("maximum_price_diagram", "Quantity", "Price", {"D", "S", "Maximum price"}),
        (
            "tariff_diagram",
            "Quantity",
            "Price",
            {"D", "S", "World price", "World price + tariff"},
        ),
        ("money_market_diagram", "Money balances", "Interest rate", {"MD", "MS"}),
        (
            "exchange_rate_diagram",
            "Quantity of sterling",
            "Exchange rate ($ per £)",
            {"D (£)", "S (£)"},
        ),
        (
            "monopsony_diagram",
            "Quantity of labour",
            "Wage / labour cost",
            {"MRP", "ACL = supply", "MCL"},
        ),
        ("demand_shift_graph", "Quantity", "Price", {"D0", "D1", "S"}),
        ("supply_shift_graph", "Quantity", "Price", {"D", "S0", "S1"}),
    ],
)
def test_admitted_aliases_render_the_declared_model(
    monkeypatch, kind, xlabel, ylabel, curves
):
    captured = {}

    def inspect(*args, **kwargs):
        ax = plt.gca()
        captured["axes"] = (ax.get_xlabel(), ax.get_ylabel())
        captured["curves"] = {line.get_label() for line in ax.lines}

    monkeypatch.setattr(plt, "savefig", inspect)
    path = Path(render_pdf._GRAPH_FUNCS[kind]())
    try:
        assert captured["axes"] == (xlabel, ylabel)
        assert curves <= captured["curves"]
    finally:
        path.unlink(missing_ok=True)


def test_development_poverty_trap_is_a_causal_cycle(monkeypatch):
    captured = {}

    def inspect(*args, **kwargs):
        ax = plt.gca()
        captured["text"] = [text.get_text() for text in ax.texts]
        captured["arrows"] = [
            text for text in ax.texts if getattr(text, "arrow_patch", None) is not None
        ]
        captured["axes"] = (ax.get_xlabel(), ax.get_ylabel())

    monkeypatch.setattr(plt, "savefig", inspect)
    path = Path(render_pdf._GRAPH_FUNCS["poverty_trap_diagram"]())
    try:
        assert {
            "Low income",
            "Low savings",
            "Low investment",
            "Low productivity",
        } <= set(captured["text"])
        assert len(captured["arrows"]) == 4
        assert captured["axes"] == ("", "")
        assert not any("Tax" in text or "T*" in text for text in captured["text"])
    finally:
        path.unlink(missing_ok=True)


def test_public_labour_adapter_prints_exact_projected_equilibrium(monkeypatch):
    params = {"eq_price": 24, "eq_quantity": 120, "kind": "labour"}
    data = _capture(monkeypatch, "labour_market_diagram", params)
    assert "24" in data["yticks"]
    assert "120" in data["xticks"]
    assert (
        diagrams.diagram_description("labour_market_diagram", params)["parameters"]
        == params
    )


@pytest.mark.parametrize(
    "kind,params",
    [
        ("minimum_price_diagram", {"price_limit": 100}),
        ("maximum_price_diagram", {"price_limit": 60}),
        ("tariff_diagram", {"world_price": 60, "tariff": 10}),
    ],
)
def test_description_accepts_the_same_supported_extras_as_rendering(
    monkeypatch, kind, params
):
    _capture(monkeypatch, kind, params)
    assert diagrams.diagram_description(kind, params)["parameters"] == params


@pytest.mark.parametrize(
    "kind", ["minimum_price_diagram", "maximum_price_diagram", "tariff_diagram"]
)
def test_balanced_extreme_scales_do_not_overflow_intermediate_products(
    monkeypatch, kind
):
    data = _capture(monkeypatch, kind, {"eq_price": 1e200, "eq_quantity": 1e200})
    assert all(np.isfinite(points).all() for points in data["lines"].values())


@pytest.mark.parametrize(
    "kind,params",
    [
        (
            "minimum_price_diagram",
            {"eq_price": 1e-100, "eq_quantity": 1e100, "price_limit": 1e308},
        ),
        ("tariff_diagram", {"world_price": 1e308, "tariff": 1e308}),
    ],
)
def test_nonrepresentable_extra_geometry_refuses_before_matplotlib(
    monkeypatch, kind, params
):
    monkeypatch.setattr(
        diagrams,
        "_axes",
        lambda *a, **k: pytest.fail("invalid geometry reached Matplotlib"),
    )
    with pytest.raises(ValueError):
        render_pdf._GRAPH_FUNCS[kind](params=params)
    with pytest.raises(ValueError):
        diagrams.diagram_description(kind, params)


def test_shortage_label_does_not_cross_demand_or_supply(monkeypatch):
    collisions = []

    def inspect(*args, **kwargs):
        fig = plt.gcf()
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        ax = plt.gca()
        shortage = next(text for text in ax.texts if text.get_text() == "Shortage")
        bounds = shortage.get_window_extent(renderer)
        collisions.extend(
            line.get_label()
            for line in ax.lines
            if line.get_label() in {"D", "S"}
            and line.get_path()
            .transformed(line.get_transform())
            .intersects_bbox(bounds, filled=False)
        )

    monkeypatch.setattr(plt, "savefig", inspect)
    path = Path(render_pdf._GRAPH_FUNCS["maximum_price_diagram"]())
    path.unlink(missing_ok=True)
    assert collisions == []


@pytest.mark.parametrize(
    "kind,params,printed",
    [
        ("labour_market_diagram", {}, {"eq_price": 14, "eq_quantity": 100}),
        (
            "labour_market_diagram",
            {"eq_price": 24, "eq_quantity": 120, "kind": "labour"},
            {"eq_price": 24, "eq_quantity": 120},
        ),
        ("tariff_diagram", {"world_price": 60}, {"world_price": 60, "tariff": 10}),
        (
            "minimum_price_diagram",
            {"price_limit": 100},
            {"eq_price": 80, "price_limit": 100},
        ),
    ],
)
def test_projection_includes_visible_default_labels_without_rebinding_requested_params(
    monkeypatch, kind, params, printed
):
    _capture(monkeypatch, kind, params)
    description = diagrams.diagram_description(kind, params)
    assert description["parameters"] == params
    assert description["printed_values"] == printed
