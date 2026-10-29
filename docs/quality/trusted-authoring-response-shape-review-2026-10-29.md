# Trusted authoring response shapes

## Current-source diagnosis

The retained Ollama Accounting Paper 2 attempt at seed 270101 failed after four
accepted items. Its parsed events record malformed choices/key for question 05,
then an independent-solver/key disagreement, then another malformed choices/key
refusal. The raw model responses were not retained, so their exact contents and
the reason for the model's behaviour cannot be reconstructed.

Current source reproduces the relevant admission gap without model calls.
Question 05 has selling price £45, variable cost £10 and allocated fixed cost £5
per unit. Its base choices are £35, £55, £45 and £30; £35 is correct. The base
question is not arithmetically defective. The old authoring JSON grammar allowed
zero to four choices and a nullable key for every kind of question. Empty choices,
three choices, duplicate choices and a null key therefore passed that grammar,
then correctly failed the candidate validator. A fresh grammatical stem passes
the same validator with the base question's valid four choices and key.

This is a demonstrated response-contract gap, not proof of the precise historical
model failure, and not evidence that a small model can complete every paper. The
default Llama-3.2-3B native attempt failed while refining question 02, but its exact
failure reason is unavailable. The accepted historical Qwen3-8B paper and failed
default-model attempt retain their own separate identities and results.

## Change and compatibility

`OutputContract.authoring_shapes` is an immutable tuple of owned identifier and
public response-kind pairs. If supplied, it must cover the exact owned identifiers
in order, use supported kinds, and belong to an authoring operation. The actual
authoring route binds it from the authoritative task, never by parsing candidate
or source prose.

- Multiple choice requires exactly four nonempty strings and an integer key from
  zero to three. The full schema also requires unique choices.
- Constructed response requires an empty choices array and a null key.
- Mixed batches use identifier-bound alternatives, preserving the expected-ID
  integrity checks. Reassigning response shapes to another owned ID is refused.
- Existing callers that omit shape metadata retain their earlier broad grammar.
  The current authoring route explicitly supplies the new metadata.

No expected answer, answer text or private marking credit enters this metadata.
The metadata is not copied into user prompts or checkpoints. Existing candidate
uniqueness, complete-choice agreement, numeric/source integrity, marking and
independent-solver checks remain. The change does not reduce validation or
reclassify an old failed attempt as successful.

## MLX grammar check

The existing MLX decoder adapter removes `uniqueItems`, which its constrained
decoder cannot express safely. The final original-schema validator still rejects
duplicate choices, and the candidate validator retains case/whitespace-aware
uniqueness checks. Exact choice count and non-null bounded integer key remain in
the decoder grammar.

Actual installed llguidance 1.9.1 compiled and validated the adapted single-MCQ,
single-constructed-response and mixed two-item grammars without errors. This was
a CPU-only grammar check with zero model calls, not an MLX speed or live-paper
acceptance run. The same check is included in the tests when llguidance is
installed; environments without the optional build dependency skip that one
grammar check rather than claiming it passed.

## Verification

The initial regression run failed 18 tests and passed the legacy-compatibility
case before production changes. Final focused checks passed 209 tests with five
existing PDF-library deprecation warnings, including the real no-model grammar
check in this environment. Ruff lint/format and diff checks passed. Evidence is
retained in this worktree under `tmp/authoring-response-shapes/`.

The focused suite covers malformed shape metadata, prompt-injection resistance,
per-ID mixed shape binding, boolean/out-of-range/null keys, malformed choice
counts, duplicate choices, copied schema ownership, the actual Accounting MCQ
authoring call, non-MCQ binding, checkpoint resume and metadata non-leakage.

Integration still requires the complete fixed-source suite, rebuilt-helper checks,
current live model acceptance, protected CI and installed-app acceptance. This
review makes no whole-paper quality, empirical calibration, full-HIG or App Store
approval claim.
