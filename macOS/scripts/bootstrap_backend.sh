#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON="${PYTHON:-python3}"

"$PYTHON" -m venv "$ROOT_DIR/.venv"
"$ROOT_DIR/.venv/bin/python" -m pip install \
  -r "$ROOT_DIR/requirements-build.txt" \
  -e "$ROOT_DIR/Resources/accounting/aqa/generator" \
  -e "$ROOT_DIR/Resources/business/aqa/generator" \
  -e "$ROOT_DIR/Resources/computer-science/aqa/generator" \
  -e "$ROOT_DIR/Resources/computer-science/ocr/generator" \
  -e "$ROOT_DIR/Resources/economics/aqa/generator" \
  -e "$ROOT_DIR/Resources/economics/edexcel-a/generator" \
  -e "$ROOT_DIR/Resources/economics/ocr/generator"

