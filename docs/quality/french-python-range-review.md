# French Python range verification

The bounded Python interpreter converted every `range` into a list. That
changed the meaning of comparisons. For example:

```python
x = range(3) == [0, 1, 2]
```

Real Python assigns `False`. The previous verifier approved `True`, and the
public French exercise validator admitted a draft with that incorrect result.
An independent source review identified the defect. Red tests reproduced both
the direct false acceptance and public admission before the production change.

## Repair and checks

The interpreter now retains bounded native range values during evaluation.
Iteration, aliases, length and indexing keep Python's range semantics. Range
equality compares the generated sequences, including empty ranges and ranges
with different stops but identical values. Unsupported ordering fails instead
of acquiring list ordering semantics.

The existing 256-item range limit, 5,000-step budget and nested-list refusal
remain. Final evidence still requires the supported JSON-compatible value
types. A raw range, including one inside a result list, refuses without
silently converting it into an answer. Failure reports remain JSON serializable.

The initial test batch found seven failures and nine passing controls. One case
expected a nested-list comparison to pass, although nested lists are outside
the interpreter's existing supported subset. That test was corrected to retain
the refusal instead of expanding production support. The resulting 25 trace
tests pass. The broader French trace, authored-exercise and SQL source-binding
selection passes 194 tests with five existing PyMuPDF/SWIG warnings.

Independent review covered the complete 610-line previous verifier and all
production changes, the complete 169-line SQL source binder, and all 78 lines
of the new range regression file. Selective caller and identity checks found
no further actionable defect in this scope. Current verifier SHA256:
`0150e723b4d7314ea588a5aec0aded5c6e1b7e32da563ec85d1e29b23505fce1`.
SQL binder SHA256:
`1e01aa318c2d9c01113c515df3381235bc07874598731234073dd160f92df055`.
New regression SHA256:
`e2283be33dd81abbf9f4923c2a07a5645f89b757ef431ac04cba563203ab4f51`.

## Acceptance limits

The current French source identity includes this implementation, so prior
review evidence cannot silently certify its changed behaviour. Historical
packages and artifacts have not been rewritten. No model was called, no
generated answer was edited and no approval threshold was lowered.

This repair covers a reproducible interpreter defect. It does not establish
that a printed question and its verification contract describe the same task,
or qualify an entire French paper, a provider, learner timing or the complete
codebase. Full frozen-source tests and protected CI are required separately
before release.
