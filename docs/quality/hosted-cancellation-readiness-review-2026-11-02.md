# Hosted cancellation test readiness

Reviewed on 2 November 2026. This changes test coordination, not app code or provider deadlines.

## Failure and reproduction

The PR158 Intel Backend run finished with 6,514 passes, seven skips and one failure: the Edexcel hosted-cancellation subprocess exceeded its three-second timeout. That timeout included interpreter startup, imports and blueprint construction. The child started its cancellation timer only after those steps. The timer could also fire before either fake provider worker had started.

A controlled reproduction added a 3.2-second delay before the original child script's imports. The unchanged parent timeout failed after 3.009 seconds, before cancellation was scheduled. This demonstrates a false-failure path in the harness. The CI run did not record worker readiness, so its exact startup and cancellation timings cannot be reconstructed from that failure alone.

## Bounded change

The parent now waits up to 20 seconds for a flushed readiness message emitted by a two-worker barrier. This confirms that two fake provider calls have entered blocked work. The parent then sends SIGTERM and retains the original three-second cancellation deadline. The child's 0.2-second timer is removed. Failure paths kill and reap only the subprocess created by the test.

Shared generation and both specialist routes are checked with ordinary startup and the controlled 3.2-second delay. Specialist imports explicitly select the current checkout and verify the selected implementation's path. A negative control deliberately creates non-daemon blocked workers. It must still fail at the three-second post-signal deadline; the harness then kills and reaps that child.

The existing hosted worker cap, result-order and late-checkpoint tests remain in place. No production executor, checkpoint policy, provider timeout or cancellation behavior changed.

## Evidence and limits

Focused scheduler and checkpoint tests passed: 92 tests, with five existing SWIG warnings, in 16.08 seconds. The command was:

```text
python -m pytest -q tests/test_hosted_generation_cancellation.py tests/test_ollama_parallel_jobs.py tests/test_assessment_checkpoint_admission.py tests/test_aqa_cs_checkpoint_admission.py tests/test_edexcel_checkpoint_admission.py
```

Private logs are `tmp/nov2-cancellation-cold-start-original.log` and `tmp/nov2-cancellation-readiness-focused.log`. The six warm/cold cancellation cases were also run separately again; their result is recorded in `tmp/nov2-cancellation-readiness-repeat.log`.

The complete reviewed test file has 237 lines and SHA-256 `dd8510101faa108c913deefd5054cdb5d0c455e3ed50c206a186bdf85197d282`. The production scheduler was read to trace its daemon-worker, caller-owned result and stop-without-join paths. No model, hosted API, download, app build, UI or accessibility action was used. These fake-provider checks do not establish live provider quality or qualify generated papers.
