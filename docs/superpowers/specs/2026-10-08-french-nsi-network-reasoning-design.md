# French NSI network reasoning depth — versioned design

Status: implementation design, 8 October 2026. This is not a teacher or examination-fidelity approval.

## Decision and scope

The pinned V17 live subject passed automation but remains a manual fidelity hold: its final Exercise 3 page contains only 3e–3f, and the official 2026 Métropole comparator develops its third case through fifteen questions over six pages. Counts are comparison signals, not a 2027 template. The next written-paper version, `fr-nsi-written-2027-v18`, will expand the original app-owned Exercise 3 into a connected, checkable reasoning sequence. Exercises 1 and 2, UK routes, and all V13–V17 saved packages remain version-pinned and readable.

Exercise 3 will have twelve questions, `3a`–`3l`, grouped into three independent parts within one coherent station case:

| Part | Questions | Candidate work and evidence |
|---|---|---|
| A: routing | 3a–3d | Read the seven-link weighted graph; show first relaxations and a predecessor table; justify the initial minimum route; recompute selected Dijkstra states after the app-owned link-cost change and compare routes. |
| B: processes | 3e–3h | Read an app-owned resource-allocation snapshot; derive a wait-for cycle; trace the specified abort-and-release recovery; justify an acquisition-order invariant and its limits. |
| C: security | 3i–3l | Order the authenticated-station-key and session-key exchange; distinguish what a passive observer can read; separate station from sender authentication; analyse visible metadata and a compromised endpoint. |

This is not twelve renamed fragments of the existing six prompts. The version-three contract adds finite intermediate states and displayed working surfaces: a Dijkstra table with pre/post-change facts, a resource-state schedule, and a message/threat table. All facts and solutions are computed or fixed in application-owned code. The model may select only a scene and finite wording IDs; it cannot submit graph facts, code, marks, answers or free-form claims. Verifiers reject missing or contradictory printed facts and answer leakage. No model-submitted code is executed.

## Scoring and timing

The existing route's E3 allocation remains exactly 5.5, 6 or 6.5 technical points. Twelve base credits of 0.25 total 3 points. The remaining 2.5, 3 or 3.5 points are allocated in quarter-point criteria to the multi-step routing, recovery and security judgements, with no credit exceeding the evidence requested in a prompt. The concrete per-question profile and its 70-minute estimate will be pinned in the blueprint and tested for every seed/allocation. The full written paper remains three exercises, 210 estimated minutes, 18 technical points plus a separate two-point indicative French-language component. Timing and marks are design estimates pending learner and teacher calibration.

## Version and presentation boundaries

- A new immutable canonical `NetworkReasoningContract` uses version 3, seed, twelve task IDs, all displayed materials, derived states, expected answers and a digest. Its constructor recomputes from the seed and rejects changed facts. V15–V17 continue to use the untouched six-question `NetworkDepthContract` V2.
- V18 receives its own finite French catalogue, prompt identity, provider schema dispatch, package replay and PDF verifier. A package cannot claim one version while carrying another version's contract, IDs or digest. French-only reference retrieval, holdout isolation, local-only default, non-official PDF labels and UK compatibility are unchanged.
- Subject page flow should keep instructions, figures, tables and the question that depends on them together without padding to a page-count target. Correction answers and their indicative credits must remain attributable, and standard/large-print output needs measured bounds and visual inspection.
- No final UK/French model matrix runs while this shared source changes. After protected integration, run one pinned French live diagnostic; retain every attempt and hash, compare every PDF page with the official 2026 paper, and record a measured pass or hold. Teacher review, learner timing/mark calibration, rights clearance and accessibility evaluation remain external gates. The practical component is unsupported.
