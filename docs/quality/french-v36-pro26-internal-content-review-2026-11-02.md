# Historical French V36 Pro26 internal content review

The retained Pro26 paper contains substantive defects despite its positive model
reviews. It remains diagnostic evidence and does not establish current-source
French release acceptance.

## Artifact identity and scope

The original artifact directory is:

```text
/Users/james/.codex/worktrees/french-nsi-integrity/Past Paper Creation/tmp/french-v36-live-20261030/deepseek-pro-run-26-contextual-clauses-270201
```

Within that directory, the reviewed files and SHA256 values are:

| File | SHA256 |
| --- | --- |
| `private-output/nsi-2027-v36-270201-7f3ba45fb428/assessment.json` | `151c603917924cc7768154958cb8efb7518e7d9eb1254a63591d441d331be43d` |
| `result.json` | `8419b5842ea07e7f6b6eb6bf8707f499910e043dae4ba27a37f939fd4bb3bda9` |
| `job.json` | `99447312aad5ba3062c5c65f3dc97d4c623a5c7041d16cf36b7eb4e946c698cc` |

The job records source commit `7ecc61265359b3634bb7d6117f36908696f1ad87`,
implementation SHA256
`963ddfb9dc94aa327a59e0ec14c6ab709df8fd7b55439b01ff69be49ee1266ec`,
model `deepseek-v4-pro`, and seed `270201`. The result records 15 completed calls,
return code 0, 1,741.54 seconds elapsed and unchanged source. The package identifies
itself as an `unreviewed_draft`, with teacher review and empirical calibration
`not_run`.

This internal review read all 16 accepted questions (5, 6 and 5 per exercise),
their contexts, materials, proposed answers and credit criteria, plus the complete
three accepted blind-solver responses and their reviewer responses/dispositions.
Retry outcomes were inspected for provenance; rejected replacement drafts were
not included in this whole-paper content assessment. No private reasoning text
was used. These are internal checks, with no teacher or learner review claimed.

## Confirmed content and marking issues

1. E3 Q4 requires an unsupported testing advantage. Both supplied counting
   functions are observationally pure when they use the same pure predicate:
   neither changes its inputs or external state, and both accept the same
   input/output tests. The correction treats the imperative function's local
   accumulator as an effect that makes its tests less straightforward. Local
   mutation alone does not establish that distinction. The rubric awards credit
   for the claimed testing advantage and also requires predicate reuse, which
   the question does not request. The reviewer accepted all flags for this item.

2. E3 Q2 does not enforce its stated character contract. Its proposed
   `isalpha()`/`isupper()`/`isdigit()` solution accepts `LIV-²²²²`, although the
   suffix is not four decimal digits. It also accepts `A中A-2024`, although not
   every letter is uppercase: `isupper()` ignores uncased letters. The blind
   answer instead tests ASCII ranges. The context does not resolve that alphabet
   difference, and the reviewer accepted both answers without discussing it.
   Harmless built-in checks on these literal strings confirmed the character
   classifications; no model-authored program was executed.

3. Some credit criteria impose an unrequested method or task. E2 Q5 reserves
   0.25 marks for `if zone in vus: continue`; enclosing neighbour expansion in
   `if zone not in vus:` is another correct minimal repair. E3 Q2 requires the
   length test before every access, excluding safe alternatives that do not need
   that order. E1 Q4 reserves 0.5 of 1.25 marks for restating the supplied
   decomposition and keys, although the question asks for anomalies and an
   explanation of their elimination. The positive reviews missed these rubric
   restrictions.

4. E1 Q1 omits declared primary-key information. The context announces an
   underlining convention, but its authored schema contains no underlined keys
   and explicitly identifies only the composite `inscription` key. Distinct
   values in the shown extracts do not establish the designated primary keys of
   `membre` and `atelier`. The blind solver raised the missing underlining; the
   reviewer dismissed it using identifier names and foreign-key notation. Those
   conventions do not supply the missing declaration.

E1 Q4 also uses `sami` as its repeated-row update-anomaly example, although the
shown register contains only one `sami` row. The duplicate `luna` rows support the
intended illustration. E3 Q5's proposed halting argument leaves its constructed
program unclear; the blind response provides the explicit construction that
executes an arbitrary program/input and then returns `True`. These observations
further limit confidence in the proposed correction.

## Independently checked positive cases

E1's SQL insert/update statements match the displayed relation order and values.
The SELECT joins and descending-date/ascending-pseudo order give
`yac/2025-09-02`, `luna/2025-09-01`, `sami/2025-09-01`, then
`luna/2025-08-20`, using the printed extracts. The repeated member is associated
with different dates. These checks do not settle whether Q2 mutations should
carry into Q3; the questions would benefit from an explicit state convention.

E2's minimum weighted route is correctly 10 minutes via S-A-D-F. Its neighbour
list, connectivity/cycle examples and matrix row for D agree with the graph.
The stack traversal and cycle-repair reasoning are coherent; the breadth-first
comparison correctly concerns edge count, not weighted duration. E3's five
classification examples and the two illustrated debugging tests are correct.
The proposed credit totals are 6 points per exercise.

## Programme, variety and acceptance limits

The registered Terminale programme source is `nsi-terminale-programme-2019`,
SHA256 `10ce34666edd722a3d8d86642a9f1ac205c7a9d128d6142a17effcba2fb85e69`.
Its retained pages 4-8 cover the assessed database, graph, programming-paradigm,
debugging and computability topics. The reference-only registration was checked
read-only in the local reference index. The retained official comparator
excerpts include database work in 2026 papers and graph/pile/file tasks in 2025
and 2021 papers. The exercises contain different assessed work, including query
construction, graph traversal/debugging and programme-contract reasoning.

The paper's nominal 70 minutes per exercise and declared difficulty values have
no observed learner timing or empirical calibration. This content review does
not establish originality against the full corpus, visual quality, full syllabus
coverage or a comparative model ranking. Pro26 demonstrates that the historical
route completed a model-authored paper; the false acceptances above prevent using
that completion as educational qualification.

No artifact was changed, replayed under a new identity or rebound to current
source. This review made no inference request and incurred no provider spend.
The separate code checks recorded for source commit
`024cbc4cf6b98c30c66b2d47f1b624e43404b391` are unchanged by this documentation-only
note. Current-source full-paper acceptance remains separate.
