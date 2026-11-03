# Numeric evidence and source-booklet padding integration

This combines two bounded repairs on top of the macro-geometry candidate.
It is not a complete paper, provider, implementation-audit or Store approval.

## Included changes

- Exact, bounded positive floating-point encoding replaces normalization using
  ambient Decimal precision. The mathematical and caller-context checks are
  recorded in `cs-floating-exactness-review.md`.
- Numeric evidence advances to `closed-numeric-v3-exact-floating`. Old numeric
  solutions, model reviews and family checkpoints refuse without rewriting
  their retained bytes. Manifest metadata uses the same shared constant.
- Deliberately padded Edexcel source-booklet leaves now display `BLANK PAGE`.
  Existing four/eight-page targets and every actual source page are retained.
  The PDF validator records trailing label-only leaves after normal checks;
  there is no new empty-page exception. See
  `edexcel-source-booklet-padding-review.md` for the narrow scope and controls.
- Edexcel's adapter identity advances to
  `edexcel-economics-v13-source-booklet-padding`. Retained v10, v11 and v12
  checkpoints are rejected rather than rebound to changed presentation.

## Integration checks

The combined targeted run passed 665 tests with five existing PyMuPDF warnings.
It covers both new numeric files, source padding, PDF validation, CS and
accounting objectives, shared numeric evidence, model review, reference demand,
checkpoint preservation, package metadata and Edexcel solver/source controls.

A separate root check encoded all 1,024 positive normalized values of the
8-bit-mantissa/4-bit-exponent format at ambient Decimal precision two. Every
result matched its independently decoded coefficient/exponent bits.

An additional integration run found one positive Edexcel test that still
asserted literal v2 evidence. Its genuine red result was one failure and 57
passing controls. The test now requires the shared current version, retaining
its source-projection and reconciliation assertions; all 58 controls pass.
Historical v2 rejection cases remain unchanged.

Maintained Ruff and formatting checks passed for 628 Python files. The configured
four-file mypy gate passed; this does not claim typing coverage of every edited
legacy module. Both author lanes and root performed scoped source reviews.
Whole-file audit rows are refreshed normally, not certified by this delta.

Private commands and outputs remain under `tmp/nov3-combined-*`; the source
reports retain their original lane-specific results and counts. These are
owned deterministic tests, not model authoring or classroom observations.

One clean, fixed-source full regression and both latest protected checks are
still required for the combined candidate. Packaging, signatures, native
installation and Dropbox replacement are separate release gates. No older
build or macro-only result is represented as acceptance of this combined tree.
