# Apple on-device provider: bounded acceptance, 30 October 2026

## Scope and result

Keldin now has a distinct `apple_intelligence` transport using Apple's system
on-device model through a signed native helper. It does not reinterpret the
existing `apple` MLX provider or migrate saved model identities. No downloaded
model, hosted API, credential or cloud fallback was used in these probes.

The connector and capacity refusal work. A tiny French JSON task passed. The
representative UK solver task did not pass its complete response contract, and
complete French NSI generation does not fit this adapter's context allowance.
These results do not qualify a paper, subject, marking scheme or provider-wide
quality claim.

## Actual local probes

All evidence below is retained in the isolated `mlx-batched-generation` checkout
under ignored `tmp/apple-intelligence-20261030`. The tasks were run sequentially.
Timings are observations, not controlled speed comparisons.

| Probe | Captured source | Result |
| --- | --- | --- |
| Tiny French arithmetic with strict JSON | `9080773d` | Returned `{"result":4}`; 129 input tokens, 256 requested output tokens, 1.7554 seconds. |
| Current scoped French author request with original reference material | `9080773d` | Refused before inference: 7,552 input + 4,096 output + 256 reserve exceeds the actual 8,192 context. No reference, schema or question was shortened. |
| Original shared UK FIFO solver, structured text | `2cd15ce1` | Refused invalid structured output after 9.6067 seconds. 990 input tokens and 1,536 output allowance fit the context. No accepted mathematical answer. |
| Same owned FIFO problem, fresh explicit guided-with-postvalidation mode | `5a5d3776` | Complete JSON returned, but an explanation step had 288 characters against the unchanged 240-character limit. Original-schema validation refused it after 13.1861 seconds. |
| Same owned FIFO problem, bounded native string-length guidance | `00b2a11e` | Refused `generation_failed` after 0.9872 seconds, with 1,409 input tokens. No candidate or mathematical verdict. The new guide's runtime support was not established. |

The final task used the actual shared `IndependentSolver` request and schema.
Its public data were purchases of 80 units at GBP12 and 120 at GBP15, followed
by sales of 150 units at GBP24, with FIFO and no other inventory movements or
costs. The independently calculated gross profit is GBP1,590. That expected
answer was kept outside the request. The final model response reached GBP1,590,
but contained an earlier incorrect GBP840 calculation before correcting its
FIFO calculation. A correct final choice does not make that a clean reasoning
pass. No explanation was shortened, repaired, retried or accepted.

The final transport wrapper only recorded the original synthetic request and
helper reply. It forwarded both unchanged. Evidence:

- `final-adapter-run1/{identity,availability,tiny,capacity}.json`
- `uk-fifo-run1/{item,requests,responses,result}.json`
- `uk-fifo-run2-guided/{item,transport-requests,transport-replies,result}.json`
- `uk-fifo-run3-bounded-guidance/{item,transport-requests,transport-replies,result}.json`

The last helper-only experiment added native regex guidance for the existing
string length limit, without changing that limit or the original-schema check.
Its helper SHA-256 was
`ff887078536d783da9e53dea4c703462bcd6cf4c1b5c6a2c51c3c3dacb44ebcd`.
The Core identity stayed unchanged. Its helper returned a classified generation
error rather than a candidate. The record-only wrapper sat above protocol error
handling, so it retained the exact request and classified error but no raw error
envelope; `transport-replies.json` is empty. No further model call followed.
Compile-time guide support is not proof of working model-time guidance.

Final guided probe pins:

- Git head: `5a5d37761f43a671db97f536148ca26397563e6a`
- Core identity: `afc328b187833dcaf3bf575266825fc01d630301919ed821dadc31e5549d812b`
- Signed helper SHA-256: `d2121fae96e09e048c161f7603823a4def91c700ad56cfa7164f56c36b892b68`
- OS: macOS 27.0.1, build 26A434
- Model identity: `apple-system-on-device`; actual context: 8,192 tokens
- Input: 1,334 tokens; requested output: 1,536; framing reserve: 256

The original reference index was read-only. Its SHA-256 was
`ec2339e6dffeba485f94d33d8e6f868e24cd2c40ad32830621201496ca32d594`.
The registered development references were used for the capacity probe; this
was not an unseen-paper comparison. Source and helper hashes were checked again
after each probe.

## Deliberate product boundaries

Complete French NSI generation is blocked in the current backend route, direct
pipeline call and native creation controls. The message asks the user to select
another provider. This is a declared capability boundary, not automatic provider
fallback. The existing MLX and other French providers are unchanged.

Generic UK tasks can use the connector, subject to strict capacity, schema and
existing quality checks. Their presence in a routing registry is not evidence
that every full UK paper completes or meets exam standards. This evidence does
not establish that claim.

Guided mode is selected before inference only for compatible shared-solver
schemas. The complete original schema remains in the counted prompt. Native
guidance supports the explicit projection; string length limits still receive
mandatory original-schema postvalidation. Unsupported projections use the
separate structured-text mode from the start, never a retry after failure.
Malformed JSON, invalid schema values and context overflow remain failures.

## Engineering checks

The final cached native gate at `5a5d3776` passed 359 tests with one skip and no
failures. Its log is `builds/native-tests-run4-order.log`. The previous final
gate at `d7ffbbd6` passed the same count. The helper's required-property order
change also passed its 14 focused Swift tests in the helper author's checkout.

Before the final helper-only ordering change, 169 focused Python tests passed.
They cover protocol identity, strict JSON and original-schema validation,
capacity errors, French route refusal, selected guidance mode, overlong guided
strings, credential-free subprocess environment and fixed bundled helper
resolution. Ruff lint and formatting passed. The dedicated Python adapter
passed its scoped strict mypy check with missing third-party stubs ignored.
These are bounded checks, not a fresh whole-project test run.

The native helper is built through an SDK capability probe. An older or
intermediate SDK without the exact token-counting APIs produces an unavailable
helper instead of compiling an unsafe inference path. Startup checks the
restored provider without requiring the user to open Settings. Bundled backend
execution uses its own helper rather than an inherited development override.

No App Store upload, approval, whole-HIG certification, learner calibration or
teacher review occurred. Native UI interaction coverage is separate from the
unit/build checks recorded here.

## Final private-reasoning contract check

The shared solver's private `steps` field now permits up to 512 Unicode
codepoints per step rather than reusing the 240-character short-field limit.
This applies generally to open, multiple-choice and response-slot solvers, not
to one expected answer. Other short fields, supplied-choice enums, 16-step
limit, output budgets and semantic checks are unchanged. A red test reproduced
the old limit; 153 focused tests then passed, including 513-character refusal,
retained short-field limits and decomposed-Unicode counting.

Exactly one fresh actual FIFO call used this new original schema and the old
working guided-with-postvalidation helper, without native regex guidance. It
failed both response structure and independent mathematical review. Step 7
contained 1,145 characters against 512. Earlier steps incorrectly stated
`80 × 12 = 9600`, `120 × 15 = 18000` and `150 × 24 = 36000`; the actual values
are 960, 1,800 and 3,600. It also subtracted all purchased inventory instead of
the FIFO cost of the 150 units sold, which is 2,010. The final supplied choice
GBP1,590 was explicitly used as a placeholder after asserting that no choice
was valid. It is not evidence of a correct solution.

The call took 18.4413 seconds, with 1,334 input tokens and a 1,536-token output
allowance. Evidence remains in `uk-fifo-run4-reasoning-contract`, including the
unaltered helper reply. Core identity was
`746cc72bb2837d6a48773eb7f26ba126aa4997a48e20adaaadad09f7657f1145`,
Git head `96f467d6df04de15d604b31964782c339feae539`, and helper SHA-256
`d2121fae96e09e048c161f7603823a4def91c700ad56cfa7164f56c36b892b68`.
Source and binary were checked unchanged afterward. No further call, answer
repair or acceptance followed. This provider remains unqualified for this task.
