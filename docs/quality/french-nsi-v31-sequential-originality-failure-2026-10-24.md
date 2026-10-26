# V31 sequential originality failure - 24 October 2026

## Release verdict: FAIL, do not merge as a completed variety fix

One three-seed live diagnostic ran on clean source `e7bb973`, implementation SHA-256 `8411f8c8c4336a8f18ad32869557cfdcdafdf19e3d246d88dbeb53019c1adb7c`. Source did not change during the run. Model: `gemma4:12b`, digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`; reference-index SHA-256 `ec2339e6dffeba485f94d33d8e6f868e24cd2c40ad32830621201496ca32d594`.

| Seed / family | Outcome | Elapsed | UTC completion |
|---|---|---|---|
| 270100 / minimum | First-attempt pass, zero repairs | 143.220 s | 00:47:56.395513 |
| 270101 / budget | E1 rejected after three attempts: previous-generation originality | 84.203 s | 00:49:20.780488 |
| 270102 / continuity | E1 rejected after three attempts: previous-generation originality | 84.475 s | 00:50:45.316460 |

Failed runs published no manifest or partial paper. Runner repair-attempt counts are 3 for each failed result; this is its recorded count, not a claim that a fourth attempt ran. The process exited 1. All results, raw attempts, checkpoints and selections remain ignored under `tmp/pdfs/french-v31-task-families-20261024/`; do not delete or relabel them as replay or success.

The accepted sample has 12 subject pages/34 questions and 24 correction pages. All 36 Poppler 80-dpi PNGs are byte-identical to inspected V30 renders; its visual findings carry forward exactly. No accepted budget/continuity live PDF exists. Earlier local fixture render inspections do not substitute for those missing outputs.

| Accepted artifact | SHA-256 |
|---|---|
| Subject | `0987e84820accf2ec972dbfc19b8c74b9b5da6b8f20fd7ecefe63a5b869d49f7` |
| Correction | `89f50215707225f980739a7abd24c6880662da43d4644a83b0d6eb5b9c2d418f` |
| Assessment | `541f5f1be1239f1357c4fec9e40879db767d6377e433098a6d4f60eb31a3a521` |
| Manifest | `d36023a7564432bebf1bfe78231140a35323c9b36b6ae1dbcf9f7203d9bd59c5` |

## Diagnosis

The new algorithm is different, but the remainder of each exercise is not sufficiently different. Deterministic fixtures from the exact V31 code reproduce this without a model. Comparing candidate text (title, context, prompts) with seed 270100 gives:

| Exercise / next seed | Longest shared prose characters | Prose five-gram Jaccard | Prose sequence | Normalised code four-gram Jaccard |
|---|---:|---:|---:|---:|
| E1 / 270101 | 854 | 0.568966 | 0.855856 | 1.0 |
| E1 / 270102 | 854 | 0.480692 | 0.784071 | 1.0 |
| E2 / 270101 | 3051 | 1.0 | 1.0 | 1.0 |
| E2 / 270102 | 3051 | 1.0 | 1.0 | 1.0 |
| E3 / 270101 | 2624 | 1.0 | 1.0 | 0.0 |
| E3 / 270102 | 1574 | 0.930894 | 0.991684 | 0.0 |

Existing rejection thresholds are respectively 160, 0.45, 0.78 and 0.70; any threshold is sufficient. E1 retains the same tree-construction block and supplied code. E2 candidate text is identical. E3 is identical or almost identical. Therefore this is not merely a harmless common-helper false positive: prose/task repetition independently fails every exercise comparison. Thresholds and history remain unchanged.

The earlier 2,975-pass full suite and 115 targeted passes did not test sequential-history acceptance. Six new release-acceptance cases in `test_successive_families_are_substantively_distinct` now fail, one for each exercise/seed pair. A seventh end-to-end test, `test_three_successive_packages_pass_with_preserved_history`, reproduces the live failure at seed 270101 with all preceding exercise texts retained. These are deliberately red on the isolated development branch, not waived or marked xfail. The branch is not ready for a protected merge. Primary main remains the earlier clean V30 baseline.

## Required next engineering work

Expand complete original exercise families, including case, public inputs, tasks, supplied code and reasoning obligations across E1, E2 and E3. One changed item, synonym substitutions, altered numbers, history deletion or weakened similarity thresholds cannot meet this acceptance criterion. Preserve the useful independently checked algorithm variants, but integrate them into substantively different whole exercises. Add sequential end-to-end tests using the same output history; do not only test isolated seeds. Then freeze source and run a new retained three-seed diagnostic before publication.

Use a new V32 identity for that repair rather than silently rewriting the accepted V31 catalogue. Move the future acceptance target to V32 while retaining an explicit V31 rejection/replay regression. Finite family coverage must remain explicit; three seeds cannot prove unlimited novelty. Any future distinction between reusable scaffolding and task repetition requires labelled calibration and must still reject the identical E2 tasks demonstrated here.

Official 2026 Metropole day 2 pages 5, 8 and 9 were re-viewed in this turn: object methods, explicit inversion definitions, test construction, code repair and composition form connected tasks. This supports the need for varied coherent task sequences, not copied wording. The registered PDF SHA-256 was rechecked: `885f3687ea83486efb9a17c08467a5fed6f7b11fb629ca65ba103240ddd37db9`. No official PDF is bundled and no official correction was newly assessed.

Full-app and French qualification remain incomplete. No teacher, learner, model-independent, accessibility or Apple approval is claimed.
