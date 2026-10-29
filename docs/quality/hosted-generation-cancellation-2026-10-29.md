# Hosted generation cancellation

Read-only review found that the shared OpenAI/Anthropic generation path and the
specialist Computer Science/Economics paths used ThreadPoolExecutor contexts.
On cancellation or a worker failure, their context managers waited for active
network calls. Native Cancel sends SIGTERM but only the app's Quit lifecycle
escalates to forced termination. An individual cancelled helper could therefore
retain its requests and checkpoint lease until those calls finished.

A red subprocess test exercised the real shared scheduling branch with two
fake 30-second requests and SIGTERM after 0.2 seconds. The process failed to exit
within three seconds. No provider, model or GPU was called.

Hosted scheduling now uses the same caller-accepted daemon-worker mechanism as
local generation. A separate entrypoint validates the hosted one-to-four worker
cap; the local one-or-two contract is unchanged. The shared and two specialist
paths use private deferred checkpoints, committed only when the caller accepts
the result. Already accepted work remains resumable. After a failure, a late
worker cannot publish its checkpoint changes.

The change does not cancel an already submitted remote operation at the provider;
it prevents that operation from holding the cancelled local helper open. No
provider-side cancellation or billing guarantee is implied. It also does not
weaken question, numeric, source, schema or final-paper validation. Result order,
source inputs and RNG use are unchanged. There are no new model-quality or
generation-speed claims.

The shared branch and both specialist branches now pass subprocess cancellation
checks with a three-second bound. Additional tests cover hosted four-worker
overlap and result order, rejection of invalid counts, preserved local limits
and failure followed by a late checkpoint-producing worker. The existing
Ollama/MLX scheduling, schema, cleanup and cancellation tests remain active.
