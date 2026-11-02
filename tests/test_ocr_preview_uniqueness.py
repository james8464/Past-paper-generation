"""Keep deterministic OCR previews distinct without bypassing publication checks."""

import hashlib
import json
import random
import subprocess
import sys
from pathlib import Path

import pytest
from ocrcsgen.configs import RULES
from ocrcsgen.generator import _distinct_short_answer_points, _question, build_paper
from ocrcsgen.syllabus import load_syllabus

from Backend.Core.assessment_package import _extract_items, validate_cross_paper_quality
from Backend.Core.subjects.computer_science_contracts import SumTrace

ROOT = Path(__file__).resolve().parents[1]
SYLLABUS = load_syllabus(
    ROOT / "Resources/computer-science/ocr/generator/data/syllabus.json"
)


def _digest(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _items(paper):
    return _extract_items(
        paper.model_dump(mode="json"),
        subject="computer_science_ocr",
        paper_number="2",
    )


def test_known_seed_replaces_the_colliding_knowledge_not_its_label() -> None:
    paper = build_paper(RULES["paper_2"], SYLLABUS, 270100)
    first = paper.sections[6].options[0].questions[1]
    second = paper.sections[8].options[0].questions[1]
    assert first.number == "7(b)" and second.number == "9(b)"
    assert first.topic_id == second.topic_id == "algorithms-2"
    assert first.marks == second.marks == 2
    assert "functions, procedures and recursion" in first.prompt
    assert "object-oriented programming" in second.prompt
    assert "object-oriented programming" in second.mark_scheme[0]
    assert "functions, procedures and recursion" not in second.mark_scheme[0]
    validate_cross_paper_quality(_items(paper))

    # Captured from af914047: every other task, raw source and RNG output is
    # byte-equivalent under canonical JSON; only this one colliding slot differs.
    unchanged = paper.model_dump(mode="json")
    unchanged["sections"][8]["options"][0]["questions"].pop(1)
    assert (
        _digest(unchanged)
        == "a12a9c6ca5526663177fbe779fc29f01085cc6a442af1b21731a17c15cfd69c3"
    )


@pytest.mark.parametrize("seed", [0, 1, 2, 42, 123, 456, 270100, 270101])
def test_finite_preview_seeds_pass_the_unmodified_duplicate_guard(seed: int) -> None:
    paper = build_paper(RULES["paper_2"], SYLLABUS, seed)
    validate_cross_paper_quality(_items(paper))


@pytest.mark.parametrize(
    ("paper", "expected"),
    [
        ("1", "612cc9f71d422787d8260f624c2cc7c7e026092634078e40f8b1f123f9624a75"),
        ("2", "431ecfaba018c519383ff8a0d8f89d64c195ba38b2e0881aaa593c869f94aa83"),
    ],
)
def test_noncolliding_seed_preserves_the_complete_prior_blueprint(
    paper: str,
    expected: str,
) -> None:
    # These exact complete-model digests were captured before repair at af914047.
    assert (
        _digest(
            build_paper(RULES[f"paper_{paper}"], SYLLABUS, 123).model_dump(mode="json")
        )
        == expected
    )


def test_renaming_an_item_does_not_bypass_the_duplicate_guard() -> None:
    first = _items(build_paper(RULES["paper_2"], SYLLABUS, 123))[0]
    with pytest.raises(ValueError, match="cross-paper duplication"):
        validate_cross_paper_quality([first, {**first, "id": "different-label"}])


def test_early_collision_does_not_steal_a_later_original_knowledge_point() -> None:
    paper = build_paper(RULES["paper_2"], SYLLABUS, 2)
    repaired = paper.sections[6].options[0].questions[0]
    later = paper.sections[6].options[0].questions[1]
    assert "object-oriented programming" in repaired.prompt
    assert "object-oriented programming" in repaired.structured_mark_scheme[0].text
    assert "functions, procedures and recursion" in later.prompt
    unchanged = paper.model_dump(mode="json")
    unchanged["sections"][6]["options"][0]["questions"].pop(0)
    assert (
        _digest(unchanged)
        == "b31db04a3bba2aa16decf0ac89eaa777442fd8ae8c1b33b92aed2b30ee24c689"
    )


def test_exhausted_genuine_point_pool_fails_instead_of_rewording_the_same_task() -> (
    None
):
    topic = next(topic for topic in SYLLABUS.topics if topic.id == "algorithms-2")
    rule = RULES["paper_2"].sections[6].questions[1]
    trace = SumTrace(values=[1, 2, 3], initial_total=0, threshold=1)
    tasks = []
    for index in [*range(1, len(topic.points) + 1), 1]:
        question = _question(
            rule,
            "99",
            index,
            topic,
            "a school robotics club",
            1234,
            random.Random(123),
            trace,
        )
        tasks.append((question, rule, topic, index, "the school robotics club"))
    with pytest.raises(
        ValueError, match="No distinct short-answer syllabus point remains"
    ):
        _distinct_short_answer_points(tasks)


def test_known_seed_completes_actual_public_preview_publication(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "bridge.py"),
            "generate",
            "--subject",
            "computer_science_ocr",
            "--paper",
            "2",
            "--seed",
            "270100",
            "--dry-run",
            "--provider",
            "ollama",
            "--model",
            "unused-offline",
            "--api-key",
            "",
            "--output",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    events = [json.loads(line) for line in result.stdout.splitlines()]
    assert events[-1]["type"] == "done"
    manifest = json.loads(next(tmp_path.glob("*-package.json")).read_text())
    assert manifest["request"]["preview_mode"] is True
    assert set(manifest["outputs"]) == {
        "question_paper",
        "mark_scheme",
        "assessment_package",
    }
    for item in manifest["outputs"].values():
        path = tmp_path / item["filename"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
        if path.suffix == ".pdf":
            assert item["pdf_validation"]["presentation"]["first_page_notice"] is True
