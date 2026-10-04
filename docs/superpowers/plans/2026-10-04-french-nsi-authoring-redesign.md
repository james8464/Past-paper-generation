# French NSI Authoring Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the French NSI route generate coherent, original, source-informed 2027 written-practice papers without allowing mislabeled or unlinked questions to pass.

**Architecture:** A deterministic, versioned exercise archetype owns the question sequence and immutable assessment metadata. AI supplies contexts and question content; an independent question-level review must establish that each item genuinely assesses its intended capability. Exact figure-link repair and targeted retry retain raw provenance.

**Tech Stack:** Python 3, Pydantic, SQLite FTS, Ollama JSON-schema transport, pytest, Ruff, existing SwiftUI bridge and PDF renderer.

**Spec:** `docs/superpowers/specs/2026-10-04-french-nsi-authoring-redesign.md`

## Global Constraints

- Preserve all UK route IDs and behaviour, recorded French v4/v5/v6 package readers, and ignored failed-attempt evidence.
- Exactly three independent 210-minute written exercises, 18 technical points plus a distinct two-point indicative language component; no practical component.
- French-only compatible reference retrieval, holdout exclusion, independent branding, no silent cloud fallback or arbitrary generated-code execution.
- No automated result is teacher, examiner or empirical learner approval.
- Keep Git and Graphify current; use protected PR checks and small reviewed merges.

## Review Focus

- A model echoes the correct programme code but asks about another concept: reject at item-level alignment review, not only metadata comparison.
- An exact figure ID appears in a prompt with empty `material_ids`: bind only the unique exact ID and record the binding; reject vague or conflicting references.
- A repaired question changes an earlier answer or diagram dependency: rerun whole-exercise affected checks and invalidate old review evidence.
- A cancelled or source-changing resume: preserve its checkpoint and refuse publication under the new identity.
- An older French package lacks new authoring evidence: validate it only through its pinned historical reader, never upgrade its claimed quality.

---

### Task 1: Coherent archetypes and source-backed question intents

**Files:** Modify `Backend/Core/france/pipeline.py`; create `Backend/Core/france/archetypes.py`; modify `tests/test_nsi_pipeline.py`; update `docs/quality/french-nsi-evaluation.md`.

**Interfaces:** `archetype_for_seed(seed: int) -> tuple[ExerciseArchetype, ...]`; `QuestionIntent` contains `required_curriculum_code`, `goal`, `response_form`, and `part_id`. `_tasks_for_seed` combines its ordered intents with the existing exact point/time allocation. Do not derive an objective by cycling over a code tuple.

- [ ] Write failing tests for seed 270100 and neighbouring seeds: each six-question sequence is grouped by its scenario parts; all required codes are known Terminale objectives; 18 technical points and 210 minutes remain exact; distinct papers vary contexts without scrambling intent order.
- [ ] Run the focused tests and record their expected failure against cyclic assignment.
- [ ] Implement versioned archetypes and add each question intent/response form to the French generation prompt. Preserve the historical prompt-version readers; bump the current version.
- [ ] Run the focused tests, French suite, Ruff and `graphify update .`; commit on a temporary review branch.

### Task 2: Exact material binding and immutable plan assembly

**Files:** Modify `Backend/Core/france/nsi.py` and `Backend/Core/france/pipeline.py`; modify `tests/test_nsi_pipeline.py` and `tests/test_nsi_assessment.py`.

**Interfaces:** `bind_explicit_material_ids(raw: dict) -> tuple[dict, list[dict]]` accepts a missing **or empty** `material_ids` only when one or more exact, unique declared IDs occur in that question's prompt. `assemble_planned_question(plan: dict, authored: dict) -> NSIQuestion` attaches immutable metadata and records original authored fields; it must not substitute a curriculum code without subsequent content alignment evidence.

- [ ] Write failing tests for empty-list exact-ID recovery, vague/unknown/conflicting IDs, raw immutability, evidence-hash tampering and v4/v5/v6 compatibility.
- [ ] Run tests red, implement exact-ID binding and evidence replay, run green.
- [ ] Write failing tests showing a content draft cannot set a different point value, ID or operation in the assembled package and cannot be accepted solely because plan metadata was injected.
- [ ] Implement explicit raw/assembled provenance and fail-closed validation; run full pytest, Ruff and Graphify; commit.

### Task 3: Per-question alignment and bounded targeted repair

**Files:** Modify `Backend/Core/france/pipeline.py`, `Backend/Core/france/provider.py`, `Backend/Core/france/nsi.py`; create `Backend/Core/france/question_review.py`; modify `tests/test_french_provider.py` and `tests/test_nsi_pipeline.py`.

**Interfaces:** `review_question_alignment(question: NSIQuestion, intent: QuestionIntent, client) -> AlignmentEvidence` returns `aligned`, `rationale`, `objective_code` and `issues`; missing, mismatched or unresolved evidence rejects the item. `repair_question(...)` replaces only a failed content draft under the same plan/scenario, with at most two repairs and a recorded raw attempt list.

- [ ] Write failing tests for a correct metadata label on semantically wrong content, missing reviewer item, reviewer disagreement, and unsupported deterministic contracts.
- [ ] Implement strict item-level review schema and independent prompt; do not reuse the author's proposed solution as reviewer evidence. Run red-green tests.
- [ ] Write failing tests for one failed item among accepted peers, dependency invalidation, cancellation and resume identity.
- [ ] Implement targeted repair and full affected rechecks without weakening originality, deterministic, timing, mark or reference gates. Run full pytest, Ruff, Graphify; commit.

### Task 4: Live qualification and publication decision

**Files:** Update `docs/quality/french-nsi-evaluation.md`, `docs/competition/occitanie-2026/claims-register.md`, `docs/competition/occitanie-2026/README.md`, and GitHub issue #16. Do not edit historical artifacts.

**Interfaces:** Use existing `tools/french_nsi_benchmark.py` with fresh output directories, fixed seeds, model digest, reference-index hash and implementation identity. No new model job while one is active.

- [ ] Review changed code independently; run full backend tests, Ruff, Swift tests and macOS release build through protected checks, then merge without bypass.
- [ ] Run one new source-pinned paper diagnostic; inspect every failure or accepted artifact. A failed run returns to the relevant task with a regression test, not a softened gate.
- [ ] Only after stable structural acceptance, run the 30-task candidate-model comparison and ten complete papers; preserve first-pass, repaired and failed counts.
- [ ] Compare all accepted PDF pages against relevant official references, record exact differences, and keep teacher/learner/hardware gates open until evidenced.
