# AQA Computer Science checkpoint admission review, 2 November 2026

## Defect and boundary

The specialist AQA Computer Science authoring route does not use shared `generate_unique_paper`. Its individually reviewed questions were saved before whole-paper validation rejected repeated part prompts. At seed 270100, controlled replacements for authored questions 4 and 5 passed the actual individual source, marking and review-metadata checks but shared the same part prompt. The real complete-blueprint validator refused `Question 5.1 duplicates another prompt`. Both payloads remained cached, so the same-identity retry made no requests and refused again.

This was reproduced with one local worker and two local workers using real owned checkpoint stores and schema-valid fake authoring/review responses. The first attempt made four fake requests; the retry made zero. No model, network, paid calls, difficulty inference, rendered PDF or user cache was involved. Synthetic positive reviews are not evidence that the deliberately colliding questions are suitable for use.

## Repair

Every question now stages its checkpoint changes, including serial questions. The caller receives the actual validated candidate and checks it together with already admitted questions before committing or reporting acceptance. The predicate matches the existing final validator exactly: `" ".join(part.prompt.casefold().split())` must be unique across parts. It adds no similarity threshold and changes no source-context policy. The final validator is unchanged.

On conflict, only the incoming question's original checkpoint key is evicted; prior admitted questions and unrelated keys remain. This repairs old conflicting payloads without resetting their identity, rewriting model output or automatically making extra model calls. A later explicit retry can reauthor the missing question while reusing the other accepted record. Source data, marks, review requirements, immutable question routes, prompt versions and cache identity are unchanged.

Serial acceptance still persists each complete reviewed question before starting the next, so later failure or cancellation preserves the valid prefix. Parallel workers only stage their private changes. Admission, real persistence and accepted progress remain caller-owned. A late result after another worker refuses cannot commit itself.

## Tests and evidence

The actual regression run reproduced six failures with eight passing preservation controls. An earlier fake-client question-identification error is retained separately and is not reported as the engineering regression. The final focused suite passed 226 tests in 5.34 seconds, with five existing SWIG dependency deprecation warnings. Ruff and formatting checks passed.

The new cases use the actual q4/q5 seed-270100 blueprint and assert that the imported specialist module belongs to the current worktree. They cover serial, two-worker local and hosted routes, case/space-only equality, accepted-count refusal, preservation of unrelated keys, legacy conflict eviction and same-identity recovery, earlier-question durability on failure/cancellation, and a late hosted question whose staging cannot change the real store. A caller-thread assertion covers the durable write. A near-but-unequal prompt pair remains accepted by this admission rule, confirming that no stricter similarity rule was introduced. A separate test calls the unchanged complete-blueprint validator to confirm its exact case/space duplicate predicate.

Final logs in the documentation worktree: `tmp/nov2-aqa-checkpoint-admission-red-final.log` and `tmp/nov2-aqa-checkpoint-admission-focused.log`. The earlier two-specialist diagnostic remains at `tmp/nov2-specialist-checkpoint-pattern-probe.log`. This repair changes only AQA Computer Science; the separately reviewed Edexcel repair is integrated alongside it.

| File | Review scope | SHA-256 |
| --- | --- | --- |
| `Resources/computer-science/aqa/generator/cspapergen/ollama_client.py` | Author subsequently reread all 867 lines through EOF at this unchanged hash; independent reviewer read the complete admission diff and relevant surroundings | `3059a9d0300aafe44d80413c865b5643846037b6f10796d7d1702b6b70db5466` |
| `tests/test_aqa_cs_checkpoint_admission.py` | Full authored and reread 324-line EOF | `07ef680f865deb8cea345d63cd67205d921aefd1473b86d9449e4a4cf7af0613` |

This is internal implementation and controlled cache-ownership evidence. It establishes neither live paper quality nor measured difficulty, teacher review, learner calibration or whole-project audit completion. No UI, accessibility testing, native build, full release suite, shared Core edit or Edexcel source edit was performed. Aggregate release checks remain the integrating pull request's responsibility.
