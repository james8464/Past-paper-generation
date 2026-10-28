# Compare OCR economics item allocations with reference-paper evidence.

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

if __package__:
    from .atomic_json import write_json_atomically
    from .calibration_common import (
        CALIBRATION_CONTENT_POLICY,
        paper_content_fingerprint,
        render_json,
    )
    from .calibration_common import integer_band as _band
    from .calibration_common import mark_sequence_inventory as _sequence_inventory
    from .calibration_common import ordered_document_fingerprint as _fingerprint
    from .pdf_process import pdf_page_count as _page_count
    from .pdf_process import pdf_text as _pdf_text
else:
    from atomic_json import write_json_atomically
    from calibration_common import (
        CALIBRATION_CONTENT_POLICY,
        paper_content_fingerprint,
        render_json,
    )
    from calibration_common import integer_band as _band
    from calibration_common import mark_sequence_inventory as _sequence_inventory
    from calibration_common import ordered_document_fingerprint as _fingerprint
    from pdf_process import pdf_page_count as _page_count
    from pdf_process import pdf_text as _pdf_text

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
REPORT_OUTPUT_V2 = OUTPUT.with_name("difficulty-calibration-v2.json")
WORD_PATTERN = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)?")
MARK_PATTERN = re.compile(r"\[(\d+)\]")
PAPER_NAMES = {
    "1": "microeconomics",
    "2": "macroeconomics",
    "3": "themes-in-economics",
}


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
            raise ValueError(
                f"no official OCR Economics Paper {paper} references found"
            )
        source_paths.extend(paths)
        texts = [_pdf_text(path) for path in paths]
        sequences = [
            [int(value) for value in MARK_PATTERN.findall(text)] for text in texts
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
        fingerprints = {paper_content_fingerprint(paper) for paper in generated}
        stimulus_fingerprints = {
            paper_content_fingerprint(paper, source_only=True) for paper in generated
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
            "unique_candidate_content_batch": len(fingerprints) == len(generated),
            "unique_public_source_batch": len(stimulus_fingerprints) == len(generated),
            "syllabus_coverage": topic_ids == rule.allowed_topic_ids,
        }
        paper_profile: dict[str, Any] = {
            "seeds": len(generated),
            "unique_candidate_content_fingerprints": len(fingerprints),
            "unique_public_source_fingerprints": len(stimulus_fingerprints),
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
        "schema_version": 2,
        "calibration_policy": CALIBRATION_CONTENT_POLICY,
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
    if args.check and not REPORT_OUTPUT_V2.exists():
        raise SystemExit(
            f"Version 2 report {REPORT_OUTPUT_V2} is missing; run tools/ocr_economics_calibration.py --write"
        )
    report = build_report(args.corpus_root)
    rendered = render_json(report)
    if args.write:
        write_json_atomically(REPORT_OUTPUT_V2, report)
        return 0
    if args.check:
        if (
            not REPORT_OUTPUT_V2.exists()
            or REPORT_OUTPUT_V2.read_text(encoding="utf-8") != rendered
        ):
            raise SystemExit(
                f"Version 2 report {REPORT_OUTPUT_V2} is missing or stale; run tools/ocr_economics_calibration.py --write"
            )
        return 0
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
