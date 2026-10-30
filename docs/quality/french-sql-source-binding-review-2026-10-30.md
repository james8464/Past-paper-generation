# French SQL source-binding review

## Finding and scope

The previous V36 SQL check compared a model's query result with its expected
result using a model-supplied private database. It did not establish that the
database reproduced the tables printed for the candidate. Two retained synthetic
tests demonstrated the gap: a printed client named Claire and a private fixture
containing Bob could pass both structural admission and SQL verification. An
all-clear mock reviewer also passed; that mock is not evidence of live approval.

This implementation self-review covers commits `968786e0`, `3c772fc7`,
`518ce021` and `6d1211e6`, based on `2f0ed2bf`. It covers the changed SQL
boundary, table metadata/caption and native completion guard. It is not a
whole-file or whole-project attestation. No model/API calls, downloads or builds
of the complete app were performed for this work.

## Implemented boundary

An optional descriptor on each printed table declares its SQLite relation name,
column types and nullable columns. The owned caption exposes that interpretation
in both subject and correction PDFs. New SQL contracts explicitly reference these
materials, which must also appear in the question's material references.

Before independent reviews, the same bounded in-memory SQLite connection used
for the query checks every fixture relation against its printed source. Column
names/order and storage types must agree. Typed row multisets preserve duplicate
multiplicity while ignoring table row order. Missing, changed, extra or unbound
rows/tables refuse the executable claim. Views, temporary objects, generated
columns and private collations also refuse. SQLite-generated, SQL-less indexes
for PRIMARY KEY/UNIQUE on a bound table are allowed; explicit user indexes remain
unsupported. DDL word detection excludes quoted identifiers, strings and comments
when checking for a real COLLATE clause.

The query then receives read-only access to bound public table columns. It cannot
modify the checked fixture, inspect SQLite schema metadata or use an implicit
unprinted row identifier. Existing extension, function and instruction limits
remain in force. Source mismatches refuse before paid review and do not trigger
an answer repair, implicit conversion to `human`, or semantic retry.

Scalar interpretation is explicit:

- INTEGER uses canonical signed 64-bit spelling, without leading zeros.
- TEXT preserves case, accents and identifiers such as `001` exactly.
- REAL accepts bounded finite dot decimals only when the shortest floating-point
  representation preserves their decimal value. The caption identifies binary
  approximation. Unsupported precision, exponents, comma decimals and nonfinite
  spellings refuse.
- `NULL` represents absence only in a nullable column. Literal text `NULL` can be
  represented in a nonnullable TEXT column. These meanings are printed, not
  inferred from prose.

Every current-source V36 package requires exact policy
`fr-nsi-v36-sql-source-v1`, including packages without SQL. Generation, package
replay, runtime publication and native completion check the policy. Removing it
does not select a legacy reader. Package/manifest identities must agree before
native history completion. Explicit historical diagnostic helpers retain unbound
reading, and absent descriptors stay absent from historical material dumps and
default authoring schemas. UK and V13-V35 dispatch remain unchanged.

Both central requirement files now declare `pydantic>=2.12,<3` because
`Field(exclude_if=...)` requires that floor. No dependency installation was made;
the minimum-version environment itself was not exercised.

## Regression evidence

- Before the first implementation, two new boundary tests failed. The final
  initial-source run passed 364 focused pipeline/layout/publication tests in
  17.54 seconds; another 31 legacy NSI assessment tests passed.
- The key-index/collation follow-up reproduced seven legitimate-data failures.
  After the fix, 201 focused source-binding/pipeline/legacy tests passed. These
  include actual NOCASE/RTRIM rejection and denied schema access with a valid
  autoindexed table.
- The dependency-floor regression first failed. After explicit requirements were
  added, 120 dependency/configuration/release-compliance/SQL tests passed.
- An actual SQLite check showed that trailing unterminated comments are removed
  from stored table DDL. A regression confirms a bound query still succeeds;
  no production lexer change was needed for that case.
- A standalone `swiftc` harness compiled the actual native request source. Red
  accepted a missing policy. Green accepted only the exact string and refused
  missing, wrong, Boolean and numeric policies. XCTest coverage was added, but
  the complete native suite was not run by this agent.

Ruff lint/format, strict mypy for `sql_sources.py` and diff checks passed.
Graphify received AST-only updates. Test counts overlap and must not be summed
as distinct coverage. No full Python suite was run for these commits.

## Retained PDF evidence

These are owned synthetic regression fixtures, not a live generated paper or a
qualification result. Artifacts remain in the ignored private worktree
`/Users/james/.codex/worktrees/mlx-batched-generation/Past Paper Creation/`.
They were rendered for the initial binding implementation; subsequent key-index
and dependency changes do not change their caption/rendering code.

Under `tmp/pdfs/sql-source-binding-20261030/`:

| PDF | Pages | SHA-256 |
| --- | ---: | --- |
| `normal-subject.pdf` | 4 | `5b5cde7712769df1ccf934ee5d4b5157033ca2ee2f8ad6720feb4884bdf4daaf` |
| `normal-correction.pdf` | 8 | `454087b778e662f5fca658fd8850e13863e44a4a5b780cafa765764b5ba70198` |
| `enlarged-subject.pdf` | 4 | `1908f53c8f94228ec0d451d2228048b92349846daccab252d0bb5567bb25648f` |
| `enlarged-correction.pdf` | 8 | `3c4b9423f2e0c6852e6deeb8d6b564dded7c40e42ec73ba0b213198892831e64` |

All 24 pages passed the full-source/A4 PDF checks and were visually inspected
through four Poppler contact sheets. Captions and rows were legible without
clipping or overlap. Sparse correction pages and stranded rubric rows remain.

Two further subjects under `tmp/pdfs/sql-source-binding-types-run1/` exercise
TEXT `001`, REAL `0.25` and nullable `NULL` together:

| Relative PDF path | Pages | SHA-256 |
| --- | ---: | --- |
| `test_real_pdf_distinguishes_te0/typed-values.pdf` | 4 | `f2ab1adaf859ad130d122caed439e7d3a3df03fdc879356387a2d9f059f6d04c` |
| `test_real_pdf_distinguishes_te1/typed-values.pdf` | 4 | `62dd4e1593bb379865269a140225538e22dbdcd97130d88d916b7354da668dad` |

Their changed page 3 was inspected individually at both print sizes. The other
six pages are full-page raster-identical to the reviewed subjects at scale 0.8.
Complete-content checks also passed. No arbitrary-table layout guarantee follows
from these small fixtures.

## Limits

Source binding proves which printed data the SQL check used. A query can still
apply the wrong filter, omit a requested result or disagree with the wording or
rubric while remaining internally consistent. Independent semantic review is
still required. A newly authored explicit `human` contract remains available for
unsupported tasks and declares no executable verification.

The optional descriptor is deliberately limited to the existing nonempty table
shape and supported scalar types. It does not infer normalized relations from a
denormalized table or construct missing foreign-key data. Refusal of an unsupported
executable claim is not proof that the underlying question is mathematically wrong.

These checks establish neither teacher validation nor observed learner timing,
official-paper equivalence, App Store approval or general model reliability.
