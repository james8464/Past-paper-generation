# French NSI V27 marking alignment

## Scope and design

V26's 3l asks candidates to compare two deadlines and explain two security limits. For the 0.5-point profile, its quarter-point rubric silently drops the compromised-terminal criterion. The 0.75-point profile already credits all three criteria.

V27 retains the timing facts, materials, three independent exercises and exact 18 technical plus 2 indicative language points. Question 3j continues to assess metadata. Revised 3l asks for both deadline comparisons and the compromised-terminal limit, without asking or crediting metadata again. Its answer explains exposure before encryption or after decryption. The 0.5-point profile credits both comparisons together, then the terminal limit. The 0.75-point profile credits each comparison separately, then the terminal limit. No security conclusion receives duplicate credit across 3j and 3l.

The revised prose catalogue has a separate version and digest. New generation selects V27; V26 generation, evidence and replay retain their original semantics. Selection evidence binds the version and candidate hash. Runtime PDF validation and benchmark acceptance select the corresponding revision, rejecting mixed identities.

## Verification plan

1. Reproduce the missing-credit defect with tests across three seeds and both wording/rubric forms.
2. Verify all requested conclusions are credited exactly once and totals remain unchanged across both point profiles.
3. Exercise V26/V27 package replay, tamper rejection, runtime publication and benchmark identity checks.
4. Run full backend and protected macOS checks, then inspect a new pinned live run separately.

## Limits

This is a marking fix, not a claim of official equivalence or a new live evaluation. V26's recorded manual fidelity HOLD remains historical evidence. Candidate depth, question progression and layout still need assessment against real papers. Official papers also contain sparse pages; neither blank padding nor matching a page count establishes quality. Teacher calibration and document-specific rights clearance remain open.
