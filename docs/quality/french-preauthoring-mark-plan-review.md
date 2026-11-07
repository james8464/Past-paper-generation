# French pre-authoring mark-plan review

This backend-only opt-in adds `fr-nsi-v36-planned-content-v1`, with separate
`fr-nsi-product-mark-plan-v1` and `fr-nsi-content-assembly-v1` policies. The public
runtime, native UI and default authoring policy are unchanged. No public rollout
or PDF qualification of the new route is claimed.

## Ownership and compatibility

Before the first author request, the application binds the actual three plans
and their canonical hash to the generation identity. A base seed and exercise ID
select one of three product-owned numerical topologies: `[1,1,2,2]`,
`[0.5,1,1,1.5,2]`, or `[0.5,0.5,1,1,1.5,1.5]`. These are not official tariffs,
question/answer catalogues, prescribed operation sequences, or quality proof.
Each immutable Decimal plan totals six points, with one or two positive credits
per question. Three independent exercises retain 18 technical points and the
separate two indicative language points; there is no 36-question or page target.

The model still authors the French context, source data, questions, answers and
criterion text. The strict content-only response rejects allocation fields and
exercise `minutes`/`target_points`; it does not strip, coerce or rescale them.
Question timing/difficulty metadata and quantitative source/graph data remain
allowed. Canonical assembly inserts only the validated plan's IDs and amounts,
then runs the existing semantic, source-binding, safety and layout checks.

One shared question definition avoids repeating the verification schema for
every slot. JSON Schema enforces exact question keys and permits only the plan's
criterion IDs, with one or two entries. The host separately enforces the exact
criterion set belonging to each question before assembly. Object key order is
irrelevant; canonical order follows the plan. Frozen model instances are
revalidated, including before schema construction.

Structural retries and whole-exercise redrafts retain the same base-derived
plan. A dedicated contract error permits only structural ID/set failures to
take the existing structural retry; unrelated semantic errors remain refusals.
Raw responses remain untouched and separately hashed from assembled exercises.
Accepted-package and terminal-refusal replay reconstruct requests and assembly
from the recorded plan. When a recovery recorder is supplied, the initial plan
is saved before dispatch; a failed initial save prevents any model call. Without
a recorder the identity is still bound in memory before dispatch.

The three historical V36 request schema/prompt fingerprints remain exact.
V13–V35 paths, strict implementation identity and old refusal history remain
unchanged. The retained `qwen-positive-contract261` failures are not repaired,
accepted or relabelled by this policy. No old invalid numeric draft is converted
into a content-only response.

## Evidence and review scope

Genuine RED controls preceded integration: the opt-in generation argument was
absent, and assembly/schema construction initially failed to reject a mismatched
exercise ID or forged frozen plan. The final 13-module focused group passed
494 offline/fake-client tests in 16.75 seconds, including existing regressions;
these are not 494 newly added tests. Controls cover all three topologies,
normal/enlarged replay, exact legacy fingerprints, retained raw refusals,
terminal refusal after prior acceptance, initial disk recording, storage failure,
cancellation, quota enforcement, source mismatches and identity/content tampering.
Ruff and diff checks passed. Scoped mypy passed for the two new modules, not the
whole pipeline. No live model, provider-grammar, content-quality, new-route PDF,
teacher, learner or empirical-timing qualification was performed.

The author read the new 165-line plan module, 128-line content module and
632-line test file completely through EOF. Pipeline attribution retains the
earlier [complete source-bound review](french-pipeline-source-bound-review.md)
and subsequent [composite policy review](french-graph-schema-review.md), plus
the complete present delta and scoped request/author/recovery/replay callers.
This is not a fresh whole-file read of the current 2,369-line pipeline or a
whole-project audit. Independent review is recorded separately.

| File | Lines | SHA-256 |
| --- | ---: | --- |
| `Backend/Core/france/mark_plan.py` | 165 | `d97f6540a40f42cec1eabf344dcd21321a0dac6daadd47998e22b15c320727e5` |
| `Backend/Core/france/content_authoring.py` | 128 | `cc433e24d56113f334d4b6ca0be9fea6dc9221cc70c172148262f1dbb21d59b6` |
| `Backend/Core/france/llm_pipeline.py` | 2369 | `36ffff5557941b645191749e437afe5bdd66eb16dc03f68261817a94bf58dd34` |
| `tests/test_french_preauthoring_marks.py` | 632 | `692d15c658ad099ada433addab6cd608b51845d04ff8f1208898c7c5e5cd9543` |

The ignored local implementation receipt and focused log retain exact command,
hashes and limits. No full suite, release build, public/default activation or
model spend was performed for this implementation. Removing model-owned budget
selection does not establish that a model can author a correct French paper.
