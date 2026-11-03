import pytest


@pytest.fixture
def owned_corpus(tmp_path):
    import json
    from hashlib import sha256

    import pymupdf

    output = tmp_path / "corpus"
    output.mkdir()
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_text((72, 72), "Owned fixture: jointure SQL et graphe.")
        content = pdf.tobytes()
    entry = {
        "id": "owned-source",
        "url": "https://eduscol.education.gouv.fr/owned-fixture.pdf",
        "sha256": sha256(content).hexdigest(),
        "category": "official_paper",
        "authority": "Owned test fixture, not an official paper",
        "session": 2026,
        "centre": "Fixture",
        "rights": "reference-only",
        "split": "reference",
    }
    register = tmp_path / "register.json"

    def write(entries):
        register.write_text(json.dumps({"schema_version": 1, "documents": entries}))
        for document in entries:
            (output / f"{document['id']}.pdf").write_bytes(content)

    return register, output, entry, write


@pytest.mark.parametrize(
    "changed",
    [
        {"split": "holdout"},
        {"rights": "not-reviewed"},
        {"sha256": "0" * 64},
        {"url": "https://example.org/not-approved.pdf"},
    ],
)
def test_failed_readmission_removes_previous_retrievable_source(owned_corpus, changed):
    from Backend.Core.education_context import NSI_CONTEXT
    from Backend.Core.france.corpus import ingest
    from Backend.Core.scoped_references import EvidenceGap, ReferenceIndex

    register, output, entry, write = owned_corpus
    write([entry])
    assert not ingest(register, output)["failures"]
    with ReferenceIndex(output / "references.sqlite") as index:
        assert (
            index.retrieve(
                NSI_CONTEXT, "nsi-2019", "jointure", categories=("official_paper",)
            )[0].source_id
            == entry["id"]
        )

    write([{**entry, **changed}])
    report = ingest(register, output)
    assert [failure["id"] for failure in report["failures"]] == [entry["id"]]
    assert report["stale_index_sources_removed"] == [entry["id"]]
    with ReferenceIndex(output / "references.sqlite") as index:
        assert index.connection.execute("SELECT id FROM sources").fetchall() == []
        assert index.connection.execute("SELECT id FROM chunks").fetchall() == []
        with pytest.raises(EvidenceGap):
            index.retrieve(
                NSI_CONTEXT, "nsi-2019", "jointure", categories=("official_paper",)
            )
    assert (output / f"{entry['id']}.pdf").exists()

    write([entry])
    assert not ingest(register, output)["failures"]


@pytest.mark.parametrize(
    "changed",
    [
        {},
        {"rights": "not-reviewed"},
        {"sha256": "0" * 64},
        {"url": "https://example.org/not-approved.pdf"},
    ],
)
@pytest.mark.parametrize("reverse_order", [False, True])
def test_failed_holdout_readmission_cannot_reenter_through_duplicate_alias(
    owned_corpus, changed, reverse_order
):
    from Backend.Core.education_context import NSI_CONTEXT
    from Backend.Core.france.corpus import ingest
    from Backend.Core.scoped_references import EvidenceGap, ReferenceIndex

    register, output, entry, write = owned_corpus
    alias = {**entry, "id": "zzz-alias"}
    documents = [entry, alias]
    write(list(reversed(documents)) if reverse_order else documents)
    assert not ingest(register, output)["failures"]
    documents = [{**entry, "split": "holdout", **changed}, alias]
    write(list(reversed(documents)) if reverse_order else documents)
    report = ingest(register, output)
    assert [failure["id"] for failure in report["failures"]] == [entry["id"]]
    assert report["holdout_quarantined_reference_ids"] == [alias["id"]]
    assert report["unresolved_holdout_ids"] == []
    assert report["documents"][0]["indexed"] is False
    with (
        ReferenceIndex(output / "references.sqlite") as index,
        pytest.raises(EvidenceGap),
    ):
        index.retrieve(
            NSI_CONTEXT, "nsi-2019", "jointure", categories=("official_paper",)
        )

    write([{**entry, "split": "holdout"}, {**entry, "id": "zzz-alias"}])
    recovered = ingest(register, output)
    assert recovered["failures"] == []
    assert recovered["unresolved_holdout_ids"] == []
    assert recovered["holdout_quarantined_reference_ids"] == ["zzz-alias"]


@pytest.mark.parametrize("reverse_order", [False, True])
def test_unresolved_holdout_identity_blocks_reference_retrieval(
    owned_corpus, reverse_order
):
    from Backend.Core.education_context import NSI_CONTEXT
    from Backend.Core.france.corpus import ingest
    from Backend.Core.scoped_references import EvidenceGap, ReferenceIndex

    register, output, entry, write = owned_corpus
    holdout = {**entry, "split": "holdout", "url": "https://example.org/rejected.pdf"}
    holdout.pop("sha256")
    documents = [holdout, {**entry, "id": "zzz-alias"}]
    write(list(reversed(documents)) if reverse_order else documents)
    report = ingest(register, output)
    assert report["failures"]
    assert report["unresolved_holdout_ids"] == [entry["id"]]
    assert report["documents"][0]["indexed"] is False
    with (
        ReferenceIndex(output / "references.sqlite") as index,
        pytest.raises(EvidenceGap),
    ):
        index.retrieve(
            NSI_CONTEXT, "nsi-2019", "jointure", categories=("official_paper",)
        )

    write([{**entry, "split": "holdout"}, {**entry, "id": "zzz-alias"}])
    recovered = ingest(register, output)
    assert recovered["failures"] == []
    assert recovered["unresolved_holdout_ids"] == []
    assert recovered["holdout_quarantined_reference_ids"] == ["zzz-alias"]


def test_known_holdout_quarantine_preserves_unrelated_valid_sources(owned_corpus):
    from hashlib import sha256

    import pymupdf

    from Backend.Core.education_context import NSI_CONTEXT
    from Backend.Core.france.corpus import ingest
    from Backend.Core.scoped_references import ReferenceIndex

    register, output, entry, write = owned_corpus
    write([entry])
    assert not ingest(register, output)["failures"]
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text(
            (72, 72), "Independent owned fixture about recursion."
        )
        unrelated = pdf.tobytes()
    other = {**entry, "id": "unrelated-source", "sha256": sha256(unrelated).hexdigest()}
    write([{**entry, "split": "holdout"}, other])
    (output / "unrelated-source.pdf").write_bytes(unrelated)
    report = ingest(register, output)
    assert [failure["id"] for failure in report["failures"]] == [entry["id"]]
    with ReferenceIndex(output / "references.sqlite") as index:
        hits = index.retrieve(
            NSI_CONTEXT, "nsi-2019", "recursion", categories=("official_paper",)
        )
    assert [hit.source_id for hit in hits] == [other["id"]]
    assert report["unresolved_holdout_ids"] == []
    assert report["documents"][0]["indexed"] is True


def test_conflicting_duplicate_id_cannot_keep_an_earlier_success_eligible(owned_corpus):
    from Backend.Core.education_context import NSI_CONTEXT
    from Backend.Core.france.corpus import ingest
    from Backend.Core.scoped_references import EvidenceGap, ReferenceIndex

    register, output, entry, write = owned_corpus
    write([entry])
    assert not ingest(register, output)["failures"]
    write([entry, {**entry, "rights": "not-reviewed"}])
    report = ingest(register, output)
    assert [failure["id"] for failure in report["failures"]] == [entry["id"]]
    assert report["documents"][0]["indexed"] is False
    with (
        ReferenceIndex(output / "references.sqlite") as index,
        pytest.raises(EvidenceGap),
    ):
        index.retrieve(
            NSI_CONTEXT, "nsi-2019", "jointure", categories=("official_paper",)
        )


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
        documents = [{"format": "standard", "file": f"26-nsij{index}-fixture.pdf"}]
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
    assert (
        sum(document["split"] == "holdout" for document in register["documents"]) == 1
    )
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
        pin_reconciled_hashes(
            register, {**manifest, "documents": manifest["documents"][:1]}
        )


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
        assert index.connection.execute("SELECT source_id FROM chunks").fetchall() == [
            ("current",)
        ]
