# Numeric labels and printed ratio validation

Date: 29 October 2026

This is a scoped semantic review and regression record for two shared validation
boundaries. The author read both implementation files and the two affected test
files completely, then wrote the tests and fixes. It is not a whole-code audit
or independent exam-paper qualification. Independent integration review remains
a separate gate.

These changes were uncommitted on `main-xcode-and-validation-follow-up`, based
on `639643600336767b713c05494c56899dcf1b7467`, at hash capture.

## Leading quantities versus declared labels

The old candidate validator treated any bare one-to-three-digit number at the
start of a line as a question/code label. This removed a genuine assessment
quantity in an unchanged prompt such as `100 workers ...`. It could also ignore
a newly inserted leading quantity, or an extra occurrence of the expected
quantity, instead of enforcing the strict numeric multiset.

Bare leading numbers are no longer ignored by default. The validator identifies
source lines whose original numeric prefix is explicitly declared as a code-line
label, item identifier or display label in the host contract. Only those source
line positions permit a corresponding bare candidate label. Thus the existing
declared `01 total = 225` to `07 total = 225` case remains valid, while a new
`100 workers ...` line is not silently exempted. Reflowing a bare label to an
undeclared line now requires a matching explicit contract rather than guessing
its meaning.

Explicit `Question 7`, `line 07`, figure/table/extract references, mark labels
and precision wording retain their separate syntactic handling. A preservation
fixture also found that the existing number lexer can represent `[2 marks]` as
`2 m`. The label recogniser now removes the exact numeric token within a known
label rather than assuming it contains bare digits. The general number grammar
was not changed, and genuine assessment quantities and units keep their existing
comparison rules.

Missing, changed and additional assessment data still fail. This is an explicit
contract/syntax distinction, not a general natural-language determination of
whether any arbitrary numeral is meaningful data.

## Comma-formatted ratio alternatives

The printed-output validator already allowed comma-formatted numbers, but its
special `accept ... without :1` ratio branch passed the alternative directly to
Decimal. A valid `1,000` alternative therefore raised a conversion error.

The fix removes grouping commas before that Decimal comparison, matching the
normal numeric-token path. It does not broaden accepted suffixes, units or
alternative values. `1,000:1 (accept 1,000 without :1)` and the ungrouped form
pass; `1,001`, `999` and `1,000,000` remain rejected for an expected ratio of
1,000. Existing output-role, currency, scale, direction and trailing-content
guards remain in place.

## Regression evidence

These ignored local logs are retained; they are not shipped resources or
guaranteed to exist in a fresh GitHub checkout.

| Log | Result |
| --- | --- |
| `tmp/numeric-label-boundaries-red.log` | 9 failed, 3 passed, 138 deselected before implementation |
| `tmp/numeric-label-boundaries-first-green.log` | 362 passed, five third-party deprecation warnings, 7.37 seconds |
| `tmp/numeric-label-boundaries-green.log` | Final related-only gate: 470 passed, five third-party deprecation warnings, 14.57 seconds |

The final related gate covered:

```text
tests/test_assessment_contracts.py
tests/test_shared_numeric_integrity.py
tests/test_mathematics_subject.py
tests/test_science_subjects.py
tests/test_computer_science_subject.py
tests/test_subject_plugins.py
tests/test_topic_reference_evidence.py
tests/test_independent_solver.py
tests/test_accounting_solver.py
tests/test_accounting_solver_completeness.py
tests/test_assessment_source_projection.py
tests/test_computer_science_objectives.py
tests/test_topic_task_contract.py
tests/test_level_of_response.py
```

This preserves the existing financial closed-output contracts and topic/math/
solver compatibility cases, including missing outputs, wrong roles, changed
units/scales, wrong directions, false alternatives and incomplete replay
provenance. Affected-file Ruff, formatting and `git diff --check` passed. The
other files in that related test selection were not modified for this package.

## Exact reviewed snapshot

| File | SHA-256 |
| --- | --- |
| `Backend/Core/assessment_quality.py` | `64c0a1d10a0755f681956eea6976e425af4627175aecf761ef7b3ca83b3b1b72` |
| `Backend/Core/numeric_integrity.py` | `124f8220c93ef1b003d6eff2921862cd1690575e1d461b8c487f286271a23e58` |
| `tests/test_assessment_contracts.py` | `f7670d75b9bb5f041ee259e494b9d6d3e9251d1f8441723f40ebfd78d9640c20` |
| `tests/test_shared_numeric_integrity.py` | `407976c049eab7cfbd209abd770ab208e1719b5b0904944113c390973a13d627` |

## Scope and remaining gates

- These shared validators have current generation/independent-solver callers;
  the specific boundary failures were established by deterministic fixtures,
  not observed as defects in an accepted native paper.
- The separately retained Gemma Accounting Paper 2 failure remains a failed
  model diagnostic. This package does not relabel it or claim its Q05 source
  bank was defective.
- No provider, model, prompt, source bank, historical French catalogue, grading
  threshold or novelty-history policy was changed.
- No model calls, full suite, native build, teacher review or learner timing
  were performed for this package.
- Core-byte identity changes require final integrated whole-suite and rebuilt
  helper checks, plus renewed current-source/French acceptance. Previous runs
  retain their original identities and are not acceptance of this new source.
- No whole-code, full-HIG, official-paper equivalence or Store approval claim is
  made by this report.
