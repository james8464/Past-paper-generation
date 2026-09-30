# French NSI evaluation protocol

Status: engineering prototype; a live model campaign is running, but no accepted
candidate-model campaign or teacher qualification is recorded.

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
