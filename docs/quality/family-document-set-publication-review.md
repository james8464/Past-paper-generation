# Complete document-set publication for direct family entry points

Two owned offline Edexcel runs reproduced a developer-CLI defect. If a later
source-booklet renderer failed or was interrupted, the earlier question paper
had already replaced its destination while old companion files remained.
Individual PDF replacement was atomic; the complete document set was not.
Eight family CLI paths shared this adapter. The installed native bridge already
had a separate outer transaction, so this was not evidence of native partial
publication or a loss of user files.

The selecting reviewer read the complete 196-line Edexcel CLI and its 30-line
runtime import guard. Independent final review read the complete 127-line shared
publisher, 220-line adapter and 323-line new lifecycle tests. Generation received
an extraction-delta review against its earlier source-bound evidence, not a new
whole-file EOF claim.

The adapter now renders every role, supporting artifact and assessment package
into a private staging directory. It checks returned files belong to that
directory, then promotes the complete role mapping under one output-root lease.
It returns final paths and emits Done only after successful commit and staging
cleanup. Authoring and preparation remain outside the commit lease.

The existing publisher, lease and cancellation exception were moved into a
dependency-safe shared module rather than copied into a second implementation.
Generation retains compatibility exports and its existing final transaction.
Distinct destination names, non-file/symlink refusal, backup recovery and rollback
behavior remain in the shared implementation.

An inner adapter commit may still be inside the bridge's private staging area.
Its cleanup therefore must not swallow cancellation before the outer user-facing
commit. The explicit `final_publication=False` setting preserves that boundary.
The final bridge transaction retains its existing behavior for cancellation
during post-commit backup cleanup. A direct caller interrupted after a complete
commit may report cancellation with a complete set present; it must not report
an incomplete set as success.

Focused controls cover actual later-render failures, support/preview/assessment
failure, old and empty outputs, final path ordering, path refusal, cancellation,
same-root commit isolation and rollback, and independent roots. A new inner
backup-cleanup test first reproduced swallowed cancellation, then passed with
the explicit boundary. Existing publication and recovery controls remain part of
the acceptance set. Owned fake-byte fixtures test lifecycle contracts only; the
actual Edexcel failure reproductions use the real offline PDF renderer.

This review does not qualify model answers, prove crash/power-loss durability,
or establish every provider's cancellation behavior. Final combined tests,
packaged acceptance and protected CI remain separate release gates.
