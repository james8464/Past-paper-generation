# Teacher-feedback follow-up — 27 September 2026

## Status and scope

This is an engineering and representative-output review, not final qualification
of every subject, model, or exam board. The paused AQA Economics Paper 3 run did
not finish; its old checkpoint must not be treated as a passing paper.

## Corrections made in this pass

- Restored editorial review for selected-response questions. A deterministic
  answer contract no longer exempts a question from checks of ambiguity,
  distractors, source interpretation and mark-scheme quality.
- Questions explicitly locked against rewriting still undergo each review
  requested by the generation policy, even without difficulty review enabled.
- The editor receives the independently derived answer, working and verification
  scope. Disagreement must identify the conflicting source or step; arithmetic
  verification does not excuse an ambiguous stem.
- Valid AI-authored MCQ stems are retained. Source-owned options, keys and
  marking guidance remain protected, including when resuming saved questions.
- Versioned the review policy in checkpoint names, checkpoint identities and
  manifest provenance. Older accepted items cannot silently inherit this review.
- Removed Paper 2 mark-scheme filler that repeated marking points and generic
  guidance to reach the 2025 reference's page count. Pagination now follows actual
  content. Removed the two unused fixed-pagination tables.
- Added a content-based release check: the scheme must retain all printed
  marking points, acceptance/rejection guidance and level descriptors from its
  matching assessment package, with no empty padding pages. The question paper's
  page geometry and fixed page-count policy are unchanged.

## Teacher checklist

| Feedback | Evidence checked |
|---|---|
| Calculation answers must include final values | Sound calculation prints the method and **24.72 MiB** for the sampled data; exact/rounded values and incorrect units have regression tests. |
| More demanding, contextual SQL | Fitness-centre schema and joined aggregate query, error identification, INSERT, scoped UPDATE and conditional DELETE. SQL verification tests execute isolated semantic checks against the declared source/intent. |
| Fetch/decode/execute must use all three buses | Sample scheme states address transfer on the address bus, read signal on the control bus, instruction transfer on the data bus, followed by register/decode/execute actions. |
| Stored-program explanation needs technical precision | Scheme links loading new instruction sequences from memory to running different programs without changing processor hardware. |
| Boolean symbols, not prose operators | Rendered expression uses multiplication, addition and overbar; glyph tests check XOR/NAND/NOR have visible ink. A final simplified answer is printed. |
| Compression answers must use context | Financial-record sample requires exact reconstruction for audit/reconciliation, not simply “better quality”. |
| Paper 2 programming should be functional | Immutable lists, base/recursive pattern matching and pure-function consequences appear in question and scheme. |
| Floating-point task must be substantive | Signed-exponent direction, denary conversion, normalisation and range/precision trade-off replace mere copying. |
| Repetitive guidance only once | The rendered Paper 2 PDF exposed repetitions missed by blueprint-only tests. Removed filler; added PDF-output regression checks. |
| Topic question banks, especially data structures | The 4.2 bank generated successfully as a preview; existing banks also cover 4.10 and 4.12. |

Primary regression coverage: `test_blueprint.py`, `test_closed_response_integrity.py`,
`test_sql_answer_verification.py`, `test_render_content.py`, `test_mark_scheme.py`
in the AQA CS generator tests; shared tests in `test_ai_assessment.py`,
`test_layout_master.py`, `test_computer_science_objectives.py` and `test_app_backend.py`.

## Output evidence and limitations

- Generated Paper 2 and bank 4.2 through the app's backend bridge with seed
  `26092701`, in **preview mode**. These are not freshly AI-authored papers.
- Manually inspected representative SQL, calculation, processor, functional,
  floating-point and Boolean pages. Compared reference question page 25 and
  mark-scheme page 20 of AQA 7517/2 June 2025 with generated typography/layout.
- Paper 2 remains 40 pages; its complete scheme decreased from 35 to 21 pages
  after removing filler. The bridge successfully published the revised package.
- The exploratory comparison at 85 dpi / 100 perceptual dpi reported 70.2% for
  the question paper and 68.8% for the revised scheme (69.5% aggregate). These are
  tool-specific similarity scores, **not** percentages of correctness or a
  qualification pass. The scheme previously scored 70.7% despite duplication;
  matching arbitrary page count is not a sound quality objective.
- A live `gemma4:12b` single-item smoke test re-authored AQA Economics P3 Q5,
  independently solved it and passed editorial review with answer **202.4** for
  `176 × 1.15`. This did not run whole-paper or reference-demand qualification.
- Local QA artifacts are under `tmp/pdfs/teacher-review-20260927/`; the corrected
  Paper 2 package is in `revised/paper-2/`. They are ignored development outputs.

## Remaining work before any “finalised” claim

1. Requalify full live papers under the restored review policy, not the bypassed
   checkpoint. A single successful question is insufficient.
2. Broaden source/task generation: some selected-response sources and CS Boolean
   exercises still use a small template set. New wording alone does not establish
   genuine cross-paper novelty or calibrated difficulty.
3. Revisit Boolean and floating-point tariffs with reference tasks: a one-step
   absorption exercise for four marks and a multi-step conversion for one mark
   need examiner-led scrutiny, even though totals and arithmetic are checked.
4. Improve typography and spacing: the reference has lighter/smaller page furniture,
   different header alignment, and different table/content density. Do not copy
   branding or misrepresent independent material as an official board paper.
5. Review Paper 1's separate continuation/reference-solution layout; this pass
   changed Paper 2 only. Do not generalise the no-padding result to every route.
6. Repeat complete print/accessibility qualification and signed App Store
   preflight after the final changes. A Debug build and static compliance scan
   are not App Store approval or exhaustive runtime/UI testing.
7. Obtain fresh teacher review of actual AI outputs and student-response evidence
   before claiming examiner-equivalent quality or empirically matched difficulty.

## Verification of this change set

- Full Python suite: **1,843 passed, 2 skipped**, with five existing PyMuPDF/SWIG
  deprecation warnings (89.34 seconds).
- Native macOS tests: **61 passed**, zero failures. Fresh final Debug build
  succeeded with warnings-as-errors and complete strict-concurrency checking.
- Static release-compliance scan passed dependency bounds, font licences,
  privacy manifest, sandbox entitlements and tracked-secret checks.
- Independent code review found no blocking regression and checked 100 seeded
  compact scheme renders without bottom overflow. A non-blocking hardening gap
  remains: the content-completeness check verifies global text presence, not
  per-part attribution or duplicate-page detection. Renderer regression tests
  separately guard the observed duplicated-guidance defect.
- Graphify refreshed after code changes. Changes committed locally; no push.

## Publication follow-up

The earlier local-only history was published to GitHub at `9934b49`. That direct
push reported an administrator bypass of the PR/check rules. Subsequent changes
use a temporary review branch and the normal pull-request checks instead.

- Compact Paper 2 marking credit is now checked within each question/part row.
  Missing repeated short answers cannot hide behind another part's identical
  text. Duplicate rows/pages and repeated or misplaced levels continuations are
  rejected; legitimate next-page levels continuations remain supported.
- Four-mark Boolean simplification now uses three variables, explicit equivalent
  intermediate expressions and three possible final functions. Truth-table tests
  verify every step. This improves demand, but three templates still do not prove
  sufficient variety or empirical calibration.
- Shared subject interfaces now live independently of plugin discovery. Fresh
  processes can import each subject directly without a circular-import crash;
  the existing public interface remains available.
- Clean GitHub checks exposed a missing cryptography test dependency and an
  optional-Boolean switch unsupported by the runner's Swift compiler. Both were
  corrected without weakening the checks.
- Preview matrix seed `26092721`: all 21 routes produced their expected outputs.
  Eighteen passed reference-demand checks; the three topic banks correctly remain
  unqualified because topic-reference evidence is insufficient. Preview output
  is not live AI qualification.
- Visually inspected the revised Boolean mark-scheme page at 1,400-pixel page
  height: the working, overbars, table borders and final answer fit without
  clipping. This is representative inspection, not exhaustive print certification.
- Final backend suite: **1,873 passed, 2 skipped**, five existing SWIG warnings
  (82.90 seconds). Native macOS suite: **61 passed**, no failures. Local Release
  build, signature/sandbox preflight, lint and release-compliance scans passed.
- Independent review found short numeric credit could match a different number.
  Whole-statement numeric checks now reject incorrect signed, decimal, fractional
  and expression variants; 34 targeted review tests passed with no remaining
  review findings. The complete suite above includes the final fix.
- Repository inventory and Graphify AST map refreshed. Required GitHub checks
  remain the merge gate; local success is not a substitute for clean-runner CI.

Full live-paper qualification, broader task variety, remaining layout fidelity,
teacher review and anonymised student calibration remain release limitations.
Do not describe the app as examiner-equivalent, visually identical, App Store
approved or fully finalised on the strength of automated checks alone.

### Clean-runner and live follow-up

The first PR check exposed 13 failures hidden by the development machine:
missing ignored reference PDFs, Linux font substitution in Mac typography
checks, and MLX handler tests assuming Apple hardware. The full PDF/backend job
now targets the supported macOS platform, without removing its assertions.
Reference-extraction unit tests use generated offline PDFs to exercise the real
extraction paths; these fixtures are not real-paper qualification evidence.

The live data-structures bank (effective seed `26092731`, `gemma4:12b`) failed
after 861.46 seconds at Q4.2 independent route reconciliation; no output package
was published. The saved graph has the unique shortest route A → C → F (two
edges), and the saved scheme is correct. The failed solver response was not
retained, so its exact cause cannot be established retrospectively. Offline
replay did expose a separate false rejection of equivalent arrow notation;
slot-specific ordered-route matching addresses that without allowing wrong,
missing, extra or reordered vertices. The failed live run remains unqualified.

The full 18-paper preview comparison reported 70.6% aggregate structural/visual
similarity (question papers 68.6–79.2%, schemes 61.1–75.2%). These diagnostic
metrics and representative page inspection show remaining differences, not
visual identity. Detailed current release gates are tracked in GitHub issues
#4 (live matrix), #5 (student calibration) and #8 (editorial/print release gates).

Final second-batch verification: **1,914 backend tests passed, 2 skipped**, five
existing SWIG warnings (73.90 seconds). The independent reviewer passed 210
targeted tests and reported no findings. The first-batch GitHub macOS job passed
its native tests and App Store preflight; the final commit must independently
pass both required hosted checks before merge. Graphify and lint were refreshed.
