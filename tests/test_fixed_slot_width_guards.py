"""Owned fixed-slot helper controls; no app renderer or saved paper is exercised."""

import math

import pytest
from reportlab.pdfbase import pdfmetrics

from Backend.Core import layout_master as subject


class RecordingCanvas:
    def __init__(self):
        self.calls = []

    def saveState(self):
        self.calls.append(("save",))

    def restoreState(self):
        self.calls.append(("restore",))

    def setFont(self, name, size):
        self.calls.append(("font", name, size))

    def drawString(self, x, y, text):
        self.calls.append(("left", x, y, text))

    def drawCentredString(self, x, y, text):
        self.calls.append(("centre", x, y, text))

    def drawRightString(self, x, y, text):
        self.calls.append(("right", x, y, text))


def slot(*, width=100, height=30, font=11, leading=13, minimum=None, align="left"):
    return subject.TextSlot(
        subject.Rect(10, 10, 10 + width, 10 + height),
        "Helvetica",
        font,
        leading,
        align,
        minimum,
    )


@pytest.mark.parametrize("text", ["WWWW", "a WWWW", "a\nWWWW"])
def test_every_oversized_token_is_refused_including_first_paragraph_token(text):
    with pytest.raises(subject.LayoutConformanceError, match="word"):
        subject.wrap_text(text, "Helvetica", 11, 10)


@pytest.mark.parametrize("text", ["WWWW", "a WWWW"])
def test_draw_tries_allowed_smaller_fonts_before_refusing_a_word(text):
    canvas = RecordingCanvas()
    width = pdfmetrics.stringWidth("WWWW", "Helvetica", 10)
    used = subject.draw_text_slot(
        canvas, 200, slot(width=width, height=40, minimum=10), text
    )
    assert used == 10
    for call in canvas.calls:
        if call[0] in {"left", "centre", "right"}:
            assert pdfmetrics.stringWidth(call[-1], "Helvetica", used) <= width


def test_impossible_width_never_paints_any_content():
    canvas = RecordingCanvas()
    with pytest.raises(subject.LayoutConformanceError):
        subject.draw_text_slot(canvas, 200, slot(width=1, minimum=10), "WWWW")
    assert canvas.calls == []


@pytest.mark.parametrize("minimum", [10.1, 10.125])
def test_off_grid_minimum_is_tried_exactly_without_undershooting(minimum):
    canvas = RecordingCanvas()
    width = pdfmetrics.stringWidth("WWWW", "Helvetica", minimum)
    used = subject.draw_text_slot(
        canvas, 200, slot(width=width, minimum=minimum), "WWWW"
    )
    assert used == minimum
    assert ("font", "Helvetica", minimum) in canvas.calls


@pytest.mark.parametrize("minimum", [10.1, 10.125])
def test_failed_fit_at_exact_minimum_ends_with_ordinary_overflow(minimum):
    canvas = RecordingCanvas()
    with pytest.raises(subject.LayoutConformanceError, match="text overflows"):
        subject.draw_text_slot(
            canvas, 200, slot(width=1, font=minimum, minimum=minimum), "WWWW"
        )
    assert canvas.calls == []


@pytest.mark.parametrize("field", ["font", "leading", "minimum"])
@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan, 0, -1])
def test_nonpositive_or_nonfinite_typography_is_refused_before_drawing(field, value):
    with pytest.raises(ValueError):
        slot(**{field: value})


def test_font_reduction_must_make_progress_without_unbounded_loop(monkeypatch):
    attempted = []

    def always_too_wide(*args):
        attempted.append(args[2])
        if len(attempted) > 2:
            raise RuntimeError("bounded canary: repeated sizing did not progress")
        raise subject.LayoutConformanceError("word cannot fit")

    monkeypatch.setattr(subject, "wrap_text", always_too_wide)
    with pytest.raises(subject.LayoutConformanceError):
        subject.draw_text_slot(RecordingCanvas(), 200, slot(font=1e20, minimum=1), "x")
    assert attempted == [1e20]


@pytest.mark.parametrize("align", ["left", "centre", "right"])
def test_normal_text_preserves_font_alignment_and_state(align):
    canvas = RecordingCanvas()
    assert subject.draw_text_slot(canvas, 200, slot(align=align), "Hello") == 11
    assert canvas.calls == [
        ("save",),
        ("font", "Helvetica", 11),
        (align, {"left": 10, "centre": 60, "right": 110}[align], 179, "Hello"),
        ("restore",),
    ]


def test_height_shrink_and_unshrinkable_height_still_work():
    canvas = RecordingCanvas()
    assert (
        subject.draw_text_slot(
            canvas, 200, slot(width=30, height=24, minimum=10), "one two"
        )
        == 10
    )
    with pytest.raises(subject.LayoutConformanceError):
        subject.draw_text_slot(RecordingCanvas(), 200, slot(height=1), "Hello")


def test_unknown_font_error_is_not_reclassified_as_width_refusal():
    canvas = RecordingCanvas()
    unknown = subject.TextSlot(
        subject.Rect(0, 0, 100, 20), "Owned-Unknown-Font", 11, 13
    )
    with pytest.raises(KeyError):
        subject.draw_text_slot(canvas, 200, unknown, "Hello")
    assert canvas.calls == []


def test_large_finite_font_search_has_logarithmic_work(monkeypatch):
    original = subject.wrap_text
    attempted = []

    def bounded_wrap(*args):
        attempted.append(args[2])
        if len(attempted) > 80:
            raise RuntimeError("bounded canary: excessive font probes")
        return original(*args)

    monkeypatch.setattr(subject, "wrap_text", bounded_wrap)
    canvas = RecordingCanvas()
    assert (
        subject.draw_text_slot(
            canvas, 200, slot(width=10, font=1e9, leading=1e9, minimum=1), "WWWW"
        )
        == 2.5
    )
    assert len(attempted) <= 40


@pytest.mark.parametrize("wanted", [1.25, 1.75, 2.0, 2.25, 2.75, 3.25])
def test_large_grid_indices_preserve_the_largest_small_fitting_font(
    monkeypatch, wanted
):
    original = subject.wrap_text
    attempted = []

    def bounded_wrap(*args):
        attempted.append(args[2])
        if len(attempted) > 64:
            raise RuntimeError("bounded canary: excessive exact-grid probes")
        return original(*args)

    monkeypatch.setattr(subject, "wrap_text", bounded_wrap)
    font = math.nextafter(float(2**52), 0)
    width = pdfmetrics.stringWidth("WWWW", "Helvetica", wanted)
    candidate = subject.TextSlot(
        subject.Rect(0, 0, width, 30), "Helvetica", font, font, minimum_font_size=1
    )
    assert (
        subject.draw_text_slot(
            RecordingCanvas(),
            200,
            candidate,
            "WWWW",
        )
        == wanted
    )
    assert len(attempted) <= 64


@pytest.mark.parametrize("font,minimum", [(11, 9), (11.125, 9.1), (10.13, 9.125)])
@pytest.mark.parametrize("width,height", [(12, 40), (30, 24), (100, 30), (1, 1)])
@pytest.mark.parametrize("text", ["one two", "WWWW", "one\ntwo three"])
@pytest.mark.parametrize("align", ["left", "centre", "right"])
def test_search_matches_small_exhaustive_descending_grid(
    font, minimum, width, height, text, align
):
    size = font
    expected = None
    while size >= minimum:
        try:
            lines = subject.wrap_text(text, "Helvetica", size, width)
        except subject.LayoutConformanceError:
            pass
        else:
            if len(lines) * 13 * (size / font) <= height + 1e-6:
                expected = size
                break
        next_size = round(size - 0.25, 2)
        if next_size < minimum < size:
            next_size = minimum
        size = next_size
    canvas = RecordingCanvas()
    candidate = slot(
        width=width, height=height, font=font, minimum=minimum, align=align
    )
    if expected is None:
        with pytest.raises(subject.LayoutConformanceError):
            subject.draw_text_slot(canvas, 200, candidate, text)
        assert canvas.calls == []
    else:
        assert subject.draw_text_slot(canvas, 200, candidate, text) == expected
        assert next(call for call in canvas.calls if call[0] == "font")[2] == expected
