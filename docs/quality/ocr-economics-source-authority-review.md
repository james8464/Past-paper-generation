# OCR Economics source authority: bounded repair

## Evidence and scope

The read-only audit at `eae9c151` read all 3,766 lines of the OCR Economics
generator, renderer, configurations, syllabus loader and CLI. Its private
receipt records exact EOF ranges and hashes. It identified four app-owned
inconsistencies, not speculative model mistakes or official-equivalence issues.

This repair starts from tested-prefix `0a4e9eba` in a separate checkout. INT and
CAPACITY remain untouched. The pre-existing review branch and `ea60479a` stash
are preserved.

## Repair boundaries

- The renderer retains every original marking statement and structured accepted
  route. It no longer appends a second generic grading scale to the existing
  question-authored levels. In particular, 15-mark questions retain their
  authored 13–15 top band instead of also printing a conflicting 9–12 top band.
- Compulsory cover wording follows the actual section-selection topology.
  Paper 3 has compulsory Sections A and B, not an optional question and a
  nonexistent Section C. Papers 1 and 2 retain their existing choice wording.
- The AO grid projects validated question allocations, including the sum of
  all 30 MCQ allocations. It no longer estimates objectives from tariff or kind.
  Missing or invalid legacy allocations fail explicitly rather than being
  silently invented. Candidate option grouping and total marks are unchanged.
- Paper 3 figures now say “index points”, matching their existing units. The
  source does not establish a 2019 base of 100: each series starts at an
  independently drawn value from 84 to 118. No series, raw value, extract,
  percentage answer or numerical contract is rebased by this title correction.
- Removing the extra descriptors exposed a spacer-only page before the Paper 3
  appendices. The existing public-preview check rejected it. The renderer now
  removes only the final body spacer immediately before the forced appendix
  break; no table or PDF page is deleted. The existing OCR content-pagination
  policy already applies to all three mark schemes without a blueprint marker;
  no strict historical page-count route or policy is changed.
- A separately authorised bounded scan of the first 128 legal seeds for all
  three papers found one HALF_UP mismatch among 384 calculation items: Paper 1,
  seed 15, Question 1(c)(i), using 88.0 and 86.9. The source displayed -1.2%
  instead of -1.3%. Both calculation and answer now use exact Decimal inputs and
  the existing typed NumericOutput/display policy, including its minus and zero
  conventions. No core helper or input, formula, tariff or tolerance is changed.

## Verification and limits

An owned-checkout RED run produced eight failures and seven passes for the
three built-in papers at seed 123. It rendered actual PDFs and inspected
question-owned table cells. A separate PDF-first title test confirmed the
incorrect base-year statement in an actual Paper 3 question paper before the
fix. Import-path assertions bind the tests to the edited checkout.

New tests compare the complete built blueprints with pre-repair SHA256
baselines, normalising only the explicitly changed figure-title fields for
Paper 3. They verify every source marking statement and structured point,
single non-overlapping source level bands covering each tariff, exact AO rows,
actual cover and chart text, renderer immutability, all three paper controls,
and explicit refusal of missing or invalid AO metadata. Separate RED witnesses
cover the actual empty physical page 25 and the seed-15 rounding mismatch.
The rounding test checks all 384 legal calculation items, independent solver
agreement, rejection of the former answer and actual printed PDF text.
Existing printed-credit,
content-pagination, question-chrome and shared-cover controls are also run.
The public bridge preview test covers all three papers and now succeeds without
changing its content or page checks. The scoped gate passed 97 tests in 12.94
seconds, with five existing SWIG deprecation warnings; scoped Ruff and
formatting checks passed after an import-order/line-wrap-only test cleanup.

Final scoped results and exact reviewed file pins are recorded in the private
implementation/review receipts. This is not a full-suite, model-generation,
every-page visual-review, GUI, native-build, teacher-review or qualification
equivalence claim. No grading tolerance, marking budget, official reference
page count, source facts or core pagination policy has been changed. The one
confirmed incorrect rounded answer is repaired, not hardcoded. Integration
metadata and release gates remain separate work.
