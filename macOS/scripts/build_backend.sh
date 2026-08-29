#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$SRCROOT/.." && pwd)"
PYTHON="$ROOT_DIR/.venv/bin/python"
HELPER_DIR="$TARGET_BUILD_DIR/$UNLOCALIZED_RESOURCES_FOLDER_PATH"
WORK_DIR="$DERIVED_FILE_DIR/PaperCreatorBackend"
DIST_DIR="$WORK_DIR/dist"
BACKEND_DIR="$HELPER_DIR/PaperCreatorBackend"
FINGERPRINT_FILE="$BACKEND_DIR/.build-fingerprint"

if [[ ! -x "$PYTHON" ]]; then
  echo "error: Missing $PYTHON. Create the project virtual environment first." >&2
  exit 1
fi

# Xcode invokes this script from macOS/, so make the repository packages
# importable for registry discovery as well as for PyInstaller itself.
export PYTHONPATH="$ROOT_DIR${PYTHONPATH:+:$PYTHONPATH}"

if ! "$PYTHON" -c 'import PyInstaller' 2>/dev/null; then
  echo "error: PyInstaller is required in .venv (pip install \"pyinstaller>=6.17,<7\")." >&2
  exit 1
fi

if ! "$PYTHON" -c 'import mlx_lm' 2>/dev/null; then
  echo "error: Apple MLX support is missing from .venv. Run 'make backend-env' before building." >&2
  exit 1
fi

build_fingerprint() {
  {
    printf '%s\n' \
      "distribution=${DISTRIBUTION_MODE:-direct}" \
      "identity=${EXPANDED_CODE_SIGN_IDENTITY:--}" \
      "architectures=${ARCHS:-arm64}" \
      "deployment=${MACOSX_DEPLOYMENT_TARGET:-unknown}"
    "$PYTHON" --version
    "$PYTHON" -c 'import PyInstaller; print(PyInstaller.__version__)'
    shasum \
      "$ROOT_DIR/bridge.py" \
      "$ROOT_DIR/requirements-build.txt" \
      "$ROOT_DIR/macOS/PaperCreator/PaperCreatorBackend.entitlements" \
      "$ROOT_DIR/macOS/scripts/build_backend.sh" \
      "$ROOT_DIR/Resources/backend-protocol.schema.json" \
      "$ROOT_DIR/Resources/generator-capability.schema.json" \
      "$ROOT_DIR/Resources/empirical-calibration.schema.json" \
      "$ROOT_DIR/Resources/empirical-calibration-policy.json" \
      "$ROOT_DIR/Resources/reference-demand-profiles.json" \
      "$ROOT_DIR/Resources/generator-registry.json" \
      "$ROOT_DIR/Resources/layout-master-runtime.json" \
      "$ROOT_DIR/Resources/layout-profiles.json" \
      "$ROOT_DIR/Resources/ollama-model-recommendations.json"
    find "$ROOT_DIR/Resources/board-profiles" -type f -name '*.json' -print0 \
      | sort -z \
      | xargs -0 shasum
    find "$ROOT_DIR/Backend" -type f -name '*.py' -print0 \
      | sort -z \
      | xargs -0 shasum
    find "$ROOT_DIR/Resources" -path '*/generator/*' -type f \
      \( -name '*.py' -o -name 'pyproject.toml' \) -print0 \
      | sort -z \
      | xargs -0 shasum
    while IFS= read -r syllabus_path; do
      shasum "$ROOT_DIR/Resources/$syllabus_path"
    done < <(
      "$PYTHON" -c \
        'from Backend.Core.generator_registry import generator_capabilities; print(*sorted({item.syllabus_path for item in generator_capabilities().values()}), sep="\n")'
    )
  } | shasum | awk '{print $1}'
}

CURRENT_FINGERPRINT="$(build_fingerprint)"
if [[ -x "$BACKEND_DIR/PaperCreatorBackend" \
  && -f "$BACKEND_DIR/.built" \
  && -f "$FINGERPRINT_FILE" \
  && "$(<"$FINGERPRINT_FILE")" == "$CURRENT_FINGERPRINT" ]]; then
  echo "Reusing unchanged standalone backend."
  exit 0
fi

rm -rf "$WORK_DIR" "$BACKEND_DIR"
mkdir -p \
  "$DIST_DIR" \
  "$HELPER_DIR" \
  "$WORK_DIR/pyinstaller-config" \
  "$WORK_DIR/matplotlib-cache" \
  "$WORK_DIR/cache"
export PYINSTALLER_CONFIG_DIR="$WORK_DIR/pyinstaller-config"
export MPLCONFIGDIR="$WORK_DIR/matplotlib-cache"
export XDG_CACHE_HOME="$WORK_DIR/cache"

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
  --collect-all mlx
  --collect-all mlx_lm
  --add-data "$ROOT_DIR/Resources/layout-master-runtime.json:Resources"
  --add-data "$ROOT_DIR/Resources/layout-profiles.json:Resources"
  --add-data "$ROOT_DIR/Resources/generator-registry.json:Resources"
  --add-data "$ROOT_DIR/Resources/ollama-model-recommendations.json:Resources"
  --add-data "$ROOT_DIR/Resources/backend-protocol.schema.json:Resources"
  --add-data "$ROOT_DIR/Resources/generator-capability.schema.json:Resources"
  --add-data "$ROOT_DIR/Resources/empirical-calibration.schema.json:Resources"
  --add-data "$ROOT_DIR/Resources/empirical-calibration-policy.json:Resources"
  --add-data "$ROOT_DIR/Resources/reference-demand-profiles.json:Resources"
  --add-data "$ROOT_DIR/Resources/board-profiles:Resources/board-profiles"
  --add-data "$ROOT_DIR/Backend/Core/fonts:Backend/Core/fonts"
)

while IFS= read -r python_path; do
  PYINSTALLER_ARGS+=(--paths "$ROOT_DIR/Resources/$python_path")
done < <(
  "$PYTHON" -c \
    'from Backend.Core.generator_registry import generator_capabilities; print(*[item.python_path for item in generator_capabilities().values()], sep="\n")'
)

while IFS=$'\t' read -r python_path package; do
  generator_root="$ROOT_DIR/Resources/$python_path"
  while IFS= read -r -d '' module_path; do
    module="${module_path#"$generator_root/"}"
    module="${module%.py}"
    module="${module//\//.}"
    module="${module%.__init__}"
    PYINSTALLER_ARGS+=(--hidden-import "$module")
  done < <(find "$generator_root/$package" -type f -name '*.py' -print0 | sort -z)
done < <(
  "$PYTHON" -c \
    'from Backend.Core.generator_registry import generator_capabilities; print(*[f"{item.python_path}\t{item.package}" for item in generator_capabilities().values()], sep="\n")'
)

while IFS= read -r syllabus_path; do
  destination="Resources/$(dirname "$syllabus_path")"
  PYINSTALLER_ARGS+=(--add-data "$ROOT_DIR/Resources/$syllabus_path:$destination")
done < <(
  "$PYTHON" -c \
    'from Backend.Core.generator_registry import generator_capabilities; print(*[item.syllabus_path for item in generator_capabilities().values()], sep="\n")'
)

PAPER_CREATOR_PYINSTALLER_NATIVE=1 \
  "$PYTHON" -m PyInstaller "${PYINSTALLER_ARGS[@]}" "$ROOT_DIR/bridge.py"

if ! "$DIST_DIR/PaperCreatorBackend/PaperCreatorBackend" bundle-check \
  > "$WORK_DIR/bundle-check.jsonl"; then
  cat "$WORK_DIR/bundle-check.jsonl" >&2
  echo "error: Packaged backend failed its generator health check." >&2
  exit 1
fi
if ! "$DIST_DIR/PaperCreatorBackend/PaperCreatorBackend" mlx-status \
  > "$WORK_DIR/mlx-status.jsonl"; then
  cat "$WORK_DIR/mlx-status.jsonl" >&2
  echo "error: Packaged backend is missing Apple MLX support." >&2
  exit 1
fi

ditto "$DIST_DIR/PaperCreatorBackend" "$BACKEND_DIR"

find "$BACKEND_DIR/_internal/Resources" -type f -exec chmod 0644 {} +
xattr -cr "$BACKEND_DIR"

SIGN_IDENTITY="${EXPANDED_CODE_SIGN_IDENTITY:--}"
HELPER_EXECUTABLE="$BACKEND_DIR/PaperCreatorBackend"
HELPER_ENTITLEMENTS="$ROOT_DIR/macOS/PaperCreator/PaperCreatorBackend.entitlements"
find "$BACKEND_DIR" -type f -print0 |
  while IFS= read -r -d '' file; do
    if /usr/bin/file -b "$file" | grep -q 'Mach-O'; then
      codesign_args=(
        --force
        --sign "$SIGN_IDENTITY"
        --timestamp=none
      )
      # Harden distribution helpers. Ad-hoc direct builds cannot satisfy
      # hardened-runtime library validation for PyInstaller's nested dylibs.
      if [[ "${DISTRIBUTION_MODE:-direct}" == "app-store" || "$SIGN_IDENTITY" != "-" ]]; then
        codesign_args+=(--options runtime)
      fi
      if [[ "${DISTRIBUTION_MODE:-direct}" == "app-store" && "$file" == "$HELPER_EXECUTABLE" ]]; then
        codesign_args+=(
          --identifier com.jamesdurup.PaperCreator.PaperCreatorBackend
          --entitlements "$HELPER_ENTITLEMENTS"
        )
      fi
      /usr/bin/codesign "${codesign_args[@]}" "$file"
    fi
  done

printf '%s\n' "$CURRENT_FINGERPRINT" > "$FINGERPRINT_FILE"
touch "$BACKEND_DIR/.built"
