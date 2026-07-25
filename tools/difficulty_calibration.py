from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CORPUS_ROOT = (
    ROOT
    / "Reference Corpus"
    / "a-level"
    / "aqa"
    / "economics"
    / "economics-7136"
)
GENERATOR_ROOT = ROOT / "Resources" / "economics" / "aqa" / "generator"
OUTPUT = GENERATOR_ROOT / "data" / "difficulty-calibration.json"
WORD_PATTERN = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)?")
MARK_PATTERN = re.compile(r"\[(\d+) marks?\]", re.IGNORECASE)


def _command(*args: str) -> str:
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return result.stdout


def _page_count(path: Path) -> int:
    match = re.search(r"^Pages:\s+(\d+)$", _command("pdfinfo", str(path)), re.MULTILINE)
    if not match:
        raise ValueError(f"could not read page count from {path}")
    return int(match.group(1))


def _pdf_text(path: Path) -> str:
    return _command("pdftotext", "-layout", str(path), "-")


def _fingerprint(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode())
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def build_reference_profile(corpus_root: Path = CORPUS_ROOT) -> dict[str, Any]:
    question_root = corpus_root / "question-papers"
    insert_root = corpus_root / "inserts"
    papers: dict[str, Any] = {}
    source_paths: list[Path] = []
    for paper in ("1", "2", "3"):
        paths = sorted(question_root.glob(f"AQA-7136{paper}-QP-*.PDF"))
        if not paths:
            raise ValueError(f"no official AQA Economics Paper {paper} references found")
        source_paths.extend(paths)
        mark_sequences = [list(map(int, MARK_PATTERN.findall(_pdf_text(path)))) for path in paths]
        pages = [_page_count(path) for path in paths]
        if len({tuple(sequence) for sequence in mark_sequences}) != 1:
            raise ValueError(f"Paper {paper} does not have a stable printed mark sequence")
        paper_profile: dict[str, Any] = {
            "documents": len(paths),
            "printed_mark_sequence": mark_sequences[0],
            "page_count": {
                "minimum": min(pages),
                "median": statistics.median(pages),
                "maximum": max(pages),
            },
        }
        if paper == "3":
            inserts = sorted(insert_root.glob("AQA-71363-INS-*.PDF"))
            source_paths.extend(inserts)
            insert_words = [len(WORD_PATTERN.findall(_pdf_text(path))) for path in inserts]
            insert_pages = [_page_count(path) for path in inserts]
            paper_profile["source_insert"] = {
                "documents": len(inserts),
                "word_count": {
                    "minimum": min(insert_words),
                    "median": statistics.median(insert_words),
                    "maximum": max(insert_words),
                },
                "page_count": {
                    "minimum": min(insert_pages),
                    "median": statistics.median(insert_pages),
                    "maximum": max(insert_pages),
                },
            }
        papers[paper] = paper_profile
    return {
        "documents": len(source_paths),
        "fingerprint": _fingerprint(source_paths),
        "derived_aggregate_only": True,
        "retains_source_text": False,
        "papers": papers,
    }


def build_generated_profile(reference: dict[str, Any], seeds: range = range(100, 120)) -> dict[str, Any]:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    if str(GENERATOR_ROOT) not in sys.path:
        sys.path.insert(0, str(GENERATOR_ROOT))
    from aqaecongen.configs import RULES
    from aqaecongen.generator import build_paper
    from aqaecongen.render_pdf import render_question_paper, render_source_booklet
    from aqaecongen.syllabus import load_syllabus

    syllabus = load_syllabus(GENERATOR_ROOT / "data" / "syllabus.json")
    papers: dict[str, Any] = {}
    for paper_number in ("1", "2", "3"):
        rule = RULES[f"paper_{paper_number}"]
        generated = [build_paper(rule, syllabus, seed) for seed in seeds]
        fingerprints = {
            hashlib.sha256(
                "\n".join(
                    question.prompt
                    for section in paper.sections
                    for option in section.options
                    for question in option.questions
                ).encode()
            ).hexdigest()
            for paper in generated
        }
        topic_ids = {
            question.topic_id
            for paper in generated
            for section in paper.sections
            for option in section.options
            for question in option.questions
        }
        mark_sequence = [
            question.marks
            for section in generated[0].sections
            for option in section.options
            for question in option.questions
        ]
        with tempfile.TemporaryDirectory(prefix=f"examforge-calibration-{paper_number}-") as folder:
            question_path = Path(folder) / "question.pdf"
            render_question_paper(generated[0], question_path)
            page_count = _page_count(question_path)
            source_insert: dict[str, Any] | None = None
            if paper_number == "3":
                insert_path = Path(folder) / "insert.pdf"
                render_source_booklet(generated[0], insert_path)
                source_insert = {
                    "page_count": _page_count(insert_path),
                    "word_count": len(WORD_PATTERN.findall(_pdf_text(insert_path))),
                }

        expected = reference["papers"][paper_number]
        page_band = expected["page_count"]
        checks: dict[str, bool] = {
            "printed_mark_sequence": mark_sequence == expected["printed_mark_sequence"],
            "page_count": page_band["minimum"] <= page_count <= page_band["maximum"],
            "unique_seed_batch": len(fingerprints) == len(generated),
            "syllabus_coverage": topic_ids == rule.allowed_topic_ids,
        }
        paper_profile: dict[str, Any] = {
            "seeds": len(generated),
            "unique_fingerprints": len(fingerprints),
            "printed_mark_sequence": mark_sequence,
            "page_count": page_count,
            "covered_topic_ids": sorted(topic_ids),
            "checks": checks,
        }
        if paper_number == "3":
            assert source_insert is not None
            insert_band = expected["source_insert"]
            mcq_questions = [
                option.questions[0] for option in generated[0].sections[0].options
            ]
            quantitative = sum("index linked" in question.prompt for question in mcq_questions)
            conceptual = len(mcq_questions) - quantitative
            checks["source_insert_page_count"] = (
                insert_band["page_count"]["minimum"]
                <= source_insert["page_count"]
                <= insert_band["page_count"]["maximum"]
            )
            checks["source_insert_word_count"] = (
                insert_band["word_count"]["minimum"]
                <= source_insert["word_count"]
                <= insert_band["word_count"]["maximum"]
            )
            checks["mcq_demand_mix"] = quantitative >= 4 and conceptual >= 20
            paper_profile["source_insert"] = source_insert
            paper_profile["mcq_demand"] = {
                "quantitative": quantitative,
                "conceptual": conceptual,
            }
        papers[paper_number] = paper_profile
    return {"seed_start": seeds.start, "seed_stop": seeds.stop, "papers": papers}


def build_report(corpus_root: Path = CORPUS_ROOT) -> dict[str, Any]:
    reference = build_reference_profile(corpus_root)
    generated = build_generated_profile(reference)
    automated_pass = all(
        all(paper["checks"].values()) for paper in generated["papers"].values()
    )
    return {
        "schema_version": 1,
        "qualification": "AQA A-level Economics 7136",
        "purpose": "aggregate structural-demand calibration; not a psychometric equivalence claim",
        "reference": reference,
        "generated": generated,
        "gates": {
            "automated_structural_demand": automated_pass,
            "independent_subject_review": False,
            "student_trial": False,
            "psychometric_equivalence": False,
            "difficulty_verified": False,
        },
    }


def render_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Calibrate AQA Economics generated-paper demand.")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--corpus-root", type=Path, default=CORPUS_ROOT)
    args = parser.parse_args(argv)
    if args.write and args.check:
        parser.error("--write and --check are mutually exclusive")
    rendered = render_json(build_report(args.corpus_root))
    if args.write:
        OUTPUT.write_text(rendered, encoding="utf-8")
        return 0
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != rendered:
            raise SystemExit(f"{OUTPUT} is stale; run tools/difficulty_calibration.py --write")
        return 0
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
