# French NSI V23 — sustained network incident case

Status: implementation design, 13 October 2026. This is an app-owned, non-official written-paper exercise, not teacher or examination approval.

## Decision and boundary

V22's pinned live paper passed automated checks but remains a manual fidelity HOLD: 32 questions on 11 subject pages versus 36 on 16 pages in the official 2026 Métropole comparator. Its Exercise 3 ends sparsely and its routing, process and security sections read as adjacent mini-cases. V23 replaces only Exercise 3 in new packages with a single causal incident. It does not alter V13–V22 packages, UK routes or state, or the app-owned E1 and E2 exercises. The page-count comparison is a diagnostic, not a padding target.

## Candidate-facing incident

Central sends a measurement packet M-27 to Station through a weighted five-node network. A link-cost change reroutes the connection and delays the packet beyond a stated deadline. At Station, the delayed packet remains queued while an ingest process holds one resource and waits for another; a maintenance process holds the second resource and waits for the first. The candidate traces the wait-for cycle, an explicitly specified abort/release/restart response and its effect on queued data. Once M-27 is processed, Station sends an encrypted processing report back to Central using a documented key exchange. The candidate evaluates confidentiality, Central's authentication as recipient, missing Station sender authentication and exposed metadata/endpoint limits. Each later section refers to a concrete result from the earlier section; no unstated network or cryptographic behaviour is assumed.

The paper presents evidence close to its dependent tasks in three stages: (1) link and packet deadline card plus before/after route-working tables; (2) packet arrival/queue and resource-allocation snapshots plus a recovery working table; (3) message cards and a threat-working table. Stages must not leak model answers. Normal and large print reserve useful candidate writing space beside the reasoning tasks and keep evidence with the questions that use it. Correction answer and credit stay together. The target is sustained checkable work, not a fixed number of pages.

## Immutable contract and scoring

`fr-nsi-written-2027-v23` has a new canonical, hash-bound E3 contract and finite French wording catalogue. Twelve question IDs `3a`–`3l` remain, but prompts and criteria require intermediate states and causal conclusions. Candidate facts include seeded graph/link change, explicit packet deadline, resource ownership and queue snapshots, specified recovery actions, and precise key/message assumptions. Expected routes and predecessors are recomputed by an independent shortest-path oracle; deadline/queue, wait-for/recovery and security answers are independently derived from the displayed facts. Contract deserialization rejects every edited, missing or mixed-version fact. The model selects only registered scene/wording IDs, never marks, facts, answers, code or free-form claims. No model-submitted code is executed.

E3 retains the existing 5.5/6/6.5 technical-point profiles and 70-minute estimate, with quarter-point criteria assigned to intermediate work and conclusions, never more credit than a prompt elicits. The complete paper remains three independent Terminale written exercises, 210 estimated minutes, exactly 18 technical points plus a distinct two-point indicative French-language component. Timing and credit are design estimates pending learner and teacher calibration.

## Dispatch, replay and verification

V23 receives explicit pipeline/provider selection, prompt identity, package identity/replay, runtime PDF verification and benchmark dispatch. A package cannot claim V23 while carrying a V22 E3 contract/catalogue/digest or vice versa. V13–V22 saved French packages and UK packages/state replay without migration or changes to their facts. Reference retrieval remains French-only with no UK fallback and holdouts excluded. PDFs retain non-official labels.

Tests cover canonical roundtrip/tampering, independent expected values for representative seeds, finite model selection, exact scoring/time, causal evidence/answer/credit checks, normal/large material association and bounds, mixed-version failure and old-package/UK replay. A NOT-LIVE fixture gets page-by-page inspection against all 16 official 2026 Métropole pages. After protected integration, one pinned French live diagnostic retains every attempt and artifact/hash; every generated PDF page is visually inspected and an honest English pass/HOLD record updates Occitanie claims. No final expensive UK/French model matrix runs while shared source changes or manual fidelity holds. Teacher review, learner calibration, document-specific rights clearance and accessibility evaluation remain external gates; no practical component is claimed.
