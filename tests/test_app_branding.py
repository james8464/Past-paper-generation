"""Public identity changes must not orphan existing documents or credentials."""

import json
import plistlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "macOS/PaperCreator"


def test_display_name_is_keldin_without_changing_bundle_identity():
    info = plistlib.loads((APP / "Info.plist").read_bytes())
    assert info["CFBundleDisplayName"] == "Keldin"
    assert info["CFBundleName"] == "Keldin"
    project = (ROOT / "macOS/project.yml").read_text()
    assert "PRODUCT_BUNDLE_IDENTIFIER: com.jamesdurup.PaperCreator" in project


def test_main_window_and_help_use_public_name():
    assert (
        'WindowGroup("Keldin"'
        in (APP / "Application/PaperCreatorApp.swift").read_text()
    )
    assert (
        '.navigationTitle("Keldin")'
        in (APP / "Navigation/SidebarView.swift").read_text()
    )
    assert (
        'Button("Keldin Help")' in (APP / "Application/AppCommands.swift").read_text()
    )


def test_rebrand_preserves_existing_storage_and_keychain_names():
    defaults = (APP / "Application/AppConfiguration.swift").read_text()
    assert '"Paper creator/Generated papers"' in defaults
    assert '.appendingPathComponent("Paper creator", isDirectory: true)' in defaults
    assert (
        'kSecAttrService as String: "Paper creator"'
        in (APP / "Services/SecretStore.swift").read_text()
    )


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


def test_warm_accent_has_hig_appearance_and_contrast_variants():
    asset = json.loads(
        (APP / "Assets.xcassets/AccentColor.colorset/Contents.json").read_text()
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
    assert actual == {
        frozenset(): (255, 141, 40),
        frozenset({("luminosity", "dark")}): (255, 146, 48),
        frozenset({("contrast", "high")}): (197, 83, 0),
        frozenset({("luminosity", "dark"), ("contrast", "high")}): (255, 160, 86),
    }
