"""Curriculum scoping limits context, never supplies questions or answers."""

from copy import deepcopy

import pytest

from Backend.Core.france import llm_pipeline as subject
from tests.test_french_llm_pipeline import Client
from tests.test_nsi_pipeline import make_index


def test_seeded_domains_are_distinct_deterministic_and_all_remain_available():
    plans = [subject.curriculum_plan(seed) for seed in range(30)]
    assert plans == [subject.curriculum_plan(seed) for seed in range(30)]
    assert all(len(plan) == len(set(plan)) == 3 for plan in plans)
    assert set().union(*map(set, plans)) == subject.TOPICS
    for invalid in (True, "42", None):
        with pytest.raises(ValueError):
            subject.curriculum_plan(invalid)


def test_scoped_package_binds_plan_sources_and_all_nine_model_calls(tmp_path):
    path = tmp_path / "references.sqlite"
    make_index(path)
    client = Client()
    package = subject.generate(index_path=path, client=client, seed=42)
    assert len(client.requests) == 9
    assert package["identity"]["source_policy"] == subject.SOURCE_POLICY
    assert [
        row["primary_topic"] for row in package["curriculum_plan"]
    ] == subject.curriculum_plan(42)
    for i, row in enumerate(package["curriculum_plan"]):
        assert row["exercise_id"] == str(i + 1)
        assert 2 <= len(row["references"]) <= 4
        assert {r["category"] for r in row["references"]} == {
            "programme",
            "official_paper",
        }
        for request in client.requests[i * 3 : i * 3 + 3]:
            assert all(r["text"] in request.prompt for r in row["references"])
        exercise = package["exercises"][i]
        assert row["primary_topic"] in exercise["topics"]
        assert any(
            subject.CURRICULUM_OBJECTIVES[code][0] == row["primary_topic"]
            for q in exercise["questions"]
            for code in q["curriculum_codes"]
        )
    assert subject.validate_package(package)
    for mutate in (
        lambda p: p["identity"].pop("source_policy"),
        lambda p: p["curriculum_plan"][0].update(primary_topic="algorithmique"),
        lambda p: p["curriculum_plan"][0]["references"].clear(),
        lambda p: p["references"].clear(),
    ):
        changed = deepcopy(package)
        mutate(changed)
        changed["identity"]["content_sha256"] = subject._digest(
            {k: v for k, v in changed.items() if k != "identity"}
        )
        with pytest.raises(ValueError):
            subject.validate_package(changed)


def test_primary_domain_cannot_be_declared_without_assessed_curriculum(tmp_path):
    path = tmp_path / "references.sqlite"
    make_index(path)
    client = Client(mutate=lambda raw: raw.update(topics=["algorithmique"]))
    with pytest.raises(ValueError, match="domaine principal"):
        subject.generate(index_path=path, client=client, seed=42)


def test_each_scoped_query_retains_strict_filters_and_two_hits_per_category(
    monkeypatch, tmp_path
):
    from dataclasses import asdict

    from Backend.Core.education_context import NSI_2027, NSI_CONTEXT
    from Backend.Core.scoped_references import ReferenceHit

    calls = []

    class Index:
        def __init__(self, path, *, read_only):
            assert read_only is True

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def retrieve(self, context, curriculum, query, *, categories, limit):
            assert context == NSI_CONTEXT and curriculum == NSI_2027.curriculum_version
            assert limit == 2 and len(categories) == 1
            calls.append((categories[0], query))
            return [
                ReferenceHit(
                    categories[0],
                    "a" * 64,
                    page,
                    "Référence du domaine",
                    "https://eduscol.education.gouv.fr/test",
                    categories[0],
                )
                for page in (1, 2)
            ]

    monkeypatch.setattr(subject, "ReferenceIndex", Index)
    for topic in sorted(subject.TOPICS):
        refs = subject._retrieve_references(
            tmp_path / "refs.sqlite", primary_topic=topic
        )
        assert len(refs) == 4
        assert refs == [
            asdict(
                ReferenceHit(
                    category,
                    "a" * 64,
                    page,
                    "Référence du domaine",
                    "https://eduscol.education.gouv.fr/test",
                    category,
                )
            )
            for category in ("programme", "official_paper")
            for page in (1, 2)
        ]
        assert all(topic.replace("-", " ") in query for _, query in calls[-2:])
        assert [category for category, _ in calls[-2:]] == [
            "programme",
            "official_paper",
        ]
    with pytest.raises(ValueError):
        subject._retrieve_references(
            tmp_path / "refs.sqlite", primary_topic="uk-fallback"
        )


def test_scoped_retrieval_excludes_foreign_holdout_and_obsolete_sources(tmp_path):
    from dataclasses import replace
    from hashlib import sha256

    from Backend.Core.education_context import NSI_CONTEXT
    from Backend.Core.scoped_references import ReferenceIndex, SourceDocument

    path = tmp_path / "refs.sqlite"
    make_index(path)
    text = " ".join(text for _, text in subject.CURRICULUM_OBJECTIVES.values())
    with ReferenceIndex(path) as index:
        for identifier, context, split, curriculum in (
            ("foreign", replace(NSI_CONTEXT, country="GB"), "reference", "nsi-2019"),
            ("holdout", NSI_CONTEXT, "holdout", "nsi-2019"),
            ("old", NSI_CONTEXT, "reference", "old"),
        ):
            index.add(
                SourceDocument(
                    identifier,
                    context,
                    curriculum,
                    "programme",
                    "MEN",
                    "https://eduscol.education.gouv.fr/test",
                    "2026-09-28T12:00:00+00:00",
                    sha256(text.encode()).hexdigest(),
                    2026,
                    "national",
                    "reference-only",
                    split,
                ),
                text,
                [(1, text)],
            )
    before = sha256(path.read_bytes()).hexdigest()
    for topic in subject.TOPICS:
        refs = subject._retrieve_references(path, primary_topic=topic)
        assert {r["source_id"] for r in refs} == {"programme", "official_paper"}
    assert sha256(path.read_bytes()).hexdigest() == before
