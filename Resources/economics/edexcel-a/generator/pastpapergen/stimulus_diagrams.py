"""Illustrative models for Edexcel stimuli whose declared kinds are distinct."""

from __future__ import annotations

import math

import numpy as np

from Backend.Core.overlay.graphs import _ax, _save, labour_market_diagram

_KINDS = {
    "poverty_trap_diagram": {"poverty_trap"},
    "demand_shift_graph": {"demand_supply"},
    "supply_shift_graph": {"demand_supply"},
    "minimum_price_diagram": {"demand_supply"},
    "maximum_price_diagram": {"demand_supply"},
    "tariff_diagram": {"tariff", "demand_supply"},
    "monopsony_diagram": {"monopsony", "labour"},
    "labour_market_diagram": {"labour"},
    "money_market_diagram": {"money_market"},
    "exchange_rate_diagram": {"exchange_rate", "demand_supply"},
}
_LABOUR_DEFAULTS = {"eq_price": 14.0, "eq_quantity": 100.0}


def _parameters(params, *, kind, extras=()):
    values = dict(params or {})
    unknown = set(values) - {"kind", "eq_price", "eq_quantity", *extras}
    if unknown:
        raise ValueError(f"Unsupported diagram parameters: {sorted(unknown)}")
    for name, value in values.items():
        if name == "kind":
            if not isinstance(value, str) or value not in {"", kind, *_KINDS[kind]}:
                raise ValueError(f"Unsupported parameters for {kind}")
            continue
        if isinstance(value, bool):
            raise ValueError(f"{name} must be finite and positive")
        try:
            number = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{name} must be finite and positive") from error
        if not math.isfinite(number) or number <= 0:
            raise ValueError(f"{name} must be finite and positive")
        values[name] = number
    return values


def _market(params, *, kind, extras=()):
    values = _parameters(params, kind=kind, extras=extras)
    price = values.get("eq_price", 80.0)
    quantity = values.get("eq_quantity", 100.0)
    if not all(
        math.isfinite(value) and value > 0
        for value in (price * 4, quantity * 4, price / quantity, quantity / price)
    ):
        raise ValueError("Diagram parameters exceed the representable geometry range")
    return values, price, quantity


def _finite_geometry(*values):
    if not all(np.isfinite(value).all() for value in values):
        raise ValueError("Diagram parameters exceed the representable geometry range")


def _market_curves(price, quantity, relative_extent):
    with np.errstate(over="ignore", invalid="ignore"):
        relative = np.linspace(0, relative_extent, 201)
        xs = relative * quantity
        demand = (2 - relative) * price
        supply = (0.5 + 0.5 * relative) * price
    _finite_geometry(xs, demand, supply)
    return xs, demand, supply


def _price_control_inputs(params, minimum):
    values, price, quantity = _market(
        params,
        kind="minimum_price_diagram" if minimum else "maximum_price_diagram",
        extras=("price_limit",),
    )
    limit = values.get("price_limit", price * (1.25 if minimum else 0.75))
    ratio = limit / price
    _finite_geometry(ratio)
    demand_quantity = max(0, 2 - ratio) * quantity
    supply_quantity = max(0, 2 * ratio - 1) * quantity
    xmax = max(2 * quantity, supply_quantity, demand_quantity) * 1.1
    ymax = max(2.1 * price, limit * 1.2)
    _finite_geometry(limit, demand_quantity, supply_quantity, xmax, ymax)
    curves = _market_curves(price, quantity, xmax / quantity)
    return (
        values,
        price,
        quantity,
        limit,
        demand_quantity,
        supply_quantity,
        xmax,
        ymax,
        curves,
    )


def _tariff_inputs(params):
    values, price, quantity = _market(
        params, kind="tariff_diagram", extras=("world_price", "tariff")
    )
    world = values.get("world_price", 0.75 * price)
    tariff = values.get("tariff", 0.125 * price)
    landed = world + tariff
    _finite_geometry(world, tariff, landed)
    if world >= price or landed >= price:
        raise ValueError(
            "The import-tariff illustration requires both prices below domestic equilibrium"
        )
    quantities = [
        (
            level,
            max(0, 2 * (level / price) - 1) * quantity,
            (2 - level / price) * quantity,
        )
        for level in (world, landed)
    ]
    _finite_geometry(quantities)
    curves = _market_curves(price, quantity, 2)
    return values, price, quantity, world, tariff, quantities, curves


def _axes(xlabel="Quantity", ylabel="Price", *, values=None):
    ax = _ax()
    ax.set_xlabel(xlabel, labelpad=28)
    ax.set_ylabel(ylabel)
    ax.set_xticks([])
    ax.set_yticks([])
    if values and "eq_quantity" in values:
        ax.set_xticks([values["eq_quantity"]], labels=[f"{values['eq_quantity']:g}"])
    if values and "eq_price" in values:
        ax.set_yticks([values["eq_price"]], labels=[f"{values['eq_price']:g}"])
    ax.set_title("Illustrative diagram", fontsize=9)
    return ax


def _quantity_guide(ax, quantity, price, label, *, offset=9):
    if ax.get_xticklabels():
        offset += 18
    ax.plot([quantity, quantity], [0, price], "k:", linewidth=0.7)
    ax.annotate(
        label,
        (quantity, 0),
        xytext=(0, -offset),
        textcoords="offset points",
        ha="center",
        va="top",
        fontsize=8,
    )


def poverty_trap_diagram(params=None):
    values = _parameters(params, kind="poverty_trap_diagram")
    if set(values) - {"kind"}:
        raise ValueError("The development poverty cycle has no numeric axes")
    ax = _axes("", "")
    ax.figure.set_size_inches(6, 2.7)
    ax.set_axis_off()
    labels = ["Low income", "Low savings", "Low investment", "Low productivity"]
    points = [(0.18, 0.78), (0.82, 0.78), (0.82, 0.22), (0.18, 0.22)]
    for label, point in zip(labels, points, strict=True):
        ax.text(*point, label, ha="center", va="center", fontsize=12)
    for index, point in enumerate(points):
        ax.annotate(
            "",
            xy=points[(index + 1) % 4],
            xytext=point,
            arrowprops={
                "arrowstyle": "->",
                "color": "black",
                "lw": 1.2,
                "shrinkA": 52 if index % 2 == 0 else 13,
                "shrinkB": 52 if index % 2 == 0 else 13,
            },
        )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    return _save()


def shifted_market_diagram(params=None, *, demand):
    values, price, quantity = _market(
        params, kind="demand_shift_graph" if demand else "supply_shift_graph"
    )
    xs, original_demand, original_supply = _market_curves(price, quantity, 2.5)
    ax = _axes(values=values)
    if demand:
        ax.plot(xs, original_demand, "k--", label="D0")
        ax.plot(xs, original_demand + 0.25 * price, "k-", label="D1")
        ax.plot(xs, original_supply, "k-", label="S")
    else:
        ax.plot(xs, original_demand, "k-", label="D")
        ax.plot(xs, original_supply, "k--", label="S0")
        ax.plot(xs, original_supply - 0.25 * price, "k-", label="S1")
    ax.set_xlim(0, 2 * quantity)
    ax.set_ylim(0, 2.1 * price)
    ax.legend(loc="upper right")
    return _save()


def price_control_diagram(params=None, *, minimum):
    (
        values,
        price,
        quantity,
        limit,
        demand_quantity,
        supply_quantity,
        xmax,
        ymax,
        curves,
    ) = _price_control_inputs(params, minimum)
    ax = _axes(values=values)
    if "price_limit" in values:
        ax.set_yticks([price, limit], labels=[f"{price:g}", f"{limit:g}"])
    xs, demand, supply = curves
    ax.plot(xs, demand, "k-", label="D")
    ax.plot(xs, supply, "k-", label="S")
    ax.axhline(
        limit,
        color="black",
        linestyle="--",
        label="Minimum price" if minimum else "Maximum price",
    )
    ax.plot(quantity, price, "ko", markersize=3)
    binding = limit > price if minimum else limit < price
    if binding:
        _quantity_guide(ax, demand_quantity, limit, "Qd")
        _quantity_guide(ax, supply_quantity, limit, "Qs")
        ax.annotate(
            "Surplus" if minimum else "Shortage",
            ((demand_quantity + supply_quantity) / 2, limit),
            xytext=(0, 12 if minimum else -12),
            textcoords="offset points",
            ha="center",
            va="bottom" if minimum else "top",
            fontsize=8,
        )
        ax.annotate(
            "",
            (demand_quantity, limit),
            (supply_quantity, limit),
            arrowprops={"arrowstyle": "<->", "color": "black"},
        )
    else:
        _quantity_guide(ax, quantity, price, "Qe")
        ax.text(0.03, 0.05, "Non-binding limit", transform=ax.transAxes, fontsize=8)
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    ax.legend(loc="upper right")
    return _save()


def tariff_diagram(params=None):
    values, price, quantity, world, tariff, quantities, curves = _tariff_inputs(params)
    landed = world + tariff
    ax = _axes(values=values)
    if "world_price" in values or "tariff" in values:
        ax.text(
            0.03,
            0.16,
            f"World price: {world:g}; tariff: {tariff:g}",
            transform=ax.transAxes,
            fontsize=8,
        )
    ax.set_xlabel("Quantity", labelpad=40)
    xs, demand, supply = curves
    ax.plot(xs, demand, "k-", label="D")
    ax.plot(xs, supply, "k-", label="S")
    ax.axhline(world, color="black", linestyle=":", label="World price")
    ax.axhline(landed, color="black", linestyle="--", label="World price + tariff")
    for (level, supply, demand), suffix in zip(quantities, ("0", "1"), strict=True):
        _quantity_guide(
            ax, supply, level, f"Qs{suffix}", offset=9 if suffix == "0" else 23
        )
        _quantity_guide(
            ax, demand, level, f"Qd{suffix}", offset=9 if suffix == "0" else 23
        )
        ax.annotate(
            "",
            (supply, level),
            (demand, level),
            arrowprops={"arrowstyle": "<->", "color": "black"},
        )
    ax.text(0.03, 0.08, "Imports = Qd - Qs", transform=ax.transAxes, fontsize=8)
    ax.set_xlim(0, 2 * quantity)
    ax.set_ylim(0, 2 * price)
    ax.legend(loc="upper right", fontsize=7)
    return _save()


def monopsony_diagram(params=None):
    values, wage, employment = _market(params, kind="monopsony_diagram")
    # ACL = w/2 + (w/2L)*q; MCL is the derivative of total labour cost.
    # MRP = 5w/2 - (w/L)*q, so MCL = MRP at q = L.
    relative = np.linspace(0, 2, 201)
    xs = relative * employment
    acl = (0.5 + 0.5 * relative) * wage
    mcl = (0.5 + relative) * wage
    mrp = (2.5 - relative) * wage
    competitive_employment = (4 / 3) * employment
    competitive_wage = (7 / 6) * wage
    _finite_geometry(xs, acl, mcl, mrp, competitive_employment, competitive_wage)
    ax = _axes("Quantity of labour", "Wage / labour cost", values=values)
    ax.plot(xs, acl, "k-", label="ACL = supply")
    ax.plot(xs, mcl, "k--", label="MCL")
    ax.plot(xs, mrp, "k-", label="MRP")
    _quantity_guide(ax, employment, 1.5 * wage, "Lm")
    ax.plot(employment, wage, "ko", markersize=3)
    ax.plot([0, employment], [wage, wage], "k:", linewidth=0.7)
    _quantity_guide(ax, competitive_employment, competitive_wage, "Lc")
    ax.annotate("Wm", (0, wage), xytext=(3, 3), textcoords="offset points", fontsize=8)
    ax.set_xlim(0, 2 * employment)
    ax.set_ylim(0, 3 * wage)
    ax.legend(loc="upper right", fontsize=7)
    return _save()


def money_market_diagram(params=None):
    values, rate, balances = _market(params, kind="money_market_diagram")
    xs, demand, _supply = _market_curves(rate, balances, 2)
    ax = _axes("Money balances", "Interest rate", values=values)
    ax.plot(xs, demand, "k-", label="MD")
    ax.axvline(balances, color="black", label="MS")
    ax.plot(balances, rate, "ko", markersize=3)
    ax.set_xlim(0, 2 * balances)
    ax.set_ylim(0, 2.1 * rate)
    ax.legend(loc="upper right")
    return _save()


def exchange_rate_diagram(params=None):
    values, rate, quantity = _market(params, kind="exchange_rate_diagram")
    xs, demand, supply = _market_curves(rate, quantity, 2)
    ax = _axes("Quantity of sterling", "Exchange rate ($ per £)", values=values)
    ax.plot(xs, demand, "k-", label="D (£)")
    ax.plot(xs, supply, "k-", label="S (£)")
    ax.plot(quantity, rate, "ko", markersize=3)
    ax.set_xlim(0, 2 * quantity)
    ax.set_ylim(0, 2.1 * rate)
    ax.legend(loc="upper right")
    return _save()


def competitive_labour_diagram(params=None):
    values = _parameters(params, kind="labour_market_diagram")
    return labour_market_diagram(
        wage=values.get("eq_price", _LABOUR_DEFAULTS["eq_price"]),
        employment=values.get("eq_quantity", _LABOUR_DEFAULTS["eq_quantity"]),
    )


DIAGRAM_RELATIONSHIPS = {
    "poverty_trap_diagram": [
        "Low income -> low savings -> low investment -> low productivity -> low income"
    ],
    "minimum_price_diagram": [
        "Horizontal price floor; binding above equilibrium creates excess supply"
    ],
    "maximum_price_diagram": [
        "Horizontal price ceiling; binding below equilibrium creates excess demand"
    ],
    "tariff_diagram": [
        "Horizontal world price and world price plus tariff; imports equal demand minus domestic supply"
    ],
    "monopsony_diagram": [
        "MCL lies above ACL; hiring at MCL = MRP; wage read from ACL"
    ],
    "money_market_diagram": [
        "Vertical money supply meets downward-sloping money demand"
    ],
    "exchange_rate_diagram": [
        "Sterling supply slopes up and demand slopes down; vertical axis is dollars per pound"
    ],
    "demand_shift_graph": ["Demand shifts right from D0 to D1; supply unchanged"],
    "supply_shift_graph": ["Supply shifts right from S0 to S1; demand unchanged"],
    "labour_market_diagram": [
        "Labour demand slopes down and supply slopes up through the marked equilibrium"
    ],
}


def diagram_description(kind, params=None):
    if kind not in DIAGRAM_RELATIONSHIPS:
        return None
    if kind in {"minimum_price_diagram", "maximum_price_diagram"}:
        inputs = _price_control_inputs(params, kind == "minimum_price_diagram")
        values, price = inputs[:2]
    elif kind == "tariff_diagram":
        inputs = _tariff_inputs(params)
        values = inputs[0]
    elif kind == "poverty_trap_diagram":
        values = _parameters(params, kind=kind)
    else:
        values = _market(params, kind=kind)[0]
    if kind == "poverty_trap_diagram" and set(values) - {"kind"}:
        raise ValueError("The development poverty cycle has no numeric axes")
    printed = {
        name: values[name] for name in ("eq_price", "eq_quantity") if name in values
    }
    if kind == "labour_market_diagram":
        printed = {
            name: values.get(name, default)
            for name, default in _LABOUR_DEFAULTS.items()
        }
    elif (
        kind in {"minimum_price_diagram", "maximum_price_diagram"}
        and "price_limit" in values
    ):
        printed.update(eq_price=price, price_limit=values["price_limit"])
    elif kind == "tariff_diagram" and {"world_price", "tariff"}.intersection(values):
        printed.update(world_price=inputs[3], tariff=inputs[4])
    return {
        "version": "edexcel-stimulus-figures-v1",
        "scale": "Illustrative diagram; supplied numeric parameters are labelled",
        "relationships": list(DIAGRAM_RELATIONSHIPS[kind]),
        "parameters": dict(params or {}),
        "printed_values": printed,
    }
