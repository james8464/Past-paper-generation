#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage: move_to_trash.sh <paths...>
USAGE
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

existing_paths=()
for path in "$@"; do
  if [[ -e "$path" ]]; then
    if [[ "$path" != /* ]]; then
      path="$(pwd -P)/$path"
    fi
    existing_paths+=("$path")
  fi
done

if [[ ${#existing_paths[@]} -eq 0 ]]; then
  exit 0
fi

if command -v trash >/dev/null 2>&1; then
  trash "${existing_paths[@]}"
  exit 0
fi

if command -v osascript >/dev/null 2>&1; then
  # Paths are arguments, never AppleScript source, including quotes and spaces.
  osascript -e 'on run argv
    repeat with itemPath in argv
      tell application "Finder" to delete POSIX file (contents of itemPath)
    end repeat
  end run' -- "${existing_paths[@]}"
  exit 0
fi

echo "No trash tool available. Install 'trash' (brew install trash) or move items to Trash manually." >&2
exit 1
