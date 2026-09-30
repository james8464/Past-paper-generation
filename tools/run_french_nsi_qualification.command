#!/bin/zsh
set -euo pipefail

SCRIPT_DIR=${0:A:h}
PROJECT_DIR=${SCRIPT_DIR:h}
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
REFERENCE_INDEX="$PROJECT_DIR/Reference Corpus/france/nsi/references.sqlite"
OUTPUT_DIR=${PAPER_CREATOR_FRENCH_QUALIFICATION_OUTPUT:-"$PROJECT_DIR/tmp/qualification-fr-nsi-2027"}
MODELS=${PAPER_CREATOR_FRENCH_MODELS:-"gemma4:12b,ministral-3:8b,qwen3:8b"}

if [[ ! -x "$PYTHON_BIN" ]]; then
  print -u2 "Python environment missing: $PYTHON_BIN"
  exit 2
fi

if [[ ! -f "$REFERENCE_INDEX" ]]; then
  print -u2 "French reference catalogue missing: $REFERENCE_INDEX"
  exit 2
fi

cd "$PROJECT_DIR"
exec "$PYTHON_BIN" tools/french_nsi_benchmark.py \
  --reference-index "$REFERENCE_INDEX" \
  --output "$OUTPUT_DIR" \
  --models "$MODELS" \
  --base-seed 270100 \
  --papers-per-model 10 \
  --timeout-seconds 10800
