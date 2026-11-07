# Accounting mark-band contracts

## Observed discrepancy

Accounting's non-grouped six-mark questions printed three positive bands:
1-2, 3-4 and 5-6. Its 25-mark questions printed five: 1-5, 6-10, 11-15,
16-20 and 21-25. The exported assessment contract instead named the generic
four-band AQA policy. Scaling that policy produced different ranges, although
the existing monotonic response simulation still reported success.

A bounded reproduction used the real enrichment, public JSON export/read-back,
marking-row and response-band paths. Its two synthetic items totalled 31 marks;
only the unrelated whole-form demand audit was isolated. This proves the
contract discrepancy, not acceptance of a complete generated exam or a model
answer. It is unrelated to the retained Q06 semantic-quality failure.

The five 25-mark ranges agree with AQA's published
[Accounting answers and commentaries](https://filestore.aqa.org.uk/resources/accounting/AQA-71271-EX2.PDF).
That resource also illustrates separately marked two-reason answers. It does
not justify applying one six-mark grid to every six-mark task. The existing
two-reason route remains two independent three-mark awards.

## Repair

Named Accounting policies now match the existing printed ranges. The generator
attaches the appropriate policy before enrichment. A small shared validator
checks each standalone policy and printed level/range at typed-contract
creation, public export and response simulation. Grouped two-reason awards
remain owned by the pre-existing grouped validator, including retained grouped
contracts with an unused generic standalone policy ID. Typed hydration defers
grouped metadata; it does not by itself prove grouped shape, caps or AO validity.
Public export and replay apply the existing grouped checks and reject forged
grouped markers on standalone 25-mark items. The repair does not alter printed
descriptors, question text, worked answers, AO budgets or maximum marks.

The catalogue's coverage thresholds remain ordered developer-diagnostic
heuristics. They are not official grade boundaries, observed student marks,
learner calibration or evidence that the app can mark a real response reliably.

The Accounting adapter has a new checkpoint version. Stale generic policies are
refused rather than silently reinterpreted. Tests check that rejected saved
packages and checkpoints retain their original bytes. Existing PDFs and history
are not rewritten or removed. Other subjects keep their generic policies.

## Verification and review

The initial targeted tests produced seven genuine failures. After repair, 63
tests passed across the Accounting contract, level-policy, typed-contract,
package-migration and package-quality groups. They include exact range equality,
public export/replay, grouped marking, other-subject controls and stale-cache
refusal. Whole-form audit isolation in synthetic exports remains explicit.

The author read the complete prior Accounting generator (1,215 lines), scheme
policy (119) and marking policy (415). Review of the generator combines that
baseline with the complete four-line repair. The initial 56-line shared validator
and 246-line test file received complete independent review. The grouped-policy
follow-up received complete-delta independent review against those baselines;
these historical counts are not claims about the current EOF sizes. Changes to shared
typed/export/replay code and adapter/catalogue paths received complete-delta
and relevant call-path review against their recorded baselines. This does not
claim a new whole-file read of each large shared dependency.

Final combined regression, packaged-build and native acceptance are separate
release gates. No model, paid service or learner trial was used for this repair.

### Combined regression follow-up

The first frozen combined full-suite attempt at `d4ff869f` was stopped after
13 failures and 312 passes in 38 seconds. It is not an acceptance result.
Eleven failures exposed incorrect standalone-validator precedence over grouped
awards and their existing rejection controls. One assertion still expected the
old Accounting adapter version. One historical content/numeric digest included
the intentionally changed standalone policy IDs.

The grouped dispatcher now retains its original precedence and error controls.
The version assertion requires the new version. The historical digest test
first asserts each new named standalone policy, then normalizes only that ID
in its comparison copy; its original content/numeric golden hashes remain
unchanged. Additional forged-marker controls demonstrated two public-export
failures before the export boundary was repaired; existing replay rejection
already passed. No validation threshold or grouped cap/AO check was relaxed.

The final scoped Accounting run passed 322 tests in 40.42 seconds: all 13
`tests/test_accounting*.py` files, `tests/test_aqa_accounting_calibration.py`,
and both files under `Resources/accounting/aqa/generator/tests`. An ignored
test-owner harness forbade unmocked Ollama admission metadata calls. Ruff,
format checks and diff checks passed. Five existing Swig deprecation warnings
were reported. This scoped result does not replace the complete frozen-suite
or packaged/native release gates. Independent review covered the final grouped
ownership/dispatch changes, explicit export precheck, and four forged-marker
controls; no actionable finding remained in that reviewed delta.
