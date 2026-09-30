import pytest


def test_macos_download_uses_verified_system_transport_without_redirects(
    monkeypatch, tmp_path
):
    from Backend.Core.france.corpus import download_with_system_trust

    calls = []

    def run(arguments, **kwargs):
        from pathlib import Path

        calls.append(arguments)
        Path(arguments[arguments.index("--output") + 1]).write_bytes(
            b"%PDF-1.7\nfixture"
        )

    monkeypatch.setattr("subprocess.run", run)
    content = download_with_system_trust("https://eduscol.education.gouv.fr/source.pdf")
    assert content.startswith(b"%PDF-")
    assert calls[0][0] == "/usr/bin/curl"
    assert "--location" not in calls[0] and "--insecure" not in calls[0]
    assert "--max-filesize" in calls[0] and "--max-time" in calls[0]
    with pytest.raises(ValueError):
        download_with_system_trust("https://evil.test/source.pdf")
    assert len(calls) == 1


def test_discovery_keeps_only_official_nsi_documents():
    from tools.french_reference_corpus import discover_links

    html = """<a href="/sites/default/files/document/nsi.pdf">Numérique et sciences informatiques</a>
    <a href="https://example.org/nsi.pdf">NSI corrigé</a>
    <a href="/maths.pdf">Mathématiques</a>"""
    assert discover_links(html, "https://www.education.gouv.fr/exams") == [
        "https://www.education.gouv.fr/sites/default/files/document/nsi.pdf"
    ]


def test_download_rejects_external_hosts_and_html_before_indexing():
    from tools.french_reference_corpus import check_download

    with pytest.raises(ValueError, match="host"):
        check_download("https://evil.test/a.pdf", b"%PDF-1.7\n")
    with pytest.raises(ValueError, match="PDF"):
        check_download(
            "https://eduscol.education.gouv.fr/a.pdf", b"<html>blocked</html>"
        )


def test_holdout_split_is_order_independent_and_stratified():
    from tools.french_reference_corpus import assign_splits

    entries = [
        dict(id=f"{year}-{i}", session=year, category="official_paper")
        for year in (2025, 2026)
        for i in range(5)
    ]
    first = assign_splits(entries)
    assert first == assign_splits(list(reversed(entries)))
    assert sum(first[f"2025-{i}"] == "holdout" for i in range(5)) == 1
    assert sum(first[f"2026-{i}"] == "holdout" for i in range(5)) == 1


def test_archive_reconciliation_freezes_standard_papers_and_records_variants():
    from tools.french_reference_corpus import reconcile_archive_discovery

    rows = []
    for index in range(5):
        documents = [
            {"format": "standard", "file": f"26-nsij{index}-fixture.pdf"}
        ]
        if index == 0:
            documents.append({"format": "A16", "file": "26-nsij0-a16.pdf"})
        rows.append(
            {
                "year": 2026,
                "session": "normal",
                "centre": "Métropole et La Réunion",
                "description": f"Jour {index + 1}",
                "documents": documents,
            }
        )
    discovery = {
        "schema_version": 1,
        "source": "https://eduscol.education.gouv.fr/5199/annales",
        "document_url_prefix": "https://eduscol.education.gouv.fr/sites/default/files/document/",
        "index_rows": 5,
        "document_links": 6,
        "unique_urls": 6,
        "rows": rows,
    }

    register = reconcile_archive_discovery(discovery, [])

    assert register["archive_reconciliation"]["complete_index"] is True
    assert register["archive_reconciliation"]["standard_papers"] == 5
    assert register["archive_reconciliation"]["accessibility_variants"] == 1
    assert len(register["documents"]) == 5
    assert len({document["id"] for document in register["documents"]}) == 5
    assert all(document["template_eligible"] for document in register["documents"])
    assert sum(document["split"] == "holdout" for document in register["documents"]) == 1
    assert register["archive_variants"] == [
        {
            "canonical_document_id": register["documents"][0]["id"],
            "format": "A16",
            "url": "https://eduscol.education.gouv.fr/sites/default/files/document/26-nsij0-a16.pdf",
            "retrieval_eligible": False,
            "reason": "accessibility-representation-of-canonical-paper",
        }
    ]


def test_archive_reconciliation_rejects_incomplete_or_ambiguous_index():
    from tools.french_reference_corpus import reconcile_archive_discovery

    discovery = {
        "schema_version": 1,
        "source": "https://eduscol.education.gouv.fr/archive",
        "document_url_prefix": "https://eduscol.education.gouv.fr/documents/",
        "index_rows": 1,
        "document_links": 2,
        "unique_urls": 2,
        "rows": [
            {
                "year": 2022,
                "session": "normal",
                "centre": "Métropole",
                "description": "Jour 1",
                "documents": [
                    {"format": "standard", "file": "one.pdf"},
                    {"format": "standard", "file": "two.pdf"},
                ],
            }
        ],
    }

    with pytest.raises(ValueError, match="exactly one standard"):
        reconcile_archive_discovery(discovery, [])


def test_pin_reconciled_hashes_requires_every_document_and_records_duplicates():
    from tools.french_reference_corpus import pin_reconciled_hashes

    register = {
        "schema_version": 1,
        "status": "archive-index-reconciled-content-acquisition-pending",
        "archive_reconciliation": {
            "complete_index": True,
            "content_hashes_complete": False,
            "standard_papers": 2,
        },
        "documents": [
            {"id": "paper-a", "category": "official_paper"},
            {"id": "paper-b", "category": "official_paper"},
        ],
    }
    digest = "a" * 64
    manifest = {
        "complete_archive": True,
        "failures": [],
        "documents": [
            {"id": "paper-a", "sha256": digest},
            {"id": "paper-b", "sha256": digest},
        ],
        "duplicates": [{"sha256": digest, "ids": ["paper-a", "paper-b"]}],
    }

    pinned = pin_reconciled_hashes(register, manifest)

    assert pinned["status"] == "archive-content-reconciled"
    assert pinned["archive_reconciliation"]["content_hashes_complete"] is True
    assert pinned["archive_reconciliation"]["duplicate_content_groups"] == 1
    assert all(document["sha256"] == digest for document in pinned["documents"])

    with pytest.raises(ValueError, match="missing documents"):
        pin_reconciled_hashes(register, {**manifest, "documents": manifest["documents"][:1]})


def test_duplicate_policy_never_leaks_a_holdout_through_a_reference_alias():
    from tools.french_reference_corpus import duplicate_index_policy

    documents = [
        {"id": "reference-copy", "sha256": "a" * 64, "split": "reference"},
        {"id": "held-out-copy", "sha256": "a" * 64, "split": "holdout"},
        {"id": "z-copy", "sha256": "b" * 64, "split": "reference"},
        {"id": "a-copy", "sha256": "b" * 64, "split": "reference"},
    ]

    groups = duplicate_index_policy(documents)

    assert groups == [
        {
            "sha256": "a" * 64,
            "ids": ["held-out-copy", "reference-copy"],
            "canonical_id": "held-out-copy",
            "excluded_ids": ["reference-copy"],
            "crosses_holdout_boundary": True,
        },
        {
            "sha256": "b" * 64,
            "ids": ["a-copy", "z-copy"],
            "canonical_id": "a-copy",
            "excluded_ids": ["z-copy"],
            "crosses_holdout_boundary": False,
        },
    ]


def test_reconciliation_prunes_sources_no_longer_in_the_register(tmp_path):
    from Backend.Core.scoped_references import ReferenceIndex
    from tools.french_reference_corpus import prune_unregistered_sources

    with ReferenceIndex(tmp_path / "references.sqlite") as index:
        with index.connection:
            index.connection.executemany(
                "INSERT INTO sources VALUES (?,?,?,?,?,?)",
                [
                    ("current", "{}", "nsi-2019", "official_paper", "reference", "{}"),
                    ("legacy", "{}", "nsi-2019", "official_paper", "reference", "{}"),
                ],
            )
            index.connection.executemany(
                "INSERT INTO chunks(source_id,page,text) VALUES (?,?,?)",
                [("current", 1, "current"), ("legacy", 1, "legacy")],
            )
        assert prune_unregistered_sources(index, {"current"}) == ["legacy"]
        assert index.connection.execute("SELECT id FROM sources").fetchall() == [
            ("current",)
        ]
        assert index.connection.execute(
            "SELECT source_id FROM chunks"
        ).fetchall() == [("current",)]
