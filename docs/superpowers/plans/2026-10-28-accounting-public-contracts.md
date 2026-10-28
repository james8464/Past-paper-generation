# Accounting public-case and marking contracts

The V10 live run is retained as a manual HOLD. Fix its reproduced defects before
another expensive live run. Keep historical packages, strict schemas and numeric
checks intact.

## Implementation boundaries

1. Define explicit Accounting marking policies before generic hydration. Share
   their allocations with Paper 1's specialised renderer. Keep account tables,
   credit-side entries, the seven-mark Q12 cap and distinct developed Q11
   reasons. Mutation must either change both representations or fail validation.
2. Project public authoring, solver and reviewer data from the same case facts
   printed for candidates. Remove stale generic facts, use distinct independent
   legal identities, and preserve referenced-source immutability.
3. Reject embedded MCQ alternatives in a generated stem while retaining normal
   references to option labels. Use the existing bounded writer repair flow.
4. Correct fixed-tax follow-through and separate general marking guidance from
   question-specific indicative content by role. Keep genuine accounting credits.
5. Add original multi-step MCQ variants with independently checked results and
   distinct plausible distractors. Do not copy official questions or add blank
   pages to imitate booklet length.

Parallel owners cover marking/rendering, public source projection and the MCQ
validation boundary. The primary reviewer owns version changes, integration,
new depth variants, source freeze and final acceptance. No concurrent full test
or live run may overlap source edits.

## Gates

- Retain failing regressions, then run focused domain/AI/PDF tests.
- Check actual full Paper 1 PDFs against the persisted marking authority.
- Verify candidate/checkpoint/package preservation and historical replay.
- Review every changed page; use raster identity only for unchanged bodies.
- Update Graphify and tracked-file inventory, review the final diff, freeze the
  implementation, then run full tests and a new pinned complete live paper.
- Require both latest-head protected checks before merging to main. A passing
  model run alone does not remove the manual HOLD or establish calibration.
