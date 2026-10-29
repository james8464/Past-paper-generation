# Tooling file review, batch 2

Read-only application-source review at base commit
`0f8dcbe16eae8612d9abbed0e14880f46eabdcc6`, with concurrent P6 work in the
isolated worktree. Each complete file below was read at the recorded SHA-256.
The calibration helper already includes the P6 public-projection import change.
No source was edited or executed by this review. Writing this record is the
only change. This is not clearance of the complete tools directory or project.

The earlier eleven-file tooling review is recorded separately in
`implementation-audit-file-review-2026-10-28.md` on the native integration branch.
This batch includes fresh reads of the shared atomic/PDF helpers previously
examined during their implementation, rather than claiming twelve entirely
unreviewed files.

## File identities and dispositions

All paths are relative to `tools/`.

| File | SHA-256 | Disposition |
| --- | --- | --- |
| `__init__.py` | `ef92f93060a1b6f69b683d6bb431a52dcf86ffd25b9ed1c45c55494420f11cce` | Comment-only package marker; no behavior to certify. |
| `atomic_json.py` | `2d0f47f50c08064b72a00ab38201974b7d8fe9761f06eac5fbeb0b26c2e6a4c3` | Lines 13-37 serialize before mutation, use a unique sibling temporary, fsync the file and replace. No directory-durability claim. No new release defect identified. |
| `pdf_process.py` | `d7050a96a05228c98b0d103ea4f89a11ebf663d0879776a4a804bdb7ee94be29` | Lines 12-49 bound commands, preserve document context and reject missing/zero page counts. No new finding. |
| `live_process.py` | `360247c89b9c55760145dbd0716b51341a9cf9127cc4ed465afea48eff376a48` | Finding A below. Process-group cleanup, wait4 ownership and RSS platform conversion were traced; RSS is not model-server/GPU memory. |
| `build_layout_masters.py` | `fb37a6843c9d2825fc6a641a08afdaab79369d706ab8831f0eb854cdb7157de1` | Lines 215-273 close the PDF in finally, extract geometry without text and write JSON directly. Atomic-output reuse is a maintainability proposal, not a reproduced corrupt report. Geometry-role heuristics are not fidelity certification. |
| `calibrate_student_responses.py` | `81e2060326e06c7d3283f6ca2b8e57d225a31578de879cfa9fbb8968e32e6c81` | Finding B below. Delegates consent, encryption and calibration to Core; those implementations are not newly cleared by reading this CLI. |
| `reconcile_french_nsi_archive.py` | `27e52459d46641979bd942d30166e13c540424c717139a9c454c95b2b8649f99` | Lines 20-26 use a fixed `.new` sibling. Unique atomic helper reuse is proposed below; no concurrent reproduction was run. |
| `french_reference_corpus.py` | `653ee3c0b1cdcd411df0ae250676d4519ad8deab2e5a7f003eae5d4df8a43f1c` | Explicit compatibility exports and delegation to Core main; no new finding in this thin entry point. Core corpus code was not completely reread. |
| `record_occitanie_demo.command` | `b28df6cd59b8780cdb3f932b77be969b9439cf6f4d4c9d395031720e59781a19` | Interactive recording and review prompts, lock-screen refusal and error propagation read completely. Uses a fixed output movie name; preserving an existing recording is a usability improvement, not evidence that a recording was overwritten. No recording or UI action performed. |
| `run_french_nsi_qualification.command` | `8f44a723765044d0441ff16251067085a146a78063d4b2d2beab2de17206b32c` | Checks Python/reference index and execs the benchmark with quoted paths and a finite fixed timeout. No new wrapper finding. Model defaults are not qualification evidence. |
| `run_french_nsi_reference_reconciliation.command` | `fb83b4b7bd91e2786dfd044def662a4f8c86810c120bdebb08b20d2e40a7bfa9` | Lock-directory acquisition and cleanup surround the reconciliation sequence. A stale lock after SIGKILL requires operator recovery; do not automatically remove another live owner's lock. No fresh run performed. |
| `calibration_common.py` | `8fa4578fd886fa36d740ba41776e35ca76023b3c55aa29f7fb24db3d74f98859` | Complete post-P6-import read. Preserves ordered raw fingerprints and scoped source-only/public-content identity. Derived workings excluded; no full printed-page or semantic-novelty equivalence claim. Earlier T8 tests remain separate evidence. |

## Actionable source findings

### A. Nonfinite timeout can defeat bounded process execution

`live_process.run_backend`, lines 47-49 and 72-84, accepts its timeout without a
finite-positive check. With NaN, the deadline comparison is always false; infinity
also prevents timeout termination. A call-site trace found the French benchmark
accepts `--timeout-seconds` with `type=float` at line 1102 and passes it through at
1023 without finite validation. This is a concrete control-flow defect, not a
fresh runtime reproduction. Add a failing fake-process test requiring refusal
before log truncation or spawn, then validate a real non-Boolean finite positive
number at the shared boundary. Preserve normal timeout cleanup and RSS semantics.

### B. Secure CLI action flags can select the wrong operation

`calibrate_student_responses._run_secure`, lines 112-137, handles delete/export
only inside `if dataset_id`. Without an ID, valid import arguments cause import
and aggregation even when `--delete` or `--export-encrypted` was requested.
Supplying both actions with an ID silently chooses deletion first. These are
source-confirmed routing defects; no real dataset was imported or deleted.
Validate mutually exclusive actions and require a dataset ID before constructing
the store or loading input data. Test with fake stores and temporary input files.
Do not treat an invalid deletion command as consent to import a new dataset.

## Reuse proposals, not additional release defects

The reconciliation writer's fixed `.new` path can collide under direct concurrent
CLI calls. Its shell wrapper currently serializes its own invocations, not all
possible callers. A focused concurrency/failure test should precede replacing
this writer with the existing unique-sibling atomic helper, preserving JSON
bytes. The layout-master writer can use that helper too, but it has no reproduced
partial-write incident in this review. Neither proposal requires a new generic
framework or altered corpus policy.

No builds, model requests, recordings, full suites, release submissions or
teacher/learner calibration were performed. Findings require separate TDD fixes
and a new fixed-source acceptance gate before being marked resolved.
