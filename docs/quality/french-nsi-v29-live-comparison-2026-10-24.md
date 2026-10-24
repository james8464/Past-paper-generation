# French NSI V29 live comparison — 24 October 2026

## Verdict

The targeted recursive-construction and correction-flow changes pass this engineering review. Overall examination fidelity remains **HOLD**. V29 improves E1 beyond a one-comparison repair, but retains substantial repeated routing work across E1/E3 and a finite authored task catalogue. One model/seed does not establish equivalent breadth, timing, difficulty or cross-paper novelty. No teacher, learner or model-independent qualification is claimed.

## Frozen-source live evidence

Two separate live runs used `gemma4:12b`, digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`, seed `270100`, and French reference-index SHA-256 `ec2339e6dffeba485f94d33d8e6f868e24cd2c40ad32830621201496ca32d594`. Both passed first attempt with zero repairs. Neither is a replay. Source was clean and unchanged during each run.

| Run | Source | Implementation SHA-256 | UTC completion / elapsed |
|---|---|---|---|
| Initial construction | `f56e93d` | `2f59799ee4d93bbebbe89e0c2ada8ddaff4b9a5b556ec62a5f610319aa2816bb` | `2026-10-23T23:55:59.064688+00:00` / 138.710 s |
| Final correction flow | `a318a36` | `7af8a518dc2ef5f9a5b97eecc02032d452fb1614373ff3b39e1138ba85a63b14` | `2026-10-24T00:04:24.819999+00:00` / 141.509 s |

Both have 12 A4 subject pages, 34 questions and a 24-page proposed correction. Final backend peak RSS was 135,839,744 bytes, excluding Ollama. Attempts, checkpoints, selections, manifests, PDFs and renders remain ignored under `tmp/pdfs/french-v29-tree-construction-20261024/` and `tmp/pdfs/french-v29-final-flow-20261024/`. Previous holds and failures remain intact. No official PDF is bundled.

| Artifact | Initial SHA-256 | Final SHA-256 |
|---|---|---|
| Subject | `be17653e1cbca2899dc873badd2fe06fc0bca9690493f4e781260e996c0350dc` | `58818911cd9b1c9a89a7494482d033ab904e827cf704ee67aa415ca565d168db` |
| Correction | `ef42efdd09d075a02e325b74d5fe3511afc512d0677057b1d1b70b63adf4fe09` | `5a8aad2ab2241f3ee728d14193987620621914277450436222f61d7c0218064a` |
| Assessment | `978567219512ac5d99787ae61d6628450b99d19b7f16c2ce55daa2072aa4a8c9` | `cf2c80466a7d3630fb72867d9b9500af8df977b08cc5541fbc2d62330881e620` |
| Manifest | `915844ca818a9a9d5514a665ad371dfbe24d2b8c9d91d7f96b9e812a018857bd` | `051df8b358aef99d21df87dbf2c2b608ad6d732be98b275fc7b27d1dbf54cbd4` |

## Official comparison and correctness

Re-read and visually inspected official 2026 Métropole day 1 pages 12–13: supplied tree-class representation, method construction, recursive interpretation and composition. The locally registered subject has SHA-256 `275b050d7577142794bb579b66ffc08fe7742a70c943a632eebd32701994310b`; [official source](https://eduscol.education.gouv.fr/sites/default/files/document/26-nsij1me1-128190.pdf). Also read day 2 pages 15–16 task text for queue/BFS distance, eccentricity construction and a justified meeting-point decision; its registered SHA-256 is `885f3687ea83486efb9a17c08467a5fed6f7b11fb629ca65ba103240ddd37db9`. This is a scoped comparison, not a new every-page official audit or comparison with an official correction.

V29's original task progresses from insertion and inorder justification to a complete recursive interval counter, inclusive boundaries, empty-tree handling and justified pruning. It does not copy the official scenario or code. For this printed tree after insertion, the keys are 10, 13, 18, 29, 35, 86; the inclusive interval 13–35 contains four keys: 13, 18, 29, 35. The reference implementation matches an independent flat-key oracle over all ordered integer intervals in the tested range, exact endpoints, empty trees and three printed-tree seed profiles. Forbidden-subtree tests check pruning; input-mutation tests check preservation. Only fixed app-owned code is executed.

Four quarter-point criteria cover the base case, justified pruning, inclusive recursion and the concrete result. E1 retains 70 indicative minutes. The complete paper retains three independent exercises, exactly 18 technical points and a separate 2-point indicative French-language rubric. These assigned times and marks are not learner calibration.

## Page-by-page visual findings

All outputs were rendered using Poppler at 80 dpi. Initial subject pages 1–4 and 6–12 were byte-identical PNGs to the inspected final V28 subject; changed page 5 was viewed individually. All 24 initial correction pages were viewed individually. All final subject pages and correction pages except 8–9 were byte-identical PNGs to that initial V29 output. Final correction pages 8–9 were viewed individually. Thus unchanged-page findings are carried forward by exact render identity, not inferred from text extraction.

| Subject page | Finding |
|---|---|
| 1 | Non-official cover and distinct technical/language totals intact. |
| 2 | Graph and introductory questions readable. |
| 3 | Dijkstra working table and complete BFS repair source present. |
| 4 | Both outage surfaces remain with the relevant questions. |
| 5 | Tree, insertion, traversal and full construction prompt together. Lower whitespace remains; legacy inline backticks are still visible in 1h/1i. |
| 6 | E2 context, faulty join and source relations readable. |
| 7 | Incident relation and comparison surface remain with tasks. |
| 8 | Count table, faulty function and full-function construction request readable. |
| 9 | State table, counterexample and prefix-invariant progression intact. |
| 10 | E3 scenario, link costs and route surface readable. |
| 11 | Timeline, route tasks and resource states intact. |
| 12 | Recovery/security tasks and distinct deadline/terminal question readable. |

| Correction page | Finding |
|---|---|
| 1–2 | Non-official cover and single indicative language rubric. |
| 3–5 | Graph, initial routing and complete BFS repair with credit readable. |
| 6 | First outage route cost 26; reduced 1f credit combines existing criteria without deleting them. |
| 7 | Second outage cost 30 and insertion task/source readable. |
| 8 | Inorder answer and new 1j prompt share the page. Initial rendering left only 1i here; regression now rejects that whole-question push. |
| 9 | Labelled 1j continuation keeps complete recursive code, pruning justification, numerical result and all four criteria together. |
| 10–11 | E2 context/relations and integrity answers readable. |
| 12 | Comparison table and 2c/2d answers/credit intact. |
| 13 | Corrected join and credit; sparse remainder remains a grouping trade-off. |
| 14 | Count table, LEFT JOIN/COUNT answer and credit together. |
| 15 | Faulty algorithm, traced incidents 103/105 and result 2 intact. |
| 16 | Full dictionary construction, S0 result and four criteria together. |
| 17 | State table, targeted updates and S0/S1/S2 results together. |
| 18 | Coincidental agreement counterexample, prefix invariant and empty-input result readable. |
| 19–20 | E3 scenario/source, timeline and initial routing answers intact. |
| 21 | Changed route cost 20 and independent deadlock cycle correctly distinguished. |
| 22 | Recovery times 22/26/28 and acquisition-order limitation intact; sparse remainder remains. |
| 23 | Security cards, transmission order and metadata distinction readable. |
| 24 | Authentication limits and separate deadline/compromised-terminal criteria aligned. |

No clipping, overlap or missing source/credit was observed at this inspection scale. Normal and large-print word-bound and content checks supplement the visual review. No blank pages were added to approach the official 16-page/36-question subject. A preliminary local render allowed natural flow but stranded the rubric; the final grouping keeps the whole answer and credit together instead. This local render was not a live model run.

## Verification and remaining work

Final-source local suite: **2,938 passed, 2 skipped**, five existing SWIG warnings, 150.59 seconds. Retained V26, final V28 and final V29 package replay passed. Ruff, repository hygiene, release compliance and diff checks passed. Graphify AST data was refreshed; 40 JSON sources still yield no nodes and semantic document extraction was not refreshed.

Read-only self-review covered version dispatch, immutable catalogue/blueprint identities, typed expected evidence, legacy replay, mark/time conservation and renderer scope. This is not independent external review. Protected Backend/macOS checks must pass on the final PR head before merge.

Engineering work remains on task-family variety, legacy inline-code typography, and final supported-route live/manual qualification. Accounting, Economics and Business release findings also need final-source output evidence. The expensive final matrix remains gated while the French fidelity review is HOLD. Teacher review, learner timing/mark calibration, document-specific rights and accessibility qualification remain external. No full-app finalisation, Apple HIG certification, school/regional approval or model-independent equivalence is claimed.
