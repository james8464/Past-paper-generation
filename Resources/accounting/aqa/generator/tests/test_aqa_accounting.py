from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from pypdf import PdfReader

from aqaaccountgen.cli import generate_package
from aqaaccountgen.configs import RULES
from aqaaccountgen.generator import build_paper
from aqaaccountgen.syllabus import load_syllabus


ROOT = Path(__file__).resolve().parents[1]
SYLLABUS = load_syllabus(ROOT / "data" / "syllabus.json")
EXPECTED = {
    "paper_1": [1] * 10 + [6, 7, 5, 2, 14, 6, 6, 8, 6, 25, 25],
    "paper_2": [1] * 10 + [3, 6, 3, 8, 4, 8, 2, 6, 8, 1, 5, 6, 25, 25],
}


def page_count(path: Path) -> int:
    text = subprocess.run(
        ["pdfinfo", str(path)], check=True, capture_output=True, text=True
    ).stdout
    return int(next(line.split(":", 1)[1] for line in text.splitlines() if line.startswith("Pages:")))


def test_exact_current_mark_sequences_and_totals() -> None:
    for key, rule in RULES.items():
        generated = build_paper(rule, SYLLABUS, 123)
        sequence = [
            question.marks
            for section in generated.sections
            for option in section.options
            for question in option.questions
        ]
        assert sequence == EXPECTED[key]
        assert sum(section.option_marks for section in rule.sections) == 120


def test_multi_seed_determinism_uniqueness_and_scope() -> None:
    for rule in RULES.values():
        papers = [build_paper(rule, SYLLABUS, seed) for seed in range(20)]
        assert build_paper(rule, SYLLABUS, 7) == build_paper(rule, SYLLABUS, 7)
        fingerprints = {
            hashlib.sha256(
                json.dumps(paper.model_dump(), sort_keys=True).encode()
            ).hexdigest()
            for paper in papers
        }
        assert len(fingerprints) == 20
        assert {
            question.topic_id
            for paper in papers
            for section in paper.sections
            for option in section.options
            for question in option.questions
        } == rule.allowed_topic_ids


def test_both_packages_render_36_page_question_papers(tmp_path: Path) -> None:
    mark_scheme_pages = {"1": 26, "2": 28}
    for paper in ("1", "2"):
        paths = generate_package(
            paper=paper,
            syllabus_path=ROOT / "data" / "syllabus.json",
            output_dir=tmp_path / paper,
            seed=123,
        )
        assert set(paths) == {"question_paper", "mark_scheme"}
        assert page_count(paths["question_paper"]) == 36
        assert page_count(paths["mark_scheme"]) == mark_scheme_pages[paper]
        assert all(path.stat().st_size > 2000 for path in paths.values())


def test_paper_one_section_a_matches_measured_case_and_account_pages(tmp_path: Path) -> None:
    paths = generate_package(
        paper="1",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=123,
    )

    pages = PdfReader(paths["question_paper"]).pages
    assert "DO NOT WRITE ON THIS PAGE" in (pages[6].extract_text() or "")
    assert "Additional information" in (pages[7].extract_text() or "")
    assert "13.1" not in (pages[8].extract_text() or "")
    assert "Sales journal" in (pages[9].extract_text() or "")
    assert "Sales Ledger Control Account" in (pages[10].extract_text() or "")
    assert "not yet been accounted for" in (pages[11].extract_text() or "")
    assert "Income statement" in (pages[12].extract_text() or "")
    assert "Capital Accounts" in (pages[15].extract_text() or "")
    assert "Drawings for the year" in (pages[17].extract_text() or "")
    assert "Profit and loss appropriation account" in (pages[18].extract_text() or "")
    assert "employ a bookkeeper" in (pages[21].extract_text() or "")
    assert "Advise the owner" in (pages[22].extract_text() or "")
    assert "DO NOT WRITE ON THIS PAGE" in (pages[26].extract_text() or "")
    assert "Statement of changes in equity" in (pages[27].extract_text() or "")
    assert "Advise the investor" in (pages[28].extract_text() or "")
    assert "There are no questions printed on this page" in (
        pages[32].extract_text() or ""
    )
    assert "Additional page, if required" in (pages[33].extract_text() or "")
    assert "Independent practice material" in (pages[35].extract_text() or "")


def test_paper_one_mark_scheme_matches_reference_question_sequence(tmp_path: Path) -> None:
    paths = generate_package(
        paper="1",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=123,
    )

    pages = PdfReader(paths["mark_scheme"]).pages
    expected = {
        7: "Objective test answers",
        8: "trade discount",
        9: "non-current assets section",
        10: "sales ledger control account",
        11: "sales account",
        12: "Prepare the income statement",
        15: "usefulness of the income statement",
        17: "partners' capital accounts",
        18: "profit and loss appropriation account",
        19: "formal partnership agreement",
        20: "Advise the owner",
        22: "Question 16 continued",
        23: "Advise the investor",
        25: "Question 17 continued",
    }
    assert len(pages) == 26
    for page_index, label in expected.items():
        assert label in (pages[page_index].extract_text() or "")


def test_invalid_paper_is_rejected(tmp_path: Path) -> None:
    try:
        generate_package(
            paper="3",
            syllabus_path=ROOT / "data" / "syllabus.json",
            output_dir=tmp_path,
        )
    except ValueError as error:
        assert "1 or 2" in str(error)
    else:
        raise AssertionError("invalid paper was accepted")
