# French positive-credit generation contract

A bounded local Qwen trial on source `05947713` failed after two authoring
responses in 419.99 seconds and published no PDF. Its source, model, reference
and process guards passed; the paper was not qualified. Root then reproduced a
specific contract gap using the actual public `exercise_request` schema:
`Draft202012Validator` accepted a Credit with `points: "0"`, while the unchanged
runtime Credit model rejected that same dictionary as nonpositive. The retained
receipt is `tmp/nov6-french-positive-credit-contract-repro.json`.

The repair expresses this existing per-field invariant in new generation
schemas. Portable bounded alternation admits the previous ASCII six-integer,
four-fraction-digit forms only when positive, including leading zeros. It uses
no lookahead, `not` constraint or value enumeration. Runtime full-match,
positive-credit and total checks remain necessary and unchanged. In particular,
some JSON Schema regex implementations accept a final newline with `$`; runtime
admission still refuses it. This is a generation-contract repair, not a change
to model responses, prose, answers, budgets or acceptance thresholds.

New generation uses `fr-nsi-v36-positive-points-v1`, recorded in package and
recovery identities. An absent identity field selects retained schema
reconstruction; an explicit unknown, null, boolean or legacy identity value is
refused. Request-schema, prompt and round hashes prevent dropping or swapping
the current policy to relabel its evidence. Explicit legacy request construction
and default historical authoring schemas keep their golden hashes. Existing
strict implementation-source identity checks are not relaxed: these controls
do not establish replay across different source implementations. No old record
or prior failed model run is rewritten as successful.

The genuine baseline exposed twelve zero-field failures with nineteen passing
controls. Twenty-four additional failures concerned APIs not yet implemented;
they are not counted as proof of the original schema bug. Final focused testing
passed 305 tests in 10.80 seconds with five existing SWIG warnings. The installed
`llguidance` package accepted the generated grammar through `grammar_from` and
`LLMatcher`; that compiler check is not Ollama or hosted inference. These tests
also cover positive forms, bounds, old schema/request/round goldens, package
policy provenance and rejected-round recovery without input mutation.

Root read the complete current 469-line NSI schema implementation. Root and an
independent reviewer read the complete new 242-line test file and the complete
pipeline delta with scoped callers. The pipeline's prior 2,102-line EOF review
is retained in `docs/quality/french-pipeline-source-bound-review.md`, evidence
SHA-256 `f3630b0f6550e76e217c54adfa4ff8ca5d290e5041eb3f2050ea6750597236f6`,
at source `8a71984c16628be3301d07fb25b39964cc573c50acb1a1ed5fd19cf2b03d7e50`.
Combining that read with the complete net 59-line repair delta supports the
current source-bound attestation, not a fresh read of all 2,161 current lines.

| File | Current SHA-256 |
| --- | --- |
| `Backend/Core/france/nsi.py` (469 lines) | `4eafcd9474c35bf02e2a23cdd923f44b5dc72b7e5633c3729e579a5b55f2b4c4` |
| `Backend/Core/france/llm_pipeline.py` (2,161 lines) | `8bb39421991695bf18865134e49e6aaf0d334e7dfd5ff8c533084887861babfa` |
| `tests/test_french_positive_credit_schema.py` (242 lines) | `9ac5d4d0815f93090164eda979760189ff3cb8b88cf50afa0c6ebfacdc4dfb28` |

The publication wrapper, `llm_runtime.py`, remains unchanged. Earlier `05947713` full-suite
and build receipts are prior evidence only; fresh frozen release gates are
pending. This review does not establish complete dependency behavior, a passing
live French paper, model-independent question quality, teacher or learner
evidence, official equivalence or complete project qualification.
