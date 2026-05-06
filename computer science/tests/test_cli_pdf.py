import subprocess

from cspapergen.cli import generate_package


def test_generate_package_writes_question_paper_and_mark_scheme_only(tmp_path):
    paths = generate_package(output_dir=tmp_path, seed=42, dry_run=True)

    assert sorted(paths) == ["mark_scheme", "question_paper"]
    assert paths["question_paper"].name == "cs-paper-2-question-paper.pdf"
    assert paths["mark_scheme"].name == "cs-paper-2-mark-scheme.pdf"
    assert paths["question_paper"].exists()
    assert paths["mark_scheme"].exists()
    assert not (tmp_path / "cs-paper-2-source-booklet.pdf").exists()
    assert not list(tmp_path.glob("*audit*"))


def test_generated_pdfs_are_a4(tmp_path):
    paths = generate_package(output_dir=tmp_path, seed=42, dry_run=True)

    for path in paths.values():
        output = subprocess.check_output(["pdfinfo", str(path)], text=True)
        assert "Page size:       595.32 x 841.92 pts (A4)" in output
