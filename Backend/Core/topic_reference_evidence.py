"""Reviewed feature-only AQA 2022-25 topic subsets, never topic AO targets.

Admission is fixed before generation: exact topic, actual operation and response
mode; robust mixed tasks remain mixed. Context-incomplete records are excluded.
Source audit: Task 7.H bank preflight, 31 August 2026. No source prose retained.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from Backend.Core.candidate_paths import identity
from Backend.Core.topic_task_contract import (
    TOPIC_CONTRACT_POLICY_ID,
    ReferenceTaskContract,
    derive_task_semantics,
)

TOPIC_POLICY_ID = "aqa-topic-operation-records-v2"
TOPIC_STYLE_IDS = {
    "4.2": {
        "data_structures_stack_queue",
        "data_structures_hash",
        "data_structures_tree",
        "data_structures_graph",
        "data_structures_choice",
    },
    "4.10": {"sql_normalisation", "erd_keys", "database_extended"},
    "4.12": {
        "functional_programming",
        "functional_recursion",
        "functional_type_short",
        "functional_extended",
    },
}
# QP/MS SHA256; all are June releases; 2023 P1 QP is the CR edition.
DOCUMENT_HASHES = {
    (2025, 1): (
        "8ee844b06b29d12f86cd64635a618e127797361ddde4481380d8ebbf7a6e5576",
        "dcb22f80e21507967743c1b1a540cb0d83c62700a3292c4e2c5b3a229761e391",
    ),
    (2025, 2): (
        "a0d7a65fc25df8029f711ad55b73c6a2f9f4427b1aca5d51c8405ef842013985",
        "f2aee82634640ac827cf94e11abb3ce4bf1561714ab58852e2c140be1482cb06",
    ),
    (2024, 1): (
        "0f192a3900489ddafff5d0618d4199f3bf31b71d3deb9537a7161b4ad6fa44ca",
        "af25688c1d02ae977650e22fc0220293f8541c83af64e052621980faafbd3908",
    ),
    (2024, 2): (
        "f22af35d33bcebeb7dff15b35df97a7c8346efc76e99a56e3a7b047e98c9f7a9",
        "c943099666954ad673b2cbf1d07169149d88f109bc3701622c511fa50f8d13d9",
    ),
    (2023, 1): (
        "341549813dc82f3927049f3ea09bf912fb2a779d5ed43cb614790a7dffb799d3",
        "e8bb1bd5db0268058cdc9eae90139926d15a2c84a4debf7f16c63993c71815fd",
    ),
    (2023, 2): (
        "c893de2ff1cf79983c16103c3d857d531e906cf9eeef39a82c3456b1a76db85a",
        "e14c54fa38f1a649641e3f4c4829a5576c736d9eb66322d7734339d663d5e9a2",
    ),
    (2022, 1): (
        "c3b39d1093d5a04a9d00980ac980a36a31f37f4e02266794809b92ddd838148e",
        "86f6b2b3a0391c680412590dda0b112805e2360bedd2d68bc9df7460004cbf24",
    ),
    (2022, 2): (
        "1656436887eac96fb19ab7f42260724aa7ebf05933aa875c8c8914f52c4c94ca",
        "9d9364a4143ae5af92b0966391207f6d476c28ad1b18bfedf70820da2b2d22ae",
    ),
}
SPECIFICATION_SHA256 = (
    "9d5c9066ab090bb66a43e61e9637c2b51b29b15b69e95f430c15a86352f92dd2"
)

# year, item, marks, AO1/AO2/AO3, operation, response mode, QP pages,
# MS pages, specification basis. Separate rows are separate marked leaves.
CORE = {
    "4.2": [
        (2025, "01.1", 1, (1, 0, 0), "explain", "prose", "2", "6", "4.2.6"),
        (2025, "01.2", 4, (4, 0, 0), "describe", "prose", "2", "6", "4.2.6"),
        (2025, "01.3", 1, (1, 0, 0), "explain", "prose", "2", "6", "4.2.6"),
        (2025, "03.2", 2, (0, 2, 0), "analyse", "prose", "3", "7", "4.2.5"),
        (2025, "03.3", 2, (0, 2, 0), "represent", "table", "3", "8", "4.2.4"),
        (2025, "05.2", 2, (2, 0, 0), "explain", "prose", "11", "13", "4.2.7"),
        (2024, "02.1", 2, (2, 0, 0), "explain", "prose", "2", "7", "4.2.2"),
        (2024, "02.2", 5, (5, 0, 0), "describe", "prose", "2", "7", "4.2.2"),
        (2024, "06.1", 2, (2, 0, 0), "retrieve", "prose", "6", "12", "4.2.5"),
        (2024, "06.4", 1, (0, 1, 0), "analyse", "prose", "6-8", "13", "4.2.3"),
        (2023, "01", 5, (5, 0, 0), "describe", "prose", "2", "6", "4.2.2"),
        (2023, "03.1", 2, (2, 0, 0), "retrieve", "prose", "4", "8", "4.2.5"),
        (2022, "02.1", 4, (4, 0, 0), "describe", "prose", "3", "7-8", "4.2.2"),
        (2022, "02.2", 3, (3, 0, 0), "explain", "prose", "3", "7-8", "4.2.1.4"),
        (2022, "02.3", 1, (0, 1, 0), "trace", "result", "3", "8", "4.2.3"),
        (2022, "02.4", 1, (0, 1, 0), "trace", "result", "3", "8", "4.2.3"),
        (2022, "02.5", 2, (2, 0, 0), "describe", "prose", "3", "8", "4.2.2/4.2.3"),
        (2022, "04.4", 1, (0, 1, 0), "represent", "table", "8", "11", "4.2.4"),
        (2022, "07.4", 1, (1, 0, 0), "explain", "prose", "14", "18", "4.2.6/4.2.7"),
    ],
    "4.10": [
        (2025, "06.1", 1, (0, 1, 0), "analyse", "prose", "12-13", "16", "4.10.2"),
        (2025, "06.2", 1, (0, 1, 0), "represent", "diagram", "12-13", "16", "4.10.1"),
        (2025, "06.3", 2, (0, 0, 2), "program", "code", "14", "17", "4.10.4"),
        (2025, "06.4", 6, (0, 4, 2), "program", "query", "12,14-15", "17-19", "4.10.4"),
        (2025, "06.5", 2, (2, 0, 0), "explain", "prose", "16", "20", "4.10.5"),
        (2024, "08.1", 1, (0, 1, 0), "analyse", "selected", "26", "27", "4.10.1"),
        (2024, "08.2", 2, (0, 0, 2), "program", "code", "27", "27-28", "4.10.4"),
        (2024, "08.3", 3, (0, 0, 3), "program", "code", "27", "27-28", "4.10.4"),
        (2024, "08.4", 3, (3, 0, 0), "explain", "prose", "28", "29-30", "4.10.5"),
        (2024, "08.5", 2, (2, 0, 0), "explain", "prose", "28", "29-30", "4.10.3"),
        (
            2023,
            "05.1",
            5,
            (0, 5, 0),
            "represent",
            "relations",
            "12-13",
            "14",
            "4.10.1/4.10.3",
        ),
        (2023, "05.2", 2, (0, 2, 0), "analyse", "prose", "14", "15", "4.10.4"),
        (2023, "05.3", 2, (1, 1, 0), "analyse", "prose", "12-14", "15", "4.10.2"),
        (2022, "07.1", 1, (1, 0, 0), "retrieve", "selected", "14", "18", "4.10.3"),
        (2022, "07.2", 2, (0, 2, 0), "represent", "diagram", "14-15", "18", "4.10.1"),
        (2022, "07.3", 3, (0, 0, 3), "program", "code", "14-15", "19", "4.10.4"),
        (2022, "07.4", 7, (0, 5, 2), "program", "query", "14,16", "20-22", "4.10.4"),
        (2022, "07.5", 2, (0, 2, 0), "analyse", "prose", "14,17", "23", "4.10.3"),
    ],
    "4.12": [
        (2025, "11.1", 1, (0, 1, 0), "analyse", "multi-selected", "28", "28", "4.12.1"),
        (2025, "11.2", 1, (0, 1, 0), "analyse", "selected", "28", "28", "4.12.1"),
        (2025, "11.4", 2, (2, 0, 0), "explain", "prose", "29", "29", "4.12.1"),
        (2024, "11.1", 1, (0, 1, 0), "analyse", "prose", "37", "35", "4.12.1"),
        (2024, "11.2", 2, (2, 0, 0), "explain", "prose", "37", "35", "4.12.1"),
        (2023, "12.1", 3, (0, 3, 0), "trace", "table", "34", "32", "4.12.3"),
        (2023, "12.2", 1, (0, 1, 0), "analyse", "selected", "34", "32", "4.12.1"),
        (2022, "12.1", 1, (0, 1, 0), "analyse", "selected", "26", "29", "4.12.2"),
        (2022, "12.2", 1, (0, 1, 0), "analyse", "multi-selected", "26", "29", "4.12.1"),
        (2022, "12.3", 4, (0, 4, 0), "trace", "table", "26-27", "29", "4.12.3"),
        (2022, "12.4", 1, (0, 1, 0), "analyse", "prose", "26-27", "29-30", "4.12.1"),
        (2022, "12.5", 1, (0, 1, 0), "analyse", "prose", "26-27", "29-30", "4.12.1"),
    ],
}
MIXED = {
    "4.2": [
        (2025, "03.5", 6, (0, 6, 0), "trace", "table", "4-7", "9", "4.2.4+algorithms"),
        (
            2024,
            "06.2",
            7,
            (0, 7, 0),
            "trace",
            "table",
            "6-8",
            "12-13",
            "4.2.3/4.2.5+algorithms",
        ),
        (
            2024,
            "06.3",
            2,
            (0, 2, 0),
            "analyse",
            "prose",
            "6-8",
            "12-13",
            "4.2.5+complexity",
        ),
        (
            2024,
            "06.5",
            1,
            (0, 1, 0),
            "complete-code",
            "code",
            "6-8",
            "12-13",
            "4.2.5+algorithms",
        ),
        (
            2023,
            "03.2",
            4,
            (0, 4, 0),
            "complete-code",
            "code",
            "4-5",
            "8",
            "4.2.5+algorithms",
        ),
        (2022, "04.5", 6, (0, 6, 0), "trace", "table", "8-9", "12", "4.2.4+algorithms"),
    ],
    "4.10": [],
    "4.12": [
        (
            2025,
            "11.3",
            2,
            (0, 2, 0),
            "analyse-complexity",
            "prose",
            "28-29",
            "28",
            "4.12+complexity",
        )
    ],
}
CONTEXT = [
    (2025, "05.3", 1, (0, 1, 0), "unknown", "unknown", "11", "13", "4.2"),
    (2025, "08", 1, (0, 1, 0), "unknown", "unknown", "14", "16", "4.2"),
    (2022, "07.3", 3, (2, 1, 0), "unknown", "unknown", "14", "18", "4.2.6"),
    (2024, "13.3", 1, (0, 0, 0), "unknown", "unknown", "18", "unaudited", "4.2.9"),
    (2024, "13.4", 1, (0, 0, 0), "unknown", "unknown", "18", "unaudited", "4.2.9"),
]
GAPS = {
    "4.2": [
        "Incomplete vectors, arrays/files and executable structure/program construction coverage.",
        "Skeleton/source-context tasks remain ineligible.",
    ],
    "4.10": [
        "Four annual schema/scenario clusters, not independent student samples.",
        "REST/HTTP/JSON and floating-point normalisation are excluded.",
    ],
    "4.12": [
        "No audited functional code-construction item; broader composition/filter/fold coverage missing.",
        "Imperative recursion does not establish functional-paradigm membership.",
    ],
}


def reviewed_topic_records(topic: str) -> list[dict[str, Any]]:
    paper = 1 if topic == "4.2" else 2
    result = []
    strata = [
        ("core", CORE[topic]),
        ("mixed", MIXED[topic]),
        ("context-incomplete", CONTEXT if topic == "4.2" else []),
    ]
    for stratum, rows in strata:
        for year, item, marks, ao, operation, mode, qp, ms, basis in rows:
            qhash, mhash = DOCUMENT_HASHES[year, paper]
            result.append(
                {
                    "id": f"7517{paper}-{year}-{item}",
                    "year": year,
                    "paper": str(paper),
                    "item": item,
                    "question_cluster": f"{year}-{paper}-{item.split('.')[0]}",
                    "topic_id": topic,
                    "topic_basis": basis,
                    "stratum": stratum,
                    "context_complete": stratum != "context-incomplete",
                    "marks": marks,
                    "assessment_objectives": {
                        f"AO{i}": value for i, value in enumerate(ao, 1) if value
                    }
                    if sum(ao)
                    else None,
                    "objective_basis": "published-item-allocation"
                    if sum(ao)
                    else "unknown",
                    "operation": operation,
                    "mode": mode,
                    "feature_basis": "reviewed-task-inference",
                    "source_dependency": "unknown"
                    if stratum == "context-incomplete"
                    else "task-context"
                    if ao[1] or ao[2]
                    else "self-contained",
                    "question_pages": qp,
                    "scheme_pages": ms,
                    "question_sha256": qhash,
                    "scheme_sha256": mhash,
                    "question_file": f"AQA-7517{paper}-QP-JUN{str(year)[2:]}{'-CR' if (year, paper) == (2023, 1) else ''}.PDF",
                    "scheme_file": f"AQA-7517{paper}-MS-JUN{str(year)[2:]}.PDF",
                    "specification_sha256": SPECIFICATION_SHA256,
                    "reasoning_steps": None,
                    "observed_minutes": None,
                    "learner_demand": None,
                }
            )
    return result


def task_features(item: dict[str, Any]) -> dict[str, Any]:
    """Require task/context membership and an evidenced response form.

    A stimulus table is not an answer table; multiple answer slots are not a
    trace table. Broad authoring operations may be refined only by an actual
    response instruction/contract, never an incidental noun in prose.
    """
    raw_contract = item.get("reference_task_contract")
    if not isinstance(raw_contract, dict):
        return {"topic_id": None, "operation": "unknown", "mode": "unknown"}
    try:
        contract = ReferenceTaskContract.model_validate(raw_contract)
    except ValueError:
        return {"topic_id": None, "operation": "unknown", "mode": "unknown"}
    topic = contract.topic_id
    prompt = str(item.get("prompt", "")).casefold()
    context = item.get("context") or []
    text = (
        prompt
        + " "
        + (
            " ".join(map(str, context)) if isinstance(context, list) else str(context)
        ).casefold()
    )
    semantics = derive_task_semantics(
        task_operation=item.get("task_operation"),
        prompt=item.get("prompt"),
        options=item.get("options") or item.get("choices") or [],
        response_slots=item.get("response_slots") or [],
    )
    source_dependency = item.get("reference_source_dependency")
    if source_dependency not in {"self-contained", "task-context"}:
        source_dependency = "task-context" if context else "self-contained"
    excluded = {
        "4.2": r"\b(database|relational|sql|primary key|foreign key|normalisation|normalization|compression)\b",
        "4.10": r"\b(rest(?:ful)?|xml|json|https?|floating-point|functional|lambda|immutable|adjacency|stack|queue|tree|graph)\b",
        "4.12": r"\b(imperative|graph|vertex|vertices|visited|while|for loop|database|relational|sql|normalisation|normalization)\b",
    }
    if (
        contract.policy_id != TOPIC_CONTRACT_POLICY_ID
        or topic not in TOPIC_STYLE_IDS
        or contract.style_id not in TOPIC_STYLE_IDS[topic]
        or item.get("topic_id") != topic
        or item.get("kind") != contract.style_id
        or semantics != (contract.operation, contract.response_mode)
        or source_dependency != contract.source_dependency
        or re.search(excluded[topic], text)
    ):
        return {"topic_id": None, "operation": "unknown", "mode": "unknown"}
    return {
        "topic_id": topic,
        "operation": contract.operation,
        "mode": contract.response_mode,
    }


def matching_records(
    records: list[dict[str, Any]], task: dict[str, Any]
) -> list[dict[str, Any]]:
    return [
        r
        for r in records
        if r["context_complete"]
        and r["stratum"] in {"core", "mixed"}
        and all(r[key] == task[key] for key in ("topic_id", "operation", "mode"))
    ]


def audit_topic_bank(
    items: list[dict[str, Any]], topic: str, records: list[dict[str, Any]]
) -> dict[str, Any]:
    matches = [
        {
            "item_id": i["id"],
            "task": task_features(i),
            "source_ids": [
                r["id"] for r in matching_records(records, task_features(i))
            ],
        }
        for i in items
    ]
    matched_ids = {source_id for match in matches for source_id in match["source_ids"]}
    eligible = [
        r
        for r in records
        if r["context_complete"] and (r["stratum"] == "core" or r["id"] in matched_ids)
    ]

    def distribution(rows):
        counts = Counter(f"{r['operation']}:{r['mode']}" for r in rows)
        return (
            {key: round(value / len(rows), 6) for key, value in sorted(counts.items())}
            if rows
            else {}
        )

    def macro(rows, key):
        clusters = sorted({r[key] for r in rows})
        values = [
            distribution([r for r in rows if r[key] == cluster]) for cluster in clusters
        ]
        keys = sorted({key for value in values for key in value})
        return {
            key: round(sum(value.get(key, 0) for value in values) / len(values), 6)
            for key in keys
        }

    strata = {
        s: {
            "parts": len(rows := [r for r in records if r["stratum"] == s]),
            "marks": sum(r["marks"] for r in rows),
        }
        for s in ("core", "mixed", "context-incomplete")
    }
    return {
        "schema_version": 1,
        "policy_id": TOPIC_POLICY_ID,
        "passed": False,
        "evidence_state": "insufficient",
        "whole_topic_qualified": False,
        "evidence_identity": identity(
            {"policy": TOPIC_POLICY_ID, "records": records, "items": items}
        ),
        "comparison_basis": "Exact topic/actual-operation/response-mode matching; mixed tasks remain labelled; no pooled full-paper AO target.",
        "strata": strata,
        "gaps": GAPS[topic]
        + [
            "Source reasoning steps, observed times and learner demand are unknown; intended demand uses explicit design constraints."
        ],
        "coverage": {
            "items": len(items),
            "matched_items": sum(bool(r["source_ids"]) for r in matches),
            "unmatched_item_ids": [
                r["item_id"] for r in matches if not r["source_ids"]
            ],
        },
        "matches": matches,
        "cluster_sensitivity": {
            "basis": "Descriptive equal question/year means, not learner samples or choice frequencies.",
            "admission": "All strict core records; mixed records only when an actual task matches topic, operation and response mode.",
            "admitted_mixed_ids": [
                r["id"] for r in eligible if r["stratum"] == "mixed"
            ],
            "pooled_parts": distribution(eligible),
            "equal_question": macro(eligible, "question_cluster"),
            "equal_year": macro(eligible, "year"),
            "leave_one_year_out": {
                str(year): macro([r for r in eligible if r["year"] != year], "year")
                for year in sorted({r["year"] for r in eligible})
            },
        },
        "empirical_equivalence_claimed": False,
    }
