"""Edition-bound, feature-only reference paths (H/F primary-source audits).

No student-time, reasoning-step or facility measurement is inferred. Tariff/
command demand bands remain declared engineering proxies. Unknown editions or
unreconciled leaf inventories are quarantined rather than treated as all-items.
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pymupdf

from Backend.Core.candidate_paths import CandidateTopology, enumerate_candidate_paths
from Backend.Core.reference_demand import (
    _collapse_command_distribution,
    operation_response_mode,
)

EXTRACTION_POLICY = "edition-leaf-path-features-v1"
OCR_EDITIONS = {
    "676764": 2022,
    "676765": 2022,
    "676766": 2022,
    "703800": 2023,
    "703801": 2023,
    "703802": 2023,
    "726591": 2024,
    "726592": 2024,
    "726593": 2024,
}
OCR_CONFLICTS = {
    2022: {
        "scheme_sha256": "ee235dfb8022ae80fc32e11a24dbdfb2bd0b2427bb94045918da6f83e5798f8a",
        "printed_total": [24, 20, 20, 16],
        "printed_mcq": [16, 6, 8, 0],
        "item_mcq": [18, 5, 7, 0],
        "printed_B": [8, 14, 12, 16],
        "item_B": [10, 12, 12, 16],
    },
    2023: {
        "scheme_sha256": "109e2281e5c7d39a87346e1cc4cedc642798b76c0f9e7a5f86efe8f0b321b4e3",
        "printed_total": [25, 21, 22, 12],
        "printed_mcq": [16, 6, 8, 0],
        "printed_B": [11, 15, 14, 12],
        "conflict": "82 subtotal marks versus 80 paper; Q35 row exceeds tariff",
    },
}


def feature_distribution(items):
    from tools.reference_demand_profiles import (
        _distribution,
        _mark_band,
        _weighted_distribution,
    )

    items = [i for i in items if i.get("demand_eligible", True)]
    observed = {
        "mark_band_distribution": _distribution(_mark_band(i["marks"]) for i in items),
        "command_word_distribution": _distribution(i["command_word"] for i in items),
        "demand_distribution": _distribution(i["demand_band"] for i in items),
        "mark_weighted_demand_distribution": _weighted_distribution(
            (i["demand_band"], i["marks"]) for i in items
        ),
        "response_mode_distribution": _distribution(i["response_mode"] for i in items),
        "cognitive_operation_distribution": _distribution(
            i["cognitive_operation"] for i in items
        ),
    }
    observed["command_family_distribution"] = _collapse_command_distribution(
        observed["command_word_distribution"]
    )
    return observed


def form_from_items(
    items, *, family: str, paper: str, year: int, source_id: str, source_sha256: str
) -> dict[str, Any]:
    total = (
        80
        if family in {"aqa/economics", "ocr/economics"}
        else 120
        if family == "aqa/accounting"
        else 140
        if family == "ocr/computer-science"
        else 100
    )
    sections = []

    def section(name, bundles, selected, marks):
        sections.append(
            {
                "id": name,
                "answer_options": selected,
                "candidate_marks": marks,
                "options": [
                    {"id": f"{name}-{n + 1}", "item_ids": [i["id"] for i in bundle]}
                    for n, bundle in enumerate(bundles)
                ],
            }
        )

    if family == "aqa/economics" and paper in {"1", "2"}:
        if [i["marks"] for i in items] != [2, 4, 9, 25] * 2 + [15, 25] * 3:
            raise ValueError("unreconciled edition context/essay leaf inventory")
        section("A", [items[:4], items[4:8]], 1, 40)
        section("B", [items[8:10], items[10:12], items[12:14]], 1, 40)
    elif family == "ocr/economics" and paper in {"1", "2"}:
        if len(items) != 10 or [i["marks"] for i in items[-4:]] != [25] * 4:
            raise ValueError("unreconciled OCR edition leaf inventory")
        section("A", [items[:-4]], 1, 30)
        section("B", [[items[-4]], [items[-3]]], 1, 25)
        section("C", [[items[-2]], [items[-1]]], 1, 25)
    elif family == "aqa/business" and paper == "1":
        expected_count = {2022: 25, 2024: 24, 2025: 24}[year]
        if len(items) != expected_count or [i["marks"] for i in items[:15]] != [1] * 15:
            raise ValueError("unreconciled Business edition leaf inventory")
        section("A", [items[:15]], 1, 15)
        section("B", [items[15:-4]], 1, 35)
        section("C", [[items[-4]], [items[-3]]], 1, 25)
        section("D", [[items[-2]], [items[-1]]], 1, 25)
    elif family == "pearson-edexcel/economics-a-2015":
        if paper in {"1", "2"}:
            section("A", [items[:-7]], 1, 25)
            section("B", [items[-7:-2]], 1, 50)
            section("C", [[items[-2]], [items[-1]]], 1, 25)
        else:
            if [i["marks"] for i in items] != [5, 8, 12, 25, 25] * 2:
                raise ValueError("unreconciled Edexcel synoptic leaf inventory")
            for n, start in enumerate((0, 5)):
                section(f"{n + 1}-mandatory", [items[start : start + 3]], 1, 25)
                section(
                    f"{n + 1}-choice", [[items[start + 3]], [items[start + 4]]], 1, 25
                )
    else:
        section("mandatory", [items], 1, total)
    topology = CandidateTopology.model_validate(
        {
            "policy_id": f"{EXTRACTION_POLICY}:{family}:{paper}:{year}",
            "total_marks": total,
            "duration_minutes": 180
            if family == "aqa/accounting"
            else 150
            if "computer-science" in family
            else 120,
            "sections": sections,
        }
    )
    paths = enumerate_candidate_paths(topology, items)
    by_id = {i["id"]: i for i in items}
    result = []
    for path in paths:
        selected = [by_id[key] for key in path.item_ids]
        ao = None
        if family == "ocr/economics":
            ao = dict(
                zip(
                    ("AO1", "AO2", "AO3", "AO4"),
                    [24, 22, 18, 16] if paper == "3" else [18, 20, 20, 22],
                    strict=True,
                )
            )
        elif family == "aqa/business" and paper in {"2", "3"}:
            vector = (
                [19, 19, 31, 31]
                if paper == "3"
                else {
                    2022: [26, 29, 24, 21],
                    2024: [18, 29, 32, 21],
                    2025: [24, 27, 28, 21],
                }[year]
            )
            ao = dict(zip(("AO1", "AO2", "AO3", "AO4"), vector, strict=True))
        result.append(
            {
                "id": path.id,
                "item_ids": path.item_ids,
                "marks": path.total_marks,
                "observed": feature_distribution(selected),
                "assessment_objectives": ao,
                "section_features": {
                    name: feature_distribution([by_id[key] for key in keys])
                    for name, keys in path.sections.items()
                },
                "observed_minutes": None,
                "reasoning_steps": None,
                "learner_demand": None,
            }
        )
    return {
        "id": source_id,
        "year": year,
        "source_sha256": source_sha256,
        "status": "eligible",
        "extraction_policy": EXTRACTION_POLICY,
        "objective_basis": "reconciled-published-aggregate"
        if result[0]["assessment_objectives"]
        else "unknown",
        "feature_basis": "published-tariff-and-inferred-task-operation-mode; learner demand unknown",
        "weighting_basis": "equal-path-within-year-equal-year-descriptive",
        "comparable_metrics": [
            "mark_band_distribution",
            "command_family_distribution",
            "response_mode_distribution",
            "cognitive_operation_distribution",
        ],
        "non_comparable_features": {
            "learner_demand": "unknown",
            "reasoning_steps": "unknown",
            "observed_minutes": "unknown",
        },
        "topology": topology.model_dump(mode="json"),
        "topology_fingerprint": topology.fingerprint,
        "printed_marks": sum(i["marks"] for i in items),
        "items": items,
        "paths": result,
    }


def _source_text(path: Path, *, family: str, paper: str) -> str:
    with pymupdf.open(path) as document:
        if family == "pearson-edexcel/economics-a-2015":
            # Exact audited 2024 editions: use original question overview once,
            # exclude repeated answer-space copies; C's standalone tariff is in
            # its total line rather than a second parent+part mark.
            pages = {
                "1": [2, 3, 4, 5, 6, 7, 8, 9, 12, 26],
                "2": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 30],
                "3": [5, 21],
            }[paper]
            text = "\n".join(document[n - 1].get_text() for n in pages)
            return re.sub(
                r"\(Total for Question [78] = (25) marks\)", r"\n(\1)\n", text
            )
        return "\n".join(p.get_text(sort=True) for p in document)


def _selected_features(rows, text, *, family, paper, year, root):
    from tools.reference_demand_profiles import _mark_pattern

    count = (
        15
        if family == "aqa/business" and paper == "1"
        else 30
        if family in {"aqa/economics", "ocr/economics"} and paper == "3"
        else 0
    )
    if not count:
        return
    matches = list(
        _mark_pattern("ocr" if family.startswith("ocr/") else "aqa").finditer(text)
    )
    tags = []
    if family == "ocr/economics" and year == 2024:
        scheme = next((root.parent / "mark-schemes").glob("726758-*.pdf"))
        with pymupdf.open(scheme) as document:
            tags = re.findall(
                r"\bAO[1-4]\b", "\n".join(document[n].get_text() for n in range(11, 17))
            )
        if len(tags) != 30 or Counter(tags) != {"AO1": 15, "AO2": 7, "AO3": 8}:
            raise ValueError("clean OCR 2024 MCQ tags no longer reconcile")
    for index, row in enumerate(rows[:count]):
        window = text[
            matches[index - 1].end() if index else 0 : matches[index].start()
        ].casefold()
        # These are transparent inference rules over required operations, not
        # empirical difficulty or claims that any scenario number means AO2.
        numeric_task = (
            bool(
                re.search(
                    r"\b(calculate|multiplier|marginal revenue|opportunity cost|percentage change|profit|elasticity)\b",
                    window,
                )
            )
            and len(re.findall(r"\d+(?:\.\d+)?", window)) >= 2
        )
        source_task = bool(re.search(r"\b(diagram|table|graph|data|curve)\b", window))
        operation = (
            "transform" if numeric_task else "analyse" if source_task else "retrieve"
        )
        if tags:
            row["assessment_objectives"] = {tags[index]: 1}
            row["objective_basis"] = "published-item-allocation"
            if tags[index] == "AO3":
                operation = "analyse"
            elif tags[index] == "AO2" and operation == "retrieve":
                operation = "contextualise"
        audited_operations = {
            ("ocr/economics", 2024, 2): "transform",
            ("ocr/economics", 2024, 5): "transform",
            ("ocr/economics", 2024, 15): "analyse",
            ("ocr/economics", 2024, 23): "analyse",
            ("aqa/economics", 2024, 5): "analyse",
            ("aqa/economics", 2024, 13): "transform",
            ("aqa/economics", 2025, 8): "transform",
            ("aqa/business", 2024, 10): "analyse",
            ("aqa/business", 2024, 14): "analyse",
            ("aqa/business", 2024, 15): "analyse",
            ("aqa/business", 2025, 6): "analyse",
            ("aqa/business", 2025, 7): "transform",
            ("aqa/business", 2025, 13): "analyse",
        }
        operation = audited_operations.get((family, year, index + 1), operation)
        row.update(
            command_word="select",
            response_mode="selected-response",
            cognitive_operation=operation,
            demand_band="low" if operation == "retrieve" else "standard",
            operation_basis="inferred-required-task-with-published-tags-where-known",
            demand_basis="engineering-proxy-not-learner-measurement",
        )


def source_forms(family_id: str, paper: str) -> list[dict[str, Any]]:
    from tools.reference_demand_profiles import (
        FAMILIES,
        _reference_paths,
        extract_reference_items,
    )

    family = next(f for f in FAMILIES if f.family_id == family_id)
    paths = _reference_paths(family.root, family.paper_patterns[paper])
    forms = []
    for path in paths:
        match = re.search(r"JUN(22|24|25)", path.name)
        year = (
            int("20" + match.group(1))
            if match
            else OCR_EDITIONS.get(path.name.split("-")[0])
        )
        if family.board == "pearson-edexcel":
            if "2024" not in path.name:
                continue
            year = 2024
        if year is None:
            if family_id != "ocr/computer-science":
                continue
            with pymupdf.open(path) as document:
                dates = re.findall(r"\b(202[1-5])\b", document[0].get_text())
            if not dates:
                continue
            year = int(dates[0])
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        if family_id == "ocr/economics" and paper == "3" and year in OCR_CONFLICTS:
            forms.append(
                {
                    "id": path.name,
                    "year": year,
                    "source_sha256": sha,
                    "status": "quarantined",
                    "objective_basis": "printed-conflicting",
                    "conflicting_evidence": OCR_CONFLICTS[year],
                    "paths": [],
                }
            )
            continue
        text = _source_text(path, family=family_id, paper=paper)
        if family.board == "pearson-edexcel":
            # Literal tariff lines from the audited page set; do not count
            # numeric parentheses in surrounding data as extra items.
            text = re.sub(r"\((\d{1,2})\)", r"\n(\1)\n", text)
        rows = extract_reference_items(
            text,
            board=family.board,
            family_id=family_id,
            paper_id=paper,
            source_name=path.name,
        )
        rows = [
            {
                **r,
                "id": str(i + 1),
                "objective_basis": "unknown",
                "assessment_objectives": None,
                "observed_minutes": None,
                "reasoning_steps": None,
                "learner_demand": None,
            }
            for i, r in enumerate(rows)
        ]
        _selected_features(
            rows, text, family=family_id, paper=paper, year=year, root=family.root
        )
        if family_id in {
            "aqa/economics",
            "ocr/economics",
            "aqa/business",
            "pearson-edexcel/economics-a-2015",
        }:
            for row in rows:
                if row["response_mode"] == "selected-response":
                    continue
                if row["command_word"] == "explain" and row["marks"] >= 9:
                    row["cognitive_operation"] = "analyse"
                    row["operation_basis"] = (
                        "inferred-developed-explanation-not-published-AO"
                    )
                row["response_mode"] = operation_response_mode(
                    row["cognitive_operation"], row["marks"]
                )
        try:
            for row in rows:
                row["historical_engineering_demand_proxy"] = row["demand_band"]
                row["demand_band"] = "unknown"
                row["demand_basis"] = "unknown-no-learner-measurement"
            form = form_from_items(
                rows,
                family=family_id,
                paper=paper,
                year=year,
                source_id=path.name,
                source_sha256=sha,
            )
        except ValueError as error:
            form = {
                "id": path.name,
                "year": year,
                "source_sha256": sha,
                "status": "quarantined",
                "objective_basis": "unknown",
                "reason": str(error),
                "paths": [],
            }
        if family_id == "ocr/economics" and paper == "3":
            form["scheme_sha256"] = (
                "7aaead3c658ab5d1e71b8cc47f9a9923610ef8b68bc5ee5fb8aa0f758f09c554"
            )
            form["qualitative_examiner_evidence"] = {
                "source_sha256": "c59b9e54ba24027399ad568c1ed817f373b0ca7f3e8655afd2e0b47c56d85909",
                "pages": [6, 19, 24],
                "challenging_mcq_ids": [7, 13, 15, 23, 28],
                "basis": "qualitative-cohort-commentary",
                "facility": None,
            }
        if family.board == "aqa":
            scheme_name = path.name.replace("-QP-", "-MS-").replace("-CR.PDF", ".PDF")
            scheme = path.parent.parent / "mark-schemes" / scheme_name
            if scheme.exists():
                form["scheme_file"] = scheme_name
                form["scheme_sha256"] = hashlib.sha256(scheme.read_bytes()).hexdigest()
        elif family_id == "ocr/economics" and paper in {"1", "2"}:
            scheme_id = (
                {2022: 676959, 2023: 703968, 2024: 726756}[year] + int(paper) - 1
            )
            schemes = list(
                (path.parent.parent / "mark-schemes").glob(f"{scheme_id}-*.pdf")
            )
            if len(schemes) == 1:
                form["scheme_file"] = schemes[0].name
                form["scheme_sha256"] = hashlib.sha256(
                    schemes[0].read_bytes()
                ).hexdigest()
        elif family.board == "pearson-edexcel":
            scheme = (
                path.parent.parent / "mark-schemes" / f"9ec0-0{paper}-rms-20240815.pdf"
            )
            if scheme.exists():
                form["scheme_file"] = scheme.name
                form["scheme_sha256"] = hashlib.sha256(scheme.read_bytes()).hexdigest()
        forms.append(form)
    return forms
