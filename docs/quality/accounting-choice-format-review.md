# Bound Accounting choice formatting

The verifier recomputes a closed Accounting answer from its public inputs.
Its four options are then checked for whole-pound currency formatting. The
old check parsed every option as a decimal and formatted it before comparing
the original text. A short string such as `£1e10000` therefore reached a
formatter that could expand the exponent before rejecting the option.

The regression test stops at the formatter boundary; it does not allocate
the expanded string. Before the repair, that test failed and seven format
controls passed. The repair checks the currency text directly and performs
arithmetic only on the existing bounded public inputs. Zero and negative
grouped amounts remain supported. No generated answer, formula, source
contract or prompt changed.

All 213 focused tests passed, including both Accounting papers' source
choices, solver choice validity and shared numeric integrity. Review covered
the complete selected-response module and its test file. The change does
not resolve the retained Accounting Paper 2 Q06 semantic false acceptance
or establish a cause for the historical macOS memory incident.

| File | Lines | SHA256 |
| --- | ---: | --- |
| `Backend/Core/subjects/accounting_selected_response.py` | 322 | `794766f3eb77720beb2e752cec8dc388bba4d6d7d113fe4214f0be474efd1ce1` |
| `tests/test_accounting_selected_response.py` | 295 | `26feb931e0ab0b9c9e58759ca49e90ec68f5d822f6933bf8dd3f8af363c10289` |
