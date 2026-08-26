from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLI_PATHS = [
    ROOT / "Resources/accounting/aqa/generator/aqaaccountgen/cli.py",
    ROOT / "Resources/business/aqa/generator/aqabizgen/cli.py",
    ROOT / "Resources/computer-science/aqa/generator/cspapergen/cli.py",
    ROOT / "Resources/computer-science/ocr/generator/ocrcsgen/cli.py",
    ROOT / "Resources/economics/aqa/generator/aqaecongen/cli.py",
    ROOT / "Resources/economics/edexcel-a/generator/pastpapergen/cli.py",
    ROOT / "Resources/economics/ocr/generator/ocregen/cli.py",
]
RENDERERS = {
    "render_question_paper",
    "render_mark_scheme",
    "render_source_booklet",
}


def _call_name(call: ast.Call) -> str | None:
    return call.func.id if isinstance(call.func, ast.Name) else None


@pytest.mark.parametrize("path", CLI_PATHS, ids=lambda path: path.parent.name)
def test_production_pdf_renderers_run_inside_atomic_transactions(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    parents: dict[ast.AST, ast.AST] = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    renderer_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _call_name(node) in RENDERERS
    ]

    assert renderer_calls, f"{path} has no PDF renderer calls"
    assert "Backend.Core.family_adapter" in source
    assert "run_family_adapter" in source
    for renderer_call in renderer_calls:
        ancestor = parents.get(renderer_call)
        while ancestor is not None and not (
            isinstance(ancestor, ast.Lambda)
        ):
            ancestor = parents.get(ancestor)
        assert ancestor is not None, (
            f"{path}:{renderer_call.lineno} must pass {_call_name(renderer_call)} "
            "as a deferred ArtifactSpec renderer"
        )


def test_shared_family_adapter_owns_atomic_pdf_transaction() -> None:
    path = ROOT / "Backend/Core/family_adapter.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _call_name(node) == "render_pdf_atomically"
    ]

    assert len(calls) == 1
    call = calls[0]
    assert any(
        isinstance(argument, ast.Attribute)
        and argument.attr == "renderer"
        for argument in call.args
    )
