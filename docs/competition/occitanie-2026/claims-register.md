# Competition claims register

Updated 8 October 2026. The status labels are deliberately strict.

| Claim | Status | Evidence or next gate |
|---|---|---|
| A distinct French Terminale NSI generation path exists | IMPLEMENTED | French education context, assessment rules, prompts, validation and rendering are separate from UK policies. |
| Papers follow the announced 2027 written structure | IMPLEMENTED | Three independent exercises, 210 minutes, 18 technical points plus a separate two-point language component. |
| PDF layout is reference-informed | PROTOTYPE — FIDELITY HOLD | A4 geometry and cover positions were measured against the official 2026 Métropole paper. All seven subject and eleven correction pages from a pinned live v17 diagnostic were inspected. The subject has 18 numbered questions versus 36 in the 16-page official comparator, with an orphaned final question, crossed graph edges and dense Dijkstra correction. See `docs/quality/french-nsi-v17-live-diagnostic-2026-10-08.md`. |
| All three exercises have locked app-owned question, answer and credit contracts | IMPLEMENTED ENGINEERING | Versioned graph/tree, SQL and network data drive French prompts, answers and exact credits; checkpoint, package replay and PDF checks preserve identity. This does not establish educational correctness or teacher approval. |
| The software produces examiner-approved papers | NOT CLAIMED | Requires two independent French NSI reviewers and revision of six stratified papers. |
| Difficulty is equivalent to the real baccalauréat | NOT CLAIMED | Current controls constrain cognitive mix; empirical timing and difficulty require a supervised pilot. |
| The complete visible 2021–2026 archive is reconciled locally | IMPLEMENTED | 79 canonical papers plus two foundational documents have pinned hashes; 13 papers are holdout-only, 43 accessibility representations are aliases, and two duplicate-content groups are collapsed in retrieval. Source PDFs remain local and reference-only. |
| A resumable local-model benchmark exists | IMPLEMENTED | Fixed seeds, model/source/code identity, checkpoints, failure preservation and duplicate-run locking are implemented. |
| A French live benchmark has selected the best model | IN PROGRESS — NO MODEL SELECTED | The first Gemma 4 12B campaign accepted 0/10; failed one-paper diagnostics and their attempts remain retained. A later single-paper gemma4:12b v17 run passed automated checks on its first attempt, but manual PDF comparison placed it on fidelity hold. This is not a ten-paper qualification or comparative model result. See `docs/quality/french-nsi-v17-live-diagnostic-2026-10-08.md`. |
| A Toulouse/Montpellier teacher pilot exists | PLANNED | No school or teacher partnership is claimed until written agreement exists. |
| Regional open data is already used in generated exercises | PLANNED | Intended optional module; values and provenance must remain distinct from synthetic exercise data. |
| Students need a Mac or AI account | FALSE | Students receive ordinary PDFs; generation remains on the teacher's Mac. |
| The project is endorsed by a public authority | NOT CLAIMED | No endorsement exists. |
| The app is suitable for every Mac | NOT CLAIMED | Hardware support depends on measured model quality, memory and latency. |
| The project is GDPR compliant | NOT CLAIMED | Local-first design reduces data transfer, but each school needs its own governance review. |
