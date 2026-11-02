# Paper conformance and supporting file review

Internal engineering review, 2 November 2026. Three Codex reviewers read the
seven files below through EOF at `a2058bd5`. For `layout_conformance.py`, the
complete 593-line baseline was followed by review of the entire 29-line repair.
The final hashes below were checked again after integration at `8c3517f3`.
Related callers and tests were inspected selectively, not given whole-file
attestations. This is not teacher review or paper qualification.

| File | Lines | Final SHA-256 |
| --- | ---: | --- |
| `macOS/Keldin/Services/UKArtifactPublisher.swift` | 119 | `3bae77bab523657c214c2d734c3ded751b89f793d42973bc2ba4cd1c07336303` |
| `macOS/Keldin/State/ModelCoordinator.swift` | 66 | `c50c69a304a7bcbe52b267377adc5ae1c2b6a5ae39751116de2e911650fca462` |
| `macOS/Keldin/State/SettingsStore.swift` | 140 | `009442ceb4a488eee3995963b139c8ca85c56616a348f42e306a36f87e88c9bf` |
| `Backend/Core/subjects/accounting.py` | 761 | `8e5284e29760deff8b84e3d18c64af6e8e7eb12f0265bb07a68d077a46c83a46` |
| `Resources/computer-science/ocr/generator/ocrcsgen/generator.py` | 645 | `d0d1ad4d464546c32f83f94637b91cea185d067d9ce3a3b0fa9f532e1b180d5c` |
| `Backend/Core/accounting_scheme_content.py` | 692 | `84152c930dca54e1d887b57a2750d269361be50f6e21032f98d009fa0e11a8ac` |
| `Backend/Core/layout_conformance.py` | 622 | `287f96a5f07f79f886569924fdc9a148269ecd196067dcfee481a19179f666c2` |

## Finding and repair

Edexcel content-driven scheme validation checked that each assessed page had
known credit and that every expected statement appeared. It did not reject a
copied assessed page. On owned copies of a fresh 25-page Paper 1 scheme, inserting
its page 4 before the final continuation produced 26 pages and still passed
with complete printed credit and no reported padding. The matching assessment
and all original files remained unchanged. This was deliberate test damage;
no current generated duplicate was observed.

Commit `70944e6ac7c8d9ed8eb2978b139ca338cce3177f` adds an Edexcel-scheme-only
rendered-body fingerprint. It uses the renderer's existing row-box limits:
85 points from the top and 54 from the bottom, across the full page width.
Ownership headings, figures and all assessed rows remain inside that region;
header/footer furniture is outside it. Dimensions and a SHA-256 of the 72-dpi
body raster distinguish pages. A repeated assessed body refuses conformance.
The first three front-matter pages and a recognized final colophon are excluded.

This imposes no one-page-per-question rule and does not compare question-paper
working pages, different papers or generation history. Distinct continuations,
ownership headings and vector/image content remain valid. The check concerns
exact rendered duplicates, not semantic similarity or general PDF tampering.
Stored files and package/state readers are unchanged; content revalidation now
refuses repeated assessed bodies rather than treating them as extra coverage.

Three regressions first reproduced copied assessed, copied continuation and
footer-renumbered pages. The final focused Edexcel/layout group passed 119 tests.
Positive controls cover all three components, multi-page credit, different
figures and different owners; real ownership-heading bounds fit the body clip.
Ruff, formatting and diff checks passed. Warm measured fingerprint medians were
0.017 to 0.020 seconds per component; the first cold call took 0.274 seconds,
including renderer import. These are local observations, not generation-speed
or device-wide performance claims.

Local diagnostic and test evidence remains under the author's ignored
`tmp/nov2-edexcel-duplicate-pages/` directory. The original accepted copied-page
probe remains in the capacity worktree at
`tmp/nov2-edexcel-duplicate-page-probe/summary.json`.
A different agent reviewed the bounded repair and tests and found no actionable
P1/P2 issue. It did not execute a second test run.

## Other complete-file scopes

- Native publication, discovery and settings: checked staging and hash
  verification, cleanup, discovery revisions and observation, credential-save
  failures and preference-only saves. No further concrete P1/P2 was established.
- Accounting and OCR construction: checked source-owned financial formulas and
  output roles, the budget premise boundary, matching prompt/credit construction,
  calibrated-task exclusions, preserved random draws and finite point selection.
- Accounting scheme content: checked policy admission, printed credit totals,
  ordered content, page ownership and historical rendering boundaries. The
  earlier positive-credit repairs remain in place.

These conclusions apply to the exact files and scopes above. They do not finish
the wider file audit or establish live model accuracy, arbitrary-seed coverage,
learner timing, accessibility conformance, corpus rights or Store approval.
No inference, paid request, UI operation or global setting change was performed
for this review. Full-suite, packaged and protected-CI acceptance of the integrated
repair remains a separate release gate.
