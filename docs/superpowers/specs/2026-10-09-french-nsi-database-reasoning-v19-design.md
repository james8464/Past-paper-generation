# French NSI database reasoning V19 design

Status: implementation design within the approved French scope, 9 October 2026. It is not an educational or accessibility approval.

## Purpose and boundary

The pinned V18 written-paper diagnostic passed automation but remains on manual fidelity hold. Its Exercise 2 displays the data and faulty code on one page, then fits all ten questions on the next. The official 2026 Métropole middle exercise develops a different topic over five pages through linked figures, code and reasoning. Its page count is a comparison signal, not a 2027 target. The goal here is to deepen our original database reasoning, not to pad pages or copy the official task. Official papers do not provide response boxes, so adding empty answer space would not solve this gap.

V19 changes only Exercise 2 authoring and presentation. The existing six-incident, three-table V2 database contract remains immutable and usable for V16–V18 package replay. Exercises 1 and 3, UK routes and saved state remain unchanged. The written component remains three independent exercises, 210 minutes, exactly 18 technical points plus a distinct two-point indicative French-language component. The practical component is unsupported.

## Ten linked tasks and exact evidence

V19 retains the app-owned V2 incident facts, faulty join, corrected join, aggregation, single-row update and faulty Python counter. A new finite French prose catalogue and explicit `fr-nsi-written-2027-v19` route replace only the Exercise 2 wording, expected explanatory steps and indicative criteria. The model selects registered scene, question and rubric IDs; it cannot author SQL, code, facts, answers, marks or free-form instructions.

| Phase | Questions | Candidate work and application-owned evidence |
|---|---|---|
| Integrity and joins | 2a–2d | Identify primary/foreign keys and their constraint; reject incident 107's invalid agent reference and name a valid replacement; trace incidents 101 and 102 through the correct join; compare their faulty-join rows with their true categories and isolate the wrong join condition. |
| Query construction | 2e–2f | Write the corrected ordered join and account for its six rows; write a left-join grouped count and explain why a newly inserted category with no incidents would still appear with count zero. The hypothetical category is explicitly separate from the locked initial tables. |
| State and debugging | 2g–2j | Update only incident 101 and calculate before/after closed totals; write an assertion exposing the supplied function's initial-state error and trace its return; correct the condition and calculate both initial and post-update returns; test the empty-list boundary and explain why no first-element access is needed. |

Every requested value is deterministically derivable from the printed six rows or from the explicitly stated hypothetical. SQLite computes the join, grouping and update facts in the V2 contract. The Python trace is interpreted from the printed bounded function; no model-authored code is executed. A teacher can inspect the derivation and alternative valid SQL, but automated validation does not certify every equivalent answer.

The ten questions retain the existing 70-minute budget and E2 technical allocations of 5.5, 6 or 6.5 points. Each prompt and its indicative rubric must ask for and credit the same finite steps; quarter-point subcriteria are permitted, exact decimal arithmetic is mandatory, and no rubric may silently demand more evidence than the prompt. The separate French-language component remains unchanged. These marks and timings are provisional pending independent NSI teacher and learner calibration.

## Version, rendering and rejection rules

- V19 has its own finite prose catalogue digest, prompt/schema identity, checkpoint and package replay dispatch. A V19 package cannot replay as V18 or use V18 catalogue IDs. V13–V18 packages remain readable through their original contracts and catalogues. Unknown versions fail closed.
- Present three clearly labelled phases near their questions. Keep the incident tables and supplied faulty SQL/Python visible and legible, without printing expected answers in the subject. Normal and large-print layouts must keep each question and its relevant phase heading together; proposed-correction answers and indicative credits remain attributable.
- PDF verification checks all V19 labels, the six printed incident facts, the faulty source snippets, the expected values and the distinct credits. It rejects a missing or interchanged explanation, an unstated hypothetical treated as an initial fact, answer leakage, and a wrong catalogue or source digest.
- French-only reference retrieval, holdout isolation, no UK fallback, local privacy and non-official subject/proposed-correction labels are unchanged. Preserve every failed attempt and accepted checkpoint.

## Evidence gates

Test each allocation and multiple seeds, V18/older French replay, UK route/state stability, normal and large-print page bounds, and adversarial PDF omissions before protected integration. Inspect every fixture PDF page against the official comparator using the PDF skill; fixture success is not live evidence. After merge, run one pinned French live diagnostic, retain all identities and hashes, and compare every generated PDF page to the official source. The expensive final UK/French matrix remains deferred until shared source freezes and manual fidelity passes. Teacher review, learner timing/mark calibration, document-level rights and accessibility remain external gates.
