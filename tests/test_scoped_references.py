from dataclasses import replace
from hashlib import sha256

import pytest


def source(identifier="fr", **changes):
    from Backend.Core.education_context import NSI_CONTEXT
    from Backend.Core.scoped_references import SourceDocument

    text = "Arbres binaires et parcours : connaissances du programme."
    values = dict(
        id=identifier, context=NSI_CONTEXT, curriculum_version="nsi-2019",
        category="programme", authority="MEN", url="https://eduscol.education.gouv.fr/example",
        retrieved_at="2026-09-28T12:00:00+00:00", sha256=sha256(text.encode()).hexdigest(),
        session=2026, centre="national", rights="reference-only", split="reference",
    )
    values.update(changes)
    return SourceDocument(**values), text


def test_retrieval_filters_before_ranking_and_never_falls_back(tmp_path):
    from Backend.Core.education_context import NSI_CONTEXT
    from Backend.Core.scoped_references import EvidenceGap, ReferenceIndex

    with ReferenceIndex(tmp_path / "references.sqlite") as index:
        document, text = source()
        index.add(document, text, [(1, text)])
        uk, text = source("uk", context=replace(NSI_CONTEXT, education_system="uk", country="GB"))
        index.add(uk, text, [(1, text)])
        holdout, text = source("holdout", split="holdout")
        index.add(holdout, text, [(1, text)])
        old, text = source("old", curriculum_version="obsolete")
        index.add(old, text, [(1, text)])
        hits = index.retrieve(NSI_CONTEXT, "nsi-2019", "arbres parcours", categories=("programme",))
        assert [hit.source_id for hit in hits] == ["fr"]
        assert hits[0].page == 1
        with pytest.raises(EvidenceGap):
            index.retrieve(NSI_CONTEXT, "nsi-2019", "physique", categories=("programme",))
        with pytest.raises(ValueError):
            index.retrieve(NSI_CONTEXT, "nsi-2019", "arbres", categories=())


def test_source_hash_and_rights_gate_ingestion(tmp_path):
    from Backend.Core.scoped_references import ReferenceIndex

    with ReferenceIndex(tmp_path / "references.sqlite") as index:
        document, text = source()
        with pytest.raises(ValueError, match="hash"):
            index.add(document, "altered", [(1, text)])
        with pytest.raises(ValueError, match="rights"):
            source(rights="unknown")


def test_identity_cannot_be_silently_overwritten(tmp_path):
    from Backend.Core.scoped_references import ReferenceIndex

    with ReferenceIndex(tmp_path / "references.sqlite") as index:
        document, text = source()
        index.add(document, text, [(1, text)])
        index.add(document, text, [(1, text)])
        with pytest.raises(ValueError, match="identity"):
            index.add(replace(document, split="holdout"), text, [(1, text)])


def test_query_punctuation_is_data_not_fts_syntax(tmp_path):
    from Backend.Core.education_context import NSI_CONTEXT
    from Backend.Core.scoped_references import ReferenceIndex

    with ReferenceIndex(tmp_path / "references.sqlite") as index:
        document, text = source()
        index.add(document, text, [(1, text)])
        assert index.retrieve(NSI_CONTEXT, "nsi-2019", 'arbres" OR * --', categories=("programme",))[0].source_id == "fr"
