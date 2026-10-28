# Inspect calibration PDFs with bounded external tools and useful failure context.

from __future__ import annotations

import re
import subprocess
from pathlib import Path

PDF_TOOL_TIMEOUT_SECONDS = 30


def _run_pdf_tool(tool: str, path: Path, *arguments: str) -> str:
    command = [tool, *arguments]
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=PDF_TOOL_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise ValueError(
            f"{tool} timed out after {PDF_TOOL_TIMEOUT_SECONDS} seconds while reading {path}"
        ) from error
    except FileNotFoundError as error:
        raise ValueError(
            f"{tool} was not found while reading {path}; install the Poppler PDF tools"
        ) from error
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or "").strip()[-500:]
        raise ValueError(
            f"{tool} failed while reading {path} (exit {error.returncode}): {detail}"
        ) from error
    except OSError as error:
        raise ValueError(
            f"{tool} could not start while reading {path}: {error}"
        ) from error
    return result.stdout


def pdf_text(path: Path) -> str:
    return _run_pdf_tool("pdftotext", path, "-layout", str(path), "-")


def pdf_page_count(path: Path) -> int:
    info = _run_pdf_tool("pdfinfo", path, str(path))
    match = re.search(r"^Pages:\s+(\d+)$", info, re.MULTILINE)
    if not match or int(match.group(1)) < 1:
        raise ValueError(f"pdfinfo returned an invalid page count for {path}")
    return int(match.group(1))
