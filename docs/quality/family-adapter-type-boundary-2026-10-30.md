# Family adapter type boundary

P5 now has a checked generic boundary for a family's syllabus, paper rule,
assessment and optional rendering context. `family_contracts.py` owns the frozen
adapter/build-result declarations. All four types flow through loading,
construction, validation, improvement, difficulty review, rendering, naming and
supporting-artifact hooks. `checkpoint_identity` returns `object` rather than
claiming that every historical identity payload has one JSON shape.

`family_adapter.py` re-exports the existing names, so the seven family CLI imports
remain unchanged. The shared minimal JSON client and concrete checkpoint class
are retained. No new client/checkpoint protocol framework or return casts were
added. The runner still accepts both an assessment returned directly and a
`BuildResult` with an optional context. Its execution order, checkpoint and
package serialization, renderer transactions, validation and errors are unchanged.

The scoped mypy gate includes the new contract module, alongside the existing
JSON-client and two infrastructure leaves. Positive fixtures check wrapped and
direct assessment construction. Negative fixtures require a specific argument
type error for a mismatched syllabus loader, rule loader, assessment result,
render-context input and wrapped-context result. They would not be satisfied by
a missing module, unsupported generic syntax or unrelated checker failure.
Runtime tests check legacy re-export identity, frozen build results and unchanged
dictionary serialization with absent or populated contexts.

The checkpoint module has one explicit `follow_imports = skip` rule in this
gate. It prevents pulling the legacy Pydantic assessment graph into a scoped
adapter-contract check; it is not an assertion that checkpoint implementations
are statically safe. The four family parameters remain concrete and checked.
The runner body, legacy generator implementations and all model/provider modules
are not declared fully type-checked. This completes the minimal adapter-boundary
step, not a repository-wide generic or static-type conversion.

Verification used the already installed mypy 2.4.1 and primary project Python.
The four configured source files passed strict checking. The existing client,
adapter/registry/migration, parallel scheduling and shared numeric-integrity
regressions passed together; the new static mismatch fixtures passed. No
inference, model download, application build or user-data operation was performed.
This change makes no generation-speed or paper-quality claim. Historical review
records and source implementations remain retained.
