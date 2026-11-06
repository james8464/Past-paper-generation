# Generation cancellation and recovery interaction review

## Scope

The new opt-in native test hosts the real `ContentView` with a controlled
provider. It uses UUID-scoped preferences, temporary history and output,
fake secrets, notifications disabled and an injected Apple-model status check.
Its backend never launches a process or contacts a model. Standard preference
domains and an owned sentinel are checked unchanged. The default CI run skips
this operator-driven window rather than waiting for computer control.

The test author and a separate reviewer read the entire 203-line fixture and
the relevant cancellation/callback ownership paths. Root reviewed the whole
fixture before execution. No production UI or cancellation policy was changed.

An earlier interaction checklist incorrectly expected ordinary generation to
remain in Cancelling until the helper exited. The actual policy releases that
UI immediately and refuses subsequent callbacks from the cancelled run.
Only MLX setup retains cancellation ownership until its helper exits. This
review corrects the test expectation; it does not describe a product repair.

## Observed native journey

Root used computer control on the actual hosted window:

1. Saw the held Accounting run at 35 percent, selected History and observed
   the active history row and persistent progress bar.
2. Pressed the real Cancel button. The progress bar disappeared and History
   showed Cancelled. The fixture verified immediate creation readiness.
3. Returned to Accounting and pressed the real Create Paper button.
4. Injected one owned provider failure. The real alert showed a concise
   unavailable-model message. Root dismissed it with OK.
5. Pressed Create Paper again. The fixture delivered old progress, file,
   completion, error and process-finish callbacks from both earlier runs.
   The replacement kept its identity and 45-percent progress, with no stale
   document or alert.
6. Pressed the real Cancel button, then finished the fixture. It verified two
   cancellations, three requests and no completed history record.

The selected XCTest passed in 64.111 seconds with no failures. Its test-host
app was then quit normally; process absence was checked without relaunching it.
All 81 regular JSON files under the installed app's data directory retained
their hashes. The canonical installed app was not replaced by this test.

Evidence is in `tmp/nov6-generation-recovery-interactive.log` and
`macOS/build/logs/nov6-recovery183/test.xcresult`. This is a bounded native
interaction check with a fake provider, not a real model-generation result,
missing-model admission test, MLX process-escalation test, complete interaction
inventory, HIG certification or French-paper qualification.

| Reviewed fixture | SHA-256 |
| --- | --- |
| `macOS/Tests/GenerationCancellationInteractiveTests.swift` | `5ebf70c8525fef26cd1a001a09f3cb9c09da952e11e06b05374052dd02179bb3` |
