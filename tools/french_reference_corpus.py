"""Fetch explicitly registered public French PDFs; never infer redistribution rights."""

import argparse
from collections import defaultdict
from dataclasses import asdict
from datetime import UTC, datetime
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

import pymupdf

from Backend.Core.education_context import NSI_CONTEXT
from Backend.Core.scoped_references import ReferenceIndex, SourceDocument

HOSTS = frozenset({"www.education.gouv.fr", "education.gouv.fr", "eduscol.education.gouv.fr", "eduscol.education.fr", "sti.eduscol.education.fr"})
MAX_BYTES = 30 * 1024 * 1024


def check_url(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in HOSTS or parsed.port not in (None, 443) or parsed.username or parsed.password:
        raise ValueError("Source URL has an unapproved host")


class OfficialRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def check_download(url: str, content: bytes):
    check_url(url)
    if len(content) > MAX_BYTES or not content.startswith(b"%PDF-"):
        raise ValueError("Source response is not a bounded PDF document")


def discover_links(html: str, base_url: str) -> list[str]:
    class Links(HTMLParser):
        def __init__(self):
            super().__init__()
            self.href = None
            self.label = []
            self.urls = set()

        def handle_starttag(self, tag, attrs):
            if tag == "a":
                self.href = dict(attrs).get("href")
                self.label = []

        def handle_data(self, data):
            if self.href:
                self.label.append(data)

        def handle_endtag(self, tag):
            if tag != "a" or not self.href:
                return
            url = urljoin(base_url, self.href)
            label = " ".join(self.label).casefold()
            if ("numérique" in label and "informatique" in label) or re.search(r"\bnsi\b", label):
                try:
                    check_url(url)
                    if urlparse(url).path.endswith(".pdf") or urlparse(url).path.endswith("/download"):
                        self.urls.add(url)
                except ValueError:
                    pass
            self.href = None

    parser = Links()
    parser.feed(html)
    return sorted(parser.urls)


def assign_splits(entries: list[dict]) -> dict[str, str]:
    """Freeze this result before authoring; one in five papers per session held out."""
    groups = defaultdict(list)
    result = {entry["id"]: "reference" for entry in entries}
    for entry in entries:
        if entry["category"] == "official_paper":
            groups[entry["session"]].append(entry["id"])
    for identifiers in groups.values():
        ordered = sorted(identifiers, key=lambda value: sha256(value.encode()).hexdigest())
        for identifier in ordered[:max(1, len(ordered) // 5)]:
            result[identifier] = "holdout"
    return result


def ingest(register: Path, output: Path) -> dict:
    payload = json.loads(register.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("Unsupported French source register")
    output.mkdir(parents=True, exist_ok=True)
    report = {"schema_version": 1, "complete_archive": False, "documents": [], "failures": []}
    opener = build_opener(OfficialRedirects())
    with ReferenceIndex(output / "references.sqlite") as index:
        for entry in payload["documents"]:
            try:
                check_url(entry["url"])
                if not re.fullmatch(r"[a-z0-9-]+", entry["id"]):
                    raise ValueError("Unsafe document identifier")
                destination = output / f"{entry['id']}.pdf"
                if destination.exists():
                    content = destination.read_bytes()
                else:
                    with opener.open(Request(entry["url"], headers={"User-Agent": "PaperCreator-ReferenceAudit/1"}), timeout=45) as response:
                        content = response.read(MAX_BYTES + 1)
                        check_download(response.url, content)
                check_download(entry["url"], content)
                digest = sha256(content).hexdigest()
                if entry.get("sha256") and digest != entry["sha256"]:
                    raise ValueError("Pinned source hash mismatch")
                with pymupdf.open(stream=content, filetype="pdf") as pdf:
                    pages = [(number + 1, page.get_text()) for number, page in enumerate(pdf) if page.get_text().strip()]
                    metrics = [{"page": number + 1, "width": page.rect.width, "height": page.rect.height,
                                "fonts": sorted({font[3] for font in page.get_fonts()})} for number, page in enumerate(pdf)]
                # A previously ingested source retains its acquisition date.
                previous = index.connection.execute("SELECT metadata FROM sources WHERE id=?", (entry["id"],)).fetchone()
                retrieved = json.loads(previous[0])["retrieved_at"] if previous else datetime.now(UTC).isoformat()
                source = SourceDocument(
                    id=entry["id"], context=NSI_CONTEXT, curriculum_version="nsi-2019",
                    category=entry["category"], authority=entry["authority"], url=entry["url"],
                    retrieved_at=retrieved, sha256=digest, session=entry["session"],
                    centre=entry["centre"], rights=entry["rights"], split=entry["split"],
                )
                index.add(source, content, pages)
                if not destination.exists():
                    destination.write_bytes(content)
                report["documents"].append({**asdict(source), "page_metrics": metrics})
            except Exception as error:
                report["failures"].append({"id": entry["id"], "error": str(error)})
    (output / "manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = ingest(args.register, args.output)
    print(json.dumps({"downloaded": len(report["documents"]), "failures": report["failures"], "complete_archive": False}, ensure_ascii=False))
    return bool(report["failures"])


if __name__ == "__main__":
    raise SystemExit(main())
