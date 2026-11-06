# Reference distributions and fixed text slots

## Review scope

The reference-demand reviewer read the original 867-line implementation through
EOF. The author, root and an independent reviewer then reviewed its two-line
collision check and the complete new 82-line tests. Root reviewed those changes,
not the complete original module. The same reference reviewer completed the
existing 816-line tests in a later EOF supplement; the earlier selective-test
receipt remains historical.

The layout reviewer read the original 492-line implementation and existing
430-line tests through EOF. The author, root and independent reviewers reviewed
the repair deltas and final 232-line tests. The current implementation has 540
lines, a net increase of 48. Root did not read the complete original module.
These source-bound reviews combine an unchanged original-file read with its
complete subsequent deltas.

Separate completed EOF reads covered the unchanged 568-line open-credit module
and its 967-line tests, and the unchanged 450-line marking-enrichment module and
its 159-line tests. Their callers were inspected selectively, without a complete
dependency audit. Prior audit attributions and exclusions remain unchanged.

## Reference distribution admission

The six declared distribution fields previously checked that their input mass
totalled one, then casefolded keys into a new dictionary. A pair such as `HIGH`
and `high`, each carrying 0.5, overwrote one value and left a validated
distribution totalling 0.5. The shared validator now refuses casefold collisions
before conversion. Single mixed-case keys still normalize with their original
mass. The finite, nonnegative and total checks, rounding, source fingerprint
format and profile policies remain unchanged.

The new tests produced six failures and 32 passing controls before repair. The
final reference group passed 102 tests. Checked-in profile serialization retains
SHA-256 `1841185823e63a401af1137fb684f4b2b713edd95b1ecb9d0d484d390abb07d1`,
including the existing source fingerprints. Canonical publication still checks
profile contents against the current checked-in record. No current checked-in
profile collision or native paper defect was established by this owned fixture.

## Fixed-slot fitting

The helper now measures the first token as well as later tokens, retries a width
refusal at allowed smaller fonts, and checks typography for finite positive
values. It tries the exact declared minimum even when that minimum lies between
quarter-point steps. An impossible fit refuses before drawing; unknown-font
errors still propagate as font errors.

A descending quarter-point loop could require billions of probes for a large
finite starting font. The replacement uses a binary search over the same grid,
with its exact minimum as the final endpoint. Rational grid arithmetic preserves
small candidate sizes when the starting size and grid index are large. It adds
no arbitrary font cap, token splitting or width tolerance. The search assumes
ordinary font metrics: shrinking a font cannot increase measured line width or
wrapped height. Custom nonmonotonic metrics are outside this guarantee.

The retained progression records distinct findings: initial width/typography
tests produced 15 failures with 12 controls passing; off-grid endpoint tests
produced two failures with two controls passing; a bounded resource canary
failed; and five genuine large-grid precision cases failed at zero-origin slots
while the 2.0-point control passed. The earlier floating-grid CLEAR and the
earlier x0=10 precision log are superseded evidence, not final acceptance.
The final layout group passed 148 tests. The reference and layout totals are
separate groups, not a full-suite result.

Repository caller inspection found this fixed-slot drawing helper in its own
definition and tests, with no current default native renderer caller. These
repairs establish helper behavior, without claiming a saved-paper defect was
repaired or a current paper visually qualified.

## Unchanged modules

Open credit remains scoped to the declared two-criterion AQA stored-program
contract. Its typed allocations, quote presence and item/solution identities
remain checked. Printed scheme meaning is model-semantic adjudication; quoted
text and recomputed content hashes do not prove general entailment or external
authenticity. The review found no new structural or replay bypass in that scope.

Marking enrichment was read with its existing tests and selected current
generator callsites. No new concrete reachable defect was established. This
does not establish equivalence to official level grids or correctness of
arbitrary generated marking prose.

## Exact reviewed files

| File | Lines | SHA-256 |
| --- | ---: | --- |
| `Backend/Core/reference_demand.py` | 869 | `3066ce169e5c8b254d4ac265be499d8a3e68e5dfe81df24e6698113c5f3ac95c` |
| `tests/test_reference_distribution_keys.py` | 82 | `1b1452fac4c583b64973c05d222a6d4ddf6ea24c6696ac2941fea05d1a9438bb` |
| `Backend/Core/layout_master.py` | 540 | `206f00003ea5a1011133269722d7129fae5640d9a1f8e024924fb3878ba512fb` |
| `tests/test_fixed_slot_width_guards.py` | 232 | `597b3fccbb4502282c8d43e08b807988e96777a83066d65fc11f6082d73682d5` |
| `Backend/Core/open_credit.py` | 568 | `6d588bd5548f9bc89939f7ce638088e837590924f2d3ed9c4b8fd3e895a9ebfe` |
| `tests/test_open_credit_reconciliation.py` | 967 | `3db195b54167e9d080d36c41e9698c7d673a6febe7f839acc51d9d1ad8e6af22` |
| `Backend/Core/mark_scheme_enrichment.py` | 450 | `7dfe05ef68c9fb89aeeed8d932ae34859f1f389b36cbf85925dd74f9be201719` |
| `tests/test_mark_scheme_enrichment.py` | 159 | `dcd8d924b8460bb2d487afdd30daacba223a90a7f7ddee67b74bd248e769cfca` |
| `tests/test_layout_master.py` | 430 | `2d60006de9f0de5bb84994ff6fbba99c537bb4ed8040eb635ca40b17d4b1de0f` |
| `tests/test_reference_demand.py` | 816 | `30bec137b8cfe3e3b03018c41538de47504f4445d3886dda5a4a17ec42a4fc86` |

No provider/model call, new paper rendering, native interaction, full-suite or
release build forms part of this review. Expected demand and timing targets are
not observed learner calibration. No teacher review, full project audit, Store
approval or generated-paper quality guarantee is claimed. Graph and inventory
updates record relationships and coverage only.
