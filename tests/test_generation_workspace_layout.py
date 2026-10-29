"""Keep generation feedback outside locked settings and documents compact."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATION = ROOT / "macOS/Keldin/Features/Generation"


def test_sidebar_navigation_is_not_disabled_during_generation():
    sidebar = (ROOT / "macOS/Keldin/Navigation/SidebarView.swift").read_text()
    assert ".disabled(application.isRunning)" not in sidebar


def test_progress_is_not_inside_the_disabled_configuration_form():
    source = (GENERATION / "GeneratorWorkspaceView.swift").read_text()
    workspace, configuration = source.split("private struct PaperConfiguration:", 1)
    assert "GenerationProgress()" not in configuration
    assert ".frame(maxHeight: 390)" not in workspace


def test_recent_documents_are_collapsed_by_default_and_height_bounded():
    source = (GENERATION / "GeneratorWorkspaceView.swift").read_text()
    recent = source.split("private struct RecentDocuments:", 1)[1].split(
        "private struct QualityReviewView:", 1
    )[0]
    assert "@State private var isExpanded = false" in recent
    assert "DisclosureGroup(isExpanded: $isExpanded)" in recent
    assert ".frame(height: 160)" in recent
    assert "maxHeight: .infinity" not in recent


def test_french_and_uk_use_the_same_visible_progress_component():
    root = (ROOT / "macOS/Keldin/Navigation/ContentView.swift").read_text()
    french = (GENERATION / "FrenchAssessmentWorkspace.swift").read_text()
    uk = (GENERATION / "GeneratorWorkspaceView.swift").read_text()
    assert ".safeAreaInset(edge: .bottom)" in root
    assert "GenerationProgress()" in root
    assert "GenerationProgress()" not in french
    assert "GenerationProgress()" not in uk
    progress = (GENERATION / "GenerationProgress.swift").read_text()
    assert "application.generationProgress" in progress
    assert "application.status" in progress
    assert "application.cancelGeneration" in progress
    assert "application.generationEstimate" in progress
    assert ".disabled(" not in progress
