# Explicit French repeat-practice policy

Date: 29 October 2026. Scoped runtime/CLI change on
`main-xcode-and-validation-follow-up`, based on protected main `63964360`.
This is not new paper-quality, visual, teacher or learner qualification.

`generate-assessment --repeat-practice` enables `repeat-practice-v1` only for
application-owned French generation. The CLI default remains strict; historical
Ollama diagnostics reject the new flag before accessing a model. Native callers
explicitly request this practice policy and provide fresh random seeds.

Selection honours supplied saved-family exclusions first, with an empty
cross-history comparison set. Only `FamilyCatalogueExhausted` permits fallback
to the requested seed. Invalid exclusions, invalid sources and other selection
failures are not swallowed. Without exclusions the standalone repeat CLI does
not infer unused families from output history. Its help describes that limit.

The retained V35 source, pipeline and renderer are unchanged. Full package
replay, reference eligibility and within-paper checks still run. Existing saved
history and files are not cleared or rewritten to permit repetition. Repeat
checkpoints have an explicit policy namespace separate from strict checkpoints;
selected seeds remain consistent in package, manifest, output folder and request.

Repeat manifests explicitly record `practice_policy: repeat-practice-v1` and
`cross_history_comparison: not_performed`. They do not claim cross-paper
uniqueness. Teacher review and empirical calibration remain `not_run`. Strict
manifests retain their prior shape.

## Focused evidence

Retained ignored logs under `tmp/`:

| Log | Result |
| --- | --- |
| `french-repeat-practice-red.log` | 5 failed, 4 passed before implementation |
| `french-repeat-practice-final-green.log` | 16 passed in 13.43 seconds |
| `french-repeat-practice-same-seed.log` | 1 passed, 16 deselected in 7.35 seconds |
| `french-repeat-practice-related-green.log` | 107 passed, 20 deselected in 301.61 seconds |
| `french-repeat-practice-final-parser.log` | 1 passed, 16 deselected in 0.87 seconds after the final help-only clarification |

The sixteen dedicated cases include seven successful real V35 package
generations, unused-family preference followed by reuse, strict-default refusal,
checkpoint separation, unchanged earlier files, actual answer/mark/duplicate
question mutation refusal, empty-reference refusal and invalid exclusions.
Their PDF stage is stubbed; these are package/runtime tests, not visual renders.
Related tests include real retained public-runtime PDF paths. The related run
finished naturally before an attempted interrupt found no remaining process;
its passing result is not a partially interrupted suite.

The separate collision test confirms that an identical explicit seed producing
an existing deterministic destination is still refused, with every existing
file unchanged. Repetition does not grant overwrite permission. New random app
seeds allow repeated families without that deterministic-path collision.

Scoped Ruff and diff checks passed. The final help clarification alone follows
the 107-test run and sixteen-case package run; its parser check is separate.
No whole suite or signed build was performed by this task. The parent owns
integrated native/build/CI acceptance. No current repeat-mode PDF has been newly
visually requalified, and no source-family diversity or calibrated difficulty
improvement is claimed.

## Final byte identities

| Path | SHA-256 |
| --- | --- |
| `Backend/Core/france/runtime.py` | `fa62e36c7941ef19dd3303770107ebb8ac614c08103be2a2a52292cf7be120f4` |
| `Backend/Core/cli.py` | `5bcf0104cb6546ac821d879e099b4cda8901ae2b7749538baf004d76dabec3f0` |
| `tests/test_french_repeat_practice.py` | `f853c754f40dc3af2a76b6fc176d921aa7daca6807892a56386acc6570e56719` |
