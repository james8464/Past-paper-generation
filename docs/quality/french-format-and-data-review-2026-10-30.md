# French formatting and saved-data review

This batch fixes a reproduced fence-parser error and two saved-data validation
errors. It does not establish a complete French paper or provider qualification.

## Printed code

The retained Flash 21 response mentions a Python fence inside a sentence before
a correctly fenced function. The old unanchored expressions paired that inline
mention with the actual opening line, leaving the function apparently unfenced.
The new shared parser recognises standalone delimiter lines. Admission, code
measurement, rendering and PDF text checks use the same spans.

The change has explicit print policy `fr-nsi-v36-model-review-v3`, bound through
the package identity, runtime rendering call, manifest and native completion
validation. V36-v1/v2 and V13–V35 retain their earlier rendering paths. V2 retains
its readable graph geometry and question numbering. No cached policy is silently
migrated.

CRLF input produced a carriage-return glyph in ReportLab's listing. V3 converts
CRLF to LF only when building that presentation. Package strings and indentation
remain unchanged. All 24 tested LF/CRLF page pairs are raster-identical. Four
affected pages and two unchanged correction-guidance pages were visually inspected. These are
application-owned fixtures, not live model qualification.

The current completeness and forbidden-operation checks remain enforced. A
partial correction branch in Flash 21's first response still violates that
complete-snippet contract. Pro 20's file-reading call still violates its original
explicit restriction. Neither failed run was repaired or promoted to a pass.
Printed strings are not executed; separate verification contracts still use the
bounded interpreter. Supporting intentional display fragments would need a
separate versioned design and review.

Untouched Flash 21 call 02 now passes its original request schema and current
normal-print authored-exercise admission in an offline replay. Its response hash
is `9f101f97c4dddbfe86c5b638583330fe47e22869e9dde9e8726bf5a5de7870b3`;
the candidate hash is
`aef5333a4d43505f1be748aba545cb95af68cbbbfda81c1f64a1ea29aa4282c5`.
The original files were unchanged. All five question contracts were human-review
contracts. No code was executed, PDF generated or answer independently validated
by that replay. It is not a fresh model run or paper qualification.

## Saved data

Calibration imports now reject non-finite scores, maxima and optional timing
before persistence. Tests cover NaN and both infinities, valid finite fractions,
and a mixed import that leaves existing encrypted files byte-identical.

Unreadable historical comparison packages no longer block practice generation.
Historical records must contain usable IDs, subject, paper and prompt text;
malformed collections are skipped intact and counted. Incomplete history yields
unknown originality evidence, not a successful comparison. Observed overlap,
current-package checks and existing thresholds remain unchanged. Native quality
presentation and manifest roundtrips preserve that unknown state. Valid prompt
whitespace is compared without rewriting the stored text.

## Complete-file review scope

The files below were read to EOF, then their final changes were reviewed. Selected
callers and tests were traced; this is not a whole-project or mathematical
correctness certificate.

| Source | SHA-256 |
| --- | --- |
| `Backend/Core/answer_projection.py` | `c929b0c81b1390dba5dd18b5214d2482cc37ebfefca81275ca0434c9a9f5a633` |
| `Backend/Core/assessment_contracts.py` | `29b9102a463b7bdf8887e57cf6abfe42d0a41c1c17991341c3953837ff9d5a8e` |
| `Backend/Core/assessment_objectives.py` | `521de62e826064c0f3fc94e4ed5af124dd2c8fa6bc6f4f3cd5b524f0a3ca1734` |
| `Backend/Core/assessment_package.py` | `52b14aa7074c25589ece964f82b91e219831cd29b4f565726351a7d932f6b48b` |
| `Backend/Core/assessment_quality.py` | `1669264dee9d075be1dd3ace628eb7c0dde93753869ef29caef2bc3ba2dcf6b2` |
| `Backend/Core/calibration_store.py` | `c56a69078804c2dd0f18868ece272b0731e09b78fc486a8eaed221e1cf093cbd` |
| `Backend/Core/france/code_fences.py` | `324032100a397474dee35419759e997d1385acd0aff69bab1f6397a36ca78d52` |
| `Backend/Core/france/code_layout.py` | `5202282c79f9acc3f5eef12e2904cc2077b636c0debe6e509081120ae480a5a3` |
| `Backend/Core/france/print_policy.py` | `85dc61e3321f0e9b3ca97cae651250f673da5739a8b4095ef5d23ab419079ffa` |
| `.github/workflows/ci.yml` | `68cb5c3a91bb8f85b9034680aea270a89f24a2c9d8bcd3ca219e8f2a67c669ba` |

## Verification

The parser batch passed 194 focused tests. The final combined French, saved-data
and packaging scope passed 250 tests. Counts overlap earlier runs and must not
be added together.
The native unknown-history fixture requires its own actual native test result.
Sixteen pure Swift helper tests passed using the exact new CI command. A failing
wiring assertion preceded that workflow change; protected CI now runs those
protocol regressions in addition to the application tests and Store-mode build.

Read-only cross-reviews checked parser/policy compatibility, calibration
persistence and nullable quality presentation. They also found the historical
member-shape gap that the follow-up closes. Logs are in
`tmp/final-validation-20261030/fence-*` and `history-*`, with original agent
red/green evidence in their private worktrees. A mistyped test path ran no tests
and is not counted as acceptance. Full regression, signed builds, protected
checks and installed-build acceptance are separate release requirements.
