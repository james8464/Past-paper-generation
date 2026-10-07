# French NSI live paper fidelity diagnostic — 7 October 2026

**Automated generation passed; product fidelity remains on hold.** The first live
paper from the app-owned three-exercise source is internally consistent and
visibly legible, but it is substantially shorter and less developed than the
official 2026 Métropole written paper. It is an unreviewed training draft, not a
validated examination product or an Occitanie submission proof of learning impact.

| Identity | Recorded value |
|---|---|
| Route and seed | `fr-bac-general-nsi-written-2027`, `270100` |
| Merged source | protected PR #36, `6ee8d5d2d4f8493d5112627e0a4016ccaf8b57de`; implementation SHA-256 `36b3edf8558173a949d710d0962cd71c884bdde3e276bed885bec1ff6c1961b8` |
| Model | local `gemma4:12b`, digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` |
| Reference index | SHA-256 `ec2339e6dffeba485f94d33d8e6f868e24cd2c40ad32830621201496ca32d594` |
| Result | `passed`, first attempt, no repair; 420.412 seconds; backend peak RSS 136,003,584 bytes, excluding Ollama |
| Subject | 6 A4 pages, SHA-256 `c2c70dc2563ed04e7e4fb6ebfd6d94ffff39ad20e56b3b8e1609b54d47027bea` |
| Proposed correction | 10 A4 pages, SHA-256 `1bbd21199d9772e13b297e423f0ad9904a6494efd0fedb9a727900ece8e32c83` |
| Local evidence | `tmp/pdfs/french-v15-network-20261007/runs/gemma4-12b/4eb23ef187e2/270100/result.json` and the hash-bound artifact folder named in that result |

The [official 2026 Métropole day-one paper](https://eduscol.education.gouv.fr/sites/default/files/document/26-nsij1me1-128190.pdf)
(SHA-256 `275b050d7577142794bb579b66ffc08fe7742a70c943a632eebd32701994310b`)
is the local primary comparison. All 16 generated pages (six subject and ten
correction) were rendered and visually inspected; the official comparison pages
14–15 were rendered as well. This is a comparison with a real paper, not an
assertion that the 2027 product must copy its exact page count or point split.

| Measure | Official 2026 paper | Generated training subject |
|---|---:|---:|
| A4 pages | 16 | 6 |
| Independent exercises | 3 | 3 |
| Numbered questions | 10 + 11 + 15 = 36 | 6 + 6 + 6 = 18 |
| Pages occupied by exercises | 2–5, 6–10, 11–16 | 2–3, 4–5, 6 |
| Illustrative database development | relational schema, sample tables and a linked SQL sequence across pages 14–16 | three small data tables and six questions across pages 4–5 |

The generated subject prints the route costs, process state, SQL rows and code
needed for its answers. The shortest-route additions, deadlock remedy and
confidentiality-versus-sender-authentication limit agree with those premises.
The subject and correction have no obvious clipped text, broken table or empty
trailing page. This is a limited manual internal-consistency finding, not a
teacher's judgement of fairness, difficulty or mark reliability.

The most important remaining gap is task depth relative to 210 minutes. The
official paper develops longer multi-step situations; this draft's third
exercise fits on one page, and its 5.5 indicative technical points are spread
over six short prompts. The second exercise also leaves much of its second
page blank. A teacher time trial and calibrated marking are needed before
claiming that the three exercises sustain the stated duration. Visually, the
weighted graph's crossing edges and labels should be made clearer. The proposed
correction's cover still repeats candidate-facing subject instructions; that
copy should be corrected.

**Decision:** preserve this live run as a passed engineering checkpoint with a
manual fidelity hold. Extend the original, app-owned exercises into fuller
reasoning sequences without changing the three-exercise structure, 18 + 2
credit policy, French-only references, or non-official status. Re-run pinned
live generation and compare every PDF page again before the final UK/French
matrix. Human NSI teacher review, learner calibration, rights clearance and
accessibility evaluation remain separate external gates. The practical
component is not supported. Issues #4 and #8 remain open.
