# Verifiable French NSI exercise authoring

Status: design, 5 October 2026. This does not qualify a paper or claim teacher approval.

## Purpose and trigger

The 2027 Terminale NSI written-practice route should produce original French
questions and indicative marking that teachers can inspect without first
repairing invented data, impossible premises or undefined programming APIs.
The three independent exercises, 210 minutes, 18 technical points and separate
indicative two-point French-language component remain unchanged. The practical
component remains out of scope.

Source-pinned Gemma 4 12B and Qwen 3.5 9B diagnostics at seed 270100 both
produced zero complete papers after successive prompt, schema, alignment and
semantic-guard changes. The latest Gemma run used `Noeud(...)` in three tree
solutions without defining it in the subject; manual reading also found false
graph-algorithm explanations. The current authoring protocol asks the model to
invent data, question semantics, code, solutions and credit in one response.
Validators can reject mistakes but cannot make that response reliable. Further
single-phrase prompt fixes are not an adequate release strategy.

## Approaches considered

1. **More prompt and regex checks.** Smallest change, but the preserved runs
   show one rejected defect is replaced by another; checks cannot prove an
   arbitrary natural-language claim true. Reject as the primary approach.
2. **Seeded, executable task contracts with model-authored presentation.** The
   application owns small datasets, APIs, operations and expected results; the
   model authors an original context, French question wording, explanations and
   indicative marking within those boundaries. Choose this approach.
3. **Fixed question bank with variable names.** Predictable and verifiable but
   too repetitive to meet the project's original-question goal. Use only as a
   development fixture, never as a silent fallback paper.

## First vertical slice: graph and tree

Introduce an immutable, versioned `GraphTreeContract` for the existing
`graph-and-tree` archetype. A seed chooses a small connected weighted graph,
an independent binary-search tree with distinct keys, a declared node API and
the exact operations required by the six-question plan. The graph is printed
as `reseau` and the tree as an `arbre` table with `cle`, `gauche`, `droite`
columns; `—` denotes no child. The paper prints the `Noeud` constructor and
its `valeur`, `gauche`, `droite` attributes before asking for code that uses
them. The contract derives canonical graph routes/traces and tree operations
with trusted bounded code. It owns the values and facts, not the prose.

The six contract task IDs map to the existing ordered slots: shortest path,
adjacency/weight interpretation, a controlled BFS debugging case with a real
defect, alphabetically ordered BFS trace, bounded BST insertion/search, and
inorder/cost reasoning with its assumptions stated. The seed varies data and
scenario, not the skill sequence. Explicit tie-breaking makes each expected
result reproducible; an ambiguous graph is rejected before authoring.

Author in coherent parts rather than asking for an unconstrained whole
exercise. The model may vary scenario, wording, distractors, explanation and
marking detail, but may not create vertices, weights, tree nodes, API names or
algorithm results outside the contract. Originality screening still compares
the final question text with eligible references and prior generations. A
model refusal or unsupported draft is a recorded failure; do not replace it
with a preview or canned paper.

Bind every authored question to one contract task ID and the unchanged
question blueprint. The raw authoring question includes `contract_task_id`
and a structured `claimed_result`. Those fields remain in evidence but do not
enter the old `NSIQuestion` package schema. Contract-owned source materials,
expected result and verification kind are assembled separately from the raw
model response. Reject a structured claim that differs from the canonical
result. For this first slice, provide the canonical answer sentence in the
part request and require the model to copy it exactly; reject a divergent
answer instead of silently replacing it. Require at least one marking
criterion to cite that checked sentence. Free-form explanatory steps remain
out of the automatically accepted answer, pending a way to verify them; the
criterion is still indicative and requires teacher review. This avoids
treating a correct JSON claim as proof that every free-text sentence is true.
Reject text that contradicts those materials or requires undeclared data.
Do not silently rewrite the model's question or marking: a bounded, logged
repair call may revise one question; all structural, mathematical, originality,
independent-solver and review checks rerun on the revised exercise. Preserve
the initial candidate, every repair, all failures and exact hashes.

For the first slice, require deterministic checks for shortest-path and
ordered graph-traversal questions, and for at least one tree operation. A
deliberate debugging task includes an application-owned, printed faulty BFS
program and a bounded graph test case. Its diagnosed defect and corrected
behavior are established by running only the exact trusted snippets, never
model-generated code. Unsupported
natural-language reasoning remains explicitly unresolved, not automatically
correct. No generated Python is executed outside the existing restricted
interpreter; generated SQL remains isolated and bounded.

## Boundaries and compatibility

Keep the existing French assessment and package schema readable; write a new
prompt/contract version and include the contract digest in checkpoint and
artifact identity. A package recheck must reconstruct the contract and verify
every bound material, question task and expected result. Old checkpoints and
failed runs are never upgraded. UK routes, saved selections, AO policies and
package readers remain untouched. French retrieval stays curriculum-scoped,
rights-filtered and holdout-free, with no UK or cloud fallback.

The question paper and proposed correction retain independent, clearly
non-official branding. This design concerns content integrity, not a claim of
2027 official visual identity. PDF layout and teacher review remain separate
release gates. No live complete-paper matrix starts while shared source changes.

## Qualification for this slice

Regression fixtures replay the three latest Gemma failures and representative
false BFS/DFS claims. Tests prove seeded contracts are reproducible, coherent
and checkable; a candidate cannot change graph/tree data, use undefined APIs,
claim an incorrect result or pass by changing metadata. A positive fixture
must render and revalidate. Cancellation, resume and tampered contract digests
must fail closed without partial publication.

After protected integration, run one new source/model/index-pinned live paper
as a diagnostic. Manually inspect every accepted exercise, solution, credit and
PDF page against official historical references and the 2027 rules. Expand to
the database and networking archetypes only after the first slice's evidence
shows the contract boundary works. Even complete automated acceptance remains
an unreviewed draft until independent French NSI teachers and later learners
assess it; do not describe it as a validated classroom product beforehand.
