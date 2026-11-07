# Optional AQA Computer Science notes-cache integrity

Scope: the optional source/API/CLI notes input, not a demonstrated ordinary
installed-native update failure or a release-194 blocker. Work is based on clean
193 commit `8af13db707c0ebb4cd9d1d14143bc3a3e9439f05` in a separate checkout;
INT is untouched. This is not a model/content-quality qualification.

## Reproduced fault and bounded repair

The prior cache compared only PDF byte counts. Different equal-length input at
the same filename left both cached PDF and extracted topic context unchanged,
including when the replacement retained its timestamp. A second reproduced fault
showed cancellation after copying a changed PDF could leave the old extracted
text paired with a newly published raw file.

The repair compares SHA-256 content digests using bounded 1 MiB reads. Changed
content forces extraction irrespective of timestamps. It stages a PDF copy and
its extracted text in an owned temporary directory, then replaces text before
raw PDF. A propagated extraction exception/cancellation before publication leaves
the prior pair intact; temporary files are cleaned up. If raw replacement fails
after text publication for changed input, old raw bytes still differ from source,
so the next call retries. This is not an atomic transaction across two files.

CLI/API signatures, default/legacy cache paths, topic matching, text limits and
extraction command are unchanged. Existing handled `OSError`/extractor failure
still produces empty text and a zero text count; it is not reinterpreted as OCR
support or a new invalid-PDF validation policy. `InterruptedError` now explicitly
propagates before the ordinary `OSError` handler, preserving cancellation identity
and the old pair. Keyboard interruption also propagates.
No global lock, manifest, dependency, model or prompt changes were introduced.

## Evidence

All fixtures use temporary directories and fake extraction/subprocess functions;
no real PDFs, extractor processes, model calls or personal caches are used.

- Initial equal-size RED: 2 failed, 5 passed in
  `tmp/nov7-cs-notes-cache-red-final.log`.
- Added cancellation RED: 3 failed, 5 passed in
  `tmp/nov7-cs-notes-cache-cancel-red.log`.
- Root caught that `InterruptedError` inherits `OSError`, so the initial repair
  still swallowed real-handler cancellation. Its dedicated real-handler RED
  failed to raise: 1 failed, 10 passed in
  `tmp/nov7-cs-notes-cache-interrupted-red.log`. This supersedes the earlier
  cancellation-scope acceptance; the initial evidence/logs are retained.
- Final focused run: 11 passed, 2 skipped in 0.08 seconds in
  `tmp/nov7-cs-notes-cache-final-v2.log`. The skips are the unchanged existing tests
  requiring the optional local notes folder. Controls cover unchanged content,
  changed length, preserved timestamps, cancellation/retry, missing extraction
  output, raw-publication failure/retry and existing handled failure semantics.
  The real extraction-handler cancellation control asserts the exact same
  exception object, unchanged old raw/text bytes and no remaining owned temps.
- Ruff check passed for the two Python paths; both were formatted with Ruff.

No full suite, build, GUI, model, metadata, ledger, graph update or commit was run.
Concurrent writers/source mutation during a call, process death between replaces,
filesystem durability and general PDF validity remain outside this bounded fix.
Ordinary native arguments do not select a notes folder and optional notes PDFs
are not included by the current builder; no stronger native lifecycle claim is
made. Earlier full-EOF backfill proposals remain read-only and unpromoted.
