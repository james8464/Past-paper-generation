# Hosted generation and French full-file review

Internal engineering review, 30 October 2026. This records complete-file reading and reviewed fixes, not whole-project completion or paper qualification.

## Coverage and exact bytes

The reviewers read every line through EOF in the five backend files below. The parent reviewed the subsequent fix diffs and their tests, then read the four listed configuration resources completely. This is internal review; authored sections also received self-review, not an external attestation.

| File | Final lines | Final SHA-256 |
| --- | ---: | --- |
| `Backend/Core/providers.py` | 1809 | `f6df0a30db0e7ed97e5e55cf89e677d15310ae9dd0f3e40faba60d76698c8157` |
| `Backend/Core/mlx_batching.py` | 209 | `698a8f535389e9ca20211474efe9cbec98d393c95e1e4a6cbab39738e93434c6` |
| `Backend/Core/france/llm_pipeline.py` | 1038 | `29f81375b79c230791059059436fd4f80c9e0bcb2bd6d7deee540073f8a1638d` |
| `Backend/Core/france/llm_runtime.py` | 232 | `a00b33867a94a757c2c2b346b9e86166067744c80da2a669873e5c63ca4304e1` |
| `Backend/Core/generation_requests.py` | 307 | `33132f38e89c63b1cf4a97576fe81f9f67d15b209b38add6a44cc7efcaeb759f` |

The provider baseline was read in full at SHA-256 `23a606149c171cbf02c773aed493df2dd913dd6ec34f5cdfd5bf9f85464f32e9`. Its only subsequent change was the four transport arguments described below. The pipeline baseline was read in full at `94217fad3a8eb481532b6e6b102d9c3270e42bd4fe9ef9aa3959d16b8923c36c`; the admission fix and contract-capability descriptions account for its complete subsequent diff. The other three files stayed byte-identical throughout their full-file reviews.

| Configuration resource read completely | SHA-256 |
| --- | --- |
| `macOS/Keldin/Assets.xcassets/BrandAccent.colorset/Contents.json` | `2e1ef28e55fc721e195b1f0aa7caddf27b489eb4bc38f95a0a298d0eeff76874` |
| `macOS/Keldin/Assets.xcassets/ForegroundAccent.colorset/Contents.json` | `277705fd066f1993b212e95456d38e63d9a07cc4ef500fc1a17b08c239dfec5c` |
| `macOS/Keldin/Info.plist` | `6d3e3740f49cdea1c60243835561e219dcebf766c7de71dda250c8697a43d958` |
| `macOS/project.yml` | `5d3b91b929bd28bdcfb33b461cd19ffdc20579229b13d13505c5ca13c9a79811` |

## Findings and repairs

### Credential-bearing redirects

OpenAI and Anthropic calls did not use the existing fixed-host transport or exact-key redaction. Python's default redirect handler can retain credential headers when following a redirect. Local and mocked tests reproduced six redirect cases and two unredacted key echoes without real credentials or external requests.

Both callers now specify their fixed HTTPS vendor host and the exact credential to redact. Redirects are refused, including same-host redirects. Ollama behavior, certificate validation, retries, budgets and response handling are unchanged. The scoped transport/provider suite passed 159 tests. Source and test changes are in commit `73c635bd`, integrated as `f9409bc8`.

### Empty independent answers

The blind-answer schema accepted whitespace-only strings. The same schema is used for live response admission and saved-review validation, so both paths now require a non-whitespace character. This does not establish that a nonempty answer is correct. Negative correctness, completeness, curriculum, language, autonomy and rubric checks still refuse publication.

### Code in prose-only material fields

A short Python function in a table cell passed the previous admission and PDF checks, but the prose renderer flattened its indentation. A real four-page PDF reproduced the problem; page 2 was rendered and visually inspected with Poppler.

V36 now audits material headings, table headers/cells and graph labels alongside the existing printed fields. These prose-only surfaces refuse code fences and recognizable Python suites with the existing bounded formatting-retry policy. Unsafe code remains a hard refusal. The author brief points to the supported context, question and answer code surfaces. No generated content is moved or rewritten, and the historical readers, generic renderer and executable interpreter are unchanged.

The two admission findings produced 13 red cases before repair. The fixed-source regression/PDF/runtime suite passed 172 tests. Commit `e2955eb0`, integrated as `a3a4ada5`, contains the fix and focused cases. A later root integration run passed 210 targeted tests across these admission, provider, budget and review boundaries.

### Undocumented proof capabilities

A later live model supplied a complete function as a `python_trace` contract. The bounded interpreter does not support function definitions, but the authoring schema described that field only as a string. The question and numerical expectations must be reviewed separately from this unsupported verification claim.

V36 schema descriptions now state the exact Python subset and limits, SQLite setup/result restrictions and shortest-path binding/distance-only scope. The author is told to choose `human` when those capabilities do not cover the task. The interpreter, hard failure rules and historical schemas are unchanged; no failed contract is silently downgraded. `verification.py` was also read to EOF to check the descriptions against its implementation. The capability follow-up passed 166 focused tests before root integration.

### Native accent roles

The previous bright global accent gave configured opaque white-on-fill ratios below 3:1. Native selected controls now follow system-managed accent roles; the icon/artwork palette is retained, byte-identical, as `BrandAccent`. Explicit warm link and chart foregrounds use a separate appearance-aware asset.

Static sRGB tests cover white and grouped light surfaces at RGB 246 and 236, plus dark surfaces at RGB 30 and 44. A red case caught the original light foreground failing on a grouped surface; the revised light variants meet 4.5:1 across those tested backgrounds. These are configured opaque-colour calculations, not measured Liquid Glass pixels. Native light/dark and both Increase Contrast appearances were checked separately, and original system appearance/accessibility preferences were restored.

The complete project and Info files retain macOS 15/arm64 scope, the personal development team, hardened runtime, explicit direct-versus-Store settings and bundled-helper build. Script sandboxing during packaging is distinct from runtime App Sandbox. This review did not create signing identities, approve rights, validate Intel distribution or submit to the Store.

## Other reviewed boundaries

- Typed requests keep schema and generation metadata separate from prompt text. Schemas are copied through finite JSON serialization; invalid sampling/batch metadata refuses.
- V36 generation and replay share review validation. Every retained blind note needs a complete typed disposition; blocking notes or question defects refuse. Advisory warnings retain the original concern and rationale and are recomputed on replay. This is model review, not independent proof.
- Three exercise identities and exactly 18 technical plus separate 2 indicative language points remain mandatory. Self-reported difficulty labels and timing estimates are not learner calibration.
- Source, references and local-model hashes are checked again before publication. Hosted model revision bytes remain unavailable. File staging and final directory rename prevent successful events for partial PDF output.
- Failure diagnostics retain bounded explicit evidence with redaction and restricted permissions. They do not automatically copy arbitrary prompts or answers.
- Printed Python fragments are not executed. The independent bounded `python_trace` interpreter and its rejected statements remain separate.
- MLX batching retains bounded coalescing, ordering and cancellation on its model-owning worker. Frozen builds still refuse runtime package installation and remote model code.

## Limits and maintenance

Full-file reading is not a proof that no defect remains. Current-source full tests, protected CI, installed-app checks, live model qualification, rights clearance and Store distribution signing are separate requirements.

A cancellation immediately after a complete private output-directory rename can leave an orphan complete folder without a successful history event. This is not a claim of partial PDF publication. A long-lived MLX client can retain its idle runner/model until explicit cleanup; the app currently bounds that lifetime through its per-job helper process. Neither observation was demonstrated as an installed cross-job leak or incomplete-output success.

Possible later refactors are extraction of review/evidence rules, profile-warning construction and a shared printed-surface inventory. They are not included merely to change style, and must preserve JSON contracts and historical replay. The broader implementation ledger still contains unreviewed files; this review does not close them.
