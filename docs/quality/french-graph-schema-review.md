# French graph generation schema

## Observed mismatch

One pinned free local Gemma4:12b run on the installed PR188 build ended with
exit status 1 after 381.87 seconds and published no PDF. Its first returned draft
failed the existing exercise credit-allocation check. Its second draft contained
a negative graph weight and failed the existing graph validator. Source, model,
reference and personal-state guards remained unchanged. This run is retained as
failure evidence, not a French paper qualification.

The public generation schema nevertheless permitted negative and over-limit
weights, and empty or oversized graph labels, which the existing typed material
validator refused. Owned public-schema tests reproduced 14 scalar mismatches:
two invalid weights and four invalid labels at each of three field locations.
The original RED run had 15 failures and 20 passing controls. Its fifteenth
failure was the not-yet-implemented policy identity, not another scalar defect.

## Generation-only repair

The new `bounded_graph_fields=False` option preserves every previous default
schema. Current generation explicitly enables it. Graph node and edge endpoint
labels must contain 1 to 24 characters, including at least one non-whitespace
character. Interior or surrounding whitespace accepted by the existing runtime
remains accepted. Edge weights retain their existing integer type and the
runtime's inclusive range of 0 to 1,000,000. The shortest-path verification
contract reuses those same bounded edge definitions.

The current schema policy is `fr-nsi-v36-graph-bounds-v1`. The named explicit
`fr-nsi-v36-positive-points-v1` policy remains available for retained V36 replay;
an absent policy still selects the older machine-fields schema. Neither replay
path relabels its evidence. New generation records the graph policy, and replay
reconstructs the corresponding request and round hashes. Removing or swapping
policy labels cannot make a current round inherit old request evidence.

The earlier default, machine-field and explicit positive-point schemas keep
their exact hashes. Existing runtime validators, prompt prose, answers, budgets,
retry counts and thresholds are unchanged. The embedded schema and its derived
prompt/request hashes intentionally change for the new policy. Strict
implementation identity remains required; these tests do not authorize replay
against a different implementation hash.

Graph membership, unique nodes, self-loops, duplicate edges and other relational
constraints still require runtime validation. Scalar schema bounds cannot fix
an incorrect credit total or establish the correctness of a model's reasoning.

## Review and verification

Root previously read the complete 469-line NSI module, then reviewed the complete
13-line graph-schema diff. Current `nsi.py` has 480 lines. For `llm_pipeline.py`,
the earlier composite EOF review remains recorded in
[the positive-credit review](french-positive-credit-schema-review.md). Root read
the selected policy, request, recovery and identity paths and the complete
14-line graph-policy diff. This does not claim a fresh full read of the current
2,167-line pipeline. The test author read both complete test files; root reviewed
the new graph tests and the one-line current-policy migration in the existing
positive-credit tests. Earlier source-review attributions remain in their notes.

The final focused group passed 318 tests with five existing PyMuPDF SWIG
warnings. Coverage includes valid field endpoints, shared shortest-path edge
bounds, unchanged cross-field runtime refusals, exact old request/round hashes,
retained positive-policy accepted and rejected records, absent machine-policy
replay and policy-laundering refusal. The installed llguidance JSON grammar
compiler accepted the schema; this is not an actual Ollama/hosted-provider
generation result. Scoped Ruff checks and formatting passed.

| File | Lines | SHA-256 |
| --- | ---: | --- |
| `Backend/Core/france/nsi.py` | 480 | `35ac192fe980fb24d697325018b8f703d5a41a8bffa1dc7cda70f81f9f129eff` |
| `Backend/Core/france/llm_pipeline.py` | 2167 | `c4dea74bacde8b5277dcdcee522f071d4c282a9e45eebd3a874b991053ff1953` |
| `tests/test_french_graph_field_schema.py` | 210 | `dbd677a830d67e31f2c88e9c0cf5e37caba6994baa51aa63ef1f2b36e23cb512` |
| `tests/test_french_positive_credit_schema.py` | 242 | `77e357006caffedd1d537323d1def3fc0d81441bfd0d183328a93fb808e80b20` |

The Gemma result and private recovery files remain in
`tmp/nov6-final-app-acceptance/french-gemma-positive-contract188/`.
The recovery JSON SHA-256 is
`1faaf75f449cce14bde71eaecd91df64c7f6d8b02836c5e65480b2df01698ad5`.
RED and focused logs are `tmp/nov6-french-graph-schema-{red,final-focused}.log`.

No model retry, new provider call, full suite, release build or native interaction
forms part of this repair's evidence. No teacher review, learner calibration,
official-paper equivalence or live French quality pass is claimed.
