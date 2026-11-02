# Edexcel specialist checkpoint admission

Internal engineering evidence, 2 November 2026. Source repair:
`a14213b5edb703b9980a34d782a86d7c408d1a14`, based on `5ff92be5`.
This is cache/retry correctness evidence, not question, model or paper qualification.

## Reproduction

The actual Paper 3 builder at seed `270100` supplies questions `1(d)` and `1(e)`
with the same Extract C and no required scope terms. Controlled, schema-valid
author/review responses can give both the same parent stem while retaining their
individual immutable source and marking. The full blueprint correctly refuses
the repeated parent stem, but the old specialist helper already saved both.
A same-identity retry then made zero fake calls and refused again.

The new regression uses the actual specialist helper, typed request schemas,
individual validators, owned checkpoint store and complete original blueprint
validator. It asserts the imported specialist module belongs to this worktree.
Only author/review responses are faked; their positive verdicts are not evidence
of educational correctness. Original blueprint objects remain unchanged.

Before the repair, six assertions failed across serial, two-worker local and
hosted modes: both newly conflicting questions remained durable, and both old
conflicting entries survived the zero-call retry. Six failure/cancellation
prefix controls already passed. The earlier independent reproduction remains
in the docs checkout under `tmp/nov2-specialist-checkpoint-pattern-probe.py`,
its matching `.log`, and `tmp/nov2-specialist-checkpoint-pattern-review.json`.

## Bounded repair

The existing final validator's case-folded, whitespace-normalized parent-stem
check is extracted into `pastpapergen.validation.admit_parent_prompt`. The final
validator invokes it at its original position; there is no new fuzzy threshold,
source exception or change to assessed parts, marks, credit or calibration.

Each question stages checkpoint changes. Caller admission checks its actual
accepted candidate against already admitted parents before `commit_item`.
Serial questions become durable individually. Parallel workers only stage;
caller-owned mapper callbacks admit and commit. An old conflicting cache entry
is evicted only when that question is refused; earlier admitted and unrelated
keys survive. No cache identity changes, blanket clear, automatic model retry,
answer rewriting or final-gate weakening are introduced.

## Focused checks and limits

Seventeen new cases cover the three modes, old-cache eviction and recovery,
no-store refusal, valid serial prefixes on failure/cancellation, write-failure
recovery, immutable source/mark preservation, and a real late hosted worker
that can stage but cannot change the checkpoint after another worker fails.
The late-worker case records actual disk writes on the caller thread only.
Recovery authors/reviews only the missing question and passes the unchanged
complete-blueprint validator.

The final focused run passed 154 tests, including the new file, existing
Edexcel authoring, blueprint and assessment-contract tests, and hosted-generation
cancellation tests. Ruff check, Ruff format check and diff checks passed.
An intermediate failure was confined to the new late-worker test's fake response
not supporting its selected multipart fixture; that fixture now selects another
real unscoped evaluation question and preserves its own extract. No existing
positive fixture or assertion was changed.

Local logs: `/tmp/keldin-edexcel-admission-red.log` (SHA-256
`10bb0a8520d1e69ac5a648f937e4cd1fd36f4fbdd282f387bf870c3d612009e6`)
and `/tmp/keldin-edexcel-admission-focused-final.log` (SHA-256
`696622cbac31a908be423076ce6fc318e79eff15b41e3e985e149405b6ea6f25`).
The primary project virtual environment ran pytest; no model, paid API, network,
UI, installed-data or user-cache operation was performed. Full integrated gates
and any live/manual paper qualification remain separate.

## Source identities and review

The author subsequently read both final source files completely through EOF.
The independent reviewer inspected the entire change and relevant surrounding
paths, plus all 310 new test lines. Neither review ran a model or qualified a paper.

| File | Completed review scope | SHA-256 |
| --- | --- | --- |
| `Resources/economics/edexcel-a/generator/pastpapergen/ollama_client.py` | Full 1,195-line EOF | `4a6ceecf3e2ec5d266152410e233fabda9066467fadf21bb9005c0afc39243e3` |
| `Resources/economics/edexcel-a/generator/pastpapergen/validation.py` | Full 140-line EOF | `3b63378429d233b7ef1e32432288affb72cd6dbc9fa50806eb11ff5f0fb43596` |
| `tests/test_edexcel_checkpoint_admission.py` | Full authored and reread 310-line EOF | `c4918e8e674fcd9a50109731e2e63889238997a706828736eb7b1e37ac41bbaf` |
