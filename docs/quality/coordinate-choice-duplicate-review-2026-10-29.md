# Reordered account-option duplicate gate

A fresh retained Qwen probe supplied both “The sale increases the asset account and the revenue account.” and “The sale increases the revenue account and the asset account.” These are the same shared-predicate conjunction, not distinct answer options. The independent model still reported a single valid choice. That is evidence for a narrow deterministic check, not evidence that a general semantic-equivalence detector is reliable.

Candidate admission and restored-checkpoint validation now share a conservative option identity. An exact normalised prefix ending in `increases` or `decreases`, followed by two definite account noun phrases joined by `and`, identifies the same option when those two account phrases are reversed. Other sentences retain the previous case/whitespace identity. This does not reorder separate debit/credit clauses, change predicate direction, ignore arbitrary word order or claim to detect all equivalent distractors. Source-owned options receive the same duplicate check without changing their keys or content.

Two red tests reproduced acceptance of the live duplicate pair through fresh candidate construction and checkpoint revalidation. Both are green after the fix. Opposite debit/credit directions, different increase/decrease predicates and directional prose remain distinct. The shared review version advances to `assessment-review-v9-coordinate-choice-duplicates` so new jobs cannot inherit a pre-gate checkpoint identity. Historical evidence is retained unchanged.

This check complements the required independent choice-validity signal and existing numeric, marking and key reconciliation. None of those gates is replaced or weakened. No model or user-interface call was made for these regressions.
