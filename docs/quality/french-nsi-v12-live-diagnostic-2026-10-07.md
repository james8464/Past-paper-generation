# French NSI first live diagnostic — 7 October 2026

**Result: failed before publication.** No subject, correction or accepted
manifest was produced. This is not a validated paper or evidence of a
successful model run.

| Identity | Pinned value |
|---|---|
| Route | Terminale NSI written practice, seed `270100` |
| Source | `f6de5ca8c94e3ce464ee9a55220ee9611ee1e96202a5f93bfd2e9c7c6e11685e` |
| Model | `gemma4:12b`, digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` |
| Reference index | `ec2339e6dffeba485f94d33d8e6f868e24cd2c40ad32830621201496ca32d594` |
| Result | `failed`, return code `1`, 71.789 seconds, three repair attempts |
| Local evidence | `tmp/pdfs/french-v12-live-20261007/runs/gemma4-12b/4eb23ef187e2/270100/` |

The model returned `scene_id=collecte` and `slots.activity=demandes` on all
three attempts. Both strings belong to the respective schema enums, but the
v2 catalogue only defined `collecte/collectes`. The validator consequently
reported `Situation ou emplacement inconnu`; the retry prompt did not resolve
the contradictory contract. All rejected raw responses and attempt records
remain in the local evidence directory. No success is inferred from fixture
PDFs or from a partially generated question.

The v3 repair makes every pair independently advertised by those enums a
finite, renderable catalogue entry, and a regression test enumerates the full
cross-product. A fresh run must use a **new** output directory and pin its own
source identity. Do not overwrite or relabel this failure. Human NSI teacher
review, learner calibration and accessibility remain outside this diagnostic.
