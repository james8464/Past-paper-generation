# Controlled French NSI network exercise — 7 October 2026

Status: approved for implementation by James. The request expressly waives a separate design presentation. This is an engineering design, not teacher approval.

## Failure to address

The first complete pinned live draft passed automated checks but its third exercise was not answerable from its stated routing facts. Its process remedy did not break the demonstrated wait cycle, and its cryptography explanation made an unjustified necessity claim. Preserve that failed draft and its manual rejection; never reclassify it as accepted evidence.

## Candidate-visible contract

Exercise 3 remains an independent 70-minute written Terminale NSI exercise with six questions and the existing seeded 5.5/6/6.5-point profiles. The app owns every fact, answer, marking criterion and printed sentence. The local model may choose only finite, versioned French scene/question/rubric IDs. A selection cannot alter the graph, process state, security premises or credit.

Part A prints a four-node bidirectional network as an explicit link-cost table: Central–R1–Station and Central–R2–Station. The two paths have distinct initial totals. One named link cost changes; the preferred path then changes without a tie. The application recomputes both totals and paths from the table, and validates that the expected answer is not supplied as an independent mutable assertion.

Part B prints a two-process, two-resource hold/wait table: B holds A and waits for B; C holds B and waits for A. The cycle is genuine. The requested repair explicitly requires process C to release/reacquire and both processes to acquire A before B. The answer must state how this breaks the cycle, not merely restate B's existing order.

Part C states that the endpoints have no pre-shared secret, the receiver public key is authenticated, and the threat considered is a passive observer. Questions ask for three conceptual exchange steps, then confidentiality and limits. The correction distinguishes confidentiality from authentication and does not say asymmetric encryption is universally indispensable; a different deployment with a pre-shared secret is possible.

## Integrity boundaries

- A canonical, seeded data contract is reconstructed and hashed, including all link costs, before/after route computation, process state and security premises.
- The finite wording catalogue is versioned and hash-bound. Selection-only JSON is strict, bounded, retry-evidenced and replayed against model/source/reference identity. Old v10–v13 readers remain separate.
- Deterministic verification recomputes routing and validates the resource cycle and security contract. Printed standard and large-print PDFs are checked for all evidence, answers and indicative credit.
- The first new live run is a one-paper diagnostic with pinned identities. Every page is compared manually with the official reference; only after a source freeze may the expensive cross-route matrix begin. Teacher review, learner calibration and accessibility remain external gates.
