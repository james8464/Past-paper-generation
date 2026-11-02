# Apple guided UK requests, 2 November 2026

## Observed failure

The development-signed sandbox app at PR147 completed an Apple system-model
request for AQA Computer Science Data structures topic practice. It rejected the
response because the parts array contained fewer entries than the owned schema
required. The private diagnostic recorded `properties.parts.minItems`, 1,260
input tokens, a 384-token output allowance and an 8,192-token context window.
This was not a context-admission failure. No PDF was published.

The exact diagnostic was read through Finder and Quick Look. No permission,
entitlement or private-container access setting was changed. Its response hash
was `27e9f6cbe8ce3befa4af750509bcd5051a87ef914f70ace9876d4af145be8cae`.
The raw response was not retained, so an output-token cutoff is not established.

## Scoped change

The helper already supports dynamic schemas with array bounds. Apple documents
[minimum and maximum array lengths](https://developer.apple.com/documentation/foundationmodels/dynamicgenerationschema/init(arrayof:minimumelements:maximumelements:))
and [guided generation](https://developer.apple.com/documentation/foundationmodels/generating-swift-data-structures-with-guided-generation).

An initial `aqa_cs`-only candidate passed its author output contract in the real
Store app. Its later review failed invalid JSON in the existing text mode:
2,142 input tokens, a 640-token allowance and an 8,192-token context window.
The review response hash was
`6052dc048caf6a9ef32283f5fd6a6a5ec59c0ec46fb9976ce91199c1ddee29df`.
No paper was published. Native navigation to History and previously saved PDFs
worked while that job was still creating questions.

Compatible known UK requests now select the existing guided mode before
inference. The explicit list covers solver, authoring, batch review, review,
difficulty, Edexcel, AQA Computer Science and open-credit operations. The
projection support check is unchanged. Unsupported constraints, French authoring
and unknown operations still use the existing text mode. There is no switch of
mode after a refusal.

Tests distinguish real compatible review and batch-review contracts from real
contracts that remain unsupported: nullable unions, unique-item constraints,
integer enums, minimum string lengths and open graph-parameter objects. Listing
an operation does not mean every schema used by that operation is guided.

The complete prompt, original schema, output allowance, provenance checks and
mandatory postvalidation remain unchanged. Native guidance receives the declared
array bounds; postvalidation still refuses missing or extra parts and overlong
strings. No marking points or answers are inserted by this change. French
authoring with the Apple system model remains outside its supported capability.

## Evidence boundary

Eight red regression cases preceded the initial authoring change. Thirteen red
cases reproduced the broader UK routing gap. The expanded focused Apple provider,
shared-client, trusted-request and packaging group passed 183 tests. Independent
reviews found no scoped P1/P2 issue. Tests use the actual two-part immutable-marking
author contract and 640-token review contract, and check helper refusal without
fallback. Full release gates and fresh native Store acceptance belong to the
associated pull request.

Guided shape does not establish a correct answer or exam-standard difficulty.
Existing semantic review, model warnings and paper-quality holds remain in force.
