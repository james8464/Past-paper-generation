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

## Editable console integration follow-up

Module tests with a repository PYTHONPATH did not prove bare console entrypoint
startup. Two new console-script-shaped subprocess tests reproduced both names
failing to import Backend from an unrelated working directory with PYTHONPATH
cleared. A third pure-package import test already passed. The red log is
`tmp/edexcel-console-runtime-red.log`.

The shared legacy CLI now imports a narrow bootstrap before Backend imports.
It adds only the exact enclosing Keldin checkout after verifying the expected
generator layout, Backend adapter and registry exist. It does not scan the
working directory, install anything or copy Core into the generator. Both new
and old commands still expose the same callable objects. Importing their package
roots alone does not perform the bootstrap. Detached generator packages refuse
with an actionable runtime requirement; the wheel alone remains non-standalone.

The follow-up gate uses synthetic editable `.pth` files and console-shaped
launchers, not pytest's import path. It runs `--help` only for these startup
checks. Parent acceptance must still refresh the real editable installation and
exercise both actual installed commands. No pip/network access, model request,
Core edit or native build was used to repair this boundary.
The final focused gate passed 31 tests in 9.21 seconds, including the console
startup cases, facade/wheel checks and existing CLI, registry and build-script
tests. Its log is `tmp/edexcel-console-runtime-green.log`. Scoped Ruff and
whitespace checks pass.

The parent refreshed the real isolate editable package with uv using no index,
no dependencies and no build isolation. Both installed console scripts then
completed `--help` from `/tmp` with PYTHONPATH removed. Their usage names are
respectively keldin-edexcel and pastpapergen. Logs are
`tmp/consolidated-edexcel-uv-refresh.log` and
`tmp/consolidated-edexcel-{command,legacy}-help-green.log`. Earlier pip/help
attempts failed and remain retained; they are not acceptance results. No model
or paper was requested by the installed-command checks.
