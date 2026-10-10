# Occitanie: original French NSI practice papers

Last updated: 2026-10-09. This is an evidence/status record, not a claim of
educational approval. No teacher, school, Région, examiner or Ministry endorsement
has been obtained. No prize application has been submitted.

Implementation tracking: [issue #16](https://github.com/james8464/Past-paper-generation/issues/16).
See the [engineering verification record](quality/french-nsi-prototype-verification-2026-09-28.md)
and [competition submission pack](competition/occitanie-2026/README.md). The formal
application currently renders as two A4 pages, within the three-page limit, but
personal eligibility, contact fields and prior-funding status still require
James's confirmation.

## Problem and beneficiaries

Official annales provide a finite set of authentic examination tasks. **HYPOTHESIS:**
additional original, carefully reviewed practice could help teachers vary revision
material without requiring student subscriptions or sharing student answers with
AI providers. Teacher correction time, access and learning effects need measurement.

## Existing UK prototype — WORKING NOW, not finalised

The Mac app supports 21 advertised UK paper/practice routes. Its local/hosted
generation, structured assessment records, rendering and quality checks are reusable
engineering. Live qualification and manual review have exposed unresolved defects;
automated passing must not be represented as examiner approval.

## French extension — IMPLEMENTED engineering / PROTOTYPE education

- Separate national-framework registry route: Terminale NSI, written component,
  session 2027. Not a translated A-level or a fictitious French exam board.
- Frozen education context, independently versioned curriculum/rules and exact
  decimal credit; three exercises, 18 technical + 2 language points.
- Local scoped SQLite/FTS references; filter before ranking; no UK fallback;
  holdouts excluded; hashes, provenance and rights status retained.
- French authoring, blind solver and separate review passes; bounded SQL, binary,
  shortest-path and restricted Python-trace checks; unsupported contracts unresolved.
- Structured tables and vector graphs; programme-capability mappings, cognitive
  operations, estimated time and a required progression beyond simple recall.
- Seeded 5.5/6/6.5 technical allocations totalling 18, plus a separate two-point
  language component. The detailed allocation remains an indicative product barème.
- Text, normalized-code, structural and generation-history originality screening;
  similarity remains risk evidence, not a copyright guarantee.
- Hash-bound checkpoints, rejected attempts retained, French draft PDFs and
  atomic folder publication. All outputs remain non-official, unreviewed drafts.
- All three written exercises now have app-owned facts, answers and exact
  credits; the model chooses only finite French wording IDs. The graph/tree,
  relational database and network/process/security contracts are replayed in
  the package and checked against extracted standard/large-print PDFs. This
  engineering control does not establish classroom suitability.
- Native French workspace, consent before downloads, French interface translations,
  local Ollama endpoint, standard/enlarged print, history metadata and review UI.
- Human review-record API tied to artifact hashes. Reviewer identity is self-attested,
  not authenticated; this is not an official signature or school approval system.

## Evidence and limits

The official 2021–2026 archive index and content are reconciled locally: 79 canonical
papers, 43 accessibility representations, 122 links, 13 frozen holdouts and no
download failures. All 81 registered documents (79 papers plus the programme and
language rubric) have pinned SHA-256 hashes. Two byte-identical Nouvelle-Calédonie
2022 normal/replacement pairs are recorded and collapsed in retrieval. Neither pair
crosses the holdout boundary. Source PDFs remain local and unbundled; document-specific
rights and third-party illustrations still need review before redistribution.
Python's certificate store failed on Eduscol in this development environment;
verified system curl was used without disabling TLS or accepting redirects.

The measured Métropole source is A4 (595.32 × 841.92 pt), mainly Arial 12 pt,
with Courier New 12 pt code. The renderer is **PROTOTYPE**: compatible fonts and
measured geometry, not pixel identity. Cover hierarchy, exercise titles, scope
lines, question indents, code, vector diagrams/tables and correction guidance are
implemented and manually inspected on fixtures. A 2026 source cannot establish an
official 2027 template. Timing and AI difficulty judgements remain non-empirical;
restricted code evaluation does not support all Python; originality thresholds
still require labelled calibration.
The [6 October v12 PDF check](quality/french-nsi-v12-pdf-verification-2026-10-06.md)
inspected all pages of four deterministic fixture PDFs. Exercise 1 is more
substantive than the earlier generic fixture, but its figure is smaller than the
official comparator and exercises 2–3 still contain repetitive fixture content.
This is a renderer and contract check, not a successful live paper or classroom
qualification.

A resumable French benchmark runner is implemented for gemma4:12b,
ministral-3:8b and qwen3:8b: ten full papers and thirty exercises per model, with
fixed seeds, model/source/code identity, failure preservation and duplicate-run
locking. The completed pinned Gemma 4 12B campaign accepted **0 of 10** complete
papers; its rejected attempts remain evidence for redesign, not qualified papers.
The campaign has not selected a model; the exact Ministral and Qwen candidates are
not currently installed. An exploratory Qwen 3.5 9B single-paper run also
accepted 0/1 complete papers on 4 October; it does not replace the planned
candidate comparison. No teacher-reviewed release, student pilot,
Intel test or multi-memory hardware matrix exists.
The v12/v13 redesign did not produce an accepted identity-pinned live
paper. The 7 October v13 diagnostic accepted its finite-authored first
exercise, but the database exercise failed three authoring attempts, so no PDF
was published. Its [failure record](quality/french-nsi-v13-live-diagnostic-2026-10-07.md)
preserves source/model/reference identities and rejected candidates. Exercises
2–3 needed stronger original-data authoring before a full-paper qualification
claim was supportable. A later [controlled-database diagnostic](quality/french-nsi-v14-controlled-diagnostic-2026-10-07.md)
published a complete three-exercise draft on one pinned Gemma/seed run with no
rejected attempts, but page-by-page manual inspection **rejected** its
model-authored third exercise for ungrounded routing answers, a weak process
repair and an unsupported cryptographic premise. Protected PR #36 replaced
that exercise with a locked network contract. The [subsequent live diagnostic](quality/french-nsi-v15-live-diagnostic-2026-10-07.md)
passed automation and yielded internally consistent PDFs, but manual comparison
with the official 2026 paper placed product fidelity on hold: six pages and
18 questions against the comparator's 16 pages and 36 questions. These counts
are not a mandatory template, but the gap requires fuller reasoning sequences
and teacher time calibration before a submission-readiness claim. Automated
completion is not subject-matter or teacher validation; the final matrix remains
on hold.

Protected PR #39 deepened the app-owned network case. A new
[source-pinned v17 live diagnostic](quality/french-nsi-v17-live-diagnostic-2026-10-08.md)
passed automated checks on its first attempt, but all seven subject and eleven
correction pages still led to a **manual fidelity hold**: 18 numbered questions,
an orphaned final question and presentation/depth gaps against the official
2026 reference. This is an engineering checkpoint, not model selection or
educational qualification. Earlier failures and the v15 hold remain retained.

Protected PR #44 added a versioned ten-question database sequence. The next
[source-pinned V16 live diagnostic](quality/french-nsi-v16-live-diagnostic-2026-10-08.md)
passed automated checks on its first attempt, and every page of its seven-page
subject and twelve-page proposed correction was inspected. The subject now has
22 questions, but the database questions occupy one page and the final network
page remains sparse, versus 36 questions across 16 pages in the official 2026
comparator. Two correction rubrics also break onto the next page. Product fidelity
therefore remains **on hold**; neither live pass is a model recommendation or
teacher validation. The v17 and v15 holds and earlier failed attempts remain
separate evidence.

Protected PR #47 added an original versioned ten-question graph/tree sequence.
The next [source-pinned V17 graph/tree live diagnostic](quality/french-nsi-v17-graph-tree-depth-live-diagnostic-2026-10-08.md)
passed automated checks on its first attempt, but page-by-page comparison kept
**manual product fidelity on hold**. The eight-page subject has 26 questions
against 36 in the official 16-page comparator. E1 is deeper, yet E2 and the
last E3 page remain sparse; the proposed correction separates the 3d rubric
from its answer and displays literal Markdown fencing in the 2g rubric. This
engineering result is not a model recommendation or teacher validation.

Protected PR #50 added a version-isolated twelve-question network, process and
security sequence with candidate working tables. Its [pinned V18 live diagnostic](quality/french-nsi-v18-network-reasoning-live-diagnostic-2026-10-09.md)
passed automation on the first attempt with no repairs. All nine subject and
fifteen proposed-correction pages were visually inspected against all sixteen
pages of the official 2026 Métropole comparator. The subject now has 32
questions, but E2 still places ten questions on one page and the final E1/E3
pages remain sparse; the official reference has 36 questions over sixteen
pages with more sustained multi-step work. **Manual product fidelity remains
on hold.** This single paper does not select a model or provide teacher or
learner validation. Earlier checkpoints and failures remain preserved.

Protected PR #52 added a version-isolated ten-question database reasoning
sequence. Its [pinned V19 live diagnostic](quality/french-nsi-v19-database-reasoning-live-diagnostic-2026-10-10.md)
passed automation on the first attempt, with no repairs. All nine subject and
sixteen proposed-correction pages were visually inspected against all sixteen
pages of the official 2026 Métropole comparator. The subject still has 32
questions across nine pages: E2's ten prompts fit on one page, and the final
E1/E3 pages are sparse. Some French scope lines need native-language copy
editing. **Manual product fidelity remains on hold.** This single paper does
not select a model or provide teacher or learner validation; previous live
holds and failed attempts remain preserved.

Protected PR #54 corrected the specific scope lines observed in V19; native
French teacher review is still required. Protected PR #55 added a
version-isolated graph-link-outage reasoning sequence. Its
[pinned V20 live diagnostic](quality/french-nsi-v20-graph-resilience-live-diagnostic-2026-10-10.md)
passed automation on the first attempt, with no repairs. Every page of the
eight-page subject and seventeen-page proposed correction was inspected,
alongside all sixteen official 2026 Métropole pages. There are still 32
questions versus the official 36: E1 and E2 each put ten questions on one
dense page, while the last E3 page is sparse. The graph outage increases E1
substance but does not supply enough sustained reasoning or usable working
space. **Manual product fidelity remains on hold.** This single-paper result
does not select a model or establish teacher, learner or examiner validation.
Earlier live holds and failed attempts remain preserved.

## Genuine Occitanie scenario — PLANNED

A teacher generates and checks a paper on a Mac; students receive a PDF through
the school's existing channel or on paper. Current loRdi equipment is Windows,
not a target for this Mac executable. The published Lenovo Gen 5 specification
includes 8 GB RAM; a 7.6 GB model download is not evidence of practical inference
within that memory. PDF reading does not require an AI model.

Recruit two NSI teachers from the Toulouse/Montpellier academies, then seek one
school pilot. No contact or partnership is assumed. Seek differing school contexts
and record actual constraints rather than asserting a rural/urban achievement gap.
Optional future work: smaller models, school-hosted inference and accessible
formats. Each requires security, hardware and institutional evaluation.

## Local AI and privacy

Generation is local by default; PDFs, reference index and job history stay on the
Mac. Downloads contact official sites and model hosts. There are no new student
accounts, answer collection or telemetry. CLI remote Ollama requires explicit
opt-in and HTTPS; the French UI currently uses loopback only. Local processing
alone is not proof of GDPR compliance. School deployment needs a governance review.

## Evaluation and success criteria — PLANNED external gates

1. Thirty fixed exercise tasks per candidate local model; retain failed attempts,
   latency, model digest, quantisation/runtime and actual hardware evidence.
2. Ten complete papers on the selected configuration, with every page inspected.
3. Two NSI teachers independently review six stratified papers: correctness,
   curriculum, French, difficulty, timing, marking, originality and layout.
4. No unresolved substantive correctness/marking defect; both reviewers recommend
   classroom practice after revisions. Record disagreements, not just averages.
5. A supervised learner pilot measures timings, ambiguous items and teacher workload.
   Claims of difficulty calibration or impact wait for this evidence.

## Twelve-month roadmap

| Period | Deliverable | Gate |
|---|---|---|
| Months 1–2 | Reviewable French prototype, source register, teacher recruitment | Complete engineering checks; no false qualification |
| Months 3–4 | Teacher evaluation and revisions | Two independent NSI reviews |
| Months 5–6 | Small supervised school pilot | School agreement and data governance |
| Months 7–9 | Measured quality/accessibility improvements | Documented evidence, not benchmark marketing |
| Months 10–12 | Decide second speciality or school-hosted inference | Demonstrated need and feasible hardware |

Provisional €1,000 use: €500 teacher review, €200 pilot travel, €200 hardware and
accessibility testing, €100 contingency. These are proposed allocations, not
expenditure or commitments. Confirm prize rules and reviewer availability first.

## Prize preparation — IMPLEMENTED documents / PLANNED submission

The announced deadline is 2 November 2026 at midnight. The formal application DOCX
and PDF, technical/user dossier and mathematical qualification note are generated and
visually verified as portable sans-serif documents. The formal application is in
French; both supporting reports are in English. The current formal PDF is two A4
pages, within the three-page limit. A factual email draft, claims register,
checklist, video script and a user-operated macOS recording command are included.
A real demonstration video has
not been recorded. Confirm applicant enrolment eligibility, contact details and
prior-funding restrictions before sending.
Do not infer environmental benefit from "local AI": measure energy, reuse and
hardware requirements before making a sustainability claim.

## Primary sources

- [Bac général overview](https://eduscol.education.gouv.fr/5700/presentation-du-baccalaureat-general)
- [NSI definition, session 2027](https://www.education.gouv.fr/bo/2026/Special4/MENE2622643N)
- [NSI programmes](https://eduscol.education.gouv.fr/5823/programmes-et-ressources-en-numerique-et-sciences-informatiques-voie-g)
- [Official annales](https://eduscol.education.gouv.fr/5199/annales-des-epreuves-du-baccalaureat-des-voies-generale-et-technologique)
- [Éduscol reuse conditions and third-party exceptions](https://eduscol.education.gouv.fr/4656/mentions-legales)
- [CNIL: teachers and AI](https://www.cnil.fr/fr/enseignant-usage-systeme-ia)
- [loRdi equipment](https://www.lordi-occitanie.fr/lordi/)
- [Lenovo Gen 5 specifications](https://www.lordi-occitanie.fr/lenovo_500w_2_in_1_gen_5_spec/)
- [Occitanie digital strategy](https://www.laregion.fr/filiere-numerique)
- [Prize announcement](https://association.centralesupelec-alumni.com/fr/article/postulez-au-prix-occitanie-2026/7/9/2026/4731/)
- [Prize regulations](https://association.centralesupelec-alumni.com/medias/editor/PRIX_OCCITANIE_2026/REGLEMENT_PRIX_OCCITANIE_2026.pdf)
