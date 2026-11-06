# Generation adapter entry points

An independent reviewer read these two maintained entry points through EOF:

| File | Lines | SHA-256 |
| --- | --- | --- |
| `Resources/accounting/aqa/generator/aqaaccountgen/cli.py` | 75 | `3cdb7b55f64f6dde4a7b44b756c77bbbd75b5ffd9425acf0d27fab5420c12135` |
| `Resources/configured-generators/generator/configuredgen/cli.py` | 132 | `9a02e63d6e3307392c5764be11c25523f9dddbaee4a641ad6d5b0107966da0e4` |

The review covered request dispatch, deferred rendering, client and checkpoint
forwarding, and error and cancellation propagation. Both entry points pass their
work to the shared family adapter. Neither catches a failure and reports success.
No implementation change was warranted within this scope.

Supporting reads covered the shared adapter's validated PDF transaction,
generation entry dispatch, capability admission, the configured-model loader
and relevant existing tests. These were scoped reads, not complete reviews of
those dependencies. Configured practical roles are not advertised by the native
capability registry; this review does not qualify a practical assessment.

This was a read-only source review. It ran no tests, builds, models or interface
checks. The two file hashes were verified separately before recording coverage.
It does not establish generated-paper correctness or complete the project audit.
