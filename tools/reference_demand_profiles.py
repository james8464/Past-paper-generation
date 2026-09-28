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

from Backend.Core.assessment_objectives import objective_policy_for  # noqa: E402
from Backend.Core.paths import REPO_ROOT  # noqa: E402
from Backend.Core.reference_demand import (  # noqa: E402
    PROFILES_PATH,
    ReferenceDemandDocument,
    ReferenceDemandProfile,
)

CORPUS_ROOT = REPO_ROOT / "Reference Corpus" / "a-level"

COMMAND_WORDS = (
    "advise",
    "analyse",
    "analyze",
    "assess",
    "calculate",
    "compare",
    "complete",
    "construct",
    "define",
    "describe",
    "design",
    "develop",
    "discuss",
    "draw",
    "estimate",
    "evaluate",
    "examine",
    "explain",
    "find",
    "give",
    "hence",
    "identify",
    "justify",
    "name",
    "outline",
    "prepare",
    "prove",
    "recommend",
    "select",
    "show",
    "sketch",
    "solve",
    "state",
    "trace",
    "suggest",
    "determine",
    "deduce",
    "verify",
    "write",
    "convert",
    "simplify",
)
COMMAND_PATTERN = re.compile(
    r"\b(" + "|".join(COMMAND_WORDS) + r")\b",
    flags=re.IGNORECASE,
)
GENERAL_COMMAND_PATTERN = re.compile(
    r"\b("
    + "|".join(
        word
        for word in COMMAND_WORDS
        if word not in {"design", "develop", "trace", "convert", "simplify"}
    )
    + r")\b",
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
    ("aqa/accounting", "1"): 10,
    ("aqa/accounting", "2"): 10,
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
        "aqa/mathematics",
        "aqa",
        CORPUS_ROOT / "aqa" / "mathematics" / "mathematics-7357" / "question-papers",
        {
            "1": "AQA-73571-QP-*.PDF",
            "2": "AQA-73572-QP-*.PDF",
            "3": "AQA-73573-QP-*.PDF",
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
        command_text = text[constructed.start() :]
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
        pattern = (
            COMMAND_PATTERN
            if objective_policy_for(family_id or "").computational
            else GENERAL_COMMAND_PATTERN
        )
        match = pattern.search(line)
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


def extract_reference_items(
    text: str,
    *,
    board: str,
    family_id: str | None = None,
    paper_id: str | None = None,
    source_name: str | None = None,
) -> list[dict[str, Any]]:
    """Pair each tariff with its nearest local command, retaining no prose."""

    policy = objective_policy_for(family_id or "")
    if policy.computational:
        # Layout extraction can put thousands of padding spaces between a task
        # and its tariff. Count source content, not invisible page geometry.
        text = "\n".join(" ".join(line.split()) for line in text.splitlines())
    matches = list(_mark_pattern(board).finditer(text))
    mcq_count = MCQ_BLOCKS.get((family_id or "", str(paper_id or "")), 0)
    items: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        marks = int(match.group(1))
        window = text[
            max(
                matches[index - 1].end() if index and policy.computational else 0,
                match.start() - 12000 if policy.computational else match.start() - 3000,
            ) : match.start()
        ]
        command = (
            "select"
            if index < mcq_count
            else _nearest_command(window, computational=policy.computational)
        )
        operation = _reference_operation(command)
        response_mode = _reference_response_mode(marks, command)
        if policy.computational:
            # Prefer the actual imperative at a part boundary, not incidental
            # verbs in the scenario, table rows or 'show your working' reminders.
            task_matches = list(
                re.finditer(
                    r"(?im)^(?:\([a-zivx]+\)[ \t]+){0,2}(?:\d(?:[ \t]+\d)?(?:[ \t]*\.[ \t]*\d+)?[ \t]+)?"
                    r"(" + "|".join(COMMAND_WORDS) + r")\b",
                    window,
                )
            )
            task_matches = [
                candidate
                for candidate in task_matches
                if not window[candidate.start() :]
                .lower()
                .startswith("show your working")
            ]
            task_text = window
            if task_matches:
                first = task_matches[0]
                command = first.group(1).lower()
                task_text = window[first.start() :]
            operation = policy.task_operation({"prompt": task_text}, command, "")
            if "program source code" in " ".join(window.lower().split()):
                command = "write"
            elif "screen capture" in window.lower() and "test" in window.lower():
                command = "evaluate"
            response_mode = policy.response_mode(operation, command, marks)
        items.append(
            {
                "marks": marks,
                "command_word": command,
                "demand_band": _item_demand(marks, command),
                "response_mode": response_mode,
                "cognitive_operation": operation,
            }
        )
    if source_name == "AQA-75171-QP-JUN25.PDF" and family_id == "aqa/computer-science":
        # June 2025 MS PDF14 explicitly discounts Q06.4. Preserve its tariff in
        # structural totals, but never use it as positive cognitive-demand evidence.
        if (
            len(items) != 39
            or sum(item["marks"] for item in items) != 100
            or items[22]["marks"] != 1
        ):
            raise ValueError("discounted AQA item inventory no longer aligns")
        items[22]["demand_eligible"] = False
    return items


def _mark_pattern(board: str) -> re.Pattern[str]:
    if board == "aqa":
        return re.compile(r"\[(\d+)\s+marks?\]", re.IGNORECASE)
    if board == "ocr":
        return re.compile(r"\[(\d+)\]")
    if board == "pearson-edexcel":
        return re.compile(r"(?m)^\s*\((\d{1,2})\)\s*$")
    raise ValueError(f"unsupported reference board: {board}")


def _nearest_command(window: str, *, computational: bool = False) -> str:
    commands: list[tuple[int, str]] = []
    for raw_line in window.splitlines():
        line = " ".join(raw_line.split())
        lowered = line.casefold()
        if not line or any(ignored in lowered for ignored in IGNORED_LINES):
            continue
        if re.search(r"\bwhich\s+(?:one\s+)?of\s+the\s+following\b", lowered):
            commands.append((window.rfind(raw_line), "select"))
            continue
        if "to what extent" in lowered:
            commands.append((window.rfind(raw_line), "evaluate"))
            continue
        match = (COMMAND_PATTERN if computational else GENERAL_COMMAND_PATTERN).search(
            line
        )
        if match is None:
            continue
        value = match.group(1).casefold()
        if value == "write" and not re.search(
            r"\bwrite\s+(?:a|an|code|down|pseudocode|sql|the)", lowered
        ):
            continue
        commands.append(
            (window.rfind(raw_line), "analyse" if value == "analyze" else value)
        )
    return max(commands, default=(-1, "unspecified"))[1]


def _item_demand(marks: int, command: str) -> str:
    if marks >= 10 or command in {"assess", "discuss", "evaluate"}:
        return "high"
    if marks <= 3 or command in {"define", "give", "identify", "select", "state"}:
        return "low"
    return "standard"


def _reference_response_mode(marks: int, command: str) -> str:
    if command == "select":
        return "selected-response"
    if command in {"deduce", "prove", "show", "verify"}:
        return "mathematical-argument"
    if command in {
        "calculate",
        "complete",
        "construct",
        "determine",
        "draw",
        "estimate",
        "find",
        "hence",
        "prepare",
        "sketch",
        "solve",
        "write",
    }:
        return "multi-stage-calculation" if marks >= 4 else "calculation"
    if command in {"define", "give", "identify", "name", "state"}:
        return "recall"
    if (
        command in {"advise", "assess", "discuss", "evaluate", "justify", "recommend"}
        or marks >= 12
    ):
        return "extended-evaluation"
    if command in {"analyse", "compare", "examine", "explain"}:
        return "structured-reasoning"
    return "constructed-response"


def _reference_operation(command: str) -> str:
    if command in {"define", "give", "identify", "name", "select", "state"}:
        return "retrieve"
    if command in {
        "calculate",
        "complete",
        "construct",
        "deduce",
        "determine",
        "draw",
        "estimate",
        "find",
        "hence",
        "prepare",
        "prove",
        "show",
        "sketch",
        "solve",
        "verify",
        "write",
    }:
        return "transform"
    if command in {"advise", "assess", "discuss", "evaluate", "justify", "recommend"}:
        return "judge"
    if command in {"analyse", "compare", "examine"}:
        return "analyse"
    if command in {"describe", "outline"}:
        return "describe"
    return "explain"


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
            reference_items = [
                item
                for path in paths
                for item in extract_reference_items(
                    _pdf_text(path),
                    board=family.board,
                    family_id=family.family_id,
                    paper_id=paper_id,
                    source_name=path.name,
                )
            ]
            if not marks or not commands:
                raise ValueError(
                    f"reference extraction is incomplete for {family.family_id} "
                    f"paper {paper_id}"
                )
            paired = [
                item
                for item in reference_items
                if item["command_word"] != "unspecified"
                and item.get("demand_eligible", True)
            ]
            coverage = len(paired) / len(reference_items) if reference_items else 0
            if coverage < 0.6:
                raise ValueError(
                    f"reference item pairing coverage is only {coverage:.1%} for "
                    f"{family.family_id} paper {paper_id}"
                )
            profile = ReferenceDemandProfile(
                family_id=family.family_id,
                paper_id=paper_id,
                comparison_basis=(
                    "Aggregate paired tariffs, response modes and cognitive "
                    "operations from "
                    f"{len(paths)} official {family.board.upper()} A-level question "
                    "papers; no source wording retained."
                    + (
                        " Discounted June 2025 Q06.4 excluded from cognitive-demand evidence."
                        if family.family_id == "aqa/computer-science"
                        and paper_id == "1"
                        else ""
                    )
                ),
                source_document_count=len(paths),
                source_fingerprint=(
                    hashlib.sha256(
                        (
                            _fingerprint(paths)
                            + "|cs-task-operations-v1-discount-exclusion"
                        ).encode()
                    ).hexdigest()
                    if "computer-science" in family.family_id
                    else _fingerprint(paths)
                ),
                mark_band_distribution=_distribution(
                    _mark_band(mark) for mark in marks
                ),
                command_word_distribution=_distribution(commands),
                demand_distribution=_distribution(
                    item["demand_band"] for item in paired
                ),
                mark_weighted_demand_distribution=_weighted_distribution(
                    (item["demand_band"], item["marks"]) for item in paired
                ),
                response_mode_distribution=_distribution(
                    item["response_mode"] for item in paired
                ),
                cognitive_operation_distribution=_distribution(
                    item["cognitive_operation"] for item in paired
                ),
                extraction_coverage=round(coverage, 6),
                metric_tolerances=_metric_tolerances(question_bank=False),
            )
            profiles.append(profile)
            family_profiles.append(profile)
        if family.family_id == "aqa/computer-science":
            profiles.extend(_question_bank_profiles(family_profiles))
    from Backend.Core.topic_reference_evidence import (
        GAPS,
        TOPIC_POLICY_ID,
        reviewed_topic_records,
    )
    from tools.source_candidate_paths import EXTRACTION_POLICY, source_forms

    for profile in profiles:
        if profile.family_id == "aqa/mathematics":
            profile.evidence_policy_id = "unqualified-reference-v1"
            profile.evidence_gaps = [
                "Unadvertised legacy aggregate profile; no H3 path qualification."
            ]
            continue
        if profile.assessment_kind == "question-bank":
            topic = profile.paper_id.removeprefix("bank-")
            records = reviewed_topic_records(topic)
            profile.topic_records = records
            profile.evidence_policy_id = TOPIC_POLICY_ID
            profile.evidence_gaps = GAPS[topic]
            profile.comparison_basis = "Reviewed topic, content-family, actual-operation, response-mode and tariff-band evidence for generated-item support; not whole-topic or learner calibration and not a scaled full-paper AO distribution."
            profile.source_fingerprint = hashlib.sha256(
                json.dumps(records, sort_keys=True).encode()
            ).hexdigest()
            profile.source_document_count = len({r["question_sha256"] for r in records})
            core = [r for r in records if r["stratum"] == "core"]
            profile.mark_band_distribution = _distribution(
                _mark_band(r["marks"]) for r in core
            )
            profile.command_word_distribution = _distribution(
                r["operation"] for r in core
            )
            profile.response_mode_distribution = _distribution(r["mode"] for r in core)
            profile.cognitive_operation_distribution = _distribution(
                r["operation"] for r in core
            )
            profile.demand_distribution = {"unknown": 1.0}
            profile.mark_weighted_demand_distribution = {"unknown": 1.0}
            continue
        profile.evidence_policy_id = EXTRACTION_POLICY
        profile.reference_forms = source_forms(profile.family_id, profile.paper_id)
        eligible = [
            form for form in profile.reference_forms if form["status"] == "eligible"
        ]
        if eligible:
            # Identical convention on both sides: each path has one feature
            # vector. Within a year paths are equally weighted descriptively;
            # years then receive equal weight (not extra candidate samples).
            for name in (
                "mark_band_distribution",
                "command_word_distribution",
                "demand_distribution",
                "mark_weighted_demand_distribution",
                "response_mode_distribution",
                "cognitive_operation_distribution",
            ):
                setattr(
                    profile,
                    name,
                    _mean_distribution(
                        [
                            _mean_distribution(
                                [path["observed"][name] for path in form["paths"]]
                            )
                            for form in eligible
                        ]
                    ),
                )
            profile.comparison_basis = "Correlated candidate-answerable paths from edition-specific official sources; equal-path/year descriptive means, not candidate choice frequency. Intended-demand bands are engineering proxies; source time/steps/learner demand unknown."
            profile.source_document_count = len(eligible)
        else:
            profile.evidence_gaps = [
                "No complete reconciled edition-specific reference path available."
            ]
    return ReferenceDemandDocument(
        schema_version=3,
        purpose=(
            "Copyright-safe aggregate demand fingerprints for reference-shaped "
            "authoring and automated form checks; not psychometric evidence."
        ),
        derived_aggregate_only=True,
        retains_source_text=False,
        profiles=sorted(profiles, key=lambda item: (item.family_id, item.paper_id)),
    )


def _reference_paths(root: Path, pattern: str) -> list[Path]:
    paths = [
        path for path in root.glob(pattern) if "correction" not in path.name.casefold()
    ]
    current = [
        path for path in paths if re.search(r"(?:JUN2[2-6]|202[2-6])", path.name, re.I)
    ]
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
    weighted_demand_distribution = _mean_distribution(
        [profile.mark_weighted_demand_distribution for profile in parents]
    )
    response_mode_distribution = _mean_distribution(
        [profile.response_mode_distribution for profile in parents]
    )
    operation_distribution = _mean_distribution(
        [profile.cognitive_operation_distribution for profile in parents]
    )
    return [
        ReferenceDemandProfile(
            family_id="aqa/computer-science",
            paper_id=paper_id,
            assessment_kind="question-bank",
            comparison_basis=(
                "Pooled whole-paper proxy, not topic-specific difficulty evidence: aggregate mark tariffs and "
                f"command-word frequencies across {documents} official AQA A-level "
                "Computer Science papers. Topic-level evidence is insufficient for a validated topic-bank match; no source wording retained."
            ),
            source_document_count=documents,
            source_fingerprint=digest,
            mark_band_distribution=mark_distribution,
            command_word_distribution=command_distribution,
            demand_distribution=demand_distribution,
            mark_weighted_demand_distribution=weighted_demand_distribution,
            response_mode_distribution=response_mode_distribution,
            cognitive_operation_distribution=operation_distribution,
            extraction_coverage=min(profile.extraction_coverage for profile in parents),
            metric_tolerances=_metric_tolerances(question_bank=True),
        )
        for paper_id in ("bank-4.2", "bank-4.10", "bank-4.12")
    ]


def _mean_distribution(values: list[dict[str, float]]) -> dict[str, float]:
    keys = sorted({key for value in values for key in value})
    raw = {
        key: sum(value.get(key, 0) for value in values) / len(values) for key in keys
    }
    return _renormalise(raw)


def _distribution(values: Any) -> dict[str, float]:
    counts = Counter(values)
    return _renormalise(dict(counts))


def _weighted_distribution(values: Any) -> dict[str, float]:
    counts: Counter[str] = Counter()
    for key, weight in values:
        counts[str(key)] += float(weight)
    return _renormalise(dict(counts))


def _metric_tolerances(*, question_bank: bool) -> dict[str, float]:
    return {
        "mark_band_distribution": 0.7 if question_bank else 0.5,
        "command_family_distribution": 0.9 if question_bank else 0.7,
        "mark_weighted_demand_distribution": 0.8 if question_bank else 0.45,
        "response_mode_distribution": 0.9 if question_bank else 0.7,
        "cognitive_operation_distribution": 1.0 if question_bank else 0.8,
    }


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
    return (
        json.dumps(
            document.model_dump(mode="json"),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    )


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
        if (
            not PROFILES_PATH.exists()
            or PROFILES_PATH.read_text(encoding="utf-8") != value
        ):
            raise SystemExit(
                "reference demand profiles are stale; run "
                "tools/reference_demand_profiles.py --write"
            )
        return 0
    print(value, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
