# English Occitanie report review

The English application, technical report and reliability note were rewritten
after the user requested a more natural voice. This is an editorial and rendered
document review, not acceptance of the application or generated exam papers.

## Reading and editorial decisions

The editor read Apple's [2026 Environmental Progress Report](https://www.apple.com/environment/pdf/Apple_Environmental_Progress_Report_2026.pdf),
PDF pages 3, 4, 5, 11, 20 and 31, and [A Day in the Life of Your Data](https://www.apple.com/privacy/docs/A_Day_in_the_Life_of_Your_Data.pdf),
pages 3 through 8. The first separates goals from measured results and explains
specific mechanisms; the second explains a technical issue through a concrete
example. These are selected sections, not a claim to have read both publications
in full. No Apple wording, statistics, affiliation or endorsement was imported.

The root reviewer read the full two-page [competition rules](https://association.centralesupelec-alumni.com/medias/editor/PRIX_OCCITANIE_2026/REGLEMENT_PRIX_OCCITANIE_2026.pdf).
The reports address regional relevance, originality, feasibility and proposed
work over the next twelve months. No invented judging weights or prediction of
a prize is made. Applicant eligibility and budget blanks remain unchanged.

The technical report now begins with the two CLEMENT MAROT dataset records and
the dictionary overwrite students can reproduce. It follows the activity into
paper generation, answer checks and current limitations. Supporting paragraphs
can continue without another heading. The application retains the official
question headings but removes internal version jargon from its narrative. The
reliability note retains exact historical counts, the extract hash and the
explicitly illustrative statistical calculation. Repeated caveats are grouped
without turning unqualified work into an accepted product.

## Verification

Native Pages copies retain the current icon, floating diagrams, typography and
footers. All ten exported A4 pages were inspected by the editor and separately
by the root reviewer: application 3, technical report 4, reliability note 3.
The full extracted text matches source paragraphs and headings in order after
whitespace/apostrophe normalisation. No clipping, overlap or stranded heading
was observed. This is not complete PDF accessibility certification.

All six canonical Pages/PDF files were byte-compared with the approved copies.
Task-owned Pages windows were closed before replacement. The previous folder
was moved to a unique recoverable Trash backup, with original hashes verified.
No unrelated user document or app was changed. Canonical files are under
`output/occitanie-2026/pages-english-final/` and remain ignored build artifacts.

Eight report-specific tests passed. The integrated report/submission/hygiene
selection passed 28 tests. The broader French implementation suite passed
5,430 tests with two skips before the prose-only source commit was integrated;
that run is not presented as a full test of the later report-source changes.
Native testing executed 353 tests, with one optional interaction test skipped
and zero failures. Direct Release and personal-development-signed Store Release
preflight passed. Protected latest-head CI remains a separate publication gate.

## Identities

| File | SHA-256 |
| --- | --- |
| tools/build_occitanie_pages_sources.py | 209e3bf9ed77aa459285b6e0da3cff8b5d2b24843dbd328f845bbe943bda109f |
| tests/test_occitanie_pages_sources.py | 73f3504d2711bf20813147dd86281cfb653d588a96fda333cdad055cd352ea45 |
| Keldin-NSI-Technical-and-User-Report.pdf | dc4bd443ac4919e2842d793d010f79169c73ad436fe856576e8116c05ca13aff |
| Keldin-NSI-Reliability-and-Validation-Note.pdf | bec59dfe75d22b758442cb372400d962936d62c78f22a08f5554103c3afd0b86 |
| Prix-Occitanie-2026-Application-English-James-Durup.pdf | 63be891389a9c1e00c6ea95292fc7a61bda30710ab7bbc3bfc9523a8ffcc8637 |

No complete current model-generated French paper has passed qualification.
Teacher review, learner timing, reference-document rights and distribution
requirements remain unresolved as described in the reports.
