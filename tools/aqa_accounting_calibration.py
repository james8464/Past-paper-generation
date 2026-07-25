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
    ROOT / "Reference Corpus" / "a-level" / "aqa" / "accounting" / "accounting-7127"
)
GENERATOR_ROOT = ROOT / "Resources" / "accounting" / "aqa" / "generator"
OUTPUT = GENERATOR_ROOT / "data" / "difficulty-calibration.json"
MARK_PATTERN = re.compile(r"\[(\d+)\s+marks?\]", re.IGNORECASE)
WORD_PATTERN = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)?")


def _command(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def _text(path: Path) -> str:
    return _command("pdftotext", "-layout", str(path), "-")


def _pages(path: Path) -> int:
    match = re.search(r"^Pages:\s+(\d+)$", _command("pdfinfo", str(path)), re.MULTILINE)
    if not match:
        raise ValueError(f"could not read page count from {path}")
    return int(match.group(1))


def _band(values: list[int]) -> dict[str, int | float]:
    return {
        "minimum": min(values),
        "median": statistics.median(values),
        "maximum": max(values),
    }


def _inventory(values: list[list[int]]) -> list[dict[str, Any]]:
    counts = Counter(tuple(value) for value in values)
    return [
        {"sequence": list(sequence), "documents": count}
        for sequence, count in sorted(counts.items())
    ]


def _fingerprint(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode())
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def build_reference_profile(corpus_root: Path = CORPUS_ROOT) -> dict[str, Any]:
    question_root = corpus_root / "question-papers"
    source_paths: list[Path] = []
    papers: dict[str, Any] = {}
    current_names = {
        "1": "AQA-71271-QP-JUN25.PDF",
        "2": "AQA-71272-QP-JUN25.PDF",
    }
    for paper in ("1", "2"):
        paths = sorted(question_root.glob(f"AQA-7127{paper}-QP-*.PDF"))
        if not paths:
            raise ValueError(f"no AQA Accounting Paper {paper} references found")
        current = question_root / current_names[paper]
        source_paths.extend(paths)
        texts = [_text(path) for path in paths]
        sequences = [
            [int(value) for value in MARK_PATTERN.findall(text)] for text in texts
        ]
        papers[paper] = {
            "documents": len(paths),
            "current_printed_mark_sequence": [
                int(value) for value in MARK_PATTERN.findall(_text(current))
            ],
            "printed_mark_sequence_inventory": _inventory(sequences),
            "page_count": _band([_pages(path) for path in paths]),
            "document_word_count": _band(
                [len(WORD_PATTERN.findall(text)) for text in texts]
            ),
        }
    return {
        "documents": len(source_paths),
        "fingerprint": _fingerprint(source_paths),
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
    from aqaaccountgen.configs import RULES
    from aqaaccountgen.generator import build_paper
    from aqaaccountgen.render_pdf import render_mark_scheme, render_question_paper
    from aqaaccountgen.syllabus import load_syllabus

    syllabus = load_syllabus(GENERATOR_ROOT / "data" / "syllabus.json")
    papers: dict[str, Any] = {}
    for paper_number in ("1", "2"):
        rule = RULES[f"paper_{paper_number}"]
        generated = [build_paper(rule, syllabus, seed) for seed in seeds]
        fingerprints = {
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
        topic_ids = {
            question.topic_id
            for paper in generated
            for section in paper.sections
            for option in section.options
            for question in option.questions
        }
        sample = generated[0]
        sequence = [
            question.marks
            for section in sample.sections
            for option in section.options
            for question in option.questions
        ]
        with tempfile.TemporaryDirectory(
            prefix=f"examforge-aqa-accounting-{paper_number}-"
        ) as folder:
            question_path = Path(folder) / "question.pdf"
            scheme_path = Path(folder) / "scheme.pdf"
            render_question_paper(sample, question_path)
            render_mark_scheme(sample, scheme_path)
            page_count = _pages(question_path)
            word_count = len(WORD_PATTERN.findall(_text(question_path)))
            scheme_pages = _pages(scheme_path)
        expected = reference["papers"][paper_number]
        page_band = expected["page_count"]
        mcqs = sample.sections[0].options[0].questions[:10]
        checks = {
            "current_printed_mark_sequence": (
                sequence == expected["current_printed_mark_sequence"]
            ),
            "page_count": page_band["minimum"] <= page_count <= page_band["maximum"],
            "unique_seed_batch": len(fingerprints) == len(generated),
            "unique_stimulus_batch": len(stimulus_fingerprints) == len(generated),
            "syllabus_coverage": topic_ids == rule.allowed_topic_ids,
            "mcq_demand_mix": (
                sum("revenue of" in question.prompt for question in mcqs) == 2
            ),
            "distinct_mcq_choices": all(
                len(set(question.choices)) == 4 for question in mcqs
            ),
        }
        papers[paper_number] = {
            "seeds": len(generated),
            "unique_fingerprints": len(fingerprints),
            "unique_stimulus_fingerprints": len(stimulus_fingerprints),
            "printed_mark_sequence": sequence,
            "page_count": page_count,
            "document_word_count": word_count,
            "mark_scheme_page_count": scheme_pages,
            "covered_topic_ids": sorted(topic_ids),
            "mcq_demand": {"quantitative": 2, "conceptual": 8},
            "checks": checks,
        }
    return {"seed_start": seeds.start, "seed_stop": seeds.stop, "papers": papers}


def build_report(corpus_root: Path = CORPUS_ROOT) -> dict[str, Any]:
    reference = build_reference_profile(corpus_root)
    generated = build_generated_profile(reference)
    return {
        "schema_version": 1,
        "qualification": "AQA A-level Accounting 7127",
        "purpose": (
            "aggregate structural-demand calibration against current paper structure; "
            "not a psychometric equivalence claim"
        ),
        "reference": reference,
        "generated": generated,
        "gates": {
            "automated_structural_demand": all(
                all(paper["checks"].values())
                for paper in generated["papers"].values()
            ),
            "independent_subject_review": False,
            "student_trial": False,
            "psychometric_equivalence": False,
            "difficulty_verified": False,
        },
    }


def render_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Calibrate AQA Accounting structure.")
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
                f"{OUTPUT} is stale; run tools/aqa_accounting_calibration.py --write"
            )
        return 0
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
