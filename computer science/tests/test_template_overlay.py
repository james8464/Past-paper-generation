import subprocess

from cspapergen.cli import generate_package
from cspapergen.template_overlay import apply_question_paper_template


def test_question_paper_template_overlay_writes_a4_pdf(tmp_path):
    paths = generate_package(output_dir=tmp_path, seed=44, dry_run=True)
    templated = tmp_path / "templated.pdf"

    apply_question_paper_template(paths["question_paper"], templated, reference_pdf=paths["question_paper"])

    output = subprocess.check_output(["pdfinfo", str(templated)], text=True)
    assert "Page size:       595.32 x 841.92 pts (A4)" in output
    assert templated.stat().st_size > 0
