"""Real generic PDFs must preserve the complete authored stream, not keywords."""

from copy import deepcopy

import pymupdf
import pytest

from Backend.Core.france import llm_pdf, rendering, whole_case_pdf
from Backend.Core.france.llm_pipeline import PRINT_POLICY, validate_authored_exercise
from Backend.Core.render_transaction import render_pdf_atomically
from tests.test_french_llm_pipeline import raw_exercise


@pytest.fixture(autouse=True)
def policy(monkeypatch):
    # Runtime integration registers this new version. Keep this isolated source
    # commit testable without editing the shared historical policy module.
    for module in (rendering, whole_case_pdf):
        monkeypatch.setattr(
            module,
            "INTERNAL_REVIEW_POLICIES",
            module.INTERNAL_REVIEW_POLICIES | {PRINT_POLICY},
        )


def exercises(*, graphs=False):
    result = []
    for identifier in ("1", "2", "3"):
        raw = raw_exercise(identifier)
        later = deepcopy(raw["materials"][0])
        later.update(id="second_table", title="Second document")
        later["rows"] = [["Gamma", "7"], ["Delta", "9"]]
        raw["materials"].append(later)
        raw["questions"][3]["material_ids"].append("second_table")
        if graphs:
            for suffix in ("one", "two"):
                raw["materials"].append(
                    dict(
                        kind="weighted_graph",
                        id=f"graph_{suffix}",
                        title=f"Réseau {suffix}",
                        nodes=["A", "B", "C"],
                        edges=[["A", "B", 2], ["B", "C", 3]],
                        directed=True,
                    )
                )
        result.append(validate_authored_exercise(raw, identifier))
    return result


def render(path, source, *, correction=False, large_print=False):
    render_pdf_atomically(
        path,
        lambda destination: rendering.render_assessment(
            destination,
            source,
            correction=correction,
            large_print=large_print,
            human_readable_graph_titles=True,
            coherent_material_flow=True,
            print_policy=PRINT_POLICY,
        ),
        role="mark_scheme" if correction else "question_paper",
        language="fr-FR",
    )


@pytest.mark.parametrize("correction", [False, True])
@pytest.mark.parametrize("large_print", [False, True])
def test_real_generic_multimaterial_first_use_later_and_both_print_sizes(
    tmp_path, correction, large_print
):
    path = tmp_path / "paper.pdf"
    source = exercises()
    render(path, source, correction=correction, large_print=large_print)
    llm_pdf.validate_llm_pdf(
        path, source, correction=correction, large_print=large_print
    )


@pytest.mark.parametrize("correction", [False, True])
def test_reused_node_labels_across_and_within_exercises_are_not_artificially_banned(
    tmp_path, correction
):
    path = tmp_path / "graphs.pdf"
    source = exercises(graphs=True)
    render(path, source, correction=correction)
    llm_pdf.validate_llm_pdf(path, source, correction=correction)


def test_swapped_subject_correction_role_refuses(tmp_path):
    path = tmp_path / "subject.pdf"
    source = exercises()
    render(path, source)
    with pytest.raises(ValueError):
        llm_pdf.validate_llm_pdf(path, source, correction=True)


def test_reversed_graph_arrow_refuses_even_when_node_and_weight_text_match(tmp_path):
    path = tmp_path / "graphs.pdf"
    source = exercises(graphs=True)
    render(path, source)
    materials = list(source[0].materials)
    graph = materials[2]
    materials[2] = graph.model_copy(update={"edges": (("B", "A", 2), ("B", "C", 3))})
    changed = [
        source[0].model_copy(update={"materials": tuple(materials)}),
        *source[1:],
    ]
    with pytest.raises(ValueError, match=r"arcs|flèche"):
        llm_pdf.validate_llm_pdf(path, changed, correction=False)


def test_python_indentation_change_cannot_pass_whitespace_compaction(tmp_path):
    source = exercises()
    question = source[0].questions[0]
    code = "valeurs = [1, 2]\nr = 0\nfor x in valeurs:\n    r = r + x"
    expected_question = question.model_copy(
        update={"prompt": question.prompt + "\n```python\n" + code + "\n```"}
    )
    expected = [
        source[0].model_copy(
            update={"questions": (expected_question, *source[0].questions[1:])}
        ),
        *source[1:],
    ]
    altered_question = expected_question.model_copy(
        update={"prompt": expected_question.prompt.replace("    r =", "r =")}
    )
    altered = [
        expected[0].model_copy(
            update={"questions": (altered_question, *expected[0].questions[1:])}
        ),
        *expected[1:],
    ]
    good = tmp_path / "indented.pdf"
    render(good, expected)
    llm_pdf.validate_llm_pdf(good, expected, correction=False)
    wrong = tmp_path / "unindented.pdf"
    render(wrong, altered)
    with pytest.raises(ValueError, match=r"code|indentation"):
        llm_pdf.validate_llm_pdf(wrong, expected, correction=False)


@pytest.mark.parametrize("mutation", ["missing", "extra", "changed"])
def test_missing_extra_or_changed_content_refuses(tmp_path, mutation):
    path = tmp_path / "source.pdf"
    source = exercises()
    render(path, source)
    with pymupdf.open(path) as pdf:
        if mutation == "missing":
            pdf.delete_page(len(pdf) - 1)
        elif mutation == "extra":
            pdf[1].insert_text((60, 60), "Un supplément non déclaré.")
        else:
            words = pdf[1].search_for("Alpha")
            pdf[1].add_redact_annot(words[0])
            pdf[1].apply_redactions()
        modified = tmp_path / "modified.pdf"
        pdf.save(modified)
    with pytest.raises(ValueError):
        llm_pdf.validate_llm_pdf(modified, source, correction=False)
