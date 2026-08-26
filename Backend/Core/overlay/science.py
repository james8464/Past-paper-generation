from __future__ import annotations

from dataclasses import dataclass

from reportlab.graphics.shapes import Circle, Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors

INK = colors.black


@dataclass(frozen=True)
class ApparatusSpec:
    vessels: tuple[str, ...]
    labels: tuple[str, ...] = ()


@dataclass(frozen=True)
class Atom:
    symbol: str
    x: float
    y: float


@dataclass(frozen=True)
class Bond:
    source: int
    target: int
    order: int = 1


@dataclass(frozen=True)
class MoleculeSpec:
    atoms: tuple[Atom, ...]
    bonds: tuple[Bond, ...]


@dataclass(frozen=True)
class CircuitComponent:
    kind: str
    label: str = ""


@dataclass(frozen=True)
class CircuitSpec:
    components: tuple[CircuitComponent, ...]


@dataclass(frozen=True)
class RaySpec:
    object_distance: float
    focal_length: float
    image_distance: float


def apparatus_diagram(specification: ApparatusSpec) -> Drawing:
    if not specification.vessels:
        raise ValueError("apparatus requires at least one vessel")
    drawing = Drawing(360, 180)
    baseline = 42
    drawing.add(Line(24, baseline, 336, baseline, strokeColor=INK, strokeWidth=0.8))
    step = 300 / len(specification.vessels)
    for index, vessel in enumerate(specification.vessels):
        centre = 30 + step * (index + 0.5)
        if vessel == "beaker":
            drawing.add(
                Polygon(
                    [centre - 30, 130, centre - 24, 55, centre + 24, 55, centre + 30, 130],
                    strokeColor=INK,
                    fillColor=None,
                    strokeWidth=1,
                )
            )
            drawing.add(Line(centre - 27, 88, centre + 27, 88, strokeColor=INK))
        elif vessel == "measuring cylinder":
            drawing.add(Rect(centre - 15, 55, 30, 82, strokeColor=INK, fillColor=None))
            for tick in range(1, 7):
                y = 55 + tick * 11
                drawing.add(Line(centre + 7, y, centre + 15, y, strokeColor=INK, strokeWidth=0.6))
        else:
            drawing.add(Rect(centre - 24, 55, 48, 70, strokeColor=INK, fillColor=None))
        drawing.add(String(centre, 25, vessel, textAnchor="middle", fontSize=8))
    for index, label in enumerate(specification.labels):
        drawing.add(String(28, 160 - index * 12, label, fontSize=8))
    return drawing


def molecule_diagram(specification: MoleculeSpec) -> Drawing:
    if not specification.atoms:
        raise ValueError("molecule requires at least one atom")
    for bond in specification.bonds:
        if (
            bond.source < 0
            or bond.target < 0
            or bond.source >= len(specification.atoms)
            or bond.target >= len(specification.atoms)
            or bond.source == bond.target
        ):
            raise ValueError("bond endpoint is outside the atom list")
        if bond.order not in {1, 2, 3}:
            raise ValueError("bond order must be one, two, or three")

    drawing = Drawing(320, 180)
    positions = [
        (160 + atom.x * 70, 90 + atom.y * 55) for atom in specification.atoms
    ]
    for bond in specification.bonds:
        x1, y1 = positions[bond.source]
        x2, y2 = positions[bond.target]
        offsets = {1: (0,), 2: (-3, 3), 3: (-5, 0, 5)}[bond.order]
        length = max(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5, 1)
        normal_x = -(y2 - y1) / length
        normal_y = (x2 - x1) / length
        for offset in offsets:
            drawing.add(
                Line(
                    x1 + normal_x * offset,
                    y1 + normal_y * offset,
                    x2 + normal_x * offset,
                    y2 + normal_y * offset,
                    strokeColor=INK,
                    strokeWidth=1,
                )
            )
    for atom, (x, y) in zip(specification.atoms, positions, strict=True):
        drawing.add(Circle(x, y, 13, strokeColor=INK, fillColor=colors.white))
        drawing.add(String(x, y - 4, atom.symbol, textAnchor="middle", fontSize=10))
    return drawing


def circuit_diagram(specification: CircuitSpec) -> Drawing:
    if len(specification.components) < 2:
        raise ValueError("circuit requires at least two components")
    drawing = Drawing(360, 180)
    left, right, bottom, top = 30, 330, 45, 130
    drawing.add(Line(left, bottom, left, top, strokeColor=INK))
    drawing.add(Line(right, bottom, right, top, strokeColor=INK))
    drawing.add(Line(left, bottom, right, bottom, strokeColor=INK))
    step = (right - left) / len(specification.components)
    for index, component in enumerate(specification.components):
        centre = left + step * (index + 0.5)
        drawing.add(Line(left + step * index, top, centre - 18, top, strokeColor=INK))
        drawing.add(Line(centre + 18, top, left + step * (index + 1), top, strokeColor=INK))
        if component.kind == "cell":
            drawing.add(Line(centre - 4, top - 15, centre - 4, top + 15, strokeColor=INK))
            drawing.add(Line(centre + 5, top - 9, centre + 5, top + 9, strokeColor=INK))
        elif component.kind == "resistor":
            drawing.add(Rect(centre - 18, top - 8, 36, 16, strokeColor=INK, fillColor=None))
        elif component.kind in {"ammeter", "voltmeter"}:
            drawing.add(Circle(centre, top, 15, strokeColor=INK, fillColor=colors.white))
            symbol = "A" if component.kind == "ammeter" else "V"
            drawing.add(String(centre, top - 4, symbol, textAnchor="middle", fontSize=10))
        else:
            raise ValueError(f"unsupported circuit component: {component.kind}")
        if component.label:
            drawing.add(String(centre, top - 30, component.label, textAnchor="middle", fontSize=8))
    return drawing


def ray_diagram(specification: RaySpec) -> Drawing:
    if specification.focal_length <= 0:
        raise ValueError("focal length must be positive")
    if specification.object_distance <= 0 or specification.image_distance <= 0:
        raise ValueError("object and image distances must be positive")
    drawing = Drawing(360, 200)
    axis_y, lens_x = 100, 180
    scale = 1.25
    object_x = lens_x - specification.object_distance * scale
    image_x = lens_x + specification.image_distance * scale
    object_height, image_height = 58, -42
    drawing.add(Line(20, axis_y, 340, axis_y, strokeColor=INK, strokeWidth=0.8))
    drawing.add(Line(lens_x, 30, lens_x, 170, strokeColor=INK, strokeWidth=1.2))
    drawing.add(Polygon([lens_x, 170, lens_x - 4, 160, lens_x + 4, 160], fillColor=INK))
    drawing.add(Polygon([lens_x, 30, lens_x - 4, 40, lens_x + 4, 40], fillColor=INK))
    drawing.add(Line(object_x, axis_y, object_x, axis_y + object_height, strokeColor=INK))
    drawing.add(Polygon([object_x, axis_y + object_height, object_x - 4, axis_y + object_height - 9, object_x + 4, axis_y + object_height - 9], fillColor=INK))
    drawing.add(Line(image_x, axis_y, image_x, axis_y + image_height, strokeColor=INK))
    drawing.add(Polygon([image_x, axis_y + image_height, image_x - 4, axis_y + image_height + 9, image_x + 4, axis_y + image_height + 9], fillColor=INK))
    drawing.add(Line(object_x, axis_y + object_height, lens_x, axis_y + object_height, strokeColor=INK))
    drawing.add(Line(lens_x, axis_y + object_height, image_x, axis_y + image_height, strokeColor=INK))
    drawing.add(Line(object_x, axis_y + object_height, lens_x, axis_y, strokeColor=INK))
    drawing.add(Line(lens_x, axis_y, image_x, axis_y + image_height, strokeColor=INK))
    for sign in (-1, 1):
        focus_x = lens_x + sign * specification.focal_length * scale
        drawing.add(Line(focus_x, axis_y - 4, focus_x, axis_y + 4, strokeColor=INK))
        drawing.add(String(focus_x, axis_y - 16, "F", textAnchor="middle", fontSize=8))
    return drawing
