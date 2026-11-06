# Business strategic-rate admission review

The complete 974-line `Backend/Core/subjects/selected_response.py` was read at
SHA-256 `26b52d9c555d8d23e6f5ebf48825db683f938aee6b1e9d43cc2885822bc9a1f2`.
The review covered operation dispatch, contract shape, numeric formatting,
public-source grammar, row ambiguity and categorical domain checks. Relevant
solver, public generator, rendering and test sections were inspected; their
complete dependency trees were not audited.

One deterministic admission fault was reproduced without a model. The
strategic-change operation accepted two equal unsupported strings, including
`not-a-rate`, as `Strategic fit`. Equal numeric text and a Decimal value also
passed. The public generator emits supported high/low rates; this finding does
not establish that a default or live paper contained an unsupported value.

The repair checks that both existing case-folded rates belong to the supported
high/low domain before comparing them. It retains the existing error text,
does not strip whitespace, and leaves the schema, policy version, prompts and
answer calculation unchanged. High/low still means drift; high/high and low/low
still mean fit; low/high remains unsupported. This is domain admission, not a
general interpretation of strategic-change prose.

The new offline tests initially produced seven failures and 25 passing
controls against the original code. After the two-line guard, 251 focused
tests passed, covering the new controls, existing dispatch/source-demand tests,
Business calibration and public Business generator tests. Input immutability,
case-insensitivity, whitespace refusal and existing malformed-contract refusals
are retained. Ruff checking and formatting, and the diff check, passed. Five
existing PyMuPDF SWIG deprecation warnings remain. No models, native app, full
project suite or release builds were run for this repair.

| File | SHA-256 |
| --- | --- |
| `Backend/Core/subjects/selected_response.py` (976 lines) | `cf84797e281307ec3e1d2a3dd2b7eee0b3fe18a8292075623cd943bcb141a231` |
| `tests/test_business_strategic_rate_domain.py` (92 lines) | `e00e2e3cba20005560ef2588ff67db6b4fc6a92fe119dd4a31a29aadf1ed8181` |

This is a bounded source review and repair receipt, not a complete subject
audit, live question-quality qualification, general semantic proof or release
acceptance. The separate Accounting Q06 semantic limitation remains open.
