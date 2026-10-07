# French NSI second live diagnostic, 7 October 2026

**No complete paper was accepted.** The repaired finite-authoring path accepted
Exercise 1, but the model-authored database exercise failed all three attempts.
No subject, correction or publication manifest was produced. This result must
not be presented as a validated product or as an inspected PDF.

| Identity | Pinned value |
|---|---|
| Written route and seed | `fr-bac-general-nsi-written-2027`, `270100` |
| Implementation SHA-256 | `9b85a10fa0155747f090ad366fa0ff55b14936e8f0cfa89bb07af6f6b90bd145` |
| Model and digest | `gemma4:12b`, `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` |
| Reference index SHA-256 | `ec2339e6dffeba485f94d33d8e6f868e24cd2c40ad32830621201496ca32d594` |
| Run result | `failed`, return code `1`, 1,368.227 recorded seconds, three Exercise 2 authoring attempts |
| Local run record | `tmp/pdfs/french-v13-live-20261007/runs/gemma4-12b/4eb23ef187e2/270100/result.json` |
| Accepted and rejected checkpoints | `tmp/pdfs/french-v13-live-20261007/artifacts/gemma4-12b/4eb23ef187e2/.papercreator-checkpoints/` |

The checkpoint retains the accepted first exercise under key `1` and all three
rejected second-exercise candidates. Attempt 1 failed because the SQL-name
detector read the French marking phrase “UPDATE avec un filtre” as a SQL
statement naming a relation `avec`. This is a demonstrable lexical false
positive, not evidence that the candidate would otherwise pass: its raw
questions and code still require independent content review. Attempts 2 and 3
failed because question text cited structured relation identifiers that did
not match the question's `material_ids`; some supplied data or code also
contradicted its own context. The validator correctly kept those candidates
out of the paper. Do not loosen the figure/data binding gate to pass them.

The next design decision is how to constrain Exercises 2 and 3 to original,
verifiable data and French wording while preserving three independent tasks.
A targeted SQL-phrase parser repair alone cannot qualify the model-authored
exercise. The final shared UK/French matrix stays on hold; teacher review,
learner calibration, accessibility and rights review remain separate gates.
