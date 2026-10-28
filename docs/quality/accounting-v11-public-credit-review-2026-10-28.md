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

| Final baseline 2 artifact | Pages | SHA-256 |
| --- | ---: | --- |
| Question paper | 36 | `24a98256816ab8a7b99f8edf021b2f8a117b7fc83576dca6dec405e14787fe6f` |
| Scheme | 24 | `0e7c60f4a84b89809976a5977dc736ecca92ea6b07d874c3e374c2bdd03803a1` |

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

The June 2025 official Paper 1 comparator's 36 pages were also reviewed during
the preceding V10 analysis. Page-count matching is not an equivalence claim.
The corrected shorter scheme retains the source rows and appropriate account
layouts; it does not copy official question wording or bundle official PDFs.

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

Full fixed-source tests, packaged acceptance, a fresh pinned complete live run
and protected publication still need their actual results recorded. Teacher
review, observed learner timing and mark calibration remain unperformed. Neither
this baseline nor any successful solver probe establishes complete provider,
paper-family, App Store or project-wide qualification.
