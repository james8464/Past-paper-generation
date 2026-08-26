from __future__ import annotations

import pytest
from reportlab.graphics import renderPDF

from Backend.Core.overlay.humanities import (
    MapFeature,
    MapSpec,
    TimelineEvent,
    TimelineSpec,
    map_diagram,
    timeline_diagram,
)


def test_timeline_and_map_are_selectable_vector_diagrams() -> None:
    timeline = timeline_diagram(
        TimelineSpec(
            events=(
                TimelineEvent(1914, "War begins"),
                TimelineEvent(1918, "Armistice"),
            )
        )
    )
    map_drawing = map_diagram(
        MapSpec(
            boundary=((0, 0), (4, 0), (5, 2), (2, 4), (0, 2)),
            features=(MapFeature("Port", 1, 1, "settlement"),),
            scale_km=10,
            north=True,
        )
    )

    assert renderPDF.drawToString(timeline).startswith(b"%PDF-")
    assert renderPDF.drawToString(map_drawing).startswith(b"%PDF-")
    assert any(getattr(shape, "text", "") == "1914" for shape in timeline.contents)
    assert any(getattr(shape, "text", "") == "Port" for shape in map_drawing.contents)


def test_humanities_diagrams_reject_misleading_or_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="chronological"):
        timeline_diagram(
            TimelineSpec(
                events=(
                    TimelineEvent(1918, "Armistice"),
                    TimelineEvent(1914, "War begins"),
                )
            )
        )
    with pytest.raises(ValueError, match="boundary"):
        map_diagram(MapSpec(boundary=((0, 0), (1, 1)), features=()))
    with pytest.raises(ValueError, match="scale"):
        map_diagram(
            MapSpec(
                boundary=((0, 0), (1, 0), (1, 1)),
                features=(),
                scale_km=0,
            )
        )
