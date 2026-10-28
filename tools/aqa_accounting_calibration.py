# Compare AQA accounting item allocations with reference-paper evidence.

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
    from .calibration_common import (
        integer_band as _band,
    )
    from .calibration_common import (
        mark_sequence_inventory as _inventory,
    )
    from .calibration_common import (
        ordered_document_fingerprint as _fingerprint,
    )
    from .pdf_process import pdf_page_count as _pages
    from .pdf_process import pdf_text as _text
else:
    from atomic_json import write_json_atomically
    from calibration_common import (
        CALIBRATION_CONTENT_POLICY,
        paper_content_fingerprint,
        render_json,
    )
    from calibration_common import (
        integer_band as _band,
    )
    from calibration_common import (
        mark_sequence_inventory as _inventory,
    )
    from calibration_common import (
        ordered_document_fingerprint as _fingerprint,
    )
    from pdf_process import pdf_page_count as _pages
    from pdf_process import pdf_text as _text

ROOT = Path(__file__).resolve().parents[1]
CORPUS_ROOT = (
    ROOT / "Reference Corpus" / "a-level" / "aqa" / "accounting" / "accounting-7127"
)
GENERATOR_ROOT = ROOT / "Resources" / "accounting" / "aqa" / "generator"
OUTPUT = GENERATOR_ROOT / "data" / "difficulty-calibration.json"
# OUTPUT remains the immutable v1 compatibility path used by retained evidence.
REPORT_OUTPUT_V2 = OUTPUT.with_name("difficulty-calibration-v2.json")
MARK_PATTERN = re.compile(r"\[(\d+)\s+marks?\]", re.IGNORECASE)
WORD_PATTERN = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)?")


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
        quantitative = sum(question.task_operation == "transform" for question in mcqs)
        expected_quantitative = sum(
            question.task_operation == "transform"
            for question in rule.sections[0].questions[:10]
        )
        checks = {
            "current_printed_mark_sequence": (
                sequence == expected["current_printed_mark_sequence"]
            ),
            "page_count": page_band["minimum"] <= page_count <= page_band["maximum"],
            "unique_candidate_content_batch": len(fingerprints) == len(generated),
            "unique_public_source_batch": len(stimulus_fingerprints) == len(generated),
            "syllabus_coverage": topic_ids == rule.allowed_topic_ids,
            "declared_mcq_operation_mix": quantitative == expected_quantitative,
            "distinct_mcq_choices": all(
                len(set(question.choices)) == 4 for question in mcqs
            ),
        }
        papers[paper_number] = {
            "seeds": len(generated),
            "unique_candidate_content_fingerprints": len(fingerprints),
            "unique_public_source_fingerprints": len(stimulus_fingerprints),
            "printed_mark_sequence": sequence,
            "page_count": page_count,
            "document_word_count": word_count,
            "mark_scheme_page_count": scheme_pages,
            "covered_topic_ids": sorted(topic_ids),
            "mcq_demand": {
                "declared_transform": quantitative,
                "other_or_unspecified": len(mcqs) - quantitative,
            },
            "checks": checks,
        }
    return {"seed_start": seeds.start, "seed_stop": seeds.stop, "papers": papers}


def build_report(corpus_root: Path = CORPUS_ROOT) -> dict[str, Any]:
    reference = build_reference_profile(corpus_root)
    generated = build_generated_profile(reference)
    return {
        "schema_version": 2,
        "calibration_policy": CALIBRATION_CONTENT_POLICY,
        "qualification": "AQA A-level Accounting 7127",
        "purpose": (
            "aggregate structural-demand calibration against current paper structure; "
            "not a psychometric equivalence claim"
        ),
        "reference": reference,
        "generated": generated,
        "gates": {
            "automated_structural_demand": all(
                all(paper["checks"].values()) for paper in generated["papers"].values()
            ),
            "independent_subject_review": False,
            "student_trial": False,
            "psychometric_equivalence": False,
            "difficulty_verified": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Calibrate AQA Accounting structure.")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--corpus-root", type=Path, default=CORPUS_ROOT)
    args = parser.parse_args(argv)
    if args.write and args.check:
        parser.error("--write and --check are mutually exclusive")
    if args.check and not REPORT_OUTPUT_V2.exists():
        raise SystemExit(
            f"Version 2 report {REPORT_OUTPUT_V2} is missing; run tools/aqa_accounting_calibration.py --write"
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
                f"Version 2 report {REPORT_OUTPUT_V2} is missing or stale; run tools/aqa_accounting_calibration.py --write"
            )
        return 0
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
