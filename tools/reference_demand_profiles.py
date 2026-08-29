from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Backend.Core.paths import REPO_ROOT  # noqa: E402
from Backend.Core.reference_demand import (  # noqa: E402
    PROFILES_PATH,
    ReferenceDemandDocument,
    ReferenceDemandProfile,
)

CORPUS_ROOT = REPO_ROOT / "Reference Corpus" / "a-level"

COMMAND_WORDS = (
    "analyse",
    "analyze",
    "assess",
    "calculate",
    "compare",
    "complete",
    "construct",
    "define",
    "describe",
    "discuss",
    "draw",
    "evaluate",
    "examine",
    "explain",
    "give",
    "identify",
    "justify",
    "name",
    "outline",
    "prepare",
    "recommend",
    "select",
    "state",
    "suggest",
    "write",
)
COMMAND_PATTERN = re.compile(
    r"\b(" + "|".join(COMMAND_WORDS) + r")\b",
    flags=re.IGNORECASE,
)
IGNORED_LINES = (
    "do not write",
    "please write",
    "write your answer",
    "write the question",
    "you must write",
    "need extra space",
    "copyright holder",
)
MCQ_BLOCKS = {
    ("aqa/economics", "3"): 30,
    ("ocr/economics", "3"): 30,
}


@dataclass(frozen=True)
class CorpusFamily:
    family_id: str
    board: str
    root: Path
    paper_patterns: dict[str, str]


FAMILIES = (
    CorpusFamily(
        "aqa/accounting",
        "aqa",
        CORPUS_ROOT / "aqa" / "accounting" / "accounting-7127" / "question-papers",
        {"1": "AQA-71271-QP-*.PDF", "2": "AQA-71272-QP-*.PDF"},
    ),
    CorpusFamily(
        "aqa/business",
        "aqa",
        CORPUS_ROOT / "aqa" / "business" / "business-7132" / "question-papers",
        {
            "1": "AQA-71321-QP-*.PDF",
            "2": "AQA-71322-QP-*.PDF",
            "3": "AQA-71323-QP-*.PDF",
        },
    ),
    CorpusFamily(
        "aqa/computer-science",
        "aqa",
        CORPUS_ROOT
        / "aqa"
        / "computer-science"
        / "computer-science-7517"
        / "question-papers",
        {"1": "AQA-75171-QP-*.PDF", "2": "AQA-75172-QP-*.PDF"},
    ),
    CorpusFamily(
        "aqa/economics",
        "aqa",
        CORPUS_ROOT / "aqa" / "economics" / "economics-7136" / "question-papers",
        {
            "1": "AQA-71361-QP-*.PDF",
            "2": "AQA-71362-QP-*.PDF",
            "3": "AQA-71363-QP-*.PDF",
        },
    ),
    CorpusFamily(
        "ocr/computer-science",
        "ocr",
        CORPUS_ROOT
        / "ocr"
        / "computer-science"
        / "computer-science-h046-h446-from-2015"
        / "question-papers",
        {
            "1": "*-question-paper-computer-systems.pdf",
            "2": "*-question-paper-algorithms-and-programming.pdf",
        },
    ),
    CorpusFamily(
        "ocr/economics",
        "ocr",
        CORPUS_ROOT
        / "ocr"
        / "economics"
        / "economics-h060-h460-from-2019"
        / "question-papers",
        {
            "1": "*-question-paper-microeconomics.pdf",
            "2": "*-question-paper-macroeconomics.pdf",
            "3": "*-question-paper-themes-in-economics.pdf",
        },
    ),
    CorpusFamily(
        "pearson-edexcel/economics-a-2015",
        "pearson-edexcel",
        CORPUS_ROOT
        / "pearson-edexcel"
        / "economics-a-2015"
        / "al15-economics-a"
        / "question-papers",
        {
            "1": "9*[Ee][Cc]0*01*que*20*.pdf",
            "2": "9*[Ee][Cc]0*02*que*20*.pdf",
            "3": "9*[Ee][Cc]0*03*que*20*.pdf",
        },
    ),
)


def extract_reference_features(
    text: str,
    *,
    board: str,
    family_id: str | None = None,
    paper_id: str | None = None,
) -> dict[str, list[Any]]:
    if board == "aqa":
        mark_pattern = re.compile(r"\[(\d+)\s+marks?\]", re.IGNORECASE)
    elif board == "ocr":
        mark_pattern = re.compile(r"\[(\d+)\]")
    elif board == "pearson-edexcel":
        mark_pattern = re.compile(r"(?m)^\s*\((\d{1,2})\)\s*$")
    else:
        raise ValueError(f"unsupported reference board: {board}")

    mcq_count = MCQ_BLOCKS.get((family_id or "", str(paper_id or "")), 0)
    command_text = text
    commands: list[str] = ["select"] * mcq_count
    if mcq_count:
        constructed = re.search(
            rf"(?m)^\s*{mcq_count + 1}\*?\s+",
            text,
        )
        if constructed is None:
            raise ValueError(
                f"could not locate question {mcq_count + 1} after MCQ block"
            )
        command_text = text[constructed.start():]
    for raw_line in command_text.splitlines():
        line = " ".join(raw_line.split())
        lowered = line.casefold()
        if not line or any(ignored in lowered for ignored in IGNORED_LINES):
            continue
        if re.search(r"\bwhich\s+(?:one\s+)?of\s+the\s+following\b", lowered):
            commands.append("select")
            continue
        if "to what extent" in lowered:
            commands.append("evaluate")
            continue
        match = COMMAND_PATTERN.search(line)
        if match is None:
            continue
        command = match.group(1).casefold()
        if command == "write" and not re.search(
            r"\bwrite\s+(?:a|an|code|down|pseudocode|sql|the)",
            lowered,
        ):
            continue
        commands.append("analyse" if command == "analyze" else command)
    return {
        "marks": [int(value) for value in mark_pattern.findall(text)],
        "command_words": commands,
    }


def build_document() -> ReferenceDemandDocument:
    profiles: list[ReferenceDemandProfile] = []
    for family in FAMILIES:
        family_profiles: list[ReferenceDemandProfile] = []
        for paper_id, pattern in family.paper_patterns.items():
            paths = _reference_paths(family.root, pattern)
            if not paths:
                raise ValueError(
                    f"no official references for {family.family_id} paper {paper_id}"
                )
            features = [
                extract_reference_features(
                    _pdf_text(path),
                    board=family.board,
                    family_id=family.family_id,
                    paper_id=paper_id,
                )
                for path in paths
            ]
            marks = [value for feature in features for value in feature["marks"]]
            commands = [
                value for feature in features for value in feature["command_words"]
            ]
            if not marks or not commands:
                raise ValueError(
                    f"reference extraction is incomplete for {family.family_id} "
                    f"paper {paper_id}"
                )
            profile = ReferenceDemandProfile(
                family_id=family.family_id,
                paper_id=paper_id,
                comparison_basis=(
                    f"Aggregate mark tariffs and command-word frequencies from "
                    f"{len(paths)} official {family.board.upper()} A-level question "
                    "papers; no source wording retained."
                ),
                source_document_count=len(paths),
                source_fingerprint=_fingerprint(paths),
                mark_band_distribution=_distribution(_mark_band(mark) for mark in marks),
                command_word_distribution=_distribution(commands),
                demand_distribution=_distribution(_mark_demand(mark) for mark in marks),
                distribution_tolerance=0.85,
            )
            profiles.append(profile)
            family_profiles.append(profile)
        if family.family_id == "aqa/computer-science":
            profiles.extend(_question_bank_profiles(family_profiles))
    return ReferenceDemandDocument(
        schema_version=1,
        purpose=(
            "Copyright-safe aggregate demand fingerprints for reference-shaped "
            "authoring and automated form checks; not psychometric evidence."
        ),
        derived_aggregate_only=True,
        retains_source_text=False,
        profiles=sorted(profiles, key=lambda item: (item.family_id, item.paper_id)),
    )


def _reference_paths(root: Path, pattern: str) -> list[Path]:
    paths = [path for path in root.glob(pattern) if "correction" not in path.name.casefold()]
    current = [path for path in paths if re.search(r"(?:JUN2[2-6]|202[2-6])", path.name, re.I)]
    return sorted(current or paths)


def _pdf_text(path: Path) -> str:
    reader = PdfReader(path)
    return "\n".join(
        page.extract_text(extraction_mode="layout") or "" for page in reader.pages
    )


def _fingerprint(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _question_bank_profiles(
    parents: list[ReferenceDemandProfile],
) -> list[ReferenceDemandProfile]:
    documents = sum(profile.source_document_count for profile in parents)
    digest = hashlib.sha256(
        "".join(profile.source_fingerprint for profile in parents).encode("ascii")
    ).hexdigest()
    mark_distribution = _mean_distribution(
        [profile.mark_band_distribution for profile in parents]
    )
    command_distribution = _mean_distribution(
        [profile.command_word_distribution for profile in parents]
    )
    demand_distribution = _mean_distribution(
        [profile.demand_distribution for profile in parents]
    )
    return [
        ReferenceDemandProfile(
            family_id="aqa/computer-science",
            paper_id=paper_id,
            assessment_kind="question-bank",
            comparison_basis=(
                "Focused-practice target derived from aggregate mark tariffs and "
                f"command-word frequencies across {documents} official AQA A-level "
                "Computer Science papers; no source wording retained."
            ),
            source_document_count=documents,
            source_fingerprint=digest,
            mark_band_distribution=mark_distribution,
            command_word_distribution=command_distribution,
            demand_distribution=demand_distribution,
            distribution_tolerance=1.4,
        )
        for paper_id in ("bank-4.2", "bank-4.10", "bank-4.12")
    ]


def _mean_distribution(values: list[dict[str, float]]) -> dict[str, float]:
    keys = sorted({key for value in values for key in value})
    raw = {
        key: sum(value.get(key, 0) for value in values) / len(values)
        for key in keys
    }
    return _renormalise(raw)


def _distribution(values: Any) -> dict[str, float]:
    counts = Counter(values)
    return _renormalise(dict(counts))


def _renormalise(values: dict[str, float]) -> dict[str, float]:
    total = sum(values.values())
    if total <= 0:
        raise ValueError("cannot build an empty reference distribution")
    result = {key: round(value / total, 6) for key, value in sorted(values.items())}
    difference = round(1.0 - sum(result.values()), 6)
    largest = max(result, key=result.get)
    result[largest] = round(result[largest] + difference, 6)
    return result


def _mark_band(marks: int) -> str:
    if marks <= 4:
        return "short"
    if marks <= 9:
        return "medium"
    return "extended"


def _mark_demand(mark: int) -> str:
    if mark >= 10:
        return "high"
    if mark <= 3:
        return "low"
    return "standard"


def render(document: ReferenceDemandDocument) -> str:
    return json.dumps(
        document.model_dump(mode="json"),
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    ) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build aggregate reference-demand profiles from official papers."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    value = render(build_document())
    if args.write:
        PROFILES_PATH.write_text(value, encoding="utf-8")
        return 0
    if args.check:
        if not PROFILES_PATH.exists() or PROFILES_PATH.read_text(encoding="utf-8") != value:
            raise SystemExit(
                "reference demand profiles are stale; run "
                "tools/reference_demand_profiles.py --write"
            )
        return 0
    print(value, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
