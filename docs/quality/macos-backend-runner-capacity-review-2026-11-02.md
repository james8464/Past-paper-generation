# Backend runner capacity review, 2 November 2026

## Observed failures

The main-branch run `41451216926` and PR158 run `41457313352` failed to provision their Backend jobs. Neither job acquired a runner or executed a test step. GitHub recorded: "The job was not acquired by Runner of type hosted even after multiple attempts" and repeated warnings about capacity constraints on macOS arm64 runners. Their native jobs passed. These are retained provisioning failures, not backend test failures or evidence that all checks passed.

The exact job annotations are available on check runs `125296612528` and `125317167705`. GitHub's global status page reported Actions operational; it did not remove these job-specific capacity warnings.

## Scoped workflow change

Only the Backend job moves from `macos-15` to the standard `macos-15-intel` pool. It keeps macOS15 system fonts for the PDF checks. The native compilation, tests, signing and Store-preflight job remains on the Apple Silicon `macos-15` runner. Check names, time limits, lint, formatting, typing, full Python tests and signing restrictions are unchanged. There is no skipped required job, continue-on-error policy, Linux substitution or protection bypass.

GitHub's [standard runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) lists `macos-15-intel` as a standard Intel macOS runner and states that standard runners are free for public repositories. This repository's visibility was verified as public. No larger runner, paid service or self-hosted credential was introduced. A different pool may also queue; actual latest-head results remain required before merging.

The new workflow regression first failed under the old Backend label with the other three signing tests passing. The revised workflow then passed the 33-test signing, configuration, formatting-boundary, Apple-packaging and release-compliance selection. Ruff and formatting checks passed. Root read the complete 85-line workflow and the complete original signing tests plus the new test. The test requires Intel only for Backend, retains Apple Silicon for native checks and retains the full pytest command without continue-on-error.

No application, model, prompt, checkpoint-admission or PDF-rendering implementation changed in this follow-up. The full local run (6,468 passes) and native run (418 executed, three skipped) certify the unchanged implementation at `f61fd89a`; they are not relabelled as a new full run including this extra workflow test. CI must run the full suite on the revised head. This change makes no claim of Intel app distribution support, live paper qualification or Store approval.
