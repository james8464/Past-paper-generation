#!/bin/zsh
set -euo pipefail

project_root="${0:A:h:h}"
corpus_root="$project_root/Reference Corpus/france/nsi"
lock_dir="$corpus_root/.reconciliation-lock"
register="$project_root/Resources/france/nsi/source-register.json"
discovery="$project_root/docs/quality/french-nsi-archive-discovery-2026-09-28.json"
manifest="$corpus_root/manifest.json"

/bin/mkdir -p "$corpus_root"
if ! /bin/mkdir "$lock_dir" 2>/dev/null; then
  print -u2 "A French NSI reference reconciliation is already running."
  exit 2
fi
trap '/bin/rmdir "$lock_dir" 2>/dev/null || true' EXIT INT TERM

cd "$project_root"
.venv/bin/python tools/reconcile_french_nsi_archive.py \
  --register "$register" \
  --discovery "$discovery"
.venv/bin/python tools/french_reference_corpus.py \
  --register "$register" \
  --output "$corpus_root"
.venv/bin/python tools/reconcile_french_nsi_archive.py \
  --register "$register" \
  --manifest "$manifest"

print "French NSI archive reconciliation completed and hashes were pinned."

