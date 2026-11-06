# Edexcel answer-frame clearance

## Reproduction and scope

The current offline Economics Paper 2 question paper visibly draws its first line
through the top answer-frame stroke on pages 7, 9, 16, 17, 18, 26 and 31. All seven
existing page renders were inspected before changing the renderer. The PDF's
SHA-256 is `b276fc96a0d953a09fb482983d693c02387ca23182bfa8211caeb4b227721f0d`.
The ignored coordinate report is `tmp/nov6-edexcel-frame-overlap-investigation.json`
in the release worktree.

The frame's top stroke is at 33.894pt in the cropped PDF, with a 1.600pt stroke
width. First-line glyph boxes begin at 31.731pt or 27.731pt on the inspected
pages. Their baselines are 42.594pt or 38.594pt. The overlap is between the
template frame and text, not two text blocks or missing content.

The renderer blob `f05e30c38f70d2870356ffa606908d5b6baf425e` is identical in
merged PR 177 and the frozen PR 178 candidate. This establishes inherited renderer
source, not an independently rendered PR 177 comparison or the defect's first date.

## Repair

The measured blank-rule origin remains 803.3pt. Content entry points reuse the
787pt ceiling already used for Section A source stems, expressed relative to
the frame's 808pt top. The actual regular/bold 12pt font ascents fit below the
stroke with more than the tested 3pt clearance. Smaller 10pt extract headings
and 8pt continuation captions receive a font-size-adjusted ceiling.

The change covers part prompts, MCQs, Section B extracts and prompt summaries,
Section C first-response instructions, Paper 3 question/choice headings, and
labeled continuation captions. Lower explicit starts are unchanged. Caption
placement does not alter its separator or any continuation writing-rule position.
There are no model, prompt, mark, extract-content or answer changes.

The Paper 3 choice instruction also extended into the right-hand rail. It now
wraps to the measured width between the existing 76pt content margins. Measurement
and drawing share the same font and box-token geometry. The wording and all three
vector cross-boxes remain unchanged; the instruction occupies three lines rather
than two. This does not change the horizontal style of the response rules.

Safer headings do consume a little response space on first-response pages. The
owned seed 42 fixtures retain page counts of 32/36/36 and lose exactly one writing
rule on each of the following pages:

| Fixture | Page: previous -> current rule count |
| --- | --- |
| Paper 1 |19: 25 -> 24;22: 25 -> 24;27: 22 -> 21 |
| Paper 2 |5: 22 -> 21;17: 25 -> 24;23: 25 -> 24;26: 25 -> 24;31: 22 -> 21 |
| Paper 3 |6: 25 -> 24;7: 25 -> 24;9: 25 -> 24;12: 17 -> 16;22: 25 -> 24;23: 25 -> 24;25: 25 -> 24;28: 16 -> 15 |

This is recorded explicitly rather than regaining a line by drawing through a
heading, shrinking line spacing or adding padding pages. All other seed 42
page rule counts are unchanged. This does not assert exact response-space parity.
The additional instruction line accounts for the reduction on Paper 3 page 12.
Sixteen pages in total lose one rule; the labeled continuation grids remain intact.

## Evidence

- Exact inherited-renderer RED: 3 failures and 5 controls passing. The trusted
  HEAD renderer blob was loaded with the worktree's file identity.
- Final focused checks cover all first-content glyph/frame clearances on three
  owned papers, font ascents/stroke clearance, nearby text/rule nonintersection,
  unchanged lower starts, pagecounts, affected rule counts and caption grids.
- Existing renderer and Edexcel checkpoint tests remain in the scoped run.
- A deliberately oversized prompt control reproduces the old test classifier's
  blind spot. The classifier now checks central-body intersection, so lines
  extending beyond the side frame still receive vertical checks. Dot-only blank
  response rules remain separate from body text and have their own origin control.
- The oversized Paper 3 instruction has its own RED bounding-box control, followed
  by checks for content-margin containment, unchanged wording and three drawn
  cross-boxes. A single oversized word is refused rather than clipped.
- Final scoped run: 77 passed in 15.94 seconds. Ruff check/format and diff checks
  passed. No full-suite, release-build or live-model run was performed here.
- Existing editable installs can import the primary checkout when pytest chooses
  the resource configuration. Initial diagnostics are retained, but acceptance
  uses explicit worktree `PYTHONPATH`, root `pytest.ini` and an import-path assertion.
- Before/after owned PDFs are retained under
  `tmp/pdfs/edexcel-frame-clearance-anan4eqe`. Poppler renders of Paper 2 pages
  5/17/19/31 and Paper 3 page 28 were viewed. Their top headings/caption clear the
  frame; no new text/rule collision was found in those examples.
- Final owned PDFs are in `tmp/pdfs/edexcel-frame-final-v4y1ql29`. Updated
  Paper 3 pages 12 and 28 were rendered with Poppler and viewed after wrapping.
  The instruction stays clear of the rail. The source-bound report
  `tmp/nov6-frame-clearance-fixture-comparison.json` records every PDF hash and
  rule-count delta. It also confirms that all three complete PDFs preserve
  non-rule text after whitespace normalisation.

Reviewed implementation SHA-256:
`2ed9bab06b647fe19c4c4fc2b996d7e85f31946001bc28b98490032d7afa30d2`.
Focused test-module SHA-256:
`fc03da7be5dc81f44343a2d775aa4c934d4926af32f7029b5c76c02b0765daed`.

A separate reviewer checked the final renderer delta and all 216 lines of the
new test module at those exact hashes. It found no actionable issue in that
scope. The complete renderer was not reviewed through EOF; its file-level audit
therefore remains pending.

## Saved evidence and limits

The scoped caller review found that `family_adapter.run_family_adapter` renders
each artifact through `render_pdf_atomically` after accepted-item checkpoint
loading. The public generation path then calls `validate_pdf_for_release` on
the newly rendered paths. Accepted authoring checkpoints are not cached PDFs;
this geometry-only repair therefore needs no new content/review version.
Previously saved PDFs and their reports are not rewritten or retroactively
certified. This is a narrow caller review, not a complete replay audit.

This review concerns the existing Edexcel Economics renderer only. It does not
qualify French papers, other boards, model output, difficulty, timing or official
equivalence. It is not a whole-paper visual audit. The measured glyph response-rule
style extends beyond the side frame and was deliberately preserved pending
comparator review; this review does not classify that style as a proven defect.
