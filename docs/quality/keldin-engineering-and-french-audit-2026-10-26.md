# Keldin engineering and French paper audit — 26 October 2026

## Scope and verdict

This is an engineering audit of PR #79 and the public V32 French route, not an educational approval. V32 provides three finite, app-authored whole-paper families. It does not call an AI model. Experimental V33 expression/postfix authoring is tested but is not the public default. The earlier V15–V31 live-model holds and failures remain valid historical evidence.

The repository-wide automated suite passed **3,515 tests, with two skips** on `3894ad3`. The following packaging-health-check extension at `267ba97` passed its 14 targeted tests. Native tests passed **79** after the test-host startup isolation fix. Ruff, Python compilation, shell syntax and release-compliance checks passed. These checks cover the repository; manual review was risk-based, concentrated on generation, provenance, persistence, rendering and changed app paths. They are not line-by-line proof of every function or a measured coverage percentage.

## Fixes found during acceptance testing

- Reject malformed V33 checkpoint failure records before accepting saved work; retain the invalid file for diagnosis.
- Stop retrying an identical deterministic V32 case after originality refusal. Legacy model retry behavior is unchanged.
- Bind every printed page to exactly one correct footer and page counter. Current whole-case PDFs say Keldin; historical Paper Creator footers remain accepted for replay.
- Clarify routing question 3e: the incorrect in-place algorithm happens to return the same B value in this case. Numerical agreement does not validate its forbidden read of the current A value.
- Keep the first E2 prompt together in enlarged print. Allocate database-table widths to preserve identifiers such as `temperature`, without reducing the requested text size.
- Remove unused model-selection state from French requests and readiness presentation. Keep the finite catalogue and teacher-review limits visible.
- Isolate the XCTest host's coordinator as well as individual tests. Tests use private preferences, temporary history and an in-memory secret store, rather than loading or pruning normal paper history.
- Fix a packaged-runtime failure found through the app: correction code inspection and catalogue hashing require the French source modules. The bundle now includes only those `.py` files, not caches or retained evidence. Its build-time health check renders all E1/E2/E3 families and reads all three catalogue fingerprints.

## Official-paper comparison

Comparator: [2026 Métropole, day 1](https://eduscol.education.gouv.fr/sites/default/files/document/26-nsij1me1-128190.pdf), 16 A4 pages, 36 numbered questions, 3 h 30. Local SHA-256: `275b050d7577142794bb579b66ffc08fe7742a70c943a632eebd32701994310b`. All 16 pages were read and visually inspected. The official file remains local reference material, not an app resource.

Three public CLI runs, seeds 270100–270102, succeeded sequentially in the same output history. A fourth, 270103, was refused for previous-generation similarity, retaining one failed attempt and publishing no paper. History was not cleared and thresholds were not relaxed. These are application-owned runs, **not new live-model qualification**.

| Seed | Sustained cases | Normal subject / correction | Enlarged subject / correction |
|---|---|---|---|
| 270100 | Ordered-tree rank and interval; sensor revisions; stale-route recovery | 7 / 18 pages | 11 / 29 pages |
| 270101 | Expression-tree revisions and dependencies; booking capacity; lock-cycle recovery | 7 / 17 pages | 10 / 28 pages |
| 270102 | Prefix decoding and transcoding; chronological stock audit; ordered message delivery | 8 / 18 pages | 12 / 29 pages |

Each paper contains 34 questions across three independent exercises, 210 indicative minutes, exactly 18 technical points and a separate 2-point indicative French-language assessment. Questions move from interpreting sources through traces, state revisions, complete function construction, SQL, counterexamples and justification. The printed answers and rubrics were checked against the app's independently tested algorithm/SQL evidence. No official marking scheme was newly compared.

The generated cases now have connected reasoning obligations rather than isolated short prompts. They remain more compact and more table-led than the comparator, which includes substantial diagrams and scaffolded code. Page count does not establish equal demand. Both formats direct candidates to answer on a separate copy; blank working pages were not added. Sparse exercise/correction tails remain, particularly when keeping a prompt, answer and rubric together. No clipping or missing content was found in the reviewed pages. The split first E2 question and broken enlarged-table identifier found during inspection were repaired and rechecked.

Every page of the three normal subjects/corrections and enlarged subjects/corrections was reviewed across the retained iterations; changed pagination and table pages were re-reviewed after the fixes. Complete ordered-content, A4, page-counter and footer validation passed for all 12 final rendered copies. Normal/enlarged copies in `layout-final` are re-renders of the frozen packages, not additional independent generations.

Educational fidelity remains **HOLD**: teacher review, actual learner timing, difficulty and mark calibration have not been obtained. Three families do not establish unlimited usable variety, full curriculum coverage or quality independent of an AI model. The public workflow explicitly discloses that limit.

## Retained artifacts

Ignored root: `tmp/pdfs/french-final-audit-20261026/`. `baseline-papercreator`, `normal`, `enlarged`, `frozen` and `layout-final` preserve the iterations. `frozen/normal` contains the three public runs, manifests and checkpoints; `frozen/repeated-family-270103.jsonl` records the refusal. `layout-final/layout-summary.json` gives absolute paths and hashes for the final rendered copies below. Previous live attempts, official references, old source identities and the local branch recovery bundle were not deleted.

| Final rendered copy | SHA-256 |
|---|---|
| 270100 normal subject | `2d175724778cd4141150f2e4705b8abe339b8532cb33614d1048a16923a352b5` |
| 270100 enlarged subject | `783e82afcc6195063d779684123d3a55ecb23ae1f5ac76107b8683fe34f58c81` |
| 270100 normal correction | `4347ba735fc8605c892591344819d33778718b52e364dbc51bef8f4e9bf6ded5` |
| 270100 enlarged correction | `062ad0d1f144e2c57bbd623a6abb550c73bd81c233c20d7946b88e41d10c2ffa` |
| 270101 normal subject | `59b2c5bf94207a19a08023d998a51f85e04ced10cb915af8afc1da1bcb9621a1` |
| 270101 enlarged subject | `5057187dc5824cfde29330b2a240de4305c332fe42adf33c2e90d17f27e59626` |
| 270101 normal correction | `10d3c76cbd658ff2c0cfec4919b8edc5f5e783ec47b7d0093a501da7b6c7a91b` |
| 270101 enlarged correction | `6c40f354be0d7b344bcab7014e6c1e4ae0c54c9f8f595d66a2a003704f09150d` |
| 270102 normal subject | `43a68e505cf8925d3abfd4e70a8ad5b19c1dbe3d8e24ad8cd1542f226b650cad` |
| 270102 enlarged subject | `f1b7e0ea848e7748a4c85090b731720f5eaeb2fcf3ab41d1fbd509beb6100514` |
| 270102 normal correction | `974b7d585f2a96911ad39905a89f857cd76ed74a5f5801c52e29658d8d3d7b9c` |
| 270102 enlarged correction | `14fcd70c55bf11ab185fb15d4f76f0f46cf708007ed0ed1b2f9e1158c9ffefb6` |

## Release boundaries

Native acceptance used the bundled helper at `267ba97`: creating a French draft with the existing local reference index succeeded without model setup; Documents displayed both the seven-page subject and 17-page correction. History recorded completion, restored the French configuration and retained the job after quitting and relaunching. The test destination was `tmp/user-acceptance-20261026`; Downloads was restored afterward. The failed packaging attempts remain visible as failed jobs rather than being erased. The completed manifest is still `unreviewed_draft`, seed `1897192199`, implementation SHA-256 `59b8d28114c27b550dbbad387d0dade2344a439eba1ae7da828ec9a414019311`.

The UI-created subject SHA-256 is `ac58eb8526379bdc6b13d50a5d942137b3830e3d926703a0937a53ebaf79a832`; correction `32f1f1a837acc5f6ca8e060ab270ce2810e93aaad082c6a78605b08499f5338f`; assessment package `d3a967036d86bb667a86256b485d31a521c933e26ed71778caba9c7c261e4cfa`.

The App Store-mode Release preflight passed: compliance gates, plist lint, strict bundle signatures, app/helper sandbox entitlements, inherited helper sandbox, hardened runtime and absence of bundled official references. This is a local build preflight, not a distribution-signed upload or Apple review. Printing, external-provider live UK generation and a new final live UK/French matrix were not performed in this acceptance run; their existing automated contracts do not substitute for fresh live evidence.

The [corpus rights audit](french-nsi-corpus-rights-audit-2026-10-11.md) still does not establish per-document redistribution permission. No official PDF is bundled. Independent accessibility testing, teacher/learner evidence, distribution signing and store review remain separate release gates. Competition eligibility, contact and funding details require the user. No examiner, Apple, school, regional or prize approval is implied.
