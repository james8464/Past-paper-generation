# Source and marking-policy boundary review

Date: 29 October 2026

This record covers ten completely read Core files and three regression-test
files. It is a semantic implementation review of the stated boundaries, not a
whole-code audit or a claim that generated papers are empirically calibrated.
Graphify was queried before inspection. The author of this report also wrote
the regression tests and implementation; independent integration review is a
separate gate.

The snapshot below was recorded while these changes were uncommitted on
`main-release-safety-audit`; HEAD at hash capture was
`b7c7cf991ddbc330782bb4615cd818b9131460ba` after the ordinal-level follow-up.
File hashes identify the reviewed
bytes even if other changes are integrated later.

## Findings and narrow fixes

### Empty option title

The shared-source heuristic used substring containment without first requiring
a nonempty option title. The empty string matches every prompt, so a missing
or blank title could give a self-contained nonnumeric, non-MCQ item a spurious
parent-source dependency. The heuristic now checks the stripped title is
nonempty before matching it. Explicit source references, source cues and owned
source-data contracts retain their existing precedence.

### Programming selection versus retrieval queries

The topic-task recogniser treated any prompt containing the substring `select`
as requiring a query response. This included ordinary Python selection,
`preselected` and identifiers such as `select_student`.

Query mode now requires an explicit retrieval-query cue:

- `SQL query`, `SELECT query` or `SELECT statement` wording;
- uppercase `SELECT ... FROM` syntax in the original prompt; or
- a `SELECT ... FROM` statement beginning at the start of the prompt or after
  a colon/newline, matched without case sensitivity.

Existing option, diagram, trace-table and response-slot precedence is unchanged.
This is a small task-shape recogniser, not a SQL parser or proof of executable
query correctness. Ordinary selection remains code mode.

An initially broader change also classified explicit INSERT/UPDATE instructions
as query mode. Existing topic-4.10 tests caught that compatibility error: two
established modification-statement tasks no longer matched their reviewed
code-mode reference contracts. The implementation was narrowed rather than
changing reference data. INSERT/UPDATE statement code mode is retained and
covered explicitly. No source inventory or reference qualification was altered.

### Response-band validity

The scale helper could assign an increasing minimum to each positive band and
then put the final maximum below that minimum when the requested tariff had
fewer marks than positive bands. It returned unchecked model copies.

The helper now refuses that impossible tariff rather than inventing a reduced
marking policy, and validates the resulting policy after scaling. Descriptor
validation rejects inverted mark ranges. Policy validation requires consecutive
ordinal level identifiers starting at zero, a zero-credit base at zero coverage,
non-overlapping ordered mark bands, strictly increasing coverage thresholds,
and maxima within the declared policy maximum. The highest band must still end
at that maximum. These checks do not claim deep immutability of model-owned
containers or exhaust every possible malformed policy.

Parent review found that merely requiring ordered, unique identifiers still
allowed gaps. The engine finds the next threshold by `selected.level + 1`.
Relabelling the same bands from `0,1,2,3,4` to `0,2,4,6,8` changed the mark for
the same 25% coverage from four to two. A new failing constructor regression
recorded this case; the validator now enforces the existing ordinal invariant
rather than changing how valid policies are marked.

All nine checked-in level policies remain accepted without data changes. Tests
also retain identity when scaling to the original tariff and check every tariff
from each policy's positive-band count through 30. The dedicated Accounting
two-reason policy remains separate; no substitute examiner policy was invented.

## Evidence

Local logs are retained under ignored `tmp/`; they are not shipped resources or
guaranteed available in a fresh GitHub checkout.

| Log | Result |
| --- | --- |
| `tmp/core-policy-boundaries-red.log` | 18 failed, 11 passed before implementation |
| `tmp/core-policy-boundaries-first-green.log` | 209 passed, one topic-4.10 compatibility failure; retained as a failed intermediate attempt |
| `tmp/core-policy-boundaries-green.log` | 215 passed, five third-party deprecation warnings, 3.47 seconds after narrowing query recognition, before the ordinal-level follow-up |
| `tmp/core-policy-level-gap-red.log` | Gapped-level regression failed; five other invalid-band cases passed |
| `tmp/core-policy-level-gap-reproduction.log` | Same 25% coverage: four marks with ordinal levels, two with relabelled gapped levels |
| `tmp/core-policy-boundaries-final-green.log` | Final focused result: 216 passed, five third-party deprecation warnings, 8.67 seconds |

The final focused run selected:

```text
tests/test_shared_source_scope.py
tests/test_topic_task_contract.py
tests/test_level_of_response.py
tests/test_topic_reference_evidence.py
tests/test_assessment_source_projection.py
tests/test_computer_science_objectives.py
```

Affected-file Ruff checks, formatting and `git diff --check` passed. No model
calls, full-suite run, native build or final French source/helper acceptance was
performed for this package. Whole-suite, packaging and protected CI gates remain
the parent's integration work. No provider, prompt, historical French catalogue
or reference-data file was edited.

## Complete-file review snapshot

“Reviewed, unchanged” means no additional actionable finding was identified
within this review. It is not a guarantee that the file has no possible defect.

| Path | Disposition | SHA-256 |
| --- | --- | --- |
| `Backend/Core/shared_source_scope.py` | Nonempty title guard | `420770af02798e484bbdae45e04626742c419432e82a6158c2e396c400b48067` |
| `Backend/Core/scoped_references.py` | Reviewed, unchanged | `52c6f37f6b2a42a21ab09de3911d97263d00460e358c6d11b65697955f4d5333` |
| `Backend/Core/candidate_identity.py` | Reviewed, unchanged | `e44e58abd43132af03cfe80d36d229482807685f60ab52ccac976e8fb9201235` |
| `Backend/Core/topic_task_contract.py` | Retrieval-query recognition | `dfd011917c4e7b6e8afe8fb5290f5a141cfb859a33042ac9ca0f53fde8e7f5de` |
| `Backend/Core/credit_policy.py` | Reviewed, unchanged | `f6f70dc0e91da9f6fca3f4baebda6d604a00b19cfc3f27339a3098c2c38da568` |
| `Backend/Core/level_of_response.py` | Ordinal bands, range validation and impossible-scale refusal | `4a77bb0f1a3e7960328bbc0abad77983dfb458d430bdd86039003289afa46d81` |
| `Backend/Core/mark_scheme_quality.py` | Reviewed, unchanged | `c66255b91fb7fde56b2121b8ffe481e4bc8df56c23ae1b7c1ca1097476b4ae01` |
| `Backend/Core/subject_contracts.py` | Reviewed, unchanged | `f3ddfc30ab056b06a9fa82119d298a8cbcd8cd520faa45b12051797161d34e97` |
| `Backend/Core/education_context.py` | Reviewed, unchanged | `b8d1cfbe319dfa2f2d51cf7d2ea93b3c4a65300a2447b38417687a2e907b6a1a` |
| `Backend/Core/generation_date.py` | Reviewed, unchanged | `6d7b340f143e2506b615650ca0b0568b317ade8bf31fe93068b196a4ed5b9de6` |
| `tests/test_shared_source_scope.py` | New source-dependency regression cases | `dc987d3fa2209ee99ded5da067d25a58a46ef8bb1fb343292cfbf50c2997bc38` |
| `tests/test_topic_task_contract.py` | New programming/SELECT and precedence cases | `71e8a7dac046b90a66929de949e6ef1e6f9528df6437c2b22e1ac369584c792b` |
| `tests/test_level_of_response.py` | Expanded invalid-policy and compatibility cases | `6c67a0af0d8ba2f57ba35f040b297e650aef099d31feee7feb60a0245f3bc5db` |

No learner timing, teacher approval, full-HIG compliance or Store approval is
established by these implementation tests.
