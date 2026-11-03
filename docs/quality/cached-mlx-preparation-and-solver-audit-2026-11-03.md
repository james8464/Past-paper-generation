# Cached MLX preparation and solver review

## Cached preparation

An owned handler fixture reproduced a storage-policy error. With a complete
cached model, an available runtime and 2 GiB free, local-only preparation was
refused by the 8 GiB download-space check before reaching the loader. That check
also hid an actionable missing-cache error. The fixture uses mocks and temporary
data; no real model, network request or user-cache change was involved.

The storage rule's comment and the HIG review describe pre-download headroom.
Native cached-model consent says preparation will not download model data.
Direct inference does not impose the same storage floor. Local preparation can
still write small approval records or dependency caches, so it is not guaranteed
write-free or guaranteed to succeed on a nearly full disk.

The handler now validates architecture and Python first. For a local-only request,
it checks runtime availability once. Only an already available runtime permits
skipping download headroom. A missing runtime keeps the full storage check before
the existing installation/frozen-build guards. Non-local setup is unchanged.
Default environment validation still requires the original 8 GiB floor.

The existing pinned revision, local-files-only, no-runtime-pip and
trust-remote-code protections are unchanged. Missing caches still refuse without
network fallback. The unsupported-Python message now uses Keldin's current name.

Red tests produced three expected failures with five passing controls. The final
77-test MLX setup/consent/download-info run passed. The eight new cases cover
cached success, both download runtime states, missing local runtime, architecture
and Python guards, missing-cache errors and the current app name. One existing
mock accepts the new optional keyword; its assertions are unchanged.

Ruff rejected an assigned lambda in the first implementation. A typed nested
function now returns the same captured runtime result. The final scoped run
passed again. No validation rule was changed to accommodate a failing test.

Evidence: `tmp/nov3-mlx-cached-storage-red.log` and
`tmp/nov3-mlx-cached-storage-green-final.log`. Full frozen, protected and packaged
gates remain required for this later source. The preceding 6,775-test result
belongs to graph-repair source `7368bd4d`, before this MLX change.

## Implementation review

`quality_status_review` read the complete prior 471-line MLX setup file and every
subsequent production delta, then reread the final new test file through EOF.
The final review found no additional P1/P2 issue. It did not execute tests or
claim real model preparation on a low-disk Mac.

`release_gap_audit` read the complete 1,309-line independent solver. The review
covered answer-key projection, strict response/slot/choice validation, citation
admission, deterministic recomputation, published-scheme reconciliation and
cancellation propagation. No new verified P1/P2 finding arose. Dependencies and
tests were inspected selectively; no new execution was performed for that EOF
review. Semantic model agreement remains distinct from deterministic proof.
The known underspecified Accounting Q06 result is not qualified by this review.

| File | Lines | SHA256 |
| --- | ---: | --- |
| `Backend/Core/mlx_setup.py` | 486 | `8f6035fd9419b89c876a2b837c5b428eb3a217d0b7075b4fb8fa1dba16eaaac4` |
| `tests/test_mlx_cached_storage.py` | 103 | `0f121a353238966377c44e8823239784de3f497f9e2f12a4c6ca52ef90f31043` |
| `Backend/Core/independent_solver.py` | 1309 | `2f426a9fd6bcfecdfb9c26d8e2957be313742b6a8964d516fc7779a778b9a5b3` |

These are bounded file reviews and a setup repair. They do not certify every
provider, complete-paper accuracy, empirical timing, all native interactions or
App Store distribution.
