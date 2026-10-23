"""V28 construction must be executable, independent of row order and replay-bound."""

import itertools
from copy import deepcopy
from decimal import Decimal

import pytest


def test_construction_solution_matches_independent_counts():
    from Backend.Core.france.database_construction_authoring import CONSTRUCTION_CODE

    namespace = {}
    exec(CONSTRUCTION_CODE, namespace)  # App-owned source, never model output.
    count = namespace["repartition_clos"]
    rows = [
        {"id_agent": 2, "id_cat": 1, "statut": "clos"},
        {"id_agent": 1, "id_cat": 2, "statut": "ouvert"},
        {"id_agent": 4, "id_cat": 1, "statut": "clos"},
        {"id_agent": 1, "id_cat": 3, "statut": "clos"},
    ]
    for permutation in itertools.permutations(rows):
        source = list(deepcopy(permutation))
        before = deepcopy(source)
        for categories in ([1, 2, 3, 5], [], [5], [3, 1]):
            assert count(source, categories) == {
                key: sum(r["id_cat"] == key and r["statut"] == "clos" for r in source)
                for key in categories
            }
            assert source == before
    assert count([], [1, 5]) == {1: 0, 5: 0}


@pytest.mark.parametrize("seed", [270100, 270101, 270102])
def test_v28_package_has_construction_credit_and_replays(tmp_path, seed):
    from Backend.Core.france.pipeline import generate_assessment, validate_package
    from tests.test_nsi_pipeline import ControlledTwoOutageFrenchClient, make_index

    index = tmp_path / "references.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=ControlledTwoOutageFrenchClient(),
        seed=seed,
        checkpoint=tmp_path / "checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v28",
    )
    questions = package["exercises"][1]["questions"]
    construction = questions[7]
    assert "repartition_clos" in construction["prompt"]
    assert "def repartition_clos" not in construction["prompt"]
    assert Decimal(construction["points"]) == 1
    assert len(construction["marking"]) == 4
    assert construction["operation"] == "design"
    from Backend.Core.france.verification import verify_contract

    verification = construction["verification"]
    assert verification["construction_version"] == "v28"
    assert verification["expected"]["construction"]["s0_counts"] == [1, 0, 2, 1, 0]
    assert verify_contract(verification)["passed"]
    changed = deepcopy(verification)
    changed["expected"]["construction"]["s0_counts"][0] = 99
    assert not verify_contract(changed)["passed"]
    changed = deepcopy(verification)
    changed["construction_version"] = "v999"
    assert not verify_contract(changed)["passed"]
    changed = deepcopy(verification)
    changed["expected"]["construction"]["prefix_counts"][0][0] = 1
    assert not verify_contract(changed)["passed"]
    assert "k premiers incidents" in questions[11]["prompt"]
    assert "repartition_clos" in questions[11]["prompt"]
    assert Decimal(questions[11]["points"]) == Decimal("0.5")
    assert sum(q["estimated_minutes"] for q in questions) == 70
    assert (
        sum(Decimal(q["points"]) for e in package["exercises"] for q in e["questions"])
        == 18
    )
    validate_package(package)
    bad = deepcopy(package)
    bad["exercises"][1]["questions"][7]["answer"] = "return {}"
    with pytest.raises(ValueError):
        validate_package(bad)
    bad = deepcopy(package)
    stripped = bad["exercises"][1]["questions"][7]["verification"]
    stripped.pop("construction_version")
    stripped["expected"].pop("construction")
    with pytest.raises(ValueError):
        validate_package(bad)


@pytest.mark.parametrize("large_print", [False, True])
def test_v28_working_tables_stay_with_questions(tmp_path, large_print):
    import pymupdf

    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.pipeline import generate_assessment
    from Backend.Core.france.rendering import render_assessment
    from tests.test_nsi_pipeline import ControlledTwoOutageFrenchClient, make_index

    index = tmp_path / "references.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=ControlledTwoOutageFrenchClient(),
        seed=270100,
        checkpoint=tmp_path / "checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v28",
    )
    exercises = [NSIExercise.model_validate(raw) for raw in package["exercises"]]
    for correction in (False, True):
        path = tmp_path / f"{correction}.pdf"
        render_assessment(
            path,
            exercises,
            correction=correction,
            large_print=large_print,
            coherent_material_flow=True,
            human_readable_graph_titles=True,
        )
        with pymupdf.open(path) as pdf:
            pages = [page.get_text() for page in pdf]
            assert all(
                0 <= w[0] <= w[2] <= p.rect.width and 0 <= w[1] <= w[3] <= p.rect.height
                for p in pdf
                for w in p.get_text("words")
            )
        assert " — recon_" not in "\n".join(pages)
        if not large_print:
            for title, question in (
                ("rapport comparé (2c–2e)", "2c."),
                ("effectifs (2f)", "2f."),
                ("états et fonction (2i–2k)", "2i."),
                ("Cartes après la reprise", "3i."),
            ):
                assert any(title in page and question in page for page in pages)
