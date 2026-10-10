# Prix Occitanie 2026 submission pack

Updated 10 October 2026.

## Formal requirement

The published call requires a concise application in PDF format, limited to three pages, sent before midnight on 2 November 2026 to `information@centralesupelec-alumni.org`. The candidate must be a CentraleSupélec student during the 2026–2027 academic year. Graduates are excluded. The rules also exclude a project that has already received outside funding.

The jury evaluates the relationship with Occitanie, originality, engineering character, feasibility, realism and the work planned for the following twelve months. A personal link with Occitanie is not required.

## Prepared files

Run `tools/build_occitanie_submission.py` with the bundled document runtime to recreate:

- `Prix-Occitanie-2026-Candidature-James-Durup.docx` — formal application (two pages before personal details; three-page maximum);
- `Paper-Creator-NSI-Technical-and-User-Report.docx` — technical and user dossier;
- `Paper-Creator-NSI-Mathematical-Analysis.docx` — measurement and decision framework.

The formal application is in French, following the organiser's form. The
supporting technical/user and mathematical reports are in English, as requested
by James. Matching PDFs have been rendered and visually checked page by page in
`output/occitanie-2026/`: two A4 pages for the formal application, four for
the technical/user dossier and three for the mathematical analysis. The directory
is intentionally ignored by Git so personal submission copies are not published
automatically. Regenerate and reinspect the formal PDF after filling personal facts.

Only the three-page application is formally required. The two appendices and the demonstration video should be provided through a private link if the organisers accept supporting material. They must not cause the formal application to exceed three pages.

## Facts James must complete

The application deliberately leaves these fields blank because the repository cannot establish them:

- promotion/year group;
- postal address;
- telephone number;
- whether this project has received or requested any previous financial support.

Before sending, James must also confirm that he remains eligible under the exact wording of the rules and that the receiving email address has not changed.

## Submission checklist

- [ ] Fill the four personal facts above in the DOCX.
- [ ] Confirm no disqualifying prior outside funding.
- [ ] Export the edited formal application to PDF and confirm it remains at most three A4 pages.
- [ ] Search the final PDF for comments, tracked changes and placeholders.
- [ ] Confirm that every claim still matches `docs/competition/occitanie-2026/claims-register.md`.
- [ ] Record the real application demonstration after unlocking the Mac.
- [ ] Keep the video and appendices behind a view-only link unless the organisers ask for attachments.
- [ ] Send before midnight on 2 November 2026 and retain the sent message and attachment hash.

## Evidence boundaries

The French NSI path is a working prototype. The official 2021–2026 archive is
reconciled locally (79 canonical papers, 13 holdouts, 43 recorded accessibility
representations, two duplicate-content groups), and automated controls, measured PDF
geometry and a resumable local-model benchmark are implemented. A complete accepted
qualifying multi-paper French benchmark, two independent French NSI teacher recommendations and a
supervised learner pilot are not yet complete. The application therefore describes
those items as planned qualification work, not achieved approval.

The first pinned Gemma 4 12B campaign accepted 0 of 10 complete papers. Its
failures and later failed one-paper diagnostics remain retained evidence, not a
model recommendation. All three exercises now use app-owned, versioned French
question, answer and credit contracts. A pinned V22 paper passed automated
checks on its first attempt, but
[manual comparison with the official 2026 paper](../../quality/french-nsi-v22-route-trace-live-diagnostic-2026-10-10.md)
kept fidelity on hold: the eleven-page subject has 32 numbered questions,
versus 36 across 16 official pages. E1 now has writable before/after route
tables, but E2 remains compact, the final network page is sparse, and sustained
multi-step depth and learner working-space flow remain insufficient. The V21–V15 live holds and
v12–v14 failures remain separate evidence. No
multi-paper model qualification, teacher recommendation or learner calibration
has been achieved. The application must present the generator as a prototype,
not a validated classroom-ready paper maker.

The project does not claim endorsement by the Ministry, the Région Occitanie, the Toulouse or Montpellier academies, CentraleSupélec or any examination board. Generated files remain independently branded and marked non-official.

The [Apple report visual audit](apple-report-visual-audit.md) records the official design references, specific differences and editorial changes. Apple's imagery and branding are not included in the submission.

## Official sources

- [Prize announcement](https://association.centralesupelec-alumni.com/fr/article/postulez-aux-prix-occitanie-2026/07/09/2026/4731)
- [Application form](https://association.centralesupelec-alumni.com/medias/editor/oneshot-images/1990614366a202b1b810af.pdf)
- [Competition rules](https://association.centralesupelec-alumni.com/medias/editor/PRIX_OCCITANIE_2026/REGLEMENT_PRIX_OCCITANIE_2026.pdf)
- [Official 2027 NSI examination definition](https://www.education.gouv.fr/bo/2026/Special4/MENE2622643N)
- [Région Occitanie open-data portal](https://data.laregion.fr/)
