from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ECONOMICS_PACK_ROOT = REPO_ROOT / "Resources" / "economics" / "edexcel-a"
AQA_ECONOMICS_PACK_ROOT = REPO_ROOT / "Resources" / "economics" / "aqa"
OCR_ECONOMICS_PACK_ROOT = REPO_ROOT / "Resources" / "economics" / "ocr"
CS_PACK_ROOT = REPO_ROOT / "Resources" / "computer-science" / "aqa"
OCR_CS_PACK_ROOT = REPO_ROOT / "Resources" / "computer-science" / "ocr"
BUSINESS_PACK_ROOT = REPO_ROOT / "Resources" / "business" / "aqa"
ACCOUNTING_PACK_ROOT = REPO_ROOT / "Resources" / "accounting" / "aqa"
ECONOMICS_ROOT = ECONOMICS_PACK_ROOT / "generator"
AQA_ECONOMICS_ROOT = AQA_ECONOMICS_PACK_ROOT / "generator"
OCR_ECONOMICS_ROOT = OCR_ECONOMICS_PACK_ROOT / "generator"
CS_ROOT = CS_PACK_ROOT / "generator"
OCR_CS_ROOT = OCR_CS_PACK_ROOT / "generator"
BUSINESS_ROOT = BUSINESS_PACK_ROOT / "generator"
ACCOUNTING_ROOT = ACCOUNTING_PACK_ROOT / "generator"
