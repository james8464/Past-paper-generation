# Release safety: cleanup, console startup and scoped static checks

Date: 29 October 2026. This is a bounded implementation review on
`main-release-safety-audit`, based on `4427e1c642c5ffe36eb26f9529eae5bd3ea0652e`.
It is not whole-project audit clearance, paper qualification or Store approval.
The repository-wide implementation audit remains incomplete.

## Confirmed defects and fixes

The old cleanup command accepted agent-name traversal and interpreted build
targets relative to the caller's working directory. It also accepted symlinked
build ownership. The revised command requires the macOS project directory,
validates the selected agent as a simple letters/digits/underscore/hyphen slug,
constructs absolute targets under its own build directory and validates the
whole batch for symlinked build roots, category ancestors and selected targets
before invoking Trash. `--all` retains the five explicit owned build categories.
This is a local defensive check, not protection against a concurrent filesystem
attacker changing paths between validation and an external Trash operation.

The Finder fallback previously interpolated paths into invalid single-quoted
AppleScript literals. It now sends a fixed script and separate absolute path
arguments. Path quotes, spaces and shell-looking characters remain data.
No real cleanup, Trash operation, Finder action or osascript execution was
performed during these tests. The harness copies the scripts into temporary
fixtures and supplies logging-only fake executables, including replacing the
old absolute osascript command in the copied script before exercising RED.
No user files or retained build artifacts were removed.

The AQA Computer Science console could not import the shared Backend when an
editable package was launched outside the checkout directory. A CLI-only local
bootstrap now recognises its exact complete-checkout location and prepares the
shared runtime before Backend imports. If that runtime is absent, the command
explains that the generator wheel is not standalone. Ordinary `import
cspapergen` remains pure. The existing Edexcel bootstrap provided the comparison
contract; its implementation and both existing command names are unchanged.
Tests use isolated Python, cleared PYTHONPATH, a non-repository working
directory and only the editable package source path. They do not use fabricated
import blockers, models, package installations or wheel builds.

## Static boundary and P5 limits

The development dependency pins mypy 2.4.1. The official PyPI release page lists
that version, released 28 October 2026:
https://pypi.org/project/mypy/2.4.1/

Evaluation installed it and its dependencies only in an ignored temporary
environment, not the application/runtime environments. `tools/typecheck.ini`
enables strict checking with normal import analysis and no blanket missing-
import suppression for exactly three leaves: `Backend/Core/json_client.py`,
`tools/pdf_process.py` and `tools/atomic_json.py`. CI runs that explicit config.
The tests require an available checker and fail if it is absent, rather than
skipping. A minimal JSON client and typed factory pass; wrong result type,
extra required argument and incompatible factory each yield one `[assignment]`
diagnostic. The static fixtures are analysed, not executed.

P5 remains partial. This gate does not type-check every adapter/provider or
remove FamilyAdapter's heterogeneous Any boundaries. It supplies no static
acceptance claim beyond the three named leaves and structural fixture boundary.

## Reproduction and verification

All log paths below are relative to the isolated checkout's retained `tmp/`.

| Gate | Result | Log |
| --- | --- | --- |
| Original cleanup behavior, fake tools only | 11 failed | `release-safety-cleanup-red.log` |
| Original CS console boundary | 2 failed, 1 passed | `release-safety-cspapergen-console-red.log` |
| Strict three-leaf evaluation | passed | `mypy-baseline-20261029.log` |
| Positive static fixture | passed | `mypy-contract-positive-20261029.log` |
| Negative static fixture baseline | expected 3 assignment errors | `mypy-contract-negative-20261029.log` |
| Cleanup, CS boundary and tracked static contract tests | 18 passed in 3.88 seconds | `release-safety-tooling-green.log` |
| Tracked three-leaf mypy config | passed | `release-safety-static-green.log` |
| Existing Edexcel facade, renderer transactions and registry tests | 26 passed in 4.49 seconds | `release-safety-tooling-related-green.log` |

The related tests emitted existing PyMuPDF SWIG deprecation warnings. Bash
syntax checks passed for both changed scripts. Scoped Ruff lint, formatting and
`git diff --check` passed. These are focused gates, not a new full-suite,
signed-build or frozen-helper qualification. The full release gates remain a
separate responsibility after all owners freeze their changes.

## Fully read files and reviewed byte identities

These files were read completely for the bounded review, including the final
owned changes. Hashes identify the reviewed bytes, not an authenticated review
attestation. CI and test dependencies changed and require refreshed review
attestation before release; existing attestations were not edited by this task.
No coverage ledger, Graphify output or inventory was changed here.

| Path | SHA-256 |
| --- | --- |
| `.github/workflows/ci.yml` | `35eebcdae545b38195b4997437347536c997ac0c67e04598edd27f8c58c491c8` |
| `requirements-test.txt` | `54ea1e390e4228fe315b5c60967f5cc9f30d775b19d7491824a102b5b3647d3f` |
| `macOS/scripts/clean.sh` | `4cd521d6631e240dec5e4607bbcd8197e64264132d5cb128ccf86a90609b61d1` |
| `macOS/scripts/move_to_trash.sh` | `19043928a36808bf0141cae1e58f0cf10451a53a421924d24426f35846c36976` |
| `macOS/scripts/resolve_agent_name.sh` | `848152f429cea8d3d88e784ccfa9c57db1d865ae5d4a7318301d17bfe070c768` |
| `Resources/computer-science/aqa/generator/cspapergen/cli.py` | `b8f6e209d8c0fed7e83c2a8cdea308681c1d11c378f5ebcafc8a064e729ef09e` |
| `Resources/computer-science/aqa/generator/cspapergen/_cli_runtime.py` | `a6da5be13ca684c12a00b3440e304fe32ca8cdfe8595ec9d4737c7a6c6a00ee5` |
| `Resources/economics/edexcel-a/generator/pastpapergen/_cli_runtime.py` | `5757563fc12b27c690b1a18572351468678428fdfb68b72b81b2217adf58aa85` |
| `Backend/Core/json_client.py` | `f1c48f8deb2fed4b7534ef62ffa7a445115cf12a3570a98166cb067a5af66a62` |
| `tools/pdf_process.py` | `03e744b9a568541c91ffa7234950754210bdf5e41b1b8319bfa3aefc22790904` |
| `tools/atomic_json.py` | `7606c5ff9dab3635dfd90494ec5605109d863c4ad5f7d47d67b365b421962387` |
| `tools/typecheck.ini` | `66b08cc8de591929e54a4da500f875fafecdd859ce0475d32eeb74bab9b223fb` |
| `tests/test_build_cleanup_safety.py` | `a3d17fdd561200a55bd71e3801804bb8acca6cab81ec354ddba56f6c205a1e4b` |
| `tests/test_cspapergen_console_runtime.py` | `a334c53011454b2b611350f3e1e1f32dd19540d47a175152ebdd397263e13d32` |
| `tests/test_static_type_contracts.py` | `18a69a44d1c92e904effc1732b68193740b18a807ad3a107ead0a73447d3bca9` |
