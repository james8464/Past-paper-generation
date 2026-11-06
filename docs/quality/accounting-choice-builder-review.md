# Accounting choice-builder review

The complete 139-line `aqaaccountgen/selected_response.py` was reviewed at
SHA-256 `906e718ec91c91275f9da9bebd132b5530c42c79ebde0e80de4e79584acfa5ad`.
Its four cases cover carriage and gross profit, sale or return, credit-sale
correction and net share premium. Each passes its printed public inputs to the
existing derivation helper; the derived answer supplies the key after shuffling.

Within the builder's ranges, the three carriage adjustments have disjoint
values. Positive cost and mark-up separate the sale-or-return alternatives.
Share premium exceeds issue costs; the smallest relevant price-gap amount is
£5,000, above the maximum £3,000 cost. These bounds prevent the numerical
distractors from matching the answer or one another. The journal case uses the
helper's four distinct entries. Construction also checks option uniqueness.

Randomness uses the supplied generator. The scoped caller supplies a separate
versioned seed for each case while preserving its previous draw sequence.
Relevant existing tests and helper/caller sections were inspected, not run.
No deterministic defect was found in this bounded review. It does not resolve
the separate conceptual Q06 semantic-review limitation or establish live paper
quality, a complete Accounting audit or release-build acceptance.
