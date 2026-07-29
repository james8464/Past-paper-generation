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

PYINSTALLER_ARGS=(
  --noconfirm
  --clean
  --onedir
  --name PaperCreatorBackend
  --distpath "$DIST_DIR"
  --workpath "$WORK_DIR/work"
  --specpath "$WORK_DIR"
  --paths "$ROOT_DIR"
  --hidden-import fitz
  --add-data "$ROOT_DIR/Resources/layout-master-runtime.json:Resources"
  --add-data "$ROOT_DIR/Resources/generator-registry.json:Resources"
  --add-data "$ROOT_DIR/Resources/backend-protocol.schema.json:Resources"
)

while IFS= read -r python_path; do
  PYINSTALLER_ARGS+=(--paths "$ROOT_DIR/Resources/$python_path")
done < <(
  "$PYTHON" -c \
    'from Backend.Core.generator_registry import generator_capabilities; print(*[item.python_path for item in generator_capabilities().values()], sep="\n")'
)

while IFS= read -r package; do
  PYINSTALLER_ARGS+=(--collect-submodules "$package")
done < <(
  "$PYTHON" -c \
    'from Backend.Core.generator_registry import generator_capabilities; print(*[item.package for item in generator_capabilities().values()], sep="\n")'
)

while IFS= read -r syllabus_path; do
  destination="Resources/$(dirname "$syllabus_path")"
  PYINSTALLER_ARGS+=(--add-data "$ROOT_DIR/Resources/$syllabus_path:$destination")
done < <(
  "$PYTHON" -c \
    'from Backend.Core.generator_registry import generator_capabilities; print(*[item.syllabus_path for item in generator_capabilities().values()], sep="\n")'
)

"$PYTHON" -m PyInstaller "${PYINSTALLER_ARGS[@]}" "$ROOT_DIR/bridge.py"

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
