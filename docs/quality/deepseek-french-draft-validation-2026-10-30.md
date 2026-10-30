# DeepSeek French draft validation

## Scope

DeepSeek is a candidate provider for model-authored French NSI drafts, not a qualified paper generator. It is unavailable for UK papers. Flash and V4 Pro use a fixed HTTPS endpoint, separate credentials and separate consent. The app sends the French references, prompts, drafts, proposed corrections and review material needed for generation. This does not imply that the provider keeps no logs.

The implementation uses typed JSON requests and validates the returned model, completion state, schema and finite values. It refuses redirects, malformed output and unbounded requests. French phases use low reasoning effort. DeepSeek authoring allows 32,768 output tokens; blind solving and review allow 16,384 each. Reasoning and final text share those ceilings. Other providers and operations keep their existing budgets. These settings follow DeepSeek's [Responses API](https://api-docs.deepseek.com/api/create-response/) and [thinking-mode documentation](https://api-docs.deepseek.com/guides/thinking_mode/), checked on 30 October 2026.

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
| Pro 16k, connected brief | First authoring response completed; display-only Python filter rejected `nonlocal` | Overbroad display restriction reproduced; no PDF published |
| Pro 16k, separated display boundary | First exercise passed authoring, blind solving and review; second authoring response exhausted 16,384 tokens | No complete paper or PDF; authoring ceiling raised separately from review budgets |
| Pro 32k, audited admission | First exercise passed all three stages; second authoring response completed but used a full function in a bounded `python_trace` contract | Unsupported proof contract refused; no PDF published, and no automatic mathematical-error verdict |
| Pro 32k, capability descriptions | Three first-exercise calls completed in 333.69 seconds; question-review issues contained explicitly nonblocking terminology and grammar notes | Strict issue rejection refused publication. Independent review separately found a justification/rubric gap, so this was not a correct paper refused only for style |

The first tiny-probe attempt called a nonexistent harness method and sent no request. It remains separate from model failures. Raw attempts, request settings, usage and hashes are retained. Do not describe replayed evidence as a new live run.

## Review-flow repair

The blind solver noted that technician T1 did not appear in the sample rows. The question asks students to write an UPDATE, not calculate its result. SQLite permits an UPDATE to match zero rows, as its [UPDATE documentation](https://www.sqlite.org/lang_update.html#details) explains. Independent tests checked both matching and nonmatching rows.

The previous flow refused every blind note before the third review could assess it. The repair is general, with no SQL-specific exception:

- The third review receives every original note unchanged.
- Every note requires an indexed decision, a strict Boolean blocking flag and a nonblank rationale.
- Missing, extra, malformed or blocking decisions refuse publication.
- Incorrect answers, incomplete corrections, inconsistent rubrics, missing data and other negative question checks still refuse publication.
- Accepted advisory notes remain visible warnings with the original concern and rationale. Package revalidation recomputes those warnings.

New question reviews also have a distinct bounded `advisories` channel for optional style suggestions. These produce question-specific warnings. Every entry in `issues` and every negative review flag still blocks, even if its prose calls it minor. Legacy saved reviews without advisories retain their original schema; partial advisory additions refuse. The Pro9 response is not retroactively converted or accepted.

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

## Display and execution boundaries

The connected-brief attempt included `nonlocal` in a printed correction. The display checker parses fragments without executing them; treating every scope declaration as unauthorized access was overbroad. Harmless declarations are now admitted as text. Declared identifiers still pass the forbidden-name checks. Import, file, network, dynamic-execution and reflective-access restrictions remain.

Executable `python_trace` verification uses a separate bounded interpreter. Its allowed statements and refusal of scope declarations/functions are unchanged. Targeted tests cover both boundaries. Revalidating the retained response after this fix admits its structure without executing its code; that replay is not a fresh generation or semantic qualification.

The 32k attempt exposed a separate authoring-documentation gap: the schema did not describe the interpreter's supported subset. Its descriptions now state the exact Python, SQLite and shortest-path verification capabilities and limits. Unsupported tasks must explicitly request human verification. Failed executable contracts still refuse; the app never silently relabels them. This change has not yet qualified a fresh live paper.

Independent review of that attempt also found a substantive error in the second exercise. Its proposed algorithm re-enqueues a vertex whenever its distance improves, without a finalized set. The explanation incorrectly claims that a previously removed vertex cannot be reconsidered and that FIFO scheduling must change the result. For the supplied FIFO example, later relaxation corrects the distance to 2. The unsupported contract had already stopped publication; repairing its documentation does not repair these generated claims.

In the later capability-description run, an independent question-only derivation found the route D-B-E-G with cost 7 and checked the adjacency list, code and debugging answer. The proposed justification compared selected alternatives but did not establish a global minimum. Its rubric awarded the justification credit for that insufficient comparison. This remains a real quality concern even though the numerical shortest-path contract passed. Original model responses and the independent derivation are retained separately; no answer or rubric was patched.

## Native interface evidence

The candidate Release showed the DeepSeek model choices and paid-credit warning. Without a saved key, French Create remained disabled with an instruction to enter one. UK creation remained disabled for DeepSeek even with layout preview enabled. No real key was saved during UI testing.

A separate native check found that the visible UK model name was missing from accessibility output after switching providers. The model row now supplies a localized label and spoken value. It does not reset the form or preview state. A selected DeepSeek provider also has a visible French-only label in the UK picker, where it is genuinely nonselectable through SwiftUI's `selectionDisabled`, not a blanket `disabled` modifier. The four supported UK alternatives are unchanged. Actual accessibility observations verified both fixes; the candidate was closed and the original provider, model, preview, language and output preferences restored.

French elapsed time starts with generation. An ETA uses matching completed French provider/model/version history; without that history it says remaining time is unknown. This measures software runtime, not learner timing. Native tests cover timer cleanup, cancellation, navigation and exercise-level advisory headings. These scoped checks do not establish complete interaction coverage.

## Remaining acceptance

### Later frozen-source checks

The Pro 18 run used seed 270100 on `a3e14e6a`. Its three calls completed in
204.59 seconds. Both solving and review identified an unstated tree-height
convention. An independent derivation found a longest branch with three edges
or four nodes, while the proposed credit accepted only three. That is a genuine
answerability and marking ambiguity. No paper or PDF was published.

Pro 19 used seed 270200 on merged PR #132 source
`b97beeeb7e30953fb85dc1fafba4d72a85f647b6`. Four calls completed in 299.75
seconds with unchanged Core identity
`746cc72bb2837d6a48773eb7f26ba126aa4997a48e20adaaadad09f7657f1145`.
The first exercise passed the automated author, solver and review stages.
The second author returned standalone indented methods in a Python answer
block. Python raised `IndentationError`; publication stopped without a PDF.

Independent question-only review also found substantive problems in the first
exercise despite its automated pass. Its description equates purity with not
modifying another function, although its ordinary memo-dictionary solution
mutates a caller-supplied argument. Its fourth question and rubric identify
recursive memoisation and iteration as two different programming paradigms.
Recursion alone does not establish functional programming. A private or copied
cache can avoid external mutation, so this finding is about the supplied task
and rubric, not a claim that all memoisation is impure.

The internal reviewer derived `trajets(4) = 5` with nine recursive calls and a
faulty iterative result of six instead of eight before reading any proposed
answers or model reviews. The progression is connected Terminale work; its
70-minute label is not observed learner timing or evidence of equivalent demand.
Eduscol's [functional-programming guidance](https://eduscol.education.gouv.fr/sites/default/files/document/ra21lyceegtnsiparadigmefonctionnelpdf-70551.pdf),
pages 3 and 5, was rendered and visually checked. It distinguishes side effects,
pure functions and functional composition. The official guidance PDF hash is
`703cbd759841b016d5acac15df02a3c17ef273430e28f46fd5d9498b0606d3f5`.
The question-only request hash is
`6ca6c0134666b570639fb7060b6543ad3a2060be52aa5e68464cdd5949b04ec5`.

The indentation failure exposed a separate recovery defect. A raw syntax error
escaped the existing bounded format-regeneration path. The prospective fix
audits every field and fence before classifying fully tokenised malformed code
as a formatting failure. Unsafe names, imports and incomplete lexical audits
still stop without retry. The existing limit remains two whole-exercise attempts;
this display audit does not dedent, repair or execute code, or patch an answer
or rubric.
Twenty regressions reproduced eighteen failures before the fix; all 103 focused
code-format, layout, scope and provider-contract tests passed afterward.
Two further negative cases showed that a definition keyword could exempt a
later dunder token across an intervening operator. The audit now permits that
exception only for the immediate method or class name. Those cases and a
legitimate indented `__init__` definition pass with the correction.

An explicitly labelled offline replay confirms that the unchanged second
response now raises the typed format error. Its SHA-256 remains
`8500d8cd6384807f127ef529dd1afade40a5de40c12976c2a1a1964b3cb34433`.
That replay is not another live run or acceptance of its content. Both live
attempts remain failed, and the first exercise's conceptual problems are not
resolved by this recovery fix. Final integrated tests and protected publication
are separate gates.

The repaired flow needs a fresh complete live paper, independent checks of every answer and rubric, and every-page comparison with the official comparator before any qualification claim changes. Native acceptance also needs the final integrated build. Store signing, third-party rights and the wider supported-paper matrix remain separate release requirements.
