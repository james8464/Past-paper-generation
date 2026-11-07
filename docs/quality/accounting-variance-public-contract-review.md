# Accounting public variance classification

## Retained failure and bounded reproduction

The retained November 3 Paper 2 run (seed 270100, Ollama `gemma4:12b`) accepted
Q06 with a favourable material-usage key. Its stem described purchases below
standard production usage and a price above standard, without establishing
actual consumption. Purchases do not determine usage. For example, standard
usage 100 kg, purchases 90 kg, opening inventory 20 kg and consumption 110 kg
fit those premises but imply adverse usage. Price above standard also supports
an adverse price variance. That retained run remains semantically unqualified.

The retained assessment SHA-256 is
`b959e1a873ca9c36824241091414cc95e5e408ca609f744450bad93be65a22e8`.
A new offline regression submitted its exact stem, options and unsupported key
to the current candidate-construction path. Before this repair, the candidate
replaced the seeded question, reproducing the structural admission gap. This
was a controlled parser reproduction, not a fresh model run. The initial new
test file reported 22 failures and two passing existing-operation controls;
most failures were the not-yet-supported operation. The retained rewrite
assertion itself failed on accepted changed text.

## Contract and source ownership

The existing Accounting selected-response architecture now has one additive
`material_variance_classification` operation. Strict public facts identify:

- price or usage as the requested variance;
- purchased or consumed quantity as the evidence basis;
- a positive-quantity domain;
- actual price versus standard price, or actual consumption versus the
  standard allowance for actual production, as below/equal/above.

Usage from purchases alone is refused. Missing/extra facts, unsupported or
mistyped quantity domains, unspecified/both variance targets and invalid
comparisons are refused. Classification is derived by the general sign rule,
not supplied by a model or taken from the private answer key. Only the declared
qualitative comparison is supported; this is not a general natural-language
Accounting solver or an arbitrary numeric-quantity parser.

A canonical host renderer emits the visible premise from the same validated
facts. Solving requires that exact wording and a unique option in the bounded
classification domain. No keyword detector attempts to infer financial truth
from arbitrary prose. The current seeded Q06 wording, options, order draws,
answer, marking text, AO allocation and one-mark budget remain unchanged.
The existing 102-seed content/RNG digest still passes without changing its
golden hash. The earlier budget byte-contract test normalizes only the four
new Q06 ownership-context fields in its comparison copy, retaining its original
content/numeric golden hashes.

Only current Accounting Paper 2 Q06 acquires this new binding. Its prompt,
options, key and scheme use the existing immutable selected-response boundary.
The existing solver derives the answer without a model request; stale or
forged checkpoint text is rejected. Q04/Q05, the Paper 1 operations and other
boards' selected-response dispatch remain unchanged.

## Compatibility and limits

The operation is additive within the existing version-1 Accounting contract
shape. Older code will not understand the new operation. The Accounting adapter
identity advances to `ai-assessment-v15-accounting-variance-contract`; both its
version and blueprint ownership data invalidate old item caches. Tests verify
that mismatch refusal leaves retained checkpoint bytes unchanged.

Existing uncontracted historical packages are not rewritten, deleted or
retroactively qualified. Their semantic-only evidence remains semantic-only.
No model-quality warning is removed. Independent review, numeric/output checks,
reconciliation, AO/mark totals, coverage checks and difficulty requirements are
not relaxed. This repair does not establish official task equivalence, whole
paper quality, learner calibration or automated marking reliability.

Verification uses focused offline tests with fake clients only. No model,
network request, GUI operation, native/build job or complete-suite run was
performed for this candidate. Final release gates remain the root owner's task.

The final targeted run passed 346 tests in 3.34 seconds across the new variance
contracts, Accounting Paper 2 source choices, Accounting selected responses,
shared selected-response dispatch, shared numeric integrity, Accounting budget
assumptions and private-credit boundaries. Five existing Swig deprecation
warnings were reported. Ruff, formatting and diff checks passed. Missing/extra
facts, zero/negative/mistyped quantity domains, wrong units, canonical-wording
mutations, unique-option controls, forged private keys and retained checkpoint
bytes are covered. These are bounded contract tests, not live-model acceptance.
