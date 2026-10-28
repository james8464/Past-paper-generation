# Keldin identity migration

All new app targets, executables, bundle IDs, folders, environment variables and
schema identifiers use Keldin. The macOS bundle ID is `com.jamesdurup.Keldin`;
the packaged service is `KeldinBackend`. Build the renamed project with
`make -C macOS build-and-run`.

Earlier spellings remain in the migration readers and compatibility tests. They
identify existing data, not the current app. Archived evidence keeps its original
file paths so the recorded results remain traceable.

## Local files and settings

### Standalone Edexcel command

`keldin-edexcel` and `python -m keldin_edexcel` provide the Keldin command name
after installing the Edexcel generator. The `keldin_edexcel.cli` facade exports
the same `main` and `generate_package` callable objects as `pastpapergen.cli`.
It is not a renamed copy of the implementation or a new set of model classes.
Internal submodules such as `models` remain under `pastpapergen`.

The distribution name, existing `pastpapergen` imports and command, registry
entry point and saved assessment IDs remain unchanged. Existing scripts require
no import or data migration. Reinstalling the editable generator exposes the new
console command alongside the old one.

For an editable installation inside a complete checkout, both CLI names locate
the checkout's shared Backend at the command boundary, regardless of the current
directory or PYTHONPATH. Importing the packages alone does not change search
paths. A generator wheel by itself does not include the Keldin Backend and is
not a standalone application; it needs that runtime separately available.

At the first normal launch, Keldin imports accessible preferences from the earlier
bundle domain and copies its Application Support files into `Keldin`. Existing
Keldin values and files win on conflicts. Originals remain in place, including
files referenced by saved job records. History pointers to copied internal artifacts
are redirected to their Keldin locations without changing document bytes or file
identities. External output paths stay unchanged. Model snapshot links are copied
as links.

The old app used both `Paper creator` and `Paper Creator` as folder names. The
migration checks both. New history, model storage, French references and internal
working output use `Keldin`.

Changing a bundle ID creates a separate macOS sandbox. The new app cannot assume
access to the earlier container or its security-scoped folder bookmarks. If
history or PDFs are missing, use **Output Settings > Import previous app data…**
and select the earlier app's folder in `Library/Application Support`. Select the
output folder again if macOS requires renewed access. Imported preferences take
effect after restarting Keldin. If macOS denies access to the old preferences
domain, set those preferences again in Keldin.

The importer copies missing data and never deletes the old installation. Remove
old files only after checking that the documents and models you need are present.

## API keys

New credentials use the `Keldin` Keychain service. If no current entry exists, the
reader tries the earlier service and writes an accessible key to the new service.
It removes the earlier entry only after the new write succeeds. Clearing a key
also clears its accessible legacy entry so it cannot reappear on the next launch.

macOS may ask permission to read an earlier credential. A changed signing identity
can also prevent access. Re-enter the key in Keldin if the import is denied; the
migration does not bypass Keychain access controls.

## Backend jobs and retained papers

New backend settings use `KELDIN_` environment variables. Python commands accept
the matching `PAPER_CREATOR_` aliases when no new value was supplied. An explicitly
empty new value takes precedence. The native development launcher also accepts
the old root override while new launch configurations use `KELDIN_ROOT`.

Checkpoints and diagnostics use `.keldin-checkpoints` and `.keldin-diagnostics`.
When a command accesses these directories, it imports missing ordinary files from
the corresponding earlier directories once. A completion marker prevents a
retired checkpoint or deleted report from being restored on the next call.
Copies are published only after their
contents have been written; symlinks are not followed. The Computer Science notes
cache imports ordinary cached files into its new `Keldin` directory on first use.

Stored packages and their hashes are not rewritten. Existing version and
implementation checks still apply, so a checkpoint tied to another implementation
may require a fresh run. Saved PDFs remain available. New PDFs use Keldin,
including historical French generation routes; validators still recognise the
former footer when inspecting an already saved paper.
