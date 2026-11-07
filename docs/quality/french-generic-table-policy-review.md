# French V36 generic table print policy

## Confirmed boundary and repair

The current model-authored schema accepts tables with 2–8 columns and 1–30
rows. The shared renderer instead selected fixed legacy column/row geometry
from three material IDs alone: `trace_initial`, `trace_fermeture`, and
`route_double_fermeture`. A valid two-column/two-row outage table raised
ReportLab's row-height-count error; the identical ordinary-ID control passed.
This was one genuine failing constructor test and one passing control, without
a model, network, PDF, or inference. The retained RED log is
`tmp/nov7-french-table-id-red.log` (SHA-256
`925a677800ea0e63d35394e1db57b7d278686eab43a313ab0846e71b7683d66f`).

Current V36 print policy is now `fr-nsi-v36-model-review-v5`. Its host-derived
table-layout flag selects the existing dimension-derived equal/measured
columns and automatic row heights, independently of material IDs. No model
field, schema ban, answer, mark, prompt, or validation limit changed.
Default/direct callers and V34/V35/V36 v1–v4 retain their old table geometry.
Explicit v4 and v5 membership preserves v4 foreign-edge-safe graph geometry
in both rendering and post-render validation; older graph policies are unchanged.

The current alias already supplies generation/recovery identity and strict
package validation. Recovery evidence rejects stale print policies; old package
identities are not relabelled or silently replayed as v5. The implementation
identity hashes Core source bytes (the executable in frozen mode). Native
publication validation uses the same new v5 identity and explicitly tests old-v4
refusal. This does not delete saved packages or modify their PDFs.

## Focused verification

The first complete focused group passed **42 tests in 1.23 s**, including four
actual v5 PDFs and seven retained/current graph-policy PDFs. A subsequent
pure-only group passed **32 tests in 0.61 s**, adding the recovery-evidence
version-binding control; it overlaps the earlier group and is not additive.
Together these cover 43 distinct cases. Ruff check/format and diff checks pass.
Native tests were edited but not executed; no native build or full suite ran.

The four synthetic v5 documents cover question paper/mark scheme in normal and
enlarged print, with all three colliding table IDs. Their 24 pages were rendered
by Poppler at 85 dpi and visually inspected through six four-page sheets; no
clipping, overlap, or broken table rows was observed in this packet. The other
seven PDFs support automated historical/current policy controls, not an asserted
fresh every-page visual review. Artifact hashes are in the ignored fix receipt.
These synthetic cases do not prove all valid 30-row tables fit every page,
whole-paper content quality, model capability, official equivalence, or native
acceptance. No live model/provider, GUI, full suite, or build was used.

## Frozen source and review attribution

- `print_policy.py`: `2a2c0133bb2e4bb2705a4b35a70c2c68f7ac6992a26d8a170ec267be6eb857be`
- `rendering.py`: `a1f993e6e7e6478b62df10296321b81736de9ca23fdffd2bb9b0ca63d248289b`
- `llm_pdf.py`: `e4a75c8bcf5cdee7c58f51caa8a26489c3349b770e6fad3736f9cfaf17e723c4`
- New policy tests: `cc4bd4466efeac0b727276ea594349451c4af79f8125cda11b252ba875189c4b`

Renderer baseline full EOF (1,210 lines, SHA-256
`bcca2bbebac1444f2435c4fd4e258c73532451aac062ca3e4765ba2f4b1f2be9`)
plus this complete narrow delta is composite review, not a fresh full-current-EOF
claim. `whole_case_pdf.py` was separately read through all 273 lines and is
unchanged. Other dependency and native test reads remain scoped as recorded in
the ignored EOF/fix receipts. The separately reviewed publication-cleanup batch
is preserved byte-exact and is not new table-policy evidence.
