# DeepSeek French draft validation

## Scope

DeepSeek is a candidate provider for model-authored French NSI drafts, not a qualified paper generator. It is unavailable for UK papers. Flash and V4 Pro use a fixed HTTPS endpoint, separate credentials and separate consent. The app sends the French references, prompts, drafts, proposed corrections and review material needed for generation. This does not imply that the provider keeps no logs.

The implementation uses typed JSON requests and validates the returned model, completion state, schema and finite values. It refuses redirects, malformed output and unbounded requests. French phases use low reasoning effort and a 16,384-token ceiling, including reasoning and final text. Other providers keep their existing budgets. These settings follow DeepSeek's [Responses API](https://api-docs.deepseek.com/api/create-response/) and [thinking-mode documentation](https://api-docs.deepseek.com/guides/thinking_mode/), checked on 30 October 2026.

## Live diagnostic evidence

Root-only tests use a US$5 cumulative cap. Credentials remain in process memory, outside saved prompts and evidence. Each request reserves a conservative upper bound before sending. Verified usage releases the unused reservation; unobserved failed calls retain it. Peak uncached rates deliberately overestimate billed usage. Prices come from the [provider's pricing page](https://api-docs.deepseek.com/quick_start/pricing/).

Evidence is retained under `tmp/french-v36-live-20261030/`:

| Run | Result | Interpretation |
| --- | --- | --- |
| Pro 8k, high reasoning | Incomplete; all 8,192 output tokens were reasoning | No final exercise, so no question-quality verdict |
| Pro 8k, low reasoning | Incomplete; all 8,192 output tokens were reasoning | Lower effort alone did not solve completion |
| Tiny Pro probe | Completed; 2 + 2 returned 4 | Connector and structured-output smoke test only |
| Flash 8k, low reasoning | Incomplete; some final text, but no complete exercise | No paper-quality verdict |
| Pro 16k | First exercise and blind solution completed; review stopped on a blind note before third review | Review-flow defect reproduced; no PDF published |
| Pro 16k, repaired review flow | All three first-exercise calls completed; incorrect shortest-path selection order refused | Genuine worked-answer error, despite the correct final distance |
| Flash 16k | Two complete authoring responses; first had an invalid table cell, second used decimal commas in credit fields | Schema/validator mismatch exposed; no PDF published |
| Pro 16k, aligned schema | All three first-exercise calls completed; review refused an unstated tree-height convention | No PDF published; independent review also found that the convention needed clarification |

The first tiny-probe attempt called a nonexistent harness method and sent no request. It remains separate from model failures. Raw attempts, request settings, usage and hashes are retained. Do not describe replayed evidence as a new live run.

## Review-flow repair

The blind solver noted that technician T1 did not appear in the sample rows. The question asks students to write an UPDATE, not calculate its result. SQLite permits an UPDATE to match zero rows, as its [UPDATE documentation](https://www.sqlite.org/lang_update.html#details) explains. Independent tests checked both matching and nonmatching rows.

The previous flow refused every blind note before the third review could assess it. The repair is general, with no SQL-specific exception:

- The third review receives every original note unchanged.
- Every note requires an indexed decision, a strict Boolean blocking flag and a nonblank rationale.
- Missing, extra, malformed or blocking decisions refuse publication.
- Incorrect answers, incomplete corrections, inconsistent rubrics, missing data and other negative question checks still refuse publication.
- Accepted advisory notes remain visible warnings with the original concern and rationale. Package revalidation recomputes those warnings.

Empty-note review schemas and saved evidence retain their previous shape. This is still model review, not independent proof. A second call to the same model can rationalise an error; manual subject review remains necessary.

## Authoring-schema alignment

The exported schema originally described credit as arbitrary text, while the existing validator required machine-readable dot decimals. V36 now includes that syntax constraint, plus the existing nonblank and 180-character limits for table cells. The original validator still checks positive credit, exact totals and table structure. It remains the final authority for edge cases such as trailing newlines in portable regular expressions.

This changes what the model is asked to produce, not its completed answers. No decimal or table value is rewritten after generation. Historical authoring schemas and package readers retain their previous behavior.

The authoring brief now asks for a connected problem: interpret a supplied representation, construct or adapt a solution, then examine its behavior and justify its limits. It permits related subparts within an exercise while retaining independence between exercises. It also asks for explicit definitions, conventions and boundary behavior, with each requested item answered and credited. This is prospective instruction, not a deterministic depth check or evidence that a generated paper improved.

## Internal first-exercise review

Two internal reviewers independently derived the graph representations, SQL and minimum routes before comparing the proposed correction. Exhaustive simple-path enumeration found a minimum of 25 through four tied routes. The proposed recursive correction uses a path-local visited set and handles dead-end branches without an empty minimum.

The marking criterion for that correction does not explicitly credit minimum selection, although the task requires it. Its allocation also appears small relative to the requested construction. The database decomposition assumes a current contact record per technician without stating that business rule. These concerns remain recorded; the generated question, answer and rubric were not manually patched.

The candidate contains four top-level question objects and ten numbered subparts. Object counts are not directly comparable with official paper question counts. No complete French paper has qualified from these attempts. Teacher review and empirical learner calibration remain `not_run`.

A later candidate declares attributes `gauche` and `droit`, but its faulty height function calls `droite` and omits the increment. One internal blind reviewer initially missed the attribute mismatch and incorrectly reported only one definite defect. The original note is retained and marked superseded. There are two defects under the node-count convention; the convention itself remains unspecified. The model review refused that ambiguity. Internal review can also be wrong and is not teacher attestation.

## Remaining acceptance

The repaired flow needs a fresh complete live paper, independent checks of every answer and rubric, and every-page comparison with the official comparator before any qualification claim changes. Native acceptance also needs the final integrated build. Store signing, third-party rights and the wider supported-paper matrix remain separate release requirements.
