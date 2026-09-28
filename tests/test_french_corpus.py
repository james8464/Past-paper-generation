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
