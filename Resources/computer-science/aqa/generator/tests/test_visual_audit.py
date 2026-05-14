from cspapergen.cli import generate_package
from cspapergen.visual_audit import audit_pdfs


def test_visual_audit_reports_zero_difference_for_same_pdf(tmp_path):
    paths = generate_package(output_dir=tmp_path, seed=123, dry_run=True)

    report = audit_pdfs(
        reference=paths["question_paper"],
        generated=paths["question_paper"],
        output_dir=tmp_path / "audit",
        first=1,
        last=1,
        dpi=72,
    )

    assert report["pages"][0]["mean_delta"] == 0
    assert report["pages"][0]["changed_ratio"] == 0
