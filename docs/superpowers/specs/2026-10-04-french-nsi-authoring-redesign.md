# French NSI authoring redesign

Status: implementation design, 4 October 2026. This is not evidence that a
paper has passed live generation or teacher review.

## Purpose and evidence

The 2027 Terminale NSI written-practice route must create original, coherent
French exercises that a teacher can inspect and, eventually, recommend for
classroom practice. The current three-exercise, 210-minute, 18-technical-point
plus separate two-point language framework remains unchanged. It is not an
official examination paper or an official marking grid.

The first Gemma 4 12B campaign accepted 0/10 papers. Source-pinned one-paper
diagnostics using prompt versions v5 and v6 each accepted 0/1 at seed 270100.
The v6 checkpoint retained three failed drafts: two did not match the detailed
question blueprint and one named a graph while leaving its structured link
empty. The v6 implementation identity is
`cba1b74b98c236608d983242778de8db6c3e891142e4ea635ebb0c7fd776c69d`.
None produced a qualified PDF.

The existing blueprint rotates curriculum codes through six slots without
regard to the exercise's narrative. At seed 270100 it asks for an algorithmic
graph operation, then a binary-tree algorithm, then graph representation,
within one weighted-graph scenario. The model often writes a coherent graph
exercise instead, so the validator rightly rejects it. The real 2026
Métropole day-one paper provides a better structural pattern: each exercise
uses one context and organised parts while spanning related concepts (for
example, network configuration, routing and communication security). That
historical paper is a reference, not a complete 2027 scoring or layout rule.

Official historical source:
https://www.education.gouv.fr/sites/default/files/document/baccalaureat-general-2026-numerique-et-sciences-informatiques-517601.pdf

## Design decision

Do not loosen the blueprint, copy official questions, or silently overwrite a
model's curriculum labels. Instead:

1. Replace cyclic objective assignment with versioned exercise archetypes.
   Each archetype has a coherent scenario brief, two or three topical parts,
   and six question intents ordered from interpretation to application and
   reasoning. The seed may vary contexts and point/time profiles, but not
   scramble the pedagogical sequence. A full paper samples distinct programme
   areas; no single paper claims exhaustive programme coverage.
2. Separate immutable plan metadata from AI-authored question content. Keep
   raw outputs and hashes. Plan fields (ID, technical credit, timing, operation,
   intended difficulty and required programme code) are attached by the
   application, never trusted merely because the model echoed them.
3. Require a question-level, independently produced alignment decision for
   each required programme capability, with a short evidence rationale. A
   rejected or unresolved item cannot be repaired by changing its label.
   Deterministic contracts continue to decide SQL, graph, binary and trace
   cases where supported; unsupported claims remain unresolved.
4. Repair only a failed question or part against the unchanged scenario and
   materials. Re-run every affected deterministic, originality, blind-solver
   and review check before acceptance. A bounded attempt count and complete
   failed-attempt ledger prevent silent infinite retries.
5. Link a question to a material when its prompt contains that material's
   exact unique ID and its supplied `material_ids` list is empty. Record the
   inference in the candidate evidence. Generic phrases such as “the graph”
   are not enough; conflicting or unknown IDs fail. This preserves v5 package
   reading and v6 evidence, rather than rewriting old artifacts.

The alternative of making the JSON schema more elaborate was rejected as the
primary fix: the local model already receives the plan and can still choose
the wrong content. Broadly weakening the curriculum gate was rejected because
it would turn incorrect papers into false passes. Generating every question in
an independent model call is reserved as a fallback if part-level repair
cannot reach acceptable first-pass quality; it would greatly increase local
latency.

## Interfaces and invariants

- `ExerciseArchetype` is a versioned, internal plan record with ordered
  `QuestionIntent`s. Each intent names one required official programme code,
  a content goal and an expected response form. Its text is guidance, not a
  reference question to copy.
- `PlannedQuestion` carries immutable identity, exact decimal credit, time,
  operation and intended difficulty. `AuthoredQuestion` carries original
  French wording, answer, marking steps, material references and a supported
  verification contract. The assembled `NSIQuestion` remains the package
  format, with separate raw/assembly provenance.
- A paper still has three independent exercises and exactly 18 technical
  points. The two language points remain separate and indicative. The
  practical component is out of scope.
- Retrieval remains French-only, curriculum-compatible, rights-filtered and
  holdout-free. No UK fallback, cloud fallback or generated code execution.
- Existing UK routes and recorded French v4/v5/v6 packages remain readable
  under their pinned identities. A new authoring version is required for any
  source-changing live qualification attempt.
- A teacher's review applies to exact artifact hashes only. Automated
  acceptance is not examiner, teacher or learner approval.

## Qualification

Test the archetype sequence and exact scoring for a seed range, including
coverage variation without incoherent objective rotation. Red-green tests
must reject a semantically mismatched question even if its metadata carries
the expected code, and reject a missing or ambiguous figure. Test targeted
repair, cancellation and resume identity without publishing partial work.
Run backend and macOS release checks, then a new pinned one-paper diagnostic
before expanding to 30 exercises and ten complete papers. Preserve failures.
Manually compare every page of accepted PDFs with the relevant official
references. Two independent French NSI teachers and a later supervised learner
pilot remain external gates.
