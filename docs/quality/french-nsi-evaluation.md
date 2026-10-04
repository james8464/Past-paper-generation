# French NSI evaluation protocol

Status: engineering prototype. The first complete Gemma 4 12B campaign finished
with zero accepted papers out of ten. No candidate-model or teacher qualification
is recorded.

## First complete live campaign (30 September 2026)

The earlier run at
`tmp/qualification-fr-nsi-2027/gemma4-blueprint-v4/benchmark-summary.json`
recorded ten failed papers from seeds 270100–270109, with thirty rejected
exercise drafts and one accepted exercise retained in per-seed checkpoints. The
implementation hash was
`bd1468ca74a1dbe501e5eedc306d26531fb52ff9a6271b20fc13607cbfafbfbb`;
the reference-index hash was
`8244bb8e149aa6d4ab6dabc96529dc220810209f9ef27fe09d6d86260e4fdea6`;
the model digest was
`4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`.
One seed accepted an initial exercise but failed the next. Most rejected drafts
omitted the question-to-figure identifiers needed to prove use of the structured
graph or table. Other failures included mismatched question plans, marking totals,
invalid decimal strings and duplicated graph edges. These are output-quality
failures, not paper passes. The model cannot be recommended for French NSI on
this evidence. Test the other exact candidate models and review the generation
architecture before another ten-paper campaign.

On 4 October 2026, the ignored run directory was recovered from an older
managed worktree and copied into the primary checkout. The summary, ten
per-seed results, ten checkpoints and event logs are now available at the path
above for audit. This recovery does not alter the 0/10 outcome or qualify the
old source/model configuration. A new identity-pinned run is still required
after the authoring redesign.

## 4 October diagnostic (not qualification)

A fresh one-paper Gemma 4 12B diagnostic at seed 270100 retained three rejected
exercise drafts and accepted no paper. Its raw checkpoint is under
`tmp/qualification-fr-nsi-2027/diagnostic-20261004-gemma4/`. All three drafts
omitted `material_ids`; two nevertheless referred to the exact graph ID in
question prose. This exposed an authoring-protocol failure, not a reason to
accept unlinked figures. The subsequent narrow repair recovers only exact IDs
written in a question when the JSON field was omitted, records the untouched
candidate, its digest and inferred links, and revalidates their consistency
with the package. Deictic mentions such as “le graphe G fourni” without a
structured link are rejected per question; other vague uses may still require
human judgement. These hashes catch accidental or isolated edits, not a
coordinated rewrite of the package: the independently stored artifact manifest
is the separate integrity boundary.
The prompt now explicitly requires both the question reference and its JSON
link. This source change invalidates the diagnostic as a qualification run;
new pinned live evidence is required. The drafts also contained substantive
questions needing independent review, so the repair does not establish
educational quality.

A second source-pinned, one-paper diagnostic using the v5 prompt also accepted
0/1 at seed 270100. Its three rejected drafts are retained under
`tmp/qualification-fr-nsi-2027/diagnostic-20261004-v5-gemma4/`. Two failed
the per-question blueprint; one named figure IDs without supplying any
`materials`. The model's transport schema had treated `materials` and each
question's `material_ids` as optional because the package reader retains
defaults for historical records. The v6 authoring schema now requires those
fields, while the package model continues to read recorded v4/v5 evidence.
This is a structural output constraint, not a claim that question content or
difficulty has improved. A fresh v6 run is required before judging that.

The pinned v6 one-paper Gemma diagnostic on 4 October also accepted 0/1
(seed 270100; implementation
`cba1b74b98c236608d983242778de8db6c3e891142e4ea635ebb0c7fd776c69d`).
All three rejected drafts and the benchmark summary are preserved under
`tmp/qualification-fr-nsi-2027/diagnostic-20261004-v6-gemma4/`. Two drafts
missed the detailed question blueprint; one left an explicitly named graph
unlinked. No PDF was published. Inspection showed that cyclic programme-code
assignment makes the six-question plan less coherent than the contextual parts
observed in the historical 2026 Métropole paper. The first redesign slice
groups question intents into contextual parts and replays their blueprint when
a package is reopened. Its remaining semantic-alignment and targeted-repair
gates are recorded in
`docs/superpowers/specs/2026-10-04-french-nsi-authoring-redesign.md`.
This slice has not passed a live paper and is not a model recommendation.

The source-pinned v7 diagnostic also accepted 0/1 complete papers (seed 270100,
implementation `20c0a8fa1f53825d6598ae1f1af59a1cee2ddbc946c4a0fd7c49233e79e0bcdf`,
model digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`).
The raw checkpoint and result are retained under
`tmp/qualification-fr-nsi-2027/diagnostic-20261004-v7-gemma4/`. All three
attempts at exercise 2 failed because its questions did not link the declared
table; its SQL drafts also described relations not supplied as structured
data. Exercise 1 was accepted by automated gates but manually rejected: it
described an invalid binary-search tree, posed an underspecified full-function
task for one point, and had a BFS debugging answer/marking mismatch. All six
question-level deterministic checks were unresolved, while the AI review
reported no issues. No PDF was produced. This is a false-positive defect in
automated content review, tracked in GitHub issue #26, not a paper pass. The v8
slice binds only exact figure identifiers and records immutable question-plan
assembly. The v9 source slice adds an answer-free, item-level AI alignment
decision for every planned capability, rejects missing or contradictory
decisions, and binds those decisions to the exact candidate view on replay.
This gate has regression tests but no live model evidence yet. A model may
still make a wrong positive judgement; bounded targeted repair and independent
teacher review remain outstanding.

## Reproducible runs

Pin the repository commit, registry/prompt version, full source hashes and split,
model digest and quantisation, Ollama/runtime version, context budget, hardware,
memory and seed. Do not run alongside the UK live matrix. Never silently reuse
checkpoints after identity changes. Keep rejected outputs as failed evidence.

Candidates: gemma4:12b, ministral-3:8b, qwen3:8b; 16K initial context. Download
sizes are not RAM requirements. Benchmark 30 fixed exercise tasks per model before
selecting a French recommendation; correctness and French NSI teacher judgement
outweigh speed. Then use ten new whole-paper seeds. Quantisation changes need
fresh evidence. Missing hardware is untested, never an inferred pass.

The executable protocol is `tools/run_french_nsi_qualification.command`. It runs
ten complete papers per model, giving thirty exercises per configuration. A global
lock prevents duplicate campaigns. Accepted checkpoints are reused only when the
implementation hash, reference-index hash, model digest and seed match. Failed
attempts remain failures unless an explicit reviewed retry is requested.

An accepted run is resumed only when its manifest fingerprint, assessment identity
and every recorded artifact hash still match. If accepted evidence is missing or
changed, the runner stops before contacting the model; investigate and preserve
the directory rather than silently replacing the paper.

## Rubric

Score each dimension 1 (unusable), 2 (major revision), 3 (minor revision), 4 (ready
for supervised practice). Record item IDs, concrete issues and corrected answers.

| Dimension | Required judgement |
|---|---|
| Correctness | Every premise, algorithm, query and solution is valid |
| Curriculum | Terminale coverage is justified; Première is prerequisite only |
| Language | Natural academic French; precise terminology and no translation artefacts |
| Difficulty | Comparable reasoning, scaffolding and unfamiliarity to held-out annales |
| Timing | Plausible student workload, reading/code/diagram overhead included |
| Marking | Exact credit, alternatives, dependencies and no duplicated rewards |
| Layout | Readable code/figures, authentic structure, no clipping or misleading branding |
| Originality | New task/context/solution structure, not superficial renaming |

Approval requires correctness and marking = 4, all other scores >= 3, and written
notes. This operational threshold is a product rule, not a Ministry standard.
Two teachers must independently assess six stratified papers. A single local
self-attested review record is not sufficient for release qualification.

## Failure policy

Deterministic failure blocks publication. Unsupported verification remains
unresolved. Model review is supplemental: agreement between models can still be
wrong. Current screening compares text n-grams, normalized code, question structure
and generation history. Its thresholds remain unqualified until labelled copied,
superficially renamed and genuinely new examples establish precision and recall.
No numeric "similarity" percentage is a substitute for examiner judgement.

## Artifact review

Review the subject, correction and metadata together. Approval is attached to
manifest and artifact hashes; any file edit invalidates the review. The record
does not authenticate credentials. Do not change a generated package's internal
teacher-review state to passed: preserve its original AI provenance and store the
human record separately. Do not collect student names or answers in the app.

## Pilot measurements

Teacher preparation/correction time, first-pass defect count, student completion
time, item ambiguity, accessibility issues and actual access constraints. Report
sample size, missing data and uncertainty. Small convenience samples cannot
establish regional impact or psychometric equivalence to a national examination.
