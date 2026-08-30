from __future__ import annotations

from types import SimpleNamespace

from Backend.Core.exam_blueprints import GeneratedQuestion
from Backend.Core.mark_scheme_enrichment import _enrich_question


def question(
    *,
    kind: str,
    command_word: str,
    marks: int,
    mark_scheme: list[str] | None = None,
    authoring_context: dict[str, object] | None = None,
) -> GeneratedQuestion:
    return GeneratedQuestion(
        rule_id="test",
        number="1",
        marks=marks,
        kind=kind,
        command_word=command_word,
        topic_id="topic",
        prompt=f"{command_word} the required response.",
        mark_scheme=mark_scheme or ["Credit an accurate, fully worked answer."],
        authoring_context=authoring_context or {},
    )


def topic() -> SimpleNamespace:
    return SimpleNamespace(
        title="Limited company accounts",
        points=["published statements", "reserves", "share capital"],
    )


def test_high_mark_calculation_keeps_points_based_marking() -> None:
    enriched = _enrich_question(
        question(kind="calculation", command_word="Prepare", marks=14),
        topic(),
        "accounting",
    )

    assert not any(
        point.casefold().startswith(("level ", "levels-based"))
        for point in enriched.mark_scheme
    )


def test_high_mark_evaluation_receives_levels_guidance() -> None:
    enriched = _enrich_question(
        question(kind="extended_response", command_word="Advise", marks=25),
        topic(),
        "accounting",
    )

    assert "Levels-based marking" in enriched.mark_scheme
    assert any(point.startswith("Level 5") for point in enriched.mark_scheme)


def test_high_mark_analysis_receives_levels_guidance() -> None:
    enriched = _enrich_question(
        question(kind="analysis", command_word="Analyse", marks=12),
        topic(),
        "business",
    )

    assert "Levels-based marking" in enriched.mark_scheme


def test_enriched_guidance_does_not_quote_a_replaceable_draft_stem() -> None:
    draft = question(kind="extended_response", command_word="Discuss", marks=25)

    enriched = _enrich_question(draft, topic(), "economics")

    assert draft.prompt not in " ".join(enriched.mark_scheme)
    assert any(
        "precise proposition in the final question" in point
        for point in enriched.mark_scheme
    )


def test_enriched_written_item_locks_guidance_and_calibrates_stem_length() -> None:
    draft = question(kind="extended_response", command_word="Discuss", marks=25)

    enriched = _enrich_question(draft, topic(), "economics")

    assert enriched.authoring_context["preserve_mark_scheme"] is True
    assert enriched.authoring_context["max_prompt_words"] == max(
        12, len(draft.prompt.split()) + 2
    )


def test_enrichment_keeps_explicit_observable_mark_points() -> None:
    expected = ["Exact answer: £12,345.", "Exact working: £15,000 − £2,655."]
    draft = question(
        kind="calculation",
        command_word="Calculate",
        marks=2,
        mark_scheme=expected,
        authoring_context={"observable_mark_points": expected},
    )

    enriched = _enrich_question(draft, topic(), "accounting")

    assert enriched.authoring_context["observable_mark_points"] == expected


def test_enrichment_derives_observable_points_before_structured_hydration() -> None:
    expected = ["Answer: 42.", "Working: 6 × 7."]
    draft = question(
        kind="calculation",
        command_word="Calculate",
        marks=2,
        mark_scheme=expected,
    )

    enriched = _enrich_question(draft, topic(), "accounting")

    assert enriched.authoring_context["observable_mark_points"] == expected
