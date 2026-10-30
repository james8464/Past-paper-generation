# French V36 Gemma reasoning-enabled diagnostic

## Pinned attempt

Exactly one public-source attempt ran with `gemma4:12b`, seed 270100, at
`da838cec471eabea94ee9234cc872e5ebeacc512`. The model digest was
`4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`.
Source and model identities were unchanged before and after the run. The
separate local Ollama session allowed one request at a time and used the
model's default reasoning setting. The normal user session was not reconfigured.
No hosted request or payment was made.

The attempt took 1,887.04 seconds and made seven provider calls. All returned
normal stop reasons, not length or context failures. No complete paper or PDF
was published. This was a live model attempt, not catalogue or checkpoint replay.

Retained private evidence is under
`tmp/french-v36-live-20261029/gemma4-12b-run-2/`. Each call has its request,
raw response and metrics. `result.json` records the return code, timings,
response hashes and before/after identity checks. The first rejected response
and the earlier reasoning-disabled attempt remain retained separately.

## What failed

The first exercise initially failed its exact six-point allocation. The existing
single structural regeneration produced a replacement; blind solving and model
review then admitted it. This is not an independent educational approval. The
replacement's four tasks mainly involve dictionary lookup, spotting a misspelled
variable, a nearest-point loop and a recursive type guard. Assigning difficulty
labels or 70 minutes does not establish sustained examination demand.

The second exercise's proposed debugging correction still calls `explorer(visin,
...)`, although the loop variable is `voisin`. Thus its supposed corrected code
retains an undefined name. Its explanation also misidentifies the affected
argument and calls this a syntax error rather than a name-resolution error.
The proposed answer and blind solution both make an unsupported blanket claim
about infinite recursion. With finite positive edge weights and a finite budget,
the budget bounds recursive path depth, although inefficient repeated exploration
or a recursion-limit failure can still occur.

The final model review sets its correctness flags to true but reports a nonempty
issue for that question. Publication correctly refuses on the issue. The existing
rule was not relaxed, the answer was not patched, and the accepted first exercise
was not substituted for a complete paper.

This establishes a real answer-quality failure, not merely a hidden metadata
convention or an overly strict subjective difficulty label. Same-model blind
solving and review missed part of the defect. They are evidence to inspect, not
mathematical proof.

## Engineering follow-up

The refusal previously surfaced only a generic error. A separate tested change
retains bounded question-specific findings in private diagnostic records and
names the exercise/question and a plain-language category in the visible error.
It does not add semantic retries, modify a question or weaken any gate.

No page-by-page comparison is possible for this attempt because it produced no
PDF. The official comparator, syllabus, historical accepted rendering checks,
teacher-review absence and lack of learner timing remain separate facts. A
stronger-model attempt must use its own pinned identities and fresh evidence.

## Separate native interaction smoke

The development-signed direct candidate built from `da838cec` was also launched
through computer control. The French workspace displayed the selected model and
the distinction between memory fit and incomplete quality evidence. Cancelling
the hosted-provider disclosure restored Ollama without accepting consent. The
MLX parallel switch was toggled and its original off setting restored; the saved
3B model's Accounting warning remained visible. Original provider/model settings
were preserved.

Cmd-Return started a genuine French request. Documents and History opened while
its progress indicator and Cancel remained available. Cancellation changed the
new job to Cancelled, left its artifact list empty and restored French creation
controls. Cmd-P in History did not open a print panel. Existing user history was
preserved; the test added one cancelled record. Private observations are in
`tmp/final-validation-20261029/native-v36-interaction-review.json`.

These checks concern a source candidate and cancellation, not the final installed
release or a completed paper. They do not establish full interaction coverage.
