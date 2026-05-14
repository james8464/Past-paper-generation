from io import StringIO

from pastpapergen.tui import PlainProgressReporter, ProgressState, TerminalProgressReporter, progress_reporter


class TtyBuffer(StringIO):
    def isatty(self) -> bool:
        return True


def test_progress_state_tracks_seed_stage_and_questions():
    state = ProgressState()

    state.update("Using seed 12345")
    state.update("Generating question 3/12: 6(c) (Section B, 12 marks, Market failure)")
    state.update("Generated question 3/12: 6(c) (Market failure)")
    state.update("Rendering mark scheme")

    snapshot = state.snapshot()
    assert snapshot.seed == "12345"
    assert snapshot.current_stage == "Rendering mark scheme"
    assert snapshot.question_current == 3
    assert snapshot.question_total == 12
    assert snapshot.questions_done == 3
    assert snapshot.recent[-1] == "Rendering mark scheme"


def test_progress_state_tracks_overall_process_steps():
    state = ProgressState()

    state.update("Loading syllabus")
    state.update("Building paper blueprint")
    state.update("Rendering question paper")

    snapshot = state.snapshot()
    assert snapshot.completed_steps == 3
    assert snapshot.total_steps >= 8


def test_terminal_progress_reporter_renders_fps_dashboard():
    stream = TtyBuffer()
    reporter = TerminalProgressReporter(stream=stream, fps=12)

    reporter.update("Using seed 12345")
    reporter.update("Generating question 1/12: 1 (Section A, 5 marks, Demand)")
    reporter.render_once()

    output = stream.getvalue()
    assert "\x1b[H" in output
    assert "FPS 12" in output
    assert "Seed: 12345" in output
    assert "Steps:" in output
    assert "Question: 1/12" in output
    assert "Generating question 1/12" in output


def test_progress_reporter_uses_plain_output_when_not_tty():
    stream = StringIO()

    reporter = progress_reporter(stream=stream, fps=10)
    with reporter as progress:
        progress("Rendering source booklet")

    assert isinstance(reporter, PlainProgressReporter)
    assert "[progress] Rendering source booklet" in stream.getvalue()


def test_progress_reporter_uses_terminal_dashboard_when_tty():
    stream = TtyBuffer()

    reporter = progress_reporter(stream=stream, fps=10)

    assert isinstance(reporter, TerminalProgressReporter)
