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
8. low similarity to every previously accepted item.

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
revalidates and resumes them without another model call. Identity drift rejects
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

PDF qualification separately rejects clipped or overlapping text and
unexplained content-free pages. OCR Economics mark-scheme overflow is allocated
across bounded continuation pages so every marking point remains present even
under adversarially long content. The deterministic qualification matrix
renders and validates every declared role for all 18 advertised papers.

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

Automation still cannot prove that a new item is pedagogically excellent. A
production release process should retain:

1. subject-specialist item review;
2. independent mark-scheme standardisation;
3. accessibility and ambiguity review;
4. small cognitive/timing pilots;
5. representative response-data calibration;
6. exposure monitoring and retirement.
