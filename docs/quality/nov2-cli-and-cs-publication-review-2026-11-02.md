# CLI publication recovery and AQA CS print review

These bounded changes address document-set recovery and three printed CS
inconsistencies. Final combined-source acceptance is pending. The checks below
used controlled local fixtures without model calls or provider spend.

## CLI document-set recovery

Author commit `68346ebd`, integrated here as `3696c64c`, changes the shared CLI
finalizer to preserve every existing destination before replacing any file.
Assessment, novelty, PDF and preview checks still run before publication, followed
by manifest construction. Distinct output filenames are required; symlink and
non-file destinations refuse before replacement.

The publisher hard-links existing destination files into a private
`.keldin-publish-*` sibling directory. A caught publication failure or cancellation
restores attempted old destinations and removes attempted new files that had no
predecessor. Each destination is recorded before its replacement, so an exception
immediately after replacement still enters rollback. Unrelated files are untouched.
If restoration fails, remaining backups stay outside render staging and the error
reports their directory. Successful publication tolerates failed backup cleanup.

This is synchronous failure recovery. It does not provide a crash/power-loss
atomic transaction or protection against concurrent external writers. A filesystem
that refuses hard links causes backup admission to fail before replacement. The
native output-folder publisher is unchanged.

The author recorded five failing assertions/cases with two controls before the
repair, then 104 focused passing tests. Logs are in the DOCS checkout
`/Users/james/.codex/worktrees/occitanie-final-nov1/Past Paper Creation/tmp/nov2-cli-publication-red.log`
and `nov2-cli-publication-green.log` in the same directory. Independent review read
all 229 new test lines and the repair/finalizer paths without rerunning them.
Fixtures exercise real link/replace/rollback operations while stubbing upstream
content validators; they do not establish PDF or educational quality.

## AQA Computer Science printed output

`d1e58c83` replaces the mark-scheme body's fixed `JUNE` with the shared generation
month/year already used by its cover. P1, P2 and all three topic banks receive
real-PDF checks for June, November and September. Every body header must agree
with its cover, including the longest month label fitting on the page. Marking
text/coordinates, vector geometry and page counts remain equal across these date
variants; blueprint data are unchanged. Explicit June header text remains the
same. The focused group passed 19 tests; logs are
`/tmp/keldin-cs-scheme-session-red.log` and
`/tmp/keldin-cs-scheme-session-green.log`.

`024cbc4c` prints one complete adjacency matrix for the explicit 36-cell response
contract in P1 Q03.3. Every printed binary value comes from its immutable answer
key. Existing two-mark guidance for symmetry and all/only listed edges remains;
the caption states that allocation consistently. The legacy path without the
full-cell contract retains its alternative matrices. No solver, marks or source
answers change. Tests check all 36 printed cells against the key, refuse malformed
bindings and partial/wrong solver responses, and retain a positive legacy layout
case. The two expected real-PDF failures became 88 focused passes. Logs are
`/tmp/keldin-cs-matrix-red.log` and
`/tmp/keldin-cs-matrix-frozen-green.log`.

Offline source-render inspection at seed 270100 covered QP4 and corrected MS7 at
1100px plus the grid of all 19 mark-scheme pages. The question paper retains all
24 pages with identical words, boxes and 1100px rasters compared with the retained
`cfaa11c0` preview. Removing duplicate/partial matrix alternatives reduces the
scheme from 20 to 19 pages. Both documents retain visible preview notices.
Evidence is in the IDENTIFIERS checkout at
`tmp/pdfs/nov2-cs-matrix-contract/`, including `report.json`, `comparison.json`,
`ms-grid.png`, `ms-07.png` and `qp-04.png`. These are source-render diagnostics,
not newly packaged-binary or whole-paper acceptance evidence.

`4c9886ea` changes the Electronic Answer Document label to `[1 mark]` for a
one-mark part, using the same singular/plural expression as the question paper.
The real 40-page fixture checks all 39 part labels, both mark counts, page count
and unchanged blueprint data. Existing fillable-field checks remain. One expected
failure became 23 focused passes; logs are `/tmp/keldin-ead-mark-label-red.log`
and `/tmp/keldin-ead-mark-label-green.log`. The change affects only label text.

Ruff, formatting and diff checks passed for each CS source change. The PDF-related
groups reported five existing PyMuPDF/SWIG deprecation warnings. The separate
read-only embedded-form preview repair is integrated in root commit `8b6ac736`;
its native acceptance evidence is outside this note. Full combined tests,
packaging and protected CI remain separate release gates. No historical artifact
or model-generated answer was rebound or patched by this documentation.
