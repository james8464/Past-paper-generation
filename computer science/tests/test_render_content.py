from cspapergen.cli import generate_package


def test_question_paper_contains_aqa_style_cover_and_rail(tmp_path):
    paths = generate_package(output_dir=tmp_path, seed=3, dry_run=True)
    data = paths["question_paper"].read_bytes()

    assert b"A-level" in data
    assert b"COMPUTER SCIENCE" in data
    assert b"Paper 2" in data
    assert b"Do not write" in data
    assert b"outside the" in data
    assert b"cs-paper-2-source-booklet" not in data


def test_mark_scheme_contains_aqa_style_table_headings(tmp_path):
    paths = generate_package(output_dir=tmp_path, seed=3, dry_run=True)
    data = paths["mark_scheme"].read_bytes()

    assert b"Mark scheme" in data
    assert b"Qu" in data
    assert b"Pt" in data
    assert b"Marking guidance" in data
    assert b"Total" in data
    assert b"marks" in data
