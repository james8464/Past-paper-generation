# Python trace name bindings

## Reproduction

A source review identified a mismatch between the bounded trace interpreter and
Python name lookup. If a program assigned an integer to `len` or `range`, the
interpreter still called the original builtin. For example:

```python
len = 7
x = len([1, 2])
```

Real Python raises `TypeError`. The verifier previously returned 2 and marked
that expectation passed. A similar reassignment of `range` incorrectly produced
a loop result of 3. Owned fixtures reproduced both mismatches directly and
through current public French exercise admission. These are implementation
false acceptances, not observations from a live generated paper.

The red tests produced four expected failures and four passing controls.
Evidence: `tmp/nov3-trace-bindings-red.log` and
`tmp/nov3-verifier-shadowing-owned-reproduction.log`.

## Repair and controls

Before evaluating a function call, the interpreter now refuses a function name
already bound in its executed environment. Supported environment values are
scalars and lists, not callable objects. The repair does not ban assignments or
reads of variables named `len` or `range`. It also leaves builtin calls usable
when a reassignment exists only in an unexecuted branch.

The final scoped suite passed 104 tests, including direct and public-admission
refusals, ordinary builtin calls, uncalled shadowed values and unexecuted
reassignments. Existing NSI assessment, contextual display, scope and verifier
capability tests passed in the same run. Evidence:
`tmp/nov3-trace-bindings-green-final.log`.

No generated question was rewritten, no expected answer was hardcoded and no
validation threshold was relaxed. The interpreter remains a bounded subset,
not a general Python execution service. The application does not use `exec` or
`eval` to implement this repair; the comparison log executed only the fixed,
owned reproduction fixtures in a separate local diagnostic.

## Review scope

`release_gap_audit` read the complete prior verifier, all of the two-line repair
and the new test file. Root then added and checked the unexecuted-branch control.
The independent production review found no additional concern in this delta.

| File | Lines | SHA256 |
| --- | ---: | --- |
| `Backend/Core/france/verification.py` | 595 | `1d7cb5e3c9e4a8ebd049bb810c5eaf566f5628b6e1520eeee1fd489f5546b50c` |
| `tests/test_french_trace_bindings.py` | 58 | `6cfbb88f4541b0b095464b6ba9d3ee404a9028b5182db1a90784872e7047e8c4` |

The isolated declared graph-vertex corner case identified in the same review is
separate and unchanged. The earlier 6,749-test full-suite result belongs to
PR167 source `51b0b8f1`, not this later repair. Final full and protected gates
remain required for the new candidate. This review does not qualify an entire
French paper, establish model reliability or certify all interpreter semantics.
