from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "macOS/scripts/build_apple_intelligence.sh"


def test_ci_runs_the_pure_apple_helper_protocol_regressions():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text()
    assert (
        "swift test --package-path macOS/AppleIntelligenceHelper "
        "--scratch-path macOS/build/apple-helper-tests -Xswiftc -warnings-as-errors"
    ) in workflow


def _fixture(tmp_path: Path, *, store: bool = False, sign_failure: bool = False):
    checkout = tmp_path / "checkout"
    source = checkout / "macOS/scripts/build_apple_intelligence.sh"
    source.parent.mkdir(parents=True)
    calls = tmp_path / "calls.jsonl"
    bin_dir = tmp_path / "binaries"
    bin_dir.mkdir()
    product = tmp_path / "swift-product"
    product.mkdir()
    (product / "KeldinAppleIntelligence").write_text("compiled helper")
    (product / "KeldinAppleIntelligence").chmod(0o755)
    sdk = tmp_path / "SDK"
    sdk.mkdir()
    wrapper = (
        "import json,os,sys\n"
        "from pathlib import Path\n"
        f"calls=Path({str(calls)!r})\n"
        "with calls.open('a') as stream: stream.write(json.dumps(sys.argv[1:])+'\\n')\n"
        "if '--show-bin-path' in sys.argv: print(os.environ['FIXTURE_PRODUCT'])\n"
        "if '--show-sdk-path' in sys.argv: print(os.environ['FIXTURE_SDK'])\n"
        "if '--force' in sys.argv and os.environ.get('FAIL_SIGN')=='1': sys.exit(12)\n"
        "if sys.argv[1:2]==['swiftc'] and os.environ.get('FAIL_CAPABILITY')=='1': sys.exit(1)\n"
    )
    for name in ("xcrun", "codesign"):
        path = bin_dir / name
        path.write_text(
            f'#!/bin/bash\nexec {shlex.quote(sys.executable)} -c {shlex.quote(wrapper)} "$@"\n'
        )
        path.chmod(0o755)
    source.write_text(
        SCRIPT.read_text().replace("/usr/bin/codesign", str(bin_dir / "codesign"))
    )
    return (
        source,
        calls,
        {
            **os.environ,
            "PATH": str(bin_dir) + os.pathsep + "/usr/bin:/bin",
            "SRCROOT": str(checkout / "macOS"),
            "TARGET_BUILD_DIR": str(tmp_path / "products"),
            "CONTENTS_FOLDER_PATH": "Keldin.app/Contents",
            "EXPANDED_CODE_SIGN_IDENTITY": "fixture-personal-identity",
            "DISTRIBUTION_MODE": "app-store" if store else "direct",
            "ARCHS": "arm64",
            "FIXTURE_PRODUCT": str(product),
            "FIXTURE_SDK": str(sdk),
            "FAIL_SIGN": "1" if sign_failure else "0",
        },
    )


def _run(source, env):
    return subprocess.run(
        ["/bin/bash", str(source)], env=env, capture_output=True, text=True, timeout=10
    )


def test_helper_packaging_uses_one_cache_and_rechecks_build_inputs(tmp_path):
    source, calls, env = _fixture(tmp_path)
    for _ in range(2):
        result = _run(source, env)
        assert result.returncode == 0, result.stderr
    commands = [json.loads(line) for line in calls.read_text().splitlines()]
    builds = [
        row
        for row in commands
        if row[:2] == ["swift", "build"] and "--show-bin-path" not in row
    ]
    assert len(builds) == 2
    assert builds[0] == builds[1]
    cache = builds[0][builds[0].index("--scratch-path") + 1]
    assert cache.endswith("/macOS/AppleIntelligenceHelper/.build")
    assert "DerivedData" not in cache
    target = (
        Path(env["TARGET_BUILD_DIR"])
        / env["CONTENTS_FOLDER_PATH"]
        / "Helpers/KeldinAppleIntelligence"
    )
    assert target.read_text() == "compiled helper"
    assert any(row[:2] == ["--verify", "--strict"] for row in commands)


def test_store_helper_inherits_sandbox_and_is_hardened(tmp_path):
    source, calls, env = _fixture(tmp_path, store=True)
    assert _run(source, env).returncode == 0
    commands = [json.loads(line) for line in calls.read_text().splitlines()]
    sign = next(row for row in commands if "--force" in row)
    assert sign[sign.index("--sign") + 1] == "fixture-personal-identity"
    assert sign[sign.index("--options") + 1] == "runtime"
    assert sign[sign.index("--entitlements") + 1].endswith(
        "Keldin/KeldinBackend.entitlements"
    )
    assert (
        sign[sign.index("--identifier") + 1]
        == "com.jamesdurup.Keldin.AppleIntelligence"
    )


def test_signing_failure_does_not_replace_existing_helper(tmp_path):
    source, _, env = _fixture(tmp_path, sign_failure=True)
    target = (
        Path(env["TARGET_BUILD_DIR"])
        / env["CONTENTS_FOLDER_PATH"]
        / "Helpers/KeldinAppleIntelligence"
    )
    target.parent.mkdir(parents=True)
    target.write_text("previous helper")
    assert _run(source, env).returncode != 0
    assert target.read_text() == "previous helper"


def test_python_backend_cache_cannot_skip_native_packaging():
    source = (ROOT / "macOS/scripts/build_backend.sh").read_text()
    assert source.index(
        '"$SRCROOT/scripts/build_apple_intelligence.sh"'
    ) < source.index('CURRENT_FINGERPRINT="$(build_fingerprint)"')
    project = (ROOT / "macOS/project.yml").read_text()
    for filename in ("Package.swift", "Main.swift", "Protocol.swift", "Schema.swift"):
        assert filename in project
    assert "$(CONTENTS_FOLDER_PATH)/Helpers/KeldinAppleIntelligence" in project


def test_release_preflight_checks_native_helper_sandbox_and_signature():
    source = (ROOT / "macOS/Makefile").read_text()
    assert (
        "APP_STORE_APPLE_HELPER_PATH := $(APP_STORE_APP_PATH)/Contents/Helpers/KeldinAppleIntelligence"
        in source
    )
    assert (
        'codesign --verify --strict --verbose=2 "$(APP_STORE_APPLE_HELPER_PATH)"'
        in source
    )
    for entitlement in ("app-sandbox", "inherit"):
        assert f"security\\.{entitlement}" in source
    assert 'codesign -dvvv "$(APP_STORE_APPLE_HELPER_PATH)"' in source


def test_old_os_and_sdk_keep_a_bounded_unavailable_path():
    package = (ROOT / "macOS/AppleIntelligenceHelper/Package.swift").read_text()
    main = (
        ROOT
        / "macOS/AppleIntelligenceHelper/Sources/KeldinAppleIntelligence/Main.swift"
    ).read_text()
    assert "platforms: [.macOS(.v15)]" in package
    assert "#if canImport(FoundationModels)" in main
    assert "guard #available(macOS 26.4, *)" in main
    assert "return errorResponse(.unavailable, requestID: request.requestID)" in main


def test_intermediate_sdk_builds_stub_when_required_api_probe_fails(tmp_path):
    for available in (True, False):
        source, calls, env = _fixture(tmp_path / str(available))
        result = _run(source, {**env, "FAIL_CAPABILITY": "0" if available else "1"})
        assert result.returncode == 0, result.stderr
        commands = [json.loads(line) for line in calls.read_text().splitlines()]
        probe = next(row for row in commands if row[:1] == ["swiftc"])
        assert "-typecheck" in probe
        assert any(value.endswith("CapabilityProbe.swift") for value in probe)
        build = next(row for row in commands if row[:2] == ["swift", "build"])
        assert ("-DKELDIN_FOUNDATION_MODELS_CAPABLE" in build) is available
    main = (
        ROOT
        / "macOS/AppleIntelligenceHelper/Sources/KeldinAppleIntelligence/Main.swift"
    ).read_text()
    assert "canImport(FoundationModels) && KELDIN_FOUNDATION_MODELS_CAPABLE" in main


def test_sdk_probe_covers_the_unified_error_symbols_used_by_helper():
    probe = (ROOT / "macOS/AppleIntelligenceHelper/CapabilityProbe.swift").read_text()
    for symbol in (
        "LanguageModelError",
        ".contextSizeExceeded",
        ".unsupportedGenerationGuide",
        ".unsupportedLanguageOrLocale",
    ):
        assert symbol in probe
