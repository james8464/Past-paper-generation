from __future__ import annotations

import hashlib
import subprocess

from pypdf import PdfReader

from cspapergen.cli import generate_package
from cspapergen.generator import build_paper1_blueprint
from cspapergen.syllabus import load_syllabus
from cspapergen.validation import validate_blueprint


def test_paper1_blueprint_is_deterministic_and_totals_100() -> None:
    syllabus = load_syllabus()
    first, first_context = build_paper1_blueprint(syllabus, seed=123)
    second, second_context = build_paper1_blueprint(syllabus, seed=123)

    assert first.model_dump() == second.model_dump()
    assert first_context.model_dump() == second_context.model_dump()
    assert first.paper_code == "7517/1"
    assert first.paper_number == "1"
    assert first.delivery_mode == "on-screen"
    assert sum(question.total_marks for question in first.questions) == 100
    assert {question.topic_id for question in first.questions} <= {
        "4.1",
        "4.2",
        "4.3",
        "4.4",
        "4.13",
    }
    validate_blueprint(first, syllabus)


def test_paper1_blueprint_and_scenario_vary_by_seed() -> None:
    syllabus = load_syllabus()
    generated = [build_paper1_blueprint(syllabus, seed=seed) for seed in range(12)]

    assert len({context.skeleton_program for _, context in generated}) >= 8
    assert len({blueprint.model_dump_json() for blueprint, _ in generated}) >= 8


def test_paper1_skeleton_program_is_valid_python() -> None:
    _, context = build_paper1_blueprint(load_syllabus(), seed=77)

    compile(context.skeleton_program, "skeleton.py", "exec")
    assert "def add_record(records):" in context.skeleton_program
    assert "def print_report(records):" in context.skeleton_program
    assert 'load_records("cs-paper-1-practice-data.txt")' in context.skeleton_program
    assert context.data_file.count("\n") == 8


def test_paper1_package_contains_all_on_screen_exam_artifacts(tmp_path) -> None:
    paths = generate_package(output_dir=tmp_path, paper="1", seed=42, dry_run=True)

    assert list(paths) == [
        "question_paper",
        "preliminary_material",
        "electronic_answer_document",
        "skeleton_program",
        "data_file",
        "mark_scheme",
    ]
    assert all(path.exists() and path.stat().st_size > 0 for path in paths.values())
    assert paths["question_paper"].name == "cs-paper-1-question-paper.pdf"
    assert paths["preliminary_material"].name == "cs-paper-1-preliminary-material.pdf"
    assert paths["electronic_answer_document"].name == "cs-paper-1-electronic-answer-document.pdf"
    assert paths["skeleton_program"].suffix == ".py"
    assert paths["data_file"].suffix == ".txt"

    for role in ("question_paper", "preliminary_material", "electronic_answer_document", "mark_scheme"):
        info = subprocess.check_output(["pdfinfo", str(paths[role])], text=True)
        assert "Page size:       595.32 x 841.92 pts (A4)" in info


def test_paper1_rendered_documents_use_correct_identity(tmp_path) -> None:
    paths = generate_package(output_dir=tmp_path, paper="1", seed=42, dry_run=True)

    question_text = subprocess.check_output(
        ["pdftotext", "-layout", str(paths["question_paper"]), "-"],
        text=True,
    )
    mark_text = subprocess.check_output(
        ["pdftotext", "-layout", "-f", "1", "-l", "1", str(paths["mark_scheme"]), "-"],
        text=True,
    )
    preliminary_text = subprocess.check_output(
        ["pdftotext", "-layout", str(paths["preliminary_material"]), "-"],
        text=True,
    )
    assert "Paper 1" in question_text
    assert "Electronic Answer Document" in question_text
    assert "7517/1" in question_text
    assert "Paper 1" in mark_text
    assert "7517/1" in mark_text
    assert "Skeleton Program" in preliminary_text

    reader = PdfReader(paths["question_paper"])
    assert len(reader.pages) == 24
    assert "Section A" in (reader.pages[1].extract_text() or "")
    assert "trace table" in (reader.pages[6].extract_text() or "").casefold()
    assert "Section B" in (reader.pages[7].extract_text() or "")
    assert "Section C" in (reader.pages[10].extract_text() or "")
    assert "Section D" in (reader.pages[15].extract_text() or "")
    assert "END OF QUESTIONS" in (reader.pages[19].extract_text() or "")


def test_electronic_answer_document_has_one_fillable_field_per_part(tmp_path) -> None:
    paths = generate_package(output_dir=tmp_path, paper="1", seed=42, dry_run=True)
    reader = PdfReader(paths["electronic_answer_document"])
    fields = reader.get_fields()
    blueprint, _context = build_paper1_blueprint(load_syllabus(), seed=42)
    expected_fields = {
        f"question_{question.number}_{part.label}"
        for question in blueprint.questions
        for part in question.parts
    }

    assert fields is not None
    assert set(fields) == expected_fields
    assert all(field.get("/FT") == "/Tx" for field in fields.values())
    assert all(int(field.get("/Ff", 0)) & 4096 for field in fields.values())


def test_paper1_artifacts_change_between_seeds(tmp_path) -> None:
    first = generate_package(output_dir=tmp_path / "a", paper="1", seed=11, dry_run=True)
    second = generate_package(output_dir=tmp_path / "b", paper="1", seed=12, dry_run=True)

    roles = {"question_paper", "preliminary_material", "skeleton_program", "data_file", "mark_scheme"}
    for role in roles:
        first_hash = hashlib.sha256(first[role].read_bytes()).hexdigest()
        second_hash = hashlib.sha256(second[role].read_bytes()).hexdigest()
        assert first_hash != second_hash, role
