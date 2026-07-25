from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

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
    for paper in ("1", "2"):
        paths = generate_package(
            paper=paper,
            syllabus_path=ROOT / "data" / "syllabus.json",
            output_dir=tmp_path / paper,
            seed=123,
        )
        assert set(paths) == {"question_paper", "mark_scheme"}
        assert page_count(paths["question_paper"]) == 36
        assert all(path.stat().st_size > 2000 for path in paths.values())


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
