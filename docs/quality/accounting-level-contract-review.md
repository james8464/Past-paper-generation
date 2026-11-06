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
checks the declared policy and every printed level/range at typed-contract
creation, public export and response simulation. It does not alter the printed
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
baseline with the complete four-line repair. The new 56-line shared validator
and 246-line test file received complete independent review; changes to shared
typed/export/replay code and adapter/catalogue paths received complete-delta
and relevant call-path review against their recorded baselines. This does not
claim a new whole-file read of each large shared dependency.

Final combined regression, packaged-build and native acceptance are separate
release gates. No model, paid service or learner trial was used for this repair.
