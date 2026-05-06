from pathlib import Path

import generate_paper
from pastpapergen.cli import default_output_dir


def test_default_output_dir_is_downloads():
    assert default_output_dir() == Path.home() / "Downloads"


def test_runner_accepts_simple_paper_choice(monkeypatch, tmp_path):
    calls = []
    answers = iter(["2", "n", ""])

    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(generate_paper, "default_output_dir", lambda: tmp_path)
    monkeypatch.setattr(
        generate_paper,
        "generate_package",
        lambda **kwargs: calls.append(kwargs)
        or {
            "question_paper": tmp_path / "paper-2-question-paper.pdf",
            "source_booklet": tmp_path / "paper-2-source-booklet.pdf",
            "mark_scheme": tmp_path / "paper-2-mark-scheme.pdf",
        },
    )

    assert generate_paper.main() == 0

    call = calls[0]
    assert callable(call.pop("progress"))
    assert call == {
        "paper": "2",
        "syllabus_path": generate_paper.PROJECT_ROOT / "data/syllabus_seed.json",
        "output_dir": tmp_path,
        "seed": None,
        "model": "qwen2.5:14b",
        "ollama_url": "http://localhost:11434",
        "dry_run": True,
    }


def test_runner_prints_progress_messages(monkeypatch, tmp_path, capsys):
    answers = iter(["1", "y", ""])

    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(generate_paper, "default_output_dir", lambda: tmp_path)

    def fake_generate_package(**kwargs):
        kwargs["progress"]("Generating question 1/12: 1 (Section A, 5 marks)")
        return {
            "question_paper": tmp_path / "paper-1-question-paper.pdf",
            "source_booklet": tmp_path / "paper-1-source-booklet.pdf",
            "mark_scheme": tmp_path / "paper-1-mark-scheme.pdf",
        }

    monkeypatch.setattr(generate_paper, "generate_package", fake_generate_package)

    assert generate_paper.main() == 0

    assert "Generating question 1/12: 1 (Section A, 5 marks)" in capsys.readouterr().out
