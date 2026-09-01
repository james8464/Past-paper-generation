"""Scoped semantic adjudication for the declared AQA stored-program task.

The preceding solver is blind. This later model review sees private criteria;
strict record checks and bounded two-criterion quote rules fail closed without
claiming a generic essay-entailment capability.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from copy import deepcopy
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from Backend.Core.credit_policy import CREDIT_POLICY_VERSION

CPU_SOURCE = "https://www.aqa.org.uk/subjects/computer-science/a-level/computer-science-7517/specification/subject-content/fundamentals-of-computer-organisation-and-architecture"
CPU_POINTS = [
    "Machine-code instructions are stored in main memory;",
    "The processor fetches and executes the instructions serially / in sequence;",
]


def cpu_credit_contract() -> dict[str, Any]:
    return {
        "id": "aqa-7517-stored-program",
        "version": CREDIT_POLICY_VERSION,
        "source": CPU_SOURCE,
        "section": "4.7.2.1",
        "criteria": [
            {
                "id": "instructions-main-memory",
                "marks": 1,
                "meaning": "Machine-code instructions are stored in main memory.",
            },
            {
                "id": "serial-processor-execution",
                "marks": 1,
                "meaning": "A processor fetches and executes those instructions serially / in sequence.",
            },
        ],
        "not_required": [
            "Shared instruction/data memory (von Neumann-specific)",
            "A common address for instructions and data",
            "Reprogrammability or hardware rewiring",
            "A separate explanation of significance",
        ],
    }


def cpu_credit_allocations() -> list[dict[str, Any]]:
    return [
        {"criterion_id": criterion["id"], "marks": 1, "point_index": index}
        for index, criterion in enumerate(cpu_credit_contract()["criteria"])
    ]


def printed_credit_points(marking: dict[str, Any]) -> list[str]:
    """Same actual text/allocation projection for renderer and adjudicator."""
    allocation = {
        row["point_index"]: row["marks"]
        for row in marking.get("credit_allocations", [])
    }
    return [
        f"{point.rstrip('; .')} ({allocation[index]} mark{'s' if allocation[index] != 1 else ''});"
        if index in allocation
        else point
        for index, point in enumerate(marking.get("points", []))
    ]


def validate_open_credit_contract(item: dict[str, Any]) -> dict[str, Any]:
    contract = item.get("authoring_context", {}).get(
        "open_credit_contract"
    ) or item.get("open_credit_contract")
    if contract != cpu_credit_contract() or item.get("marks") != 2:
        raise ValueError("unknown or changed open credit contract")
    marking = item.get("marking", {})
    allocations = marking.get("credit_allocations", [])
    # Exactly two distinct printed rows, each one mark. No two marks for one
    # feature, duplicated criterion, unprinted private criterion or extra credit.
    if len(allocations) != 2 or len(marking.get("points", [])) != 2:
        raise ValueError("CPU scheme must print two separately allocated criteria")
    expected = {row["criterion_id"]: row["marks"] for row in cpu_credit_allocations()}
    if (
        {row.get("criterion_id"): row.get("marks") for row in allocations} != expected
        or {row.get("point_index") for row in allocations} != {0, 1}
        or any(
            type(row.get("marks")) is not int or type(row.get("point_index")) is not int
            for row in allocations
        )
    ):
        raise ValueError(
            "CPU scheme has incomplete, duplicate or changed credit allocation"
        )
    return contract


def credit_item_projection(item: dict[str, Any]) -> dict[str, Any]:
    value = deepcopy(item)
    for field in ("open_credit_review", "difficulty_evidence"):
        value.pop(field, None)
    return value


def credit_identity(item: dict[str, Any], solution: dict[str, Any]) -> str:
    value = {
        "policy": CREDIT_POLICY_VERSION,
        "item": credit_item_projection(item),
        "solution": solution,
    }
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


class CriterionDecision(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    criterion_id: str
    decision: Literal["supported", "unsupported", "uncertain"]
    answer_quote: str
    scheme_quote: str
    point_index: int = Field(ge=0)
    marks: int = Field(ge=0)


class CreditJudgement(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    criteria: list[CriterionDecision]
    issues: list[str]
    advisory_conflicts: list[str]


_CPU_INSTRUCTION = (
    r"(?:machine code(?: instructions?)?|machine instructions?|"
    r"program(?:me)?s?(?: code| instructions?)?|instructions?)"
)
_CPU_STORAGE = r"(?:stored|held|kept|loaded)"
_CPU_MAIN_MEMORY = r"(?:main memory|ram)"
_CPU_EXECUTION = (
    r"(?:execut(?:e|es|ed|ing)|run(?:s|ning)?|process(?:es|ed|ing)?|"
    r"perform(?:s|ed|ing)?|carr(?:y|ies|ied|ying) out|"
    r"complete(?:s|d|ing)?|finish(?:es|ed|ing)?)"
)
_CPU_ORDER = (
    r"(?:serially|sequentially|in sequence|in order(?! to)|one at a time|"
    r"one after another|one by one|instruction by instruction)"
)
_CPU_NEGATOR = (
    r"(?:not|never|without|cannot|cant|isnt|arent|wasnt|werent|"
    r"doesnt|dont|didnt|wont|wouldnt|shouldnt)"
)


def _normalise_cpu_quote(value: str) -> str:
    """Apply only harmless normalization for this fixed English contract."""
    text = unicodedata.normalize("NFKC", value).casefold()
    text = re.sub(r"[\u2010-\u2015\u2212-]+", " ", text)
    text = text.replace("’", "").replace("'", "")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def _relation_is_qualified(text: str, match: re.Match[str] | None) -> bool:
    """Detect a restricting qualifier attached immediately to one proposition."""
    if match is None:
        return False
    return bool(
        re.match(
            r" (?:but |and |though )?(?:not always|only sometimes)\b",
            text[match.end() :],
        )
    )


def _cpu_quote_supports_criterion(criterion_id: str, answer_quote: str) -> bool:
    """Fail-closed evidence rules for the two registered stored-program marks."""
    text = _normalise_cpu_quote(answer_quote)
    if not text:
        return False
    if criterion_id == "instructions-main-memory":
        negated_passive = re.search(
            rf"\b{_CPU_INSTRUCTION}\b (?:(?:is|are|can|may|must|gets?) )?"
            rf"(?:{_CPU_NEGATOR} )(?:necessarily )?(?:be )?{_CPU_STORAGE} "
            rf"(?:in|into|within|on) (?:the )?(?:computer s )?{_CPU_MAIN_MEMORY}\b",
            text,
        )
        passive = re.search(
            rf"\b{_CPU_INSTRUCTION}\b "
            rf"(?:(?:is|are|must|gets?) )?(?:be )?{_CPU_STORAGE} "
            rf"(?:in|into|within|on) (?:the )?(?:computer s )?{_CPU_MAIN_MEMORY}\b",
            text,
        )
        memory_active = re.search(
            rf"\b{_CPU_MAIN_MEMORY}\b (?:stores|holds|keeps|contains) "
            rf"(?:the )?{_CPU_INSTRUCTION}\b",
            text,
        )
        loader_active = re.search(
            rf"\b(?:loads?|places?) (?:the )?{_CPU_INSTRUCTION}\b "
            rf"(?:in|into|within) (?:the )?(?:computer s )?{_CPU_MAIN_MEMORY}\b",
            text,
        )
        negated_active = re.search(
            rf"\b{_CPU_MAIN_MEMORY}\b (?:does |can |may |must )?{_CPU_NEGATOR} "
            rf"(?:necessarily )?(?:stores|holds|keeps|contains) (?:the )?{_CPU_INSTRUCTION}\b|"
            rf"\b(?:cpu|processor)\b (?:does |can |may |must )?{_CPU_NEGATOR} "
            rf"(?:necessarily )?(?:loads?|places?) (?:the )?{_CPU_INSTRUCTION}\b "
            rf"(?:in|into|within) (?:the )?(?:computer s )?{_CPU_MAIN_MEMORY}\b",
            text,
        )
        no_instructions = re.search(
            rf"\bno {_CPU_INSTRUCTION}\b (?:\w+ ){{0,3}}\b{_CPU_MAIN_MEMORY}\b",
            text,
        )
        storage_assertions = (passive, memory_active, loader_active)
        return bool(
            not negated_passive
            and not negated_active
            and not no_instructions
            and any(
                match and not _relation_is_qualified(text, match)
                for match in storage_assertions
            )
        )
    if criterion_id == "serial-processor-execution":
        instruction_anchor = re.search(rf"\b{_CPU_INSTRUCTION}\b", text)
        pronoun_anchor = re.search(
            r"\b(?:cpu|processor)\b.*\b(?:them|these)\b", text
        )
        execution_target = rf"(?:{_CPU_INSTRUCTION}|them|these|they)"
        action_subject_order = re.search(
            rf"\b{_CPU_EXECUTION}\b (?:each |the |an? |one )?"
            rf"\b{execution_target}\b \b{_CPU_ORDER}\b",
            text,
        )
        subject_action_order = re.search(
            rf"\b{execution_target}\b "
            rf"(?:(?:is|are|be|then|each) ){{0,3}}"
            rf"\b{_CPU_EXECUTION}\b \b{_CPU_ORDER}\b",
            text,
        )
        order_cpu_action = re.search(
            rf"\b{_CPU_ORDER}\b (?:the )?(?:cpu|processor) "
            rf"(?:(?:fetches|retrieves) and )?\b{_CPU_EXECUTION}\b "
            rf"(?:the )?\b{execution_target}\b",
            text,
        )
        ordered_matches = (
            action_subject_order,
            subject_action_order,
            order_cpu_action,
        )
        before_next = re.search(
            r"\b(?:complete(?:s|d|ing)?|finish(?:es|ed|ing)?|execut(?:e|es|ed|ing))\b "
            r"(?:\w+ ){0,3}\b(?:instructions?|it|one)\b (?:\w+ ){0,2}before "
            r"(?:\w+ ){0,2}\b(?:fetch(?:es|ed|ing)?|start(?:s|ed|ing)?|begins?|"
            r"execut(?:e|es|ed|ing)|runs?)\b (?:\w+ ){0,2}\b(?:next|another|following)\b",
            text,
        )
        passive_before_next = re.search(
            r"\b(?:an? |each |one )?instruction\b (?:is )?"
            r"(?:completed|finished|executed) before (?:the )?"
            r"(?:next|following|another) (?:instruction |one )?(?:is )?"
            r"(?:fetched|started|begun|executed)\b",
            text,
        )
        passive_one_at_time = re.search(
            r"\b(?:one|each|an?) instruction\b (?:is )?"
            rf"\b{_CPU_EXECUTION}\b at a time\b",
            text,
        )
        negated_credited_relation = re.search(
            rf"(?:\b{execution_target}\b (?:\w+ ){{0,3}}\b{_CPU_NEGATOR}\b "
            rf"(?:necessarily )?(?:be |being )?\b{_CPU_EXECUTION}\b "
            rf"(?:\w+ ){{0,2}}\b{_CPU_ORDER}\b|"
            rf"\b(?:cpu|processor)\b (?:does |do |can |may |must |will |would |should )?"
            rf"\b{_CPU_NEGATOR}\b (?:necessarily |always )?\b{_CPU_EXECUTION}\b "
            rf"(?:each |the )?\b{execution_target}\b \b{_CPU_ORDER}\b|"
            rf"\b{_CPU_EXECUTION}\b (?:each |the |an? |one )?\b{execution_target}\b "
            rf"(?:\w+ ){{0,2}}\b{_CPU_NEGATOR}\b \b{_CPU_ORDER}\b)",
            text,
        )
        possible_or_intermittent_relation = re.search(
            rf"(?:\b{execution_target}\b (?:is |are )?"
            rf"(?:may|might|could|can|only sometimes) (?:be )?\b{_CPU_EXECUTION}\b "
            rf"(?:\w+ ){{0,2}}\b{_CPU_ORDER}\b|"
            rf"\b(?:cpu|processor)\b (?:may|might|could|can|only sometimes) "
            rf"\b{_CPU_EXECUTION}\b (?:each |the )?\b{execution_target}\b "
            rf"\b{_CPU_ORDER}\b)",
            text,
        )
        incompatible_modes = list(
            re.finditer(
                r"\b(?:in any order|out of sequence|simultaneously|at once|"
                r"in parallel|concurrently)\b",
                text,
            )
        )
        contradictory_order = any(
            not re.search(
                rf"\b{_CPU_NEGATOR}\b (?:\w+ ){{0,3}}$",
                text[: match.start()],
            )
            for match in incompatible_modes
        )
        return bool(
            not negated_credited_relation
            and not possible_or_intermittent_relation
            and not contradictory_order
            and (instruction_anchor or pronoun_anchor)
            and (
                any(
                    match and not _relation_is_qualified(text, match)
                    for match in ordered_matches
                )
                or (
                    before_next
                    and not _relation_is_qualified(text, before_next)
                )
                or (
                    passive_before_next
                    and not _relation_is_qualified(text, passive_before_next)
                )
                or (
                    passive_one_at_time
                    and not _relation_is_qualified(text, passive_one_at_time)
                )
            )
        )
    raise ValueError(f"unknown CPU credit criterion: {criterion_id}")


def _validate_judgement(
    item: dict[str, Any], solution: dict[str, Any], raw: Any
) -> CreditJudgement:
    contract = validate_open_credit_contract(item)
    result = CreditJudgement.model_validate(raw, strict=True)
    ids = [row.criterion_id for row in result.criteria]
    if len(ids) != len(set(ids)) or set(ids) != {
        row["id"] for row in contract["criteria"]
    }:
        raise ValueError(
            "semantic review lacks complete unique known criterion decisions"
        )
    if result.issues:
        raise ValueError(
            "semantic review reports unsupported credit: " + "; ".join(result.issues)
        )
    allocations = {
        row["criterion_id"]: row for row in item["marking"]["credit_allocations"]
    }
    unsupported_quotes: list[str] = []
    for row in result.criteria:
        allocation = allocations[row.criterion_id]
        if row.decision != "supported" or (row.point_index, row.marks) != (
            allocation["point_index"],
            allocation["marks"],
        ):
            raise ValueError(
                "semantic review does not support the declared criterion and allocation"
            )
        point = printed_credit_points(item["marking"])[row.point_index]
        if (
            not row.answer_quote.strip()
            or row.answer_quote not in solution["answer"]
            or not row.scheme_quote.strip()
            or row.scheme_quote not in point
        ):
            raise ValueError(
                "semantic review evidence quote is absent from the actual answer or printed point"
            )
        if not _cpu_quote_supports_criterion(row.criterion_id, row.answer_quote):
            meaning = (
                "instructions stored in main memory"
                if row.criterion_id == "instructions-main-memory"
                else "explicit ordered execution"
            )
            unsupported_quotes.append(
                f"{row.criterion_id} exact answer quote lacks {meaning}"
            )
    if unsupported_quotes:
        raise ValueError("; ".join(unsupported_quotes))
    return result


def _semantic_response_envelope(item: dict[str, Any]) -> dict[str, Any]:
    """Describe the exact response shape without supplying semantic answers."""
    contract = validate_open_credit_contract(item)
    allocations = {
        row["criterion_id"]: row for row in item["marking"]["credit_allocations"]
    }
    return {
        "criteria": [
            {
                "criterion_id": criterion["id"],
                "decision": "<supported|unsupported|uncertain>",
                "answer_quote": "<exact final-answer substring or empty string>",
                "scheme_quote": "<exact printed-point substring or empty string>",
                "point_index": allocations[criterion["id"]]["point_index"],
                "marks": allocations[criterion["id"]]["marks"],
            }
            for criterion in contract["criteria"]
        ],
        "issues": ["<zero or more issue strings>"],
        "advisory_conflicts": ["<zero or more advisory-conflict strings>"],
    }


def review_open_credit(
    client: Any, item: dict[str, Any], solution: Any
) -> dict[str, Any]:
    validate_open_credit_contract(item)
    solved = solution.model_dump(mode="json")
    if (
        solved.get("credit_policy_version") != CREDIT_POLICY_VERSION
        or solved.get("solution_source") != "independent-model"
    ):
        raise ValueError(
            "CPU semantic review requires a current independently solved answer"
        )
    raw = client.generate_json(
        "Act as a scoped semantic credit adjudicator, AFTER the blind independent solver. "
        "Judge only the two declared AQA 7517 section 4.7.2.1 criteria. This is model review, not deterministic proof. "
        "For EACH unique criterion decide supported, unsupported or uncertain separately against the independent final answer AND "
        "the actual printed marking point and its allocation. Supported requires both to express the criterion without contradiction. "
        "Read whole statements, including negation and qualifications; quotations alone do not establish support. "
        "Accept genuine paraphrase and reordering. Instructions in main memory and serial processor fetch/execution are distinct one-mark features. "
        "Fetches and executes instructions 'as needed' does not establish ordered execution. "
        "Naming the fetch-decode-execute cycle or only current/next instructions does not establish it either. "
        "Shared instruction/data RAM is not required by the stored-program concept: that is von Neumann-specific. "
        "Same-address confusion, secondary-storage-only and permanent storage of the entire program in the processor do not establish main-memory storage. "
        "Significance, reprogrammability and hardware rewiring are not required. Do not impose model-advisory alternatives, caps or commentary as extra criteria. "
        "Flag contradictory advisory rules in advisory_conflicts, without changing the declared tariff or demanding that advice be printed. "
        "Reject missing, duplicated, extra or contradictory credited meaning; two repetitions of storage cannot earn both marks. "
        "Return only the exact JSON envelope below. Keep criteria in the shown order. "
        "Criterion IDs must be values of criterion_id in that ordered array, never top-level keys. "
        "Do not add keys or omit keys. Use exact substrings of the final answer and actual_printed_points[point_index] as evidence quotes. "
        "Use unsupported/uncertain if either side lacks support; do not fabricate quotations. All lists must be explicit, including empty ones.\n"
        "Exact response envelope (replace every angle-bracket placeholder; use [] when an array is empty):\n"
        + json.dumps(_semantic_response_envelope(item), ensure_ascii=False)
        + "\nReview inputs:\n"
        + json.dumps(
            {
                "item": credit_item_projection(item),
                "actual_printed_points": printed_credit_points(item["marking"]),
                "independent_solution": solved,
            },
            ensure_ascii=False,
        )
    )
    judgement = _validate_judgement(item, solved, raw)
    return {
        "credit_policy_version": CREDIT_POLICY_VERSION,
        "provenance": "model-semantic-adjudication",
        "identity": credit_identity(item, solved),
        "solution": solved,
        "judgement": judgement.model_dump(mode="json"),
    }


def validate_open_credit_review(
    item: dict[str, Any], evidence: Any, *, solution: Any = None
) -> None:
    if (
        not isinstance(evidence, dict)
        or evidence.get("credit_policy_version") != CREDIT_POLICY_VERSION
        or evidence.get("provenance") != "model-semantic-adjudication"
    ):
        raise ValueError("missing or stale semantic credit review")
    solved = evidence.get("solution", {})
    if (
        solved.get("credit_policy_version") != CREDIT_POLICY_VERSION
        or solved.get("solution_source") != "independent-model"
    ):
        raise ValueError(
            "semantic credit review has untyped or stale independent solution"
        )
    if solution is not None and solved != solution.model_dump(mode="json"):
        raise ValueError("semantic credit review belongs to another independent answer")
    if evidence.get("identity") != credit_identity(item, solved):
        raise ValueError(
            "semantic credit review is stale for the source, criteria, answer or scheme"
        )
    _validate_judgement(item, solved, evidence.get("judgement"))
