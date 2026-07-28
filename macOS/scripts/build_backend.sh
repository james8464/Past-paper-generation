#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$SRCROOT/.." && pwd)"
PYTHON="$ROOT_DIR/.venv/bin/python"
HELPER_DIR="$TARGET_BUILD_DIR/$UNLOCALIZED_RESOURCES_FOLDER_PATH"
WORK_DIR="$DERIVED_FILE_DIR/PaperCreatorBackend"
DIST_DIR="$WORK_DIR/dist"
BACKEND_DIR="$HELPER_DIR/PaperCreatorBackend"

if [[ ! -x "$PYTHON" ]]; then
  echo "error: Missing $PYTHON. Create the project virtual environment first." >&2
  exit 1
fi

if ! "$PYTHON" -c 'import PyInstaller' 2>/dev/null; then
  echo "error: PyInstaller is required in .venv (pip install \"pyinstaller>=6.17,<7\")." >&2
  exit 1
fi

rm -rf "$WORK_DIR" "$BACKEND_DIR"
mkdir -p "$DIST_DIR" "$HELPER_DIR"

"$PYTHON" -m PyInstaller \
  --noconfirm \
  --clean \
  --onedir \
  --name PaperCreatorBackend \
  --distpath "$DIST_DIR" \
  --workpath "$WORK_DIR/work" \
  --specpath "$WORK_DIR" \
  --paths "$ROOT_DIR" \
  --paths "$ROOT_DIR/Resources/economics/edexcel-a/generator" \
  --paths "$ROOT_DIR/Resources/economics/aqa/generator" \
  --paths "$ROOT_DIR/Resources/economics/ocr/generator" \
  --paths "$ROOT_DIR/Resources/computer-science/aqa/generator" \
  --paths "$ROOT_DIR/Resources/computer-science/ocr/generator" \
  --paths "$ROOT_DIR/Resources/business/aqa/generator" \
  --paths "$ROOT_DIR/Resources/accounting/aqa/generator" \
  --collect-submodules pastpapergen \
  --collect-submodules aqaecongen \
  --collect-submodules ocregen \
  --collect-submodules cspapergen \
  --collect-submodules ocrcsgen \
  --collect-submodules aqabizgen \
  --collect-submodules aqaaccountgen \
  --hidden-import fitz \
  --add-data "$ROOT_DIR/Resources/layout-master-runtime.json:Resources" \
  --add-data "$ROOT_DIR/Resources/economics/edexcel-a/generator/data/syllabus_seed.json:Resources/economics/edexcel-a/generator/data" \
  --add-data "$ROOT_DIR/Resources/economics/aqa/generator/data/syllabus.json:Resources/economics/aqa/generator/data" \
  --add-data "$ROOT_DIR/Resources/economics/ocr/generator/data/syllabus.json:Resources/economics/ocr/generator/data" \
  --add-data "$ROOT_DIR/Resources/computer-science/aqa/generator/data/syllabus_seed.json:Resources/computer-science/aqa/generator/data" \
  --add-data "$ROOT_DIR/Resources/computer-science/ocr/generator/data/syllabus.json:Resources/computer-science/ocr/generator/data" \
  --add-data "$ROOT_DIR/Resources/business/aqa/generator/data/syllabus.json:Resources/business/aqa/generator/data" \
  --add-data "$ROOT_DIR/Resources/accounting/aqa/generator/data/syllabus.json:Resources/accounting/aqa/generator/data" \
  "$ROOT_DIR/bridge.py"

ditto "$DIST_DIR/PaperCreatorBackend" "$BACKEND_DIR"

find "$BACKEND_DIR/_internal/Resources" -type f -exec chmod 0644 {} +
xattr -cr "$BACKEND_DIR"

SIGN_IDENTITY="${EXPANDED_CODE_SIGN_IDENTITY:--}"
find "$BACKEND_DIR" -type f -print0 |
  while IFS= read -r -d '' file; do
    if /usr/bin/file -b "$file" | grep -q 'Mach-O'; then
      /usr/bin/codesign --force --sign "$SIGN_IDENTITY" --timestamp=none "$file"
    fi
  done

touch "$BACKEND_DIR/.built"
