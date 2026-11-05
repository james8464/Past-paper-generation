# French generation error presentation

## Scope

The native error alert exposed an internal Pydantic validation dump when a
French model-generated exercise was rejected. A second observed refusal reported
a failed independent generic verification. Both refusals correctly stopped
publication; this change affects their presentation, not their acceptance rules.

`GenerationPresentation.error` now uses the existing English/French quality-check
recovery message for these two explicit French failure prefixes. Classification
requires `french_generation_failed`, the first line, and a valid exercise or
question identifier. The generic verification identifier matches `NSIQuestion`:
`[1-9][0-9]?[a-z]?`. Provider, network, output and cancellation failures retain
their original presentation. A quality-check phrase later in a diagnostic does
not classify the failure.

No prompts, model output, answers, validators, schemas or publication rules
changed. Full backend messages remain in activity, diagnostic summaries and
failed run records.

## Source identity

- `macOS/Keldin/Domain/GenerationPresentation.swift`:
  `b44d8386b5263d0d3c3a7a2a7b2715895805538985c4aa969d2ce75aea501a83`
- `macOS/Tests/CoordinatorTests.swift`:
  `6cf8d1a5037b67b90c6f380bfa0b2660b68e9fd09b2c1f0126dd0b034e1d32c0`

Root independently reviewed this exact two-file delta before commit. This is a
scoped change review, not a new whole-file or whole-project audit attestation.

## Runtime checks

The captured structural refusal reproduced four expected assertion failures in
two focused native tests. English/French presenter and coordinator alert checks
failed; preservation and negative controls passed. The captured generic
verification refusal independently reproduced four expected failures in two
focused tests before the production fix.

After the fix, 75 native tests passed with no failures: `CoordinatorTests`,
`NativeInterfaceAuditTests` and `FinalInterfaceGuardTests`. Tests used isolated
preferences, controlled backend requests and isolated history. No model request,
native user interaction or real user-data mutation was needed.

Logs retained in the implementation worktree:

- `tmp/nov5-french-error-red.log`
- `tmp/nov5-french-error-semantic-red.log`
- `tmp/nov5-french-error-green.log`

## Limits

This verifies the alert text and preservation of raw failure records. It does not
qualify a French paper, improve a model's reasoning, certify all failure messages,
or establish complete interaction coverage. The observed model outputs remain
rejected. Native full-suite, release, protected CI and installation checks belong
to the final combined release gates.
