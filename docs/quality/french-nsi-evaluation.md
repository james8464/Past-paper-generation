# French NSI evaluation protocol

Status: engineering prototype; no live model or teacher qualification recorded.

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
wrong. Existing contiguous-text screening is uncalibrated and does not establish
copyright compliance or algorithmic originality. Add labelled copied/renamed/new
examples before setting qualified thresholds. No numeric "similarity" percentage
is a substitute for examiner judgement.

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
