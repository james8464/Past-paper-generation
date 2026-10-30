# Public identity changes must not orphan existing documents or credentials.

import hashlib
import json
import plistlib
import re
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "macOS/Keldin"


def test_native_test_host_and_bundle_share_the_personal_signing_team():
    source = (ROOT / "macOS/project.yml").read_text()
    test_target = source.split("  KeldinTests:", 1)[1]
    assert "DEVELOPMENT_TEAM: Z29CKRV8C9" in test_target
    assert "CODE_SIGN_STYLE: Automatic" in test_target
    project = (ROOT / "macOS/Keldin.xcodeproj/project.pbxproj").read_text()
    configurations = re.findall(
        r'/\* (Debug|Release) configuration for PBXNativeTarget "(Keldin(?:Tests)?)" \*/ = \{'
        r".*?buildSettings = \{(.*?)\n\t\t\t\};",
        project,
        re.DOTALL,
    )
    assert len(configurations) == 4
    for configuration, target, settings in configurations:
        assert "DEVELOPMENT_TEAM = Z29CKRV8C9;" in settings, (
            configuration,
            target,
        )
        assert "CODE_SIGN_STYLE = Automatic;" in settings


def test_startup_migration_failure_uses_selected_language_and_preserves_copy():
    source = (APP / "Application/KeldinApp.swift").read_text()
    branch = source.split("if !failures.isEmpty {", 1)[1].split(
        "application.showError = true", 1
    )[0]
    assert re.search(
        r"application\.errorMessage\s*=\s*InterfaceText\.resolve\(", branch
    )
    assert re.search(
        r'language:\s*UserDefaults\.standard\.string\(forKey: "interfaceLanguage"\)\s*\?\?\s*"system"',
        branch,
    )
    english = "Some previous app data could not be imported. Use Import previous app data in Output Settings to retry."
    assert english in branch
    catalog = json.loads((APP / "Localizable.xcstrings").read_text())
    entry = catalog["strings"][english]
    expected = {
        "en": english,
        "fr": "Certaines données de l’ancienne app n’ont pas pu être importées. Réessayez avec l’option d’import des données de l’ancienne app dans les réglages Sortie.",
    }
    for language, text in expected.items():
        unit = entry.get("localizations", {}).get(language, {}).get("stringUnit", {})
        assert unit.get("value", english) == text


def test_native_app_copy_uses_plain_punctuation():
    offenders = [
        str(path.relative_to(ROOT))
        for path in APP.rglob("*.swift")
        if re.search("[\u2013\u2014]", path.read_text())
    ]
    assert not offenders, offenders
    catalog = json.loads((APP / "Localizable.xcstrings").read_text())
    for key, entry in catalog["strings"].items():
        assert not re.search("[\u2013\u2014]", key), key
        for language, localization in entry.get("localizations", {}).items():
            value = localization.get("stringUnit", {}).get("value", "")
            assert not re.search("[\u2013\u2014]", value), (key, language)


def test_panel_actions_signal_that_more_input_is_needed():
    for source, label in (
        (
            "Features/Generation/FrenchAssessmentWorkspace.swift",
            "Choose output folder…",
        ),
        (
            "Features/Generation/FrenchAssessmentWorkspace.swift",
            "Record a teacher review…",
        ),
        ("Features/Generation/FrenchAssessmentWorkspace.swift", "Save review…"),
        ("Features/Documents/DocumentPreviewView.swift", "Print…"),
        ("Features/Settings/SettingsPane.swift", "Choose…"),
    ):
        assert f'Button("{label}"' in (APP / source).read_text(), (source, label)
    catalog = json.loads((APP / "Localizable.xcstrings").read_text())["strings"]
    assert (
        catalog["%@ (recommended)"]["localizations"]["fr"]["stringUnit"]["value"]
        == "%@ (recommandé)"
    )
    assert (
        catalog["%lld to %lld"]["localizations"]["fr"]["stringUnit"]["value"]
        == "%lld à %lld"
    )


def test_display_and_bundle_identity_use_keldin():
    info = plistlib.loads((APP / "Info.plist").read_bytes())
    assert info["CFBundleDisplayName"] == "Keldin"
    assert info["CFBundleName"] == "Keldin"
    project = (ROOT / "macOS/project.yml").read_text()
    assert "PRODUCT_BUNDLE_IDENTIFIER: com.jamesdurup.Keldin" in project


def test_main_window_and_help_use_public_name():
    assert 'WindowGroup("Keldin"' in (APP / "Application/KeldinApp.swift").read_text()
    assert (
        '.navigationTitle("Keldin")'
        in (APP / "Navigation/SidebarView.swift").read_text()
    )
    commands = (APP / "Application/AppCommands.swift").read_text()
    assert 'Button(localized("Keldin Help"))' in commands
    # Native router tests cover ordering and recovery; keep this wiring visible.
    assert "navigate(.help(.gettingStarted))" in commands
    catalog = json.loads((APP / "Localizable.xcstrings").read_text())["strings"]
    assert (
        catalog["Keldin Help"]["localizations"]["fr"]["stringUnit"]["value"]
        == "Aide de Keldin"
    )


def test_rebrand_uses_keldin_storage_and_imports_legacy_credentials():
    defaults = (APP / "Application/AppConfiguration.swift").read_text()
    assert '"Keldin/Generated papers"' in defaults
    assert '.appendingPathComponent("Keldin", isDirectory: true)' in defaults
    secrets = (APP / "Services/SecretStore.swift").read_text()
    assert 'baseQuery(account, service: "Keldin")' in secrets
    assert "KeldinMigration.legacyKeychainService" in secrets
    assert (
        "if status == errSecSuccess { SecItemDelete(legacyQuery as CFDictionary) }"
        not in secrets
    )
    launch = (APP / "Application/KeldinApp.swift").read_text()
    assert "KeldinMigration.prepare()" in launch


def test_current_uk_renderers_do_not_publish_the_previous_name():
    from Backend.Core.branding import APP_NAME, PDF_WORDMARK

    assert APP_NAME == "Keldin" and PDF_WORDMARK == "KELDIN"
    sources = [ROOT / "Backend/Core/exam_cover.py", ROOT / "Backend/Core/exam_pages.py"]
    sources.extend((ROOT / "Resources").glob("*/*/generator/*/render_pdf.py"))
    for path in sources:
        assert "paper creator" not in path.read_text().casefold(), path


def test_native_icon_has_seven_editable_glass_layers():
    root = APP / "AppIcon.icon"
    icon = json.loads((root / "icon.json").read_text())
    assert icon["fill"] == "system-light"
    groups = icon["groups"]
    assert len(groups) == 1
    group = groups[0]
    assert len(group["layers"]) == 7
    assert group["refractivity"]["enabled"] is True
    assert group["translucency"]["enabled"] is True
    assert 0 < group["blur-material"] < 1
    assert 0 < group["shadow"]["opacity"] < 1
    palette = {"#FF383C", "#FF2D55", "#FF8D28", "#FFCC00", "#FFFFFF"}
    for layer in group["layers"]:
        asset = root / "Assets" / layer["image-name"]
        assert asset.is_file()
        source = asset.read_text()
        assert "<svg" in source
        fills = set(re.findall(r'fill="(#[A-Fa-f0-9]{6})"', source))
        assert fills and fills <= palette


def test_fallback_icons_and_design_master_match_current_composer_export():
    manifest = json.loads((ROOT / "macOS/Branding/icon-export.json").read_text())
    assert manifest["schema_version"] == 1
    assert manifest["source"] == "macOS/Keldin/AppIcon.icon"
    source_files = {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((APP / "AppIcon.icon").rglob("*"))
        if path.is_file()
    }
    assert manifest["source_files"] == source_files
    assert (
        manifest["source_sha256"]
        == hashlib.sha256(
            json.dumps(source_files, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )
    assert manifest["rendition"] == {"platform": "macOS", "appearance": "Default"}
    fallback = APP / "Assets.xcassets/AppIcon.appiconset"
    images = json.loads((fallback / "Contents.json").read_text())["images"]
    expected = {
        str((fallback / item["filename"]).relative_to(ROOT)): int(
            item["size"].split("x")[0]
        )
        * int(item["scale"].removesuffix("x"))
        for item in images
    }
    expected["Design/AppIcon/Keldin-AppIcon-Master.png"] = 1024
    assert set(manifest["outputs"]) == set(expected)
    for relative, pixels in expected.items():
        data = (ROOT / relative).read_bytes()
        assert data[:8] == b"\x89PNG\r\n\x1a\n", relative
        assert struct.unpack("!II", data[16:24]) == (pixels, pixels), relative
        assert manifest["outputs"][relative] == {
            "pixels": pixels,
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    master = "Design/AppIcon/Keldin-AppIcon-Master.png"
    largest = "macOS/Keldin/Assets.xcassets/AppIcon.appiconset/AppIcon-512x512@2x.png"
    assert (
        manifest["outputs"][master]["sha256"] == manifest["outputs"][largest]["sha256"]
    )
    assert manifest["outputs"][master]["sha256"] not in {
        "731f3eccd049e015ffa4d925b6845be7b3e75ad5da5c111ea1522a84c1625f7e",
        "4c5dbf3721c98200c5eb61cb9d543454dc81bbc01639c12f700f608ad7d41b3f",
    }


def _color_variants(name):
    asset = json.loads(
        (APP / f"Assets.xcassets/{name}.colorset/Contents.json").read_text()
    )
    actual = {}
    for color in asset["colors"]:
        appearances = frozenset(
            (item["appearance"], item["value"]) for item in color.get("appearances", [])
        )
        components = color["color"]["components"]
        actual[appearances] = tuple(
            int(components[key], 16) for key in ("red", "green", "blue")
        )
    return actual


def _contrast(first, second):
    def luminance(rgb):
        components = [value / 255 for value in rgb]
        linear = [
            value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
            for value in components
        ]
        return sum(
            value * weight
            for value, weight in zip(linear, (0.2126, 0.7152, 0.0722), strict=True)
        )

    one, two = luminance(first), luminance(second)
    return (max(one, two) + 0.05) / (min(one, two) + 0.05)


def test_native_controls_use_the_requested_warm_scene_accent():
    assert (
        plistlib.loads((APP / "Info.plist").read_bytes())["NSAccentColorName"]
        == "ControlAccent"
    )
    assert _color_variants("AccentColor") == _color_variants("ForegroundAccent")
    for name in ("project.yml", "Keldin.xcodeproj/project.pbxproj"):
        assert (
            "ASSETCATALOG_COMPILER_GLOBAL_ACCENT_COLOR_NAME: ControlAccent"
            if name.endswith(".yml")
            else "ASSETCATALOG_COMPILER_GLOBAL_ACCENT_COLOR_NAME = ControlAccent;"
        ) in (ROOT / "macOS" / name).read_text()
    source = (APP / "Application/KeldinApp.swift").read_text()
    assert source.count('.tint(Color("AccentColor"))') == 2
    for appearance, rgb in _color_variants("AccentColor").items():
        if ("luminosity", "dark") not in appearance:
            assert _contrast(rgb, (255, 255, 255)) >= 4.5


def test_warm_links_keep_text_contrast_on_light_and_dark_surfaces():
    variants = _color_variants("ForegroundAccent")
    assert variants.keys() == _color_variants("BrandAccent").keys()
    for appearance, rgb in variants.items():
        backdrops = (
            ((30, 30, 30), (44, 44, 44))
            if ("luminosity", "dark") in appearance
            else ((255, 255, 255), (246, 246, 246), (236, 236, 236))
        )
        for backdrop in backdrops:
            assert _contrast(rgb, backdrop) >= 4.5, (appearance, backdrop)


def test_native_selected_and_filled_controls_keep_white_foreground_contrast():
    for appearance, rgb in _color_variants("ControlAccent").items():
        assert _contrast(rgb, (255, 255, 255)) >= 4.5, appearance
    sidebar = (APP / "Navigation/SidebarView.swift").read_text()
    assert '.tint(Color("ControlAccent"))' in sidebar
    style = (APP / "Components/NativeVisualStyle.swift").read_text()
    assert (
        'buttonStyle(.borderedProminent)\n            .tint(Color("ControlAccent"))'
        in style
    )
    for path in (APP / "Features").rglob("*.swift"):
        assert ".buttonStyle(.borderedProminent)" not in path.read_text(), path


def test_segmented_pickers_use_the_safe_native_control_fill():
    count = 0
    for path in APP.rglob("*.swift"):
        lines = path.read_text().splitlines()
        for index, line in enumerate(lines):
            if line.strip() == ".pickerStyle(.segmented)":
                assert lines[index + 1].strip() == '.tint(Color("ControlAccent"))', path
                count += 1
    assert count == 3


def test_external_links_use_the_text_tint_without_retinting_native_controls():
    count = 0
    for path in (APP / "Features").rglob("*.swift"):
        lines = path.read_text().splitlines()
        for index, line in enumerate(lines):
            if re.match(r"\s*Link\(", line):
                assert (
                    lines[index + 1].strip()
                    == '.foregroundStyle(Color("ForegroundAccent"))'
                ), path
                count += 1
    assert count == 8


def test_benchmark_data_stroke_uses_the_foreground_role_not_the_control_fill():
    source = (APP / "Features/Benchmark/BenchmarkView.swift").read_text()
    assert (
        '.tint(Color("ForegroundAccent"))\n                    .chartXAxisLabel'
        in source
    )
    assert ".foregroundStyle(.tint)" in source
    for appearance, rgb in _color_variants("ForegroundAccent").items():
        backdrop = (
            (30, 30, 30) if ("luminosity", "dark") in appearance else (255, 255, 255)
        )
        assert _contrast(rgb, backdrop) >= 3, appearance


def test_active_code_and_build_names_only_use_legacy_identity_in_migration_readers():
    legacy = re.compile(r"paper[ _-]?creator", re.IGNORECASE)
    exceptions = {
        "Backend/Core/legacy_migration.py",
        "macOS/Keldin/Application/KeldinMigration.swift",
    }
    paths = subprocess.check_output(
        ["git", "ls-files"], cwd=ROOT, text=True
    ).splitlines()
    offenders = []
    for name in paths:
        if (
            name.startswith(
                (".codex/", "graphify-out/", "docs/", "tests/", "macOS/Tests/")
            )
            or "/tests/" in name
        ):
            continue
        assert not legacy.search(name), name
        if name in exceptions:
            continue
        try:
            text = (ROOT / name).read_text()
        except UnicodeDecodeError:
            continue
        if legacy.search(text):
            offenders.append(name)
    assert not offenders, offenders
