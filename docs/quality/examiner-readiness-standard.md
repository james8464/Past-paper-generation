# Examiner-readiness standard

The aim is original, AI-authored practice assessments which a subject specialist
could consider suitable for a real examination. This is a quality target, not
permission to claim exam-board, teacher or moderator approval. No finite test
matrix guarantees the correctness of every future stochastic generation.

## Release criteria for every advertised route

1. **Specification and structure:** current applicable board/paper coverage,
   allowed task types, candidate choices, timings, total marks and assessment
   objectives. A valid total cannot excuse inappropriate tasks or repeated credit.
2. **Answerability:** all required facts, definitions, tables, diagrams, datasets
   and numerical inputs are printed and consistent. The writer, blind solver,
   reviewer and renderer consume the same public source contract. No hidden
   chart values or worked answers may substitute for candidate evidence.
3. **Subject correctness:** independently checked calculations, units, code,
   queries, logic and causal reasoning; valid assumptions and alternative routes.
   Unknown or disputed results remain unresolved, never silently passed.
4. **Marking:** specific observable credit, accurate final answers where required,
   defensible partial credit and follow-through, and the correct board/task level
   bands. Explanatory answers must not require evaluative judgement merely because
   another task with the same tariff does. General guidance appears once.
5. **Demand and originality:** coherent original scenarios and genuine reasoning,
   not renamed topics in generic prose. Difficulty, scaffolding, breadth and mark
   distribution are compared to several relevant real task examples. Source
   support and model estimates are not student-response calibration.
6. **Diagrams and presentation:** diagrams express the actual task and solution,
   with correct axes, labels and changes. PDFs preserve every required credit and
   input, readable board-style typography, appropriate tables and writing space,
   and natural pagination. No padding or repeated guidance to match a page count.
   Independent branding and truthful practice-paper labelling remain.
7. **Reliability:** reproducible regression tests for every discovered defect;
   successful final-source live generation, artifact identity verification and
   manual inspection on all 21 advertised routes. One seed is smoke evidence,
   not route-wide reliability: then inspect at least three distinct live seeds
   per route, covering materially different supported task/case variants. Existing
   seeds count only if final identities remain valid. More variants require more
   evidence; three seeds do not certify unseen variants.
8. **Honest qualification:** automated generation, content checks, visual review,
   subject-expert review and empirical calibration remain separate evidence
   states. Zero unresolved critical/major content, source, marking or readability
   defects in the inspected release samples. A route with unresolved defects is
   not finalised. Human approval can only be recorded from a real identified
   review of the exact artifacts; never synthesize or infer it from AI approval.

## Current findings and delivery order

Issues #12 and #13 are release blockers, not cosmetic polish: Accounting decision
cases are incoherent/incomplete, and Economics marking policies, diagrams and
source labels diverge. The earlier Accounting Paper 1 blind-solution failure
also remains unresolved. Similar mechanisms must be audited across other routes.

First preserve and finish the single stable baseline matrix to expose failures.
In parallel, implement bounded repairs in an isolated checkout without running
another model job. Do not integrate changed runtime into the active batch.
Then review and publish through protected PR checks, rerun against final identity,
and perform route-by-route content and full-size PDF review. Repeat until the
engineering criteria are met; prepare a review packet for actual teachers or
moderators without presenting that pending external review as completed.

The teacher's CS feedback remains an acceptance checklist: explicit numerical
answers, demanding contextual SQL, complete bus explanations, A-level depth,
symbolic Boolean operations, context-bound answers, correct paper scope,
meaningful floating-point tasks, non-repetitive guidance and useful topic banks.
Verify these against fresh outputs, not just the presence of implementation code.

Release build, runtime, accessibility, Intel compatibility and Apple distribution
checks remain separate from assessment quality. Neither successful compilation
nor App Store acceptance would establish educational validity.
