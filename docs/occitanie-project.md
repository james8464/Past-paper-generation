# Occitanie: original French NSI practice papers

Last updated: 2026-09-28. This is an evidence/status record, not a claim of
educational approval. No teacher, school, Région, examiner or Ministry endorsement
has been obtained. No prize application has been submitted.

Implementation tracking: [issue #16](https://github.com/james8464/Past-paper-generation/issues/16).
See the [engineering verification record](quality/french-nsi-prototype-verification-2026-09-28.md)
and [French application-content draft](occitanie-application-draft.md). The latter
is not yet a paginated or eligibility-confirmed submission.

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
- Hash-bound checkpoints, rejected attempts retained, French draft PDFs and
  atomic folder publication. All outputs remain non-official, unreviewed drafts.
- Native French workspace, consent before downloads, selected French interface
  translations, local Ollama endpoint, standard/enlarged print, history metadata.
- Human review-record API tied to artifact hashes. Reviewer identity is self-attested,
  not authenticated; this is not an official signature or school approval system.

## Evidence and limits

Four seed PDFs are locally acquired with pinned hashes: Terminale programme,
2027 language rubric, 2026 Métropole subject and one centres-étrangers holdout.
The official archive index has been traversed: 79 NSI entries and 122 linked
documents (114 PDFs/eight Braille ZIPs), preserved in the discovery snapshot.
The full 2021–2026 **content reconciliation remains incomplete**: download hashes,
duplicates, rights and holdouts are not established for those newly discovered links.
Only the four-source seed corpus is retrieval-enabled.
Python's certificate store failed on Eduscol in this development environment;
verified system curl obtained the programme. No insecure TLS mode was used.

The measured Métropole source is A4 (595.32 × 841.92 pt), mainly Arial 12 pt,
with Courier New 12 pt code. The renderer is **PROTOTYPE**: compatible fonts and
geometry, not pixel identity. Structured diagram/table rendering, exhaustive visual
comparison, calibrated originality thresholds and whole-topic reference coverage
are not yet qualified. Equal six-point exercise allocations are a product choice,
not an official 2027 allocation. Timing estimates and AI difficulty judgements are
not empirical calibration. Restricted code evaluation does not support all Python.

No French live model benchmark has run: the separate UK matrix still owns the
local model. No French model is recommended as validated. No teacher-reviewed
release, student pilot, Intel test or multi-memory hardware matrix exists.

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

## Prize preparation — PLANNED

The announced deadline is 2 November 2026. Confirm applicant enrolment eligibility,
prior-funding restrictions and whether this educational/territorial proposal fits
the competition's regional and sustainable-development remit with the organisers.
The prescribed application is limited to three pages. Prepare an honest prototype
demonstration and twelve-month plan; do not promise final qualification by deadline.
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
