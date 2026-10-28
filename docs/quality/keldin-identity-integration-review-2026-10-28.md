# Keldin identity integration review

The user authorised integration of `keldin-naming-and-comments` on 28 October.
Its retained source commit is `e02190c`. The integration includes the later
V35 French catalogue, Accounting component repair, model-guidance corrections
and updated competition reports. It does not replace those fixes with the
earlier branch state.

## Migration findings and repairs

Three native red tests showed that the original preference allowlist omitted
the persistent V35 family ledger. The repair imports that ledger even when old
job history has been pruned, unions valid imported and current identifiers,
and blocks French generation on an unreadable import without deleting current
values. A repaired import clears that blocking state. Migration version two
revisits installations that already completed the earlier version-one import.

The credential copy no longer deletes the legacy Keychain entry after a
successful nonempty write. This keeps recoverable older installations usable.
Explicit user clearing still removes both copies so an old key cannot reappear.
No user credential was printed or used in these tests; real Keychain access
remains subject to macOS permissions.

A red identity test caught a changed digest for the historical application-owned
V32 origin. The old digest is now preserved in the compatibility module. New
V35 generation retains its own versioned identity. Checkpoint migration copies
old bytes without replacing them, while new V35 checkpoints retain the full
version, implementation identity and selected seed in their names.

Four known Ollama availability messages now use French resources in Settings.
The underlying protocol messages remain unchanged. This is not a claim that
every possible external error message is translated.

## Review scope

Python AST comparison separated comment and docstring edits from executable
changes in the original branch. The executable changes concern branding,
environment aliases, storage migration, packaging and compatibility. Adding
comments does not establish human authorship or educational correctness.

Native tests use isolated preferences, temporary history and fake secrets.
Retained red and green logs are under ignored `tmp/keldin-*`. Final full-suite,
signed-package and native migration acceptance must pass before release.
No Store submission, certificate creation or security relaxation is included.
