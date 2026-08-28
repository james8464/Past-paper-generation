# Cambridge International engineering foundation — 26 August 2026

## Scope

The repository now contains versioned, data-driven foundations for:

- Economics 9708 Papers 1–4 for the 2026–2028 syllabus;
- Computer Science 9618 Papers 1–4 for the 2026 syllabus, including the
  Paper 4 source-code and testing-evidence output roles.

The structures, timings, marks, content boundaries, programming-language
rules, and provenance links come from Cambridge International's published
syllabuses:

- <https://www.cambridgeinternational.org/Images/697423-2026-2028-syllabus.pdf>
- <https://www.cambridgeinternational.org/Images/697372-2026-syllabus.pdf>

No official PDF, logo, question wording, candidate data, or mark-scheme text is
stored in the repository.

## Implemented evidence

The shared configured-family adapter generates original deterministic previews
and uses the existing independent AI authoring/review pipeline for live runs.
Every configured paper produces a question paper, mark scheme, and assessment
package; Computer Science Paper 4 also produces an editable source file and a
testing-evidence template. The renderer uses selectable vector PDF content,
atomic publication, adaptive cover typography, collision-safe mark placement,
weighted and wrapped scheme cells, section-specific topic boundaries, and the
Cambridge board profile. Deterministic calculation and trace previews contain
enough original data to solve and include independently recomputed results;
live runs still use the AI authoring and review pipeline.

Automated review generated all eight previews with seed `8464` and verified:

- exact paper IDs, marks, timings, section choices, output roles, and syllabus
  provenance;
- blueprint and structured mark-scheme reconciliation;
- microeconomics/macroeconomics section boundaries, coherent source-panel
  routing, exact calculations, and executable trace-table logic;
- assessment-package release validation, including contract guidance and
  levels-based responses;
- readable/selectable PDFs, no empty pages, and no text outside the page box;
- valid practical source/evidence artifacts for 9618 Paper 4;
- deterministic coverage-matrix discovery without exposing either family in
  the app.

All sixteen PDFs were regenerated and passed release-PDF validation. A manual
page review covered a data-response question page, a dense scheme page, and a
programming question page after fixing mark-label collisions, narrow guidance
columns, awkward option instructions, invalid calculations, and underspecified
trace questions. The local preview artifacts are intentionally outside Git at
`/tmp/paper-creator-cambridge-v6.G95ZDy`.

## Deliberate release gate

Both registry entries remain `advertised: false`, with engineering, visual,
and empirical qualification set to `not_run`. Cambridge's public past-paper
page states that question-paper layout and formatting changed from March 2026,
so older specimen papers are not sufficient evidence for a current visual
profile. Promotion requires current authorised examples, a two-seed live-model
matrix, migration/package checks, 300/600-DPI comparison, print review, and a
subject-competent reviewer. Empirical readiness additionally requires the
external calibration programme.
