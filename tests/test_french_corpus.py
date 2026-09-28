import pytest


def test_discovery_keeps_only_official_nsi_documents():
    from tools.french_reference_corpus import discover_links

    html = '''<a href="/sites/default/files/document/nsi.pdf">Numérique et sciences informatiques</a>
    <a href="https://example.org/nsi.pdf">NSI corrigé</a>
    <a href="/maths.pdf">Mathématiques</a>'''
    assert discover_links(html, "https://www.education.gouv.fr/exams") == [
        "https://www.education.gouv.fr/sites/default/files/document/nsi.pdf"
    ]


def test_download_rejects_external_hosts_and_html_before_indexing():
    from tools.french_reference_corpus import check_download

    with pytest.raises(ValueError, match="host"):
        check_download("https://evil.test/a.pdf", b"%PDF-1.7\n")
    with pytest.raises(ValueError, match="PDF"):
        check_download("https://eduscol.education.gouv.fr/a.pdf", b"<html>blocked</html>")


def test_holdout_split_is_order_independent_and_stratified():
    from tools.french_reference_corpus import assign_splits

    entries = [dict(id=f"{year}-{i}", session=year, category="official_paper") for year in (2025, 2026) for i in range(5)]
    first = assign_splits(entries)
    assert first == assign_splits(list(reversed(entries)))
    assert sum(first[f"2025-{i}"] == "holdout" for i in range(5)) == 1
    assert sum(first[f"2026-{i}"] == "holdout" for i in range(5)) == 1
