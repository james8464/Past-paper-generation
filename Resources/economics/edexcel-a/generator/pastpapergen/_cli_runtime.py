# Only CLI imports prepare the shared runtime; importing the package stays pure.

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _prepare_runtime() -> None:
    if importlib.util.find_spec("Backend") is not None:
        return
    source = Path(__file__).resolve()
    root = source.parents[5] if len(source.parents) > 5 else None
    if (
        root is not None
        and source.parent.parent == root / "Resources/economics/edexcel-a/generator"
        and (root / "Backend/Core/family_adapter.py").is_file()
        and (root / "Resources/generator-registry.json").is_file()
    ):
        sys.path.insert(0, str(root))
        return
    raise RuntimeError(
        "The Edexcel command needs the shared Keldin Backend runtime. "
        "Install this generator from a complete Keldin checkout or make the "
        "Keldin runtime importable. The generator wheel alone is not standalone."
    )


_prepare_runtime()
