# Apple guided authoring, 2 November 2026

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

Compatible `aqa_cs` authoring requests now select the existing guided mode before
inference, alongside the previously supported shared solver. The projection
support check is unchanged. Unknown constraints and other authoring operations
still use the existing text mode. There is no switch of mode after a refusal.

The complete prompt, original schema, output allowance, provenance checks and
mandatory postvalidation remain unchanged. Native guidance receives the declared
array bounds; postvalidation still refuses missing or extra parts and overlong
strings. No marking points or answers are inserted by this change. French
authoring with the Apple system model remains outside its supported capability.

## Evidence boundary

Eight red regression cases preceded the change. The focused Apple provider,
shared-client, trusted-request and packaging group passed 163 tests. Independent
review found no scoped P1/P2 issue. Tests use the actual two-part immutable-marking
output contract and check helper refusal without fallback. Full release gates
and fresh native Store acceptance belong to the associated pull request.

Guided shape does not establish a correct answer or exam-standard difficulty.
Existing semantic review, model warnings and paper-quality holds remain in force.
