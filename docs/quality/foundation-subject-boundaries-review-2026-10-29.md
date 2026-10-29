# Foundation subject boundary review

Date: 29 October 2026

This scoped review covers four subject utility modules and their three expanded
test files. The author read those files completely and wrote the regression
tests and fixes. Independent review and release acceptance remain separate
gates. The snapshot was uncommitted on `main-xcode-and-validation-follow-up`,
based on `639643600336767b713c05494c56899dcf1b7467`, when hashes were recorded.

## Findings and implementation

- **Mathematical expression syntax:** the old character whitelist admitted
  Python attribute/method syntax before calling SymPy's parser. The official
  [SymPy parsing documentation](https://docs.sympy.org/latest/modules/parsing.html)
  warns that `parse_expr` uses evaluation and requires sanitized input. A
  pre-parser AST whitelist now permits arithmetic, finite numeric literals,
  ordinary variable names and bare calls to the previously supported math
  functions. Attributes, subscripts, private names and other Python syntax are
  refused before the parser is called. The evaluation namespace also has empty
  builtins. Regression spies raise if the parser is reached for those inputs;
  no exploit payload was executed.
- **Explicit mathematical precision:** significant-figure metadata was ignored
  by the answer comparator. Numeric literal formatting is now checked when
  precision is explicitly requested, including scientific notation. Without an
  explicit requirement, existing symbolic equivalence and tolerance behavior
  remain unchanged. This does not add a new precision requirement to questions.
- **Physics nonfinite values:** Decimal construction can accept NaN/infinity
  before later operations fail. Nonfinite operands and nonfinite/negative
  tolerances now return a controlled rejection. Finite comparison arithmetic
  errors are also handled without converting an invalid answer into a pass.
- **Chemical grammar:** trailing unmatched closing parentheses, empty groups,
  zero atom/group counts and zero equation coefficients are rejected. Existing
  valid nested formulae and balanced equations remain supported. This is grammar
  and atom-count validation, not a complete chemical-validity judgement.
- **Pseudocode literal identity:** normalization retains quoted string content,
  including case and arrow characters inside strings. Keywords and unquoted
  assignment arrows keep their previous normalization.
- **Boolean token boundaries:** operator names no longer consume prefixes of
  identifiers such as `ORANGE` and `NOT_FOUND`. Trailing whitespace is accepted;
  supported operators and their existing precedence are unchanged.

## Evidence

The following ignored local logs are retained. They are not shipped resources
or guaranteed to exist in a new GitHub checkout.

| Log | Result |
| --- | --- |
| `tmp/foundation-validation-boundaries-red.log` | 29 failed, 35 passed before the fixes |
| `tmp/foundation-validation-boundaries-first-green.log` | 84 passed in 3.68 seconds |

The green run selected `tests/test_mathematics_subject.py`,
`tests/test_science_subjects.py`, `tests/test_computer_science_subject.py` and
`tests/test_subject_plugins.py`. The expanded tests preserve existing symbolic
identities, units/tolerances, valid nested formulae, finite physics answers,
keyword normalization and all six Boolean operations. Affected-file Ruff,
formatting and `git diff --check` passed. No full suite, model call or build was
performed for this package.

## Actual caller scope

The registry discovers subject plugins when validating capability metadata.
Discovery imports these modules but does not demonstrate that a plugin's solver
was invoked for a generated paper. Mathematics is a currently unadvertised
foundation in `Resources/generator-registry.json`; biology, chemistry and physics
are registered subject foundations rather than advertised complete generation
routes in that registry.

The pseudocode/Boolean helpers are exposed through the specialised CS plugin.
Current advertised CS generation also has separate closed-answer contracts and
validators. No production call outside these utility modules was found for the
math/physics comparison helpers or pseudocode-equivalence helper during the
scoped caller search. These fixes are not evidence of improved MLX, Accounting
or French paper difficulty, reasoning depth or provider-quality equivalence.

No historical French catalogue, question bank, provider, prompt, mark tariff or
reference-data file was edited. In particular, the separately retained failed
Gemma Accounting Paper 2 diagnostic is not explained or repaired by these
foundation changes.

## Exact reviewed bytes

| File | SHA-256 |
| --- | --- |
| `Backend/Core/subjects/mathematics.py` | `c981cbc4f1866191fecb6a04965e179beb08150dda4464a6421613b9ca773f40` |
| `Backend/Core/subjects/physics.py` | `88b7bf9a128d001f16ca780466bb51acb27ebf916d5aa410bce9e866ebe4bc27` |
| `Backend/Core/subjects/chemistry.py` | `da68092ec5af9ba3e0ce8404b5dc8186b5119d2389e1cbacfdd2bef049d88ee4` |
| `Backend/Core/subjects/computer_science.py` | `b477b0bcec748bcd1462a96964cd048b3e3eba4cb7ea30d6a696fcc79730cbd8` |
| `tests/test_mathematics_subject.py` | `c696ec5544308d9cd0a0a70cd24c97e5eb125cd97a5bd6ed87fa04a5ec7da95f` |
| `tests/test_science_subjects.py` | `558a6858b93ab7895a78f5129147e73106e213680cabc53d9114b1711cbea68a` |
| `tests/test_computer_science_subject.py` | `c3deffe498199bde771c6d06d8d02e390467142a0ca8713c7f10a2e97188342c` |

## Limits and pending gates

- The AST gate is not a general-purpose execution sandbox or a resource/time
  bound for arbitrary symbolic algebra. No penetration-test or complete
  mathematical-domain validation claim is made.
- Precision comparison applies to explicitly requested numeric literal output;
  it does not infer a precision policy for unrestricted symbolic answers.
- Chemical grammar checks do not establish physical feasibility or a complete
  periodic-table, ion, hydrate or practical-assessment implementation.
- The existing truth-table/pseudocode utilities are not a full compiler or a
  proof that arbitrary student programs are equivalent.
- Final whole-suite, native, rebuilt-helper and protected CI gates remain
  pending for the integrated source. Earlier native/model outputs retain their
  original helper identities and are not relabelled as results of this source.
- No teacher validation, observed learner timing, full-HIG compliance or Store
  approval follows from these tests.
