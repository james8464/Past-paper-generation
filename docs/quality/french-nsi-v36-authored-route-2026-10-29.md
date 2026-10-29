# V36 model-authored route

## Scope

This new route responds to the explicit requirement for genuinely model-authored
French papers. It does not select, vary or reword the finite V13-V35 families.
Those historical modules and their package readers are unchanged. The new
`llm_pipeline.generate` API is separate from runtime dispatch until integration.
No live-model, installed-app or printed-page acceptance is established here.

The author receives the Terminale capability descriptions and eligible local
French programme and official-paper reference excerpts. It supplies the context,
data, structured materials, tasks, proposed answers and individual credit criteria.
There is no source-owned question or answer bank in this route. Each of three
autonomous exercises has six technical points and 70 indicative minutes. The
separate two-point language rubric remains numerically indicative. At least
three broad curriculum domains must be covered; difficulty and time remain
uncalibrated.

## Admission and evidence

Requests use the shared typed provider interface with an explicit
`french_nsi_authoring` operation and JSON schemas. Normal production generation
requires both reference categories from the French scope and reference split.
Missing eligible material refuses before any model request. The isolated
`exercise_request` capability probe may use an empty reference list; that is not
a qualified full-paper route.

Existing exercise validators check exact credits, question identifiers,
curriculum codes, material links, timings and declared cognitive progression.
Model Python fragments are parsed, not executed; imports, dynamic execution,
filesystem/system/network access and introspective names are refused. The
existing bounded interpreter, in-memory SQL checker and shortest-path calculator
may check generic model-supplied verification contracts. Such consistency is
not proof that the printed task, answer and contract describe the same problem.
Unsupported or theoretical questions are recorded as `not_checked`, not passed.
Fixed-family verification contracts are not accepted.

A separate blind-solving request receives no proposed answers, marking criteria
or verification contracts. A further full review compares the task, answer,
rubric, blind solution and references, question by question. Missing fields,
negative flags or reported issues refuse the draft. Reusing the same model for
these requests does not provide an independent expert or mathematical proof.
Capability probes and human inspection must retain that limitation.

Packages bind provider, model, seed, source implementation, assessment definition,
print policy, reference evidence and complete content. Reviews are bound to their
exercise hashes. Replay validates the strict reviews, recalculates supported
contracts and requires the exact warnings, language rubric and credit totals.
The package states `model_used=true`, `generation_origin=model_authored` and
`status=unreviewed_draft`; teacher review and empirical calibration stay
`not_run`. Runtime integration must use the V36 notice policy rather than an old
teacher-approval notice and must not silently fall back to a finite family.

## Mocked verification

Tests show different model responses produce different substantive papers, exact
marks and curriculum constraints refuse malformed output, negative model reviews
stop generation, and empty or holdout-only references cannot trigger fallback.
Two focused red/green checks exposed and repaired missing restored-review
validation and an unsafe system-call fragment without an import. All three JSON
schemas compile with the installed llguidance decoder without loading a model.
These checks establish engineering behaviour, not model capability or exam
equivalence. Source and output identity remain distinct from educational quality.

## Integration boundary

The existing Ollama typed transport honours each requested token budget. The
current Apple typed path still has a separate 4,096-token ceiling; propagating
bounded request budgets is a provider task, not part of this module. A truncated
exercise must remain a failure, not be converted into a fixed-catalogue paper or
treated as evidence that another model has passed.
