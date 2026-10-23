# French NSI V28 live comparison — 24 October 2026

## Verdict

The targeted construction and response-flow repairs pass this engineering review. E2 now requires a complete function and a prefix-count justification, rather than only tracing and a one-condition repair. Working tables stay with the relevant questions in the normal-print subject and correction. **Overall examination fidelity remains HOLD**: one seed/model and a finite authored catalogue do not establish equivalent breadth, difficulty, timing or cross-paper novelty. No teacher or learner qualification is claimed.

Three separate live runs were retained. None is a replay. All used `gemma4:12b`, digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`, seed `270100`, and French reference-index SHA-256 `ec2339e6dffeba485f94d33d8e6f868e24cd2c40ad32830621201496ca32d594`. All passed first attempt with zero repairs. Source was clean and unchanged during each run. Dates below are UTC; completion was 24 October in Paris. The third, verification-only follow-up is recorded at the end; the page log describes its identical printed content.

| Run | Source | Implementation SHA-256 | Completion / elapsed |
|---|---|---|---|
| Initial construction/flow | `5719e2a` | `e624dbb0cc4400e0236010451fabe7ca9961c0e3c1b8daea7db0fdf1bdfc8a9c` | `2026-10-23T22:31:47.263918+00:00` / 139.141 s |
| Final flow follow-up | `5fe0b9d` | `7445740777b0644263abbfabddb40e3e9545399ebbb90be97b9df4571e26ef9c` | `2026-10-23T22:36:17.215652+00:00` / 85.249 s |

The first command invocation failed at import before inference because a new benchmark import preceded its path bootstrap. The initial live run then used `PYTHONPATH=.`. A red/green CLI regression fixed the bootstrap order; the final run uses the direct command without that workaround.

## Retained artifacts

All attempts, selections, checkpoints, PDFs, manifests and renders remain ignored under `tmp/pdfs/french-v28-construction-flow-20261024/` and `tmp/pdfs/french-v28-final-flow-20261024/`. Earlier V27–V15 holds and V12–V14 failures are preserved. The first V28 catalogue is an unreleased iteration: replay it with its recorded source, not the revised catalogue. Released V13–V27 behavior remains version-bound.

| Artifact | Initial SHA-256 | Final SHA-256 |
|---|---|---|
| Subject | `1321360aa537b5ee6a742d466acbd95e57de25c6f12a166b6fd69665b186b161` | `6c71735c47d07d8ea2c7993c626791894fb7cbe512c7584af92d6080ae731ade` |
| Correction | `b8534717c6883ba4bba93c5d7ab3ae17fc28ada17cb291fc46b0617ee068c7f9` | `2e8d2df7b0602d8a090cfc0ae949c9bba8a8de2510b10a7b9ac32c7b62e1c49b` |
| Assessment | `4286020ee53764ff87840859ae99cb7d4967bd61f90cbb4bf2bae6acc1de18d5` | `3e39612deb8d880fe3cd23c07257427ae593c578896363f62712adeac423279e` |
| Manifest | `118a0cbeb4f1eb090d14a9468ccfe58fa227e6ab18d40605e4fd89b0650231d8` | `5200dd7594d64ed03f6bd5f45d30f162c1b7321fb06e311c1dd904df9825d0c0` |

Both subjects have 12 A4 pages and 34 questions. The initial correction has 21 pages; the final correction has 23. Final backend peak RSS was 135,856,128 bytes, excluding Ollama. No pages were inserted to match an official page count.

## Official comparison

Two locally registered official 2026 Métropole subjects informed the review. No official correction was compared and no official PDF is bundled.

- Day 1: `nsi-2026-normal-metropole-jour-1.pdf`, SHA-256 `275b050d7577142794bb579b66ffc08fe7742a70c943a632eebd32701994310b`; [official source](https://eduscol.education.gouv.fr/sites/default/files/document/26-nsij1me1-128190.pdf). Re-inspected pages 7–10 and 12–13 visually, with extracted task text: representation, construction, composition and recursive reasoning.
- Day 2: `nsi-2026-normal-metropole-jour-2.pdf`, SHA-256 `885f3687ea83486efb9a17c08467a5fed6f7b11fb629ca65ba103240ddd37db9`. Read the relevant task text and rendered pages 5, 8–9 and 16: class-method construction, test/correction progression, function composition and a justified graph decision. This is a scoped comparison, not a fresh visual audit of all its pages.

The official progression supports the new construction-plus-invariant demand, but does not prove equal workload. Both official subjects also contain legitimate sparse pages. Whitespace and 12 versus 16 pages are not correctness measures. V28 still devotes substantial work to repeated shortest-path tracing across E1/E3; the official examples contain more varied composed code tasks. Broader authored task diversity and a final live matrix remain engineering/evaluation work, not problems solved by padding or typography.

## Every-page visual review

All initial 33 pages were rendered with Poppler at 80 dpi and viewed. This exposed correction table/question splits at E2 2f and 2i, and the ambiguous phrase “your function” in 2l after intervening questions about the old function. The follow-up fixes these and the E3 security-card split, and removes internal `recon_*` headings without hiding SQL relation names.

All final pages were rendered at the same scale. Subject pages 1–6 and 10–12 are byte-identical PNGs to the inspected first run; changed subject pages 7–9 were viewed. All 23 final correction pages were viewed individually, including pages changed only by the total-page footer. No clipping, overlap or missing content was observed at this scale. Automated normal/large-print word-bound checks supplement, not replace, this review.

| Final subject page | Finding |
|---|---|
| 1 | Non-official cover, three independent exercises, 18 technical plus 2 language points. |
| 2 | Readable graph and introductory tasks; edge weights agree with source list. |
| 3 | Dijkstra table attached to 1c; complete BFS bug code visible. |
| 4 | Both outage working surfaces and 1f/1g share a page; less fragmentation. |
| 5 | Tree table, insertion, inorder and search tasks together; lower space is unused, not padded. |
| 6 | E2 context, faulty join and two named source relations readable. |
| 7 | Incident relation and comparison table attached to their tasks; internal heading removed. |
| 8 | Count table, complete faulty function and new full-function request readable. |
| 9 | State table, counterexample and invariant prompt; explicit reference to 2h/repartition_clos. |
| 10 | E3 scenario, link costs and route surface readable. |
| 11 | Timeline, route tasks and resource state together. |
| 12 | Recovery/security sequence and distinct deadline/terminal question readable. |

| Final correction page | Finding |
|---|---|
| 1–2 | Cover and one general indicative-language rubric; no official marking claim. |
| 3 | Graph, degree and detour answers readable. |
| 4 | Initial trace, route and credit together; shortest cost 23. |
| 5 | Complete BFS repair and four distinct quarter-point criteria. |
| 6 | First-closure table, 1f, answer and rubric together; route cost 26. |
| 7 | Second-closure route cost 30 and insertion table/task together. |
| 8 | Inorder/search answers and credit readable. |
| 9–10 | E2 source relations, integrity questions and reduced credit readable. |
| 11 | Join comparison surface, row answers and 2c/2d credit together. |
| 12 | Correct SQL and 2e credit intact; sparse remainder is the grouping trade-off. |
| 13 | Count surface now shares the page with 2f, SQL answer and rubric. |
| 14 | Complete faulty function, traced rows 103/105 and answer 2. |
| 15 | Full app-owned construction code, S0 dictionary and four criteria intact. |
| 16 | State surface now shares the page with 2i/2j and targeted updates. |
| 17 | Fortuitous agreement counterexample and prefix invariant/empty-input answer. |
| 18 | E3 scenario and route source intact. |
| 19 | Timeline and initial routing answers/credit readable. |
| 20 | Changed route and deadlock tasks; cost 20 and cycle correctly distinguished. |
| 21 | Recovery at 22/26/28 and acquisition-order limitation intact; sparse remainder. |
| 22 | Security cards now share the page with 3i and its answer/credit; metadata separate. |
| 23 | Authentication and distinct deadline/compromised-terminal credit consistent. |

Independent arithmetic/code checks agree with the printed answers: closed S0 counts are `{1:1,2:0,3:2,4:1,5:0}`; S0/S1/S2 corrected category-2 counts are 0/1/2; faulty counts remain 2/2/2. The new reference function matches an independent sum oracle over row permutations, empty inputs and category subsets without input mutation. This does not assess arbitrary student code.

## Verification and remaining gates

Final full local suite: **2,917 passed, 2 skipped**, five existing SWIG warnings. Ruff, diff checks and static release compliance passed. Graphify AST inventory was refreshed; 40 JSON sources still produce no graph nodes, so this is not a complete semantic-document refresh. Read-only self-review covered version dispatch, catalogue hashes, legacy defaults, reference-code behavior and layout tests; it is not an independent teacher or external code review. Protected Backend/macOS checks are required before merge.

Remaining work includes broader task-family diversity and final supported-route/model qualification. Teacher review, learner timing/mark calibration, per-document rights and accessibility qualification remain external. The final expensive matrix is not run while the overall manual fidelity gate is HOLD. No full-app, Apple HIG, examiner, school, regional or model-independent-equivalence claim is made.

## Verification-only follow-up on final code

Read-only review identified that the new construction tasks retained only the older incident-verification facts. Their authored prose/code were catalogue-bound and unit-tested, but their saved deterministic evidence did not explicitly report the new counts. The repair adds versioned evidence for questions 2h/2l: independently recomputed S0 counts, all prefix counts, empty-category results and the app-owned code hash. Unknown versions, altered counts/prefixes and stripped package evidence are rejected by regressions. No model-supplied code is executed; prefix examples are not a formal proof of arbitrary programs.

A third clean-source live run at `72483b3` completed `2026-10-23T22:48:19.817072+00:00` in 135.903 seconds, first attempt/zero repairs. Implementation SHA-256: `ff58586f046390180236e355b0a925bf139d489df2bfb6c501056cea1ac93a28`. Backend peak RSS: 135,938,048 bytes, excluding Ollama. Retained directory: `tmp/pdfs/french-v28-construction-evidence-20261024/`. All 35 rendered pages are byte-identical PNGs to the reviewed flow follow-up: 12-page subject/34 questions and 23-page correction. Thus the page findings above apply without a new visual-layout claim. The two earlier V28 iterations require their recorded source for replay; they are not silently upgraded.

| Final artifact | SHA-256 |
|---|---|
| Subject | `961886ec145a75baa47513408cafa324bb0d948662f327162e335fea0aaeec2e` |
| Correction | `0bb2c5af47ee5c848bff851e55d15b2e7e837d407fabd6912adc78a6f1c0729b` |
| Assessment | `6aced2c29d3e7f08d90325f91e931ffb1040c39f329bccc5fa5ef605a0a6e6b8` |
| Manifest | `c4a242b53a4fc146230c99421175c7030d1a48b49451a2bfd7f499b970662f2d` |

The full suite was rerun after this repair: **2,917 passed, 2 skipped**, five SWIG warnings, 137.92 seconds. The earlier green CI head is not sufficient; protected checks must pass on the final PR head before merge. Overall qualification remains HOLD.
