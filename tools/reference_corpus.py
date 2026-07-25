#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import ssl
import statistics
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = ROOT / "Reference Corpus"
DEFAULT_MANIFEST = DEFAULT_CORPUS / "manifest.json"
DEFAULT_LAYOUT_SUMMARY = ROOT / "Resources" / "layout-profiles.json"
USER_AGENT = "ExamForge-Reference-Corpus/1.0"
ALLOWED_DOWNLOAD_HOSTS = {
    "cdn.sanity.io",
    "filestore.aqa.org.uk",
    "qualifications.pearson.com",
    "www.ocr.org.uk",
    "www.wjec.co.uk",
    "resource.download.wjec.co.uk",
    "ccea.org.uk",
    "www.ccea.org.uk",
}

AQA_RESOURCE_PATTERN = re.compile(
    r'\\"originalFilename\\":\\"(?P<filename>[^\\"]+?\.pdf)\\"'
    r'.*?\\"sha1hash\\":\\"(?P<sha1>[0-9a-f]+)\\"'
    r'.*?\\"size\\":(?P<size>\d+)'
    r'.*?\\"url\\":\\"(?P<url>https:[^\\"]+?\.pdf)\\"'
    r'.*?\\"title\\":\\"(?P<title>[^\\"]+)\\"',
    re.IGNORECASE,
)
AQA_ASSESSMENT_URL_PATTERN = re.compile(
    r"<loc>(https://www\.aqa\.org\.uk/subjects/([^/]+)/a-level/([^<]+)/assessment-resources)</loc>"
)
OCR_ASSESSMENT_URL_PATTERN = re.compile(
    r"<loc>(https://www\.ocr\.org\.uk/qualifications/as-and-a-level/([^<]+?)/assessment)/?</loc>"
)
OCR_RESOURCE_PATTERN = re.compile(
    r'<a\s+href="(?P<url>/Images/[^"]+?\.pdf)"[^>]*>(?P<title>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
PEARSON_COURSE_URL_PATTERN = re.compile(
    r"<loc>(https://qualifications\.pearson\.com/en/qualifications/edexcel-a-levels/[^<]+?\.coursematerials\.html)</loc>"
)
PEARSON_SPEC_PATTERN = re.compile(
    r"category:Pearson-UK:Specification-Code/(?:A-Level/\d+/)?(al\d+-[a-z0-9-]+)",
    re.IGNORECASE,
)
PEARSON_SPEC_ALIASES = {
    # The Mathematics course page uses this presentation code, while its
    # Algolia records use the specification facet below.
    "al17-maths": "maths-2017-as-al",
}


def fetch(url: str, *, timeout: int = 60) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    context = ssl.create_default_context(cafile=_certificate_bundle())
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        return response.read()


def _certificate_bundle() -> str | None:
    try:
        import certifi
    except ImportError:
        return None
    return certifi.where()


def post_json(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json", "User-Agent": USER_AGENT},
        method="POST",
    )
    context = ssl.create_default_context(cafile=_certificate_bundle())
    with urllib.request.urlopen(request, timeout=60, context=context) as response:
        return json.load(response)


def discover_aqa(*, include_accessible: bool = False) -> list[dict[str, Any]]:
    sitemap = fetch("https://www.aqa.org.uk/sitemap.xml").decode("utf-8", errors="replace")
    pages = sorted(set(AQA_ASSESSMENT_URL_PATTERN.findall(sitemap)))
    documents: list[dict[str, Any]] = []
    for page_url, subject, qualification_slug in pages:
        page = fetch(page_url).decode("utf-8", errors="replace")
        overview_url = page_url.removesuffix("/assessment-resources")
        overview = fetch(overview_url).decode("utf-8", errors="replace")
        documents.extend(
            parse_aqa_resources(
                page,
                page_url=page_url,
                subject=subject,
                qualification_slug=qualification_slug,
                include_accessible=include_accessible,
            )
        )
        documents.extend(
            parse_aqa_resources(
                overview,
                page_url=overview_url,
                subject=subject,
                qualification_slug=qualification_slug,
                include_accessible=include_accessible,
            )
        )
    return _deduplicate(documents)


def discover_ocr() -> list[dict[str, Any]]:
    sitemap = fetch("https://www.ocr.org.uk/sitemap.xml/").decode(
        "utf-8", errors="replace"
    )
    pages = sorted(set(OCR_ASSESSMENT_URL_PATTERN.findall(sitemap)))
    documents: list[dict[str, Any]] = []
    for page_url, qualification_slug in pages:
        page = fetch(page_url + "/").decode("utf-8", errors="replace")
        overview_url = page_url.removesuffix("/assessment")
        overview = fetch(overview_url + "/").decode("utf-8", errors="replace")
        subject = _ocr_subject(qualification_slug)
        documents.extend(
            parse_ocr_resources(
                page,
                page_url=page_url + "/",
                subject=subject,
                qualification_slug=qualification_slug,
            )
        )
        documents.extend(
            parse_ocr_specifications(
                overview,
                page_url=overview_url + "/",
                subject=subject,
                qualification_slug=qualification_slug,
            )
        )
    return _deduplicate(documents)


def discover_pearson() -> list[dict[str, Any]]:
    sitemap = fetch("https://qualifications.pearson.com/en/sitemap1.xml").decode(
        "utf-8", errors="replace"
    )
    course_pages = sorted(set(PEARSON_COURSE_URL_PATTERN.findall(sitemap)))
    documents: list[dict[str, Any]] = []
    for page_url in course_pages:
        page = fetch(page_url).decode("utf-8", errors="replace")
        spec_matches = PEARSON_SPEC_PATTERN.findall(page)
        if not spec_matches:
            continue
        page_specification_code = sorted(set(spec_matches), key=len)[0].lower()
        specification_code = PEARSON_SPEC_ALIASES.get(
            page_specification_code, page_specification_code
        )
        app_id = _hidden_value(page, "algoliaAppId")
        api_key = _hidden_value(page, "algoliaAPIKey")
        index_name = _hidden_value(page, "algoliaIndexName")
        if not app_id or not api_key or not index_name:
            continue
        subject = page_url.rsplit("/", 1)[-1].removesuffix(".coursematerials.html")
        endpoint = f"https://{app_id}-dsn.algolia.net/1/indexes/{index_name}/query"
        headers = {
            "x-algolia-application-id": app_id,
            "x-algolia-api-key": api_key,
        }
        page_number = 0
        while True:
            result = post_json(
                endpoint,
                {
                    "query": "",
                    "page": page_number,
                    "hitsPerPage": 1000,
                    "facetFilters": [
                        f"category:Pearson-UK:Specification-Code/{specification_code}"
                    ],
                },
                headers,
            )
            for hit in result.get("hits", []):
                item = parse_pearson_resource(
                    hit,
                    page_url=page_url,
                    subject=subject,
                    qualification_slug=specification_code,
                )
                if item is not None:
                    documents.append(item)
            page_number += 1
            if page_number >= int(result.get("nbPages", 0)):
                break
    return _deduplicate(documents)


def parse_aqa_resources(
    page: str,
    *,
    page_url: str,
    subject: str,
    qualification_slug: str,
    include_accessible: bool = False,
) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    for match in AQA_RESOURCE_PATTERN.finditer(page):
        item = match.groupdict()
        title = item["title"]
        lowered = title.lower()
        kind = _resource_kind(lowered)
        if kind is None:
            continue
        if not include_accessible and any(
            marker in lowered
            for marker in ("modified", "braille", "large print", "tactile")
        ):
            continue
        filename = _safe_filename(item["filename"])
        documents.append(
            {
                "id": f"aqa-{item['sha1'][:16]}",
                "board": "aqa",
                "qualification": "a-level",
                "subject": subject,
                "qualification_slug": qualification_slug,
                "kind": kind,
                "title": title,
                "filename": filename,
                "url": item["url"],
                "source_page": page_url,
                "sha1": item["sha1"],
                "size": int(item["size"]),
            }
        )
    return documents


def parse_ocr_resources(
    page: str,
    *,
    page_url: str,
    subject: str,
    qualification_slug: str,
) -> list[dict[str, Any]]:
    a_level_section = page
    start = page.find('id="specification-tab-1"')
    end = page.find('id="specification-tab-2"', start + 1)
    if start >= 0:
        a_level_section = page[start : end if end >= 0 else len(page)]

    documents: list[dict[str, Any]] = []
    for match in OCR_RESOURCE_PATTERN.finditer(a_level_section):
        title = re.sub(r"<[^>]+>", "", match.group("title"))
        title = " ".join(title.split())
        lowered = title.lower()
        kind = _resource_kind(lowered)
        if kind is None or "erratum" in lowered:
            continue
        if kind == "question-papers" and any(
            marker in lowered for marker in ("insert", "advance notice", "resource booklet")
        ):
            kind = "inserts"
        url = urllib.parse.urljoin("https://www.ocr.org.uk", match.group("url"))
        filename = _safe_filename(urllib.parse.urlparse(url).path)
        documents.append(
            {
                "id": f"ocr-{Path(filename).stem.split('-', 1)[0]}",
                "board": "ocr",
                "qualification": "a-level",
                "subject": subject,
                "qualification_slug": qualification_slug,
                "kind": kind,
                "title": title,
                "filename": filename,
                "url": url,
                "source_page": page_url,
            }
        )
    return documents


def parse_ocr_specifications(
    page: str,
    *,
    page_url: str,
    subject: str,
    qualification_slug: str,
) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    for match in OCR_RESOURCE_PATTERN.finditer(page):
        title = re.sub(r"<[^>]+>", "", match.group("title"))
        title = " ".join(title.split())
        lowered = title.lower()
        if "a level specification" not in lowered or "as level" in lowered:
            continue
        url = urllib.parse.urljoin("https://www.ocr.org.uk", match.group("url"))
        filename = _safe_filename(urllib.parse.urlparse(url).path)
        documents.append(
            {
                "id": f"ocr-{Path(filename).stem.split('-', 1)[0]}",
                "board": "ocr",
                "qualification": "a-level",
                "subject": subject,
                "qualification_slug": qualification_slug,
                "kind": "specifications",
                "title": title,
                "filename": filename,
                "url": url,
                "source_page": page_url,
            }
        )
    return documents


def parse_pearson_resource(
    hit: dict[str, Any],
    *,
    page_url: str,
    subject: str,
    qualification_slug: str,
) -> dict[str, Any] | None:
    if hit.get("extension", "").lower() != "pdf" or hit.get("gating", False):
        return None
    categories = [str(value) for value in hit.get("category", [])]
    kind = None
    category_text = " ".join(categories).lower()
    if "document-type/question-paper" in category_text:
        kind = "question-papers"
    elif "document-type/mark-scheme" in category_text:
        kind = "mark-schemes"
    elif any(
        marker in category_text
        for marker in ("document-type/source-booklet", "document-type/insert")
    ):
        kind = "inserts"
    elif "document-type/specification" in category_text:
        kind = "specifications"
    if kind is None:
        return None
    path = str(hit.get("url") or hit.get("id") or "")
    if not path.lower().endswith(".pdf"):
        return None
    if "/secure/" in path.lower():
        return None
    quoted_path = urllib.parse.quote(path, safe="/:%()_+-")
    url = urllib.parse.urljoin("https://qualifications.pearson.com", quoted_path)
    filename = _safe_filename(urllib.parse.urlparse(url).path)
    return {
        "id": f"pearson-{hit.get('objectID') or hashlib.sha1(url.encode()).hexdigest()[:16]}",
        "board": "pearson-edexcel",
        "qualification": "a-level",
        "subject": subject,
        "qualification_slug": qualification_slug,
        "kind": kind,
        "title": str(hit.get("title") or filename),
        "filename": filename,
        "url": url,
        "source_page": page_url,
    }


def write_manifest(documents: Iterable[dict[str, Any]], path: Path) -> None:
    payload = {
        "schema_version": 1,
        "distribution": "development-only",
        "qualification": "a-level",
        "documents": sorted(
            documents,
            key=lambda item: (
                item["board"],
                item["subject"],
                item["qualification_slug"],
                item["kind"],
                item["filename"],
            ),
        ),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def merge_manifest(documents: Iterable[dict[str, Any]], path: Path) -> None:
    existing: list[dict[str, Any]] = []
    if path.exists():
        existing = load_manifest(path).get("documents", [])
    keyed = {
        (item["board"], item.get("sha1") or item["url"]): item
        for item in [*existing, *documents]
    }
    write_manifest(keyed.values(), path)


def replace_board_manifest(
    documents: Iterable[dict[str, Any]], path: Path, *, board: str
) -> None:
    existing: list[dict[str, Any]] = []
    if path.exists():
        existing = [
            item
            for item in load_manifest(path).get("documents", [])
            if item["board"] != board
        ]
    write_manifest([*existing, *documents], path)


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def download_manifest(
    manifest_path: Path,
    corpus_root: Path,
    *,
    workers: int = 4,
    board: str | None = None,
    subject: str | None = None,
) -> tuple[int, int, list[dict[str, str]]]:
    documents = load_manifest(manifest_path)["documents"]
    selected = [
        item
        for item in documents
        if (board is None or item["board"] == board)
        and (subject is None or item["subject"] == subject)
    ]
    downloaded = 0
    existing = 0
    failures: list[dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {
            pool.submit(_download_one, item, corpus_root): item
            for item in selected
        }
        for future in as_completed(futures):
            item = futures[future]
            try:
                changed = future.result()
            except Exception as error:  # Continue through stale/gated index records.
                failures.append(
                    {
                        "id": str(item["id"]),
                        "url": str(item["url"]),
                        "error": f"{type(error).__name__}: {error}",
                    }
                )
                continue
            downloaded += int(changed)
            existing += int(not changed)
    return downloaded, existing, failures


def profile_manifest(
    manifest_path: Path,
    corpus_root: Path,
    *,
    board: str | None = None,
    subject: str | None = None,
    kind: str | None = None,
    workers: int = 4,
    max_per_subject: int | None = None,
    missing_groups_only: bool = False,
) -> tuple[int, int, list[dict[str, str]]]:
    documents = load_manifest(manifest_path)["documents"]
    selected = [
        item
        for item in documents
        if (board is None or item["board"] == board)
        and (subject is None or item["subject"] == subject)
        and (kind is None or item["kind"] == kind)
    ]
    if missing_groups_only:
        covered = {
            (item["board"], item["subject"])
            for item in selected
            if document_path(item, corpus_root).with_suffix(".layout.json").exists()
        }
        seen_missing: set[tuple[str, str]] = set()
        selected = [
            item
            for item in selected
            if (item["board"], item["subject"]) not in covered
            and not (
                (item["board"], item["subject"]) in seen_missing
                or seen_missing.add((item["board"], item["subject"]))
            )
        ]
    if max_per_subject is not None:
        counts: Counter[tuple[str, str]] = Counter()
        limited = []
        for item in selected:
            key = (item["board"], item["subject"])
            if counts[key] >= max_per_subject:
                continue
            counts[key] += 1
            limited.append(item)
        selected = limited
    created = 0
    missing = 0
    failures: list[dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {}
        for item in selected:
            pdf_path = document_path(item, corpus_root)
            if not pdf_path.exists():
                missing += 1
                continue
            futures[pool.submit(_profile_one, pdf_path)] = item
        for future in as_completed(futures):
            item = futures[future]
            try:
                future.result()
            except Exception as error:
                failures.append(
                    {
                        "id": str(item["id"]),
                        "path": str(document_path(item, corpus_root)),
                        "error": f"{type(error).__name__}: {error}",
                    }
                )
                continue
            created += 1
    return created, missing, failures


def _profile_one(pdf_path: Path) -> None:
    profile_path = pdf_path.with_suffix(".layout.json")
    temporary = profile_path.with_suffix(profile_path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(profile_pdf(pdf_path), indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(profile_path)


def profile_pdf(path: Path) -> dict[str, Any]:
    try:
        import fitz
    except ImportError as error:
        raise SystemExit("PyMuPDF is required: python3 -m pip install pymupdf") from error

    document = fitz.open(path)
    sizes: Counter[tuple[float, float]] = Counter()
    fonts: Counter[tuple[str, float]] = Counter()
    stroke_widths: Counter[float] = Counter()
    page_margins: list[dict[str, float]] = []
    image_count = 0
    drawing_count = 0
    text_blocks = 0

    for page in document:
        width = round(page.rect.width, 2)
        height = round(page.rect.height, 2)
        sizes[(width, height)] += 1
        boxes: list[tuple[float, float, float, float]] = []
        text = page.get_text("dict")
        for block in text.get("blocks", []):
            if block.get("type") != 0:
                continue
            text_blocks += 1
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    value = span.get("text", "").strip()
                    if not value:
                        continue
                    box = tuple(float(value) for value in span["bbox"])
                    boxes.append(box)
                    fonts[(span.get("font", "unknown"), round(float(span.get("size", 0)), 1))] += len(value)
        for drawing in page.get_drawings():
            drawing_count += 1
            stroke_widths[round(float(drawing.get("width") or 0), 2)] += 1
        image_count += len(page.get_images(full=True))
        if boxes:
            left = min(box[0] for box in boxes)
            top = min(box[1] for box in boxes)
            right = max(box[2] for box in boxes)
            bottom = max(box[3] for box in boxes)
            page_margins.append(
                {
                    "left": round(left, 2),
                    "top": round(top, 2),
                    "right": round(width - right, 2),
                    "bottom": round(height - bottom, 2),
                }
            )

    document.close()
    return {
        "schema_version": 1,
        "source_sha256": _digest(path, "sha256"),
        "pages": sum(sizes.values()),
        "page_sizes": [
            {"width": width, "height": height, "count": count}
            for (width, height), count in sizes.most_common()
        ],
        "median_text_margins": _median_margins(page_margins),
        "fonts": [
            {"family": family, "size": size, "characters": count}
            for (family, size), count in fonts.most_common(20)
        ],
        "stroke_widths": [
            {"width": width, "count": count}
            for width, count in stroke_widths.most_common(12)
        ],
        "text_blocks": text_blocks,
        "drawings": drawing_count,
        "images": image_count,
    }


def summarize_profiles(
    manifest_path: Path, corpus_root: Path, output_path: Path
) -> int:
    documents = load_manifest(manifest_path)["documents"]
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for item in documents:
        if item["kind"] != "question-papers":
            continue
        profile_path = document_path(item, corpus_root).with_suffix(".layout.json")
        if not profile_path.exists():
            continue
        grouped.setdefault((item["board"], item["subject"]), []).append(
            load_manifest(profile_path)
        )

    profiles = []
    for (board, subject), items in sorted(grouped.items()):
        page_sizes: Counter[tuple[float, float]] = Counter()
        fonts: Counter[tuple[str, float]] = Counter()
        strokes: Counter[float] = Counter()
        margins: list[dict[str, float]] = []
        page_counts: list[int] = []
        for item in items:
            page_counts.append(int(item["pages"]))
            for size in item["page_sizes"]:
                page_sizes[(size["width"], size["height"])] += size["count"]
            for font in item["fonts"]:
                fonts[(font["family"], font["size"])] += font["characters"]
            for stroke in item["stroke_widths"]:
                strokes[stroke["width"]] += stroke["count"]
            if item["median_text_margins"]:
                margins.append(item["median_text_margins"])
        primary_size = page_sizes.most_common(1)[0][0]
        profiles.append(
            {
                "board": board,
                "subject": subject,
                "question_papers_profiled": len(items),
                "page_count": {
                    "minimum": min(page_counts),
                    "median": statistics.median(page_counts),
                    "maximum": max(page_counts),
                },
                "primary_page_size": {
                    "width": primary_size[0],
                    "height": primary_size[1],
                },
                "median_text_margins": _median_margins(margins),
                "fonts": [
                    {"family": family, "size": size, "characters": count}
                    for (family, size), count in fonts.most_common(8)
                ],
                "stroke_widths": [
                    {"width": width, "count": count}
                    for width, count in strokes.most_common(8)
                ],
            }
        )

    payload = {
        "schema_version": 1,
        "qualification": "a-level",
        "derived_data_only": True,
        "profiles": profiles,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return len(profiles)


def document_path(item: dict[str, Any], corpus_root: Path) -> Path:
    return (
        corpus_root
        / item["qualification"]
        / item["board"]
        / item["subject"]
        / item["qualification_slug"]
        / item["kind"]
        / _safe_filename(item["filename"])
    )


def _download_one(item: dict[str, Any], corpus_root: Path) -> bool:
    url = item["url"]
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    if urllib.parse.urlparse(url).scheme != "https" or host not in ALLOWED_DOWNLOAD_HOSTS:
        raise ValueError(f"Refusing non-official download host: {url}")
    target = document_path(item, corpus_root)
    if target.exists():
        expected_existing = item.get("sha1")
        if not expected_existing or _digest(target, "sha1") == expected_existing:
            return False
    expected = item.get("sha1")
    content = b""
    for attempt in range(3):
        content = fetch(url, timeout=120)
        actual = hashlib.sha1(content).hexdigest()
        if content.startswith(b"%PDF") and (not expected or actual == expected):
            break
        if attempt < 2:
            time.sleep(attempt + 1)
    if not content.startswith(b"%PDF"):
        raise ValueError(f"Downloaded file is not a PDF: {url}")
    if expected and hashlib.sha1(content).hexdigest() != expected:
        raise ValueError(f"SHA-1 mismatch for {url}")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".download")
    temporary.write_bytes(content)
    temporary.replace(target)
    return True


def _resource_kind(title: str) -> str | None:
    if title.startswith("question paper"):
        return "question-papers"
    if title.startswith("mark scheme"):
        return "mark-schemes"
    if title.startswith("insert"):
        return "inserts"
    if "specification" in title:
        return "specifications"
    return None


def _ocr_subject(qualification_slug: str) -> str:
    match = re.match(r"(.+?)-(?:h|j|f)\d", qualification_slug)
    return match.group(1) if match else qualification_slug


def _hidden_value(page: str, class_name: str) -> str | None:
    match = re.search(
        rf'<input[^>]+value="([^"]+)"[^>]+class="{re.escape(class_name)}"',
        page,
        re.IGNORECASE,
    )
    return match.group(1) if match else None


def _safe_filename(value: str) -> str:
    name = Path(value.replace("\\", "/")).name
    cleaned = re.sub(r"[^A-Za-z0-9._()+ -]", "_", name).strip(" .")
    if not cleaned:
        raise ValueError("Empty filename")
    return cleaned


def _deduplicate(documents: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for item in documents:
        unique[item.get("sha1") or item["url"]] = item
    return list(unique.values())


def _digest(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _median_margins(margins: list[dict[str, float]]) -> dict[str, float] | None:
    if not margins:
        return None
    return {
        key: round(statistics.median(item[key] for item in margins), 2)
        for key in ("left", "top", "right", "bottom")
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage development-only exam references.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser("discover-aqa")
    discover.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    discover.add_argument("--include-accessible", action="store_true")

    discover_ocr_parser = subparsers.add_parser("discover-ocr")
    discover_ocr_parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)

    discover_pearson_parser = subparsers.add_parser("discover-pearson")
    discover_pearson_parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)

    download = subparsers.add_parser("download")
    download.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    download.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    download.add_argument("--workers", type=int, default=4)
    download.add_argument("--board")
    download.add_argument("--subject")

    profile = subparsers.add_parser("profile")
    profile.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    profile.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    profile.add_argument("--board")
    profile.add_argument("--subject")
    profile.add_argument("--kind")
    profile.add_argument("--workers", type=int, default=4)
    profile.add_argument("--max-per-subject", type=int)
    profile.add_argument("--missing-groups-only", action="store_true")

    summarize = subparsers.add_parser("summarize")
    summarize.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    summarize.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    summarize.add_argument("--output", type=Path, default=DEFAULT_LAYOUT_SUMMARY)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "discover-aqa":
        documents = discover_aqa(include_accessible=args.include_accessible)
        replace_board_manifest(documents, args.manifest, board="aqa")
        print(f"Discovered {len(documents)} AQA A-level reference PDFs.")
        return 0
    if args.command == "discover-ocr":
        documents = discover_ocr()
        replace_board_manifest(documents, args.manifest, board="ocr")
        print(f"Discovered {len(documents)} OCR A-level reference PDFs.")
        return 0
    if args.command == "discover-pearson":
        documents = discover_pearson()
        replace_board_manifest(documents, args.manifest, board="pearson-edexcel")
        print(f"Discovered {len(documents)} Pearson Edexcel A-level reference PDFs.")
        return 0
    if args.command == "download":
        downloaded, existing, failures = download_manifest(
            args.manifest,
            args.corpus,
            workers=args.workers,
            board=args.board,
            subject=args.subject,
        )
        suffix = f"-{args.board}" if args.board else ""
        failure_path = args.corpus / f"download-errors{suffix}.json"
        if failures:
            failure_path.parent.mkdir(parents=True, exist_ok=True)
            failure_path.write_text(
                json.dumps(failures, indent=2) + "\n", encoding="utf-8"
            )
        elif failure_path.exists():
            failure_path.unlink()
        print(
            f"Downloaded {downloaded}; already present {existing}; "
            f"inaccessible {len(failures)}."
        )
        return 0
    if args.command == "profile":
        created, missing, failures = profile_manifest(
            args.manifest,
            args.corpus,
            board=args.board,
            subject=args.subject,
            kind=args.kind,
            workers=args.workers,
            max_per_subject=args.max_per_subject,
            missing_groups_only=args.missing_groups_only,
        )
        print(
            f"Created {created} layout profiles; missing PDFs {missing}; "
            f"failed {len(failures)}."
        )
        return 0
    if args.command == "summarize":
        count = summarize_profiles(args.manifest, args.corpus, args.output)
        print(f"Wrote {count} board/subject layout profiles to {args.output}.")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
