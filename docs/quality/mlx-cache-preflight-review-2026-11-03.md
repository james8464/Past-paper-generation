# MLX cache preflight review

The internal author read `Backend/Core/mlx_download_info.py` through EOF and traced the selected setup call sites and existing focused tests. An owned temporary fixture showed that empty `config.json` and tokenizer files were reported as cached. The native setup path would then request local-only preparation. No model was loaded or downloaded for this diagnostic.

The repair requires nonempty configuration data and a nonempty supported tokenizer alternative: `tokenizer.json`, `tokenizer.model`, `tiktoken.model`, or nonempty `vocab.json` with an existing `merges.txt`. An empty merge table is valid for BPE and remains supported. An owned probe using the installed `tokenizers.models.BPE.from_file` confirmed that case during review; the initial overbroad requirement was corrected before publication. A valid alternative still permits offline use when an unused tokenizer file is empty. Existing weight, indexed-shard, size, revision and remote-code policies are unchanged. Explicit incomplete folders refuse; incomplete repository caches proceed to public size metadata instead of being labelled offline-ready. No model or user file is removed.

## Verification

The final tests-only run against the unchanged baseline failed in all five invalid empty-file cases, with 25 tests passing. The corrected tests include an explicit valid empty-merge-table control. After the repair, the 30 download-info tests and 17 related setup tests passed. Ruff and diff hygiene checks passed. Logs remain under `tmp/nov3-mlx-cache-preflight-final-red.log` and `tmp/nov3-mlx-cache-preflight-frozen-green.log` in the author checkout; earlier superseded attempts are retained separately.

The author reread the final source and focused test file through EOF:

| File | Lines | SHA-256 |
| --- | ---: | --- |
| `Backend/Core/mlx_download_info.py` | 193 | `dbf5ed828d4fbd51c1351e0fd4997810e64ba53128d6c3cc15a3991c90dd8a4c` |
| `tests/test_mlx_download_info.py` | 196 | `22a9eb900a223f1cf754481f836ee411fa6d0ae441ffd000552700eafa28356f` |
| `tests/test_live_process.py` | 220 | `614b9a02b22f60baefebc2acff57e4bb215107f02734f9a2fc3bc42bf35214bd` |

## Full-suite failures and timeout-fixture repair

The first full run at `8b55a711` ended with 6,617 passes, two skips and 11 failures because the invocation omitted the virtual environment's executable directory from `PATH`. All 11 failures required `mypy` on that path. With the path corrected, both affected static-contract files passed all 13 tests. The second full run ended with 6,627 passes, two skips and one failure: a timeout fixture expected a Python child to print before its 300 ms lifetime expired. These runs remain failed evidence in `tmp/nov3-mlx-cache-preflight-frozen-full-suite.log` and `tmp/nov3-mlx-cache-preflight-full-suite-env-correct.log`.

The unchanged timeout test passed alone. An owned control with a deliberate 500 ms pre-banner delay reproduced empty output under the unchanged 300 ms timeout. This demonstrates the fixture's scheduling assumption, not the original child's measured startup latency. Production `tools/live_process.py` is unchanged. The test-only repair waits for the actual child banner within a separate five-second startup budget before handing the child to the production timer. Immediate and delayed-start cases retain every original assertion and explicitly verify reaping. A readiness-failure case verifies cleanup before handoff. All eight focused process tests passed; the corrected full suite and new protected checks are still required. Logs are `tmp/nov3-mlx-cache-preflight-timeout-targeted.log`, `tmp/nov3-mlx-cache-preflight-timeout-startup-probe.log` and `tmp/nov3-timeout-readiness-focused.log`.

This is a bounded cache-readiness repair and test-fixture correction. It does not parse or certify model contents, repair corrupt Hub blobs automatically, prove model compatibility or qualify generated papers. No native UI action, real model setup or inference was performed for this change. Selectively traced dependencies are not attested as full-file reviews here.
