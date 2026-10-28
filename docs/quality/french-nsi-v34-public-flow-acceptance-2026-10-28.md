# French NSI V34 public flow acceptance

## Scope and decision

The candidate public application-owned route now uses V34 and its four finite
paper families. Explicit Ollama diagnostic calls retain V32 for historical
compatibility. No AI model produced the papers in this acceptance run.

This change connects the previously reviewed V34 source, print policy and family
selector to the command line and native app. It does not alter exercise content,
credit allocations or originality thresholds. The app records the selected seed
from the published manifest, including when the preferred family was already
used. Invalid or absent publication metadata prevents a successful history entry.

The four-family catalogue is suitable for further non-official practice use with
its stated limitations. Full syllabus coverage, equal difficulty to an official
paper and calibrated completion time have not been established. Teacher review
and empirical calibration remain `not_run`. The user requested internal review
instead of unavailable teacher review; no teacher attestation was invented.

## Public command-line checks

Retained evidence is under
`tmp/pdfs/v34-reference-review-20261028/public-acceptance-run2/`.
Its `summary.json` records all package and PDF hashes. `pdf-review.json` records
page counts and comparisons.

The source entry point generated normal and enlarged papers using the actual
local French reference index. The signed frozen backend received preferred seed
270100 four times in the same output folder. It published seeds 270100, 270101,
270102 and 270103, one from each family. Assessment identity, manifest, checkpoint
and destination all agree on the selected seed. A fifth request failed before
publication, with every existing output file unchanged.

Every exercise equals the previously reviewed run-9 exercise for the same seed.
All 166 page bodies across these twelve PDFs are raster-identical to run 9 at
100 dpi, excluding the footer region. Complete ordered content, A4 geometry,
footer and nonempty-body checks also passed. This inherits the recorded run-9
visual coverage; it is not a claim that 166 new pages were manually inspected.

Frozen execution intentionally binds implementation identity to the helper
executable; source execution binds it to Python sources. An initial cross-runtime
replay attempt correctly refused the different identity. The acceptance script
then checked the unchanged frozen artifacts against an independently rebuilt
source content model. It preserved both identities and excluded only identity
and its evidence digest from the cross-runtime comparison. The frozen backend
had already validated its own package and PDFs before publishing them. No
production validation was relaxed. Both earlier diagnostic attempts are retained.

## Native app checks

Computer control exercised the candidate Debug app, separate from the installed
PR93 app. The four-family explanation was visible. More options and the native
folder picker selected a test-only output directory. Generation disabled the
relevant controls while running, then opened the completed subject in Documents.
History showed a completed `app-owned-v34` entry. The fresh-question action from
that entry returned to the French workspace and produced a second family.

The two published seeds were 287194963 and 1410663380. Each completed history
record matches its manifest seed. Their subjects have nine and seven pages;
their corrections have twenty and seventeen pages. All 53 pages were rendered
and visually inspected, with independent ordered-content checks. Code indentation,
tables, headings and page numbers remain legible. No missing content, overlap,
clipping or body-empty page was found. The output preference was restored to
Downloads and the test app was closed. Existing documents and history were kept.

The subject flow retains linked tracing, helper construction, counterexamples
and explanation tasks. The compiler family connects tree traversal to stack
execution; its library exercise carries a refused loan through a correction and
new insertion; its scheduler distinguishes boundary ordering, waiting time,
termination and idle periods. The ordered-tree family reuses counts after
insertions, then combines SQL extraction with Python sensor summaries and a
causal routing case. These are internally checked task sequences, not observed
learner outcomes.

Some correction pages remain sparse, particularly the final routing answer page.
The subjects ask candidates to work on separate paper and reproduce requested
tables. The seven-to-nine-page normal subjects remain more compact than the
sixteen-page, thirty-six-question official 2026 Metropole comparator. V34 has
thirty-four questions. The comparison and syllabus limits in
`french-nsi-v34-curriculum-and-variety-review-2026-10-28.md` still apply. Page-count
matching would not prove equal demand. No blank-page padding was added.

## Regression and release checks

The final fixed-source backend suite passed 3,734 tests with two skips. The native
suite passed 95 tests. The earlier broad run exposed two stale V32 help-copy
assertions; the workspace, help article and French translations now state V34.
The final suite followed those corrections. New tests cover seed reconciliation,
missing or forged manifests, translated completion notices and catalogue
exhaustion. Historical replay tests remain in the suite.

The App Store-mode Release preflight passed strict bundle signatures and sandbox
checks using the personal Apple Development team Z29CKRV8C9. This is not an Apple
Distribution archive, submission or approval. The personal Distribution identity
is still unavailable. No certificate was created and no upload was attempted.

Logs are retained in `tmp/final-validation-20261028/`, including
`v34-public-full-suite-final.log`, `v34-public-native-copy-final.log`,
`v34-public-store-preflight.log`, `v34-public-actual-acceptance-resumed.log` and
`v34-public-pdf-review.log`. Native artifacts are retained under
`native-v34-public-output/`. Official source PDFs are not bundled. Per-document
rights clearance and the existing UK qualification holds remain open.
