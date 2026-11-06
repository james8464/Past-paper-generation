# Computer Science functional-source binding review

An owned topic 4.12 question passed structural validation after its printed
definition changed from `mapped xs = map double xs` to
`mapped xs = map double xs ++ [999]`. The source projection retained the complete
definition, but the contract extractor only looked for the original substring.
It therefore derived the original mapped list and total as deterministic
results. For values `[5, 2, 6]`, it reported `[10, 4, 12]` and 26 rather than the
printed program's `[10, 4, 12, 999]` and 1025. No displayed program was executed
to establish this arithmetic. This is an owned input-boundary fault, not a
claim that a default paper or a live model produced the altered program.

The repair recognises the complete supported five-definition source language
before deriving its contract. The values, multiplier and filter threshold
remain parameters; the map and fold definitions must match completely and in
order. Extra expressions, helpers, redefinitions, comments, malformed lists,
missing definitions and meaningful indentation are refused. Blank lines and
ordinary line-ending variants remain harmless. No general Haskell interpreter,
new numeric range, answer repair or authoring prompt has been introduced.

The same parser runs during solver projection and before saved question-review
admission, including the built-in early return. Existing resume, package-write
and package-read callers therefore revalidate the source instead of trusting
an old matching content hash alone. The review digest and its policy version
are unchanged: supported historical canonical programs retain their identity;
unsupported historical programs now fail fresh admission. No old record is
rewritten or labelled as newly verified.

The initial controls produced 40 failures and 25 passes against the old code.
The focused repair tests now cover the original append counterexample, extra
fold arithmetic, redefinition, helper/comment/indent/order changes, malformed
or truncated source, saved approvals and package export/read boundaries.
Twenty representative public topic-bank seeds, signed and zero multiplier or
threshold parameters, and three line-ending forms retain their expected
contracts. These are bounded controls, not an exhaustive integer-seed claim.
The combined source/checkpoint/objective and AQA generator suite passed 501
tests, with two existing skips. Ruff checking and formatting passed. The
configured type gate passed its four existing infrastructure modules; it does
not statically certify this complete authoring module.

| Reviewed file | SHA-256 |
| --- | --- |
| `Backend/Core/computer_science_authoring.py` | `c85da33c357c41db9a725387f7a4f29810217ee564ca232e7adb591a88a843d4` |
| `tests/test_cs_functional_source_binding.py` | `606ef4fb0af162c94cf4f0f5323785100f40684dfdd213b14a1f5222f0c3c1c1` |

The prior full 289-line source audit and this complete repair delta are scoped
implementation evidence. They do not establish all dependency behaviour,
question difficulty, live model quality, official-paper equivalence, a complete
project audit or release-build acceptance. Frozen-runtime and protected release
gates remain separate.
