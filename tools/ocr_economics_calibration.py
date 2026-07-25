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
    / "economics"
    / "economics-h060-h460-from-2019"
)
GENERATOR_ROOT = ROOT / "Resources" / "economics" / "ocr" / "generator"
OUTPUT = GENERATOR_ROOT / "data" / "difficulty-calibration.json"
WORD_PATTERN = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)?")
MARK_PATTERN = re.compile(r"\[(\d+)\]")
PAPER_NAMES = {
    "1": "microeconomics",
    "2": "macroeconomics",
    "3": "themes-in-economics",
}


def _command(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


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


def _band(values: list[int]) -> dict[str, float | int]:
    return {
        "minimum": min(values),
        "median": statistics.median(values),
        "maximum": max(values),
    }


def _sequence_inventory(sequences: list[list[int]]) -> list[dict[str, Any]]:
    counts = Counter(tuple(sequence) for sequence in sequences)
    return [
        {"sequence": list(sequence), "documents": count}
        for sequence, count in sorted(counts.items())
    ]


def build_reference_profile(corpus_root: Path = CORPUS_ROOT) -> dict[str, Any]:
    question_root = corpus_root / "question-papers"
    papers: dict[str, Any] = {}
    source_paths: list[Path] = []
    for paper, name in PAPER_NAMES.items():
        paths = sorted(
            path
            for path in question_root.glob(f"*-question-paper-{name}.pdf")
            if "correction" not in path.name
        )
        if not paths:
            raise ValueError(f"no official OCR Economics Paper {paper} references found")
        source_paths.extend(paths)
        texts = [_pdf_text(path) for path in paths]
        sequences = [
            [int(value) for value in MARK_PATTERN.findall(text)]
            for text in texts
        ]
        papers[paper] = {
            "documents": len(paths),
            "current_printed_mark_sequence": sequences[-1],
            "printed_mark_sequence_inventory": _sequence_inventory(sequences),
            "page_count": _band([_page_count(path) for path in paths]),
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
    from ocregen.configs import RULES
    from ocregen.generator import build_paper
    from ocregen.render_pdf import render_mark_scheme, render_question_paper
    from ocregen.syllabus import load_syllabus

    syllabus = load_syllabus(GENERATOR_ROOT / "data" / "syllabus.json")
    papers: dict[str, Any] = {}
    for paper_number in ("1", "2", "3"):
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
        mark_sequence = [
            question.marks
            for section in sample.sections
            for option in section.options
            for question in option.questions
        ]
        stimulus_words = len(
            WORD_PATTERN.findall(
                "\n".join(
                    text
                    for section in sample.sections
                    for option in section.options
                    for text in option.stimulus
                )
            )
        )
        with tempfile.TemporaryDirectory(
            prefix=f"examforge-ocr-calibration-{paper_number}-"
        ) as folder:
            question_path = Path(folder) / "question.pdf"
            scheme_path = Path(folder) / "scheme.pdf"
            render_question_paper(sample, question_path)
            render_mark_scheme(sample, scheme_path)
            page_count = _page_count(question_path)
            document_words = len(WORD_PATTERN.findall(_pdf_text(question_path)))
            scheme_pages = _page_count(scheme_path)

        expected = reference["papers"][paper_number]
        page_band = expected["page_count"]
        checks: dict[str, bool] = {
            "current_printed_mark_sequence": (
                mark_sequence == expected["current_printed_mark_sequence"]
            ),
            "page_count": page_band["minimum"] <= page_count <= page_band["maximum"],
            "unique_seed_batch": len(fingerprints) == len(generated),
            "unique_stimulus_batch": len(stimulus_fingerprints) == len(generated),
            "syllabus_coverage": topic_ids == rule.allowed_topic_ids,
        }
        paper_profile: dict[str, Any] = {
            "seeds": len(generated),
            "unique_fingerprints": len(fingerprints),
            "unique_stimulus_fingerprints": len(stimulus_fingerprints),
            "printed_mark_sequence": mark_sequence,
            "page_count": page_count,
            "document_word_count": document_words,
            "stimulus_word_count": stimulus_words,
            "mark_scheme_page_count": scheme_pages,
            "covered_topic_ids": sorted(topic_ids),
            "checks": checks,
        }
        if paper_number == "3":
            mcqs = [option.questions[0] for option in sample.sections[0].options]
            quantitative = sum(
                question.number in {"5", "10", "15", "20", "25", "30"}
                for question in mcqs
            )
            conceptual = len(mcqs) - quantitative
            checks["mcq_demand_mix"] = quantitative == 6 and conceptual == 24
            checks["distinct_mcq_choices"] = all(
                len(set(question.choices)) == 4 for question in mcqs
            )
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
        "qualification": "OCR A-level Economics H460",
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
        description="Calibrate OCR Economics generated-paper structure."
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
                f"{OUTPUT} is stale; run tools/ocr_economics_calibration.py --write"
            )
        return 0
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
