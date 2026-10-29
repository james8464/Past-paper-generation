#!/usr/bin/env bash
set -euo pipefail

ALL=0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRASH="$SCRIPT_DIR/move_to_trash.sh"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"

if [[ "$(pwd -P)" != "$PROJECT_ROOT" ]]; then
  echo "Run clean.sh from the macOS project directory: $PROJECT_ROOT" >&2
  exit 1
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all)
      ALL=1
      shift
      ;;
    -h|--help)
      echo "Usage: clean.sh [--all]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

AGENT_NAME_VALUE="${AGENT_NAME:-}"
if [[ $ALL -eq 0 && -z "$AGENT_NAME_VALUE" ]]; then
  AGENT_NAME_VALUE="$("$SCRIPT_DIR/resolve_agent_name.sh")"
fi

if [[ $ALL -eq 0 && ! "$AGENT_NAME_VALUE" =~ ^[A-Za-z0-9][A-Za-z0-9_-]*$ ]]; then
  echo "Invalid agent name; use letters, digits, underscores or hyphens." >&2
  exit 1
fi

# Validate the entire batch before handing any owned directory to Trash.
if [[ -L "$PROJECT_ROOT/build" ]]; then
  echo "Refusing a symlinked build directory." >&2
  exit 1
fi
targets=()
for name in DerivedData logs cache tmp home; do
  ancestor="$PROJECT_ROOT/build/$name"
  target="$ancestor"
  if [[ $ALL -eq 0 ]]; then
    target="$ancestor/$AGENT_NAME_VALUE"
  fi
  if [[ -L "$ancestor" || -L "$target" ]]; then
    echo "Refusing symlinked build ownership: $target" >&2
    exit 1
  fi
  targets+=("$target")
done
"$TRASH" "${targets[@]}"
echo "Build artifacts moved to Trash."
