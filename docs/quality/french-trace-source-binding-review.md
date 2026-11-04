# French trace source binding

Current V36 admission now requires a `python_trace` program to match one complete candidate-visible Python fence in the shared exercise context or that question's prompt. Answers, marking criteria and other questions cannot supply the program. Supported unlabelled fences retain their existing Python interpretation; SQL and unknown-language fences do not bind a Python trace.

The comparison normalizes CRLF line endings and boundary newline characters only. It preserves indentation, comments, literal contents and other whitespace. It does not concatenate blocks, infer missing statements or change the printed source or proposed answer. A missing or mismatched source produces failed verification. Public admission raises its ordinary verification error, which the authoring path does not treat as a retryable formatting defect.

## Reproduction and tests

The owned reproduction printed `x = 2 + 3` and proposed the answer 6 while privately verifying `x = 2 + 4`. Before the repair, the private contract passed and public admission accepted the exercise. Evaluating the printed program against the same expected value failed with actual value 5. The private program was absent from the candidate view, and validation left the supplied input unchanged.

The new regression file covers absent, answer-only, marking-only and other-question source; a different private program; exact context and question blocks; multiple blocks without concatenation; CRLF and boundary newlines; indentation, comments and literal preservation; unsupported or unclosed fences; unsafe execution and incorrect expected values. It also checks recomputed evidence, non-retryable authoring refusal and implementation-bound package admission.

Two existing positive fixtures had supplied an unprinted trace. Each now prints that same exact program in the question. Their existing unsafe or incorrect-program refusal assertions remain intact. No prompt, schema, output allowance, scoring rule or retry count changed.

Retained logs are under `tmp/nov4-local-pdf-boundary/`:

- `trace-source-corrected-red.log`: 13 intended failures and 6 passing controls against the unchanged production helper, in 1.24 seconds. An earlier exploratory run contained a short-prompt fixture setup error and is retained separately; it is not counted as proof.
- `trace-source-green.log`: 127 passing cases across five selected files, before the final owned-copy identity control was added.
- `trace-source-broad.log`: the final source and tests passed 425 cases across thirteen relevant French files in 15.95 seconds, with five existing PyMuPDF warnings. This includes authoring, runtime, reviewed redraft, budgets, display fragments, fence boundaries, SQL source binding and isolated graph vertices.
- `trace-source-lint.log`: maintained Python Ruff checks passed and all 630 files passed formatting checks.
- `trace-source-mypy.log`: the configured four-file type-check gate passed. It is not a whole-pipeline type-check claim.

## Identity and review limits

The shared evidence collector calls the same `_verify_question` helper, so recomputation cannot retain a passed private trace after its printed source changes. Semantic `_validate_review` validates the review envelope; it does not itself execute trace contracts. Package and round admission separately revalidate exercises.

French implementation identity hashes Core source bytes. The tests prove that changing an owned copy of the binding source changes this identity, and that a package from a previous identity is refused without mutating its evidence. Historical files are preserved. This change does not add a missing-policy fallback or relabel old evidence as approved.

The author reviewed the complete new 187-line test file and every production and fixture change. Relevant shared parser, source identity, public admission, evidence and recovery callers were inspected selectively. This scoped change does not renew a complete-file semantic attestation for the large pipeline or existing test files.

Root independently reviewed all 19 production lines, the new test file and both positive-fixture changes, with no remaining finding.

| File | SHA-256 |
| --- | --- |
| `Backend/Core/france/llm_pipeline.py` | `8a71984c16628be3301d07fb25b39964cc573c50acb1a1ed5fd19cf2b03d7e50` |
| `tests/test_french_trace_source_binding.py` | `1f4d71db1b55eecc19235755c03961bfb761cff65cc70b08b614bbf9eeced807` |
| `tests/test_french_llm_pipeline.py` | `0272ed7b18dd61baf35124ad39e7153f904276492e110c07d213cd8cb4fe96a3` |
| `tests/test_french_verification_capability_brief.py` | `f6287a9e44985f23d371519e48f3dd7eecec04a05298ec1dda11dbe7cae0b7e4` |

Exact source membership establishes which printed program the bounded interpreter checked. It does not prove that the question refers unambiguously to that block, that the proposed explanation is complete or that the full paper is educationally qualified. Changed-code tasks and incomplete fragments still need an appropriate human/semantic review path. No provider, network, native UI, full suite or release build was invoked in this authoring lane.
