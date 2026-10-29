# Independent choice-validity contract

The retained Qwen question-pair probe exposed a solver limitation. A draft asked for contribution from price £45 and variable cost £10 but supplied £30/£40/£50/£55. The independent solver correctly calculated £35 in its steps. Its answer grammar nevertheless required one of the public options, so it emitted £30. Later validation refused the paper; the solver itself could not report that no option was correct.

Trusted multiple-choice solver requests now require `has_single_valid_choice`, a strict Boolean. The blind prompt asks the solver to derive the result, assess every public option and report false for either zero or multiple valid options. False refuses the candidate before canonical solution construction and reconciliation. The required public-option answer is only a rejected placeholder in this case. No private key or draft marking guidance enters the prompt or schema.

The signal is a model judgment, not a mathematical proof. True does not bypass agreement between answer and mark point, independent numerical checks, private-key reconciliation or later content review. The change does not promise that a small model will reliably detect every defective question.

Real typed `generate_request` providers must supply an actual Boolean; missing, null, integers and strings refuse. Historical `generate_json`-only lightweight clients may omit the new field deliberately. If they supply it, strict Boolean and false-refusal rules still apply. Non-choice and slot-mapped response contracts retain their earlier shape and reject an unexpected choice-validity signal. Deterministically solved items keep their existing code-owned checks.

The shared review version is now `assessment-review-v8-single-valid-choice`. New jobs cannot resume an accepted item from a pre-gate checkpoint under the unchanged review identity. Existing packages and checkpoint evidence are not rewritten.

No-model regression coverage includes absent and multiply valid options, missing/coerced signals, true with an incorrect private key, contradictory mark points, blind prompt privacy, legacy compatibility, unchanged open/slot responses and actual llguidance grammar compilation. The former schema was reproduced without loading a model: its required fields contain no choice-validity signal. Live model evidence must be rerun on the integrated source; the old retained failure is not a passing qualification.
