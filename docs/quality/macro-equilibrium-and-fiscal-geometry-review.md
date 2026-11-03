# Macro equilibrium and fiscal geometry

This bounded repair follows a Graphify query and actual current-source red
tests. It does not qualify a complete generated paper or clear every diagram.

## Reproduced defects

- The default AD/AS and Keynesian plots marked a stated equilibrium away from
  the intersection of their plotted curves. Public `eq_quantity` was ignored
  while the helper read only `eq_output`.
- Tax revenue and subsidy spending were shaded with incorrect polygons rather
  than the post-intervention quantity multiplied by the price wedge. Sampling
  a nearby grid point also displaced the equilibrium and welfare area.
- The PPF marker used array index 30 as its ordinate while labelling its
  abscissa 30. Those refer to different quantities on the sampled grid.
- A blank optional graph-kind string discarded otherwise supplied numerical
  parameters from both rendering and the candidate's source projection.
- PPF public dispatch passed `params` to a helper that did not accept it.
- Freshly rendered Keynesian and fiscal figures exposed curve/legend overlap.

The initial geometry file produced 28 failing tests. Additional targeted red
tests reproduced the blank-kind forwarding, PPF dispatch and three legend
placement defects before their repairs.

## Implementation

Macro curves retain their illustrative piecewise style but are scaled through
the declared positive price/output point. The exact point belongs to the sample
grid. `eq_quantity` and historical `eq_output` are aliases; conflicting values
are refused. Invalid, Boolean, nonfinite and unrepresentable scales refuse
before axes are created.

For the fiscal example, demand and original supply cross at P,Q, with respective
absolute slopes 2P/(3Q) and 5P/(6Q). A per-unit wedge t shifts supply vertically.
The exact new quantity is Q minus t/(1.5P/Q) for tax, or plus that amount for
subsidy. The fiscal rectangle extends from zero to that new quantity between
consumer and producer prices. The DWL triangle spans the old and new quantities
between the original curves. Intervention magnitudes outside this bounded
positive-price illustrative market refuse instead of producing invalid geometry.

The PPF point now evaluates the existing frontier at its actual quantity. The
frontier's existing illustrative functional form is unchanged; this repair does
not establish that its curvature is appropriate to every question context.
The helper accepts the existing public dispatch parameter argument. Numeric
graph parameters survive an empty optional kind in rendering and review evidence.
Legends for the three changed curve functions sit above, outside, the plot.

Edexcel's source-review identity is now
`edexcel-economics-v12-macro-geometry`. Tests refuse both v10 and v11 caches
without rebinding, deleting or changing their saved bytes. Historical evidence
is retained; it is not represented as acceptance of the changed images.

## Checks and limits

The final scoped run passed 105 tests: the new geometry/source-binding tests,
existing stimulus-diagram controls and Edexcel checkpoint-admission tests.
Maintained Ruff and formatting checks passed (625 Python files). The project's
existing four-file mypy gate passed; it does not type-check these legacy plot
implementations.

Nine actual PNG outputs were rendered for default/custom macro and fiscal
inputs and the PPF. All nine initial outputs were visually inspected; their
legend overlap led to the additional red tests. Four representative final
outputs were freshly inspected after the legend-only correction. The unchanged
PPF image was byte-identical between those visual runs. Mathematical tests
check all default/custom changed templates. Evidence stays under ignored
`tmp/nov3-macro-visual*`; it is not bundled in the app or repository.

An independent read-only reviewer inspected the production diff, caller binding,
tests and final legend-only delta and found no additional material defect within
that scope. This was not teacher review, a complete-file semantic attestation,
live-model qualification, a whole-code audit or an App Store approval.
Full fixed-source regression and protected publication gates remain required
before release. No model calls, answer substitutions or weaker quality gates
were used to make these deterministic plotting checks pass.

## Reviewed production identities

| File | SHA-256 |
| --- | --- |
| `Backend/Core/overlay/graphs.py` | `8306e6c693e35aba3a9e52870391154a57dfec967163af1c225730be6dcdf5cc` |
| `Resources/economics/edexcel-a/generator/pastpapergen/render_pdf.py` | `54fb76a083af7aafe69dd26c14640903cd7ef8b05ce2a6b10eec84abba606162` |
| `Resources/economics/edexcel-a/generator/pastpapergen/cli.py` | `a4e519076ac0afed11df6ec001bda153210569991334623f71519b3d1bda5308` |
