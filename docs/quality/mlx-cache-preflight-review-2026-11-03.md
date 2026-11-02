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

This is a bounded cache-readiness repair. It does not parse or certify model contents, repair corrupt Hub blobs automatically, prove model compatibility or qualify generated papers. No native UI action, real model setup, inference or full-project test run was performed for this change. Selectively traced dependencies are not attested as full-file reviews here.
