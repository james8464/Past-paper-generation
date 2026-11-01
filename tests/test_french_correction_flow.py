"""Generic current-V36 corrections keep small questions with their credits."""

from copy import deepcopy

import pymupdf
import pytest

from Backend.Core.france import rendering
from Backend.Core.france.llm_pdf import validate_llm_pdf
from Backend.Core.france.llm_pipeline import PRINT_POLICY
from Backend.Core.france.print_policy import (
    V35_PRINT_POLICY,
    V36_LEGACY_PRINT_POLICY,
    V36_READABLE_PRINT_POLICY,
)
from Backend.Core.render_transaction import render_pdf_atomically
from tests.test_french_llm_pdf import exercises


def source_with_small_questions(context_lines=0):
    source = exercises()
    first = source[0]
    questions = []
    for index, question in enumerate(first.questions, 1):
        questions.append(
            question.model_copy(
                update={
                    "prompt": f"QUESTION_{index} : justifier le résultat de cette étape.",
                    "answer": f"RESULTAT_{index} : le résultat satisfait la propriété demandée.",
                    "marking": (
                        question.marking[0].model_copy(
                            update={
                                "criterion": f"CREDIT_{index} : justification correcte."
                            }
                        ),
                    ),
                    "material_ids": (),
                    "verification": {"kind": "human"},
                }
            )
        )
    source[0] = first.model_copy(
        update={
            "context": "CONTEXTE : les étapes sont indépendantes.\n"
            + "\n".join(
                f"Situation {index} : les quantités sont entières."
                for index in range(context_lines)
            ),
            "materials": (),
            "questions": tuple(questions),
        }
    )
    return source


def render(path, source, *, policy=PRINT_POLICY, large_print=False, correction=True):
    render_pdf_atomically(
        path,
        lambda destination: rendering.render_assessment(
            destination,
            source,
            correction=correction,
            large_print=large_print,
            human_readable_graph_titles=True,
            coherent_material_flow=True,
            print_policy=policy,
        ),
        role="mark_scheme" if correction else "question_paper",
        language="fr-FR",
    )


def page_of(pdf, marker):
    pages = [index for index, page in enumerate(pdf) if marker in page.get_text()]
    assert len(pages) == 1
    return pages[0]


@pytest.mark.parametrize("context_lines", [0, 8, 16, 24])
@pytest.mark.parametrize("large_print", [False, True])
def test_small_question_answer_and_credits_share_a_page(
    tmp_path, context_lines, large_print
):
    source = source_with_small_questions(context_lines)
    original = deepcopy([item.model_dump(mode="json") for item in source])
    path = tmp_path / "cohesive.pdf"
    render(path, source, large_print=large_print)
    validate_llm_pdf(path, source, correction=True, large_print=large_print)
    with pymupdf.open(path) as pdf:
        for index in range(1, 7):
            assert (
                page_of(pdf, f"QUESTION_{index}")
                == page_of(pdf, f"RESULTAT_{index}")
                == page_of(pdf, f"CREDIT_{index}")
            )
    assert [item.model_dump(mode="json") for item in source] == original


@pytest.mark.parametrize("large_print", [False, True])
def test_short_code_first_prompts_do_not_create_nested_group_sentinel_heights(
    tmp_path, large_print
):
    source = source_with_small_questions(8)
    first = source[0]
    source[0] = first.model_copy(
        update={
            "questions": tuple(
                question.model_copy(
                    update={
                        "prompt": "```python\nif True:\n    valeur = 1\n```\n"
                        + question.prompt
                    }
                )
                for question in first.questions
            )
        }
    )
    path = tmp_path / "code-first.pdf"
    render(path, source, large_print=large_print)
    validate_llm_pdf(path, source, correction=True, large_print=large_print)
    with pymupdf.open(path) as pdf:
        for index in range(1, 7):
            assert (
                page_of(pdf, f"QUESTION_{index}")
                == page_of(pdf, f"RESULTAT_{index}")
                == page_of(pdf, f"CREDIT_{index}")
            )


@pytest.mark.parametrize("large_print", [False, True])
@pytest.mark.parametrize("code_first", [False, True])
def test_oversized_question_splits_code_without_empty_pages_or_forced_fresh_start(
    tmp_path, large_print, code_first
):
    source = source_with_small_questions()
    first = source[0]
    question = first.questions[0]
    short_code = "```python\nif True:\n    valeur = 1\n```\n"
    code = "if True:\n" + "\n".join(
        f"    valeur_{index:03} = {index}" for index in range(120)
    )
    question = question.model_copy(
        update={
            "prompt": (short_code if code_first else "") + question.prompt,
            "answer": "RESULTAT_1 : programme complet.\n```python\n" + code + "\n```",
        }
    )
    source[0] = first.model_copy(update={"questions": (question, *first.questions[1:])})
    original = deepcopy([item.model_dump(mode="json") for item in source])
    path = tmp_path / "oversized.pdf"
    render(path, source, large_print=large_print)
    validate_llm_pdf(path, source, correction=True, large_print=large_print)
    with pymupdf.open(path) as pdf:
        assert page_of(pdf, "QUESTION_1") == page_of(pdf, "CONTEXTE")
        assert page_of(pdf, "CREDIT_1") > page_of(pdf, "RESULTAT_1")
        assert page_of(pdf, "valeur_119") >= page_of(pdf, "valeur_000") + 2
    assert [item.model_dump(mode="json") for item in source] == original


@pytest.mark.parametrize(
    "policy",
    [None, V35_PRINT_POLICY, V36_LEGACY_PRINT_POLICY, V36_READABLE_PRINT_POLICY],
)
def test_historical_correction_does_not_use_new_grouping(tmp_path, monkeypatch, policy):
    def forbidden(*args, **kwargs):
        raise AssertionError("Historical correction flow must remain unchanged")

    monkeypatch.setattr(rendering, "_QuestionGroup", forbidden, raising=False)
    render(tmp_path / "historical.pdf", source_with_small_questions(), policy=policy)


def test_current_subject_does_not_use_correction_grouping(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("The subject must not use correction grouping")

    monkeypatch.setattr(rendering, "_QuestionGroup", forbidden, raising=False)
    source = source_with_small_questions()
    path = tmp_path / "subject.pdf"
    render(path, source, correction=False)
    validate_llm_pdf(path, source, correction=False)


def test_current_correction_does_not_leave_a_spacer_before_exercise_page_break(
    tmp_path, monkeypatch
):
    original = rendering.SimpleDocTemplate.build

    def checked_build(document, story, *args, **kwargs):
        for index, item in enumerate(story):
            # The first Spacer/PageBreak pair owns the cover, not a question.
            if index > 1 and isinstance(item, rendering.PageBreak):
                assert not isinstance(story[index - 1], rendering.Spacer)
        return original(document, story, *args, **kwargs)

    monkeypatch.setattr(rendering.SimpleDocTemplate, "build", checked_build)
    source = source_with_small_questions()
    path = tmp_path / "boundaries.pdf"
    render(path, source)
    validate_llm_pdf(path, source, correction=True)
