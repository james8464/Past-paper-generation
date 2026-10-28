# Accounting V10 live Paper 1 review

## Result: HOLD

One fresh source-runtime run used seed 270100 and local Gemma 4 12B digest
`4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`.
It completed automated generation and reference-demand checks in 2,457.89 seconds.
This was source execution, not a frozen-helper run. The fixed-source Python suite
passed 3,885 tests with two skips before generation. Neither result establishes
paper quality by itself.

Retained run: `tmp/final-validation-20261028/accounting-live-quality-run3`.
Retained renders: `tmp/pdfs/accounting-live-v10-20261028`.

| Artifact | SHA-256 |
| --- | --- |
| Question paper, 36 A4 pages | `67dbeb294ef35c56e83e74e72f15b2cac7eaea26178459b84a261ecc1a8f2733` |
| Scheme, 26 pages | `9b98b6b239ee82fed4774181f855d88793148a9c4e3bf4720939f4f4c7ffe82d` |
| Assessment JSON | `c85fc4e56d7d73fbc989086c773a825ce3e6e715c2d63b5ae9ca46dd225b55ea` |
| Package | `e144c8722d1fb209aaa095c96d6574c9461be8dc897f324400b31e9e3777335e` |

## Review coverage

The main reviewer visually inspected all 36 generated question pages, all 26
scheme pages and all 36 pages of the local AQA 7127/1 June 2025 question paper.
The final official pages 25–36 were inspected separately after a multi-image
tool result was truncated. No clipping, overlap or missing glyph was found in
the generated pages. Deliberate blank and response pages are not renderer
failures. Matching the official booklet's page count is not evidence of matching
difficulty or task quality. The official paper remains outside the distributed
app.

Independent read-only reviews recomputed 52 numeric assertions using Decimal
from public figures, without calling production solvers. The ten MCQ keys and
the asset, ledger, income, partnership and investor calculations agreed. In
particular, Q14 profit for the year is £1,701,298. No arithmetic discrepancy was
found in those checks. They do not establish complete semantic correctness,
observed timing or calibrated difficulty.

## Source-bound findings

1. Q03 prints alternatives within its stem and again as structured options.
   Reject or repair that writer output at the MCQ boundary, not just in the PDF.
2. Q15.3 uses Bracken Retail from Q14 instead of its partnership case. Its stored
   generic context also differs from the printed case. Q16/Q17 retain unprinted
   generic profit facts; the same entity name describes incompatible legal
   forms across those independent cases. Public authoring and review inputs
   must match candidate-visible source data, rather than merely renaming a stem.
3. Persisted marking allocations and specialised Paper 1 printing disagree.
   Q13.1 persists 2/2/1 while printing five one-mark entries; Q13.2 persists two
   marks on the debit/transfer line while printing one for each account side.
   Q15.1 gives a genuine goodwill credit no mark. Generic hydration interprets
   accounting lines beginning `Credit ` as guidance. Accounting needs an
   explicit credit contract before that fallback, shared with its renderer.
4. Q11 persists six separate points but prints two developed reasons assessed
   up to three marks each. Q12's printed 3/3/1 grouping can fit seven marks, but
   working marks are not labelled as included and an extra presentation award
   is unsupported by the stored contract. This is ambiguity, not proof that
   twelve marks are available.
5. Q14.1 supplies a fixed £399,070 current-year tax expense. Its follow-through
   note wrongly permits a tax charge recalculated from the student's profit,
   even though no tax rate is supplied.
6. Scheme page 17 repeats general AO and level guidance within Q14.2 indicative
   content after the level table. Similar general guidance appears in the long
   Q16/Q17 answers. Front-matter pages contain different guidance and should not
   all be described as duplicate pages. Separate general guidance from typed
   question-specific content; do not broadly delete genuine accounting credits.
7. Reasoning depth and variety remain limited. Generated MCQ7/9 are direct
   arithmetic, while official examples combine reverse percentages, movements,
   entry sides and accrual effects. Longer cases provide alternatives and
   conditional judgements, but no equivalence or timing claim is justified.

## Next acceptance boundary

Keep this run and its automated result unchanged. Introduce a new Accounting
version for public-case projection, explicit marking contracts and writer
validation. Add failing source/PDF/serialization tests first. Recheck original
multi-step MCQ variants independently, then freeze source and rerun complete
paper acceptance. Do not start Paper 2 or the expensive final provider matrix
while these known Paper 1 defects remain. Teacher review and empirical learner
calibration remain unperformed; no such evidence is invented here.
