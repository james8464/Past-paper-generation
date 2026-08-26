# Assessment quality and originality

## Release invariants

The generated paper is new content inside a fixed assessment contract. AI may
change wording, contexts, data, distractors, marking points, and indicative
content. It may not change:

- paper and section structure;
- question/option identity;
- marks and exact AO allocation;
- syllabus outcome;
- command-word demand;
- expected response time and answer mode;
- required source references and numeric invariants;
- multiple-choice option count and answer-key validity.

## Qualification evidence baseline

Qualification is reported as three independent levels: engineering validated,
visually calibrated, and empirically calibrated. The canonical evidence model is
defined by `Resources/qualification-schema.json`; the gates required for each
level are defined by `Resources/qualification-policy.json`. A live matrix run
writes one immutable manifest per paper and an aggregate manifest containing
only relative evidence references and hashes.

The current live baseline contains seven advertised generator families and 18
papers. The latest complete `gemma4:12b` Ollama run passed generation and release
validation for all 18 and has been backfilled into the qualification ledger.
That baseline is engineering evidence, not a new visual or empirical claim.
AQA Computer Science Paper 2 and Pearson Edexcel Economics A Papers 1–3 retain
their uncalibrated visual state. Every current paper retains an uncalibrated
empirical state because no qualifying external learner/marker dataset is linked
to the generated form.

The normal generation path fails closed if it cannot satisfy the contract after
bounded retries. It never silently substitutes the deterministic planning draft.

## Item transactions and two-pass generation

Each question is authored, validated, adversarially reviewed, and checkpointed
before the next local-model question starts. Hosted providers may execute
independent item transactions concurrently, but a rejected item is repaired in
isolation and cannot discard an accepted neighbour.

The first model call writes one newly authored item. The
prompt includes only the selected syllabus outcome, immutable blueprint,
per-question draft intent, exact output schema, a per-item numeric-token
contract, and the failure reason from an earlier attempt. A repair call also
receives only the rejected candidate and structured review issues.

The parser then verifies:

1. exactly one response per requested blueprint ID;
2. preserved numeric tokens where the renderer/source depends on them;
3. command-word presence and immutable metadata;
4. exact marks and AO point totals;
5. specific, distinct marking points;
6. unique and valid MCQ options;
7. material difference from the planning draft;
8. low similarity to every previously accepted item;
9. the same examiner-usable mark-scheme depth gate used by package release.

A separate, deterministic-temperature model call receives the frozen blueprint,
candidate item, and syllabus point. It reviews adversarially and must explicitly
approve factual correctness, mark coverage, source consistency, difficulty,
ambiguity, grammatical scope, distractor exclusivity, and answer correctness
with no issue arrays. A missing, malformed, or negative review rejects the item.
Because the selected model performs both passes, this is second-pass quality
control, not an independent examiner review.

Numeric values carry semantic roles. Assessment data is compared as a multiset
unless order is explicitly meaningful; marks, item IDs, figure/extract labels,
and pseudocode line labels are excluded from data comparison. Declared generated
fields are range-checked. Undeclared or changed quantities still fail closed.

Accepted items are written atomically to an output-local checkpoint identified
by the paper blueprint hash, seed, provider, model, and prompt version. A restart
revalidates and resumes them without another model call. An item written by an
older validation boundary that no longer passes is removed individually and
regenerated; valid neighbours remain intact. Identity drift rejects
the checkpoint instead of mixing generations. The checkpoint is deleted only
after the complete package publishes successfully; cancellation and failure
retain it.

High-risk deterministic subject rules run before model review. Current rules
include complete accounting costing identities and exchange-rate direction
checks. This prevents a fluent reviewer response from approving a contribution
calculated from profit or a reversed appreciation/depreciation effect.

## Mark-scheme quality

Marking guidance is data, not renderer prose. Structured marking points record:

- point text;
- awarded marks;
- assessment objective;
- acceptable alternatives;
- rejected answers;
- level descriptors where the question uses levels.

Every question mark must be traceable to this structure. The validator rejects
duplicate points, missing mark coverage, incorrect AO totals, generic empty
guidance, invalid keys, and schemes too sparse for the available marks.
Question papers and mark schemes are rendered from the same model, preventing
answer drift.

The release-depth gate also scales with response type and tariff. It requires
enough substantive credit points for the available marks, AO coverage matching
the blueprint, explicit method and accuracy guidance for calculations,
acceptable alternatives and credit limits where examiner judgement is needed,
question-bound source evidence for data response, and complete level
descriptors for levels-based extended responses. The assessment package keeps
the original question kind, AO allocation, evidence identifiers, and structured
scheme so these checks run before renderer-specific prose can disguise a thin
answer.

For levels-based schemes, deterministic normalisation supplies the invariant
examiner boilerplate for accepting another well-supported route and preventing
duplicate or unsupported credit when the model omits it. The model remains
responsible for the question-specific indicative content; the invariant marking
rules do not depend on model compliance.

PDF qualification separately rejects clipped or overlapping text and
unexplained content-free pages. OCR Economics mark-scheme overflow is allocated
across bounded continuation pages so every marking point remains present even
under adversarially long content. The deterministic qualification matrix
renders and validates every declared role for all 18 advertised papers.

### Measured visual qualification

`tools/paper_fidelity_audit.py` compares each generated document with its local
reference at both document and page-role level. The registered comparison
separately measures stable furniture, text placement, and geometry so newly
authored question wording does not dominate the result. The versioned minima in
`Resources/fidelity-thresholds.json` cover every advertised family, question
paper, mark scheme, and observed page role. The command exits non-zero when a
document is absent, a role disappears, the audit schema changes, or a score
falls more than 0.5 percentage points below its qualified baseline.

The final 26 August 2026 qualification generated all 18 papers with the
recommended live `gemma4:12b` Ollama model and release-validated every declared
artifact. Its 36 primary PDFs produced a 68.9% aggregate registered similarity
score, and every calibrated document and page-role floor passed.
All 151 overview, weakest-page, and per-document contact sheets were inspected
for:

- cover hierarchy, candidate boxes, typography, margins, rules, barcodes, and
  page folios;
- question numbering, command words, mark boxes, response allocation, and
  section transitions;
- table borders, diagrams, graph axes, legends, data labels, and image clarity;
- mark-scheme columns, marking-point density, levels, alternatives, and
  continuation behaviour;
- intentional blanks, answer rules, legal-notice exclusion zones, clipping,
  collisions, missing glyphs, and malformed pages.

No rendering defect was found in that matrix. Differences caused by independently
authored questions remain expected, and the neutral Paper Creator identity is
deliberately used instead of exam-board logos or copyrighted footer material.
The score is therefore a regression boundary, not a claim that the documents
are official or pixel-identical.

### Print-resolution qualification boundary

The excellence audit added a stricter evidence layer after the earlier visual
review. It matches semantic page roles across up to three same-paper sessions,
derives its structural grid from physical page size, and records glyph
baselines and boxes, font embedding, leading, rules, answer-line spacing,
mark-position geometry, tables, reading order, PDF tags, safe-print bounds, and
monochrome contrast. CI uses 300 DPI; final qualification uses 600 DPI at 100%
scale.

A deterministic 18-family structural run over the existing live matrix found
no audit crash, but it did find genuine qualification gaps. The generated PDFs
are not yet tagged; some documents retain an unembedded standard-font fallback;
and recurring footer furniture crosses the conservative 4.2–5 mm safe-print
box on many pages. Manual 300-DPI cover and weakest-page inspection also found
that OCR cover furniture remains less faithful than AQA and Pearson, while
role-aware matching prevented ruled answer pages from being compared with
graph/data pages. These are explicit print failures to be resolved by the
shared rendering work, not reasons to lower thresholds.

Calculation cases are typed shared contracts consumed by the printed source,
AI authoring pass, verified answers and mark scheme. This prevents an item from
asking candidates to use a figure that the paper never supplies.

When both the prompt and scheme are completely determined by one of these typed
calculation contracts, the production authoring batch bypasses stochastic model
rewriting and records `verified-contract` provenance. The representative live
Accounting Paper 1 run therefore used Ollama for 15 genuinely open-ended items
and retained six calculation prompts and schemes directly from their verified
shared cases. Mixed batches are partitioned automatically, so this boundary
also reduces generation time without reducing AI novelty where it is useful.

Contracts may also declare mandatory marking content and forbidden semantic
relationships. These deterministic checks catch a fluent rewrite that assigns
an adjustment to the wrong account or omits a required period even when a
second model reviewer approves it.

Levels-based enrichment is limited to extended responses and other high-mark
non-calculation questions. Calculations and data tasks remain points-based even
when they carry many marks, so the model receives method/accuracy requirements
rather than a contradictory levels-of-response contract.

For a one-mark multiple-choice item, a model shorthand such as “Statement C” is
normalised to the complete keyed option in the mark scheme. The answer itself
still undergoes factual and ambiguity review; this normalisation removes a
format-only retry without weakening correctness checks.

## Novelty and exposure

Each assessment package contains normalised SHA-256 fingerprints. Weighted
token-shingle Jaccard comparison is used because it catches reordered or lightly
edited paraphrases while abstracting incidental numeric changes.

- Draft-to-candidate limit: family/shared policy, normally 0.82–0.90.
- Within-paper limit: 0.84.
- Published-history limit: 0.84 for the same subject and paper.

Normal generation rejects a threshold match before publication and records the
nearest historic match and comparison count in the manifest. Preview drafts do
not enter exposure history and are clearly labelled non-release output.

## Difficulty claims

Blueprint validation can establish intended demand, not experienced difficulty.
Consequently, every current registry difficulty gate remains false.

`tools/calibrate_student_responses.py` implements exact-form calibration from
anonymised long-form CSV data:

```csv
candidate_id,item_id,score,max_score,time_seconds,group,marker_id
```

The resulting fingerprinted evidence includes item facility, corrected
item-total discrimination, median time, Cronbach's alpha, pairwise normalised
marker agreement, and a group facility-gap screen. A verified result requires
all of the following:

- at least 100 candidates;
- at least 80 responses and discrimination of 0.15 per item;
- at least 90% of facilities between 0.20 and 0.85;
- reliability of at least 0.70;
- at least 30 double-marked pairs and agreement of at least 0.80;
- no facility gap above 0.15 where both groups have at least 30 responses;
- an identified independent reviewer, role, date, and explicit approval.

Evidence is tied to one `form_id` and is not transferable to future AI-created
questions. The group comparison is a screening flag, not a substitute for
matched DIF/IRT analysis.

## Human release review

## Independent solution and response-band qualification

AI-authored items now carry explicit answer-form, timing, prerequisite,
misconception, observable-mark-point, alternative-answer, partial-credit,
common-error, follow-through, and level-policy contracts. Production generation
through the shared AQA/OCR pipelines performs an additional solver call in a
context that excludes the drafted mark scheme, deterministically recomputes any
declared calculation expression, binds citations to supplied evidence, and
reconciles the resulting answer, marks, AOs, alternatives and credit boundaries
before the existing adversarial model review.

Levels-based items use versioned best-fit policies for AQA, OCR, Pearson Edexcel
and Cambridge International. Synthetic weak, average and excellent responses
must receive strictly increasing marks, with a written reason for every awarded
and withheld mark. Assessment packages also record cross-paper topic, AO,
command-word, mark and demand distributions and fail closed on duplicate
prompt/context pairs, answer leakage, ambiguous opening pronouns and non-finite
data. The AQA Computer Science and Pearson pipelines retain their existing
immutable-answer and independent-review paths pending migration to the shared
document/assessment DSL.

Automation still cannot prove that a new item is pedagogically excellent. A
production release process should retain:

1. subject-specialist item review;
2. independent mark-scheme standardisation;
3. accessibility and ambiguity review;
4. small cognitive/timing pilots;
5. representative response-data calibration;
6. exposure monitoring and retirement.
