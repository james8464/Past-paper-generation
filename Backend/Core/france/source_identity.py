"""Bind resumable work to its implementation so a version label alone cannot validate it."""

import sys
from hashlib import sha256

from Backend.Core.paths import REPO_ROOT


def implementation_identity() -> str:
    from pathlib import Path

    if getattr(sys, "frozen", False):
        files = [Path(sys.executable)]
    else:
        files = sorted((REPO_ROOT / "Backend" / "Core").rglob("*.py"))
    # Hash source bytes, including comments, so even prose edits change this identity.
    files += sorted((REPO_ROOT / "Resources" / "france").rglob("*.json"))
    result = sha256()
    for path in files:
        # Names distinguish identical content moved between modules. Absolute
        # machine-specific roots never enter the identity.
        name = (
            str(path.relative_to(REPO_ROOT))
            if path.is_relative_to(REPO_ROOT)
            else path.name
        )
        result.update(name.encode() + b"\0")
        result.update(sha256(path.read_bytes()).digest())
    return result.hexdigest()
