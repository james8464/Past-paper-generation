from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ECONOMICS_PACK_ROOT = REPO_ROOT / "a-levels" / "economics" / "edexcel-a"
CS_PACK_ROOT = REPO_ROOT / "a-levels" / "computer-science" / "aqa"
ECONOMICS_ROOT = ECONOMICS_PACK_ROOT / "generator"
CS_ROOT = CS_PACK_ROOT / "generator"
