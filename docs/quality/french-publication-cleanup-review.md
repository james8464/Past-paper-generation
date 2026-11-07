# French publication cleanup review

## Finding and bounded repair

The French publishers rename their completed staging directory before clearing
the staging variable and reporting files. A cancellation in that interval could
leave the complete bundle committed, then mask the original cancellation with
`FileNotFoundError` while removing the now-absent staging path. This affects both
the explicit historical catalogue publisher and the current V36 publisher.

The repair adds `remove_owned_staging` to the existing temporary-cleanup module
and replaces only the two final cleanup calls and their imports. The helper calls
`shutil.rmtree` normally. It handles `FileNotFoundError` only when a subsequent
`lstat` of the root also raises `FileNotFoundError`. A missing descendant while
the root remains, `PermissionError`, and other unexpected errors still propagate.
The existing failed-file cleanup helper is unchanged.

There is no destination, inode or commit-success inference. Pre-commit
cancellation is unchanged; a retained committed bundle does not manufacture
successful event delivery. Post-commit `InterruptedError` and `BrokenPipeError`
still do not produce a false `done`. Python `KeyboardInterrupt` remains distinct
from the installed SIGTERM handler's cooperative cancellation/130 path. Native
run ownership, cancelled history and termination escalation are unchanged.

## Actual verification

The reviewed 254-line test draft ran once against unchanged production:
**4 failed, 10 passed in 1.34 seconds**. All four failures were the expected
post-rename SIGTERM/KeyboardInterrupt cleanup errors across the two handlers.
The real owned-directory rename succeeded; cleanup masked the original exception.
Complete fixture bundles, original log and their hashes were retained.

The final explicit focused selection passed **26 tests in 0.44 seconds**, with
five existing SWIG warnings: 18 new publication/helper cases and eight existing
fake cancellation, missing-reference, resource-refusal and checkpoint-cleanup
controls. Earlier overlapping 18-, 8- and 20-pass runs are retained, not added to
the final count. The original 254-line prefix remains byte-identical; four direct
helper controls were appended. Fake artifact bytes and validation/provider seams
isolate cleanup behavior; there were no real PDF rendering or model requests.

Ruff check/format, `git diff --check`, and strict typing of the 24-line helper
passed. Logs are `tmp/nov7-french-postrename-red.log` and
`tmp/nov7-french-postrename-final-focused.log`. Root and independent review cleared
the four source/test pins below before this note was added.

## Review attribution and exact pins

The base is merged PR194 `ad950aca4c1e77bcec6ce91318ec80d931147adb`, tree
`001366e4c8a2777e276429d77ffbe6388e9e9002`. The legacy runtime was previously read
through all 2,756 lines at SHA-256
`2a7906a035785c135a0060dc67d3bdc4bf6b85d3beebc347d7bb57f30f7771a7`.
That complete baseline read plus the exact import/final-cleanup delta is composite
review evidence, not a claimed fresh whole-file reread. V36 runtime attribution
is scoped to relevant caller/publication/cancellation spans and its small delta;
no new complete-file V36-runtime review is claimed. The helper and new test file
were read completely through EOF, including the appended error controls.

| File | Lines | SHA-256 |
| --- | ---: | --- |
| `Backend/Core/temporary_cleanup.py` | 24 | `90221f5c7e99bac14b5d0605d0003a8786cef0001e0020a81dece04b57817eea` |
| `Backend/Core/france/runtime.py` | 2756 | `b5a9353b5b3d4de38fdebf260fad2b571181005d0d8a1ecd4ef5ca31f05e838b` |
| `Backend/Core/france/llm_runtime.py` | 284 | `2bb19b2567a84e82c00dc34a994c745bf5b247e3ffd741c7ec58504a3131dfbe` |
| `tests/test_french_postrename_cleanup.py` | 311 | `ad264c35e1ca8a47502b827f6bfe1750ce3bdaf634717630db304e47e3ce28b2` |

This fixes absent-staging cleanup masking only. It does not guarantee atomic
terminal delivery, handling of uncatchable termination, native cancellation
reconciliation, whole-paper quality, model capability or official equivalence.
No prompts, answers, marks, routing, generation limits or user data changed.
No full suite, build, GUI, live model or native acceptance run is claimed here;
final integration and release gates remain separate.
