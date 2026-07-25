from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CORPUS_ROOT = (
    ROOT
    / "Reference Corpus"
    / "a-level"
    / "ocr"
    / "computer-science"
    / "computer-science-h046-h446-from-2015"
)
GENERATOR_ROOT = ROOT / "Resources" / "computer-science" / "ocr" / "generator"
OUTPUT = GENERATOR_ROOT / "data" / "difficulty-calibration.json"
WORD_PATTERN = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)?")
MARK_PATTERN = re.compile(r"\[(\d+)\]")
PAPER_NAMES = {"1": "computer-systems", "2": "algorithms-and-programming"}


def _command(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def _page_count(path: Path) -> int:
    match = re.search(r"^Pages:\s+(\d+)$", _command("pdfinfo", str(path)), re.MULTILINE)
    if not match:
        raise ValueError(f"could not read page count from {path}")
    return int(match.group(1))


def _pdf_text(path: Path) -> str:
    return _command("pdftotext", "-layout", str(path), "-")


def _band(values: list[int]) -> dict[str, float | int]:
    return {
        "minimum": min(values),
        "median": statistics.median(values),
        "maximum": max(values),
    }


def _fingerprint(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode())
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _inventory(sequences: list[list[int]]) -> list[dict[str, Any]]:
    counts = Counter(tuple(sequence) for sequence in sequences)
    return [
        {"sequence": list(sequence), "documents": count}
        for sequence, count in sorted(counts.items())
    ]


def build_reference_profile(corpus_root: Path = CORPUS_ROOT) -> dict[str, Any]:
    question_root = corpus_root / "question-papers"
    papers: dict[str, Any] = {}
    all_paths: list[Path] = []
    for paper, name in PAPER_NAMES.items():
        paths = sorted(question_root.glob(f"*-question-paper-{name}.pdf"))
        if not paths:
            raise ValueError(f"no official OCR H446/{paper} references found")
        all_paths.extend(paths)
        texts = [_pdf_text(path) for path in paths]
        sequences = [
            [int(value) for value in MARK_PATTERN.findall(text)] for text in texts
        ]
        papers[paper] = {
            "documents": len(paths),
            "current_printed_mark_sequence": sequences[-1],
            "printed_mark_sequence_inventory": _inventory(sequences),
            "page_count": _band([_page_count(path) for path in paths]),
            "document_word_count": _band(
                [len(WORD_PATTERN.findall(text)) for text in texts]
            ),
        }
    return {
        "documents": len(all_paths),
        "fingerprint": _fingerprint(all_paths),
        "derived_aggregate_only": True,
        "retains_source_text": False,
        "papers": papers,
    }


def build_generated_profile(
    reference: dict[str, Any], seeds: range = range(100, 120)
) -> dict[str, Any]:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    if str(GENERATOR_ROOT) not in sys.path:
        sys.path.insert(0, str(GENERATOR_ROOT))
    from ocrcsgen.configs import RULES
    from ocrcsgen.generator import build_paper
    from ocrcsgen.render_pdf import render_mark_scheme, render_question_paper
    from ocrcsgen.syllabus import load_syllabus

    syllabus = load_syllabus(GENERATOR_ROOT / "data" / "syllabus.json")
    papers: dict[str, Any] = {}
    for paper_number in ("1", "2"):
        rule = RULES[f"paper_{paper_number}"]
        generated = [build_paper(rule, syllabus, seed) for seed in seeds]
        paper_fingerprints = {
            hashlib.sha256(
                json.dumps(paper.model_dump(), sort_keys=True).encode()
            ).hexdigest()
            for paper in generated
        }
        stimulus_fingerprints = {
            hashlib.sha256(
                "\n".join(
                    text
                    for section in paper.sections
                    for option in section.options
                    for text in option.stimulus
                ).encode()
            ).hexdigest()
            for paper in generated
        }
        topics = {
            question.topic_id
            for paper in generated
            for section in paper.sections
            for option in section.options
            for question in option.questions
        }
        sample = generated[0]
        questions = [
            question
            for section in sample.sections
            for option in section.options
            for question in option.questions
        ]
        mark_sequence = [question.marks for question in questions]
        kind_counts = Counter(question.kind for question in questions)
        with tempfile.TemporaryDirectory(
            prefix=f"examforge-ocr-cs-calibration-{paper_number}-"
        ) as folder:
            question_path = Path(folder) / "question.pdf"
            scheme_path = Path(folder) / "scheme.pdf"
            render_question_paper(sample, question_path)
            render_mark_scheme(sample, scheme_path)
            page_count = _page_count(question_path)
            scheme_pages = _page_count(scheme_path)
            document_words = len(WORD_PATTERN.findall(_pdf_text(question_path)))

        expected = reference["papers"][paper_number]
        page_band = expected["page_count"]
        checks = {
            "current_printed_mark_sequence": (
                mark_sequence == expected["current_printed_mark_sequence"]
            ),
            "page_count": page_band["minimum"] <= page_count <= page_band["maximum"],
            "question_count": len(questions) == (41 if paper_number == "1" else 40),
            "unique_seed_batch": len(paper_fingerprints) == len(generated),
            "unique_stimulus_batch": len(stimulus_fingerprints) == len(generated),
            "syllabus_coverage": topics == rule.allowed_topic_ids,
            "mixed_technical_demand": (
                kind_counts["programming"] >= 3
                and kind_counts["extended_response"] >= 2
                and kind_counts["analysis"] >= 8
            ),
        }
        papers[paper_number] = {
            "seeds": len(generated),
            "unique_fingerprints": len(paper_fingerprints),
            "unique_stimulus_fingerprints": len(stimulus_fingerprints),
            "printed_mark_sequence": mark_sequence,
            "question_count": len(questions),
            "page_count": page_count,
            "mark_scheme_page_count": scheme_pages,
            "document_word_count": document_words,
            "question_kind_counts": dict(sorted(kind_counts.items())),
            "covered_topic_ids": sorted(topics),
            "checks": checks,
        }
    return {"seed_start": seeds.start, "seed_stop": seeds.stop, "papers": papers}


def build_report(corpus_root: Path = CORPUS_ROOT) -> dict[str, Any]:
    reference = build_reference_profile(corpus_root)
    generated = build_generated_profile(reference)
    automated_pass = all(
        all(paper["checks"].values()) for paper in generated["papers"].values()
    )
    return {
        "schema_version": 1,
        "qualification": "OCR A-level Computer Science H446",
        "purpose": (
            "aggregate structural-demand calibration against current paper structure; "
            "not a psychometric equivalence claim"
        ),
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
    parser = argparse.ArgumentParser(
        description="Calibrate OCR H446 generated-paper structure."
    )
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
            raise SystemExit(
                f"{OUTPUT} is stale; run tools/ocr_computer_science_calibration.py --write"
            )
        return 0
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
