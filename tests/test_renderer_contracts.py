from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

import pytest

from Backend.Core.document_dsl import DocumentRole, RendererContract

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = (
    ("Resources/accounting/aqa/generator", "aqaaccountgen.render_pdf", "aqa"),
    ("Resources/business/aqa/generator", "aqabizgen.render_pdf", "aqa"),
    ("Resources/computer-science/aqa/generator", "cspapergen.render_pdf", "aqa"),
    ("Resources/computer-science/ocr/generator", "ocrcsgen.render_pdf", "ocr"),
    ("Resources/economics/aqa/generator", "aqaecongen.render_pdf", "aqa"),
    (
        "Resources/economics/edexcel-a/generator",
        "pastpapergen.render_pdf",
        "pearson-edexcel",
    ),
    ("Resources/economics/ocr/generator", "ocregen.render_pdf", "ocr"),
)


@pytest.mark.parametrize(("relative_root", "module_name", "profile_id"), FAMILIES)
def test_every_family_declares_shared_renderer_contract(
    relative_root: str,
    module_name: str,
    profile_id: str,
) -> None:
    package_root = str(ROOT / relative_root)
    sys.path.insert(0, package_root)
    try:
        module = importlib.import_module(module_name)
    finally:
        sys.path.remove(package_root)

    contract = module.RENDERER_CONTRACT
    assert isinstance(contract, RendererContract)
    assert contract.profile.id == profile_id
    assert DocumentRole.QUESTION_PAPER in contract.document_roles
    assert DocumentRole.MARK_SCHEME in contract.document_roles
    assert contract.vector_components


def test_renderers_do_not_retain_unreferenced_private_helpers() -> None:
    dead: dict[str, list[str]] = {}
    for relative_root, module_name, _ in FAMILIES:
        module_path = ROOT / relative_root / (module_name.replace(".", "/") + ".py")
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        loaded_names = {
            node.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
        }
        unused = [
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.name.startswith("_")
            and node.name not in loaded_names
        ]
        if unused:
            dead[str(module_path.relative_to(ROOT))] = unused

    assert dead == {}
