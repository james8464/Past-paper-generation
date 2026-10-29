# Shared JSON client boundary

`Backend/Core/json_client.py` defines the common `generate_json(prompt)` protocol.
Existing solver, reviewer, simulator and specialist-CS import names remain aliases.
The richer assessment client still declares provider/model metadata and parallel
generation support. Adapter factories, hooks, eight maintained CLI entry points
and Edexcel client parameters now name the shared minimal protocol.

Provider implementations, payloads, prompts, retry counts, sampling defaults and
checkpoint/package JSON are unchanged. Minimal fake clients still need only
`generate_json`. This change makes annotations consistent; it adds no runtime
client-validation layer, configured static type checker or performance claim.

The first contract run failed three tests and passed four. The final focused
contract run passed eight tests, including shared aliases, resolved annotations,
all dynamically loaded entry points, factory/supplied-client identity, preview
without AI work and solver/simulator private-answer canaries. The wider
fixed-source targeted gate passed 692 tests with two skips in 8.29 seconds,
covering providers, reviews, replay, numeric contracts and specialist generators.
Ruff and the whitespace diff check passed.

Logs remain at `tmp/json-client-contract-red.log`,
`tmp/json-client-contract-green.log` and
`tmp/json-client-contract-targeted-final-green.log`. These are targeted results;
the combined final-source release suite and protected checks remain required.
