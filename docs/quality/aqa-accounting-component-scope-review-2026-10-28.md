# Accounting component scope review

## Findings and repair

The current source, not an old retained model output, reproduced three defects. The allowed topic sets disagreed with the official components. Questions 7 and 9 both calculated gross profit by subtraction. When a task's intended topic was unavailable, the generator silently assigned another allowed topic. The bookkeeping-system decision also carried an incomplete-records or investment-appraisal label despite asking about information systems.

Nine focused tests failed before the repair. Each component now has its own ten-task MCQ bank. A task carries its topic beside its stem, answer and distractors. The generator rejects an unavailable topic rather than relabelling the task. The bookkeeping decision uses topic 1, which explicitly covers accounting information systems and oversight of bookkeepers.

Paper 1 retains one gross-profit calculation and replaces the duplicate with a share-premium calculation. Paper 2 instead calculates a cash-budget closing balance and contribution per unit. Independent tests derive the four answers from the printed inputs over 100 seeds per component and require four distinct options. The gross-profit-margin formula retains its percentage multiplier. The component-specific checkpoint prompt version changes, and the complete generated blueprint remains part of checkpoint identity.

## Official scope

[AQA's assessment specification](https://www.aqa.org.uk/subjects/accounting/a-level/accounting-7127/specification/specification-at-a-glance), checked on 28 October 2026, assigns topics 1 to 8 and 14 to 18 to Paper 1, and topics 1 to 3, 8 to 13, 17 and 18 to Paper 2. Both components have 120 marks over three hours, with section totals of 30, 40 and 50. These mark and duration rules are unchanged.

The [role of the accountant](https://www.aqa.org.uk/subjects/accounting/a-level/accounting-7127/specification/subject-content/an-introduction-to-the-role-of-the-accountant-in-business) supports the information-systems mapping. The [financial analysis specification](https://www.aqa.org.uk/subjects/accounting/a-level/accounting-7127/specification/subject-content/analysis-and-evaluation-of-financial-information) includes gearing in topic 8. Gearing is therefore not automatically outside Paper 2; the task's demand and actual binding matter.

The source templates do not cover every topic allowed in Paper 1. In particular, this bank does not independently assess topic 2 or topic 14. The previous test mistook random topic labels for coverage. Its scope assertion now checks that actual tasks remain within the official component, while separate tests verify the intended topic of each MCQ. This repair makes no full-curriculum claim.

## Printed source review

The diagnostic uses seed 270100 and the application source templates without an AI writer. Four PDFs and their hashes are retained in `tmp/pdfs/accounting-component-scope-20261028/run-2/summary.json`. Every MCQ stem, option and answer-key entry is checked against extracted PDF content. The eight subject pages containing the MCQs and both correction pages containing their keys were rendered and visually inspected. No clipping, overlap, missing multiplier or mismatched option/key was found on those pages.

The initially retained diagnostic stopped because its inspection script expected Paper 2 to use Paper 1's answer-table heading. Paper 2 prints the questions and their keys together. The corrected inspection selects that actual page and checks all ten entries. Both attempts remain available.

The printed seed has Paper 1 gross profit of £130,000 and share premium of £80,000. Paper 2 closing cash is £70,000 and contribution is £20 per unit. Each is the uniquely keyed option. Layout elsewhere is not newly certified by this scoped review.

Changing the seeded MCQ calculations also changes later random draws. One independent-solver regression therefore encountered different, valid financial-statement inputs. Its four hardcoded expected amounts were recalculated from the new visible inputs, with the workings kept beside the assertions: inventory write-down £22,344, irrecoverable debt £144,877, and debenture interest of £34,146 and £61,273. No solver comparison or reconciliation check was removed.

## Acceptance limits

The focused Accounting suite passes 54 tests. This is a source-template and component-scope repair, not a live MLX or Ollama qualification. Model-authored question quality, complete-paper reasoning, empirical difficulty and every-page final live review remain part of the release checklist. Issue 12 is not closed by these checks alone.
