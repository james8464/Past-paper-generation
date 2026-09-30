# Selected-response label integrity implementation plan

> **For agentic workers:** Use superpowers:executing-plans for inline implementation and one fresh whole-branch review. Steps use checkbox syntax for tracking.

**Goal:** Repair the reproduced Economics Paper 3 public-label mismatch without freezing original AI wording or weakening review.

**Architecture:** Keep the existing typed opportunity-cost projection and its immutable choices. Declare its product labels to the writer and validate their presence in the candidate stem before deterministic credit can be returned. Generation, checkpoint replay and independent solving continue through existing validation boundaries.

**Tech Stack:** Python, Pydantic, pytest, Graphify, GitHub protected PR checks.

**Spec:** `docs/quality/examiner-readiness-standard.md`; issue #13 and preserved baseline failure `economics_aqa:3`, seed26092844.

## Global constraints

- Original practice questions; never claim teacher/moderator/board approval.
- Do not change the source used by live controller16114 or run a second model job.
- Do not weaken correctness, originality, difficulty, printed-credit or reference gates.
- Keep all other outstanding issues open. This repair does not complete examiner readiness.
- Use the isolated `examiner-readiness` branch; defer integration into main until the stable batch ends.

## Review focus

- A renamed, absent or partial label must not pass because arithmetic is correct.
- Case and ordinary whitespace changes must not invalidate the same entity name.
- Wrong distractors and keys must still fail existing deterministic checks.
- The typed projector must pass its public prompt to the solver, not rely on hidden data.
- Model repairs and checkpoint replay must retain the required-label contract.

### Task 1: Bind opportunity-cost product labels

**Files:**
- Modify: `Backend/Core/subjects/selected_response.py`
- Modify: `Backend/Core/ai_assessment.py`
- Modify: `Resources/economics/aqa/generator/aqaecongen/generator.py`
- Test: `Resources/economics/aqa/generator/tests/test_aqa_economics.py`
- Test: `tests/test_shared_numeric_integrity.py` if shared parser fixtures are needed.
- Test: `tests/test_task_source_demand.py` (complete public prompt fixtures).

**Interfaces:** `project_applied_mcq(source)` continues returning `AppliedMCQProjection`; its authoring context declares `required_prompt_terms` for product X and product Y. `solve_selected_response(item)` keeps its return schema and raises ValueError when an opportunity-cost stem fails public-label validation. No API keys or model calls are involved.

- [x] Add a negative test using paper3 seed26092844: rename X/Y to A/B without
  changing choices; deterministic solving must raise ValueError. Add absent,
  substring-only and case/whitespace variants; unchanged valid answer is
  `12 units of product Y`.
- [x] Run the focused tests and observe the expected missing-validation failures.
- [x] Pass the projected prompt into the source solver, declare required labels
  to the AI author, and validate whole labels case-insensitively with normalized
  whitespace before calculating opportunity cost. Do not normalize A/B to X/Y
  or alter user-visible question meaning after review.
- [x] Verify the real parser rejects a generated stem that omits required labels;
  retain its existing originality and numeric checks. Check replay validation.
- [x] Run focused generator/shared-numeric tests, then the full pytest suite.
  Expected: all tests pass, with any environment-only skips explicitly recorded.
- [x] Update Graphify and repository inventory; run lint and inventory validation;
  obtain fresh code review, repair findings with regressions and commit.
- [ ] Publish a PR with exact validation evidence, keep runtime integration
  blocked while the stable matrix runs, and record the next repair handoff.

## Subsequent bounded work (separate implementation tasks)

Review added two boundary regressions: substring-only labels must fail in the
real parser before optional model review, and renamed labels must fail actual
checkpoint replay, not merely a separately invoked independent solver. Both
boundaries now invoke deterministic public selected-response validation. Locked
marking changes are rejected before public solving, preserving immutable-field
diagnostics. Existing numeric policy tests retain their original assertions.

Final local verification: 2087 passed, 2 skipped (optional local CS notes absent),
5 existing SWIG deprecation warnings, 96.77 seconds. Focused suite: 219 passed;
checkpoint suite: 8 passed. Ruff and whitespace checks passed. Graphify AST:
6843 nodes/19194 edges; inventory: 506 tracked files, no forbidden/unclassified
paths. Native CI and final-source live/manual qualification remain separate.

Limit: label presence does not establish complete entity/quantity association
through arbitrary prose. Retaining X/Y elsewhere while changing another entity
reference still needs the broader source/task coherence work in issue #13.

Continue #12 typed Accounting cases and content-preserving natural schemes;
#13 board/task-specific level policies and substantive credit, shared causal
diagram intent and coherent economic cases; audit all remaining routes and the
teacher's CS checklist. Follow the standard above for final multi-seed validation
and actual reviewer handoff. Do not label this first fix project completion.
