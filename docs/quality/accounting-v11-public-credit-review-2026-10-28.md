# Accounting V11 public-case and credit review

## Scope

The V10 live paper remains a manual HOLD, retained with its actual automated
PASS result. V11 fixes the reproduced public-case, marking and rendering defects.
It does not relabel that older run or claim live acceptance before a new run.
The adapter identity is `ai-assessment-v11-accounting-public-credit-contracts`.

### Public source parity

Paper 1 no longer gives models invented shared planning extracts that candidates
never see. The former random draws are consumed explicitly so later seeded case
amounts remain unchanged. Public titles and narratives come from the owned case.
Q15.3 names its partners and uses their retirement/profit-sharing data, rather
than Q14's company. Q16's sole trader and Q17's plc are identified separately;
their models receive the same case facts printed for candidates. Candidate
source and selected-response contracts cannot change before independent solving.

### One marking authority

Explicit Accounting policy supplies positive structured credits before generic
hydration. Specialised Paper 1 tables use that same authority, including genuine
credit-side entries. Mutating an allocation is rejected rather than silently
printing a second scheme. Q12's working marks are included in its seven-mark
total, with no unsupported extra presentation award. Q14's fixed supplied tax
charge stays fixed on own-figure calculations.

Q11 has two distinct reasons, each capped at three marks. Its grouped policy
tests each reason separately, then sums synthetic bands to 2/4/6. Missing,
malformed, repeated or wrongly weighted groups refuse. Both supported Accounting
subject aliases work; other subjects cannot use this domain policy. This is a
synthetic consistency diagnostic, not evidence about learner performance or
reliable automated marking of arbitrary student writing.

Typed source content separates question-specific indicative material from later
generic enrichment. Private source-credit content and grouped reason features
are recursively excluded from the blind solver. Public accounting credit
columns remain available. These private policies are also immutable before
model use. New canaries first reproduced two leaks and three mutation paths;
the combined privacy, solver and projection suite then passed 28 tests.

### Four original multi-step choices

Paper 1 choices 6–9 now require carriage/purchase-return classification,
sale-or-return corrections using mark-up on cost, a correcting journal without
duplicating a recorded sale, and share premium after pence conversion and issue
costs. A narrow strict public-input contract dispatches to pure Decimal functions.
Choices, keys and stems are source-owned; wrong units, missing/extra inputs,
duplicate answers and altered private keys fail. A separate versioned MCQ RNG
preserves later case arithmetic. Independent static review found no arithmetic,
unit or journal-direction discrepancy. These four one-mark items add workload;
their timing and difficulty have not been calibrated.

The writer now refuses a stem containing a complete A–D copy of its structured
choices, including formatted labels. It uses the existing bounded repair path,
not silent PDF text stripping. Ordinary label references and different-text
multiline source material remain valid.

## Fresh seeded baseline and every-page review

This is app-owned source rendering, **not live AI qualification**. Seed 270100:

| Final baseline 4 artifact | Pages | SHA-256 |
| --- | ---: | --- |
| Question paper | 36 | `b62b2e84f98a0a753d18176345ece63175bc8e196e2e18b1f65b059fd913bf91` |
| Scheme | 24 | `a61dc29c61ffe3995fa2b3cbccbf2499370067c6a52df227f7b9d312885eac5d` |

Retained root: `tmp/pdfs/accounting-marking-policy-20261028`. The main reviewer
inspected all 36 subject and 26 scheme pages of baseline 1. That review found
Q12's nested 167 mm table exceeded its 153 mm cell and crossed the answer border.
A vector regression reproduced x=575.46 pt against a 561.26 pt right border.
The corrected table fits the cell; page-boundary tests cover all 36 pages.

General judgement advice was still repeated in Q16/Q17. It now appears once in
front matter. All six/eight respective source rows fit one continuation page per
question, removing two sparse extra pages without deleting assessed content or
padding to a target count.

Baseline 2's changed subject page 8 and scheme pages 2, 3, 16, 17, 21–24 were
freshly inspected by the main reviewer and a second reviewer. Remaining 35
subject and 16 scheme pages have exact full-page raster matches to reviewed
baseline 1 at 100 dpi. No clipping, overlap or answer-border overflow was found
in the final changed pages. Some level-grid pages remain sparse. Deliberate
blank and candidate-working pages are not mistaken for missing content.

Baseline 3 reproduced all 60 baseline 2 pages exactly at 100 dpi after the
shared credit-row and level-grid helpers were introduced. Baseline 4 changes
only scheme page 8: the four new multi-step MCQ answers now include their option
letters. The renderer derives every key from `choices` and `correct_choice`,
independently of mutable `mark_scheme` prose. The main reviewer and second
reviewer inspected that complete page; its ten numbered answers and one-mark
awards are readable, with no clipping or overlap. The other 59 full-page rasters
are identical to baseline 3. All four baseline directories remain retained.

`baseline-run-4/raster-comparison.json` records PDF hashes, actual page dimensions
and per-page RGB hashes. Comparisons use the complete 100 dpi page, including
headers and footers, rather than cropped answer regions. Byte differences in
PDF metadata do not invalidate an otherwise identical page raster.

The June 2025 official Paper 1 comparator's 36 pages were also reviewed during
the preceding V10 analysis. Page-count matching is not an equivalence claim.
The corrected shorter scheme retains the source rows and appropriate account
layouts; it does not copy official question wording or bundle official PDFs.

## Compact scheme acceptance policy

`generated-aqa-accounting-paper1-credit-v1` applies only to the AQA Accounting
Paper 1 mark scheme. A package declaring the explicit marking policy must have
exactly 24 scheme pages and matching exported assessed items. Its 21 questions
must follow the configured order, number, rule, kind, tariff and assessment
objectives, with the expected paper identity and one option per section.
Changing the package and recomputing its item projection cannot bypass these
checks. Unmarked historical schemes retain their exact 26-page fallback; an
unmarked 24-page scheme is not accepted. No other subject's page requirement is
lowered.

Printed checks require the correct MCQ question/letter/text/mark rows and the
complete credit tables and levels grids for each written part. Renderer and
validator share the canonical key, feature-label, credit-weight and level-row
helpers. Missing grids, changed bands and swapped awards are rejected even when
all question text, numerical answers and total marks remain elsewhere on the
page. An altered `scheme_mode` cannot hide a missing decision grid.

All six primary calculation tables are also bound to the independent Core
candidate-input solver and raw candidate postings: Q12's asset roles and
depreciation deductions, Q13's debit/credit account sides, Q14's labelled income
and expense columns, Q15.1's partner capital columns and Q15.2's period columns
and appropriation deductions. The verifier does not use renderer case objects
or worked formulae as answer evidence. Intermediate workings retain the earlier
numeric-presence checks; those checks alone do not establish role or sign
correctness for every intermediate cell.

The pinned build/test dependency is PyMuPDF 1.28.2. Its supported
`no_recommend_layout()` switch suppresses only the optional layout-package
advertisement before table extraction. Missing quiet table support produces an
actionable error. A fresh-process regression validates actual generated paths
and requires exactly one JSON output line, protecting the native event stream
without redirecting or hiding diagnostics.

## Tests and remaining gates

Scoped case/choice tests passed 240 cases. Integrated domain, AI, migration and
tool tests passed 357 before the final layout compaction. That integration found
an unsupported restriction to only one existing Accounting alias and a legacy
fixture relying on newly removed planning extracts. Both were corrected without
weakening source-scope replay: the fixture explicitly supplies a retained shared
source, and additional tests cover valid aliases and invalid subjects.

The final renderer/domain scoped suite passes 120 tests. All red attempts,
targeted results and baseline 1 remain retained under
`tmp/final-validation-20261028` and the PDF root above. Ruff passes. Graphify was
updated with AST-only extraction; 42 JSON resource files again produce no code
nodes, so this graph does not imply semantic review of those resources.

The first full V11 run finished with 4 failures, 4,089 passes and 2 skips in
476.64 seconds. It exposed the old 26-page scheme requirement, a mismatch
between exported source demands and the new MCQ/company-case inputs, and two
fixtures that still assumed the previous planning text or simpler MCQs. The
repairs declare the compact policy, carry the configured source dependencies
into generated questions, inject legacy text explicitly where its exclusion is
being tested, and recompute the new MCQ expectations from their public inputs.
That full run is retained in `accounting-v11-full-suite.log`; it does not certify
the later fixed source.

The first printed-credit mutation run reproduced 9 failures with 8 existing
passes. A separate forged-mode mutation reproduced another failure. The final
positional checks reproduced 9 further failures: a wrong MCQ letter, swapped
answer rows, mutable answer prose, swapped carrying amounts, an expense with
its deduction sign removed, switched appropriation periods, debit/credit swaps
in both Q13 tables and switched partner columns. After repair, the combined
pagination/marking-policy suite passes 63 tests. Its final logs are
`accounting-scheme-position-red.log` and `accounting-scheme-position-green.log`
under `tmp/final-validation-20261028`. Ruff and the diff whitespace check pass.

The final fixed-source suite at `bc36bb09` passed 4,122 tests with two skips in
538.70 seconds. Five warnings came from PyMuPDF's SWIG bindings. The retained log
is `tmp/final-validation-20261028/accounting-v11-final-full-suite.log`.
Personal-development-signed Store Release preflight and strict bundle/helper
signature checks also passed, recorded in `accounting-v11-final-store-preflight.log`.
This is engineering preflight, not App Store approval. Direct frozen-runtime
acceptance, a fresh pinned complete live run and protected publication still
need their actual results recorded. Teacher
review, observed learner timing and mark calibration remain unperformed. Neither
this baseline nor any successful solver probe establishes complete provider,
paper-family, App Store or project-wide qualification.
