# Compatible Edexcel command branding

This selectively integrates the useful command-name intent of branch
`keldin-identifier-comment-cleanup` at `31ec4cd`, without copying its older
implementation files or changing immutable French catalogue bytes.

## Public surface

The new `keldin-edexcel` console command and `python -m keldin_edexcel` delegate
to the existing `pastpapergen.cli.main`. `keldin_edexcel.cli.generate_package`
is the existing callable, not a wrapper or duplicate implementation. Only this
CLI facade and the existing version string are advertised under the new package.
No new model classes or aliases for internal submodules are introduced.

The `pastpapergen` distribution, command, imports, model classes and registry
entry point remain unchanged. Both packages are included in wheel discovery.
The frozen helper explicitly collects the facade CLI; its imports resolve to
the existing implementation already collected from the unchanged registry.
Bootstrap paths and editable distribution requirements therefore need no change.

The original branch's wholesale implementation/package rename, generic phrase
ban, immutable French comment edits, historical documentation rewrites and stale
derived metadata are not integrated by this patch. This is not a claim that the
whole branch has been merged or can yet be deleted. Native internal-name changes
are a separate integration scope.

## Evidence

All five new tests failed before the facade/packaging changes, recorded in
`tmp/edexcel-branding-facade-red.log`. The focused facade gate then passed five
tests in 4.14 seconds, recorded in `tmp/edexcel-branding-facade-green.log`.
Tests assert exact old/new callable identity and equal fake console dispatch.
They build a wheel in a temporary copy using the already installed setuptools
backend, inspect both packages and console entry points, and import from that
wheel without installing it or accessing the network.

Both module names also generated deterministic layout previews with the same
paper ID and seed. All three PDFs' extracted page texts match. This establishes
command-path parity, not byte-identical PDFs, live AI quality or a renewed
educational qualification. No real model request was made. Existing saved IDs
and registry implementation bindings are asserted unchanged.

The related gate including existing Edexcel CLI, registry and fake build-script
integrity tests passed 27 tests in 8.49 seconds, recorded in
`tmp/edexcel-branding-facade-related-green.log`. Existing implementation files,
the registry and French source have no changes from this integration.

Ruff, shell syntax and whitespace checks pass. The hidden-import declaration is
tested statically; a newly frozen application build has not been run by this
batch. Parent integration still requires packaged import and release gates.
