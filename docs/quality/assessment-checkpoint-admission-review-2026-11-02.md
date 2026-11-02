# Assessment checkpoint admission review, 2 November 2026

## Reproduced defect

A full-file review of `Backend/Core/ai_assessment.py` at `8975cf8bd91a0cf22957e8b7efc9d0ef561dcfe1` found that individually accepted batches became durable before cross-batch distinctness was checked. A fake typed provider and real, owned checkpoint store reproduced the failure in both sequential and parallel execution. Two one-item batches returned identical stems and positive schema-valid reviews. The first run made four fake requests and correctly refused the duplicate paper, but cached both items. A same-identity retry made zero requests and refused again with identical checkpoint bytes. This is an acceptance-ordering defect, separate from a model producing duplicate wording.

Private reproduction evidence remains in the documentation worktree at `tmp/nov2-ai-assessment-checkpoint-controls.log` and its owned `tmp/nov2-ai-assessment-checkpoint-controls/` directories. The initial parallel-only probe remains separately retained. No user cache, network, model inference, paid credits or rendered paper was involved.

## Bounded repair

Sequential and parallel batches now stage their checkpoint changes. One caller-owned admission function checks the cumulative set of prompts, keyed by task identity, before committing accepted work or reporting its accepted count. The final paper validation and distinctness checks remain in place, with unchanged thresholds and contracts.

Sequential generation keeps its existing per-item durability. An optional accepted-item callback receives the actual validated, resumed or trusted candidate, rather than inferring correctness from progress messages or rereading an unrelated cached payload. It admits each item before committing just that staged entry. A later failure or cancellation does not discard the valid prefix. The small `commit_item` helper removes an entry only after its own persistence succeeds; the existing whole-batch `commit` behavior is unchanged. Parallel workers do not receive this acceptance callback and cannot commit late results themselves.

A cumulative conflict evicts only the refused incoming item or batch entries, preserving already admitted tasks and unrelated checkpoint keys. This also repairs old duplicate caches without resetting their identity or silently making extra model requests. A later explicit retry can reauthor the evicted entry. Trusted preserved originals bypass stale cached payloads as before. Source contracts, marks, solver/reviewer/difficulty gates, provider selection and request/prompt versions are unchanged. No answers were hardcoded and no validation was relaxed.

## Tests and review scope

The initial focused regression run reproduced six failures with eight passing preservation controls. The final targeted suite passed 230 tests in 3.32 seconds, with five existing SWIG dependency deprecation warnings. Ruff checks and formatting checks passed. The two existing cancellation fixtures now supply task keys and identifiers instead of bare integers; their timing, refusal, late-write and cancellation assertions are unchanged.

New tests cover serial, two-worker local and hosted admission; duplicate cache eviction followed by a same-identity retry; prior accepted work surviving later failure or cancellation; the first five items surviving a sixth-item failure within one serial batch; retryable failed saves and discards; caller-thread writes and a late hosted worker; trusted originals with and without stale cached data; resumed metadata and monotonic counts; and solver, typed review and difficulty checks preceding admission. The gate-ordering positive uses controlled solver and difficulty results plus an actual schema-valid fake review. It proves orchestration, not answer correctness or measured difficulty. Existing solver and review tests run alongside it.

Final logs: `tmp/nov2-ai-assessment-admission-red.log` and `tmp/nov2-ai-assessment-admission-final-green.log`. Intermediate runs and the stale bare-integer fixture failures are retained separately. Aggregate release gates remain the integrating pull request's responsibility.

| File | Review scope | SHA-256 |
| --- | --- | --- |
| `Backend/Core/ai_assessment.py` | Full original 1,659-line EOF plus complete final repair; current 1,707 lines | `858d06800fed56bdde334f990c5bb746dac099099e41135362985ffb12bb556b` |
| `Backend/Core/assessment_checkpoints.py` | Fresh full 322-line EOF, including unchanged identity, atomic write and lock boundaries | `dbf6e24d4beee4f1e5d314b82fbcfb8d6212a7403055b5c6e858837e4242729b` |
| `tests/test_assessment_checkpoint_admission.py` | Full authored and reread 567-line EOF | `eaa127b410239ae1da203dd78bf118ff6d5b24dc50b44d8b1c32f774dd42deab` |
| `tests/test_hosted_generation_cancellation.py` | Bounded fixture delta review; current 163 lines, not a new complete-file review | `32fd80aca6bb4b8a91b3f476bdbd90bdcfdbd3b7d57e01024da7c1f23e8f83f7` |

Dependencies were traced selectively. This is internal implementation evidence, not teacher review, learner calibration, live model qualification or whole-project audit completion. No UI, accessibility testing, native build or new model request was performed. French paper qualification and distribution-signing limits remain separate and unchanged.
