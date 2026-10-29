# UK repeat-practice publication policy

## Scope

The public UK generation route now permits similarity to earlier saved practice
papers. This is an explicit publication policy, not a relaxation of answer,
reference, source-fidelity, or within-paper validation. It does not change model
requests, generation attempts, the draft-paraphrase screen, or subject banks.

`validate_package_novelty` retains its strict default for existing diagnostic and
other direct callers. Only the public generation finaliser explicitly selects
`repeat-practice-v1`. Historical files are not changed or removed. Existing
package bytes are not migrated or reinterpreted by this change.

## Evidence contract

New results retain the existing algorithm, threshold, comparison count and nearest
match. Under `evidence.novelty_validation`, they additionally record:

- `cross_generation_policy`: `repeat-practice-v1` for public generation, or
  `strict-cross-generation-v1` for default direct callers.
- `within_paper_passed`: true only after the unchanged within-paper screen passes.
- `historical_overlap`: whether a relevant historical comparison reached the
  existing threshold.

In repeat-practice mode an overlap does not reject publication, but `passed`
remains false when overlap exists. Permitted repetition must not be displayed as
proof of originality. Native policy-aware presentation is a separate integration
task. Preview history-skipping behaviour is unchanged.

History matching remains scoped to the same subject and paper. The current
transaction's replacement filename is still excluded. All remaining relevant
comparisons run even after an overlap, so the nearest-match evidence is retained.
Unreadable history handling is unchanged. This is not a copyright guarantee or a
semantic assessment of whether similar questions are pedagogically interchangeable.

## Red and green checks

- `tmp/uk-repeat-practice-red.log`: five failures and one pass before production
  edits. Failures covered the missing policy argument and missing explicit public
  opt-in; the strict-default rejection already passed.
- `tmp/uk-repeat-practice-green.log`: 83 passed, five third-party warnings.
- `tmp/uk-repeat-practice-final-green.log`: 116 passed, five third-party warnings,
  in 40.93 seconds. This includes eight dedicated policy tests, assessment
  contracts, generation-policy validation, and backend integration tests.
- Ruff formatting/checks and `git diff --check` passed for the scoped changes.

Dedicated tests cover permitted historical overlap without a false success flag,
unchanged strict-default refusal, within-paper duplicate refusal, empty history,
subject/paper scoping, continued comparison after a match, invalid policy refusal,
and explicit selection by the actual public finalisation function. No models,
downloads, native builds or full Python suite were run for this change.

## Reviewed file snapshots

| File | SHA-256 |
| --- | --- |
| `Backend/Core/assessment_quality.py` | `71000b22e1ddcc5c5799100bca55995fc00323d2ad991f1fad3b946868e6c088` |
| `Backend/Core/generation.py` | `64d7e11ba7908891a76439de1262f8c009a7e75a6a1936ee66dc22b3bd30f007` |
| `tests/test_repeat_practice_policy.py` | `b49296b5b0c86d644eee86bab5c3c0908a457587e979d041710f098e921e02ed` |

The assessment-quality snapshot also includes the earlier separately reviewed
numeric-label boundary changes. This report records the later snapshot without
overwriting that earlier report's historical hashes.

Whole-suite, native policy-aware presentation, protected CI and final packaged
acceptance remain integration gates. This report does not establish complete app,
paper-quality, provider-equivalence or release qualification.
