"""Reviewed feature-only AQA topic subsets, never topic AO targets.

Admission is fixed before generation: exact topic, actual operation and response
mode; robust mixed tasks remain mixed. Context-incomplete records are excluded.
Source audit expanded 28 September 2026. No source prose retained.
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

TOPIC_POLICY_ID = "aqa-topic-operation-records-v3"
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
    (2020, 1): (
        "000673a60b361c19c01cdbaed46725580a07e35181859f1b215da8ee324cd342",
        "ecbe57b6c727fcdc4f36d85c1c4371781fef8d931b6690111099112876ad5ba2",
    ),
    (2017, 2): (
        "69173c5e964635db2c948ac0e1255ef013cba45afad4ac5b85ab22067d137fc9",
        "34a9f1d417a75f035b3dee98a9421dfe0c9f50a400976a68b1129683b8b37905",
    ),
    (2020, 2): (
        "e55def6c924122b12c2f95750f63956a71d183039985128858e95bc63d166720",
        "115cf68eb69c6041ab95029e3c7649f8e69390540e78a1ae7bfd1daf052a202a",
    ),
    (2021, 1): (
        "edfb71e3e90e593adb94c4b16fbcea3f83e5e529ee3ec0c39fda3f8a4e0ef2bf",
        "ab830f38594fb417d2b61ee15dddc27e31793f3b1c817d2a52bfa22b1e6f79e4",
    ),
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
        (2022, "02.2", 3, (3, 0, 0), "describe", "prose", "3", "7-8", "4.2.1.4"),
        (2022, "02.3", 1, (0, 1, 0), "trace", "result", "3", "8", "4.2.3"),
        (2022, "02.4", 1, (0, 1, 0), "trace", "result", "3", "8", "4.2.3"),
        (2022, "02.5", 2, (2, 0, 0), "explain", "prose", "3", "8", "4.2.2/4.2.3"),
        (2022, "04.4", 1, (0, 1, 0), "represent", "table", "8", "11", "4.2.4"),
        (2022, "07.4", 1, (1, 0, 0), "explain", "prose", "14", "18", "4.2.6/4.2.7"),
        (2021, "02.2", 2, (0, 2, 0), "analyse", "sequence", "4", "7", "4.2.5"),
        (2020, "04.1", 4, (4, 0, 0), "judge", "prose", "7", "11", "4.2.1.4"),
    ],
    "4.10": [
        (2025, "06.1", 1, (0, 1, 0), "analyse", "prose", "12-13", "16", "4.10.2"),
        (2025, "06.2", 1, (0, 1, 0), "represent", "diagram", "12-13", "16", "4.10.1"),
        (2025, "06.3", 2, (0, 0, 2), "program", "code", "14", "17", "4.10.4"),
        (2025, "06.4", 6, (0, 4, 2), "program", "query", "12,14-15", "17-19", "4.10.4"),
        (2025, "06.5", 2, (2, 0, 0), "describe", "prose", "16", "20", "4.10.5"),
        (2024, "08.1", 1, (0, 1, 0), "analyse", "selected", "26", "27", "4.10.1"),
        (2024, "08.2", 2, (0, 0, 2), "program", "code", "27", "27-28", "4.10.4"),
        (2024, "08.3", 3, (0, 0, 3), "program", "code", "27", "27-28", "4.10.4"),
        (2024, "08.4", 3, (3, 0, 0), "describe", "prose", "28", "29-30", "4.10.5"),
        (2024, "08.5", 2, (2, 0, 0), "describe", "prose", "28", "29-30", "4.10.3"),
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
        (2025, "11.4", 2, (2, 0, 0), "describe", "prose", "29", "29", "4.12.1"),
        (2024, "11.1", 1, (0, 1, 0), "analyse", "prose", "37", "35", "4.12.1"),
        (2024, "11.2", 2, (2, 0, 0), "describe", "prose", "37", "35", "4.12.1"),
        (2023, "12.1", 3, (0, 3, 0), "trace", "table", "34", "32", "4.12.3"),
        (2023, "12.2", 1, (0, 1, 0), "analyse", "selected", "34", "32", "4.12.1"),
        (2022, "12.1", 1, (0, 1, 0), "analyse", "selected", "26", "29", "4.12.2"),
        (2022, "12.2", 1, (0, 1, 0), "analyse", "multi-selected", "26", "29", "4.12.1"),
        (2022, "12.3", 4, (0, 4, 0), "trace", "table", "26-27", "29", "4.12.3"),
        (2022, "12.4", 1, (0, 1, 0), "analyse", "prose", "26-27", "29-30", "4.12.1"),
        (2022, "12.5", 1, (0, 1, 0), "analyse", "prose", "26-27", "29-30", "4.12.1"),
        (2020, "11.2", 3, (0, 3, 0), "analyse", "prose", "34", "24", "4.12.3"),
        (2020, "11.3", 2, (2, 0, 0), "explain", "prose", "35", "24", "4.12.2"),
        (2020, "11.4", 1, (0, 1, 0), "analyse", "result", "35", "24", "4.12.3"),
        (2017, "06.2", 3, (0, 3, 0), "trace", "table", "15", "12", "4.12.2/4.12.3"),
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
            "analyse",
            "prose",
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
            "analyse",
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
        "No audited functional code-construction item; reviewed map/filter/fold and recursion tasks do not cover the whole topic.",
        "Imperative recursion does not establish functional-paradigm membership.",
    ],
}

# Reviewed content families, not keyword-derived source annotations. Empty means
# no content-level qualification: a generic operation match is diagnostic only.
SOURCE_FOCUS = {
    "75171-2025-01.1": "hash-performance", "75171-2025-01.2": "hash-insertion",
    "75171-2025-01.3": "hash-performance", "75171-2025-03.2": "tree-properties",
    "75171-2025-03.3": "graph-representation", "75171-2024-02.1": "queue-choice",
    "75171-2024-02.2": "queue-operations", "75171-2024-06.1": "tree-properties",
    "75171-2024-06.3": "tree-shape", "75171-2023-01": "queue-operations",
    "75171-2023-03.1": "tree-properties", "75171-2022-02.1": "queue-operations",
    "75171-2022-02.2": "dynamic-static", "75171-2022-02.3": "stack-access",
    "75171-2022-02.4": "stack-access", "75171-2022-02.5": "stack-reversal",
    "75171-2022-04.4": "graph-representation", "75171-2021-02.2": "tree-traversal",
    "75172-2025-06.1": "database-keys", "75172-2025-06.2": "database-relationships",
    "75172-2025-06.3": "sql-insert", "75172-2025-06.4": "sql-select",
    "75172-2025-06.5": "database-concurrency", "75172-2024-08.2": "sql-insert",
    "75172-2024-08.3": "sql-update", "75172-2024-08.4": "database-timestamps",
    "75172-2024-08.5": "database-normalisation", "75172-2023-05.1": "database-design",
    "75172-2023-05.2": "sql-delete-errors", "75172-2023-05.3": "database-integrity",
    "75172-2022-07.2": "database-relationships", "75172-2022-07.3": "sql-create",
    "75172-2022-07.4": "sql-select", "75172-2022-07.5": "database-denormalisation",
    "75172-2025-11.1": "functional-properties", "75172-2025-11.2": "function-type",
    "75172-2025-11.3": "recursive-efficiency", "75172-2025-11.4": "partial-application",
    "75172-2024-11.1": "function-type", "75172-2024-11.2": "functional-distribution",
    "75172-2023-12.1": "functional-evaluation", "75172-2023-12.2": "function-type",
    "75172-2022-12.1": "higher-order", "75172-2022-12.2": "functional-recursion",
    "75172-2022-12.3": "functional-evaluation", "75172-2022-12.4": "functional-purpose",
    "75172-2022-12.5": "functional-composition", "75172-2020-11.2": "functional-recursion",
    "75172-2020-11.3": "higher-order", "75172-2020-11.4": "functional-evaluation",
    "75172-2017-06.2": "functional-evaluation",
    "75171-2020-04.1": "dynamic-static",
}

STYLE_FOCUS = {
    "data_structures_stack_queue": {"queue-operations", "queue-choice", "stack-access", "stack-reversal"},
    "data_structures_hash": {"hash-insertion", "hash-performance"},
    "data_structures_tree": {"tree-properties", "tree-traversal", "tree-shape"},
    "data_structures_graph": {"graph-representation", "tree-properties"},
    "data_structures_choice": {"dynamic-static", "stack-reversal", "stack-access"},
    "sql_normalisation": {"sql-select", "sql-insert", "sql-update", "sql-delete-errors"},
    "erd_keys": {"database-relationships", "database-keys", "database-normalisation", "database-denormalisation"},
    "database_extended": {"database-design", "sql-create", "database-concurrency"},
    "functional_programming": {"functional-evaluation", "higher-order", "partial-application"},
    "functional_recursion": {"functional-evaluation", "functional-recursion", "functional-purpose", "higher-order"},
    "functional_type_short": {"function-type", "functional-distribution"},
    "functional_extended": {"functional-evaluation", "recursive-efficiency", "partial-application", "higher-order"},
}


def task_content_focus(item: dict[str, Any]) -> str | None:
    """Conservative semantic selectors for reviewed bank tasks; hints cannot override prose."""
    prompt = str(item.get("prompt", "")).casefold()
    rules = {
        "4.2": [
            ("queue-operations", r"(?:dequeue|remove.*circular queue|add.*circular queue)"),
            ("queue-choice", r"circular queue.*linear queue|linear queue.*circular queue"),
            ("hash-insertion", r"(?:insert|add).*hash table"),
            ("hash-performance", r"hash table.*(?:full|performance|slow|search|load)"),
            ("tree-traversal", r"(?:in-order|pre-order|post-order).*traversal"),
            ("tree-shape", r"tree.*(?:chain|shape|stack capacity)"),
            ("tree-properties", r"(?:properties|characteristics|reasons).*tree|tree.*(?:properties|characteristics)"),
            ("graph-representation", r"adjacency matrix|adjacency list"),
            ("dynamic-static", r"dynamic.*static|static.*dynamic"),
            ("stack-reversal", r"stack.*reverse|reverse.*stack"),
            ("stack-access", r"peek|pop operation"),
        ],
        "4.10": [
            ("sql-delete-errors", r"errors.*delete|delete.*errors"),
            ("sql-select", r"write.*select|write.*query"),
            ("sql-insert", r"write.*insert"), ("sql-update", r"write.*update"),
            ("sql-create", r"(?:write|complete).*create table"),
            ("database-relationships", r"draw.*relationship"),
            ("database-design", r"(?:develop|construct).*normalised.*(?:relations|design)"),
            ("database-denormalisation", r"advantage.*disadvantage.*(?:additional|redundant)"),
            ("database-integrity", r"delet.*(?:reference|referential|dependent)"),
            ("database-keys", r"(?:composite|primary).*key"),
            ("database-timestamps", r"timestamp ordering"),
            ("database-concurrency", r"concurrent|simultaneous"),
            ("database-normalisation", r"normalis"),
        ],
        "4.12": [
            ("functional-evaluation", r"trace table.*(?:filtered values|mapped values|total\s*(?:values|\[)|h\s*\[)|result.*fold"),
            ("higher-order", r"higher-order"),
            ("partial-application", r"partial.*appli"),
            ("function-type", r"co-domain|function type"),
            ("functional-distribution", r"distribut.*server|server.*distribut"),
            ("recursive-efficiency", r"recurs.*(?:inefficien|repeated|efficien)"),
            ("functional-recursion", r"recurs"),
            ("functional-purpose", r"purpose.*function|function.*purpose"),
            ("functional-composition", r"compos"),
            ("functional-properties", r"statements.*function"),
        ],
    }
    for focus, pattern in rules.get(str(item.get("topic_id")), []):
        if re.search(pattern, prompt):
            return focus
    return None


def task_context_complete(item: dict[str, Any], focus: str | None) -> bool:
    """Conservative dependencies for the reviewed bank forms, not a language solver.

    Presence of an introductory stem is not presence of its data. Applied tasks
    must retain the named definitions/schema/relationships that make them
    answerable. New forms need reviewed selectors rather than a metadata escape.
    """
    raw = item.get("context") or []
    context = "\n".join(raw).casefold() if isinstance(raw, list) and all(isinstance(v, str) for v in raw) else ""
    prompt = str(item.get("prompt", "")).casefold()
    if focus == "functional-evaluation" and "trace table" in prompt:
        functions = {name for name in ("filtered", "mapped", "total", "h") if re.search(rf"\b{name}\b", prompt)}
        if not functions or not all(re.search(rf"(?m)^{name}\s+[^=\n]+\s*=\s*\S+", context) for name in functions):
            return False
        if "values" in prompt and not re.search(r"(?m)^values\s*=\s*\[\s*\d+(?:\s*,\s*\d+)*\s*\]", context):
            return False
        if "mapped" in functions and not re.search(r"(?m)^double\s+\w+\s*=", context):
            return False
        if "h" in functions or ("total" in functions and "fold" not in context):
            name = "h" if "h" in functions else "total"
            return bool(re.search(rf"(?m)^{name}\s+\[\]\s*=", context) and re.search(rf"(?m)^{name}\s+\(\w+:\w+\)\s*=.*\b{name}\b", context))
        return True
    requirements = {
        "tree-traversal": [r"root:\s*\d+", r"node\s+\d+:\s*left=\d+,\s*right=\d+"],
        "graph-representation": [r"edges:\s*[a-z]-[a-z](?:,\s*[a-z]-[a-z])+"],
        "database-design": [r"clientid", r"name and email", r"registrationid", r"one client", r"booking date", r"several workshops", r"workshopid", r"places.*registration/workshop"],
        "database-relationships": [r"member.*many bookings", r"session.*many bookings", r"exactly one member and one session"],
        "sql-select": [r"session\([^)]*sessionid[^)]*activity", r"booking\([^)]*sessionid"],
        "sql-insert": [r"member\([^)]*memberid[^)]*fullname[^)]*email"],
        "sql-update": [r"booking\([^)]*memberid[^)]*sessionid[^)]*attended"],
        "sql-delete-errors": [r"booking\([^)]*sessionid[^)]*attended"],
        "functional-recursion": [r"(?m)^total\s+\[\]\s*=", r"(?m)^total\s+\(x:xs\)\s*=.*\btotal\b"],
        "functional-purpose": [r"(?m)^total\s+\[\]\s*=", r"(?m)^total\s+\(x:xs\)\s*=.*\btotal\b"],
        "recursive-efficiency": [r"(?m)^ways 1\s*=", r"(?m)^ways 2\s*=", r"(?m)^ways n\s*=.*ways.*ways"],
        "function-type": [r"f:\s*natural\s*->\s*real|function f maps natural numbers to real numbers"],
    }
    return all(re.search(pattern, context) for pattern in requirements.get(focus, []))


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
                    "content_focus": SOURCE_FOCUS.get(f"7517{paper}-{year}-{item}", ""),
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
                    "question_file": f"AQA-7517{paper}-QP-{'NOV' if year in (2020, 2021) else 'JUN'}{str(year)[2:]}{'-CR' if (year, paper) == (2023, 1) else ''}.PDF",
                    "scheme_file": f"AQA-7517{paper}-{'W-' if year in (2017, 2020) else ''}MS-{'NOV' if year in (2020, 2021) else 'JUN'}{str(year)[2:]}.PDF",
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
        or (contract.source_dependency == "task-context" and not any(str(value).strip() for value in context))
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
    inventory_valid = topic in TOPIC_STYLE_IDS and records == reviewed_topic_records(topic)
    # Treat the committed, source-reviewed inventory as an allowlist. Schema-valid
    # synthetic hashes, changed tariffs and fabricated anchors are not evidence.
    records = records if inventory_valid else []
    def compared_sources(item):
        focus = task_content_focus(item)
        def band(mark):
            return "short" if mark <= 4 else "medium" if mark <= 9 else "extended"
        marks = item.get("marks")
        if (focus not in STYLE_FOCUS.get(item.get("kind"), set())
                or not isinstance(marks, int) or marks <= 0
                or not task_context_complete(item, focus)):
            return []
        return [r for r in matching_records(records, task_features(item))
                if r.get("content_focus") == focus and band(r["marks"]) == band(marks)]

    matches = [
        {
            "item_id": i["id"],
            "task": task_features(i),
            "content_focus": task_content_focus(i),
            "source_ids": [
                r["id"] for r in compared_sources(i)
            ],
        }
        for i in items
    ]
    matched_ids = {source_id for match in matches for source_id in match["source_ids"]}
    support_years = {r["year"] for r in records if r["id"] in matched_ids}
    support_focus = {m["content_focus"] for m in matches if m["source_ids"]}
    passed = bool(inventory_valid and items and all(m["source_ids"] for m in matches)
                  and len(support_years) >= 2 and len(support_focus) >= 3)
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
        "passed": passed,
        "evidence_state": "source-supported" if passed else "insufficient",
        "evidence_validation_passed": inventory_valid,
        "qualification_scope": "generated-items",
        "sufficiency_policy": {
            "every_item_matched": True, "minimum_source_years": 2,
            "minimum_content_families": 3,
            "observed_source_years": len(support_years),
            "observed_content_families": len(support_focus),
            "basis": "Engineering coverage rule, not a statistical sample-size or empirical calibration claim.",
        },
        "whole_topic_qualified": False,
        "evidence_identity": identity(
            {"policy": TOPIC_POLICY_ID, "records": records, "items": items}
        ),
        "comparison_basis": "Reviewed inventory; exact topic/actual-operation/response-mode/content-family and short/medium/extended tariff-band matching. Comparable task form, not identical content or empirical difficulty. Mixed sources remain labelled; no pooled AO target.",
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
