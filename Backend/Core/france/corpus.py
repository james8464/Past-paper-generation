"""Fetch explicitly registered public French PDFs; never infer redistribution rights."""

import argparse
import json
import re
import subprocess
import sys
import tempfile
import unicodedata
from collections import defaultdict
from dataclasses import asdict
from datetime import UTC, datetime
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

import pymupdf

from Backend.Core.education_context import NSI_CONTEXT
from Backend.Core.scoped_references import ReferenceIndex, SourceDocument

HOSTS = frozenset(
    {
        "www.education.gouv.fr",
        "education.gouv.fr",
        "eduscol.education.gouv.fr",
        "eduscol.education.fr",
        "sti.eduscol.education.fr",
    }
)
MAX_BYTES = 30 * 1024 * 1024


def check_url(url):
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in HOSTS
        or parsed.port not in (None, 443)
        or parsed.username
        or parsed.password
    ):
        raise ValueError("Source URL has an unapproved host")


class OfficialRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def check_download(url: str, content: bytes):
    check_url(url)
    if len(content) > MAX_BYTES or not content.startswith(b"%PDF-"):
        raise ValueError("Source response is not a bounded PDF document")


def download_with_system_trust(url: str) -> bytes:
    """Use macOS certificate trust when bundled Python cannot reach an official PDF.

    Redirects are deliberately disabled: only a registered canonical URL may be
    fetched by this fallback. TLS verification is never disabled.
    """
    check_url(url)
    with tempfile.TemporaryDirectory(prefix="papercreator-reference-") as folder:
        destination = Path(folder) / "source.pdf"
        subprocess.run(
            [
                "/usr/bin/curl",
                "-q",
                "--fail",
                "--silent",
                "--show-error",
                "--proto",
                "=https",
                "--max-time",
                "45",
                "--max-filesize",
                str(MAX_BYTES),
                "--output",
                str(destination),
                url,
            ],
            check=True,
            timeout=50,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if destination.stat().st_size > MAX_BYTES:
            raise ValueError("Source PDF exceeds the size limit")
        content = destination.read_bytes()
    check_download(url, content)
    return content


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
            if ("numérique" in label and "informatique" in label) or re.search(
                r"\bnsi\b", label
            ):
                try:
                    check_url(url)
                    if urlparse(url).path.endswith(".pdf") or urlparse(
                        url
                    ).path.endswith("/download"):
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
        ordered = sorted(
            identifiers, key=lambda value: sha256(value.encode()).hexdigest()
        )
        for identifier in ordered[: max(1, len(ordered) // 5)]:
            result[identifier] = "holdout"
    return result


def _identifier_part(value: str) -> str:
    plain = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", plain.casefold()).strip("-")


def reconcile_archive_discovery(
    discovery: dict, foundational_documents: list[dict]
) -> dict:
    """Turn a captured official archive index into a frozen acquisition register.

    The split is assigned from metadata before any new paper content is read. Only
    the standard representation becomes a candidate source; enlarged-print and
    braille links remain in the manifest as non-retrieval aliases.
    """
    if discovery.get("schema_version") != 1:
        raise ValueError("Unsupported French archive discovery schema")
    rows = discovery.get("rows")
    if not isinstance(rows, list) or len(rows) != discovery.get("index_rows"):
        raise ValueError("Archive row count does not match the captured index")
    prefix = discovery.get("document_url_prefix", "")
    check_url(prefix)

    files = [
        document.get("file")
        for row in rows
        for document in row.get("documents", [])
    ]
    if any(not isinstance(filename, str) or not filename for filename in files):
        raise ValueError("Archive document is missing its filename")
    urls = [urljoin(prefix, filename) for filename in files]
    if len(urls) != discovery.get("document_links"):
        raise ValueError("Archive link count does not match the captured index")
    if len(set(urls)) != discovery.get("unique_urls"):
        raise ValueError("Archive unique-link count does not match the captured index")
    for url in urls:
        check_url(url)

    papers = []
    variants = []
    identifiers = set()
    for row in rows:
        standard = [
            document
            for document in row.get("documents", [])
            if document.get("format") == "standard"
        ]
        if len(standard) != 1:
            raise ValueError("Each archive row must contain exactly one standard paper")
        identifier = "nsi-{}-{}-{}-{}".format(
            row["year"],
            _identifier_part(row["session"]),
            _identifier_part(row["centre"]),
            _identifier_part(row["description"]),
        )
        if identifier in identifiers:
            suffix = sha256(standard[0]["file"].encode()).hexdigest()[:8]
            identifier = f"{identifier}-{suffix}"
        identifiers.add(identifier)
        paper = {
            "id": identifier,
            "category": "official_paper",
            "authority": "MEN",
            "url": urljoin(prefix, standard[0]["file"]),
            "session": int(row["year"]),
            "centre": row["centre"],
            "rights": "reference-only",
            "split": "reference",
            "exam_session": row["session"],
            "description": row["description"],
            "curriculum_version": "nsi-2019",
            "document_language": "fr-FR",
            "template_eligible": int(row["year"]) >= 2023,
            "historical_format_note": (
                None
                if int(row["year"]) >= 2023
                else "Legacy or exceptional format; never use as a 2027 layout template."
            ),
        }
        papers.append(paper)
        for document in row.get("documents", []):
            if document is standard[0]:
                continue
            variants.append(
                {
                    "canonical_document_id": identifier,
                    "format": document["format"],
                    "url": urljoin(prefix, document["file"]),
                    "retrieval_eligible": False,
                    "reason": "accessibility-representation-of-canonical-paper",
                }
            )

    splits = assign_splits(papers)
    for paper in papers:
        paper["split"] = splits[paper["id"]]
        paper["retrieval_eligible"] = paper["split"] == "reference"

    foundational = [dict(document) for document in foundational_documents]
    if any(document.get("category") == "official_paper" for document in foundational):
        raise ValueError("Foundational documents must not duplicate archive papers")
    return {
        "schema_version": 1,
        "status": "archive-index-reconciled-content-acquisition-pending",
        "scope": "fr-national/bac-general/generale/terminale/nsi/nsi-2019",
        "rights_note": (
            "Local reference inspection only; no source PDFs bundled. Rights and "
            "third-party illustrations require document-specific review."
        ),
        "archive_url": discovery["source"],
        "assessment_rules_url": "https://www.education.gouv.fr/bo/2026/Special4/MENE2622643N",
        "archive_reconciliation": {
            "observed_at": discovery.get("observed_at"),
            "complete_index": True,
            "content_hashes_complete": False,
            "standard_papers": len(papers),
            "accessibility_variants": len(variants),
            "total_links": len(urls),
            "holdout_papers": sum(
                paper["split"] == "holdout" for paper in papers
            ),
        },
        "documents": foundational + papers,
        "archive_variants": variants,
    }


def pin_reconciled_hashes(register: dict, manifest: dict) -> dict:
    """Pin successfully acquired bytes without concealing gaps or duplicates."""
    if manifest.get("failures") or not manifest.get("complete_archive"):
        raise ValueError("Cannot pin an incomplete French archive acquisition")
    by_id = {
        document["id"]: document["sha256"]
        for document in manifest.get("documents", [])
    }
    expected = {document["id"] for document in register.get("documents", [])}
    missing = sorted(expected - by_id.keys())
    if missing:
        raise ValueError(f"Archive manifest is missing documents: {', '.join(missing)}")
    pinned = json.loads(json.dumps(register, ensure_ascii=False))
    for document in pinned["documents"]:
        digest = by_id[document["id"]]
        if not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError(f"Invalid acquired hash for {document['id']}")
        document["sha256"] = digest
    reconciliation = pinned["archive_reconciliation"]
    reconciliation["content_hashes_complete"] = True
    reconciliation["duplicate_content_groups"] = len(
        manifest.get("duplicates", [])
    )
    reconciliation["acquired_documents"] = len(pinned["documents"])
    pinned["status"] = "archive-content-reconciled"
    return pinned


def duplicate_index_policy(documents: list[dict]) -> list[dict]:
    """Choose one indexed identity per byte-identical group.

    When an identical file crosses the holdout boundary, the holdout identity is
    retained so the same bytes can never re-enter retrieval through an alias.
    """
    by_digest = defaultdict(list)
    for document in documents:
        by_digest[document["sha256"]].append(document)
    groups = []
    for digest, copies in sorted(by_digest.items()):
        if len(copies) < 2:
            continue
        ordered_ids = sorted(document["id"] for document in copies)
        held_out = sorted(
            document["id"]
            for document in copies
            if document["split"] == "holdout"
        )
        canonical = held_out[0] if held_out else ordered_ids[0]
        groups.append(
            {
                "sha256": digest,
                "ids": ordered_ids,
                "canonical_id": canonical,
                "excluded_ids": [
                    identifier for identifier in ordered_ids if identifier != canonical
                ],
                "crosses_holdout_boundary": bool(held_out)
                and len(held_out) != len(copies),
            }
        )
    return groups


def prune_unregistered_sources(
    index: ReferenceIndex, registered_ids: set[str]
) -> list[str]:
    existing = {
        row[0] for row in index.connection.execute("SELECT id FROM sources").fetchall()
    }
    stale = sorted(existing - registered_ids)
    if stale:
        with index.connection:
            index.connection.executemany(
                "DELETE FROM chunks WHERE source_id=?",
                [(identifier,) for identifier in stale],
            )
            index.connection.executemany(
                "DELETE FROM sources WHERE id=?",
                [(identifier,) for identifier in stale],
            )
    return stale


def ingest(register: Path, output: Path) -> dict:
    payload = json.loads(register.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("Unsupported French source register")
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": 1,
        "complete_archive": False,
        "documents": [],
        "failures": [],
        "duplicates": [],
    }
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
                    try:
                        with opener.open(
                            Request(
                                entry["url"],
                                headers={"User-Agent": "PaperCreator-ReferenceAudit/1"},
                            ),
                            timeout=45,
                        ) as response:
                            content = response.read(MAX_BYTES + 1)
                            check_download(response.url, content)
                    except URLError:
                        if sys.platform != "darwin":
                            raise
                        content = download_with_system_trust(entry["url"])
                check_download(entry["url"], content)
                digest = sha256(content).hexdigest()
                if entry.get("sha256") and digest != entry["sha256"]:
                    raise ValueError("Pinned source hash mismatch")
                with pymupdf.open(stream=content, filetype="pdf") as pdf:
                    pages = [
                        (number + 1, page.get_text())
                        for number, page in enumerate(pdf)
                        if page.get_text().strip()
                    ]
                    metrics = [
                        {
                            "page": number + 1,
                            "width": page.rect.width,
                            "height": page.rect.height,
                            "fonts": sorted({font[3] for font in page.get_fonts()}),
                        }
                        for number, page in enumerate(pdf)
                    ]
                # A previously ingested source retains its acquisition date.
                previous = index.connection.execute(
                    "SELECT metadata FROM sources WHERE id=?", (entry["id"],)
                ).fetchone()
                retrieved = (
                    json.loads(previous[0])["retrieved_at"]
                    if previous
                    else datetime.now(UTC).isoformat()
                )
                source = SourceDocument(
                    id=entry["id"],
                    context=NSI_CONTEXT,
                    curriculum_version="nsi-2019",
                    category=entry["category"],
                    authority=entry["authority"],
                    url=entry["url"],
                    retrieved_at=retrieved,
                    sha256=digest,
                    session=entry["session"],
                    centre=entry["centre"],
                    rights=entry["rights"],
                    split=entry["split"],
                )
                index.add(source, content, pages)
                if not destination.exists():
                    destination.write_bytes(content)
                report["documents"].append({**asdict(source), "page_metrics": metrics})
            except Exception as error:
                report["failures"].append({"id": entry["id"], "error": str(error)})
    expected_archive = payload.get("archive_reconciliation", {}).get(
        "standard_papers"
    )
    acquired_archive = sum(
        document["category"] == "official_paper"
        for document in report["documents"]
    )
    report["complete_archive"] = bool(
        expected_archive is not None
        and acquired_archive == expected_archive
        and not report["failures"]
    )
    report["duplicates"] = duplicate_index_policy(report["documents"])
    excluded = {
        identifier
        for group in report["duplicates"]
        for identifier in group["excluded_ids"]
    }
    registered_ids = {entry["id"] for entry in payload["documents"]}
    with ReferenceIndex(output / "references.sqlite") as index:
        if excluded:
            with index.connection:
                index.connection.executemany(
                    "DELETE FROM chunks WHERE source_id=?",
                    [(identifier,) for identifier in sorted(excluded)],
                )
                index.connection.executemany(
                    "DELETE FROM sources WHERE id=?",
                    [(identifier,) for identifier in sorted(excluded)],
                )
        report["stale_index_sources_removed"] = prune_unregistered_sources(
            index, registered_ids
        )
    for document in report["documents"]:
        document["indexed"] = document["id"] not in excluded
    (output / "manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = ingest(args.register, args.output)
    print(
        json.dumps(
            {
                "downloaded": len(report["documents"]),
                "failures": report["failures"],
                "complete_archive": report["complete_archive"],
                "duplicates": len(report["duplicates"]),
            },
            ensure_ascii=False,
        )
    )
    return bool(report["failures"])


if __name__ == "__main__":
    raise SystemExit(main())
