"""Original task allocations calibrated to AQA 7517, not tariff-based guessing.

Full-paper design budgets match the locally verified June 2025 totals
(20/30/50 and 56/40/4). The source's discounted P1 item is not used as a
difficulty anchor. Focused banks deliberately have their own task-led budgets.
"""
from __future__ import annotations

from Backend.Core.assessment_objectives import objective_policy_for
from Backend.Core.topic_task_contract import (
    TOPIC_CONTRACT_POLICY_ID,
    derive_task_semantics,
)
from cspapergen.models import (
    PaperBlueprint,
    Question,
    QuestionPart,
    ReferenceTaskContract,
)

# Each tuple gives AO1/AO2/AO3 marks for one actual part, not qualification shares.
PAPER2 = {
    "software_classification": [(2,0,0),(2,0,0),(4,0,0)],
    "sound_sampling": [(0,2,0),(1,1,0),(2,0,0),(2,0,0)],
    "bitmap_storage": [(0,6,0),(2,0,0)],
    "legal_issues_short": [(3,0,0)],
    "client_server_short": [(1,2,0)],
    "sql_normalisation": [(0,1,0),(0,4,2),(0,0,2),(0,2,0),(0,1,0)],
    "stored_program": [(2,0,0),(6,0,0),(1,0,0),(1,0,0)],
    "ipv4_extended": [(12,0,0)],
    "truth_table_completion": [(0,4,0),(0,2,0),(1,0,0)],
    "compression_short": [(2,0,0),(2,0,0)],
    "fibonacci_recursion": [(0,1,0),(0,1,0),(2,0,0),(2,0,0)],
    "floating_point": [(1,0,0),(0,3,0),(1,0,0),(1,0,0),(2,0,0),(1,0,0)],
    "boolean_simplification": [(0,4,0)],
    "assembly_program": [(0,6,0)],
}
BANKS = {
    "data_structures_stack_queue": [(0,2,0),(0,2,0),(0,2,0)],
    "data_structures_hash": [(0,3,0),(1,0,0),(2,0,0)],
    "data_structures_tree": [(0,3,0),(0,1,0),(2,0,0)],
    "data_structures_graph": [(0,2,0),(0,2,0),(0,2,0)],
    "data_structures_choice": [(0,2,0),(0,4,0)],
    "sql_normalisation": [(0,1,1),(0,2,1),(0,0,2),(0,2,1),(0,1,1)],
    "erd_keys": [(0,2,0),(0,2,0),(0,2,0),(0,2,0)],
    "database_extended": [(4,3,3)],
    "functional_programming": [(0,2,0),(2,0,0),(2,0,0),(2,0,0)],
    "functional_recursion": [(0,2,0),(0,2,0),(4,0,0)],
    "functional_type_short": [(0,1,0),(3,0,0)],
    "functional_extended": [(4,3,3)],
}


def _reference_task_contract(question: Question, part: QuestionPart) -> ReferenceTaskContract | None:
    if question.topic_id not in {"4.2", "4.10", "4.12"}:
        return None
    semantics = derive_task_semantics(
        task_operation=part.task_operation,
        prompt=part.prompt,
        options=part.options,
        response_slots=part.response_slots,
    )
    if semantics is None:
        return None
    operation, mode = semantics
    return ReferenceTaskContract(
        policy_id=TOPIC_CONTRACT_POLICY_ID,
        topic_id=question.topic_id,
        style_id=question.style_id,
        operation=operation,
        response_mode=mode,
        source_dependency=part.reference_source_dependency,
    )


def calibrate_blueprint(paper: PaperBlueprint) -> PaperBlueprint:
    policy = objective_policy_for("7517")
    for question in paper.questions:
        allocations = (
            BANKS[question.style_id] if paper.assessment_kind == "question-bank"
            else PAPER2[question.style_id] if paper.paper_number == "2"
            else None
        )
        if allocations is not None and len(allocations) != len(question.parts):
            raise ValueError("CS task allocation does not match the part structure")
        for index, part in enumerate(question.parts):
            if allocations is None:
                objective = part.marking.ao
                # General hashing knowledge is AO1; executing the supplied
                # recursive function is AO2 even when the command is "State".
                objective = {
                    (1, "2"): "AO1", (1, "3"): "AO1",
                    (5, "1"): "AO2", (6, "7"): "AO1",
                }.get((question.number, part.label), objective)
                part.assessment_objectives = {objective: part.marks}
            else:
                part.assessment_objectives = {
                    f"AO{i}": n for i, n in enumerate(allocations[index], 1) if n
                }
            if sum(part.assessment_objectives.values()) != part.marks:
                raise ValueError("CS allocated work does not match its tariff")
            part.marking.ao = (
                next(iter(part.assessment_objectives)) if len(part.assessment_objectives) == 1
                else ", ".join(f"{ao} ({n})" for ao, n in part.assessment_objectives.items())
            )
            part.marking.assessment_objectives = dict(part.assessment_objectives)
            part.expected_minutes = paper.duration_minutes * part.marks / paper.total_marks
            raw = part.model_dump(mode="json")
            operation = policy.task_operation(raw, part.prompt.split()[0].lower(), question.style_id)
            if part.response_slots and operation not in {"trace", "transform"}:
                operation = "retrieve" if set(part.assessment_objectives) == {"AO1"} else "analyse"
            if paper.paper_number == "1" and question.number == 6 and part.label in {"2", "3"}:
                operation = "analyse"  # equivalent language/test strings, not new system design
            if paper.paper_number == "1" and question.number == 4 and part.label == "2":
                operation = "judge"
            part.task_operation = operation
            part.reference_source_dependency = (
                "task-context" if question.stimulus else "self-contained"
            )
            part.reference_task_contract = _reference_task_contract(question, part)
            if paper.assessment_kind == "question-bank" and part.marking.levels:
                high = part.marks
                part.marking.levels = [
                    f"Level 4 ({high - 2}–{high}): accurate, developed, contextual reasoning with a supported choice.",
                    f"Level 3 ({high - 5}–{high - 3}): relevant developed reasoning and a partly supported choice.",
                    f"Level 2 (3–{high - 6}): some relevant knowledge and limited application.",
                    "Level 1 (1–2): isolated relevant points.", "Level 0 (0): no creditworthy material.",
                ] if high >= 9 else [
                    f"Level 3 (5–{high}): accurate contextual comparison and a supported choice.",
                    "Level 2 (3–4): some developed comparison with partial application.",
                    "Level 1 (1–2): isolated relevant points.", "Level 0 (0): no creditworthy material.",
                ]
    policy.validate(paper)
    return paper
