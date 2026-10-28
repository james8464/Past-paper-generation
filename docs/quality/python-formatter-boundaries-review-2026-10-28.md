# Python formatter boundaries

This preparatory change configures formatting checks without formatting the
application while another source change is in progress. It does not establish
that the repository-wide formatting gate currently passes.

## Retained source

The 29 exact paths in `ruff.toml` are the union of source filenames consumed by
six raw-byte French catalogue producers: `tree_case_authoring.catalogue_digest`,
`system_case_authoring.catalogue_digest`,
`database_case_authoring.catalogue_digest`,
`synthesized_authoring.catalogue_digest`, `extended_pipeline._catalogue` and
`expanded_pipeline._catalogue`. The latter includes the retained V34 catalogue.
These exclusions affect the formatter only; existing lint rules still apply.

`database_case_prose._solution` also uses inspected algorithm source as printed
code, so formatting can alter correction content despite equivalent execution.
The relevant providers are already covered by this finite catalogue union.
Other French prose catalogues hash canonical data rather than raw source bytes;
there is no blanket exclusion for the French package.

`source_identity.implementation_identity` separately hashes all Core Python
files. Formatting maintained Core source therefore invalidates current runtime
identity and checkpoints and must precede a new source freeze and acceptance
gates. This does not justify excluding all Core files from formatting.

## Next integration step

After all executable edits freeze, format maintained Python and prove the AST
and literal values of each changed file are unchanged. Verify all 29 excluded
files remain byte-identical. Run the formatter check, the lint gate including
`bridge.py` and `conftest.py`, relevant tests and release gates against that
fixed source. No archived report or acceptance result should be relabelled.

Exact Swift-fragment and shell-delimiter tests are outside Python formatting.
Keep their behavioral assertions unless a separately reviewed change requires
them to move. Existing AST renderer-transaction tests must retain their ancestry
checks rather than being reduced to token presence.

## Evidence

Three new boundary tests failed before configuration. They check the finite
29-file union, both CI command scopes and continued Ruff lint selection of every
excluded file. Their red log is `tmp/formatter-boundaries-red.log`. This batch
changes configuration, tests and this review only, not executable application
source or historical catalogue bytes.

## Mechanical application after the coordinated freeze

The parent applied Ruff to the maintained scope after the prompt, checkpoint,
tooling and compatible naming work was committed. The retained proof compares
535 tracked Python files before and after the operation. Exactly 230 changed;
every compared syntax tree and literal-value sequence is identical, and all 29
excluded catalogue files are byte-identical. The proof is retained at
`tmp/formatter-preservation-20261028.json`; its baseline is recorded inside it.

The formatter check and lint both pass for Backend, Resources, tools, tests,
bridge.py and conftest.py. These checks establish mechanical preservation, not a
semantic review of every file or a performance improvement. Final combined tests,
packaging, replay and protected checks are still required. The consolidation
rebase changed no Backend, Resources, tools, tests, macOS, CI or Ruff bytes from
the formatting commit. Generated metadata will be refreshed separately.
