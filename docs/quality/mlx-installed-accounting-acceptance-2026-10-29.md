# Installed Apple MLX Accounting acceptance

Date: 29 October 2026. This records two real native attempts, not checkpoint
replay. One model completed one paper; the smaller default model did not.
It does not qualify every paper, provider, difficulty level or release build.

## Fixed application and model identities

Both attempts used installed PR116, merged as
`4427e1c642c5ffe36eb26f9529eae5bd3ea0652e`. Application production code and
executables stayed unchanged throughout generation. Later release-safety
source changes require their own gates and do not inherit this acceptance.

| Identity | SHA-256 |
| --- | --- |
| Installed frontend | `b5bca6515aed65c2c890354446af0fd186cad4a2591a34dbc30b2c15f96d37d8` |
| Installed frozen helper | `6158ff7cf0fe4c05d2b1b940b66ed1648a855c339427bae17fd35df528cfc25e` |
| Source Core identity | `15ad925de29b2efbd10c1b0a7f520fd9aac4c10302d429ac92ac5f762d2b083d` |
| Source runtime identity | `605cb2f99ca371503abaac72bd8dc0ef6f2860378c9e765ae2119fafb30191bf` |

Read-only preparation recorded cached model files and hashes before generation.
Llama-3.2-3B-Instruct-4bit resolved to revision
`7f0dc925e0d0afb0322d96f9255cfddf2ba5636e`; Qwen3-8B-4bit to
`545dc4251c05440727734bcd94334791f6ab0192`. Both cache references were checked
again after the attempts and were unchanged. The cache record is retained at
`tmp/mlx-final-acceptance-20261029/cache-preparation.json`.

## Outcomes

The Apple MLX route ran from the installed native application with Accounting
AQA Paper 1 selected and preview disabled. Guided setup checked support and
prepared the selected model. No administrator prompt, hosted-consent agreement,
security change or application-source change was used to obtain a result.

| Model | Seed | Native outcome |
| --- | --- | --- |
| `mlx-community/Llama-3.2-3B-Instruct-4bit` | `1638859718` | Failed the item-quality process after accepting one item; failed history entry, no published artifacts |
| `mlx-community/Qwen3-8B-4bit` | `1112969546` | Completed and published four artifacts at 11:08:23 UTC |

The smaller-model attempt establishes runtime startup, not complete-paper
acceptance. Its exact final raw refinement reason was not retained, so this
record does not infer one from the generic quality alert. Its original failed
checkpoint remains in `native-default-output`.

The Qwen attempt included repairs. Native Quality Activity showed two exact-
paraphrase refusals for item 11 and two overlong prompt refusals for item 14.2
(29 then 24 words against a 15-word limit). Generation subsequently accepted
those items. The printed final 14.2 stem has 13 words. This was not a zero-repair
run.

## Published bytes and validation

All paths below are relative to the isolated checkout's ignored
`tmp/mlx-final-acceptance-20261029/native-qwen-output/` directory.

| Artifact | SHA-256 |
| --- | --- |
| `accounting-aqa-paper-1-package.json` | `5af9817f96e5aac0b09897e5f2c58f14b4999e2354a96e18d582d7409f9829fa` |
| `aqa-accounting-paper-1-assessment.json` | `0570070206149c5c64f15a8906d0f225106c5e9ae6b96e3c6860063e542e4fd8` |
| `aqa-accounting-paper-1-question-paper.pdf`, 36 pages | `c8e010e088941cd48c52cf2e262ed7825f82388dfd715eec321ca6859cc1753d` |
| `aqa-accounting-paper-1-mark-scheme.pdf`, 24 pages | `b75280e314beccd43722f5f118f414135a339411dcda424fe44513bfc2d36f5b` |

The manifest passed blueprint, mark distribution, mark scheme, question type,
release, renderer, runtime, syllabus, uniqueness and visual gates. Difficulty
was not empirically calibrated. Its qualification separates engineering and
visual acceptance from the false empirical-calibration field.

All 60 PDF pages were freshly viewed in 15 four-page Poppler 100dpi grids.
There was no observed clipping, overlap, missing table row, unintended blank
page or unreadable body. Headers, footers, answer areas and table rules were
consistent. General marking guidance appeared once. Question-paper pages 7,
27 and 33 were deliberately crossed-out blank pages. Source-only pages 10 and
18 and some scheme continuations were sparse. Matching an official paper's
page count does not establish equivalent pacing or difficulty.

A separate Decimal-based audit did not call the production solver or a model.
It passed 55 numerical checks and four equity reconciliations, checked all ten
MCQ option sets and printed key parity, and reconciled 120 marks into sections
30/40/50. It found no substantive arithmetic or keyed-answer error. The initial
audit harness disagreed only over terminal punctuation in an expected answer;
the original harness failure is retained and was not a paper arithmetic error.
The final record is `native-qwen-review/independent-arithmetic.json`, SHA-256
`91792cd917a0a1ba1ad9d03d157725c938de3c1bbe7da2419c791e6f0a474e29`.

Editorial limitations remain: question 02 has an unnecessary parenthetical
and an implicit percentage-conversion convention; question 10 says
“Professional Integrity” rather than the simpler principle name “Integrity”.
Reusing a company name across separately labelled sole-trader and PLC cases
limits contextual variety, though the entity labels distinguish the cases.
These observations do not establish a wrong key.

## Native checks and limits

Completed history recorded the chosen model, selected seed and all four
artifacts. Documents opened the actual PDFs. Cmd-P showed all 36 question-paper
pages and all 24 scheme pages; both print panels were cancelled. No printing,
export, credential change or clipboard modification occurred. Original provider,
saved model, output directory, privacy tab and benchmark navigation were restored.
All retained user history and documents were preserved.

A separate UI check found that the old segmented document selector overflowed
with 30 saved PDFs. That is a native presentation defect, not a defect in the
published PDF bytes. Its replacement and selection/action consistency require
separate tests before release.

The evidence is one Accounting AQA Paper 1 sample on this Mac. It supplies no
teacher review, observed learner timing, complete provider/subject matrix,
PDF/UA certification, full-HIG claim or App Store approval. The failed default
model attempt remains a release limitation. The direct MLX route's existing
runtime-install restrictions, `trust_remote_code=false`, signing and security
protections were not weakened.
