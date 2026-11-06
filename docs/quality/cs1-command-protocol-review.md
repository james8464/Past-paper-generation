# Computer Science Paper 1 command contract

A fresh offline preview from the installed PR179 helper produced four PDFs:
24-page question paper, 40-page electronic answer document, 19-page mark scheme
and two-page preliminary material. All 85 pages were visually inspected across
two reviewers. No clipping, broken table continuation or missing response area
was observed in that sample. Sparse support pages and the full-page response
areas for short items remain recorded, not treated as calibrated writing space.

The question paper's page 17 printed a comma-separated command format. The
supplied program instead accepts standalone ADD, REPORT, BEST and QUIT commands.
An owned stdin test confirmed that the printed ADD format produces “Unknown
command” and never enters the function candidates are asked to complete.

One deterministic renderer line now describes the actual command prompt. It
does not rewrite a model response, change the supplied program, alter Question
11 or 12, or change any mark allocation. The CSV data format remains separate.

Regression controls bind printed commands to the generated program's command
comparisons and context metadata across all four current scenario families.
Four tests failed before the change; the actual program-loop control already
passed. The final focused set passed 14 tests. Five baseline/current render
comparisons retain 24 pages and differ in extracted text only by this exact
guidance replacement on page 17. The changed page was rendered and viewed.

The new command-contract test file received a complete source review. The large
renderer received a one-line delta review, not a whole-file audit. These are
offline layout and workflow checks, not freshly model-authored paper quality,
official fidelity or observed student timing.
