# French NSI V27 marking alignment

## Scope and design

V26's 3l asks candidates to compare two deadlines and explain two security limits. For the 0.5-point profile, its quarter-point rubric silently drops the compromised-terminal criterion. The 0.75-point profile already credits all three criteria.

V27 retains the questions, answers, timing facts, materials, three independent exercises and exact 18 technical plus 2 indicative language points. It groups both security limits into the second quarter-point criterion only for the 0.5-point profile. The first criterion still credits both deadline comparisons. The 0.75-point profile remains unchanged and does not double-credit either security limit.

The revised prose catalogue has a separate version and digest. New generation selects V27; V26 generation, evidence and replay retain their original semantics. Selection evidence binds the version and candidate hash. Runtime PDF validation and benchmark acceptance select the corresponding revision, rejecting mixed identities.

## Verification plan

1. Reproduce the missing-credit defect with tests across three seeds and both wording/rubric forms.
2. Verify all requested conclusions are credited exactly once and totals remain unchanged.
3. Exercise V26/V27 package replay, tamper rejection, runtime publication and benchmark identity checks.
4. Run full backend and protected macOS checks, then inspect a new pinned live run separately.

## Limits

This is a marking fix, not a claim of official equivalence or a new live evaluation. V26's recorded manual fidelity HOLD remains historical evidence. Candidate depth, question progression and layout still need assessment against real papers. Official papers also contain sparse pages; neither blank padding nor matching a page count establishes quality. Teacher calibration and document-specific rights clearance remain open.
