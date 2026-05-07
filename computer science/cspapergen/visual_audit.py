from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render and compare PDF pages visually.")
    parser.add_argument("reference")
    parser.add_argument("generated")
    parser.add_argument("--out", default="/tmp/cs-paper-visual-audit")
    parser.add_argument("--first", type=int, default=1)
    parser.add_argument("--last", type=int, default=6)
    parser.add_argument("--dpi", type=int, default=120)
    args = parser.parse_args(argv)

    report = audit_pdfs(
        reference=Path(args.reference),
        generated=Path(args.generated),
        output_dir=Path(args.out),
        first=args.first,
        last=args.last,
        dpi=args.dpi,
    )
    print(json.dumps(report, indent=2))
    return 0


def audit_pdfs(reference: Path, generated: Path, output_dir: Path, first: int = 1, last: int = 6, dpi: int = 120) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    reference_dir = output_dir / "reference"
    generated_dir = output_dir / "generated"
    diff_dir = output_dir / "diff"
    for directory in (reference_dir, generated_dir, diff_dir):
        directory.mkdir(parents=True, exist_ok=True)

    _render(reference, reference_dir / "page", first, last, dpi)
    _render(generated, generated_dir / "page", first, last, dpi)

    pages = []
    for page_number in range(first, last + 1):
        ref_png = _page_png(reference_dir, page_number)
        gen_png = _page_png(generated_dir, page_number)
        if not ref_png.exists() or not gen_png.exists():
            continue
        diff_png = diff_dir / f"page-{page_number:02d}.png"
        pages.append(_compare_page(ref_png, gen_png, diff_png, page_number))
    return {"reference": str(reference), "generated": str(generated), "pages": pages, "diff_dir": str(diff_dir)}


def _render(pdf: Path, prefix: Path, first: int, last: int, dpi: int) -> None:
    subprocess.run(["pdftoppm", "-png", "-f", str(first), "-l", str(last), "-r", str(dpi), str(pdf), str(prefix)], check=True)


def _page_png(directory: Path, page_number: int) -> Path:
    return directory / f"page-{page_number:02d}.png"


def _compare_page(reference: Path, generated: Path, diff_path: Path, page_number: int) -> dict[str, object]:
    with Image.open(reference).convert("RGB") as ref, Image.open(generated).convert("RGB") as gen:
        if ref.size != gen.size:
            gen = gen.resize(ref.size)
        diff = ImageChops.difference(ref, gen)
        diff.save(diff_path)
        stat = ImageStat.Stat(diff)
        mean_delta = sum(stat.mean) / len(stat.mean)
        bbox = diff.getbbox()
        changed_pixels = 0
        if bbox:
            gray = diff.convert("L")
            pixels = gray.get_flattened_data() if hasattr(gray, "get_flattened_data") else gray.getdata()
            changed_pixels = sum(1 for pixel in pixels if pixel > 12)
        total_pixels = ref.size[0] * ref.size[1]
    return {
        "page": page_number,
        "mean_delta": round(mean_delta, 3),
        "changed_ratio": round(changed_pixels / total_pixels, 4),
        "diff": str(diff_path),
    }


if __name__ == "__main__":
    raise SystemExit(main())
