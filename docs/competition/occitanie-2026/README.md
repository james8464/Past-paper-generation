# Prix Occitanie 2026 submission pack

Updated 29 October 2026.

## Formal requirement

The published call requires a concise application in PDF format, limited to three pages, sent before midnight on 2 November 2026 to `information@centralesupelec-alumni.org`. The candidate must be a CentraleSupélec student during the 2026–2027 academic year. Graduates are excluded. The rules also exclude a project that has already received outside funding.

The jury evaluates the relationship with Occitanie, originality, engineering character, feasibility, realism and the work planned for the following twelve months. A personal link with Occitanie is not required.

## Prepared files

The current working dossier is in English, as requested by James. Its native Pages documents and PDF exports belong in `output/occitanie-2026/pages-english-final/`. The formal application is named `Prix-Occitanie-2026-Application-English-James-Durup`; the technical/user and reliability/mathematical reports are supporting documents. `tools/build_occitanie_pages_sources.py` prepares the English source material for the Pages workflow. Final acceptance requires inspecting every exported page and checking the formal application's three-page limit after personal details are filled in. The English draft is not a claim that the organiser has approved its language or accepted a submission.

Earlier Word exports are superseded. Their generated copies were removed from the working output folders on 30 October; the source builder remains available. Run `tools/build_occitanie_submission.py` with the bundled document runtime to recreate them. Use `--output` with a fresh directory to avoid replacing completed personal forms:

- `Prix-Occitanie-2026-Candidature-James-Durup.docx` — formal application (two pages before personal details; three-page maximum);
- `Keldin-NSI-Technical-and-User-Report.docx` — technical and user dossier;
- `Keldin-NSI-Mathematical-Analysis.docx` — measurement and decision framework.

In that older Word set, the formal application is in French and the supporting
reports are in English. Matching PDFs were previously rendered and visually checked:
two A4 pages for the formal application, four for the technical/user dossier and three
for the mathematical analysis. Those superseded exports do not certify the current
Pages dossier. Output folders are ignored by Git so personal submission copies are
not published automatically. Keep the current Pages documents and PDFs; older report
exports are rebuildable and need not accumulate beside them. Retain unique paper
validation evidence and failure records separately from submission exports.

Only the three-page application is formally required. The two appendices and the demonstration video should be provided through a private link if the organisers accept supporting material. They must not cause the formal application to exceed three pages.

## Facts James must complete

The application deliberately leaves these fields blank because the repository cannot establish them:

- promotion/year group;
- postal address;
- telephone number;
- whether this project has received or requested any previous financial support.

Before sending, James must also confirm that he remains eligible under the exact wording of the rules and that the receiving email address has not changed.

## Submission checklist

- [ ] Fill the four personal facts above in the current editable application.
- [ ] Confirm no disqualifying prior outside funding.
- [ ] Export the edited formal application to PDF and confirm it remains at most three A4 pages.
- [ ] Search the final PDF for comments, tracked changes and placeholders.
- [ ] Confirm that every claim still matches `docs/competition/occitanie-2026/claims-register.md`.
- [ ] Record the real application demonstration after unlocking the Mac.
- [ ] Keep the video and appendices behind a view-only link unless the organisers ask for attachments.
- [ ] Send before midnight on 2 November 2026 and retain the sent message and attachment hash.

## Evidence boundaries

The public French V35 path is a working prototype with five finite whole-paper
families. It makes no AI-provider call, prefers unused families and permits
explicitly requested repeat practice. The
[local corpus audit](../../quality/french-nsi-corpus-rights-audit-2026-10-11.md)
verified 81 registered files. Its 79 indexed sources comprise 77 distinct paper
contents and two foundational documents, with 66 reference / 13 holdout sources.
Source PDFs remain local and reference-only; per-document rights remain open.
Teacher recommendations and a supervised learner pilot have not been obtained.
Teacher review is unavailable. Internal review is used for engineering acceptance,
without inventing external approval or learner timing.

The first pinned Gemma 4 12B campaign accepted 0 of 10 complete papers. Its
failures and later failed one-paper diagnostics remain retained evidence, not a
model recommendation. All three exercises now use app-owned, versioned French
question, answer and credit contracts. The earlier model-driven failures and
V15–V31 single-paper holds remain separate historical evidence. The
[V35 internal comparison](../../quality/french-nsi-v35-expanded-practice-review-2026-10-28.md)
records all 341 standard/enlarged pages, inspected or raster-matched in full to
previously inspected pages. Standard subjects have 7–9 pages and 34 or 36 questions,
versus 36 in the 16-page official 2026 comparator. The fifth family adds object
graphs, backtracking allocation and blocking-channel reasoning. Sparse tails remain.
Difficulty and duration are uncalibrated. No model qualification, teacher recommendation or learner
calibration is claimed. The technical report labels its retained screenshot as
an earlier interface, not the current V35 workflow.

An additional offline activity uses a licensed twelve-record extract from the
Région Occitanie's 2025–2026 school dataset. Duplicate names and inconsistent
capitalisation lead to concrete Python and SQL tasks. It exports two PDFs and
is separate from exam generation. Source attribution and limits appear in both.
See the [activity review](../../quality/occitanie-case-study-review-2026-10-29.md).

The project does not claim endorsement by the Ministry, the Région Occitanie, the Toulouse or Montpellier academies, CentraleSupélec or any examination board. Generated files remain independently branded and marked non-official.

The [Apple report visual audit](apple-report-visual-audit.md) records the official design references, specific differences and editorial changes. Apple's imagery and branding are not included in the submission.

## Official sources

- [Prize announcement](https://association.centralesupelec-alumni.com/fr/article/postulez-aux-prix-occitanie-2026/07/09/2026/4731)
- [Application form](https://association.centralesupelec-alumni.com/medias/editor/oneshot-images/1990614366a202b1b810af.pdf)
- [Competition rules](https://association.centralesupelec-alumni.com/medias/editor/PRIX_OCCITANIE_2026/REGLEMENT_PRIX_OCCITANIE_2026.pdf)
- [Official 2027 NSI examination definition](https://www.education.gouv.fr/bo/2026/Special4/MENE2622643N)
- [Région Occitanie open-data portal](https://data.laregion.fr/)
