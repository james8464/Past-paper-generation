# Prompt construction and known-key projection

P6 separates prompt construction from model orchestration. It preserves the
current trusted request contract, prompt text, retries and subject-solving order.
Historical French modules were not edited.

## Ownership

`assessment_prompts.py` owns the task input record and the existing authoring,
repair, batch-review, semantic/source and demand-input builders. Established
helper names in `ai_assessment.py` remain aliases, including `_Task` and the
semantic stopword set. Generation, candidate validation and checkpoint work stay
in the orchestrator.

`solver_prompts.py` builds the blind solver prompt and its public output-shape
contract. Numeric-evidence retry behaviour remains in the solver. The four
deterministic subject calls have one named helper in their original module;
there is no new plugin registry or dispatch framework. Accounting, CS, Economics
and selected-response precedence is unchanged. A non-None empty dictionary
still stops that chain and then fails the existing empty-answer check. Explicit
numeric-expression evaluation still overrides an earlier subject result.

`answer_projection.without_private_answer_keys` retains exactly the existing
hidden-key set and dictionary/list recursion. The legacy `_without_answer_key`
name remains an alias. The calibration helper's lazy import uses the public API.
This filter is not a printed-candidate whitelist: `required_entries` and other
unlisted metadata remain, as do ordinary source columns named `credit`. Tuple
and scalar behaviour is unchanged. Author/reviewer evidence projections were
not replaced with this blind-solver filter.

## Characterisation

Before refactoring, 18 tests passed against the frozen P4 source. The retained
JSON fixture contains the complete prompt strings, UTF-8 SHA-256 hashes and
trusted request metadata for authoring, repair, review and open/closed/MCQ/SQL
solver cases. It contains app-owned test inputs, not official paper material.
The fixture was not regenerated after extraction.

After extraction, 19 tests passed, including the new compatibility-alias check.
They preserve exact prompt bytes, schema hashes, sampling, budgets, identifiers,
dispatch short-circuiting, exception propagation, numeric precedence, source
privacy canaries and unchanged input objects. Separate literal checks against
baseline `0f8dcbe` confirmed unchanged string constants in all moved assessment
builders and the key filter, and an unchanged combined solver-literal multiset.
Those checks support the runtime snapshots; they do not establish arbitrary
behavioural equivalence on their own.

Logs are retained in `tmp/p6-pre-refactor-characterisation-green.log`,
`tmp/p6-characterisation-post-refactor-green.log` and
`tmp/p6-string-literal-parity.log`. The fixture is
`tests/fixtures/assessment_prompt_snapshots.json`.

The final fixed-source targeted gate passed 1305 tests with two skips in 21.69
seconds. It includes the prompt/request, privacy, source/credit, calibration,
historical French, checkpoint and specialist suites. Its log is
`tmp/p6-prompt-projection-fixed-source-green.log`. Ruff and the whitespace diff
check passed. This is a targeted result; the combined final release suite and
packaging checks have not run for this P6 source.

This is a structural refactor. It establishes no performance improvement,
configured static-type-checker result, live provider qualification or complete
paper-quality approval. Core implementation fingerprints change with the source;
final-source release checks remain required.
