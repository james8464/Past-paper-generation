# Generate and review draft items, resuming only accepted checkpoint content.

from __future__ import annotations

import json
import logging
import math
import re
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import ValidationError

from Backend.Core import assessment_prompts as _assessment_prompts
from Backend.Core.assessment_checkpoints import AssessmentCheckpointStore
from Backend.Core.assessment_contracts import EvidenceRecord, contract_for_question
from Backend.Core.assessment_quality import (
    assert_distinct_items,
    content_similarity,
    numeric_tokens,
    validate_candidate_contract,
    validate_economics_causal_direction,
)
from Backend.Core.candidate_identity import shared_difficulty_candidate_projection
from Backend.Core.events import GenerationUpdate
from Backend.Core.exam_blueprints import (
    GeneratedOption,
    GeneratedPaper,
    GeneratedQuestion,
    GeneratedSection,
    MarkSchemePoint,
    PaperRule,
    validate_generated_paper,
)
from Backend.Core.generation_diagnostics import GenerationEvidenceError
from Backend.Core.generation_requests import OutputContract, make_request, request_json
from Backend.Core.independent_solver import (
    CanonicalSolution,
    IndependentSolver,
    reconcile_solution,
    solution_failure_evidence,
)
from Backend.Core.json_client import JSONGenerationClient
from Backend.Core.mark_scheme_quality import validate_mark_scheme_item
from Backend.Core.model_review import (
    ReviewResult,
    require_difficulty_review,
    validate_saved_difficulty_evidence,
)
from Backend.Core.reference_demand import (
    ReferenceDemandProfile,
    build_item_demand_target,
)
from Backend.Core.subjects.selected_response import solve_selected_response

# Keep established helper entry points while prompt construction has one owner.
_Task = _assessment_prompts.AssessmentPromptTask
_generation_prompt = _assessment_prompts.generation_prompt
_repair_prompt = _assessment_prompts.repair_prompt
_review_prompt = _assessment_prompts.review_prompt
_required_awarded_entries = _assessment_prompts.required_awarded_entries
_semantic_task_contract = _assessment_prompts.semantic_task_contract
_review_question_payload = _assessment_prompts.review_question_payload
_task_source = _assessment_prompts.task_source
_demand_item = _assessment_prompts.demand_item
_question_uses_option_source = _assessment_prompts.question_uses_option_source
_SEMANTIC_STOPWORDS = _assessment_prompts._SEMANTIC_STOPWORDS

LOGGER = logging.getLogger(__name__)
ASSESSMENT_REVIEW_VERSION = "assessment-review-v7-trusted-generation-requests"


class AssessmentLLMClient(JSONGenerationClient, Protocol):
    provider: str
    model: str

    @property
    def supports_parallel_generation(self) -> bool: ...


@dataclass(frozen=True)
class GenerationPolicy:
    batch_size: int = 6
    attempts: int = 3
    max_workers: int = 4
    draft_similarity_limit: float = 0.82
    paper_similarity_limit: float = 0.84
    require_model_review: bool = True
    require_independent_solution: bool = False
    require_difficulty_review: bool = False

    def __post_init__(self) -> None:
        for name in ("batch_size", "attempts", "max_workers"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"{name} must be a positive integer, not a boolean")
        # Similarity scores lie in 0...1. The inclusive comparison deliberately
        # keeps zero maximally strict and one able to reject exact duplicates.
        for name in ("draft_similarity_limit", "paper_similarity_limit"):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not 0 <= value <= 1
                or not math.isfinite(value)
            ):
                raise ValueError(f"{name} must be a finite number between 0 and 1")


# A checked answer does not establish stem or distractor quality.
def _requires_model_review(
    question: GeneratedQuestion,
    policy: GenerationPolicy,
) -> bool:

    return policy.require_model_review


# Replace draft items while keeping the authoritative assessment blueprint frozen.
def generate_unique_paper(
    paper: GeneratedPaper,
    *,
    rule: PaperRule,
    syllabus_topics: Iterable[Any],
    syllabus_topic_ids: Iterable[str],
    client: AssessmentLLMClient,
    subject: str,
    progress: Callable[[str | GenerationUpdate], None] | None = None,
    policy: GenerationPolicy | None = None,
    checkpoint_store: AssessmentCheckpointStore | None = None,
    demand_profile: ReferenceDemandProfile | None = None,
) -> GeneratedPaper:

    policy = policy or GenerationPolicy()
    emit = progress or (lambda _message: None)
    topics = {str(topic.id): topic for topic in syllabus_topics}
    tasks = _tasks(paper, topics)
    batches = _batches_for_client(tasks, client=client, policy=policy)
    emit(
        f"Generating {len(tasks)} original items in {len(batches)} "
        "blueprint-constrained batches"
    )

    generated: dict[tuple[int, int, int], GeneratedQuestion] = {}
    if getattr(client, "supports_parallel_generation", False) and len(batches) > 1:
        with ThreadPoolExecutor(
            max_workers=min(policy.max_workers, len(batches)),
            thread_name_prefix="paper-items",
        ) as executor:
            futures = {
                executor.submit(
                    _generate_batch,
                    batch,
                    client=client,
                    subject=subject,
                    seed=paper.seed,
                    policy=policy,
                    progress=None,
                    checkpoint_store=checkpoint_store,
                    demand_profile=demand_profile,
                ): batch
                for batch in batches
            }
            completed_items = 0
            for completed, future in enumerate(as_completed(futures), start=1):
                batch_result = future.result()
                generated.update(batch_result)
                completed_items += len(batch_result)
                emit(
                    GenerationUpdate(
                        stage="checkpoint",
                        message=(
                            f"Accepted {completed_items} of {len(tasks)} AI items"
                        ),
                        completed_units=completed_items,
                        total_units=len(tasks),
                    )
                )
                emit(f"Validated AI item batch {completed} of {len(batches)}")
    else:
        completed_items = 0
        for index, batch in enumerate(batches, start=1):
            emit(f"Drafting and reviewing AI item batch {index} of {len(batches)}")
            generated.update(
                _generate_batch(
                    batch,
                    client=client,
                    subject=subject,
                    seed=paper.seed,
                    policy=policy,
                    progress=emit,
                    checkpoint_store=checkpoint_store,
                    demand_profile=demand_profile,
                    total_items=len(tasks),
                    completed_before=completed_items,
                )
            )
            completed_items += len(batch)
            emit(f"Validated AI item batch {index} of {len(batches)}")

    sections: list[GeneratedSection] = []
    for section_index, section in enumerate(paper.sections):
        options: list[GeneratedOption] = []
        for option_index, option in enumerate(section.options):
            questions = [
                generated[(section_index, option_index, question_index)]
                for question_index in range(len(option.questions))
            ]
            options.append(option.model_copy(update={"questions": questions}))
        sections.append(section.model_copy(update={"options": options}))
    result = paper.model_copy(update={"sections": sections})
    validate_generated_paper(result, rule, syllabus_topic_ids)
    assert_distinct_items(
        (
            {
                "id": task.id,
                "prompt": generated[task.key].prompt,
            }
            for task in tasks
        ),
        threshold=policy.paper_similarity_limit,
    )
    return result


def _tasks(paper: GeneratedPaper, topics: dict[str, Any]) -> list[_Task]:
    result: list[_Task] = []
    for section_index, section in enumerate(paper.sections):
        for option_index, option in enumerate(section.options):
            for question_index, question in enumerate(option.questions):
                try:
                    topic = topics[question.topic_id]
                except KeyError as error:
                    raise ValueError(
                        f"question {question.number} references unknown topic "
                        f"{question.topic_id}"
                    ) from error
                result.append(
                    _Task(
                        key=(section_index, option_index, question_index),
                        question=question,
                        option=option,
                        topic=topic,
                    )
                )
    return result


def _generate_batch(
    tasks: list[_Task],
    *,
    client: AssessmentLLMClient,
    subject: str,
    seed: int,
    policy: GenerationPolicy,
    progress: Callable[[str | GenerationUpdate], None] | None,
    checkpoint_store: AssessmentCheckpointStore | None = None,
    total_items: int | None = None,
    completed_before: int = 0,
    demand_profile: ReferenceDemandProfile | None = None,
) -> dict[tuple[int, int, int], GeneratedQuestion]:
    verified = [
        task
        for task in tasks
        if task.question.authoring_context.get("preserve_prompt") is True
        and task.question.authoring_context.get("preserve_mark_scheme") is True
    ]
    for task in verified:
        _validate_release_mark_scheme(task.question)
    verified_to_review = (
        verified
        if (
            policy.require_model_review
            or policy.require_independent_solution
            or policy.require_difficulty_review
        )
        else []
    )
    trusted_verified = [] if verified_to_review else verified
    result: dict[tuple[int, int, int], GeneratedQuestion] = {
        task.key: task.question.model_copy(update={"provenance": "verified-contract"})
        for task in trusted_verified
    }
    resumed: list[_Task] = []
    if checkpoint_store is not None:
        for task in tasks:
            if task.key in result:
                continue
            stored = checkpoint_store.load_item(task.id)
            if stored is None:
                continue
            original_stored = stored
            stored = _upgrade_checkpoint_metadata(task, stored)
            try:
                _validate_checkpoint_item(
                    task,
                    stored,
                    demand_profile=demand_profile
                    if policy.require_difficulty_review
                    else None,
                )
            except ValueError as error:
                LOGGER.info(
                    "Discarding invalid checkpoint item %s: %s",
                    task.id,
                    error,
                )
                checkpoint_store.discard_item(task.id)
                continue
            if stored != original_stored:
                checkpoint_store.save_item(task.id, stored)
            result[task.key] = stored
            resumed.append(task)
    accepted: list[dict[str, str]] = [
        {"id": task.id, "prompt": result[task.key].prompt}
        for task in [*trusted_verified, *resumed]
    ]
    if progress is not None:
        for index, task in enumerate([*trusted_verified, *resumed], start=1):
            progress(
                GenerationUpdate(
                    stage="checkpoint",
                    message=f"Resumed accepted AI item {task.question.number}",
                    item_id=task.id,
                    completed_units=completed_before + index,
                    total_units=total_items or len(tasks),
                )
            )
    for task in verified_to_review:
        if task.key in result:
            continue
        candidate = _review_verified_contract(
            task,
            client=client,
            subject=subject,
            policy=policy,
            progress=progress,
            demand_profile=demand_profile,
        )
        if checkpoint_store is not None:
            checkpoint_store.save_item(task.id, candidate)
        result[task.key] = candidate
        accepted.append({"id": task.id, "prompt": candidate.prompt})
        if progress is not None:
            progress(
                GenerationUpdate(
                    stage="checkpoint",
                    message=f"Accepted reviewed contract {task.question.number}",
                    item_id=task.id,
                    completed_units=completed_before + len(result),
                    total_units=total_items or len(tasks),
                )
            )
    completed_keys = set(result)
    for task in (task for task in tasks if task.key not in completed_keys):
        candidate = _generate_item_transaction(
            task,
            client=client,
            subject=subject,
            seed=seed,
            policy=policy,
            progress=progress,
            accepted_prompts=accepted,
            demand_profile=demand_profile,
        )
        if checkpoint_store is not None:
            checkpoint_store.save_item(task.id, candidate)
        result[task.key] = candidate
        accepted.append({"id": task.id, "prompt": candidate.prompt})
        if progress is not None:
            progress(
                GenerationUpdate(
                    stage="checkpoint",
                    message=f"Accepted AI item {task.question.number}",
                    item_id=task.id,
                    completed_units=completed_before + len(result),
                    total_units=total_items or len(tasks),
                )
            )
    return result


def _review_verified_contract(
    task: _Task,
    *,
    client: AssessmentLLMClient,
    subject: str,
    policy: GenerationPolicy,
    progress: Callable[[str | GenerationUpdate], None] | None,
    demand_profile: ReferenceDemandProfile | None,
) -> GeneratedQuestion:
    candidate = task.question
    canonical_solution = (
        _independently_validate_candidate(task, candidate, client=client)
        if policy.require_independent_solution
        else None
    )
    review = (
        _review_batch(
            [task],
            [candidate],
            client=client,
            subject=subject,
            canonical_solutions={task.id: canonical_solution},
        )[task.id]
        if _requires_model_review(candidate, policy)
        else ReviewResult(approved=True)
    )
    if not review.approved or review.issues:
        raise RuntimeError(
            f"verified contract {task.question.number} failed assessment review: "
            + "; ".join(review.issues or ["not approved"])
        )
    if policy.require_difficulty_review:
        if demand_profile is None:
            raise ValueError("reference-demand review requires a paper profile")
        if progress is not None:
            progress(
                GenerationUpdate(
                    stage="difficulty-review",
                    message=(
                        "Checking locked question "
                        f"{task.question.number} against real-paper demand"
                    ),
                    item_id=task.id,
                )
            )
        difficulty_evidence = require_difficulty_review(
            client,
            item_id=task.id,
            subject=subject,
            target=build_item_demand_target(_demand_item(task), demand_profile),
            candidate=_difficulty_candidate(task, candidate),
            specification=_difficulty_specification(task),
            canonical_solution=canonical_solution,
        )
        candidate = candidate.model_copy(
            update={
                "authoring_context": {
                    **candidate.authoring_context,
                    "difficulty_evidence": difficulty_evidence.model_dump(mode="json"),
                }
            }
        )
    return candidate.model_copy(update={"provenance": "verified-contract-reviewed"})


def _validate_checkpoint_item(
    task: _Task,
    candidate: GeneratedQuestion,
    *,
    demand_profile: ReferenceDemandProfile | None = None,
) -> None:
    original = task.question
    if (
        original.authoring_context.get("preserve_prompt")
        and candidate.prompt != original.prompt
    ):
        raise ValueError(
            f"checkpoint item {task.id} changed immutable preserved prompt"
        )
    immutable = (
        "rule_id",
        "number",
        "marks",
        "kind",
        "command_word",
        "topic_id",
        "assessment_objectives",
        "intended_demand",
        "expected_minutes",
        "scheme_mode",
        "contract",
        "source_references",
    )
    changed = [
        name
        for name in immutable
        if getattr(candidate, name) != getattr(original, name)
    ]
    if changed:
        raise ValueError(
            f"checkpoint item {task.id} changed immutable fields: {changed}"
        )
    original_context = dict(original.authoring_context)
    candidate_context = dict(candidate.authoring_context)
    original_context.pop("difficulty_evidence", None)
    candidate_context.pop("difficulty_evidence", None)
    if candidate_context != original_context:
        raise ValueError(
            f"checkpoint item {task.id} changed immutable authoring context"
        )
    selected_response = isinstance(
        original.authoring_context.get("selected_response_contract"), dict
    )
    if selected_response and (
        candidate.choices != original.choices
        or candidate.correct_choice != original.correct_choice
    ):
        raise ValueError(
            f"checkpoint item {task.id} changed source-owned choices or key"
        )
    preserves_scheme = (
        original.authoring_context.get("preserve_mark_scheme") is True
        or selected_response
    )
    if preserves_scheme and (
        candidate.mark_scheme != original.mark_scheme
        or candidate.structured_mark_scheme != original.structured_mark_scheme
    ):
        raise ValueError(f"checkpoint item {task.id} changed verified marking guidance")
    if selected_response:
        solve_selected_response(candidate.model_dump(mode="json"))
    if not candidate.prompt.strip() or not candidate.structured_mark_scheme:
        raise ValueError(f"checkpoint item {task.id} is incomplete")
    _validate_prompt_length(original, candidate.prompt)
    if not preserves_scheme:
        _validate_mark_points(original, candidate.structured_mark_scheme)
    _validate_release_mark_scheme(candidate)
    if demand_profile is not None:
        validate_saved_difficulty_evidence(
            candidate.authoring_context.get("difficulty_evidence", {}),
            build_item_demand_target(_demand_item(task), demand_profile),
            item_id=task.id,
            candidate=_difficulty_candidate(task, candidate),
        )


# Adopt a newly added layout budget without weakening item validation.
def _upgrade_checkpoint_metadata(
    task: _Task,
    candidate: GeneratedQuestion,
) -> GeneratedQuestion:

    current = dict(task.question.authoring_context)
    stored = dict(candidate.authoring_context)
    evidence = stored.pop("difficulty_evidence", None)
    if stored == current or "max_prompt_words" not in current:
        return candidate
    previous = dict(current)
    previous.pop("max_prompt_words")
    if stored != previous:
        return candidate
    if evidence is not None:
        current["difficulty_evidence"] = evidence
    return candidate.model_copy(update={"authoring_context": current})


def _generate_item_transaction(
    task: _Task,
    *,
    client: AssessmentLLMClient,
    subject: str,
    seed: int,
    policy: GenerationPolicy,
    progress: Callable[[str | GenerationUpdate], None] | None,
    accepted_prompts: list[dict[str, str]],
    demand_profile: ReferenceDemandProfile | None = None,
) -> GeneratedQuestion:
    failure = ""
    last_error: Exception | None = None
    candidate: GeneratedQuestion | None = None
    review: ReviewResult | None = None
    for attempt in range(1, policy.attempts + 1):
        last_error = None
        try:
            prompt = (
                _generation_prompt(
                    [task],
                    subject=subject,
                    seed=seed,
                    attempt=attempt,
                    previous_failure=failure,
                    demand_profile=demand_profile,
                )
                if candidate is None or review is None
                else _repair_prompt(
                    task,
                    candidate,
                    review,
                    subject=subject,
                    seed=seed,
                    attempt=attempt,
                    demand_profile=demand_profile,
                )
            )
            raw = request_json(
                client,
                make_request(
                    prompt,
                    OutputContract(
                        "authoring",
                        identifiers=(task.id,),
                        mark_schemes_locked=task.question.authoring_context.get(
                            "preserve_mark_scheme"
                        )
                        is True,
                    ),
                    generation_seed=seed,
                    attempt=attempt,
                ),
            )
            candidate = _parse_batch(
                raw,
                [task],
                client=client,
                policy=policy,
            )[0]
            canonical_solution: CanonicalSolution | None = None
            if policy.require_independent_solution:
                canonical_solution = _independently_validate_candidate(
                    task,
                    candidate,
                    client=client,
                )
            if "economics" in subject.casefold():
                validate_economics_causal_direction(
                    " ".join(
                        [
                            candidate.prompt,
                            *(point.text for point in candidate.structured_mark_scheme),
                        ]
                    )
                )
            review = (
                _review_batch(
                    [task],
                    [candidate],
                    client=client,
                    subject=subject,
                    canonical_solutions={task.id: canonical_solution},
                )[task.id]
                if _requires_model_review(candidate, policy)
                else ReviewResult(approved=True)
            )
            if review.approved and not review.issues:
                if policy.require_difficulty_review:
                    if demand_profile is None:
                        raise ValueError(
                            "reference-demand review requires a paper profile"
                        )
                    if progress is not None:
                        progress(
                            GenerationUpdate(
                                stage="difficulty-review",
                                message=(
                                    "Checking question "
                                    f"{task.question.number} against real-paper demand"
                                ),
                                item_id=task.id,
                            )
                        )
                    try:
                        difficulty_evidence = require_difficulty_review(
                            client,
                            item_id=task.id,
                            subject=subject,
                            target=build_item_demand_target(
                                _demand_item(task),
                                demand_profile,
                            ),
                            candidate=_difficulty_candidate(task, candidate),
                            specification=_difficulty_specification(task),
                            canonical_solution=canonical_solution,
                        )
                        candidate = candidate.model_copy(
                            update={
                                "authoring_context": {
                                    **candidate.authoring_context,
                                    "difficulty_evidence": difficulty_evidence.model_dump(
                                        mode="json"
                                    ),
                                }
                            }
                        )
                    except ValueError as error:
                        review = ReviewResult(
                            approved=False,
                            difficulty_issues=[str(error)],
                        )
                        raise
                assert_distinct_items(
                    [
                        *accepted_prompts,
                        {"id": task.id, "prompt": candidate.prompt},
                    ],
                    threshold=policy.paper_similarity_limit,
                    context="accepted AI items",
                )
                return candidate
            failure = "; ".join(review.issues or ["not approved"])
        except (KeyError, TypeError, ValueError, ValidationError) as error:
            last_error = error
            failure = str(error)[:800]
            LOGGER.debug(
                "AI item attempt %s of %s failed for question %s: %s",
                attempt,
                policy.attempts,
                task.question.number,
                failure,
            )
        if attempt < policy.attempts and progress is not None:
            progress(
                f"Refining AI item {task.question.number} after an automated "
                f"quality check: {failure}"
            )
    provider = str(getattr(client, "provider", "custom"))
    if _seeded_fallback_allowed(provider=provider, failure=failure):
        fallback = task.question
        _validate_release_mark_scheme(fallback)
        canonical_solution = (
            _independently_validate_candidate(task, fallback, client=client)
            if policy.require_independent_solution
            else None
        )
        fallback_review = (
            _review_batch(
                [task],
                [fallback],
                client=client,
                subject=subject,
                canonical_solutions={task.id: canonical_solution},
            )[task.id]
            if _requires_model_review(fallback, policy)
            else ReviewResult(approved=True)
        )
        if fallback_review.approved and not fallback_review.issues:
            if policy.require_difficulty_review:
                if demand_profile is None:
                    raise ValueError("reference-demand review requires a paper profile")
                difficulty_evidence = require_difficulty_review(
                    client,
                    item_id=task.id,
                    subject=subject,
                    target=build_item_demand_target(
                        _demand_item(task),
                        demand_profile,
                    ),
                    candidate=_difficulty_candidate(task, fallback),
                    specification=_difficulty_specification(task),
                    canonical_solution=canonical_solution,
                )
                fallback = fallback.model_copy(
                    update={
                        "authoring_context": {
                            **fallback.authoring_context,
                            "difficulty_evidence": difficulty_evidence.model_dump(
                                mode="json"
                            ),
                        }
                    }
                )
            assert_distinct_items(
                [
                    *accepted_prompts,
                    {"id": task.id, "prompt": fallback.prompt},
                ],
                threshold=policy.paper_similarity_limit,
                context="accepted AI items",
            )
            return fallback.model_copy(
                update={"provenance": f"reviewed-seeded-fallback:{provider}"}
            )
        failure = "; ".join(fallback_review.issues or ["not approved"])
    raise RuntimeError(
        "AI could not produce a valid, second-pass reviewed item for "
        f"question {task.question.number}: {failure}"
    ) from last_error


def _independently_validate_candidate(
    task: _Task,
    candidate: GeneratedQuestion,
    *,
    client: AssessmentLLMClient,
) -> CanonicalSolution:
    if (
        task.question.authoring_context.get("preserve_prompt")
        and candidate.prompt != task.question.prompt
    ):
        raise ValueError(
            f"question {candidate.number} changed immutable numeric prompt"
        )
    numeric_fields = {
        key
        for key in task.question.authoring_context
        if key.startswith("calculation_")
        or key
        in {
            "cs_input_contract",
            "numeric_input_contract",
            "source_data",
            "candidate_source",
            "selected_response_contract",
            "accounting_source_content",
            "accounting_marking_policy",
            "grouped_level_policy",
            "opening_balances",
            "depreciation_policy",
            "transactions_at_start_of_year",
            "adjustment_source_data",
            "adjustment_policy",
            "task_scope",
            "required_entries",
            "referenced_question_data",
            "independent_solver_instructions",
        }
    }
    if any(
        candidate.authoring_context.get(key) != task.question.authoring_context[key]
        for key in numeric_fields
    ):
        raise ValueError(
            f"question {candidate.number} changed immutable numeric source contract"
        )
    contract_for_question(
        candidate
    )  # Retain full contract validation before model use.
    # The option may contain planning extracts that its specialist renderer
    # never prints (e.g. Accounting 14.2 uses the company-statement case).
    # A blind solver must see the same public evidence as the writer/reviewer.
    sources = [
        EvidenceRecord.model_validate(source)
        for source in _task_source(task).get("evidence", [])
    ]
    solution = IndependentSolver(client).solve(candidate, sources)
    result = reconcile_solution(solution, candidate)
    if not result.passed:
        diagnostics = [
            {"field": issue.field, "message": issue.message} for issue in result.issues
        ]
        raise GenerationEvidenceError(
            f"question {candidate.number} failed independent solution "
            f"reconciliation: {json.dumps(diagnostics, ensure_ascii=False)}",
            details=solution_failure_evidence(solution, result.issues),
        )
    return solution


# Permit a reviewed local blueprint stem only for formatting-only drift.
def _seeded_fallback_allowed(*, provider: str, failure: str) -> bool:

    return provider.casefold() in {"ollama", "apple"} and any(
        reason in failure.casefold()
        for reason in (
            "changed the required precision instruction",
            "only a paraphrase of the draft",
            "words; maximum is",
            "omitted a required source or visual term",
            "changed immutable numeric data",
        )
    )


# Keep local structured responses below practical context/output limits.
def _effective_batch_size(
    client: AssessmentLLMClient,
    policy: GenerationPolicy,
) -> int:

    if getattr(client, "supports_parallel_generation", False):
        return policy.batch_size
    return min(policy.batch_size, 3)


def _batches_for_client(
    tasks: list[_Task],
    *,
    client: AssessmentLLMClient,
    policy: GenerationPolicy,
) -> list[list[_Task]]:
    if getattr(client, "supports_parallel_generation", False):
        return [
            tasks[index : index + policy.batch_size]
            for index in range(0, len(tasks), policy.batch_size)
        ]

    batches: list[list[_Task]] = []
    current: list[_Task] = []
    current_weight = 0
    for task in tasks:
        weight = 2 + min(task.question.marks, 8)
        if current and (
            len(current) >= _effective_batch_size(client, policy)
            or current_weight + weight > 12
        ):
            batches.append(current)
            current = []
            current_weight = 0
        current.append(task)
        current_weight += weight
    if current:
        batches.append(current)
    return batches


def _parse_batch(
    raw: dict[str, object],
    tasks: list[_Task],
    *,
    client: AssessmentLLMClient,
    policy: GenerationPolicy,
) -> list[GeneratedQuestion]:
    values = raw.get("questions")
    if not isinstance(values, list) or len(values) != len(tasks):
        raise ValueError(
            "response must contain exactly one result per requested question"
        )
    by_id = {str(value.get("id")): value for value in values if isinstance(value, dict)}
    if set(by_id) != {task.id for task in tasks}:
        raise ValueError("response question identifiers do not match the blueprint")
    candidates = [
        _candidate_question(
            task,
            by_id[task.id],
            client=client,
            policy=policy,
        )
        for task in tasks
    ]
    assert_distinct_items(
        (
            {"id": task.id, "prompt": candidate.prompt}
            for task, candidate in zip(tasks, candidates, strict=True)
        ),
        threshold=policy.paper_similarity_limit,
        context="AI batch",
    )
    return candidates


def _candidate_question(
    task: _Task,
    raw: dict[str, Any],
    *,
    client: AssessmentLLMClient,
    policy: GenerationPolicy,
) -> GeneratedQuestion:
    original = task.question
    selected_response_contract = original.authoring_context.get(
        "selected_response_contract"
    )
    has_selected_response_contract = isinstance(selected_response_contract, dict)
    generated_prompt = _clean_generated_prompt(
        _bounded_text(raw.get("prompt"), name="prompt", limit=5000),
        question=original,
    )
    generated_prompt = _normalise_command_word(
        generated_prompt,
        original.command_word,
    )
    preserve_prompt = original.authoring_context.get("preserve_prompt") is True
    prompt = original.prompt if preserve_prompt else generated_prompt
    _validate_prompt_length(original, prompt)
    generated_values = raw.get("generated_numeric_values")
    validate_candidate_contract(
        original.prompt,
        prompt,
        contract_for_question(original),
        generated_values=(
            {
                str(name): float(value)
                for name, value in generated_values.items()
                if isinstance(value, (int, float))
            }
            if isinstance(generated_values, dict)
            else None
        ),
    )
    if original.kind != "multiple_choice" and not _contains_command_word(
        prompt, original.command_word
    ):
        raise ValueError(
            f"question {original.number} omitted command word {original.command_word!r}"
        )
    if not preserve_prompt:
        similarity = content_similarity(prompt, original.prompt)
        word_count = len(prompt.split())
        limit = 0.9 if word_count < 10 else policy.draft_similarity_limit
        if similarity >= limit:
            raise ValueError(
                f"question {original.number} is only a paraphrase of the draft "
                f"({similarity:.3f})"
            )
    required_prompt_terms = original.authoring_context.get(
        "required_prompt_terms",
        [],
    )
    if required_prompt_terms and (
        not isinstance(required_prompt_terms, list)
        or not all(
            isinstance(term, str) and term.casefold() in prompt.casefold()
            for term in required_prompt_terms
        )
    ):
        raise ValueError(
            f"question {original.number} omitted a required source or visual term"
        )
    forbidden_prompt_terms = original.authoring_context.get(
        "forbidden_prompt_terms",
        [],
    )
    if forbidden_prompt_terms and (
        not isinstance(forbidden_prompt_terms, list)
        or any(
            not isinstance(term, str) or term.casefold() in prompt.casefold()
            for term in forbidden_prompt_terms
        )
    ):
        raise ValueError(
            f"question {original.number} included a forbidden semantic term"
        )

    preserve_mark_scheme = (
        original.authoring_context.get("preserve_mark_scheme") is True
        or has_selected_response_contract
    )
    if preserve_mark_scheme:
        points = list(original.structured_mark_scheme)
        if not points:
            raise ValueError(
                f"question {original.number} has no verified structured mark scheme"
            )
    else:
        raw_points = raw.get("mark_scheme")
        if not isinstance(raw_points, list) or not raw_points:
            raise ValueError(
                f"question {original.number} requires structured marking points"
            )
        points = [MarkSchemePoint.model_validate(point) for point in raw_points]
        points = _normalise_level_allocations(original, points)
    points = _normalise_calculation_guidance(original, points)
    if not preserve_mark_scheme:
        _validate_mark_points(original, points)
    required_mark_scheme_terms = original.authoring_context.get(
        "required_mark_scheme_terms",
        [],
    )
    marking_text = " ".join(point.text for point in points).casefold()
    if required_mark_scheme_terms and (
        not isinstance(required_mark_scheme_terms, list)
        or not all(
            isinstance(term, str) and term.casefold() in marking_text
            for term in required_mark_scheme_terms
        )
    ):
        raise ValueError(f"question {original.number} omitted required marking content")
    forbidden_mark_scheme_terms = original.authoring_context.get(
        "forbidden_mark_scheme_terms",
        [],
    )
    if forbidden_mark_scheme_terms and (
        not isinstance(forbidden_mark_scheme_terms, list)
        or any(
            not isinstance(term, str) or term.casefold() in marking_text
            for term in forbidden_mark_scheme_terms
        )
    ):
        raise ValueError(
            f"question {original.number} included forbidden marking content"
        )

    if original.kind == "multiple_choice":
        if has_selected_response_contract:
            # The choices and answer key are projections of public, deterministic
            # source data. A language model may improve the stem, but must not
            # alter a unit, precision, distractor or key owned by that contract.
            rendered_choices = list(original.choices)
            correct_choice = original.correct_choice
        else:
            choices = raw.get("choices")
            correct_choice = raw.get("correct_choice")
            if (
                not isinstance(choices, list)
                or len(choices) != 4
                or not all(
                    isinstance(choice, str) and choice.strip() for choice in choices
                )
                or len({" ".join(choice.casefold().split()) for choice in choices}) != 4
                or not isinstance(correct_choice, int)
                or correct_choice not in range(4)
            ):
                raise ValueError(
                    f"question {original.number} requires four unique choices and a valid answer"
                )
            rendered_choices = [str(choice).strip() for choice in choices]
            answer = rendered_choices[correct_choice].casefold()
            if answer not in " ".join(point.text for point in points).casefold():
                points = _normalise_multiple_choice_answer(
                    original,
                    points,
                    rendered_choices[correct_choice],
                )
        _validate_mcq_prompt_options(original, prompt, rendered_choices)
    else:
        rendered_choices = []
        correct_choice = None

    provider = str(getattr(client, "provider", "custom"))
    model = str(getattr(client, "model", "unknown"))
    rendered_scheme = (
        list(original.mark_scheme)
        if preserve_mark_scheme
        else [
            point.text
            for point in points
            if original.scheme_mode != "levels" or point.credit_type == "guidance"
        ]
    )
    candidate = original.model_copy(
        update={
            "prompt": prompt,
            "mark_scheme": rendered_scheme,
            "choices": rendered_choices,
            "correct_choice": correct_choice,
            "scheme_mode": original.scheme_mode,
            "structured_mark_scheme": points,
            "provenance": f"ai:{provider}:{model}",
        }
    )
    if has_selected_response_contract:
        # Reject invalid public stems inside the repair loop, before review or
        # checkpointing, even when optional independent model solving is off.
        solve_selected_response(candidate.model_dump(mode="json"))
    _validate_release_mark_scheme(candidate)
    return candidate


def _normalise_calculation_guidance(
    question: GeneratedQuestion,
    points: list[MarkSchemePoint],
) -> list[MarkSchemePoint]:
    calculation = (
        question.kind == "calculation"
        or question.command_word.casefold()
        in {
            "calculate",
            "complete",
            "prepare",
        }
    )
    if not calculation or question.marks < 3:
        return points
    guidance_text = " ".join(point.text for point in points).casefold()
    if any(
        token in guidance_text
        for token in ("working", "method", "formula", "calculation", " = ", "step")
    ):
        return points
    return [
        *points,
        MarkSchemePoint(
            text=(
                "Award method credit for a correct formula, substitution and "
                "consistent working, including a valid answer carried forward."
            ),
            marks=0,
            credit_type="guidance",
        ),
    ]


# Apply the package quality gate before an item can be checkpointed.
def _validate_release_mark_scheme(question: GeneratedQuestion) -> None:

    raw = question.model_dump(mode="json")
    evidence_ids = list(question.source_references)
    contract = raw.get("contract")
    if isinstance(contract, dict):
        allowed = contract.get("allowed_evidence_ids")
        if isinstance(allowed, list):
            evidence_ids.extend(str(value) for value in allowed)
    validate_mark_scheme_item(
        {
            "id": question.number,
            "marks": question.marks,
            "kind": question.kind,
            "command_word": question.command_word,
            "mark_scheme": question.mark_scheme,
            "structured_mark_scheme": raw["structured_mark_scheme"],
            "assessment_objectives": question.assessment_objectives,
            "evidence_ids": list(dict.fromkeys(evidence_ids)),
            "assessment_contract": (
                contract
                if isinstance(contract, dict)
                else {
                    field: question.authoring_context[field]
                    for field in (
                        "valid_alternatives",
                        "partial_credit_boundaries",
                        "follow_through_rules",
                    )
                    if field in question.authoring_context
                }
            ),
        }
    )


# Reject an option list that the renderer would print a second time.
def _validate_mcq_prompt_options(
    question: GeneratedQuestion, prompt: str, choices: list[str]
) -> None:
    # The renderer owns the option list. Match the actual four choices, rather
    # than banning labels that could legitimately identify data in the stem.
    labels = list(
        re.finditer(
            r"(?<!\w)(?:\*\*|__)?\(?([A-D])(?:\*\*|__)?\s*[.):\-\u2013\u2014](?:\*\*|__)?\s+",
            prompt,
            re.IGNORECASE,
        )
    )
    choice_words = [re.findall(r"\w+", choice.casefold()) for choice in choices]
    for start in range(len(labels) - 3):
        group = labels[start : start + 4]
        if [match.group(1).upper() for match in group] != list("ABCD"):
            continue
        duplicated = True
        for index, match in enumerate(group):
            end = group[index + 1].start() if index < 3 else len(prompt)
            words = re.findall(r"\w+", prompt[match.end() : end].casefold())
            expected = choice_words[index]
            if not expected or words[: len(expected)] != expected:
                duplicated = False
                break
        if duplicated:
            raise ValueError(
                f"question {question.number} embedded alternatives in its prompt; "
                "provide options only in choices"
            )


# Make the selected answer explicit when a model uses only a shorthand label.
def _normalise_multiple_choice_answer(
    question: GeneratedQuestion,
    points: list[MarkSchemePoint],
    answer: str,
) -> list[MarkSchemePoint]:

    awarded = [index for index, point in enumerate(points) if point.marks]
    if question.marks != 1 or len(awarded) != 1:
        raise ValueError(
            f"question {question.number} marking points do not state the correct choice"
        )
    index = awarded[0]
    result = list(points)
    result[index] = result[index].model_copy(update={"text": answer})
    return result


def _validate_mark_points(
    question: GeneratedQuestion,
    points: list[MarkSchemePoint],
) -> None:
    maximum_points = max(8, min(18, question.marks + 6))
    if len(points) > maximum_points:
        raise ValueError(
            f"question {question.number} has {len(points)} marking entries; "
            f"maximum {maximum_points}"
        )
    if any(len(point.text) > 400 for point in points):
        raise ValueError(f"question {question.number} has an overlong marking entry")
    awarded = [point for point in points if point.marks]
    is_levels = question.scheme_mode == "levels"
    if not is_levels:
        meta_awards = [
            point.text for point in awarded if _is_examiner_meta_guidance(point.text)
        ]
        if meta_awards:
            raise ValueError(
                f"question {question.number} awarded marking points must state "
                "candidate answer content, not examiner guidance: "
                + "; ".join(meta_awards)
            )
    minimum_awarded = (
        1
        if question.kind == "multiple_choice"
        else (
            len(question.assessment_objectives) if is_levels else min(question.marks, 8)
        )
    )
    if len(awarded) < minimum_awarded:
        raise ValueError(
            f"question {question.number} needs at least "
            f"{minimum_awarded} distinct awarded marking points"
        )
    if len(points) - len(awarded) > 8:
        raise ValueError(f"question {question.number} has excessive zero-mark guidance")
    level_descriptors = [
        point for point in points if point.credit_type == "level" and point.marks == 0
    ]
    if is_levels and len(level_descriptors) < 3:
        raise ValueError(
            f"question {question.number} requires at least three zero-mark "
            "level descriptors"
        )
    if sum(point.marks for point in points) != question.marks:
        raise ValueError(
            f"question {question.number} marking points do not trace "
            f"{question.marks} marks"
        )
    normalised = {" ".join(point.text.casefold().split()) for point in points}
    if len(normalised) != len(points):
        raise ValueError(f"question {question.number} repeats a marking point")
    allocation: dict[str, int] = {}
    for point in points:
        if point.marks and not point.assessment_objective:
            raise ValueError(
                f"question {question.number} has an unclassified awarded mark"
            )
        if point.assessment_objective:
            allocation[point.assessment_objective] = (
                allocation.get(point.assessment_objective, 0) + point.marks
            )
    if allocation != question.assessment_objectives:
        raise ValueError(
            f"question {question.number} AO allocation {allocation} does not "
            f"match {question.assessment_objectives}"
        )


def _is_examiner_meta_guidance(text: str) -> bool:
    normalised = " ".join(text.casefold().split())
    if normalised in {"answer", "guidance", "indicative content", "mark scheme"}:
        return True
    return bool(
        re.match(
            r"^(?:award|credit|accept|allow|ignore|do not accept|examiner|marker|"
            r"indicative content|guidance|maximum)\b",
            normalised,
        )
    )


# Use blueprint AO totals when building levels-based schemes.
#
# Levels-based schemes separate AO accounting, band descriptors and indicative
# content. Local models often blur those roles, so retain their substantive
# material as guidance while creating neutral, exact AO allocation rows.
def _normalise_level_allocations(
    question: GeneratedQuestion,
    points: list[MarkSchemePoint],
) -> list[MarkSchemePoint]:

    if question.scheme_mode != "levels":
        return points

    objectives = list(question.assessment_objectives)
    substantive = [
        (index, point)
        for index, point in enumerate(points)
        if point.credit_type not in {"level", "guidance"}
    ]
    if not substantive:
        raise ValueError(
            f"question {question.number} has no substantive indicative content"
        )

    awarded = [
        MarkSchemePoint(
            text=_canonical_objective_allocation(objective),
            marks=question.assessment_objectives[objective],
            credit_type="point",
            assessment_objective=objective,
        )
        for objective in objectives
    ]
    level_entries = [
        point.model_copy(update={"marks": 0, "assessment_objective": None})
        for point in points
        if point.credit_type == "level"
    ]
    indicative_entries = [
        point.model_copy(
            update={
                "marks": 0,
                "credit_type": "guidance",
                "assessment_objective": None,
            }
        )
        for point in points
        if point.credit_type != "level"
    ]
    zero_mark_entries = level_entries + indicative_entries
    guidance_target = len(level_entries) if indicative_entries else 0
    updates: dict[str, list[str]] = {}
    if not any(point.alternatives or point.allow for point in zero_mark_entries):
        updates["alternatives"] = [
            "Accept any other well-supported route consistent with the source "
            "and the question."
        ]
    if not any(point.do_not_accept or point.ignore for point in zero_mark_entries):
        updates["do_not_accept"] = [
            "Do not award unsupported assertions or duplicate credit for the "
            "same developed point."
        ]
    if updates:
        zero_mark_entries[guidance_target] = zero_mark_entries[
            guidance_target
        ].model_copy(update=updates)
    zero_mark_entries = zero_mark_entries[:8]
    return awarded + zero_mark_entries


def _canonical_objective_allocation(objective: str) -> str:
    return (
        f"{objective} allocation within the levels grid; apply the band "
        "descriptors and indicative content below."
    )


def _review_batch(
    tasks: list[_Task],
    candidates: list[GeneratedQuestion],
    *,
    client: AssessmentLLMClient,
    subject: str,
    canonical_solutions: dict[str, CanonicalSolution | None] | None = None,
) -> dict[str, ReviewResult]:
    prompt = _review_prompt(
        tasks, candidates, subject=subject, canonical_solutions=canonical_solutions
    )
    raw = request_json(
        client,
        make_request(
            prompt,
            OutputContract(
                "batch_review", identifiers=tuple(task.id for task in tasks)
            ),
        ),
    )
    reviews = raw.get("reviews")
    if not isinstance(reviews, list):
        raise ValueError("second-pass review response has no reviews")
    by_id = {
        str(review.get("id")): review for review in reviews if isinstance(review, dict)
    }
    if set(by_id) != {task.id for task in tasks}:
        raise ValueError("second-pass review identifiers do not match the batch")
    results: dict[str, ReviewResult] = {}
    for task in tasks:
        review = by_id[task.id]
        result = ReviewResult.model_validate(
            {key: value for key, value in review.items() if key != "id"}
        )
        if result.issues and result.approved:
            result = result.model_copy(update={"approved": False})
        results[task.id] = result
    return results


def _bounded_text(value: Any, *, name: str, limit: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be text")
    compact = re.sub(r"\s+", " ", value).strip()
    if not compact or len(compact) > limit:
        raise ValueError(f"{name} is empty or exceeds {limit} characters")
    return compact


def _difficulty_candidate(
    task: _Task,
    candidate: GeneratedQuestion,
) -> object:
    projection = shared_difficulty_candidate_projection(
        question=candidate,
        option=task.option,
    )
    # Keep the full parent identity for conservative checkpoint invalidation;
    # only the model-visible view excludes unprinted planning material.
    return projection.model_copy(
        update={
            "review_content": {
                **projection.review_content,
                "parent_source": _task_source(task),
            }
        }
    )


def _difficulty_specification(task: _Task) -> dict[str, object]:
    return {
        "topic_id": str(task.topic.id),
        "topic_title": str(task.topic.title),
        "specification_points": [
            str(point) for point in getattr(task.topic, "points", [])
        ],
        "source": _task_source(task),
    }


# Remove model-added presentation labels that the renderer already owns.
def _clean_generated_prompt(
    value: str,
    *,
    question: GeneratedQuestion,
) -> str:

    labels = {
        question.number,
        question.number.lstrip("0") or "0",
    }
    label_pattern = "|".join(
        re.escape(label) for label in sorted(labels, key=len, reverse=True)
    )
    value = re.sub(
        rf"^(?:question\s+)?(?:{label_pattern})(?:\s*[:.)-]\s*|\s+)",
        "",
        value,
        count=1,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        r"^(?:question\s+)?\d{1,2}\s*[:.)-]\s+",
        "",
        value,
        count=1,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        rf"\s*[\[(]\s*{question.marks}\s+marks?\s*[\])]\s*$",
        "",
        value,
        count=1,
        flags=re.IGNORECASE,
    )
    if not numeric_tokens(question.prompt):
        value = re.sub(
            r"\b(?:the\s+)?(extract|figure|table|source|chart)\s+"
            r"\d+(?:\.\d+)*\b",
            lambda match: f"the {match.group(1).casefold()}",
            value,
            flags=re.IGNORECASE,
        )
    return value.strip()


def _contains_command_word(prompt: str, command_word: str) -> bool:
    aliases = {
        "analyse": {"analyse", "analyze"},
        "analyze": {"analyse", "analyze"},
    }
    expected = aliases.get(command_word.casefold(), {command_word.casefold()})
    words = set(re.findall(r"[a-z]+", prompt.casefold()))
    return bool(words & expected)


# Replace only a leading alternative exam command with the blueprint command.
def _normalise_command_word(prompt: str, command_word: str) -> str:

    if _contains_command_word(prompt, command_word):
        return prompt
    match = re.match(r"\s*([a-z]+)\b", prompt, flags=re.IGNORECASE)
    alternatives = {
        "analyse",
        "analyze",
        "assess",
        "calculate",
        "complete",
        "define",
        "describe",
        "discuss",
        "draw",
        "evaluate",
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
    }
    if match is None or match.group(1).casefold() not in alternatives:
        return prompt
    replacement = command_word.strip()
    if match.group(1)[:1].isupper():
        replacement = replacement[:1].upper() + replacement[1:]
    return f"{prompt[: match.start(1)]}{replacement}{prompt[match.end(1) :]}"


def _validate_prompt_length(question: GeneratedQuestion, prompt: str) -> None:
    raw_limit = question.authoring_context.get("max_prompt_words")
    if raw_limit is None:
        return
    if not isinstance(raw_limit, int) or raw_limit < 8:
        raise ValueError(f"question {question.number} has an invalid prompt word limit")
    word_count = len(re.findall(r"\b[\w'-]+\b", prompt))
    if word_count > raw_limit:
        raise ValueError(
            f"question {question.number} prompt has {word_count} words; "
            f"maximum is {raw_limit}"
        )
