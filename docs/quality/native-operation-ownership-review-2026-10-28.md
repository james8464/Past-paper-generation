# Native operation ownership

## Findings and changes

The benchmark result event previously released `isRunning` before the helper exited. Another benchmark or model download could then start while the first helper still owned its process. A result now supplies the verdict and final progress; only the matching process completion releases benchmark ownership.

Model download and MLX setup confirmations previously relied on view-level disabling. Their launch methods now refuse work while either generation/model work or a benchmark is running. The download control in Settings also reflects benchmark ownership.

A model download previously finished through the generation completion handler. If an earlier generation's cancellation could not be written to history, completing the download could complete or fail that unrelated job. Downloads now have a separate terminal handler that does not complete, fail, export or otherwise write a generation job. Successful downloads still select the model and refresh Ollama. Failed downloads do not select it. The nonzero-exit message has English and French copy.

The same ownership problem existed when cancelling a download. The initial fix limited cancellation writes to generation operations. The typed ownership follow-up below now requires the exact job ID as well. Cancelling a model download preserves any unrelated active record and uses model-specific English or French copy. MLX setup retains its existing wait-for-exit cancellation behavior.

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

## Typed per-run ownership follow-up

A later source trace found that seed-free French reference preparation and
review-record operations shared generation completion without beginning a job.
A controlled regression reproduced changes to an earlier job's progress,
artifacts and persisted JSON after its cancellation write had failed. The fault
uses only temporary history directories; no user history is changed.

`BackendRun` now owns the run token, intent, process, optional job ID, immutable
target labels and model, document collection, cancellation phase and backend
error. `isRunning` is derived from that owner. Only a successfully persisted
paper begin acquires a job ID. Reference preparation, review recording, model
downloads and setup never acquire one. Their terminal handlers do not publish
or finalize a paper. A completed document collection outlives the process so the
last result remains available without retaining a false running state.

Every generation progress, artifact, completion, cancellation and failure call
requires the expected job UUID. A changed owner refuses mutation before artifact
assignment or history writes. The application also checks the owner before
publishing files. Actual backend closures retain their captured run UUID; late
events and duplicate completions cannot act on a replacement run. MLX setup
keeps its cancellation lease until the matching helper exits.

Paper file labels use the launch snapshot rather than a later catalogue
selection. Model-management file events are not paper artifacts and cannot
replace the last paper's result collection. A reliable history-begin failure
leaves the previous active record untouched and launches no helper.

### MLX continuation boundary

Normal setup UI already locks target controls and guarded selection methods.
No ordinary-user target-switch misrouting is claimed. A boundary test that
directly changes coordinator state did demonstrate that setup completion could
call `generate()` for a different target. Setup now captures board, paper,
provider, active model, preview mode, output URL and pending seed. It continues
automatically only if that target is unchanged. Otherwise the captured model
is ready, newer selections remain intact, and generation requires an explicit
request. Cancellation never auto-resumes generation.

### Follow-up test evidence

- Ownership red: `tmp/owned-operation-red.log`, one regression with 20 assertion failures.
- First targeted run: `tmp/owned-operation-green.log`, 74 tests with one migrated fixture failure. The fixture had bypassed the welcome guard before migration; its explicit welcome preference was corrected without changing the production guard.
- Combined resource red: `tmp/owned-operation-benchmark-red.log`, 82 tests with seven expected missing French benchmark-resource assertions; all 77 ownership/coordinator/publication tests passed.
- Combined green: `tmp/owned-operation-benchmark-green.log`, 82 tests passed.
- MLX boundary red: `tmp/owned-mlx-target-red.log`, one regression with 22 assertion failures.
- Final targeted green: `tmp/owned-operation-final-green.log`, 83 tests passed: 30 run-isolation, 40 coordinator, eight publication and five benchmark-localisation tests.
- Final result bundle: `macOS/build/logs/owned-operation-final-green/test.xcresult`.

The final cases include both maintenance intents across success, nonzero exit,
thrown completion and cancellation, launch failure, exact persisted-byte
preservation, wrong-job refusal, unchanged-target paper completion and MLX
continuation, target drift, stale callbacks and setup cancellation. Fixtures
simulate backend outcomes; they do not demonstrate live model quality.

The concrete operation-ownership findings are addressed by this scoped package.
N8's broader architecture cleanup remains partial: model-discovery snapshots,
model-option deduplication and further coordinator decomposition are not changed.
These are separate maintainability decisions, not measured performance gains.
Full native, release-signing, Store and real interaction gates remain for the
parent release workflow; this targeted pass does not certify the entire app.
