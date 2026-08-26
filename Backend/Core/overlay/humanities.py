from __future__ import annotations

from dataclasses import dataclass

from reportlab.graphics.shapes import Circle, Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors


@dataclass(frozen=True)
class TimelineEvent:
    year: int
    label: str


@dataclass(frozen=True)
class TimelineSpec:
    events: tuple[TimelineEvent, ...]


@dataclass(frozen=True)
class MapFeature:
    label: str
    x: float
    y: float
    kind: str


@dataclass(frozen=True)
class MapSpec:
    boundary: tuple[tuple[float, float], ...]
    features: tuple[MapFeature, ...]
    scale_km: float = 1
    north: bool = True


def timeline_diagram(specification: TimelineSpec) -> Drawing:
    if not specification.events:
        raise ValueError("timeline requires at least one event")
    years = [event.year for event in specification.events]
    if years != sorted(years):
        raise ValueError("timeline events must be chronological")
    if any(not event.label.strip() for event in specification.events):
        raise ValueError("timeline event labels cannot be empty")

    drawing = Drawing(420, 160)
    left, right, axis_y = 35, 385, 78
    drawing.add(Line(left, axis_y, right, axis_y, strokeColor=colors.black))
    span = max(years[-1] - years[0], 1)
    for index, event in enumerate(specification.events):
        x = left + (event.year - years[0]) / span * (right - left)
        if len(specification.events) == 1:
            x = (left + right) / 2
        above = index % 2 == 0
        label_y = 116 if above else 35
        drawing.add(Line(x, axis_y - 6, x, axis_y + 6, strokeColor=colors.black))
        drawing.add(String(x, axis_y - 19, str(event.year), textAnchor="middle", fontSize=8))
        drawing.add(Line(x, axis_y + (6 if above else -6), x, label_y, strokeColor=colors.grey))
        drawing.add(String(x, label_y + (3 if above else -10), event.label, textAnchor="middle", fontSize=8))
    return drawing


def map_diagram(specification: MapSpec) -> Drawing:
    if len(specification.boundary) < 3:
        raise ValueError("map boundary requires at least three points")
    if specification.scale_km <= 0:
        raise ValueError("map scale must be positive")
    xs = [point[0] for point in specification.boundary]
    ys = [point[1] for point in specification.boundary]
    x_span = max(xs) - min(xs)
    y_span = max(ys) - min(ys)
    if x_span <= 0 or y_span <= 0:
        raise ValueError("map boundary must have non-zero area")

    drawing = Drawing(360, 230)

    def position(x: float, y: float) -> tuple[float, float]:
        return (
            35 + (x - min(xs)) / x_span * 285,
            35 + (y - min(ys)) / y_span * 160,
        )

    boundary: list[float] = []
    for point in specification.boundary:
        boundary.extend(position(*point))
    drawing.add(
        Polygon(
            boundary,
            strokeColor=colors.black,
            fillColor=colors.HexColor("#f5f5f5"),
            strokeWidth=1,
        )
    )
    for feature in specification.features:
        x, y = position(feature.x, feature.y)
        if feature.kind == "settlement":
            drawing.add(Circle(x, y, 3, fillColor=colors.black, strokeColor=None))
        elif feature.kind == "site":
            drawing.add(Rect(x - 3, y - 3, 6, 6, fillColor=None, strokeColor=colors.black))
        else:
            drawing.add(Line(x - 4, y - 4, x + 4, y + 4, strokeColor=colors.black))
            drawing.add(Line(x - 4, y + 4, x + 4, y - 4, strokeColor=colors.black))
        drawing.add(String(x + 6, y - 3, feature.label, fontSize=8))

    drawing.add(Line(35, 18, 105, 18, strokeColor=colors.black, strokeWidth=1.2))
    drawing.add(Line(35, 14, 35, 22, strokeColor=colors.black))
    drawing.add(Line(105, 14, 105, 22, strokeColor=colors.black))
    drawing.add(
        String(
            70,
            5,
            f"{specification.scale_km:g} km",
            textAnchor="middle",
            fontSize=8,
        )
    )
    if specification.north:
        drawing.add(Line(335, 165, 335, 205, strokeColor=colors.black))
        drawing.add(Polygon([335, 210, 330, 200, 340, 200], fillColor=colors.black))
        drawing.add(String(335, 215, "N", textAnchor="middle", fontSize=9))
    return drawing
