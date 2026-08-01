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

## Two-pass generation

The first model call writes a bounded batch of independently authored items. The
prompt includes only the selected syllabus outcome, immutable blueprint,
per-question draft intent, exact output schema, and the failure reason from an
earlier attempt.

The parser then verifies:

1. exactly one response per requested blueprint ID;
2. preserved numeric tokens where the renderer/source depends on them;
3. command-word presence and immutable metadata;
4. exact marks and AO point totals;
5. specific, distinct marking points;
6. unique and valid MCQ options;
7. material difference from the planning draft;
8. low similarity between items in the same batch.

A separate review call receives the frozen blueprint, candidate item, and
syllabus point. It must explicitly approve factual correctness, mark coverage,
source consistency, difficulty, ambiguity, and answer correctness with no issue
arrays. A missing, malformed, or negative review rejects the item.

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
