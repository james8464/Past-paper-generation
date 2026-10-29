# Private records and document-only publication

## Behaviour

Native UK and French generation now writes into a unique folder under Keldin's
private job-history storage. JSON packages, manifests, diagnostics and their
original relative-path documents remain there. Publication copies usable
documents into the selected export folder without modifying their bytes.

The export allowlist covers question papers, marking schemes, source booklets,
preliminary material, electronic answer documents, skeleton programs and practice
data. JSON files are excluded even when their role would otherwise be allowed.
The existing atomic directory publisher prevents a partial export from replacing
earlier papers. Technical history artifacts retain their private URLs; public
documents receive their committed export URLs only after a successful copy.

Benchmarks also write to private storage and no longer follow the document export
folder setting. Changing that setting does not change the benchmark destination.

Existing files in Downloads are untouched. Command-line diagnostic and explicit
assessment-bundle exports retain their existing contracts. Paper content,
validation, selected seeds and historical package replay are unchanged. No
resource slider is included in this change.

## Verification

- Native suite: 283 tests, one opt-in interaction test skipped, no failures.
  Log: `tmp/private-documents-final-green.log`.
- The first red build demonstrated the missing document-only publication method.
  A subsequent full run exposed a stale test using an absent `/fixture` PDF; that
  fixture now creates a real file inside the captured private job folder. The new
  completion fixture also needed onboarding dismissed and canonical comparison
  of macOS `/var` and `/private/var` aliases. Production path checks were retained.
- Controlled UK and French completions export exactly two PDF fixture files,
  retain the original JSON manifest privately, complete history and preserve
  source/export byte equality. French manifest identity and practice policy are
  still checked before successful history completion.
- Additional tests cover distinct private job folders, private benchmark output,
  unchanged original records and document-only copying. Existing copy/commit
  failure, repeated-publication and path/symlink rejection tests remain active.

These tests use controlled backend events and opaque file fixtures. They make no
model calls, change no user data and are not new visual paper qualification or a
generation-speed benchmark. Protected Backend and macOS checks must pass before
merge; the installed application is updated only after acceptance.
