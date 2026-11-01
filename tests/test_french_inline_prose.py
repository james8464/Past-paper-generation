"""Current V36 inline prose is allowlisted; raw data and fenced code stay exact."""

from copy import deepcopy

import pymupdf
import pytest

from Backend.Core.france.code_fences import fenced_parts
from Backend.Core.france.inline_prose import inline_markup, inline_text, printed_prose
from Backend.Core.france.llm_pdf import validate_llm_pdf
from Backend.Core.france.llm_pipeline import (
    PythonCodeFormatError,
    validate_authored_exercise,
)
from Backend.Core.france.print_policy import (
    V35_PRINT_POLICY,
    V36_LEGACY_PRINT_POLICY,
    V36_READABLE_PRINT_POLICY,
)
from Backend.Core.france.rendering import french_prose_markup, render_assessment
from tests.test_french_llm_pdf import exercises, render


@pytest.mark.parametrize(
    ("source", "visible", "markup"),
    [
        (
            "Clé <u>identifiant</u>, `x < y`.",
            "Clé identifiant, x < y.",
            "Clé <u>identifiant</u>, x &lt; y.",
        ),
        (
            "`<u>code</u> &amp;`",
            "<u>code</u> &amp;",
            "&lt;u&gt;code&lt;/u&gt; &amp;amp;",
        ),
        (
            "<b>gras</b> &amp; &#60;",
            "<b>gras</b> &amp; &#60;",
            "&lt;b&gt;gras&lt;/b&gt; &amp;amp; &amp;#60;",
        ),
        (
            '<u color="red">x</u>',
            '<u color="red">x</u>',
            '&lt;u color="red"&gt;x&lt;/u&gt;',
        ),
        (
            '<img src="file:///secret"/>',
            '<img src="file:///secret"/>',
            '&lt;img src="file:///secret"/&gt;',
        ),
        (
            '<font name="remote" color="red">x</font>',
            '<font name="remote" color="red">x</font>',
            '&lt;font name="remote" color="red"&gt;x&lt;/font&gt;',
        ),
        (
            "&lt;u&gt;entite&lt;/u&gt;",
            "&lt;u&gt;entite&lt;/u&gt;",
            "&amp;lt;u&amp;gt;entite&amp;lt;/u&amp;gt;",
        ),
        ("<u>x `y</u> z`", "<u>x `y</u> z`", "&lt;u&gt;x `y&lt;/u&gt; z`"),
        (
            "<u>x <u>y</u></u>",
            "<u>x <u>y</u></u>",
            "&lt;u&gt;x &lt;u&gt;y&lt;/u&gt;&lt;/u&gt;",
        ),
        ("<u>x\ny</u>", "<u>x\ny</u>", "&lt;u&gt;x<br/>y&lt;/u&gt;"),
        ("`x\ny`", "`x\ny`", "`x<br/>y`"),
        ("``x`` et ```python", "``x`` et ```python", "``x`` et ```python"),
        ("<u>vide", "<u>vide", "&lt;u&gt;vide"),
        ("fin</u>", "fin</u>", "fin&lt;/u&gt;"),
        ("`non fermé", "`non fermé", "`non fermé"),
        ("x < y et <u>z</u>", "x < y et z", "x &lt; y et <u>z</u>"),
        (
            '<a title="`x` <u>z</u>">lien</a>',
            '<a title="`x` <u>z</u>">lien</a>',
            '&lt;a title="`x` &lt;u&gt;z&lt;/u&gt;"&gt;lien&lt;/a&gt;',
        ),
    ],
)
def test_narrow_inline_grammar_has_matching_visible_text(source, visible, markup):
    assert inline_text(source) == visible
    assert inline_markup(source) == markup


def test_fences_are_opaque_to_visible_prose_normalisation():
    source = "Clé <u>id</u> et `appel`.\n```python\ns = '<u>raw</u> `raw`'\n```\nFin."
    assert printed_prose(source) == "Clé id et appel.\ns = '<u>raw</u> `raw`'\nFin."


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_unknown_and_empty_fences_keep_contents_opaque(newline):
    source = (
        "<u>avant</u>\n```text\n<u>brut</u> `brut`\n```\n```python\n```\n`apres`"
    ).replace("\n", newline)
    assert printed_prose(source) == (
        "avant\n<u>brut</u> `brut`\napres".replace("\n", newline)
    )


@pytest.mark.parametrize("language", ["text", "python", "sql", ""])
def test_direct_inline_entrypoints_preserve_fences_including_delimiters(language):
    fence = f"```{language}\nvaleur = '<u>brut</u> `brut`'\n```"
    source = "Avant `prose`.\n" + fence + "\nAprès <u>texte</u>."
    assert inline_text(source) == "Avant prose.\n" + fence + "\nAprès texte."
    assert inline_markup(source) == (
        "Avant prose.<br/>"
        + fence.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
        + "<br/>Après <u>texte</u>."
    )


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
@pytest.mark.parametrize("closed", [False, True])
@pytest.mark.parametrize("language", ["text", "python", "sql", ""])
def test_opt_in_fence_spans_retain_all_source_bytes(newline, closed, language):
    fence = f"  ```{language}\n<u>brut</u> `brut`\n"
    if closed:
        fence += "  ```  \n"
    source = ("Avant `prose`.\n" + fence).replace("\n", newline)
    parts = fenced_parts(source, require_closed=False, include_delimiters=True)
    assert "".join(part.text for part in parts) == source
    assert parts[1].closed is closed
    assert inline_text(source) == ("Avant prose.\n" + fence).replace("\n", newline)


@pytest.mark.parametrize("language", ["text", "python", "sql", ""])
@pytest.mark.parametrize("field", ["criterion", "scope"])
@pytest.mark.parametrize("large_print", [False, True])
def test_direct_pdf_prose_fields_leave_fenced_contents_literal(
    tmp_path, language, field, large_print
):
    source = exercises()
    fence = f"```{language}\nvaleur = '<u>brut</u> `brut`'\n```"
    value = "Prose `avant`.\n" + fence + "\n<u>apres</u>."
    if field == "criterion":
        question = source[0].questions[0]
        question = question.model_copy(
            update={
                "marking": (
                    question.marking[0].model_copy(update={"criterion": value}),
                    *question.marking[1:],
                )
            }
        )
        source[0] = source[0].model_copy(
            update={"questions": (question, *source[0].questions[1:])}
        )
        # Short expression/listing criteria are permitted, unlike bare suites.
        validate_authored_exercise(source[0].model_dump(mode="json"), "1")
    else:
        source[0] = source[0].model_copy(update={"title": value})
        # The renderer stays fail-safe even for a direct diagnostic model; this
        # does not relax the stricter authoring boundary on titles/documents.
        with pytest.raises(PythonCodeFormatError):
            validate_authored_exercise(source[0].model_dump(mode="json"), "1")
    before = deepcopy([item.model_dump(mode="json") for item in source])
    path = tmp_path / "direct-prose.pdf"
    render(path, source, correction=True, large_print=large_print)
    validate_llm_pdf(path, source, correction=True, large_print=large_print)
    assert [item.model_dump(mode="json") for item in source] == before
    with pymupdf.open(path) as pdf:
        visible = "".join("".join(page.get_text().split()) for page in pdf)
        assert "<u>brut</u>`brut`" in visible
        assert f"```{language}" in visible
        assert "Proseavant." in visible


def marked_exercises():
    source = exercises(graphs=True)
    question = source[0].questions[0]
    code = "texte = '<u>raw</u> `raw`'\nif True:\n    valeur = 1"
    source[0] = source[0].model_copy(
        update={
            "title": "Étude de `titre_inline`",
            "context": "La clé <u>cle_primaire</u> est soulignée. `code_inline` <b>reste</b> &amp;.\n"
            '<img src="file:///never-read"/>\n```python\n'
            + code
            + "\n```\n```text\n<u>fence_literal</u> `fence_literal`\n```",
            "questions": (
                question.model_copy(
                    update={
                        "prompt": "Expliquer `question_inline` et <u>propriete</u>.",
                        "answer": "La réponse est `reponse_inline` et <u>solution</u>.",
                        "marking": (
                            question.marking[0].model_copy(
                                update={
                                    "criterion": "Justifie `critere_inline` et <u>credit</u>."
                                }
                            ),
                            *question.marking[1:],
                        ),
                    }
                ),
                *source[0].questions[1:],
            ),
            "materials": (
                source[0]
                .materials[0]
                .model_copy(
                    update={
                        "rows": (
                            ("<u>donnee</u> `cellule`", "7"),
                            *source[0].materials[0].rows[1:],
                        )
                    }
                ),
                *source[0].materials[1:],
            ),
        }
    )
    graph = source[0].materials[-1]
    graph = graph.model_copy(
        update={
            "title": "<u>titre_document</u> `litteral`",
            "nodes": ("`A`", "B", "C"),
            "edges": (("`A`", "B", 2), ("B", "C", 3)),
        }
    )
    source[0] = source[0].model_copy(
        update={"materials": (*source[0].materials[:-1], graph)}
    )
    return source


@pytest.mark.parametrize("large_print", [False, True])
@pytest.mark.parametrize("correction", [False, True])
def test_real_pdf_underlines_only_prose_without_changing_raw_or_fenced_source(
    tmp_path, large_print, correction
):
    source = marked_exercises()
    original = deepcopy([exercise.model_dump(mode="json") for exercise in source])
    path = tmp_path / "inline.pdf"
    render(path, source, large_print=large_print, correction=correction)
    validate_llm_pdf(path, source, large_print=large_print, correction=correction)
    assert [exercise.model_dump(mode="json") for exercise in source] == original
    with pymupdf.open(path) as pdf:
        text = "\n".join(page.get_text() for page in pdf)
        assert "<u>cle_primaire</u>" not in text and "`code_inline`" not in text
        assert "`titre_inline`" not in text and "`question_inline`" not in text
        assert "<b>reste</b>&amp;." in "".join(text.split())
        assert '<imgsrc="file:///never-read"/>' in "".join(text.split())
        assert "<u>raw</u> `raw`" in text
        assert "<u>fence_literal</u> `fence_literal`" in text
        assert "<u>donnee</u> `cellule`" in text
        assert "<u>titre_document</u> `litteral`" in text and "`A`" in text
        assert all(
            not span["flags"] & 8
            for page in pdf
            for block in page.get_text("dict")["blocks"]
            for line in block.get("lines", [])
            for span in line["spans"]
            if "code_inline" in span["text"]
        ), "Inline code must not enter the monospace fenced-code audit channel"
        if correction:
            assert "`reponse_inline`" not in text and "`critere_inline`" not in text
        underlines = []
        for page in pdf:
            for bounds in page.search_for("cle_primaire"):
                for drawing in page.get_drawings():
                    for item in drawing["items"]:
                        if item[0] == "l":
                            start, end = item[1:]
                            if (
                                abs(start.y - end.y) < 0.1
                                and abs(start.x - bounds.x0) < 2
                                and abs(end.x - bounds.x1) < 2
                                and bounds.y0 < start.y < bounds.y1 + 2
                            ):
                                underlines.append(item)
        assert underlines, (
            "The primary-key word must actually be underlined, not merely stripped"
        )


@pytest.mark.parametrize("mutation", ["missing", "extra", "indentation"])
def test_complete_stream_and_fenced_indentation_checks_still_refuse(tmp_path, mutation):
    source = marked_exercises()
    exercise = source[0]
    if mutation == "indentation":
        context = exercise.context.replace("    valeur = 1", "valeur = 1")
    elif mutation == "missing":
        context = exercise.context.replace("cle_primaire", "")
    else:
        context = exercise.context + "\nTexte ajouté."
    altered = [exercise.model_copy(update={"context": context}), *source[1:]]
    path = tmp_path / "changed.pdf"
    render(path, altered)
    with pytest.raises(ValueError):
        validate_llm_pdf(path, source, correction=False)


@pytest.mark.parametrize(
    "policy",
    [None, V35_PRINT_POLICY, V36_LEGACY_PRINT_POLICY, V36_READABLE_PRINT_POLICY],
)
def test_historical_policy_keeps_literal_inline_delimiters(tmp_path, policy):
    source = exercises()
    source[0] = source[0].model_copy(
        update={"context": "Clé <u>ancienne</u> et `historique`."}
    )
    path = tmp_path / "historical.pdf"
    render_assessment(path, source, correction=False, print_policy=policy)
    with pymupdf.open(path) as pdf:
        text = "\n".join(page.get_text() for page in pdf)
    assert "<u>ancienne</u>" in text and "`historique`" in text
    assert (
        french_prose_markup("<u>ancienne</u> et `historique`.")
        == "&lt;u&gt;ancienne&lt;/u&gt; et `historique`."
    )
