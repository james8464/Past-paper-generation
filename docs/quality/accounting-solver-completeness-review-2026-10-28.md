# Accounting independent solver completeness

## Reproduced failure

A fresh frozen-backend Accounting Paper 1 run used seed 270100 and the installed
Gemma 4 12B digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`.
It stopped at question 14.2 after 1,697 seconds, without publishing a paper.
The reviewer repeatedly found that the independent answer omitted the derived
£1,701,298 profit and did not apply the invoice and irrecoverable-debt figures.
All earlier accepted checkpoints and failure logs remain retained under ignored
`tmp/final-validation-20261028/accounting-live-quality-run2`.

The outer retry repaired the candidate question and scheme. Its blind solver
still received the same fixed public case and instructions, so another writer
attempt did not target the omitted solver evidence. Ollama documents seeded
reproducible requests in its [API reference](https://github.com/ollama/ollama/blob/main/docs/api.md#request-reproducible-outputs).
Changing a seed is not the repair used here.

## Bounded source-only repair

For the existing company-adjustment contract, the source-only arithmetic now
declares three required public numeric facts: profit for the year, the
irrecoverable debt and the supplier invoice. A valid solver envelope must use
their figures in its answer or steps, the fields actually shown to the content
reviewer. Values hidden only in mark points do not satisfy this pre-screen.

One additional blind solver request is permitted when those figures are absent.
Feedback names missing public roles and reuses the original public case. It
does not pass the draft marking key or the content reviewer's private expected
answer back to the solver. A second omission fails closed with bounded private
diagnostic evidence for both attempts. Invalid envelope shapes retain their
existing rejection behaviour.

The writer also cannot alter referenced source inputs or independent-solver
instructions before this check. Separate semantic and difficulty reviews remain
required. Numeric presence alone does not establish correct interpretation,
complete reasoning, marking quality or calibrated difficulty. Successful open
answers remain labelled `independent-model` and `semantic-review-only`.

Accounting prompt version is now `ai-assessment-v10-accounting-solver-completeness`.
Old V9 attempts are not relabelled, copied into a new acceptance sample or
silently approved.

## Evidence and remaining acceptance

Five initial regression cases failed against the old solver; two further tests
showed that changed public inputs and instructions reached the solver boundary.
The focused suite now passes 215 tests, including rejection after two omissions,
incorrect figures, mark-points-only figures and private-key canaries.

A focused live diagnostic of the revised question 14.2 solver returned and
reconciled all required figures in one model call. Prompts, raw response and
solution are retained in `accounting-solver-focused-live-run1`. It used source
implementation `23dcf71f9c7052c46e91df8ae83fcf78f21968fa69d2c2a1447d46937b3abeb3`;
the later explicit source-immutability guard was not part of that diagnostic.
This was one solver response, not a complete-paper or provider qualification.
Full fixed-source tests and a fresh complete-paper run remain required.
