# Keldin user acceptance — 27 October 2026

## Result

Computer-control testing reproduced failures that the source-tree tests had missed. This update fixes MLX setup, instruct-model formatting, packaged UK marking policies, document selection, replaced-file previews, multi-page printing and safe PDF export. It does **not** qualify every model or establish that the app is ready for public educational use.

The installed direct build is `/Users/james/Applications/Keldin.app`. Test outputs remain under the isolated checkout's ignored `tmp/user-acceptance-20261027/`. Previous builds were moved to Trash, not permanently deleted. User history, downloaded references and earlier paper evidence were retained.

## Failures and fixes

- MLX setup loaded a model, then rejected its cache because the Hub client expected repository files that mlx-lm intentionally does not download, including README.md and .gitattributes. Local resolution now uses mlx-lm 0.30.2's inference-file filter. Generation still forbids network downloads outside approved setup; missing inference files still require setup.
- MLX instruct models received raw prompts. The provider now applies the tokenizer's chat template when available; base-model behavior is unchanged.
- The packaged UK preview failed because `level-of-response-policies.json` was absent. It is now included in the helper and build fingerprint. The bundled health check parses it and fails on missing or invalid policies.
- Successful generation selected the oldest question paper. It now selects the newest. A replaced filename receives a fresh document identity, the PDF view reloads that revision, and externally requested selections propagate into the preview. Restoring the document library removes duplicate paths without deleting job records.
- Separate current-generation artifacts from the document library. Completion records and sandbox exports now use only files emitted by that operation; older library PDFs cannot be attached to a new job's provenance. The final native Accounting preview stored exactly its four artifacts. Ambiguous historical artifact identities and reused paths no longer enable Copy Provenance; the original records remain unchanged. Teacher review records already written beside a selected manifest are not exported as new paper bundles.
- Printing used a zero-sized PDFView and offered one page for a multi-page document. PDFKit now creates the whole-document print operation. The corrected native dialog showed page 1 of 18 for the French correction. No physical print job was sent.
- Export removed an existing destination before reading the source. Selecting the source itself could therefore delete it. Same-path export is now a no-op; other exports read first and write atomically. Tests also verify that a missing source leaves an existing export intact.
- The first clean-sandbox Economics preview exposed an axis-label/MCQ-mark collision. An independent packaged scan of seeds 0–23 reproduced it at Edexcel paper 1, seed 22. Diagram layout now reserves the axis caption and its descent before the following prompt. All 24 seeds pass packaged validation after the fix; seed 22's rendered page 6 was visually checked. The native sandbox job that originally failed was duplicated with its original seed and completed successfully with the corrected helper.

Each regression was observed failing before its fix. Native regression tests cover newest/replaced documents, restored-library deduplication, all-page printing, same-path export and failed-source export. Python tests cover filtered offline snapshots, chat templates and missing bundled marking policies.

## Checks performed

| Workflow | Evidence |
|---|---|
| Installed MLX runtime | Bundled `mlx-status` reported available |
| Guided MLX setup | Original failure reproduced; corrected setup continued into live drafting |
| Real local MLX inference | Cached Llama-3.2-3B-Instruct-4bit returned the requested JSON object through the corrected provider |
| Full live MLX Accounting paper | **Failed validation**: question identifiers did not match the blueprint; no live paper published |
| Cancel generation | Running MLX attempt stopped; History retained its cancelled state |
| Duplicate configuration | Restored Accounting paper 1 and Apple MLX from the cancelled job |
| UK packaged layout previews | All 21 advertised paper/practice routes passed through the installed helper, with expected output events and no errors; these are placeholder previews, not live model qualification |
| Native Accounting preview | Created both PDFs and packages; corrected app opened the new Accounting paper rather than the older French PDF |
| Native French generation | Created a V32 draft without AI setup; opened the new French PDF |
| Documents | Paper/correction selection, Quick Look, print dialog and export exercised; exported correction hash matched its source |
| Navigation | Subject search, OCR selection, unavailable Chemistry state and return to the full list exercised; unavailable subject exposed no Create action |
| Settings | AI, Output and Privacy panes opened; temporary output folder selected through the native chooser |
| Benchmark | Built-in 30-second test completed and displayed results; this is hardware evidence, not paper-quality qualification |
| Automated suite | 3,518 backend tests passed, two skipped; 85 native tests passed |
| Distribution build | Static App Store-mode Release preflight passed. The original ad-hoc identity failed library validation; personal-development signing of that identity stalled in OS sandbox initialization. A separate development-signed test identity launched, replayed its failed preview successfully after the diagram fix, then generated and externally exported paper 2. Production identity/migration and distribution upload remain unqualified |

The tests did not send physical print jobs, create teacher attestations, delete the user's reference corpus, change API keys or purchase model/API credits. Fresh live OpenAI/Anthropic generation, every Ollama model, independent VoiceOver testing and distribution-signed App Store upload were not performed. The acceptance inventory is not a claim that every possible state or button combination has been tested.

### Sandboxed launch failure

An actual App Store-mode launch exposed a limitation that static signature checks do not detect. The ad-hoc hardened helper could not load its nested Python dylib because library validation requires a matching signing team. No library-validation exception or sandbox bypass was added. A copy signed locally with an existing personal Apple development identity passed strict signature verification, but then stalled in `_libsecinit_appsandbox` before app initialization; its one-second process sample is retained in `/tmp/keldin-store-startup-sample.txt`. Xcode's separate attempt to use that identity also failed certificate/team selection. Neither result qualifies a distribution build. The stalled test process was stopped, existing containers were not removed or reassigned, and the working direct build was restored. A correctly provisioned distribution-signing configuration and a fresh sandboxed runtime test remain required.

A diagnostic copy used a separate `SandboxQA` identity, the same personal development signing team, and a new app container. It launched and completed onboarding without disabling any protections. Its first Economics preview was correctly rejected for the diagram collision described above. Updating only that copy's packaged helper to the corrected build, preserving its failed history entry, allowed Duplicate Configuration to replay the original seed successfully. A second preview, paper 2, exported through a security-scoped folder chosen in the native dialog. The external test folder contains exactly paper 2's question paper, source booklet, mark scheme, assessment package and manifest; no earlier paper 1 artifacts leaked into the export. This is clean-container development evidence, not validation of the production bundle identity or an App Store-signed archive. Existing production containers remain untouched.

## French output retained

UI-created package: `nsi-2027-1535248359-8dde7ff64a15`, seed 1535248359, public application-owned V32. The manifest remains `unreviewed_draft`, with exactly 18 technical and a distinct 2 indicative language points. No live-model qualification is inferred.

- Subject SHA-256: `d1804d7fd610b22a8b184955b703c39928251d255c2ea944477966d853bb3bf6`.
- Correction and exported-copy SHA-256: `7944f1b76eadf32c2eaff015f45b8cc8f85692445bebf4136ebdf9e4026b7eec`.
- Assessment SHA-256: `4930fd5c873aee4a220ee5fa8305a38a3f0eec11b01b0281c831fa3a734e5260`.

There were no French authoring or layout changes in this update. The [26 October page-by-page comparison](keldin-engineering-and-french-audit-2026-10-26.md) and its manual fidelity **HOLD** remain in force: three finite families, compact/table-led response flow, no teacher/learner timing and mark calibration. No new final expensive live UK/French matrix was run.

## Remaining release gates

The default MLX 3B model has not passed full-paper validation. A successful setup or small JSON request must not be presented as evidence that it can author a valid complete assessment. Do not weaken identifier, answer, marking or second-pass review checks to make it pass.

Older UK layouts still display Paper Creator branding; this update does not rewrite their calibrated cover masters. Per-document reference rights, independent accessibility review, teacher/learner evidence, distribution signing and store review also remain open. No Apple, examiner, school, regional or prize approval is claimed.
