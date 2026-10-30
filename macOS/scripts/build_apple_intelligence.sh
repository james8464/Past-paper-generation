#!/usr/bin/env bash
# Build one reusable native helper, then sign the copy owned by this app bundle.
set -euo pipefail

ROOT_DIR="$(cd "$SRCROOT/.." && pwd)"
PACKAGE_DIR="$ROOT_DIR/macOS/AppleIntelligenceHelper"
SCRATCH_DIR="$PACKAGE_DIR/.build"
DESTINATION_DIR="$TARGET_BUILD_DIR/$CONTENTS_FOLDER_PATH/Helpers"
DESTINATION="$DESTINATION_DIR/KeldinAppleIntelligence"
SIGN_IDENTITY="${EXPANDED_CODE_SIGN_IDENTITY:--}"

if [[ "${ARCHS:-arm64}" != "arm64" ]]; then
  echo "error: The Apple Intelligence helper currently supports the app's arm64 architecture only." >&2
  exit 1
fi

# SwiftPM tracks source, package, compiler and SDK inputs. Always ask it to build:
# the Python helper's independent fingerprint must not hide a native change.
SDK_PATH="$(xcrun --show-sdk-path)"
BUILD_ARGS=(
  --package-path "$PACKAGE_DIR"
  --scratch-path "$SCRATCH_DIR"
  --configuration release
  --arch arm64
  --sdk "$SDK_PATH"
)
# A framework can exist in an older SDK without the 26.4 token-counting APIs.
# Probe those members at compile time; runtime availability alone cannot guard
# symbols the compiler has never seen. The probe does not load a model.
if xcrun swiftc -typecheck -target arm64-apple-macos15.0 -sdk "$SDK_PATH" \
  "$PACKAGE_DIR/CapabilityProbe.swift" > /dev/null 2>&1; then
  BUILD_ARGS+=(-Xswiftc -DKELDIN_FOUNDATION_MODELS_CAPABLE)
else
  echo "Building Apple Intelligence availability stub: required SDK APIs are absent."
fi
xcrun swift build "${BUILD_ARGS[@]}"
PRODUCT_DIR="$(xcrun swift build "${BUILD_ARGS[@]}" --show-bin-path)"
SOURCE="$PRODUCT_DIR/KeldinAppleIntelligence"
if [[ ! -x "$SOURCE" ]]; then
  echo "error: The Apple Intelligence helper build did not produce its executable." >&2
  exit 1
fi

mkdir -p "$DESTINATION_DIR"
TEMPORARY="$(mktemp "$DESTINATION_DIR/.KeldinAppleIntelligence.XXXXXX")"
trap 'rm -f "$TEMPORARY"' EXIT
cp "$SOURCE" "$TEMPORARY"
chmod 0755 "$TEMPORARY"
CODESIGN_ARGS=(--force --sign "$SIGN_IDENTITY" --timestamp=none)
if [[ "${DISTRIBUTION_MODE:-direct}" == "app-store" || "$SIGN_IDENTITY" != "-" ]]; then
  CODESIGN_ARGS+=(--options runtime)
fi
if [[ "${DISTRIBUTION_MODE:-direct}" == "app-store" ]]; then
  CODESIGN_ARGS+=(
    --identifier com.jamesdurup.Keldin.AppleIntelligence
    --entitlements "$ROOT_DIR/macOS/Keldin/KeldinBackend.entitlements"
  )
fi
/usr/bin/codesign "${CODESIGN_ARGS[@]}" "$TEMPORARY"
/usr/bin/codesign --verify --strict --verbose=2 "$TEMPORARY"
mv -f "$TEMPORARY" "$DESTINATION"
