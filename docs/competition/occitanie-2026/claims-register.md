# Competition claims register

Updated 6 October 2026. The status labels are deliberately strict.

| Claim | Status | Evidence or next gate |
|---|---|---|
| A distinct French Terminale NSI generation path exists | IMPLEMENTED | French education context, assessment rules, prompts, validation and rendering are separate from UK policies. |
| Papers follow the announced 2027 written structure | IMPLEMENTED | Three independent exercises, 210 minutes, 18 technical points plus a separate two-point language component. |
| PDF layout is reference-informed | PROTOTYPE | A4 geometry and cover positions were compared with the official 2026 Métropole paper. A v12 graph/tree fixture was also inspected in standard and large print, but its figure is smaller and its other two exercises remain generic. No complete live 2027 PDF has passed visual review; the 2027 profile remains provisional. See `docs/quality/french-nsi-v12-pdf-verification-2026-10-06.md`. |
| The first graph/tree exercise has a locked prose and answer contract | IMPLEMENTED ENGINEERING | A finite French catalogue renders the six instructions, answers and exact credits from graph/tree data. Selection, catalogue digest, checkpoint, package replay and extracted-PDF checks are covered by deterministic tests. This does not qualify exercises 2–3 or establish teacher approval. |
| The software produces examiner-approved papers | NOT CLAIMED | Requires two independent French NSI reviewers and revision of six stratified papers. |
| Difficulty is equivalent to the real baccalauréat | NOT CLAIMED | Current controls constrain cognitive mix; empirical timing and difficulty require a supervised pilot. |
| The complete visible 2021–2026 archive is reconciled locally | IMPLEMENTED | 79 canonical papers plus two foundational documents have pinned hashes; 13 papers are holdout-only, 43 accessibility representations are aliases, and two duplicate-content groups are collapsed in retrieval. Source PDFs remain local and reference-only. |
| A resumable local-model benchmark exists | IMPLEMENTED | Fixed seeds, model/source/code identity, checkpoints, failure preservation and duplicate-run locking are implemented. |
| A French live benchmark has selected the best model | IN PROGRESS | The first Gemma 4 12B campaign accepted 0/10 papers. Its ten checkpoints, per-seed results and event logs are retained locally. Six fresh one-paper diagnostics on 4 October each accepted 0/1; the v10 run again exposed false-positive automated exercise review and failed all three attempts at the SQL/table exercise. See `docs/quality/french-nsi-evaluation.md` and issue #26. New pinned live runs, other candidate models and teacher review are still needed. No model is selected yet. |
| A Toulouse/Montpellier teacher pilot exists | PLANNED | No school or teacher partnership is claimed until written agreement exists. |
| Regional open data is already used in generated exercises | PLANNED | Intended optional module; values and provenance must remain distinct from synthetic exercise data. |
| Students need a Mac or AI account | FALSE | Students receive ordinary PDFs; generation remains on the teacher's Mac. |
| The project is endorsed by a public authority | NOT CLAIMED | No endorsement exists. |
| The app is suitable for every Mac | NOT CLAIMED | Hardware support depends on measured model quality, memory and latency. |
| The project is GDPR compliant | NOT CLAIMED | Local-first design reduces data transfer, but each school needs its own governance review. |
