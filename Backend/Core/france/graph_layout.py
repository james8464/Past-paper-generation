"""Bounded, deterministic V36-v2 figure geometry shared with PDF checks."""

from dataclasses import dataclass
from math import atan2, ceil, cos, hypot, pi, sin, sqrt

from reportlab.pdfbase.pdfmetrics import getAscentDescent, stringWidth

from Backend.Core.fonts import register_fonts
from Backend.Core.france.code_layout import CodeLayoutError, code_layout
from Backend.Core.france.nsi import NSIWeightedGraphMaterial

Point = tuple[float, float]
Box = tuple[float, float, float, float]


@dataclass(frozen=True)
class GraphRoute:
    start: Point
    end: Point
    arrow: tuple[Point, ...]
    label: str
    label_origin: Point
    label_box: Box


@dataclass(frozen=True)
class GraphLayout:
    width: float
    height: float
    radius: float
    font_size: int
    regular_font: str
    bold_font: str
    positions: dict[str, Point]
    routes: tuple[GraphRoute, ...]


class _CongestedGraph(CodeLayoutError):
    """The current bounded figure size cannot separate every weight."""


def _intersects(first: Box, second: Box, gap: float = 2) -> bool:
    return not (
        first[2] + gap <= second[0]
        or second[2] + gap <= first[0]
        or first[3] + gap <= second[1]
        or second[3] + gap <= first[1]
    )


def _segment_distance(point: Point, start: Point, end: Point) -> float:
    vx, vy = end[0] - start[0], end[1] - start[1]
    projection = ((point[0] - start[0]) * vx + (point[1] - start[1]) * vy) / (
        vx * vx + vy * vy
    )
    fraction = max(0, min(1, projection))
    return hypot(
        point[0] - start[0] - fraction * vx, point[1] - start[1] - fraction * vy
    )


def graph_layout(
    material: NSIWeightedGraphMaterial,
    large_print: bool,
    available_width: float | None = None,
) -> GraphLayout:
    last_error = None
    for floor in (0, 340, 420, 460):
        try:
            return _fit_graph(material, large_print, available_width, floor)
        except _CongestedGraph as error:
            last_error = error
    raise CodeLayoutError(str(last_error)) from last_error


def _fit_graph(
    material: NSIWeightedGraphMaterial,
    large_print: bool,
    available_width: float | None,
    height_floor: float,
) -> GraphLayout:
    page = code_layout(large_print)
    width = min(
        available_width if available_width is not None else page.content_width + 12, 440
    )
    fonts = register_fonts("ExamSans", "ExamSans-Bold")
    regular, bold = fonts["ExamSans"], fonts["ExamSans-Bold"]
    size = 14 if large_print else 10
    if any(not node.isprintable() for node in material.nodes):
        raise CodeLayoutError(
            "Les noms des sommets doivent tenir sur une ligne imprimable."
        )
    ascent, descent = getAscentDescent(regular, size)
    radius = max(
        18 if not large_print else 24,
        ceil(max(stringWidth(node, bold, size) for node in material.nodes) / 2 + 6),
    )
    count = len(material.nodes)
    required_ring = (2 * radius + 8) / (2 * sin(pi / count))
    # Wider named circles need a readable corridor for reciprocal labels; short
    # identifiers retain a more compact figure rather than padding every graph.
    minimum_height = max(
        260 if radius > 24 else 220 if large_print else 180, min(280, 42 * count)
    )
    height = max(minimum_height, height_floor, 2 * (required_ring + radius + 18))
    if height > 460 or required_ring > width / 2 - radius - 18:
        raise CodeLayoutError(
            "Le graphe ne tient pas avec des libellés lisibles : utiliser des noms de sommets plus courts ou moins de sommets."
        )
    ring = min(width / 2 - radius - 18, height / 2 - radius - 18)
    positions = {
        node: (
            width / 2 + ring * cos(-pi / 2 + 2 * pi * i / count),
            height / 2 + ring * sin(-pi / 2 + 2 * pi * i / count),
        )
        for i, node in enumerate(material.nodes)
    }
    node_boxes = [
        (x - radius, y - radius, x + radius, y + radius) for x, y in positions.values()
    ]
    pairs = {(start, end) for start, end, _ in material.edges}
    routes: list[GraphRoute] = []
    label_boxes: list[Box] = []
    for start, end, weight in material.edges:
        x1, y1 = positions[start]
        x2, y2 = positions[end]
        distance = hypot(x2 - x1, y2 - y1)
        ux, uy = (x2 - x1) / distance, (y2 - y1) / distance
        nx, ny = -uy, ux
        reciprocal = material.directed and (end, start) in pairs
        offset = radius / 2 if reciprocal else 0
        line_start = (x1 + nx * offset, y1 + ny * offset)
        line_end = (x2 + nx * offset, y2 + ny * offset)
        # Four points also clear the arrowhead's ~3pt half-width plus stroke.
        if any(
            _segment_distance(point, line_start, line_end) < radius + 4
            for node, point in positions.items()
            if node not in {start, end}
        ):
            raise _CongestedGraph(
                "Un arc traverse un autre sommet dans ce format : rédiger un graphe lisible avec des noms plus courts."
            )
        arrow: tuple[Point, ...] = ()
        if material.directed:
            boundary = sqrt(radius * radius - offset * offset)
            tip = (line_end[0] - ux * boundary, line_end[1] - uy * boundary)
            angle = atan2(uy, ux)
            arrow = (
                tip,
                *[
                    (tip[0] - 7 * cos(angle + turn), tip[1] - 7 * sin(angle + turn))
                    for turn in (-0.45, 0.45)
                ],
            )
        label = str(weight)
        text_width = stringWidth(label, regular, size)
        box_width, box_height = text_width + 6, ascent - descent + 6
        clearance = abs(nx) * box_width / 2 + abs(ny) * box_height / 2 + 3
        placement = None
        # A finite placement search, not a general graph-routing engine. Refuse
        # unsupported congestion rather than silently hiding a source weight.
        for fraction in (0.5, 0.33, 0.67, 0.2, 0.8):
            for side in (1,) if reciprocal else (1, -1):
                cx = (
                    line_start[0]
                    + fraction * (line_end[0] - line_start[0])
                    + side * nx * clearance
                )
                cy = (
                    line_start[1]
                    + fraction * (line_end[1] - line_start[1])
                    + side * ny * clearance
                )
                box = (
                    cx - box_width / 2,
                    cy - box_height / 2,
                    cx + box_width / 2,
                    cy + box_height / 2,
                )
                if (
                    min(box[:2]) < 0
                    or box[2] > width
                    or box[3] > height
                    or any(_intersects(box, node) for node in node_boxes)
                    or any(_intersects(box, previous) for previous in label_boxes)
                ):
                    continue
                placement = (box, (cx - text_width / 2, cy - (ascent + descent) / 2))
                break
            if placement is not None:
                break
        if placement is None:
            raise _CongestedGraph(
                "Les poids du graphe se chevauchent dans ce format : rédiger un graphe moins dense avec des libellés plus courts."
            )
        box, origin = placement
        label_boxes.append(box)
        routes.append(GraphRoute(line_start, line_end, arrow, label, origin, box))
    return GraphLayout(
        width, height, radius, size, regular, bold, positions, tuple(routes)
    )
