# V35 must explicitly request its notices and preserve all printed content

from copy import deepcopy
from itertools import combinations

import pymupdf
import pytest

from tests.test_french_expanded_pipeline import generate


@pytest.mark.parametrize("correction", [False, True])
def test_expanded_paper_keeps_its_content_and_internal_review_notices(
    tmp_path, correction
):
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.rendering import render_assessment
    from Backend.Core.france.whole_case_pdf import validate_whole_case_pdf
    from Backend.Core.render_transaction import render_pdf_atomically

    package = generate(tmp_path)
    path = tmp_path / "expanded.pdf"
    render_pdf_atomically(
        path,
        lambda destination: render_assessment(
            destination,
            [NSIExercise.model_validate(exercise) for exercise in package["exercises"]],
            correction=correction,
            human_readable_graph_titles=True,
            coherent_material_flow=True,
            compact_correction=True,
            print_policy=package["identity"]["print_policy"],
        ),
        role="mark_scheme" if correction else "question_paper",
        language="fr-FR",
    )
    validate_whole_case_pdf(path, package, correction=correction)
    with pymupdf.open(path) as pdf:
        assert "Difficulté et durée non calibrées" in pdf[0].get_text()
        assert all(
            page.get_text(clip=pymupdf.Rect(0, 0, 595, 760)).strip() for page in pdf
        )
        text = "\n".join(page.get_text() for page in pdf)
        assert "3l." in text and "1a." in text


def test_explicit_v35_generation_dispatch_never_calls_a_model(tmp_path):
    from Backend.Core.france.pipeline import generate_assessment, validate_package
    from tests.test_nsi_pipeline import make_index

    class NoModel:
        def generate_json(self, *args, **kwargs):
            pytest.fail("The app-owned source must not call a model")

    index = tmp_path / "references.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=NoModel(),
        seed=270104,
        checkpoint=tmp_path / "checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v35",
    )
    assert package["identity"]["model"] == "app-owned-v35"
    assert validate_package(package)["structural_checks"] == "passed"


@pytest.mark.parametrize("change", ["reverse", "endpoint", "undirected"])
def test_graph_connections_cannot_change_while_leaving_its_labels_unchanged(
    tmp_path, change
):
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.rendering import render_assessment
    from Backend.Core.france.whole_case_pdf import validate_whole_case_pdf
    from Backend.Core.render_transaction import render_pdf_atomically

    package = generate(tmp_path)
    raw = deepcopy(package["exercises"])
    graph = raw[0]["materials"][0]
    if change == "reverse":
        graph["edges"][0] = ["a", "r", 1]
    elif change == "endpoint":
        graph["edges"][0] = ["r", "e", 1]
    else:
        graph["directed"] = False
    path = tmp_path / "wrong-graph.pdf"
    render_pdf_atomically(
        path,
        lambda destination: render_assessment(
            destination,
            [NSIExercise.model_validate(e) for e in raw],
            correction=False,
            human_readable_graph_titles=True,
            coherent_material_flow=True,
            compact_correction=True,
            print_policy=package["identity"]["print_policy"],
        ),
        role="question_paper",
        language="fr-FR",
    )
    with pytest.raises(ValueError, match="graphe"):
        validate_whole_case_pdf(path, package, correction=False)


def test_enlarged_graph_keeps_its_node_labels_at_the_body_size(tmp_path):
    from Backend.Core.france.graph_pdf import _centres
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.rendering import render_assessment
    from Backend.Core.render_transaction import render_pdf_atomically

    package = generate(tmp_path)
    path = tmp_path / "enlarged.pdf"
    render_pdf_atomically(
        path,
        lambda destination: render_assessment(
            destination,
            [NSIExercise.model_validate(e) for e in package["exercises"]],
            correction=False,
            large_print=True,
            human_readable_graph_titles=True,
            coherent_material_flow=True,
            compact_correction=True,
            print_policy=package["identity"]["print_policy"],
        ),
        role="question_paper",
        language="fr-FR",
    )
    with pymupdf.open(path) as pdf:
        page = next(
            page for page in pdf if "Raccourcis du catalogue" in page.get_text()
        )
        positions = _centres(page, tuple("rabcde"), page.get_drawings())
        assert positions is not None
        edges = package["exercises"][0]["materials"][0]["edges"]

        def side(a, b, c):
            return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

        for (a, b, _), (c, d, _) in combinations(edges, 2):
            if len({a, b, c, d}) < 4:
                continue
            first = side(positions[a], positions[b], positions[c]) * side(
                positions[a], positions[b], positions[d]
            )
            second = side(positions[c], positions[d], positions[a]) * side(
                positions[c], positions[d], positions[b]
            )
            assert not (first < 0 and second < 0), (a, b, c, d)
        sizes = []
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    if span["text"] not in positions:
                        continue
                    rect = pymupdf.Rect(span["bbox"])
                    point = pymupdf.Point(
                        (rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2
                    )
                    centre = positions[span["text"]]
                    if abs(point.x - centre[0]) < 16 and abs(point.y - centre[1]) < 16:
                        sizes.append(span["size"])
        assert len(sizes) == 6
        context_sizes = [
            span["size"]
            for source_page in pdf
            for block in source_page.get_text("dict")["blocks"]
            for line in block.get("lines", [])
            for span in line["spans"]
            if span["text"].startswith("Un catalogue")
        ]
        assert context_sizes
        assert min(sizes) >= max(context_sizes)
