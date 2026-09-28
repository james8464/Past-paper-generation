# AQA Computer Science bank-item reference support

## Scope and result

This is a source-comparability check for the **generated items**, not empirical
difficulty calibration, a whole-topic certification, or a scaled full-paper AO
target. Learner demand, observed completion times and source reasoning-step
counts remain unknown. The banks retain their designed 30 marks / 45 minutes.

| Bank | Previous broad operation/mode matches | Reviewed redesigned bank | Matched source years | Content families |
| --- | --- | --- | --- | --- |
| 4.2 Data structures | 7/14 | 12/12 | 6 | 10 |
| 4.10 Databases | 8/10 | 11/11 | 4 | 11 |
| 4.12 Functional programming | 5/10 | 13/13 | 6 | 8 |

These results were reproduced with seeds 111, 42, 26083125 and 26092851. The before count
was permissive: for example a hash collision definition could match an unrelated
tree definition. Before/after counts are therefore not a claim of equal task
coverage or measured improvement in student attainment.

## Admission rule

Policy `aqa-topic-operation-records-v3` requires:

- Exact equality with the committed, source-reviewed record inventory. A
  schema-valid fabricated hash, altered mark allocation, omitted record or
  substituted source cannot qualify.
- Every item has a valid contract agreeing with its actual operation and response
  form. A question asking for an explanation of a trace table is not a table trace.
- Exact topic, operation, response mode and reviewed content family; the content
  family must also belong to the declared bank style. SQL INSERT, UPDATE, CREATE
  and deletion-error analysis have different content families.
- The same tariff band (1-4, 5-9, or 10+ marks), with context-complete references
  only. Required task context cannot be absent: scoped selectors check for the
  actual named code definitions, input values, schema links or scenario facts,
  not merely a non-empty introductory stem. Construction instructions cannot be
  relabelled as prose; generic trace-table wording does not establish functional
  content. These selectors conservatively support the reviewed bank forms, not
  arbitrary natural-language tasks.
- At least two source years and three distinct content families across the bank.
  This is an explicit engineering coverage floor, not a statistical sample-size
  claim. Every item still needs its own matching reference; the floor cannot
  compensate for an unmatched item.

The outcome `source-supported` carries `qualification_scope=generated-items`,
`whole_topic_qualified=false` and `empirical_equivalence_claimed=false`. Printed
item reviews, source/content identity, correctness and structural checks remain
separate requirements. Source support alone cannot make a missing-review bank
build-eligible.

## Source checks and provenance

Existing June 2022-25 QPs/MSs were inspected for the item semantics being used.
All inventory document hashes were checked against local ignored PDFs. New
feature-only records retain original filenames, item IDs, document SHA256s and
one-based PDF pages:

| Release | Item | QP / MS pages | Feature evidence |
| --- | --- | --- | --- |
| November 2020, Paper 1 | 04.1 | 7 / 11 | Four-mark balanced dynamic/static comparison; AO1 4 |
| November 2021, Paper 1 | 02.2 | 4 / 7 | Seven-node tree traversal sequence; AO2 2 |
| November 2020, Paper 2 | 11.2 | 34 / 24 | Explain recursive list accumulation; AO2 3 |
| November 2020, Paper 2 | 11.3 | 35 / 24 | Higher-order definition; AO1 2 |
| November 2020, Paper 2 | 11.4 | 35 / 24 | Evaluate fold; AO2 1 |
| June 2017, Paper 2 | 06.2 | 15 / 12 | Tabulated map/filter/fold evaluations; AO2 3 |

The 2020/2021 files are November releases whose printed running headers say
June. The record filenames preserve the actual release edition. For 2020 P2
11.3 the MS has an internal heading typo saying three marks, but both QP tariff,
MS total column and MS maximum award are two; the recorded total is two.

The 2017 QP/MS are original AQA documents downloaded from the public
[question-paper archive](https://pastpapers.co/aqa/A-Level/Computer%20Science-7516-7517/AQA-75172-QP-JUN17.pdf)
and [mark-scheme archive](https://pastpapers.co/aqa/A-Level/Computer%20Science-7516-7517/AQA-75172-W-MS-JUN17.pdf).
Older official filestore URLs returned 404 during this check. Their hashes are
`69173c5e964635db2c948ac0e1255ef013cba45afad4ac5b85ab22067d137fc9`
and `34a9f1d417a75f035b3dee98a9421dfe0c9f50a400976a68b1129683b8b37905`.
PDFs and extracted/rendered review material remain ignored; no source questions
or mark-scheme prose are added to the committed evidence inventory.

Corrections include 2022 P1 02.2 (describe), 02.5 (explain); 2024 P1 06.5
(analyse/prose, not completed code); 2024 P2 08.4/08.5 and 2025 P2 06.5
(describe); 2024 P2 11.2 and 2025 P2 11.4 (describe). Functional-recursion
efficiency remains a labelled mixed topic/complexity record, not a new core item.

## Original bank redesign

Only the topic-bank construction path changes; full-paper templates are retained.

- Structures retain queue operations, hash insertion/load, a seven-node tree
  traversal, graph representation, four-mark dynamic/static discussion and stack
  reversal. Unsupported BST construction and graph-route shapes are not falsely
  labelled as table traces.
- Databases retain independently executable SELECT/INSERT intents, targeted
  UPDATE, and DELETE error analysis, plus relationship diagrams, composite-key
  constraints, normalisation/denormalisation, five-mark relational design,
  CREATE TABLE and concurrent-update reasoning. The unsupported ten-mark NoSQL
  choice essay is replaced by applied tasks with genuine same-family precedents.
- Functional work includes map/filter/fold/composition, recursive call results,
  recursive mechanism/purpose, higher-order definitions, partial application,
  codomain, distributed processing and repeated-recursion cost. An unsupported
  ten-mark paradigm essay becomes an applied multi-part question.

## Remaining limits

Content-family/tariff-band support is not proof that two tasks have equal
difficulty or identical syntax, datasets or reasoning steps. In particular the
generated aggregate SELECT query is a new retrieval task, not an exact copy of
the historical joins/date-filter query. Whole-topic vectors/arrays/files and
functional program-construction coverage remain incomplete. Skeleton-dependent
records without their complete context remain ineligible. Source questions in
one annual scenario are correlated, not independent learner samples.

Regression checks cover sparse and fabricated inventories, wrong response modes,
wrong content families, wrong topics, missing context, excessive tariffs and
preservation of the separate item-review gate. The regeneration tool, rather
than hand editing, produces the committed demand profile JSON.

Independent review checked all 24 document hashes, added historical anchors and
fixed answers. Its three gate findings were reproduced as failing tests and
corrected: blank/stem-only context, construction-as-prose, and unrelated trace
prompts. The preview seed 26092851 also exposed a grammatical validator bug:
explicit plural "errors" now counts as error analysis, while deleting that task
still fails the unchanged SELECT/INSERT/UPDATE/DELETE/error-analysis requirement.
The bounded re-review approved the fixes and independently passed 114 focused
tests. The broader evidence/objective/candidate-path/CS-generator suite passed
469 tests with two skips; Ruff and whitespace checks passed. These are code and
deterministic-data checks, not a replacement for live-model or visual review.
The repository-wide suite then passed 2021 tests with two skips (five existing
SWIG deprecation warnings) in 108.91 seconds.
