"""Check vector connections, not just the text labels of a printed NSI graph."""

from math import atan2, cos, hypot, sin

import pymupdf


def _near(first, second):
    return hypot(first[0] - second[0], first[1] - second[1]) < 0.4


def _centres(page, nodes, drawings):
    circles = [
        drawing["rect"]
        for drawing in drawings
        if len(drawing["items"]) == 4
        and all(item[0] == "c" for item in drawing["items"])
        and abs(drawing["rect"].width - 32) < 0.4
        and abs(drawing["rect"].height - 32) < 0.4
    ]
    positions = {}
    for node in nodes:
        matches = []
        for word in page.get_text("words"):
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


def validate_graph(pdf, material):
    """Require one figure with the exact edge stream and destination arrows.

    The current vector renderer draws 16-point-radius node circles. Position
    and page placement may change; connections are checked using their actual
    labelled centres. This does not certify raster visibility or accessibility.
    """
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
