# Model download and packaging input review, 2 November 2026

## Confirmed defects and repairs

The native Download request captured a model name but not its selected Ollama endpoint. Its CLI child inherited `OLLAMA_HOST`, so selecting port 11435 could still download to port 11434 or another inherited destination. The confirmation now captures both values. The parser passes the captured endpoint through the existing local-only validation before command lookup, and only the owned child receives an environment copy with that explicit host. Discovery's existing default-server CLI fallback is pinned too. Failed custom-server discovery still does not fall back elsewhere. Store restrictions, remote-generation consent and cancellation ownership are unchanged.

Nine fake-only regressions failed before this repair, with 24 passing controls. The author's 180-test selection passed. Root's combined endpoint, child-lifecycle, recommendations, review and packaging selection passed 179 tests. Different selections are recorded separately, not added together. The native captured-endpoint regression awaits the integrating native run. No model was downloaded or queried.

The packaged backend also omitted bundled font data from its reuse fingerprint. A changed font therefore kept the same cache key. Separately, an unreadable required input could print an error and still return a successful partial fingerprint. Root reproduced both defects using the actual extracted Bash function in a private fixture. The repair hashes the entire packaged font directory in sorted order, explicitly propagates input/scan failures and checks syllabus enumeration before consuming it. No signing, entitlement, runtime-installation or PyInstaller payload policy changed.

The final packaging tests passed 14 cases after five failures and nine passing controls against the original function. They exercise font-byte changes, stable enumeration order, missing JSON/syllabus inputs, failed registry discovery and failed directory scans. These fixtures use owned temporary files, not the installed application or user documents. Earlier failed and superseded diagnostics are retained.

Both repairs received separate author and independent changed-path reviews. The integrating pull request still requires fixed-source Python tests, native compilation/tests, direct Release, Store preflight and protected CI. Earlier results at `db730dd5` certify only that earlier source. Offline PDF preservation is not live French-paper qualification.

## File-level evidence

The integrating ledger binds each reviewed file and this document by exact SHA-256. Scope is explicit below. Dependency traces and changed tests are not automatically whole-file attestations. Private reports remain in the documentation and identifier worktrees under `tmp/nov2-*-eof-audit*.json`.

| Scope | Complete files or composed review |
| --- | --- |
| Shared endpoint and CLI child | Root read the complete current `Backend/Core/cli.py` and `events.py`. The author read all of `ollama.py`, then its complete routing repair; independent review covered all seven changed files and relevant callers. Root read the full 59-line download-presentation source and the coordinator's complete seven-line repair over its previously reviewed, hash-matching baseline. The coordinator was not reread in full. |
| Packaging | Root read the entire original 230-line build script and 205-line integrity test, then every repair and test addition. Independent review covered the complete final test file and script delta. |
| Native/build support | Root read all of `bootstrap_backend.sh` (17), `build_apple_intelligence.sh` (61), `run_app_macos.sh` (73), `diagnose.sh` (40), `xcbuild.sh` (146), Apple helper `Schema.swift` (150) and `CapabilityProbe.swift` (27). The launcher gives a Bash argument error rather than friendly usage when `--app-path` has no value; this is retained low-priority developer-tool feedback, not a claimed fix. |
| Active provider policy | Author read all of `model_recommendations.py` (120), `model_review.py` (688) and the original Ollama implementation (182), with the complete final Ollama delta reviewed separately. Memory recommendations are not empirical model qualification. |
| French live pipeline | Reviewer read all of `france/llm_pipeline.py` (2,065), `llm_runtime.py` (280), `llm_pdf.py` (289) and `recovery_evidence.py` (253). Public V36 remains model-authored, with bounded retries, blind candidate projection, refusal histories, staged validation and explicit unreviewed statuses. No new confirmed P1/P2 finding arose in these four files. |
| Smaller Core contracts | Reviewer read all of `computer_science_audit.py` (135), `computer_science_reference_solutions.py` (87), `family_contracts.py` (81) and `france/code_fences.py` (80). These contracts and reference snippets do not prove arbitrary model answers or observed learner timing. |
| Maintenance/test helpers | Reviewer read all of `tests/support/edexcel.py` (23), `solver_responses.py` (18), `tools/build_supported_layout_masters.py` (166) and `validate_generator_migration.py` (359). Migration preview executes only the first advertised paper per family, not the full live matrix. |

The source-bound ledger supplies exact identities; line counts above describe the reads performed, not permanent file-size promises. Other dependencies and the native regression were inspected selectively. The native regression's changed paths are reviewed, but the large test file remains pending for whole-file review.

## Limits

This is bounded internal implementation review. The PDF checks establish content, vector and code consistency, not universal visual legibility or semantic correctness. Recovery hashes establish consistency, not authentication of hostile fabricated packages. Model judgments remain fallible; human-only verification contracts are not automatically proved. Existing tests inspected during read-only audits are not new executed results.

No paid inference, model-output repair, answer hardcoding, teacher record, learner timing, accessibility certification, whole-project audit completion, official-paper equivalence or Store approval is claimed. French live-paper qualification, third-party rights, personal Distribution signing and the applicant's submission details remain separate.
