# Prix Occitanie 2026 submission pack

Updated 2 November 2026.

## Formal requirement

The published call requires a concise application in PDF format, limited to three pages, sent before midnight on 2 November 2026 to `information@centralesupelec-alumni.org`. The candidate must be a CentraleSupélec student during the 2026 to 2027 academic year. Graduates are excluded. The rules also exclude a project that has already received outside funding.

The jury evaluates the relationship with Occitanie, originality, engineering character, feasibility, realism and the work planned for the following twelve months. A personal link with Occitanie is not required.

The live announcement, application form and rules were checked on 1 November.
The form asks applicants to preserve its paragraph topics; its optional
illustrations may occupy at most one page within the overall three-page maximum.
Neither linked PDF states a language condition, but English acceptance has not
been expressly confirmed. Explain the planned use of either award without
inventing costs: the reduced EUR 500 plan also needs the applicant's decision.

## Prepared files

The current source builder is dated 2 November and centres the regional activity
and proposed twelve-month work. It produces RTF and SVG inputs, not native Pages documents.
Generate into a separate fresh folder with
`python tools/build_occitanie_pages_sources.py --output output/occitanie-2026/pages-20261102-english-sources`.
Its explicit page structure remains three application pages, four technical-report
pages and three reliability-note pages. RTF page breaks and word-count tests do
not certify Pages pagination: native editing, PDF export and inspection of every
new page are still required. Preserve the current orange Keldin icon and report
cover whitespace when editing in Pages. The active English email draft no longer
describes the historical fixed-paper route as current.

The current English working dossier is in `output/occitanie-2026/pages-20261102-english/`: three native Pages documents, their matching PDFs and `Read before sending.txt`. All ten exported A4 pages were visually reviewed on 2 November: three application pages, four technical/user-report pages and three reliability-note pages. The formal application is named `Prix-Occitanie-2026-Application-English-James-Durup`; the other two reports are supporting documents. The working application is not submit-ready until James completes the facts below, removes drafting notices and placeholders, re-exports it and checks that it remains at most three A4 pages. The organiser has not confirmed English acceptance or accepted a submission.

Earlier Word exports are superseded. Their generated copies were removed from the working output folders on 30 October. The legacy builder still recreates historical V35 content and must not be used as the current submission without a separate update and review. Run `tools/build_occitanie_submission.py` with the bundled document runtime to recreate that older set. Use `--output` with a fresh directory to avoid replacing completed personal forms:

- `Prix-Occitanie-2026-Candidature-James-Durup.docx`: formal application (two pages before personal details; three-page maximum);
- `Keldin-NSI-Technical-and-User-Report.docx`: technical and user dossier;
- `Keldin-NSI-Mathematical-Analysis.docx`: measurement and decision framework.

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

- promotion/year group, postal address and telephone number;
- a short account of studies, interests and commitments;
- confirmation of current 2026-2027 student status and eligibility;
- confirmation of the earlier British teacher presentation and all other presentations;
- all support requested or received, including previous funding;
- intended use of a EUR 1,000 award and a reduced EUR 500 plan.

Before sending, James must also confirm that he remains eligible under the exact wording of the rules and that the receiving email address has not changed.

## Submission checklist

- [ ] Complete every applicant-only fact above in the current editable Pages application.
- [ ] Confirm no disqualifying prior outside funding.
- [ ] Resolve submission language; English acceptance remains unconfirmed.
- [ ] Remove working-draft notices, comments, tracked changes and all completion placeholders.
- [ ] Re-export the edited application to PDF; inspect every page and confirm at most three A4 pages.
- [ ] Confirm that every claim still matches `docs/competition/occitanie-2026/claims-register.md`.
- [ ] If offering a demonstration, do not present failed, historical or manually held output as a qualified current paper.
- [ ] Keep the video and appendices behind a view-only link unless the organisers ask for attachments.
- [ ] Send before midnight on 2 November 2026 and retain the sent message and attachment hash.

## Evidence boundaries

PR #152 is merged at `a009e1fc` and its developer-signed build installed after strict
signature and backend-byte checks on 2 November. Recovery permits at most two whole-exercise
rounds after a validated semantic refusal and retains private returned-object
evidence. Synthetic HTTP transport checks and software regression tests establish
bounded software behaviour, not complete-paper or educational quality. Replay
does not approve a paper. No complete current French paper has passed qualification.

The current public French route is V36. The selected model writes the exercise
contexts, materials, questions, proposed answers and marking criteria. Independent
model calls solve and review the work; schema, credit and supported executable
checks can refuse publication. No complete V36 French paper has passed
qualification. The later DeepSeek Pro 18 diagnostic correctly refused an unstated
tree-height convention; the draft was not accepted.

The earlier V35 route offered five finite whole-paper families without a model
call. Its versioned source and recorded reviews remain historical evidence. The
[local corpus audit](../../quality/french-nsi-corpus-rights-audit-2026-10-11.md)
verified 81 registered files. Its 79 indexed sources comprise 77 distinct paper
contents and two foundational documents, with 66 reference / 13 holdout sources.
Source PDFs remain local and reference-only; per-document rights remain open.
Teacher review is unavailable and the user has waived it as a required milestone.
French qualification uses internal comparison with official syllabus content,
reasoning and representation, question structure, proposed answers and credits,
with inspection of each new exported page.
Teacher approval and learner calibration remain `not_run`; no recommendation,
school partnership or observed learner timing is implied.

The first pinned Gemma 4 12B campaign accepted 0 of 10 complete papers. Its
failures and later failed one-paper diagnostics remain historical evidence, not a
model recommendation. V36's current questions and answers are model-authored;
the earlier fixed question/answer contracts do not establish their correctness.
The earlier model-driven failures and V15 to V31 single-paper holds remain
separate historical evidence. The
[V35 internal comparison](../../quality/french-nsi-v35-expanded-practice-review-2026-10-28.md)
records all 341 standard/enlarged pages, inspected or raster-matched in full to
previously inspected pages. Those standard subjects had 7 to 9 pages and 34 or 36 questions,
versus 36 in the 16-page official 2026 comparator. The fifth family adds object
graphs, backtracking allocation and blocking-channel reasoning. Sparse tails remain.
Difficulty and duration are uncalibrated. No model qualification, teacher
recommendation or learner calibration is claimed. The official Métropole paper
is a development reference, not evidence of an unseen-holdout pass.

Apple Intelligence is a separate on-device provider published through PR #132
and installed after signed-build and native checks. It uses Apple's system model
without a downloaded MLX model.
A tiny strict-JSON task passed. A shared FIFO solver task failed structural and
arithmetic checks, and the actual 8,192-token context cannot hold the current full
French author request. French creation is therefore disabled for this provider.
The Apple cloud entry is a placeholder, not an available generation route or a
model recommendation. See the [bounded provider review](../../quality/apple-intelligence-provider-acceptance-2026-10-30.md).

An additional offline activity uses a licensed twelve-record extract from the
Région Occitanie's 2025 to 2026 school dataset. Duplicate names and inconsistent
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
