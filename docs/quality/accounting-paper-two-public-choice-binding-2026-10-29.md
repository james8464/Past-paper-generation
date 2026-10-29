# Public arithmetic for Accounting Paper 2 choices

## Demonstrated gap and bounded fix

A retained live model attempt changed the contribution question's options to £30/£40/£50/£55 even though its own working obtained £45 minus £10 = £35. Later validity checks refused this, but repeated model repair is unnecessary for public arithmetic that the seeded source already owns.

Paper 2 questions 04 (closing cash balance) and 05 (contribution per unit) now carry explicit Accounting selected-response contracts. The existing seeded builder supplies the public inputs. Decimal arithmetic derives the answer without reading a private key or asking a model whether a single choice is valid. The existing source-owned route preserves these verified stems, options, order, keys and marking. Conceptual choices are not implicitly locked or reclassified.

The cash calculation adds opening balance and receipts, then subtracts payments. It permits a negative closing balance. Unit contribution subtracts variable cost from selling price; the explicitly supplied allocated fixed cost is not deducted. All public inputs must follow the existing finite, nonnegative decimal-input contract and whole-pound option policy. Missing or extra input names, wrong units, unsupported operations and missing derived answer options still fail closed.

## Primary-source check

AQA's [Marginal costing specification](https://www.aqa.org.uk/subjects/accounting/a-level/accounting-7127/specification/subject-content/marginal-costing) includes contribution per unit and distinguishes variable and fixed costs. Its [official 2021 Paper 2 marking scheme](https://filestore.aqa.org.uk/sample-papers-and-mark-schemes/2021/november/AQA-71272-MS-NOV21.PDF), question 15, calculates contribution after variable costs and deducts fixed costs afterwards to obtain profit. The [Budgeting specification](https://www.aqa.org.uk/subjects/accounting/a-level/accounting-7127/specification/subject-content/budgeting) includes cash-budget preparation and analysis. These sources support the limited arithmetic policy; they do not approve the generated questions or establish difficulty equivalence.

## Verification and compatibility

Red tests reproduced absence of public contracts, mutable numeric questions and inability to resolve the new operations. The baseline projection of every Paper 2 question over 102 seeds (0 through 99, 270100 and 270101) has SHA-256 `f42616ec0240caf5c7d72c92d4f545e21acca9ab0f8fe771dd257e5695f1aadb`, captured before this fix. After the fix, it matches exactly when excluding only authoring context. Thus all seeded stems, choices, option order, keys, schemes and downstream question/RNG results remain unchanged.

Tests independently compute the two answers from Decimal public inputs across 20 seeds. They prove model edits and false raw model flags cannot override source-owned truth, private wrong keys do not change the derived answer and still fail reconciliation, and restored checkpoints reject mutated source-owned choices/keys. No model is loaded for these checks.

The existing `accounting-selected-response-v1` payloads retain their previous meanings; the supported operation set gains two explicit new values. Existing four-operation tests remain green. The shared review identity advances to `assessment-review-v10-accounting-public-numeric-choices`, preventing new admissions from silently resuming pre-binding accepted checkpoints. Historical packages, attempts and replay evidence are not rewritten. Final integrated source identity and release gates must be rebuilt after integration.

This removes two avoidable model-dependent correctness/repair paths. It is not a measured speed claim, a general semantic validator or proof that all Accounting questions or providers are qualified. No GPU, native UI or GitHub mutation was used for this change.
