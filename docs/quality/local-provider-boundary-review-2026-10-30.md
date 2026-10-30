# Local provider and checkpoint boundary review

This review read the five source files below to EOF, then reviewed their fixes.
It covered owned subprocesses, the Apple helper protocol, Ollama model discovery
and checkpoint corruption. Related callers and tests were inspected within that
scope. It does not establish a whole-project review or model quality.

## Findings and fixes

- Apple helper cleanup previously allowed two seconds before killing a child
  that ignored termination. The app also force-stops the backend after two
  seconds. Both helper waits are now 0.25 seconds. A real, owned test child
  reproduced the old delay and was reaped after the fix. Only its `Popen` is
  signalled; no process name, shared service or process group is targeted.
- Guided helper output decoded every JSON number as `Double`, silently changing
  an integer such as `9007199254740993`. Integer-looking values now require exact
  native-Int conversion and agreement with the original Decimal value. Supported
  exact integers are encoded through Int. Unrepresentable integers are refused.
  Ordinary fractional values retain floating-point approximation; this is not an
  arbitrary-precision decimal implementation.
- Cancelling a model pull could leave its CLI child alive. The progress wrapper
  now owns that exact child through spawn, cancellation and cleanup, restores
  the previous termination handler and bounds both waits to 0.35 seconds.
  Repeated termination cannot interrupt cleanup. The shared Ollama service is
  never stopped by this wrapper. Startup errors no longer echo all arguments.
- Valid JSON with malformed Ollama catalogue structure, or invalid UTF-8, could
  break discovery. Explicit response-shape checks now return the existing
  unavailable/fallback result. Unexpected programming errors still propagate.
- Invalid UTF-8 in a checkpoint escaped the actionable corruption error. It now
  raises `CheckpointCorrupt` with the path and original cause, leaving bytes and
  identity checks unchanged. The validated item mapping has an explicit static
  type, and the progress callback no longer reuses a float variable for an
  optional value.

## Reviewed source bytes

| File | SHA-256 |
| --- | --- |
| `Backend/Core/apple_intelligence.py` | `f72fbe40505c53ac8b8951377938a529c4ea763af7fda4d928375349fafc165d` |
| `Backend/Core/assessment_checkpoints.py` | `a7df228605c6e70184189378739612bd53405638579a6930412d1ade02f54a5b` |
| `Backend/Core/events.py` | `5af17abdf2ccc45275dfd99b427848599b5b1e98a6302a36d2b441a210998c72` |
| `Backend/Core/ollama.py` | `bf25ece5ea0bb93a312ce8fc9456c511eaeeb2bc4df9130188926eeb6f0ec53b` |
| `macOS/AppleIntelligenceHelper/Sources/KeldinAppleIntelligence/Protocol.swift` | `ce8bd852ebf9f880a941bceb44236435c8cb35bcfa516188455c86f444627f34` |

## Test evidence and limits

The corrected Apple shutdown reproduction failed before the fix. Its first
fixture used `InterruptedError`, which `communicate` retries; those earlier logs
are not acceptance evidence. The corrected fixture raises the same kind of
non-retried exception used by application cancellation. It checks a real child
that ignores TERM, without invoking a model.

The combined Python boundary gate passed 148 tests. The separate Swift helper
gate passed 16 tests, including plain, decimal and exponent spellings, signed
limits and near-integral fractions. Four-file mypy, Ruff and formatting checks
are separate from release builds. Test counts overlap earlier agent runs.
Logs are under `tmp/final-validation-20261030/local-boundaries-*` and the private
agent worktrees' `tmp/apple-intelligence-20261030/builds/`,
`tmp/checkpoint-encoding-20261030/` and `tmp/occitanie-editorial-rewrite/`.

Separate read-only reviews checked the Apple shutdown and exact-number changes.
No inference, download, hosted request or model-quality test was performed by
this batch. Timing tests establish cleanup on the tested host, not a universal
kernel scheduling guarantee. Full regression, signed builds, protected checks
and installed-build acceptance remain separate release requirements.
