#!/usr/bin/env python3
"""Export every legacy icon size from the maintained Icon Composer artwork."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def export_icons(root: Path, ictool: Path) -> None:
    source = root / "macOS/Keldin/AppIcon.icon"
    fallback = root / "macOS/Keldin/Assets.xcassets/AppIcon.appiconset"
    images = json.loads((fallback / "Contents.json").read_text())["images"]
    source_files = {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(source.rglob("*"))
        if path.is_file()
    }
    manifest = {
        "schema_version": 1,
        "source": str(source.relative_to(root)),
        "source_files": source_files,
        "source_sha256": hashlib.sha256(
            json.dumps(source_files, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "rendition": {"platform": "macOS", "appearance": "Default"},
        "outputs": {},
    }
    # Finish all native renders before replacing any tracked artwork.
    with tempfile.TemporaryDirectory(prefix="keldin-icon-export-") as temporary:
        staging = Path(temporary)
        outputs: list[tuple[Path, Path, int]] = []
        for image in images:
            pixels = int(image["size"].split("x")[0]) * int(
                image["scale"].removesuffix("x")
            )
            rendered = staging / image["filename"]
            subprocess.run(
                [
                    str(ictool),
                    str(source),
                    "--export-image",
                    "--output-file",
                    str(rendered),
                    "--platform",
                    "macOS",
                    "--rendition",
                    "Default",
                    "--width",
                    str(pixels),
                    "--height",
                    str(pixels),
                    "--scale",
                    "1",
                ],
                check=True,
            )
            outputs.append((rendered, fallback / image["filename"], pixels))
        largest = staging / "AppIcon-512x512@2x.png"
        outputs.append(
            (largest, root / "Design/AppIcon/Keldin-AppIcon-Master.png", 1024)
        )
        for rendered, destination, pixels in outputs:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(rendered, destination)
            manifest["outputs"][str(destination.relative_to(root))] = {
                "pixels": pixels,
                "sha256": hashlib.sha256(rendered.read_bytes()).hexdigest(),
            }
    (root / "macOS/Branding/icon-export.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ictool", type=Path, help="Override the active Xcode's Icon Composer tool."
    )
    arguments = parser.parse_args()
    developer = Path(subprocess.check_output(["xcode-select", "-p"], text=True).strip())
    ictool = (
        arguments.ictool
        or developer.parent
        / "Applications/Icon Composer.app/Contents/Executables/ictool"
    )
    if not ictool.is_file():
        parser.error(
            "The selected Xcode does not include Icon Composer's ictool. Select a current Xcode or pass --ictool."
        )
    export_icons(Path(__file__).resolve().parents[2], ictool)


if __name__ == "__main__":
    main()
