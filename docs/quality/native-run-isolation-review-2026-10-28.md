# Native run isolation and UTF-8 event review

## Reproduced defects

The implementation-practice audit found two release-relevant defects in the
native helper boundary. Regression tests reproduced both against the old
behaviour: the 121-test native suite reported 37 assertion failures, including
all six cancellation/lifecycle tests. The unchanged tests outside these new
regressions passed. The red log is retained at
`tmp/native-run-isolation-red.log`.

Cancelling generation immediately released the interface while the old helper's
queued callbacks still referenced the shared coordinator. Delivering its progress,
file, error or completion after a replacement started could attach the wrong PDF,
change the new job's status or finish that job. A cancelled model pull could also
select its model after another operation started. The benchmark coordinator had
the same callback-ownership problem.

Separately, the helper reader decoded each arbitrary pipe read as a complete
UTF-8 string. Splitting an accented French character across two reads made decoding
fail and discarded that entire read. A lost chunk could contain part of a JSON
event, including an artifact path.

A second-pass review found an older related defect in Ollama discovery. Its
status/models collection awaited a helper, then applied results without checking
whether a new generation or benchmark owned the interface. Five further tests
reproduced 17 assertion failures in a 128-test suite: delayed discovery errors
could overwrite French-generation status and poison its error state. A refresh
could also become stale while a new run started and finished. The original 123
tests still passed. Evidence is retained at `tmp/native-refresh-isolation-red.log`.

## Changes

Each launched operation now captures a private session token. Only matching
callbacks can change coordinator state. Normal cancellation invalidates ownership
before terminating the helper. Repeated completion or late events are ignored.
MLX setup retains its existing cancellation contract: the interface waits for
that setup helper's exit, ignores buffered events while cancelling and does not
restart generation. Successful setup transfers ownership to the generation run.
Benchmark sessions use the same ownership rule.

Ollama discovery also captures a revision that becomes obsolete when a newer
operation starts or is cancelled. Status, model-list and failure paths check the
revision after suspension. The revision remains changed after a run finishes,
so its old discovery request cannot regain ownership. French generation still
does not require Ollama or wait for discovery to finish.

The helper boundary now accepts an injected `BackendRunning` implementation.
Tests capture the callbacks passed by the actual production launch paths, without
starting a model or modifying user documents. This interface does not change
Store fallback restrictions or helper signing.

The stream reader buffers bytes until a newline, then decodes the complete event.
EOF flushes an unterminated final line. Invalid UTF-8 produces an unreadable event
for the existing strict JSON rejection path; it is not silently removed or repaired
inside otherwise valid JSON.

## Verification and limits

The first fixed native suite passed 123 tests with no failures, retained at
`tmp/native-run-isolation-green.log`. After the discovery fix, the final native
suite passes 128 tests with no failures, retained at
`tmp/native-run-isolation-final-green.log`. New coverage includes every possible byte
split of an accented French/emoji JSON event, one-byte chunks, multiple lines,
EOF and invalid UTF-8. Seven lifecycle tests cover UK/French replacement,
cancelled buffered events, repeated completion, cancelled model selection,
MLX cancellation/successful handoff and benchmark replacement.
Five deferred-discovery tests cover stale status, model-list and thrown failures,
a completed replacement and an active benchmark. They use controlled
continuations and published-state expectations without timing sleeps.

Personal-development-signed Store-mode preflight and direct Release builds pass,
with logs `tmp/native-run-isolation-final-store.log` and
`tmp/native-run-isolation-final-direct.log`. The direct bundle passes strict
signature verification. These are development signatures, not App Store approval.

Computer control launched the tested Debug candidate on the existing user profile,
started and cancelled a benchmark, restarted and cancelled it again, then returned
to the French workspace. The expected fifth-family exhaustion notice appeared
without a stale benchmark failure. The candidate was closed. No model, output,
language or enlarged-print preference was changed. This was a cancellation check,
not a completed performance calibration or a fresh generated French paper.

These tests establish callback isolation and byte-framing behaviour. They do not
establish transactional publication, termination of every descendant process,
complete interface coverage or model/paper quality. Protected checks and merge
evidence remain required before release. Existing user history, MLX trust
restrictions and sandbox settings are
unchanged.
