# Concurrent backend event output

MLX's inference owner and the generation caller can emit progress concurrently.
The previous emitter allocated IDs before an unlocked `print`, which can perform
separate writes for the JSON body and newline. The counter alone did not make a
whole event atomic.

One reentrant lock now covers ID allocation, envelope construction, serialization
and the complete flushed print. Fields, protocol version, payload behavior and
counter lifetime are unchanged.

The deterministic regression pauses the first emitter halfway through its JSON
write, then starts a second emitter. A handshake observes either its lock attempt
or its unprotected write before releasing the first. The original code fails JSON
parsing; the locked code preserves two valid lines with IDs 1 then 2 and all
existing fields. No sleeps or probabilistic scheduling window decide the result.
Logs are retained locally under `tmp/mlx-batching-20261029`.

The regression, existing event/protocol/backend checks and batching tests passed
59 tests with the five existing PDF-library deprecation warnings. Ruff and the
diff whitespace check passed. No model, user data or UI actions were involved.
