from __future__ import annotations

import math
import os
import tempfile

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

GRAPH_WIDTH = 4.2
GRAPH_HEIGHT = 3.0
GRAPH_DPI = 350
LINEWIDTH = 1.6
FONTSIZE = 10

_cleared = False


def _ensure_style() -> None:
    global _cleared
    if not _cleared:
        plt.rcdefaults()
        plt.rc("font", size=FONTSIZE, family="Helvetica")
        plt.rc("axes", labelsize=FONTSIZE, titlesize=FONTSIZE, linewidth=0.6)
        plt.rc("xtick", labelsize=8)
        plt.rc("ytick", labelsize=8)
        plt.rc("lines", linewidth=LINEWIDTH)
        plt.rc("legend", fontsize=7.5, frameon=False)
        _cleared = True


def _save() -> str:
    fd, path = tempfile.mkstemp(suffix=".png", prefix="graph_")
    os.close(fd)
    plt.savefig(
        path,
        dpi=GRAPH_DPI,
        bbox_inches="tight",
        pad_inches=0.08,
        transparent=False,
        facecolor="white",
    )
    plt.close()
    return path


def _ax() -> plt.Axes:
    _ensure_style()
    _, ax = plt.subplots(figsize=(GRAPH_WIDTH, GRAPH_HEIGHT))
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_position(("outward", 6))
    ax.spines["left"].set_position(("outward", 6))
    return ax


def _arrow_axes(ax: plt.Axes, x_max: float, y_max: float) -> None:
    ax.plot(
        x_max * 1.04,
        0,
        ">k",
        markersize=4,
        clip_on=False,
        transform=ax.get_xaxis_transform(),
    )
    ax.plot(
        0,
        y_max * 1.04,
        "^k",
        markersize=4,
        clip_on=False,
        transform=ax.get_yaxis_transform(),
    )


def _label(
    ax: plt.Axes,
    text: str,
    x: float,
    y: float,
    fontsize: int = 9,
    ha: str = "center",
    va: str = "center",
) -> None:
    ax.text(x, y, text, fontsize=fontsize, ha=ha, va=va)


def _eq_point(ax: plt.Axes, x: float, y: float, x_max: float, y_max: float) -> None:
    ax.plot(x, y, "ko", markersize=3.5, zorder=5)
    ax.axhline(
        y=y,
        xmin=0,
        xmax=x / x_max,
        linestyle=":",
        color="gray",
        linewidth=0.8,
        zorder=1,
    )
    ax.axvline(
        x=x,
        ymin=0,
        ymax=y / y_max,
        linestyle=":",
        color="gray",
        linewidth=0.8,
        zorder=1,
    )


def _gp(params: dict[str, object] | None, key: str, default: float) -> float:
    if params is None:
        return default
    value = params.get(key)
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _gp_str(params: dict[str, object] | None, key: str, default: str) -> str:
    if params is None:
        return default
    value = params.get(key)
    if not isinstance(value, str) or not value:
        return default
    return value


def _positive_scale(value: object, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be finite and positive")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{name} must be finite and positive") from error
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return number


def _market_scales(params, price, quantity):
    values = params or {}
    price = _positive_scale(values.get("eq_price", price), "eq_price")
    quantity = _positive_scale(
        values.get("eq_quantity", values.get("eq_output", quantity)), "eq_quantity"
    )
    if (
        "eq_output" in values
        and _positive_scale(values["eq_output"], "eq_output") != quantity
    ):
        raise ValueError("Conflicting equilibrium output and quantity")
    if not all(
        math.isfinite(value) and value > 0
        for value in (price * 8, quantity * 8, price / quantity, quantity / price)
    ):
        raise ValueError("Diagram scales exceed representable geometry")
    return price, quantity


def _macro_curves(price, output, *, keynesian, separate_keynesian=False):
    # Include the stated equilibrium itself, not a nearby sampled grid point.
    relative = np.unique(np.append(np.linspace(0, 1.8, 400), 1.0))
    if keynesian:
        first, second = (40 / 110, 100 / 110) if separate_keynesian else (0.3, 0.9)
        initial, low, middle, steep = (
            (0.25, 0.4, 0.06, 2.8) if separate_keynesian else (0.3, 0.5, 0.08, 2.5)
        )

        def supply(ratio):
            return (
                initial
                + low * np.minimum(ratio, first)
                + middle * np.clip(ratio - first, 0, second - first)
                + steep * np.maximum(ratio - second, 0)
            )

        as_y = price * supply(relative) / supply(1.0)
    else:
        as_y = price * (0.3 + 0.7 * relative)
    ad = price * (1.8 - 0.8 * relative)
    return relative * output, ad, as_y


def mr_mc_ac_diagram(
    title: str = "Cost and revenue curves",
    mc_peak: float = 150,
    ac_min: float = 100,
    ar_intercept: float = 160,
    mr_intercept: float = 120,
    q_profit_max: float = 88,
    p_profit_max: float = 128,
    ac_at_q: float = 82,
    params: dict[str, object] | None = None,
) -> str:
    ax = _ax()
    q_max = 150
    y_max = 185
    xs = np.linspace(0, q_max, 300)
    mc = 30 + (xs - 40) ** 2 / 85
    mc = np.clip(mc, 20, mc_peak)
    ac = 110 + (xs - 55) ** 2 / 70 - xs * 0.4
    ac = np.clip(ac, ac_min, 160)
    ar = ar_intercept - xs * 0.35
    mr = np.clip(mr_intercept - xs * 0.7, 0, mr_intercept)

    profit_max_idx = np.argmin(np.abs(mc - mr))
    actual_q = xs[profit_max_idx]
    actual_p = ar[profit_max_idx]
    actual_ac = ac[profit_max_idx]

    ax.plot(xs, mc, "k-", label="MC")
    ax.plot(xs, ac, "k--", label="AC")
    ax.plot(xs, ar, "k-", label="AR")
    ax.plot(xs[: profit_max_idx + 1], mr[: profit_max_idx + 1], "k-", label="MR")

    ax.plot(actual_q, actual_p, "ko", markersize=3.5, zorder=5)
    ax.axvline(
        x=actual_q,
        ymin=0,
        ymax=actual_p / y_max,
        linestyle=":",
        color="gray",
        linewidth=0.8,
        zorder=1,
    )
    ax.axhline(
        y=actual_p,
        xmin=0,
        xmax=actual_q / q_max,
        linestyle=":",
        color="gray",
        linewidth=0.8,
        zorder=1,
    )
    ax.axhline(
        y=actual_ac,
        xmin=0,
        xmax=actual_q / q_max,
        linestyle=":",
        color="gray",
        linewidth=0.8,
        zorder=1,
    )

    supernormal_profit = actual_p - actual_ac
    if supernormal_profit > 0 and actual_q > 0:
        ax.fill(
            [0, actual_q, actual_q, 0],
            [actual_ac, actual_ac, actual_p, actual_p],
            alpha=0.08,
            color="gray",
            label="Profit",
        )

    ax.set_xlim(0, q_max)
    ax.set_ylim(0, y_max)
    ax.set_xlabel("Quantity")
    ax.set_ylabel("Cost / Revenue")
    _arrow_axes(ax, q_max, y_max)
    ax.legend(loc="upper right")
    _label(ax, "MC", q_max * 0.82, mc[int(q_max * 0.82)], fontsize=8)
    _label(ax, "AC", q_max * 0.72, ac[int(q_max * 0.72)], fontsize=8)
    _label(ax, "AR", q_max * 0.78, ar[int(q_max * 0.78)], fontsize=8)
    _label(ax, "MR", q_max * 0.52, mr[int(q_max * 0.52)], fontsize=8)
    _label(ax, f"Q{int(actual_q)}", actual_q, -6, fontsize=7.5)
    _label(
        ax, f"P{int(actual_p)}", -7, actual_p, fontsize=7.5, ha="center", va="center"
    )
    return _save()


def demand_supply_diagram(
    title: str = "Demand and supply",
    eq_price: float = 80,
    eq_quantity: float = 100,
    demand_slope: float = 0.8,
    supply_slope: float = 0.6,
    params: dict[str, object] | None = None,
) -> str:
    eq_price = _gp(params, "eq_price", eq_price)
    eq_quantity = _gp(params, "eq_quantity", eq_quantity)
    ax = _ax()
    q_max = 180
    y_max = eq_price + 45
    xs = np.linspace(0, q_max, 200)
    demand = eq_price + demand_slope * (eq_quantity - xs)
    supply = xs * (eq_price / eq_quantity)

    ax.plot(xs, demand, "k-", label="D")
    ax.plot(xs, supply, "k-", label="S")
    _eq_point(ax, eq_quantity, eq_price, q_max, y_max)
    _label(ax, "Pe", eq_quantity + 7, eq_price - 3, fontsize=8)
    _label(ax, "Qe", eq_quantity, -6, fontsize=8)
    ax.set_xlim(0, q_max)
    ax.set_ylim(0, y_max)
    ax.set_xlabel("Quantity")
    ax.set_ylabel("Price")
    _arrow_axes(ax, q_max, y_max)
    ax.legend(loc="upper right")
    return _save()


def ad_as_diagram(
    title: str = "AD/AS",
    eq_price: float = 100,
    eq_output: float = 100,
    as_type: str = "keynesian",
    params: dict[str, object] | None = None,
) -> str:
    eq_price, eq_output = _market_scales(params, eq_price, eq_output)
    # Public kind names select a diagram, not its supply-curve shape.
    if params and params.get("kind") in {"keynesian", "classical"}:
        as_type = str(params["kind"])
    xs, ad, as_y = _macro_curves(eq_price, eq_output, keynesian=as_type == "keynesian")
    ax = _ax()
    q_max = 1.8 * eq_output
    y_max = 2.1 * eq_price

    ax.plot(xs, ad, "k-", label="AD")
    ax.plot(xs, as_y, "k-", label="AS")
    _eq_point(ax, eq_output, eq_price, q_max, y_max)
    ax.set_xlim(0, q_max)
    ax.set_ylim(0, y_max)
    ax.set_xlabel("Real GDP")
    ax.set_ylabel("Price Level")
    _arrow_axes(ax, q_max, y_max)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.08), ncol=2)
    return _save()


def phillips_curve(
    title: str = "Phillips Curve",
    lrpc_rate: float = 5.0,
    params: dict[str, object] | None = None,
) -> str:
    lrpc_rate = _gp(params, "lrpc_rate", lrpc_rate)
    ax = _ax()
    xs = np.linspace(1, 10, 200)
    srpc = 8.5 - 2.2 * np.sqrt(xs - 0.5)
    srpc = np.clip(srpc, 0.5, 10)
    ax.plot(xs, srpc, "k-", label="SRPC")
    ax.axvline(
        x=lrpc_rate,
        ymin=0,
        ymax=0.82,
        linestyle="--",
        color="gray",
        linewidth=1.2,
        label="LRPC",
    )
    _label(ax, f"U*={lrpc_rate}%", lrpc_rate, 0.5, fontsize=8)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 10)
    ax.set_xlabel("Unemployment rate (%)")
    ax.set_ylabel("Inflation rate (%)")
    _arrow_axes(ax, 11, 10)
    ax.legend(loc="upper right")
    return _save()


def lorenz_curve(
    title: str = "Lorenz Curve",
    gini: float = 0.32,
    params: dict[str, object] | None = None,
) -> str:
    gini = _gp(params, "gini", gini)
    ax = _ax()
    xs = np.linspace(0, 100, 200)
    line_of_equality = xs
    exponent = 1 + 2.0 * gini
    lorenz = (xs / 100) ** exponent * 100
    lorenz = np.minimum(lorenz, xs)
    ax.plot(xs, line_of_equality, "k--", label="Line of equality", linewidth=1.0)
    ax.plot(xs, lorenz, "k-", label="Lorenz curve")
    ax.fill_between(xs, lorenz, line_of_equality, alpha=0.1, color="gray")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_xlabel("Cumulative % of population")
    ax.set_ylabel("Cumulative % of income/wealth")
    _arrow_axes(ax, 100, 100)
    ax.legend(loc="upper left")
    ax.set_aspect("equal")
    return _save()


def laffer_curve(
    title: str = "Laffer Curve",
    revenue_peak_rate: float = 60,
    params: dict[str, object] | None = None,
) -> str:
    revenue_peak_rate = _gp(params, "revenue_peak_rate", revenue_peak_rate)
    ax = _ax()
    xs = np.linspace(0, 100, 300)
    revenue = xs * (1 - xs / 100) * 1.6
    revenue = np.maximum(revenue, 0)
    peak_idx = np.argmax(revenue)
    peak_x = xs[peak_idx]
    peak_y = revenue[peak_idx]
    ax.plot(xs, revenue, "k-")
    ax.plot(peak_x, peak_y, "ko", markersize=3, zorder=5)
    ax.axvline(
        x=peak_x,
        ymin=0,
        ymax=peak_y / 100,
        linestyle=":",
        color="gray",
        linewidth=0.8,
        zorder=1,
    )
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_xlabel("Tax rate (%)")
    ax.set_ylabel("Tax revenue")
    _arrow_axes(ax, 100, 100)
    _label(ax, f"T*={peak_x:.0f}%", peak_x, -5, fontsize=8)
    return _save()


def labour_market_diagram(
    title: str = "Labour market",
    wage: float = 14,
    employment: float = 100,
    params: dict[str, object] | None = None,
) -> str:
    def positive_parameter(name, default):
        value = params.get(name, default) if params is not None else default
        if isinstance(value, bool):
            raise ValueError(f"{name} must be finite and positive")
        try:
            number = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{name} must be finite and positive") from error
        if not np.isfinite(number) or number <= 0 or not np.isfinite(number * 2.1):
            raise ValueError(f"{name} must be finite and positive")
        return number

    wage = positive_parameter("wage", wage)
    employment = positive_parameter("employment", employment)
    if not np.isfinite(wage / employment) or wage / employment == 0:
        raise ValueError("Labour parameters must yield a finite and positive slope")
    q_max = employment * 2
    y_max = wage * 2
    relative = np.linspace(0, 2, 200)
    xs = relative * employment
    dL = (2 - relative) * wage
    sL = (0.5 + 0.5 * relative) * wage
    if not all(np.isfinite(values).all() for values in (xs, dL, sL)):
        raise ValueError("Labour parameters must yield finite and positive geometry")
    dL = np.clip(dL, 0, y_max)
    sL = np.clip(sL, 0, y_max)

    ax = _ax()
    ax.plot(xs, dL, "k-", label="DL")
    ax.plot(xs, sL, "k-", label="SL")
    _eq_point(ax, employment, wage, q_max, y_max)
    ax.annotate("We", (0, wage), xytext=(8, 10), textcoords="offset points", fontsize=8)
    ax.annotate(
        "Le", (employment, 0), xytext=(8, 10), textcoords="offset points", fontsize=8
    )
    ax.set_xlim(0, q_max)
    ax.set_ylim(0, y_max)
    ax.set_xlabel("Quantity of labour")
    ax.set_ylabel("Wage rate (\u00a3)")
    ax.set_xticks([0, employment, q_max], labels=["0", f"{employment:g}", f"{q_max:g}"])
    ax.set_yticks([0, wage, y_max], labels=["0", f"{wage:g}", f"{y_max:g}"])
    _arrow_axes(ax, q_max, y_max)
    ax.legend(loc="upper right")
    return _save()


def externality_diagram(
    title: str = "Negative externality",
    kind: str = "negative",
    params: dict[str, object] | None = None,
) -> str:
    kind = _gp_str(params, "kind", kind)
    if kind in {"externality", "externality_diagram"}:
        kind = "negative"
    if kind not in {"negative", "positive"}:
        raise ValueError("Expected a negative or positive externality kind")
    benefit_intercept, benefit_slope = 100, 0.6
    cost_intercept, cost_slope = 12, 0.48
    benefit_gap, cost_gap = (0, 20) if kind == "negative" else (22, 0)
    q_private = (benefit_intercept - cost_intercept) / (benefit_slope + cost_slope)
    q_social = (benefit_intercept + benefit_gap - cost_intercept - cost_gap) / (
        benefit_slope + cost_slope
    )
    p_private = benefit_intercept - benefit_slope * q_private
    p_social = benefit_intercept + benefit_gap - benefit_slope * q_social
    ax = _ax()
    xs = np.unique(np.append(np.linspace(0, 120, 200), [q_private, q_social]))
    y_max = 115
    mpb = benefit_intercept - xs * benefit_slope
    mpc = cost_intercept + xs * cost_slope
    msb, msc = mpb + benefit_gap, mpc + cost_gap

    ax.plot(xs, mpb, "k-", label="MPB")
    ax.plot(xs, mpc, "k--", label="MPC", linewidth=1.2)
    ax.plot(xs, msc, "k-", label="MSC")
    ax.plot(xs, msb, "k--", label="MSB", linewidth=1.0, alpha=0.6)

    ax.plot(q_private, p_private, "ko", markersize=3, zorder=5)
    ax.plot(q_social, p_social, "ko", markersize=3, zorder=5)

    # Welfare loss spans MSB and MSC at private output, meeting at social output.
    dwl_x = [q_social, q_private, q_private]
    dwl_y = [p_social, p_private + benefit_gap, p_private + cost_gap]
    ax.fill(dwl_x, dwl_y, alpha=0.1, color="gray", label="DWL")
    ax.axvline(
        x=q_social,
        ymin=0,
        ymax=p_social / y_max,
        linestyle=":",
        color="gray",
        linewidth=0.7,
    )

    ax.axvline(
        x=q_private,
        ymin=0,
        ymax=p_private / y_max,
        linestyle=":",
        color="gray",
        linewidth=0.7,
    )
    ax.set_xlim(0, 105)
    ax.set_ylim(0, y_max)
    ax.set_xlabel("Quantity")
    ax.set_ylabel("Cost / Benefit")
    _arrow_axes(ax, 105, y_max)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.08), ncol=5)
    return _save()


def ppf_diagram(
    title: str = "Production Possibility Frontier",
    params: dict[str, object] | None = None,
) -> str:
    ax = _ax()
    xs = np.linspace(0, 100, 200)
    ppf = 100 * (1 - (xs / 100) ** 0.6)
    ax.plot(xs, ppf, "k-")
    point_y = 100 * (1 - (30 / 100) ** 0.6)
    ax.plot(30, point_y, "ko", markersize=3.5, zorder=5)
    _label(ax, "A", 30 - 4, point_y - 3, fontsize=9)
    ax.set_xlim(0, 105)
    ax.set_ylim(0, 105)
    ax.set_xlabel("Good X")
    ax.set_ylabel("Good Y")
    _arrow_axes(ax, 105, 105)
    return _save()


def perfect_competition_diagram(
    title: str = "Perfect competition",
    price: float = 80,
    q_firm: float = 60,
    params: dict[str, object] | None = None,
) -> str:
    price = _gp(params, "price", price)
    q_firm = _gp(params, "q_firm", q_firm)
    ax = _ax()
    x_max = 100
    y_max = 180
    xs = np.linspace(0.1, x_max, 300)
    mc = 25 + (xs - 35) ** 2 / 18
    mc = np.clip(mc, 10, y_max)

    mc_idx = np.argmin(np.abs(mc - price))
    actual_q = xs[mc_idx]

    ac = 120 - (xs - 40) ** 2 / 20 + xs * 0.05
    ac = np.clip(ac, 40, y_max)
    actual_ac = ac[mc_idx]

    ax.plot(xs, mc, "k-", label="MC")
    ax.plot(xs, ac, "k--", label="AC")
    ax.axhline(
        y=price,
        xmin=0,
        xmax=1,
        linestyle="-",
        color="gray",
        linewidth=1.2,
        label="D = AR = MR",
    )
    ax.plot(actual_q, price, "ko", markersize=3.5, zorder=5)
    ax.axvline(
        x=actual_q,
        ymin=0,
        ymax=price / y_max,
        linestyle=":",
        color="gray",
        linewidth=0.8,
        zorder=1,
    )

    if actual_ac < price:
        ax.fill(
            [0, actual_q, actual_q, 0],
            [actual_ac, actual_ac, price, price],
            alpha=0.08,
            color="gray",
            label="Profit",
        )

    ax.set_xlim(0, x_max)
    ax.set_ylim(0, y_max)
    ax.set_xlabel("Output")
    ax.set_ylabel("Cost / Revenue")
    _arrow_axes(ax, x_max, y_max)
    ax.legend(loc="upper right")
    return _save()


def monopoly_diagram(
    title: str = "Monopoly",
    price: float = 90,
    quantity: float = 50,
    ar_intercept: float = 140,
    params: dict[str, object] | None = None,
) -> str:
    price = _gp(params, "price", price)
    quantity = _gp(params, "quantity", quantity)
    ax = _ax()
    q_max = 120
    y_max = ar_intercept + 15
    xs = np.linspace(0, q_max, 200)

    ar = ar_intercept - xs
    mr = np.clip(ar_intercept - 2 * xs, 0, ar_intercept)
    mc = 30 + (xs - quantity) ** 2 / 50
    mc = np.clip(mc, 25, 110)

    mr_idx = np.argmin(np.abs(mr - mc))
    actual_q = xs[mr_idx]
    actual_p = ar[mr_idx]

    try:
        ac_idx = np.argmin(np.abs(xs - actual_q))
        ac_raw = 55 + (xs - 40) ** 2 / 30 + xs * 0.15
        ac_raw = np.clip(ac_raw, 40, 120)
        actual_ac = ac_raw[ac_idx]
    except Exception:
        actual_ac = 50

    ax.plot(xs, ar, "k-", label="AR (Demand)")
    ax.plot(xs[mr_idx + 1 :], mr[mr_idx + 1 :], "k--", alpha=0.3, linewidth=1.0)
    ax.plot(xs[: mr_idx + 1], mr[: mr_idx + 1], "k--", label="MR", linewidth=1.3)
    ax.plot(xs, mc, "k-", label="MC")

    if actual_ac < actual_p:
        ax.fill(
            [0, actual_q, actual_q, 0],
            [actual_ac, actual_ac, actual_p, actual_p],
            alpha=0.08,
            color="gray",
            label="Profit",
        )

    ax.plot(actual_q, actual_p, "ko", markersize=3.5, zorder=5)
    ax.axvline(
        x=actual_q,
        ymin=0,
        ymax=actual_p / y_max,
        linestyle=":",
        color="gray",
        linewidth=0.8,
        zorder=1,
    )
    ax.axhline(
        y=actual_p,
        xmin=0,
        xmax=actual_q / q_max,
        linestyle=":",
        color="gray",
        linewidth=0.8,
        zorder=1,
    )

    ax.set_xlim(0, q_max)
    ax.set_ylim(0, y_max)
    ax.set_xlabel("Quantity")
    ax.set_ylabel("Cost / Revenue")
    _arrow_axes(ax, q_max, y_max)
    ax.legend(loc="upper right")
    _label(ax, "Qm", actual_q, -3, fontsize=7.5)
    _label(ax, "Pm", -4, actual_p + 2, fontsize=7.5, ha="center", va="center")
    return _save()


def trade_cycle_diagram(
    title: str = "Trade cycle",
) -> str:
    ax = _ax()
    xs = np.linspace(0, 20, 500)
    trend = 11 + xs * 0.45
    cycle = (
        10 * np.sin(xs * 0.7) * np.exp(-xs * 0.03)
        + 5 * np.sin(xs * 1.9) * np.exp(-xs * 0.06)
        + trend
    )
    ax.plot(xs, cycle, "k-", label="Actual GDP", linewidth=1.5)
    ax.plot(xs, trend, "k--", label="Trend GDP", linewidth=1.2)
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 32)
    ax.set_xlabel("Time")
    ax.set_ylabel("Real GDP")
    _arrow_axes(ax, 20, 32)
    ax.legend(loc="upper left")
    return _save()


def tax_subsidy_diagram(
    title: str = "Tax / Subsidy",
    kind: str = "tax",
    tax_amount: float = 15,
    params: dict[str, object] | None = None,
) -> str:
    requested_kind = _gp_str(params, "kind", kind)
    if requested_kind in {"tax", "subsidy"}:
        kind = requested_kind
    if kind not in {"tax", "subsidy"}:
        raise ValueError("Expected a tax or subsidy")
    p_eq, q_eq = _market_scales(params, 60, 100)
    tax_amount = _positive_scale(
        (params or {}).get("tax_amount", tax_amount), "tax_amount"
    )
    # Positive post-intervention output and producer/consumer prices are required.
    if tax_amount >= 0.9 * p_eq:
        raise ValueError("Intervention exceeds this illustrative market's range")
    relative_change = tax_amount / (1.5 * p_eq)
    q_new = q_eq * (1 - relative_change if kind == "tax" else 1 + relative_change)
    p_new = p_eq * (1 - (q_new / q_eq - 1) * (2 / 3))
    p_producer = p_new + (tax_amount if kind == "subsidy" else -tax_amount)
    xs = np.unique(np.append(np.linspace(0, 1.8 * q_eq, 300), [q_eq, q_new]))
    demand = p_eq * (1 + (1 - xs / q_eq) * (2 / 3))
    supply = p_eq * (1 + (xs / q_eq - 1) * (5 / 6))
    supply_shifted = supply + (tax_amount if kind == "tax" else -tax_amount)
    ax = _ax()
    q_max = 1.8 * q_eq
    y_max = 2.1 * p_eq
    ax.plot(xs, supply_shifted, "k-", label=f"S1 (after {kind})")
    ax.fill(
        [0, q_new, q_new, 0],
        [p_producer, p_producer, p_new, p_new],
        alpha=0.08,
        color="gray",
        label="Tax revenue" if kind == "tax" else "Subsidy cost",
    )
    ax.fill(
        [q_new, q_new, q_eq],
        [p_new, p_producer, p_eq],
        alpha=0.15,
        color="gray",
        label="DWL",
        hatch="////",
    )

    ax.plot(xs, demand, "k-", label="D")
    ax.plot(xs, supply, "k--", label="S0", linewidth=1.2)

    ax.plot(q_new, p_new, "ko", markersize=3, zorder=5)
    ax.plot(q_eq, p_eq, "ko", markersize=2.5, zorder=4, alpha=0.5)

    ax.set_xlim(0, q_max)
    ax.set_ylim(0, y_max)
    ax.set_xlabel("Quantity")
    ax.set_ylabel("Price")
    _arrow_axes(ax, q_max, y_max)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.08), ncol=3, fontsize=7)
    return _save()


def consumer_producer_surplus(
    title: str = "Consumer and producer surplus",
    price: float = 55,
    quantity: float = 70,
    params: dict[str, object] | None = None,
) -> str:
    values = dict(params or {})
    for canonical, legacy in (("eq_price", "price"), ("eq_quantity", "quantity")):
        if legacy in values:
            legacy_value = _positive_scale(values[legacy], legacy)
            if (
                canonical in values
                and _positive_scale(values[canonical], canonical) != legacy_value
            ):
                raise ValueError(f"Conflicting {canonical} and {legacy}")
            values[canonical] = legacy_value
    price, quantity = _market_scales(values, price, quantity)
    ax = _ax()
    q_max = 1.8 * quantity
    y_max = 2.1 * price
    xs = np.unique(np.append(np.linspace(0, q_max, 200), quantity))

    demand = price * (2 - xs / quantity)
    supply = price * (xs / quantity)

    traded = xs <= quantity

    ax.plot(xs, demand, "k-", label="D")
    ax.plot(xs, supply, "k-", label="S")
    ax.fill_between(
        xs[traded], price, demand[traded], alpha=0.1, color="gray", label="CS"
    )
    ax.fill_between(
        xs[traded], supply[traded], price, alpha=0.06, color="gray", label="PS"
    )
    ax.axhline(
        y=price,
        xmin=0,
        xmax=quantity / q_max,
        linestyle=":",
        color="gray",
        linewidth=0.8,
    )
    ax.plot(quantity, price, "ko", markersize=3.5, zorder=5)
    ax.annotate("Pe", (0, price), xytext=(8, 8), textcoords="offset points", fontsize=8)
    ax.annotate(
        "Qe", (quantity, 0), xytext=(8, 8), textcoords="offset points", fontsize=8
    )
    ax.set_xlim(0, q_max)
    ax.set_ylim(0, y_max)
    ax.set_xlabel("Quantity")
    ax.set_ylabel("Price")
    _arrow_axes(ax, q_max, y_max)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.08), ncol=4)
    return _save()


def circular_flow_diagram(
    title: str = "Circular flow of income",
) -> str:
    ax = _ax()
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    _label(ax, "Firms", 5, 8, fontsize=11)
    _label(ax, "Households", 5, 2, fontsize=11)
    ax.annotate(
        "", xy=(5, 6.5), xytext=(5, 3.5), arrowprops=dict(arrowstyle="->", lw=1.2)
    )
    ax.annotate(
        "", xy=(5, 3.5), xytext=(5, 6.5), arrowprops=dict(arrowstyle="->", lw=1.2)
    )
    _label(ax, "Goods & services", 7.5, 5.5, fontsize=8)
    _label(ax, "Factor payments", 2.5, 5, fontsize=8)
    _label(ax, "Spending (G+S)", 5, 6.2, fontsize=8)
    _label(ax, "Factor incomes", 5, 3.8, fontsize=8)
    ax.set_title(title, fontsize=10, pad=8)
    return _save()


def keynesian_ad_as_diagram(
    title: str = "Keynesian AS",
    eq_price: float = 110,
    eq_output: float = 110,
    params: dict[str, object] | None = None,
) -> str:
    eq_price, eq_output = _market_scales(params, eq_price, eq_output)
    xs, ad, as_y = _macro_curves(
        eq_price, eq_output, keynesian=True, separate_keynesian=True
    )
    ax = _ax()
    q_max = 1.8 * eq_output
    y_max = 2.1 * eq_price

    ax.plot(xs, ad, "k-", label="AD")
    ax.plot(xs, as_y, "k-", label="AS (Keynesian)")
    _eq_point(ax, eq_output, eq_price, q_max, y_max)
    ax.set_xlim(0, q_max)
    ax.set_ylim(0, y_max)
    ax.set_xlabel("Real GDP")
    ax.set_ylabel("Price Level")
    _arrow_axes(ax, q_max, y_max)
    ax.legend(fontsize=7.5, loc="lower center", bbox_to_anchor=(0.5, 1.08), ncol=2)
    return _save()


def subsidy_diagram(
    title: str = "Subsidy diagram",
    subsidy_amount: float = 12,
    params: dict[str, object] | None = None,
) -> str:
    subsidy_amount = _gp(params, "subsidy_amount", subsidy_amount)
    return tax_subsidy_diagram(
        title=title, kind="subsidy", tax_amount=subsidy_amount, params=params
    )
