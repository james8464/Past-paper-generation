# French NSI controlled-database live diagnostic — 7 October 2026

**Automated run: passed. Product/content review: failed. Not a validated paper or submission-ready product.** This is the first identity-pinned live run to publish a complete three-exercise subject and proposed correction after the app-owned graph/tree and database contracts. It used one installed local model and one seed, so it does not replace the final shared-source matrix.

| Identity | Recorded value |
|---|---|
| Route and seed | `fr-bac-general-nsi-written-2027`, `270100` |
| Source | commit `722d2f16b1395be2c8558011077987a2cf56d4cc`; implementation SHA-256 `6e66af0be6ac3b3329363e3d5f7cf4130a3df738c59f3481c50e349a6b77e1ba` |
| Model | `gemma4:12b`, digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` |
| Reference index | SHA-256 `ec2339e6dffeba485f94d33d8e6f868e24cd2c40ad32830621201496ca32d594` |
| Automated result | `passed`, return code `0`, 850.849 recorded seconds, zero rejected authoring attempts |
| Subject | 7 pages, SHA-256 `4d06632f0a29f74ccde57594e4f77280b0e46a721686c50df4866ad38abd44ea` |
| Proposed correction | 11 pages, SHA-256 `8e357033887dd0c09c737dbee7e4825edd87f778393dc203c4814c4ea5438f7e` |
| Local run evidence | `tmp/pdfs/french-v14-controlled-20261007/runs/gemma4-12b/4eb23ef187e2/270100/result.json` |
| Local bundle | `tmp/pdfs/french-v14-controlled-20261007/artifacts/gemma4-12b/4eb23ef187e2/nsi-2027-270100-cc926e9ebfa6/` |

Both PDFs were rendered and inspected page by page against the local official 2026 Métropole NSI paper's page geometry, table treatment, code presentation and question hierarchy (in particular its pages 14–15). The non-official cover and separate indicative French-language component are present. The app-owned first exercise has a coherent graph/tree and matching answer; the second has explicit relational data, SQL and Python code, and answers tied to the printed rows. The second exercise's chosen *service* scene nevertheless retained an *atelier* table caption; that is corrected in the next source checkpoint. A large-print fixture also exposed a correction rubric row beginning on the next page; it is a layout polish gap, not evidence of lost credit.

The model-authored **Exercise 3 is not acceptable** despite passing structural checks:

- Its routing table provides destination, next hop and cost, but no complete edge/link costs for the requested route through `R1` and `R3`. The proposed solution adds `10 + 5 = 15` using unrelated destination entries. The route and its total cost are not derivable from the printed facts.
- The changed-link-cost question has no defined alternative routes or costs, so its claimed optimal-route change cannot be checked against the subject.
- The resource-order question asks Process B to follow alphabetical order; the supplied answer merely repeats B's existing `Buffer_A` then `Buffer_B` order and does not repair the actual B–C wait cycle.
- The asymmetric-encryption question calls that method *indispensable* although the scenario does not exclude an authenticated pre-shared key. Its proposed answer treats an unstated premise as fact.
- The last Exercise 3 question spills just two lines onto an almost empty seventh subject page. The correction's final page contains only one answer and rubric; both are visibly weaker than the official reference's deliberate pagination.

The manifest is explicitly `unreviewed_draft`: teacher review, learner calibration, accessibility evaluation, rights clearance and Apple/platform approval are **not_run** or unverified. This diagnostic is preserved as failure evidence, not promoted as qualification. Replace Exercise 3's model-authored facts/answers with a bounded, original, app-owned network/process/key-exchange contract before a new pinned live run. Do not launch the expensive shared UK/French matrix until that source freezes; do not close issues #4 or #8.
