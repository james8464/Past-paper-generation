# Check vector connections, not just the text labels of a printed NSI graph.

from math import atan2, cos, hypot, sin

import pymupdf


def _near(first, second):
    return hypot(first[0] - second[0], first[1] - second[1]) < 0.4


def _centres(page, nodes, drawings, *, radius=16, text_spans=False):
    circles = [
        drawing["rect"]
        for drawing in drawings
        if len(drawing["items"]) == 4
        and all(item[0] == "c" for item in drawing["items"])
        and abs(drawing["rect"].width - 2 * radius) < 0.4
        and abs(drawing["rect"].height - 2 * radius) < 0.4
    ]
    words = page.get_text("words")
    if text_spans:
        words = [
            (*span["bbox"], span["text"])
            for block in page.get_text("dict")["blocks"]
            for line in block.get("lines", [])
            for span in line["spans"]
        ]
    positions = {}
    for node in nodes:
        matches = []
        for word in words:
            if word[4] != node:
                continue
            word_centre = pymupdf.Point(
                (word[0] + word[2]) / 2, (word[1] + word[3]) / 2
            )
            for circle in circles:
                if circle.contains(word_centre):
                    matches.append(
                        ((circle.x0 + circle.x1) / 2, (circle.y0 + circle.y1) / 2)
                    )
        if len(matches) != 1:
            return None
        positions[node] = matches[0]
    return positions


# Require one figure with the exact edge stream and destination arrows.
#
# The current vector renderer draws 16-point-radius node circles. Position
# and page placement may change; connections are checked using their actual
# labelled centres. This does not certify raster visibility or accessibility.
def validate_graph(pdf, material, *, geometry=None):
    if geometry is not None:
        return _validate_routed_graph(pdf, material, geometry)
    figures = []
    for page in pdf:
        drawings = page.get_drawings()
        positions = _centres(page, material.nodes, drawings)
        if positions is not None:
            figures.append((drawings, positions))
    if len(figures) != 1:
        raise ValueError("Sommets du graphe absents, dupliqués ou séparés")
    drawings, positions = figures[0]
    edges, triangles = [], []
    for drawing in drawings:
        items = drawing["items"]
        if len(items) == 1 and items[0][0] == "l":
            start, end = items[0][1:]
            starts = [node for node, point in positions.items() if _near(start, point)]
            ends = [node for node, point in positions.items() if _near(end, point)]
            if len(starts) == len(ends) == 1:
                edges.append((starts[0], ends[0]))
        if (
            len(items) == 3
            and all(item[0] == "l" for item in items)
            and _near(items[-1][2], items[0][1])
        ):
            triangles.append([item[1] for item in items])
    expected = [(start, end) for start, end, _ in material.edges]
    if material.directed:
        matches = edges == expected
    else:
        matches = [frozenset(pair) for pair in edges] == [
            frozenset(pair) for pair in expected
        ]
    if not matches:
        raise ValueError("Les arcs du graphe divergent des sources vérifiées")
    if len(triangles) != (len(expected) if material.directed else 0):
        raise ValueError("Flèches du graphe absentes ou supplémentaires")
    for start, end in expected if material.directed else []:
        x1, y1 = positions[start]
        x2, y2 = positions[end]
        angle = atan2(y2 - y1, x2 - x1)
        tip = (x2 - 16 * cos(angle), y2 - 16 * sin(angle))
        arrow = [
            tip,
            *[
                (tip[0] - 7 * cos(angle + offset), tip[1] - 7 * sin(angle + offset))
                for offset in (-0.45, 0.45)
            ],
        ]
        found = [
            triangle
            for triangle in triangles
            if all(any(_near(point, vertex) for vertex in triangle) for point in arrow)
        ]
        if len(found) != 1:
            raise ValueError("Sens d'une flèche du graphe incompatible avec la source")


def _validate_routed_graph(pdf, material, geometry):
    figures = []
    for page in pdf:
        drawings = page.get_drawings()
        positions = _centres(
            page, material.nodes, drawings, radius=geometry.radius, text_spans=True
        )
        if positions is not None:
            figures.append((page, drawings, positions))
    if len(figures) != 1:
        raise ValueError("Sommets du graphe absents, dupliqués ou séparés")
    page, drawings, positions = figures[0]
    first = material.nodes[0]
    dx = positions[first][0] - geometry.positions[first][0]
    dy = -positions[first][1] - geometry.positions[first][1]

    def placed(point):
        return (point[0] + dx, -(point[1] + dy))

    if any(
        not _near(positions[node], placed(point))
        for node, point in geometry.positions.items()
    ):
        raise ValueError("Disposition du graphe incompatible avec la source")
    for node, centre in positions.items():
        matches = []
        for span in page.get_texttrace():
            if "".join(chr(char[0]) for char in span["chars"]) != node:
                continue
            box = pymupdf.Rect(span["bbox"])
            if (
                hypot(
                    (box.x0 + box.x1) / 2 - centre[0], (box.y0 + box.y1) / 2 - centre[1]
                )
                < geometry.radius / 2
            ):
                matches.append((span, box))
        if len(matches) != 1 or abs(matches[0][0]["size"] - geometry.font_size) >= 0.05:
            raise ValueError("Libellé de sommet absent ou illisible")
        if any(
            hypot(point[0] - centre[0], point[1] - centre[1]) > geometry.radius - 1
            for point in (
                matches[0][1].tl,
                matches[0][1].tr,
                matches[0][1].bl,
                matches[0][1].br,
            )
        ):
            raise ValueError("Libellé de sommet hors de son cercle")
    edges, triangles = [], []
    for drawing in drawings:
        items = drawing["items"]
        if len(items) == 1 and items[0][0] == "l":
            edges.append(items[0][1:])
        if (
            len(items) == 3
            and all(item[0] == "l" for item in items)
            and _near(items[-1][2], items[0][1])
        ):
            triangles.append([item[1] for item in items])
    if len(edges) != len(geometry.routes) or any(
        not _near(actual[0], placed(route.start))
        or not _near(actual[1], placed(route.end))
        for actual, route in zip(edges, geometry.routes, strict=True)
    ):
        raise ValueError("Les arcs du graphe divergent des sources vérifiées")
    arrows = [route.arrow for route in geometry.routes if route.arrow]
    if len(triangles) != len(arrows) or any(
        not all(
            any(_near(placed(point), vertex) for vertex in triangle) for point in arrow
        )
        for triangle, arrow in zip(triangles, arrows, strict=True)
    ):
        raise ValueError("Sens d'une flèche du graphe incompatible avec la source")
    for route in geometry.routes:
        expected = placed(route.label_origin)
        matches = [
            span
            for span in page.get_texttrace()
            if "".join(chr(char[0]) for char in span["chars"]) == route.label
            and span["chars"]
            and _near(span["chars"][0][2], expected)
            and abs(span["size"] - geometry.font_size) < 0.05
        ]
        if len(matches) != 1:
            raise ValueError("Poids du graphe absent ou mal placé")
