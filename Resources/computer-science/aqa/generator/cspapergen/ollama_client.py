from __future__ import annotations

import json
import re
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Protocol

from Backend.Core.assessment_checkpoints import AssessmentCheckpointStore
from Backend.Core.assessment_contracts import EvidenceRecord
from Backend.Core.assessment_objectives import objective_policy_for
from Backend.Core.assessment_quality import numeric_tokens
from Backend.Core.computer_science_authoring import (
    aqa_cs_difficulty_candidate,
    aqa_cs_solver_item,
    authoring_route,
    question_content_sha256,
    reviewed_question_metadata,
    validate_question_review,
)
from Backend.Core.independent_solver import (
    IndependentSolver,
    SQLProgramAttemptAudit,
    require_solution_matches_scheme,
)
from Backend.Core.model_review import (
    assert_materially_new,
    require_difficulty_review,
    require_independent_review,
)
from Backend.Core.open_credit import review_open_credit
from Backend.Core.providers import OllamaClient
from Backend.Core.reference_demand import (
    assessment_objectives_for_item,
    build_item_demand_target,
    profile_for,
)
from Backend.Core.subjects.sql_contracts import (
    SQL_VALIDATION_VERSION,
    SQL_VERIFIED_SCOPE,
    SQLSourceContract,
    SQLValidationFinding,
    SQLValidationResult,
    render_sql_schema,
    selected_sql_answer_contract,
    sql_source_intent_sha256,
    validate_sql_response,
)
from cspapergen.models import (
    PaperBlueprint,
    Question,
    QuestionPart,
    Syllabus,
)
from cspapergen.notes import note_context_for_topic
from cspapergen.render_pdf import candidate_stimulus_data


class JSONGenerationClient(Protocol):
    def generate_json(self, prompt: str) -> dict[str, object]: ...


def improve_questions_with_ollama(
    client: JSONGenerationClient,
    blueprint: PaperBlueprint,
    syllabus: Syllabus,
    progress: Callable[[str], None] | None = None,
    checkpoint_store: AssessmentCheckpointStore | None = None,
) -> PaperBlueprint:
    emit = progress or (lambda _message: None)
    total = len(blueprint.questions)
    improved = list(blueprint.questions)
    supports_parallel = getattr(
        client,
        "supports_parallel_generation",
        not isinstance(client, OllamaClient),
    )
    max_workers = max(1, min(total, 4)) if supports_parallel else 1

    def _improve(index: int, question: Question) -> tuple[Question, str]:
        topic = syllabus.get_topic(question.topic_id)
        display_index = index + 1
        checkpoint_key = f"question-{question.number}"
        if checkpoint_store is not None:
            stored = checkpoint_store.load_payload(checkpoint_key)
            if stored is not None:
                try:
                    candidate = Question.model_validate(stored)
                    validate_question_review(candidate.model_dump(mode="json"), question.model_dump(mode="json"), required=True)
                    _validate_ai_question(question, candidate)
                except (ValueError, TypeError):
                    checkpoint_store.discard_item(checkpoint_key)
                else:
                    return (
                        candidate,
                        (
                            f"Resumed reviewed question {display_index}/{total}: "
                            f"0 {question.number:02d}"
                        ),
                    )
        if _uses_review_only_generation(question):
            emit(f"Reviewing fixed question {display_index}/{total}: 0 {question.number:02d} ({topic.title})")
            review = require_independent_review(
                client,
                item_id=f"question-{question.number}",
                subject="AQA A-level Computer Science",
                blueprint=question,
                candidate=question,
                specification=topic,
            )
            candidate = question.model_copy(update=reviewed_question_metadata(
                question.model_dump(mode="json"), question.model_dump(mode="json"), review))
            validate_question_review(candidate.model_dump(mode="json"), question.model_dump(mode="json"), required=True)
            if checkpoint_store is not None:
                checkpoint_store.save_payload(
                    checkpoint_key,
                    candidate.model_dump(mode="json"),
                )
            return (
                candidate,
                (
                    f"Reviewed fixed question {display_index}/{total}: "
                    f"0 {question.number:02d}"
                ),
            )
        emit(f"Generating question {display_index}/{total}: 0 {question.number:02d} ({topic.title})")
        base_prompt = _prompt(
            question,
            topic.title,
            note_context_for_topic(topic.id, topic.title),
            blueprint,
        )
        failure = ""
        for attempt in range(1, 4):
            retry_prompt = (
                base_prompt
                if not failure
                else f"{base_prompt}\nPrevious attempt rejected: {failure}\nCorrect every issue in the next response."
            )
            payload = client.generate_json(retry_prompt)
            try:
                candidate = _merge_question(question, payload)
                _validate_ai_question(question, candidate)
                review = require_independent_review(
                    client,
                    item_id=f"question-{question.number}",
                    subject="AQA A-level Computer Science",
                    blueprint=question,
                    candidate=candidate,
                    specification=topic,
                )
                candidate = candidate.model_copy(update=reviewed_question_metadata(
                    question.model_dump(mode="json"), candidate.model_dump(mode="json"), review))
                validate_question_review(candidate.model_dump(mode="json"), question.model_dump(mode="json"), required=True)
                break
            except ValueError as error:
                failure = str(error)
                if attempt == 3:
                    raise ValueError(
                        f"question-{question.number} failed after 3 reviewed attempts: {failure}"
                    ) from error
        if checkpoint_store is not None:
            checkpoint_store.save_payload(
                checkpoint_key,
                candidate.model_dump(mode="json"),
            )
        return (
            candidate,
            (
                f"Generated and reviewed question {display_index}/{total}: "
                f"0 {question.number:02d}"
            ),
        )

    if max_workers == 1:
        for index, question in enumerate(blueprint.questions):
            improved[index], message = _improve(index, question)
            emit(message)
        return blueprint.model_copy(update={"questions": improved})

    completed_messages: dict[int, str] = {}
    next_message = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_improve, index, question): index
            for index, question in enumerate(blueprint.questions)
        }
        for future in as_completed(futures):
            index = futures[future]
            improved[index], completed_messages[index] = future.result()
            while next_message in completed_messages:
                emit(completed_messages.pop(next_message))
                next_message += 1
    return blueprint.model_copy(update={"questions": improved})


def review_blueprint_difficulty(
    client: JSONGenerationClient,
    blueprint: PaperBlueprint,
    syllabus: Syllabus,
    progress: Callable[[str], None] | None = None,
) -> PaperBlueprint:
    emit = progress or (lambda _message: None)
    paper_id = (
        f"bank-{blueprint.focus_topic_id}"
        if blueprint.assessment_kind == "question-bank"
        else blueprint.paper_number
    )
    profile = profile_for("aqa/computer-science", paper_id)
    item_count = sum(len(question.parts) for question in blueprint.questions)
    item_index = 0
    reviewed_questions: list[Question] = []
    for question in blueprint.questions:
        topic = syllabus.get_topic(question.topic_id)
        reviewed_parts: list[QuestionPart] = []
        for part in question.parts:
            item_index += 1
            item = _part_demand_item(question, part)
            emit(
                f"Checking reference demand {item_index}/{item_count}: "
                f"0 {question.number:02d}({part.label})"
            )
            projection = _part_solver_projection(question, part)
            solver_item = projection.item
            solution = _solve_part_with_sql_validation(client, projection)
            credit_review = review_open_credit(client, solver_item, solution) if part.open_credit_contract else {}
            require_solution_matches_scheme(
                solution,
                {"marks": part.marks, "mark_scheme": [*part.marking.points, *part.marking.levels],
                 "assessment_objectives": part.marking.assessment_objectives,
                 "alternatives": part.marking.accept,
                 "closed_answers": part.marking.closed_answers,
                 "credit_review_item": solver_item, "open_credit_review": credit_review},
                expected_choice=(next((o.text for o in part.options if o.label == part.correct_option), "")
                                 if part.options else None),
            )
            evidence = require_difficulty_review(
                client,
                item_id=f"question-{question.number}-{part.label}",
                subject="AQA A-level Computer Science",
                target=build_item_demand_target(item, profile),
                candidate=_difficulty_candidate(question, part),
                specification=topic,
                canonical_solution=_difficulty_solution(solution),
            )
            reviewed_parts.append(
                part.model_copy(
                    update={"difficulty_evidence": evidence.model_dump(mode="json"), "open_credit_review": credit_review}
                )
            )
        reviewed_questions.append(question.model_copy(update={"parts": reviewed_parts}))
    return blueprint.model_copy(update={"questions": reviewed_questions})


def _difficulty_candidate(question: Question, part: QuestionPart) -> object:
    return aqa_cs_difficulty_candidate(
        question.model_dump(mode="json"),
        part.model_dump(mode="json"),
    )


def _difficulty_solution(solution: object) -> dict[str, object]:
    """Keep independent work for demand review, never its private CPU contract."""
    public_solution = solution.model_dump(mode="json")
    public_solution.pop("open_credit_contract", None)
    public_solution.pop("program_first_failure", None)
    return public_solution


def _prompt(
    question: Question,
    topic_title: str,
    notes: str,
    blueprint: PaperBlueprint,
) -> str:
    parts = "\n".join(f"- Part {part.label}: {part.marks} marks, {part.prompt}" for part in question.parts)
    paper_id = (
        f"bank-{blueprint.focus_topic_id}"
        if blueprint.assessment_kind == "question-bank"
        else blueprint.paper_number
    )
    profile = profile_for("aqa/computer-science", paper_id)
    demand_targets = [
        build_item_demand_target(
            _part_demand_item(question, part),
            profile,
        ).model_dump(mode="json")
        for part in question.parts
    ]
    objective_guidance = objective_policy_for("computer science").guidance() + " Computer Science has no AO4."
    if _uses_scenario_only_generation(question):
        stem_numbers = ", ".join(numeric_tokens(question.stem)) or "none"
        scenario_terms = ", ".join(_required_scenario_terms(question)) or "none"
        return f"""You are writing an unofficial A-level Computer Science {blueprint.paper_code} Paper {blueprint.paper_number}.

Use only this syllabus topic: {question.topic_id} {topic_title}
Immutable assessment focus: {question.title} ({question.style_id}). Do not substitute another subtopic, process or technology.
Immutable reference-demand targets: {json.dumps(demand_targets, ensure_ascii=False)}
{objective_guidance}

Create a concise, materially new fictional scenario stem for the immutable multipart task below. The stem must establish the same technical setting without copying a complete sentence from the draft. Preserve these numeric tokens from the draft stem exactly: {stem_numbers}. Introduce no other numeric values. Do not repeat, rewrite or answer the parts. Do not add exam-board branding.
Preserve these marking-coupled scenario terms exactly: {scenario_terms}.

Draft stem: {question.stem}
Immutable parts for context only:
{parts}

Return JSON only:
{{
  "stem": "string",
  "parts": []
}}
"""
    return f"""You are writing an unofficial A-level Computer Science {blueprint.paper_code} Paper {blueprint.paper_number}.

Use only this syllabus topic: {question.topic_id} {topic_title}
Immutable assessment focus: {question.title} ({question.style_id}). Do not substitute another subtopic, process or technology.
Immutable reference-demand targets: {json.dumps(demand_targets, ensure_ascii=False)}
{objective_guidance}
Revision-note context:
{notes}

Create a genuinely new independent question in concise UK exam style. Do not copy, reconstruct or closely paraphrase a live, historic or draft paper question. Replace the stem and every complete part-prompt sentence with materially new wording and a new fictional scenario. The verified marking guidance, marks, part labels, answer units, stimulus data, numeric values and correct answers are immutable. Do not return or rewrite marking guidance. Do not add exam-board branding.

Question stem: {question.stem}
Parts:
{parts}

VERIFIED MARKING IS IMMUTABLE. Return JSON only:
{{
  "stem": "string",
  "parts": [
    {{
      "label": "1",
      "prompt": "string"
    }}
  ]
}}
"""


def _part_demand_item(
    question: Question,
    part: QuestionPart,
) -> dict[str, object]:
    objectives = assessment_objectives_for_item(part.model_dump(mode="json"))
    stimulus: list[str] = []
    if question.stimulus is not None:
        stimulus.extend(question.stimulus.lines)
        stimulus.extend(cell for row in question.stimulus.rows for cell in row)
        if question.stimulus.code:
            stimulus.append(question.stimulus.code)
    prompt = str(part.prompt)
    return {
        "id": f"question-{question.number}-{part.label}",
        "marks": int(part.marks),
        "kind": question.style_id,
        "command_word": prompt.split(maxsplit=1)[0].strip(".,:;!?()[]{}"),
        "prompt": prompt,
        "assessment_objectives": objectives,
        "expected_minutes": part.expected_minutes,
        "task_operation": part.task_operation,
        "context": [question.stem, *stimulus],
    }


def _part_solver_item(question: Question, part: QuestionPart) -> dict[str, object]:
    return _part_solver_projection(question, part).item


@dataclass(frozen=True)
class _SolverProjection:
    item: dict[str, object]
    evidence: tuple[EvidenceRecord, ...]
    sql_contract: SQLSourceContract | None = None
    sql_intent_id: str = ""


def _part_solver_projection(
    question: Question, part: QuestionPart
) -> _SolverProjection:
    stimulus = candidate_stimulus_data(question.stimulus)
    item = aqa_cs_solver_item(
        question.model_dump(mode="json"), part.model_dump(mode="json"), stimulus
    )
    if question.stimulus is None or question.stimulus.sql_contract is None:
        if part.sql_intent_id:
            raise ValueError("SQL part has no candidate-visible public SQL contract")
        return _SolverProjection(item=item, evidence=())
    contract = question.stimulus.sql_contract
    evidence = (
        EvidenceRecord(
            id=contract.source_id,
            text=json.dumps(stimulus, ensure_ascii=False, sort_keys=True),
        ),
    )
    if json.loads(evidence[0].text) != item.get("stimulus"):
        raise ValueError("public SQL evidence differs from the solver stimulus")
    if not part.sql_intent_id:
        return _SolverProjection(item=item, evidence=evidence)
    if question.style_id != "sql_normalisation":
        raise ValueError("SQL part has no candidate-visible public SQL contract")
    _validate_sql_solver_projection(item, evidence, contract, part.sql_intent_id)
    return _SolverProjection(
        item=item,
        evidence=evidence,
        sql_contract=contract,
        sql_intent_id=part.sql_intent_id,
    )


def _validate_sql_solver_projection(
    item: dict[str, object],
    evidence: tuple[EvidenceRecord, ...],
    contract: SQLSourceContract,
    intent_id: str,
) -> None:
    if len(evidence) != 1 or evidence[0].id != contract.source_id:
        raise ValueError("SQL solver requires one exact public SQL source")
    try:
        source = json.loads(evidence[0].text)
    except json.JSONDecodeError as error:
        raise ValueError("public SQL evidence is not valid JSON") from error
    if source != item.get("stimulus"):
        raise ValueError("public SQL evidence differs from the solver stimulus")
    if source.get("source_id") != contract.source_id:
        raise ValueError("public SQL source identity differs from its contract")
    if source.get("sql_contract") != contract.model_dump(mode="json"):
        raise ValueError("public SQL source differs from its typed contract")
    if source.get("code") != render_sql_schema(contract):
        raise ValueError("public SQL rendered schema differs from its typed contract")
    context = item.get("authoring_context")
    if not isinstance(context, dict):
        raise ValueError("SQL solver item has no authoring context")
    digest = sql_source_intent_sha256(contract, intent_id)
    if context.get("sql_source_intent_sha256") != digest:
        raise ValueError("public SQL source/intent digest is stale")
    public_contract = context.get("sql_answer_contract")
    if public_contract != selected_sql_answer_contract(contract, intent_id):
        raise ValueError("SQL solver item has no selected public intent")
    forbidden = {"marking", "mark_scheme", "worked_query", "canonical_solution"}
    if forbidden & set(public_contract):
        raise ValueError("public SQL solver contract contains private answer material")


def _solve_part_with_sql_validation(
    client: JSONGenerationClient, projection: _SolverProjection
):
    solver = IndependentSolver(client)
    first = solver.solve(projection.item, projection.evidence)
    if projection.sql_contract is None:
        return first
    first_validation = _sql_solution_validation(first, projection)
    if first_validation.passed:
        return _verified_sql_solution(first, projection, None)
    first_audit = _sql_attempt_audit(first, first_validation)
    structured = [
        finding.model_dump(mode="json")
        for finding in first_validation.findings
    ]
    replacement = solver.solve(
        projection.item,
        projection.evidence,
        correction_findings=structured,
    )
    replacement_validation = _sql_solution_validation(replacement, projection)
    if not replacement_validation.passed:
        raise SQLProgramValidationError(
            first_audit,
            _sql_attempt_audit(replacement, replacement_validation),
        )
    return _verified_sql_solution(replacement, projection, first_audit)


def _sql_solution_validation(
    solution, projection: _SolverProjection
) -> SQLValidationResult:
    assert projection.sql_contract is not None
    result = validate_sql_response(
        solution.answer,
        solution.mark_points,
        projection.sql_contract,
        projection.sql_intent_id,
    )
    findings = list(result.findings)
    if solution.evidence_ids != [projection.sql_contract.source_id]:
        findings.append(SQLValidationFinding(
            code="source-citation",
            message="The SQL response must cite the one supplied public schema source.",
            location="evidence_ids",
        ))
    return result.model_copy(update={"passed": not findings, "findings": findings})


def _sql_attempt_audit(
    solution, validation_result: SQLValidationResult
) -> SQLProgramAttemptAudit:
    return SQLProgramAttemptAudit(
        answer=solution.answer,
        mark_points=list(solution.mark_points),
        evidence_ids=list(solution.evidence_ids),
        validation_result=validation_result,
    )


class SQLProgramValidationError(ValueError):
    """A bounded SQL correction failed, retaining both private attempts."""

    def __init__(
        self,
        first_attempt: SQLProgramAttemptAudit,
        replacement_attempt: SQLProgramAttemptAudit,
    ) -> None:
        self.first_attempt = first_attempt
        self.replacement_attempt = replacement_attempt
        super().__init__(
            "failed bounded SQL verification after one correction: first="
            + first_attempt.model_dump_json()
            + "; replacement="
            + replacement_attempt.model_dump_json()
        )


def _verified_sql_solution(
    solution,
    projection: _SolverProjection,
    first_failure: SQLProgramAttemptAudit | None,
):
    assert projection.sql_contract is not None
    digest = sql_source_intent_sha256(
        projection.sql_contract, projection.sql_intent_id
    )
    return solution.model_copy(update={
        "verified_scope": SQL_VERIFIED_SCOPE,
        "program_validation_version": SQL_VALIDATION_VERSION,
        "program_validation_scope": SQL_VERIFIED_SCOPE,
        "source_intent_sha256": digest,
        "program_first_failure": first_failure,
    })


def _uses_scenario_only_generation(question: Question) -> bool:
    return authoring_route(question.model_dump(mode="json")) == "scenario-only"


def _uses_review_only_generation(question: Question) -> bool:
    """Keep all source-coupled tasks immutable, without claiming authorship."""
    return authoring_route(question.model_dump(mode="json")) == "reviewed-fixed"


def _merge_question(question: Question, payload: dict[str, object]) -> Question:
    stem = _clean(str(payload.get("stem") or question.stem))
    if question.stimulus is not None:
        stem = question.stem
    if not _uses_scenario_only_generation(question) and numeric_tokens(stem) != numeric_tokens(question.stem):
        stem = question.stem
    raw_parts = payload.get("parts")
    parts = question.parts
    if isinstance(raw_parts, list):
        by_label = {str(item.get("label")): item for item in raw_parts if isinstance(item, dict)}
        merged = []
        for part in question.parts:
            raw = by_label.get(part.label, {})
            prompt = _clean(str(raw.get("prompt") or part.prompt)) if isinstance(raw, dict) else part.prompt
            if question.stimulus is not None:
                prompt = part.prompt
            if numeric_tokens(prompt) != numeric_tokens(part.prompt):
                prompt = part.prompt
            points = _text_list(raw.get("marking_points") if isinstance(raw, dict) else None, part.marking.points)
            required_points = min(part.marks, 3)
            seen = {point.casefold() for point in points}
            for fallback in part.marking.points:
                if len(seen) >= required_points:
                    break
                if fallback.casefold() not in seen:
                    points.append(fallback)
                    seen.add(fallback.casefold())
            accept = _text_list(raw.get("accept") if isinstance(raw, dict) else None, part.marking.accept)
            reject = _text_list(raw.get("reject") if isinstance(raw, dict) else None, part.marking.reject)
            marking = part.marking.model_copy(
                deep=True, update={"points": points, "accept": accept, "reject": reject}
            )
            merged.append(part.model_copy(update={"prompt": prompt, "marking": marking}))
        parts = merged
    return question.model_copy(update={"stem": stem, "parts": parts})


def _validate_ai_question(original: Question, candidate: Question) -> None:
    if _uses_review_only_generation(original):
        if question_content_sha256(original.model_dump(mode="json")) != question_content_sha256(candidate.model_dump(mode="json")):
            raise ValueError("immutable source-coupled question was changed")
        return
    original_text = " ".join(
        [original.stem, *(part.prompt for part in original.parts)]
    )
    candidate_text = " ".join(
        [candidate.stem, *(part.prompt for part in candidate.parts)]
    )
    missing_scenario_terms = [
        term
        for term in _required_scenario_terms(original)
        if term.casefold() not in candidate.stem.casefold()
    ]
    if missing_scenario_terms:
        raise ValueError(
            "question changed a required scenario term: "
            + ", ".join(missing_scenario_terms)
        )
    constrained_multipart = len(original.parts) >= 3 and bool(
        numeric_tokens(original_text)
    )
    if constrained_multipart and original.stem.strip():
        assert_materially_new(
            original.stem,
            candidate.stem,
            item_id=f"question-{original.number}-scenario",
            similarity_limit=0.9,
            preserve_numbers=False,
        )
    assert_materially_new(
        original_text,
        candidate_text,
        item_id=f"question-{original.number}",
        similarity_limit=0.98 if constrained_multipart else 0.9,
    )
    if len(candidate.parts) != len(original.parts):
        raise ValueError(f"question-{original.number} changed its part count")
    for original_part, candidate_part in zip(
        original.parts, candidate.parts, strict=True
    ):
        immutable = (
            original_part.label,
            original_part.marks,
            original_part.answer_lines,
            original_part.answer_unit,
            original_part.options,
            original_part.correct_option,
            original_part.marking.ao,
            original_part.assessment_objectives,
            original_part.expected_minutes,
            original_part.task_operation,
            original_part.response_slots,
            original_part.marking.closed_answers,
            original_part.open_credit_contract,
            original_part.marking.credit_allocations,
        )
        actual = (
            candidate_part.label,
            candidate_part.marks,
            candidate_part.answer_lines,
            candidate_part.answer_unit,
            candidate_part.options,
            candidate_part.correct_option,
            candidate_part.marking.ao,
            candidate_part.assessment_objectives,
            candidate_part.expected_minutes,
            candidate_part.task_operation,
            candidate_part.response_slots,
            candidate_part.marking.closed_answers,
            candidate_part.open_credit_contract,
            candidate_part.marking.credit_allocations,
        )
        if actual != immutable:
            raise ValueError(
                f"question-{original.number}-{original_part.label} changed "
                "an immutable assessment field"
            )
        points = [
            point.strip()
            for point in candidate_part.marking.points
            if point.strip()
        ]
        if len(set(point.casefold() for point in points)) < min(
            candidate_part.marks, 3
        ):
            raise ValueError(
                f"question-{original.number}-{original_part.label} has "
                "insufficient distinct marking points"
            )


def _text_list(raw: object, fallback: list[str]) -> list[str]:
    if not isinstance(raw, list):
        return fallback
    values = [str(item).strip() for item in raw if str(item).strip()]
    return values or fallback


def _required_scenario_terms(question: Question) -> list[str]:
    if question.style_id == "database_extended":
        return [
            "CLIENT",
            "ClientID",
            "REGISTRATION",
            "RegistrationID",
            "BookingDate",
            "WORKSHOP",
            "WorkshopID",
            "Places",
        ]
    if question.style_id == "compression_short" and len(question.parts) >= 2:
        prefix = "Explain why lossless compression may be required for "
        prompt = question.parts[1].prompt
        if not prompt.startswith(prefix):
            raise ValueError("compression question has no marking-coupled data type")
        term = prompt.removeprefix(prefix).rstrip(". ")
        if not term:
            raise ValueError("compression question has an empty data type")
        return [term]
    return []


def _clean(text: str) -> str:
    text = re.sub(r"\[\s*\d+\s*marks?\s*\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\(\s*\d+\s*marks?\s*\)", "", text, flags=re.IGNORECASE)
    text = text.replace("$", "")
    text = re.sub(r"\\(?:texttt|mathrm|mathbf)\{([^{}]+)\}", r"\1", text)
    text = text.replace(r"\(", "").replace(r"\)", "")
    return " ".join(text.split())
