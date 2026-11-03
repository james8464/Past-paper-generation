"""Interactive navigation fixtures must not write the operator's app preferences."""

from pathlib import Path


def test_controlled_navigation_root_owns_its_app_storage():
    root = Path(__file__).resolve().parents[1]
    source = (
        root / "macOS/Tests/GenerationNavigationInteractiveTests.swift"
    ).read_text()
    method = source.split(
        "func testNavigationDuringControlledGeneration() async throws {", 1
    )[1].split("\n    }", 1)[0]
    hosted_content = method.split("let content = VStack", 1)[1].split(
        "let window = NSWindow", 1
    )[0]
    assert "}.defaultAppStorage(defaults)" in hosted_content
