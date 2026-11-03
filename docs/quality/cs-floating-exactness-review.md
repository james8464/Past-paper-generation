# Bounded CS floating-point encoding

The previous encoder used ambient Decimal arithmetic to normalise a positive value, then treated an integral scaled mantissa as evidence of exact representability. At ordinary precision, a decimal just above 0.5 could round to the same mantissa as 0.5. Exponent bounds were checked after repeated normalisation, allowing excessive work for values far outside the declared format. These are owned implementation reproductions, not observed failures in generated papers.

The encoder now reads the exact decimal coefficient and exponent. Width-derived coefficient and magnitude bounds are checked before allocating integer powers or ratios. Bounded integer comparison, shifts and division then determine the normalised exponent and exact mantissa. A nonzero remainder refuses the source. No generated program is executed and no global Decimal precision is changed. Decimal parsing uses a temporary context so an invalid spelling does not change the caller's signal flags.

The existing domain remains positive finite values, 2–16 mantissa bits and 2–8 exponent bits. Zero, negative values, unsupported types, out-of-range values and nonrepresentable fractions still refuse. Positive mantissas retain a zero sign bit and exponents retain their declared two's-complement width. Equivalent decimal spellings and insignificant trailing zeroes remain valid. The current OCR factory's 6.5 example remains `01101011`.

The coefficient limit is conservative, not a new arbitrary numerical threshold. A representable source has the form `M * 2**(e - (mantissa_bits - 1))`. Its canonical decimal coefficient has fewer than `2 * mantissa_bits + 2**(exponent_bits - 1)` digits. Together with the magnitude check, the supported widths bound subsequent integer-power construction. Parsing and stripping an already supplied decimal string remain proportional to its length; this does not claim constant-time handling of unbounded input strings.

## Evidence

- `tmp/nov3-cs-floating-exactness-red.log`: three genuine failures and 18 passing controls on the old encoder. Two failures show ambient rounding; the third hits an owned 32-operation budget on the modest input `1e-100`. No enormous old-source exponent was executed.
- `tmp/nov3-cs-floating-exactness-final-focused.log`: 303 passed, five existing PyMuPDF warnings. Controls include 16 width combinations at the smallest, zero and greatest exponents with two mantissa endpoints, low ambient precision, padded decimals, sNaN, large exponent strings and an allocation-order trap. The large-string cases run only against the repaired guard.
- `tmp/nov3-cs-floating-evidence-version-red.log`: three version-bound failures before the version change. The old canonical was accepted; saved review passed the integrity check and failed a later profile check; the real OCR adapter reached the forbidden resume callback.
- `tmp/nov3-cs-floating-evidence-version-green.log`: those three cases passed after the version change.
- `tmp/nov3-cs-floating-version-final-focused.log`: 513 passed, five existing PyMuPDF warnings, in 3.80 seconds. This covers both new files, CS objectives, shared numeric integrity, model review, reference demand, checkpoints and publication-manifest controls. No full suite or release build was run in this authoring lane.

Imports in the exactness test assert the owned checkout's source path. Focused commands use the primary environment's interpreter with `PYTHONPATH=.`. No provider or model is invoked.

## Evidence and checkpoint compatibility

Shared numeric evidence advances to `closed-numeric-v3-exact-floating`. Canonical reconciliation and saved difficulty review already enforce that shared version. Family checkpoint identities include it alongside the blueprint, provider, model and review version. The regression calls the real OCR adapter and proves a v2 checkpoint is refused before resumed authoring, without changing its bytes; it remains readable using its original identity. Existing artifacts are not rewritten or relabelled.

UK checkpoint identities are version- and blueprint-bound, not universal source-file hashes. The new shared version is therefore necessary; changing the helper alone would not invalidate all prior acceptance. The package manifest's former hardcoded v2 label now uses the same shared constant. Positive current-version fixtures use that constant; historical refusal fixtures retain their old versions.

## Review scope and limits

The author read the complete 288-line baseline CS contract file and every final change, and the complete 292-line numeric integrity file plus its one-line version change. Both new test files were read completely. Generation manifest, checkpoint, model-review and solver callers were inspected selectively. Root independently reviewed the arithmetic bounds and production delta; this is not a fresh whole-file review of the dispatcher or every dependency.

The configured four-file mypy gate passes. A separate leaf check retains an existing inferred-result indexed-assignment error, now at line 317. The same statement failed on the baseline at line 286; five additional baseline branch-inference errors disappear with the extracted helper. No ignore, cast or unrelated result-type edit was added. Lint, formatting and final metadata checks retain their own logs.

Whole maintained-Python Ruff check and format check passed (626 files). The final exactness/version and inventory tests passed 98 cases with five existing warnings in 1.75 seconds (`tmp/nov3-cs-floating-final-metadata-tests.log`). Normal audit refresh leaves whole-file review rows pending and invalidates the dispatcher's old source-hash attestation. The AST-only Graphify update produced 13,417 nodes and 39,305 edges, retaining 49 known zero-node resource warnings; no API or semantic extraction was used. The inventory records 1,177 files: 231 reviewed, 612 pending and 334 excluded. None of those counts proves pending code defective or completes a whole-project review.

| Maintained source | Lines | SHA-256 |
| --- | ---: | --- |
| `Backend/Core/subjects/computer_science_contracts.py` | 319 | `ba73d680f5694fa30d4bd6c425b8a2317a35f43dede08e1361cf65232ed5e205` |
| `Backend/Core/numeric_integrity.py` | 292 | `4c409fd99e2bd34e2b4cb5e773884c616ed3b696050a0bab0074e43ed972a14a` |
| `tests/test_cs_floating_exactness.py` | 169 | `d879e1ecfee8f5caca03dd98541683c66add6ced6b2bf3d06b87610eb60fed8f` |
| `tests/test_cs_floating_evidence_version.py` | 139 | `fab13f6cb616cd5e9d75250d6a46bfe0a1cd30d72dbc7e8a4203b9b1d97df02a` |

The selectively reviewed dispatcher delta has SHA-256 `19b000ee43e7deb47b06e515796b4561bc5c04c73eaf1920a53048d67acb8e45`; it is not included in the complete-file scope above.

This review does not qualify a complete paper, model answer, difficulty estimate or live provider route. Protected checks, combined-source tests and packaging remain separate release gates.
