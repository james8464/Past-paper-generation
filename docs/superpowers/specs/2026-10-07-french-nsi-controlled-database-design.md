# Controlled database and debugging exercise for French NSI

Status: implementation design, 7 October 2026. This extends the approved
French written-practice route; it does not qualify a paper or alter the
practical component. The 7 October pinned live diagnostic accepted the first
exercise but rejected all three model-authored database attempts. Recorded
lexical false positives coexist with independently visible content defects.

## Decision

Exercise 2 will use an original, seeded application-owned contract for its
relational data, SQL operations and Python debugging case. A finite French
catalogue owns the printed context, six prompts, answers and indicative
criteria. The local model may choose only documented wording IDs in one compact
JSON response; it cannot supply a fact, SQL identifier, code fragment, answer,
credit or sentence that reaches the PDF. Unknown, inconsistent or extra fields
fail closed, with the exact raw response and reason retained. There is no
fallback to UK references, a remote model or an unreviewed free-text draft.

This deliberately favors verifiable variation over unrestricted prose. A
prompt-only repair cannot establish the consistency of arbitrary SQL, code and
marking; switching models would change the failure distribution, not the
assurance boundary. The contract and catalogue can vary original data and
surface forms, but they do not imply unlimited novelty or teacher approval.

## Exercise and factual contract

The route keeps three independent 70-minute written exercises and its existing
seeded technical allocation of 6 points for Exercise 1, 6.5 points for Exercise 2
and 5.5 points for Exercise 3, plus a separate two-point
indicative French-language component. Exercise 2 retains six blueprint IDs
`2a`–`2f`, parts A/B/C and the mapped official 2019 curriculum capabilities.
Its scenario is independent of the graph/tree and network exercises.

The `DatabaseContract` is canonical JSON with version, seed, exercise ID,
task IDs, three small related tables, key/foreign-key declarations, one
deliberately faulty SELECT/JOIN, one bounded UPDATE, one deliberately faulty
Python counting function, a concrete test case and recomputed expected
results. The original maintenance scenario uses `agent(id_agent, nom, secteur)`,
`categorie(id_cat, libelle)` and
`incident(id_incident, id_agent, id_cat, statut)`, with three agents, three
categories and four incidents; one agent owns at least two incidents. The
faulty JOIN compares `incident.id_agent` with `categorie.id_cat` instead of
`incident.id_cat`, with seed data chosen so the error changes the result. The
shown Python function counts `ouvert` rows when asked for `clos` rows, with
unequal counts so a supplied assertion exposes the defect. `from_dict`
rejects unknown keys, duplicate primary keys, broken
foreign keys, unsupported SQL names, nonrectangular materials and inconsistent
expected results. The seed varies neutral names and row values within those
invariants. No official annale text or holdout content is incorporated into
the generator.

Part A asks for a concrete anomaly and a joined-data interpretation; B asks
for a correction to the shown faulty query and a bounded mutation; C asks for
a test revealing the shown Python defect and a justified correction using the
same data. Every answer is computable or defined by the contract; the supplied
code and table rows are visible to the learner. The contract never executes
model-authored Python or SQL. It may use an in-memory, restricted SQLite
calculation as an independent check, but publication requires deterministic
agreement with the contract and exact decimal credit. A human still judges
whether the exercise is pedagogically sound and the indicative rubric fair.

## Selection and publication boundary

One French JSON selection request includes only exercise ID, supported scene
and wording IDs, task IDs and the small contract-owned facts needed to choose a
presentation. The schema and direct validator describe the same finite set of
valid combinations. The renderer uses only catalogue text and contract values;
no unbounded response field is copied to a candidate. A failed model call or
invalid selection leaves a hashed attempt record and no published paper.

A new generation/prompt version binds the contract hash, catalogue version and
digest, source implementation, model digest, scoped reference index and
selection response to the checkpoint and package. Replay re-renders the
exercise and compares every structured field and exact credit, not just a
top-level hash. Older French v10–v12 packages and UK route IDs remain on their
historical readers without silent migration. A version or digest mismatch
stops resume and publication.

Standard and large-print PDFs must display the exact tables, key notes, faulty
SQL/code, six prompts and credits. The subject must not leak the answer or
rubric. The correction must show the contract-derived answers and distinct
indicative credit. Extraction checks bind printed rows, code, instructions,
answers and credit; every generated page is then inspected visually against
relevant official papers for hierarchy, legibility and page flow. Official
2026 papers inform visual comparison only, not 2027 claims or generator data.

## Verification and release gate

Tests cover multiple seeds; uniqueness and foreign-key failures; SQL JOIN and
UPDATE results; the Python defect, revealing test and correction; every
schema-advertised selection; injection and free-text rejection; exact points;
checkpoint tampering and replay; v10–v12/UK compatibility; and standard/large
PDF mutations. A focused live diagnostic must be pinned to a new source/model/
reference identity and preserve failures. Exercise 3 remains unqualified until
its own controlled network/process/security design is implemented and checked.
The final shared-source matrix waits until both French exercises and their PDF
gates are stable. Teacher review, learner calibration, accessibility assessment,
source rights and applicant details remain external gates.
