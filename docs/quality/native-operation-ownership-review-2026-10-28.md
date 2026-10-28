# Native operation ownership

## Findings and changes

The benchmark result event previously released `isRunning` before the helper exited. Another benchmark or model download could then start while the first helper still owned its process. A result now supplies the verdict and final progress; only the matching process completion releases benchmark ownership.

Model download and MLX setup confirmations previously relied on view-level disabling. Their launch methods now refuse work while either generation/model work or a benchmark is running. The download control in Settings also reflects benchmark ownership.

A model download previously finished through the generation completion handler. If an earlier generation's cancellation could not be written to history, completing the download could complete or fail that unrelated job. Downloads now have a separate terminal handler that does not complete, fail, export or otherwise write a generation job. Successful downloads still select the model and refresh Ollama. Failed downloads do not select it. The nonzero-exit message has English and French copy.

The same ownership problem existed when cancelling a download. Cancellation now writes a generation record only when the cancelled operation is a generation. Cancelling a model download preserves any unrelated active record and uses model-specific English or French copy. MLX setup retains its existing wait-for-exit cancellation behavior.

## Targeted evidence

All evidence below is from controlled native unit tests, without downloading a model or editing user history.

- Red: `tmp/model-operation-ownership-red.log`, 19 tests with 14 assertion failures and no unexpected failures. The pre-existing 15 isolation tests remained green.
- Green: `tmp/model-operation-ownership-green.log`, 20 tests passed, zero failures.
- Result bundle: `macOS/build/logs/model-operation-ownership-green/test.xcresult`.
- Cancellation follow-up red: `tmp/model-cancel-ownership-red.log`, one test with four assertion failures.
- Final targeted green: `tmp/model-cancel-ownership-green.log`, 21 tests passed, zero failures. Result bundle: `macOS/build/logs/model-cancel-ownership-green/test.xcresult`.

The six new tests cover the result-before-exit benchmark boundary, both launch confirmations during benchmarking and generation, three model-pull outcomes and model-pull cancellation after a reliable temporary history-write fault. The history cases check the unrelated active job, in-memory history and exact persisted JSON bytes. French copy is checked with an explicit application-language preference. Existing cancelled-session, delayed discovery and MLX cancellation tests remain in the targeted gate.

## Scope and remaining checks

No backend, paper content, PDF access, signing or Keychain execution changes are included. These tests do not replace the full native suite, Store-mode preflight or native interaction checks.

Keychain calls remain synchronous. This review establishes no measured UI stall and makes no performance claim. Measure privacy-safe operation durations before considering an asynchronous credential boundary.

N8 remains partial. A later source trace found that seed-free French reference
preparation and review-record operations share generic generation completion
without first beginning a generation job. A dangling earlier job after a failed
history write may therefore still be affected. This path needs its own controlled
regression and an explicit per-run owned-job fence before final release. The
model-pull fixes above are not presented as proof that every operation is isolated.
