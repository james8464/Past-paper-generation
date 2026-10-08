import json
from dataclasses import asdict
from decimal import Decimal
from hashlib import sha256

import pytest

from Backend.Core.education_context import NSI_CONTEXT
from Backend.Core.scoped_references import ReferenceIndex, SourceDocument


def make_index(path):
    with ReferenceIndex(path) as index:
        for category in ("programme", "official_paper"):
            text = "Structures de données arbres listes piles files graphes algorithmique réseaux routage bases de données SQL programmation."
            document = SourceDocument(
                id=category,
                context=NSI_CONTEXT,
                curriculum_version="nsi-2019",
                category=category,
                authority="MEN",
                url="https://eduscol.education.gouv.fr/test",
                retrieved_at="2026-09-28T12:00:00+00:00",
                sha256=sha256(text.encode()).hexdigest(),
                session=2026,
                centre="national",
                rights="reference-only",
                split="reference",
            )
            index.add(document, text, [(1, text)])


def test_graph_tree_binding_prints_locked_materials_and_declared_node_api():
    from Backend.Core.france.graph_tree_binding import canonical_answer
    from Backend.Core.france.graph_tree_contract import build_graph_tree_contract
    from Backend.Core.france.pipeline import _bind_graph_tree_contract

    contract = build_graph_tree_contract(270100, "1")
    expected = contract.to_dict()["expected"]
    raw = {
        "context": "Une équipe étudie ses trajets et les demandes d'intervention.",
        "materials": [],
        "questions": [
            {
                "id": task_id,
                "contract_task_id": task_id,
                "claimed_result": expected[task_id],
                "prompt": f"Examinez le support `{'arbre' if task_id in ('1e', '1f') else 'reseau'}`.",
                "answer": canonical_answer(task_id, expected[task_id]),
                "marking": [
                    {
                        "points": "1",
                        "criterion": canonical_answer(task_id, expected[task_id]),
                    }
                ],
            }
            for task_id in contract.to_dict()["task_ids"]
        ],
    }

    bound, binding = _bind_graph_tree_contract(raw, contract)
    assert {item["id"] for item in bound["materials"]} == {"reseau", "arbre"}
    assert "class Noeud:" in bound["context"]
    assert "self.gauche = None" in bound["context"]
    assert "def parcours_largeur(reseau, depart):" in bound["context"]
    assert "if visin not in visites:" in bound["context"]
    assert binding["contract_sha256"] == contract.digest
    assert [item["task_id"] for item in binding["questions"]] == contract.to_dict()[
        "task_ids"
    ]
    assert all("claimed_result" not in item for item in bound["questions"])
    assert (
        " → ".join(contract.to_dict()["expected"]["1a"]["path"])
        in bound["questions"][0]["answer"]
    )
    assert (
        " → ".join(contract.to_dict()["expected"]["1d"]["order"])
        in bound["questions"][3]["answer"]
    )
    assert bound["questions"][4]["answer"] == raw["questions"][4]["answer"]


def test_graph_tree_binding_rejects_a_missing_graph_edge():
    from Backend.Core.france.graph_tree_binding import canonical_answer
    from Backend.Core.france.graph_tree_contract import build_graph_tree_contract
    from Backend.Core.france.pipeline import _bind_graph_tree_contract

    contract = build_graph_tree_contract(270100, "1")
    raw = {
        "context": "Un réseau de collecte relie les postes.",
        "materials": [],
        "questions": [
            {
                "id": task_id,
                "contract_task_id": task_id,
                "claimed_result": contract.to_dict()["expected"][task_id],
                "prompt": "Le graphe `reseau` contient l'arête A-F. Calculez son poids."
                if task_id == "1a"
                else "Examinez les données.",
                "answer": canonical_answer(
                    task_id, contract.to_dict()["expected"][task_id]
                ),
                "marking": [
                    {
                        "points": "1",
                        "criterion": canonical_answer(
                            task_id, contract.to_dict()["expected"][task_id]
                        ),
                    }
                ],
            }
            for task_id in contract.to_dict()["task_ids"]
        ],
    }
    with pytest.raises(ValueError, match=r"arête|graphe"):
        _bind_graph_tree_contract(raw, contract)


def test_graph_tree_binding_rejects_false_weight_for_an_existing_edge():
    """A correct structured claim cannot license a contradictory printed fact."""
    from Backend.Core.france.graph_tree_binding import canonical_answer
    from Backend.Core.france.graph_tree_contract import build_graph_tree_contract
    from Backend.Core.france.pipeline import _bind_graph_tree_contract

    contract = build_graph_tree_contract(270100, "1")
    raw = {
        "context": "Une équipe étudie un réseau de collecte.",
        "materials": [],
        "questions": [
            {
                "id": task_id,
                "contract_task_id": task_id,
                "claimed_result": contract.to_dict()["expected"][task_id],
                "prompt": "L'arête A-B a un poids de 99. Quel chemin choisir ?"
                if task_id == "1a"
                else "Examinez les données fournies.",
                "answer": canonical_answer(
                    task_id, contract.to_dict()["expected"][task_id]
                ),
                "marking": [
                    {
                        "points": "1",
                        "criterion": canonical_answer(
                            task_id, contract.to_dict()["expected"][task_id]
                        ),
                    }
                ],
            }
            for task_id in contract.to_dict()["task_ids"]
        ],
    }
    with pytest.raises(ValueError, match=r"poids|arête"):
        _bind_graph_tree_contract(raw, contract)


def test_graph_tree_binding_rejects_false_context_weight_even_with_valid_questions():
    from Backend.Core.france.graph_tree_binding import canonical_answer
    from Backend.Core.france.graph_tree_contract import build_graph_tree_contract
    from Backend.Core.france.pipeline import _bind_graph_tree_contract

    contract = build_graph_tree_contract(270100, "1")
    expected = contract.to_dict()["expected"]
    raw = {
        "context": "L'arête A-B a un poids de 99 dans ce réseau de collecte.",
        "materials": [],
        "questions": [
            {
                "id": task_id,
                "contract_task_id": task_id,
                "claimed_result": expected[task_id],
                "prompt": "Analysez les données fournies.",
                "answer": canonical_answer(task_id, expected[task_id]),
                "marking": [
                    {
                        "points": "1",
                        "criterion": canonical_answer(task_id, expected[task_id]),
                    }
                ],
            }
            for task_id in contract.to_dict()["task_ids"]
        ],
    }
    with pytest.raises(ValueError, match=r"poids|arête"):
        _bind_graph_tree_contract(raw, contract)


def test_graph_tree_binding_rejects_false_authored_answer_instead_of_replacing_it():
    from Backend.Core.france.graph_tree_contract import build_graph_tree_contract
    from Backend.Core.france.pipeline import _bind_graph_tree_contract

    contract = build_graph_tree_contract(270100, "1")
    raw = {
        "context": "Une équipe étudie un réseau de collecte.",
        "materials": [],
        "questions": [
            {
                "id": task_id,
                "contract_task_id": task_id,
                "claimed_result": contract.to_dict()["expected"][task_id],
                "prompt": "Analysez le support de l'exercice.",
                "answer": "Le chemin le plus court a un poids total de 99."
                if task_id == "1a"
                else "Réponse contextualisée.",
            }
            for task_id in contract.to_dict()["task_ids"]
        ],
    }
    with pytest.raises(ValueError, match=r"réponse|Résultat|contrat"):
        _bind_graph_tree_contract(raw, contract)


def test_graph_tree_binding_rejects_generic_credit_with_no_checked_result():
    from Backend.Core.france.graph_tree_binding import canonical_answer
    from Backend.Core.france.graph_tree_contract import build_graph_tree_contract
    from Backend.Core.france.pipeline import _bind_graph_tree_contract

    contract = build_graph_tree_contract(270100, "1")
    expected = contract.to_dict()["expected"]
    raw = {
        "context": "Une équipe étudie un réseau de collecte.",
        "materials": [],
        "questions": [
            {
                "id": task_id,
                "contract_task_id": task_id,
                "claimed_result": expected[task_id],
                "prompt": "Analysez le support de l'exercice.",
                "answer": canonical_answer(task_id, expected[task_id]),
                "marking": [
                    {"points": "1", "criterion": "Méthode et résultat corrects."}
                ],
            }
            for task_id in contract.to_dict()["task_ids"]
        ],
    }
    with pytest.raises(ValueError, match=r"barème|critère|résultat"):
        _bind_graph_tree_contract(raw, contract)


def test_graph_tree_binding_rejects_an_incorrect_bfs_claim():
    from Backend.Core.france.graph_tree_binding import canonical_answer
    from Backend.Core.france.graph_tree_contract import build_graph_tree_contract
    from Backend.Core.france.pipeline import _bind_graph_tree_contract

    contract = build_graph_tree_contract(270100, "1")
    raw = {
        "context": "Un réseau de collecte relie les postes.",
        "materials": [],
        "questions": [
            {
                "id": task_id,
                "contract_task_id": task_id,
                "claimed_result": {"order": ["F", "E", "D", "C", "B", "A"]}
                if task_id == "1d"
                else contract.to_dict()["expected"][task_id],
                "prompt": "Examinez les données.",
                "answer": canonical_answer(
                    task_id, contract.to_dict()["expected"][task_id]
                ),
                "marking": [
                    {
                        "points": "1",
                        "criterion": canonical_answer(
                            task_id, contract.to_dict()["expected"][task_id]
                        ),
                    }
                ],
            }
            for task_id in contract.to_dict()["task_ids"]
        ],
    }
    with pytest.raises(ValueError, match="Résultat déclaré"):
        _bind_graph_tree_contract(raw, contract)


def test_graph_tree_binding_rejects_a_bfs_answer_that_contradicts_its_claim():
    from Backend.Core.france.graph_tree_binding import canonical_answer
    from Backend.Core.france.graph_tree_contract import build_graph_tree_contract
    from Backend.Core.france.pipeline import _bind_graph_tree_contract

    contract = build_graph_tree_contract(270100, "1")
    raw = {
        "context": "Un réseau de collecte relie les postes.",
        "materials": [],
        "questions": [
            {
                "id": task_id,
                "contract_task_id": task_id,
                "claimed_result": contract.to_dict()["expected"][task_id],
                "prompt": "Examinez les données.",
                "answer": "Ordre du parcours en largeur : F, E, D, C, B, A."
                if task_id == "1d"
                else canonical_answer(task_id, contract.to_dict()["expected"][task_id]),
                "marking": [
                    {
                        "points": "1",
                        "criterion": canonical_answer(
                            task_id, contract.to_dict()["expected"][task_id]
                        ),
                    }
                ],
            }
            for task_id in contract.to_dict()["task_ids"]
        ],
    }
    with pytest.raises(ValueError, match=r"parcours|réponse"):
        _bind_graph_tree_contract(raw, contract)


def test_graph_tree_candidate_uses_locked_materials_before_all_exercise_checks():
    from Backend.Core.france.graph_tree_binding import canonical_answer
    from Backend.Core.france.graph_tree_contract import build_graph_tree_contract
    from Backend.Core.france.pipeline import (
        _prepare_candidate,
        _prompt,
        _tasks_for_seed,
    )

    task = _tasks_for_seed(270100)[0]
    contract = build_graph_tree_contract(270100, "1")
    raw = FrenchClient().generate_json(
        _prompt({**task, "exercise_id": "1"}, [], 270100, 1, "")
    )
    raw["materials"] = []
    raw["context"] = (
        "Une équipe étudie un réseau de collecte et les demandes associées."
    )
    for question in raw["questions"]:
        task_id = question["id"]
        material_id = "arbre" if task_id in ("1e", "1f") else "reseau"
        question["contract_task_id"] = task_id
        question["claimed_result"] = contract.to_dict()["expected"][task_id]
        question["material_ids"] = [material_id]
        question["prompt"] = (
            f"Examinez le support `{material_id}` et justifiez votre résultat."
        )
        question["verification"] = {"kind": "human"}
        question["answer"] = canonical_answer(
            task_id, contract.to_dict()["expected"][task_id]
        )
        question["marking"] = [
            {"points": question["points"], "criterion": question["answer"]}
        ]

    exercise, _, _, checks, _, binding = _prepare_candidate(
        raw, task, "1", [], [], contract=contract
    )
    assert {item.id for item in exercise.materials} == {"reseau", "arbre"}
    assert "class Noeud:" in exercise.context
    assert binding["contract_sha256"] == contract.digest
    assert all(item["state"] != "failed" for item in checks)


class FrenchClient:
    provider = "ollama"
    model = "fixture"
    model_digest = "fixture-digest"

    def __init__(self, reject=False):
        self.calls = 0
        self.reject = reject

    def generate_json(self, prompt):
        self.calls += 1
        if prompt.startswith("Contrôle indépendant des capacités"):
            request = json.loads(prompt.split("\nDONNÉES_JSON\n", 1)[1])
            return {
                "questions": [
                    {
                        "question_id": planned["id"],
                        "objective_code": planned["required_curriculum_code"],
                        "aligned": True,
                        "rationale": "La consigne de cette question mobilise effectivement la capacité prévue dans le plan.",
                        "issues": [],
                    }
                    for planned in request["question_blueprint"]
                ]
            }
        if prompt.startswith("Résous indépendamment"):
            candidate = json.loads(prompt.split("\n", 1)[1])
            return {
                "answers": {
                    question["id"]: str(index)
                    for index, question in enumerate(candidate["questions"], start=1)
                },
                "issues": [],
                "minutes": 60,
            }
        if prompt.startswith("Vérifie ce sujet"):
            candidate = json.loads(prompt.split("\n", 1)[1])["exercise"]
            return {
                "correct": not self.reject,
                "native_french": True,
                "curriculum_aligned": True,
                "difficulty_appropriate": True,
                "marking_consistent": True,
                "context_consistent": True,
                "issues": [],
                "rationale": "Analyse détaillée de chaque réponse et de son barème.",
                "question_ids": [question["id"] for question in candidate["questions"]],
            }
        task = json.loads(prompt.split("DONNÉES_JSON\n", 1)[1])
        number = task["exercise_id"]
        question_blueprint = task["question_blueprint"]
        if task["required_material_kind"] == "weighted_graph":
            materials = [
                {
                    "kind": "weighted_graph",
                    "id": "support",
                    "title": "Graphe de travail",
                    "nodes": ["A", "B", "C"],
                    "edges": [["A", "B", 2], ["B", "C", 3]],
                    "directed": True,
                }
            ]
        else:
            materials = [
                {
                    "kind": "table",
                    "id": "support",
                    "title": "Données de travail",
                    "columns": ["id", "valeur"],
                    "rows": [["1", "4"], ["2", "7"]],
                }
            ]
        scenarios = {
            "1": (
                "Parcours forestiers",
                "Un service forestier compare des parcours pondérés entre plusieurs postes de surveillance.",
                "Pour le parcours {i}, calculer le coût obtenu et démontrer chaque étape de l'algorithme.",
            ),
            "2": (
                "Catalogue de médiathèque",
                "Une médiathèque conserve les emprunts et les ouvrages dans des relations normalisées.",
                "Pour le besoin {i}, écrire la requête relationnelle et expliquer les contraintes mobilisées.",
            ),
            "3": (
                "Collecte météorologique",
                "Un observatoire échange des mesures entre capteurs, routeurs et serveurs de stockage.",
                "Pour le paquet {i}, analyser le traitement effectué et justifier la décision du protocole.",
            ),
        }
        title, context, prompt = scenarios[number]
        return {
            "id": number,
            "title": title,
            "context": context,
            "topics": task["topics"],
            "minutes": task["minutes"],
            "target_points": task["technical_points"],
            "materials": materials,
            "questions": [
                dict(
                    id=plan["id"],
                    prompt=prompt.format(i=i),
                    points=plan["points"],
                    answer=str(i),
                    marking=[
                        {
                            "points": plan["points"],
                            "criterion": f"Résultat {i} et justification.",
                        }
                    ],
                    material_ids=["support"] if i == 1 else [],
                    curriculum_codes=[plan["required_curriculum_code"]],
                    operation=plan["operation"],
                    difficulty=plan["difficulty"],
                    estimated_minutes=plan["estimated_minutes"],
                    verification={
                        "kind": "binary",
                        "input": format(i, "b"),
                        "expected": i,
                    },
                )
                for i, plan in enumerate(question_blueprint, start=1)
            ],
        }


class ContractFrenchClient(FrenchClient):
    def __init__(self, stop_on_part=None):
        super().__init__()
        self.part_calls = []
        self.stop_on_part = stop_on_part

    def generate_json(self, prompt):
        if prompt.startswith("Rédige la partie "):
            part = prompt[len("Rédige la partie ")]
            if self.stop_on_part == part:
                raise KeyboardInterrupt
            self.part_calls.append(part)
            self.calls += 1
            request = json.loads(prompt.split("\nDONNÉES_JSON\n", 1)[1])
            questions = []
            for plan in request["question_blueprint"]:
                material = "arbre" if plan["id"] in {"1e", "1f"} else "reseau"
                questions.append(
                    {
                        "id": plan["id"],
                        "contract_task_id": plan["id"],
                        "claimed_result": request["expected"][plan["id"]],
                        "prompt": f"Pour la tâche {plan['id']}, analysez le support `{material}` et justifiez le résultat.",
                        "points": plan["points"],
                        "answer": request["required_answers"][plan["id"]],
                        "marking": [
                            {
                                "points": plan["points"],
                                "criterion": request["required_answers"][plan["id"]],
                            }
                        ],
                        "material_ids": [material],
                        "curriculum_codes": [plan["required_curriculum_code"]],
                        "operation": plan["operation"],
                        "difficulty": plan["difficulty"],
                        "estimated_minutes": plan["estimated_minutes"],
                        "verification": {"kind": "human"},
                    }
                )
            if request["part"] == "A":
                return {
                    "title": "Réseau et interventions",
                    "context": "Une équipe étudie les trajets et les demandes d'intervention.",
                    "questions": questions,
                }
            return {"questions": questions}
        return super().generate_json(prompt)


class ClosedProseFrenchClient(FrenchClient):
    """Only the external model response is faked; package validation is real."""

    def generate_json(self, prompt):
        if prompt.startswith("Sélectionne la partie "):
            request = json.loads(prompt.split("\nDONNÉES_JSON\n", 1)[1])
            result = {
                "questions": [
                    {
                        "contract_task_id": task_id,
                        "claimed_result": request["expected"][task_id],
                        "question_form_id": f"{task_id}-q1",
                        "rubric_form_id": f"{task_id}-r1",
                    }
                    for task_id in request["task_ids"]
                ]
            }
            if request["part"] == "A":
                result.update(scene_id="service", slots={"activity": "interventions"})
            return result
        return super().generate_json(prompt)


class ControlledDatabaseFrenchClient(ClosedProseFrenchClient):
    def generate_json(self, prompt):
        if prompt.startswith("Sélectionne l'exercice 2"):
            return {
                "scene_id": "atelier",
                "question_forms": {
                    f"2{letter}": f"2{letter}-q1" for letter in "abcdef"
                },
                "rubric_forms": {f"2{letter}": f"2{letter}-r1" for letter in "abcdef"},
            }
        return super().generate_json(prompt)


class ControlledNetworkFrenchClient(ControlledDatabaseFrenchClient):
    def generate_json(self, prompt):
        if prompt.startswith("Sélectionne l'exercice 3"):
            return {
                "scene_id": "campus",
                "question_forms": {
                    f"3{letter}": f"3{letter}-q1" for letter in "abcdef"
                },
                "rubric_forms": {f"3{letter}": f"3{letter}-r1" for letter in "abcdef"},
            }
        return super().generate_json(prompt)


class ControlledNetworkDepthFrenchClient(ControlledNetworkFrenchClient):
    def generate_json(self, prompt):
        if prompt.startswith("Sélectionne la séquence réseau v15"):
            return {
                "scene_id": "campus",
                "question_forms": {
                    f"3{letter}": f"3{letter}-q1" for letter in "abcdef"
                },
                "rubric_forms": {f"3{letter}": f"3{letter}-r1" for letter in "abcdef"},
            }
        return super().generate_json(prompt)


class ControlledDatabaseDepthFrenchClient(ControlledNetworkDepthFrenchClient):
    def generate_json(self, prompt):
        if prompt.startswith("Sélectionne l'exercice 2 v16"):
            return {
                "scene_id": "atelier",
                "question_forms": {
                    f"2{letter}": f"2{letter}-q1" for letter in "abcdefghij"
                },
                "rubric_forms": {
                    f"2{letter}": f"2{letter}-r1" for letter in "abcdefghij"
                },
            }
        return super().generate_json(prompt)


class ControlledGraphTreeDepthFrenchClient(ControlledDatabaseDepthFrenchClient):
    def generate_json(self, prompt):
        if prompt.startswith("Sélectionne l'exercice 1 v17"):
            return {
                "scene_id": "service",
                "question_forms": {
                    f"1{letter}": f"1{letter}-q1" for letter in "abcdefghij"
                },
                "rubric_forms": {
                    f"1{letter}": f"1{letter}-r1" for letter in "abcdefghij"
                },
            }
        return super().generate_json(prompt)


def test_v17_graph_tree_depth_package_replays_without_changing_v16(tmp_path):
    from copy import deepcopy
    from decimal import Decimal

    from Backend.Core.france.graph_tree_contract import build_graph_tree_contract
    from Backend.Core.france.pipeline import (
        _tasks_for_seed_v17,
        digest,
        generate_assessment,
        validate_package,
    )

    index = tmp_path / "sources.sqlite"
    make_index(index)
    blueprint = _tasks_for_seed_v17(270100)
    assert [item["id"] for item in blueprint[0]["question_blueprint"]] == [
        f"1{letter}" for letter in "abcdefghij"
    ]
    assert len(blueprint[1]["question_blueprint"]) == 10
    assert len(blueprint[2]["question_blueprint"]) == 6
    package = generate_assessment(
        index_path=index,
        client=ControlledGraphTreeDepthFrenchClient(),
        seed=270100,
        checkpoint=tmp_path / "v17-checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v17",
    )
    assert package["identity"]["prompt_version"] == "fr-nsi-written-2027-v17"
    assert package["identity"]["graph_tree_depth_contract_sha256"]
    assert [len(item["questions"]) for item in package["exercises"]] == [10, 10, 6]
    assert sum(Decimal(item["target_points"]) for item in package["exercises"]) == 18
    assert package["language_points"] == "2"
    assert package["evidence"][0]["graph_tree_depth_selection"]["accepted"]["response"]
    assert validate_package(package)["structural_checks"] == "passed"

    changed = deepcopy(package)
    changed["exercises"][0]["questions"][0]["answer"] = "Réponse inventée."
    changed["content_sha256"] = digest(changed["exercises"])
    changed["evidence"][0]["exercise_sha256"] = digest(changed["exercises"][0])
    with pytest.raises(ValueError):
        validate_package(changed)
    mixed = deepcopy(package)
    mixed["identity"]["graph_tree_depth_contract_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        validate_package(mixed)
    mixed = deepcopy(package)
    mixed["identity"]["graph_tree_contract_sha256"] = build_graph_tree_contract(
        270100, "1"
    ).digest
    for item, key in zip(
        mixed["evidence"],
        (
            "graph_tree_depth_selection",
            "database_depth_selection",
            "network_depth_selection",
        ),
        strict=True,
    ):
        item[key]["run_identity_sha256"] = digest(mixed["identity"])
    with pytest.raises(ValueError, match=r"mixte|incompatible"):
        validate_package(mixed)

    old = generate_assessment(
        index_path=index,
        client=ControlledDatabaseDepthFrenchClient(),
        seed=270100,
        checkpoint=tmp_path / "v16-checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v16",
    )
    assert validate_package(old)["structural_checks"] == "passed"
    assert len(old["exercises"][0]["questions"]) == 6
    with pytest.raises(ValueError, match="identité"):
        generate_assessment(
            index_path=index,
            client=ControlledGraphTreeDepthFrenchClient(),
            seed=270100,
            checkpoint=tmp_path / "v16-checkpoint.json",
            contract_graph_tree=True,
            contract_authoring_version="v17",
        )


def test_v16_database_depth_package_replays_with_exact_credit(tmp_path):
    from copy import deepcopy

    from Backend.Core.france.pipeline import (
        _tasks_for_seed_v16,
        digest,
        generate_assessment,
        validate_package,
    )

    index = tmp_path / "sources.sqlite"
    make_index(index)
    blueprint = _tasks_for_seed_v16(270100)
    assert [item["id"] for item in blueprint[1]["question_blueprint"]] == [
        f"2{letter}" for letter in "abcdefghij"
    ]
    assert (
        sum(item["estimated_minutes"] for item in blueprint[1]["question_blueprint"])
        == 70
    )
    package = generate_assessment(
        index_path=index,
        client=ControlledDatabaseDepthFrenchClient(),
        seed=270100,
        checkpoint=tmp_path / "v16-checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v16",
    )
    assert package["identity"]["prompt_version"] == "fr-nsi-written-2027-v16"
    assert package["identity"]["database_depth_contract_sha256"]
    assert len(package["exercises"][1]["questions"]) == 10
    assert (
        sum(float(exercise["target_points"]) for exercise in package["exercises"]) == 18
    )
    assert package["language_points"] == "2"
    assert package["evidence"][1]["database_depth_selection"]["accepted"]["response"]
    assert validate_package(package)["structural_checks"] == "passed"
    changed = deepcopy(package)
    changed["exercises"][1]["questions"][0]["answer"] = "Une réponse inventée."
    changed["content_sha256"] = digest(changed["exercises"])
    changed["evidence"][1]["exercise_sha256"] = digest(changed["exercises"][1])
    with pytest.raises(ValueError):
        validate_package(changed)


def test_v15_checkpoint_cannot_resume_as_v16_and_old_package_still_replays(tmp_path):
    from Backend.Core.france.pipeline import generate_assessment, validate_package

    index = tmp_path / "sources.sqlite"
    make_index(index)
    checkpoint = tmp_path / "preserve-v15.json"
    package = generate_assessment(
        index_path=index,
        client=ControlledNetworkDepthFrenchClient(),
        seed=270100,
        checkpoint=checkpoint,
        contract_graph_tree=True,
        contract_authoring_version="v15",
    )
    original = checkpoint.read_bytes()
    with pytest.raises(ValueError, match="identité"):
        generate_assessment(
            index_path=index,
            client=ControlledDatabaseDepthFrenchClient(),
            seed=270100,
            checkpoint=checkpoint,
            contract_graph_tree=True,
            contract_authoring_version="v16",
        )
    assert checkpoint.read_bytes() == original
    assert validate_package(package)["structural_checks"] == "passed"


def test_v15_network_depth_package_has_exact_credit_and_replays(tmp_path):
    from copy import deepcopy

    from Backend.Core.france.pipeline import (
        digest,
        generate_assessment,
        validate_package,
    )

    index = tmp_path / "sources.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=ControlledNetworkDepthFrenchClient(),
        seed=270100,
        checkpoint=tmp_path / "v15-checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v15",
    )
    assert package["identity"]["prompt_version"] == "fr-nsi-written-2027-v15"
    assert package["identity"]["network_depth_contract_sha256"]
    assert (
        sum(float(exercise["target_points"]) for exercise in package["exercises"]) == 18
    )
    assert package["language_points"] == "2"
    assert package["evidence"][2]["network_depth_selection"]["accepted"]["response"]
    assert validate_package(package)["structural_checks"] == "passed"
    changed = deepcopy(package)
    changed["exercises"][2]["questions"][1]["answer"] = "Une autre route."
    changed["content_sha256"] = digest(changed["exercises"])
    changed["evidence"][2]["exercise_sha256"] = digest(changed["exercises"][2])
    with pytest.raises(ValueError):
        validate_package(changed)


def test_v14_checkpoint_is_not_resumed_as_v15_and_old_package_still_replays(tmp_path):
    from Backend.Core.france.pipeline import generate_assessment, validate_package

    index = tmp_path / "sources.sqlite"
    make_index(index)
    checkpoint = tmp_path / "preserve-v14.json"
    package = generate_assessment(
        index_path=index,
        client=ControlledNetworkFrenchClient(),
        seed=270100,
        checkpoint=checkpoint,
        contract_graph_tree=True,
        contract_authoring_version="v14",
    )
    original = checkpoint.read_bytes()
    assert validate_package(package)["structural_checks"] == "passed"
    with pytest.raises(ValueError, match="identité"):
        generate_assessment(
            index_path=index,
            client=ControlledNetworkDepthFrenchClient(),
            seed=270100,
            checkpoint=checkpoint,
            contract_graph_tree=True,
            contract_authoring_version="v15",
        )
    assert checkpoint.read_bytes() == original
    assert validate_package(package)["structural_checks"] == "passed"


def test_v14_controlled_network_package_replays_and_rejects_rehashed_tamper(tmp_path):
    from copy import deepcopy

    from Backend.Core.france.pipeline import (
        digest,
        generate_assessment,
        validate_package,
    )

    index = tmp_path / "sources.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=ControlledNetworkFrenchClient(),
        seed=270100,
        checkpoint=tmp_path / "checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v14",
    )
    assert package["identity"]["prompt_version"] == "fr-nsi-written-2027-v14"
    assert package["identity"]["network_contract_sha256"]
    assert package["evidence"][2]["network_selection"]["accepted"]["response"]
    assert validate_package(package)["structural_checks"] == "passed"
    changed = deepcopy(package)
    changed["exercises"][2]["questions"][1]["answer"] = "Une autre route."
    changed["content_sha256"] = digest(changed["exercises"])
    changed["evidence"][2]["exercise_sha256"] = digest(changed["exercises"][2])
    with pytest.raises(ValueError, match=r"network|Network|identique|preuve"):
        validate_package(changed)


def test_v13_controlled_database_package_replays_and_rejects_rehashed_tamper(tmp_path):
    from copy import deepcopy

    from Backend.Core.france.pipeline import (
        digest,
        generate_assessment,
        validate_package,
    )

    index = tmp_path / "sources.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=ControlledDatabaseFrenchClient(),
        seed=270100,
        checkpoint=tmp_path / "checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v13",
    )
    assert package["identity"]["prompt_version"] == "fr-nsi-written-2027-v13"
    assert package["identity"]["database_contract_sha256"]
    assert package["evidence"][1]["database_selection"]["accepted"]["response"]
    assert validate_package(package)["structural_checks"] == "passed"
    changed = deepcopy(package)
    changed["exercises"][1]["questions"][2]["answer"] = "Une autre requête."
    changed["content_sha256"] = digest(changed["exercises"])
    changed["evidence"][1]["exercise_sha256"] = digest(changed["exercises"][1])
    with pytest.raises(ValueError, match=r"database|Database|identique|preuve"):
        validate_package(changed)


def test_v12_closed_prose_package_replays_and_binds_catalogue(tmp_path):
    from Backend.Core.france.graph_tree_prose import (
        PROSE_CONTRACT_VERSION,
        prose_catalogue_digest,
    )
    from Backend.Core.france.pipeline import generate_assessment, validate_package

    index = tmp_path / "sources.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=ClosedProseFrenchClient(),
        seed=270100,
        checkpoint=tmp_path / "checkpoint.json",
        contract_graph_tree=True,
    )
    assert package["identity"]["prompt_version"] == "fr-nsi-written-2027-v12"
    assert package["identity"]["prose_contract_version"] == PROSE_CONTRACT_VERSION
    assert package["identity"]["prose_catalogue_sha256"] == prose_catalogue_digest()
    assert (
        package["evidence"][0]["contract_binding"]["prose_contract_version"]
        == PROSE_CONTRACT_VERSION
    )
    assert validate_package(package)["structural_checks"] == "passed"


def test_v12_package_rejects_rehashed_printed_text_and_provenance_tampering(tmp_path):
    from copy import deepcopy

    from Backend.Core.france.pipeline import (
        digest,
        generate_assessment,
        validate_package,
    )

    index = tmp_path / "sources.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=ClosedProseFrenchClient(),
        seed=270100,
        checkpoint=tmp_path / "checkpoint.json",
        contract_graph_tree=True,
    )
    for mutate in (
        lambda changed: changed["exercises"][0].update(
            title="A et F sont directement reliés."
        ),
        lambda changed: changed["exercises"][0].update(
            context="Le graphe est complet."
        ),
        lambda changed: changed["exercises"][0]["questions"][0].update(
            prompt="A et F sont directement reliés."
        ),
        lambda changed: changed["exercises"][0]["questions"][0].update(
            answer="Le poids est 999."
        ),
        lambda changed: changed["exercises"][0]["questions"][1]["marking"][0].update(
            criterion="La clé 999 existe."
        ),
        lambda changed: changed["exercises"][0]["questions"][1]["marking"][0].update(
            points="0.75"
        ),
        lambda changed: changed["exercises"][0]["materials"][0]["edges"][0].__setitem__(
            2, 999
        ),
        lambda changed: changed["exercises"][0]["materials"][1]["rows"][0].__setitem__(
            0, "999"
        ),
    ):
        changed = deepcopy(package)
        mutate(changed)
        changed["content_sha256"] = digest(changed["exercises"])
        changed["evidence"][0]["exercise_sha256"] = digest(changed["exercises"][0])
        with pytest.raises(ValueError):
            validate_package(changed)
    for field in ("prose_contract_version", "prose_catalogue_sha256"):
        changed = deepcopy(package)
        changed["identity"][field] = "0" * 64
        with pytest.raises(ValueError):
            validate_package(changed)
    changed = deepcopy(package)
    del changed["evidence"][0]["part_evidence"]
    with pytest.raises(ValueError):
        validate_package(changed)


def test_v12_targeted_choice_repair_is_replayed_and_tampering_rejected(tmp_path):
    from copy import deepcopy

    from Backend.Core.france.pipeline import generate_assessment, validate_package

    class RepairingClient(ClosedProseFrenchClient):
        def __init__(self):
            super().__init__()
            self.review_count = 0

        def generate_json(self, prompt):
            if prompt.startswith("Contrôle indépendant des capacités"):
                review = super().generate_json(prompt)
                if self.review_count == 0:
                    review["questions"][0]["aligned"] = False
                    review["questions"][0]["issues"] = ["Formulation à préciser"]
                self.review_count += 1
                return review
            if prompt.startswith("Répare une sélection verrouillée"):
                request = json.loads(prompt.split("\nDONNÉES_JSON\n", 1)[1])
                replacement = dict(request["question"])
                replacement["question_form_id"] = "1a-q2"
                return replacement
            return super().generate_json(prompt)

    index = tmp_path / "sources.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=RepairingClient(),
        seed=270100,
        checkpoint=tmp_path / "checkpoint.json",
        contract_graph_tree=True,
    )
    repairs = package["evidence"][0]["targeted_repairs"]
    assert len(repairs) == 1
    assert repairs[0]["question_id"] == "1a"
    assert validate_package(package)["structural_checks"] == "passed"
    changed = deepcopy(package)
    changed["evidence"][0]["targeted_repairs"][0]["replacement"]["question_form_id"] = (
        "1a-q1"
    )
    with pytest.raises(ValueError):
        validate_package(changed)


def test_v11_contract_route_generates_and_replays_three_exercises(tmp_path):
    from Backend.Core.france.pipeline import generate_assessment, validate_package

    index = tmp_path / "sources.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=ContractFrenchClient(),
        seed=270100,
        checkpoint=tmp_path / "checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v11",
    )
    assert package["identity"]["prompt_version"] == "fr-nsi-written-2027-v11"
    assert len(package["exercises"]) == 3
    assert len(package["evidence"][0]["part_evidence"]["parts"]) == 3
    assert all(
        item["state"] == "passed" for item in package["evidence"][0]["deterministic"]
    )
    assert validate_package(package)["structural_checks"] == "passed"
    assert package["status"] == "unreviewed_draft"


def test_v11_contract_checkpoint_resumes_only_missing_parts(tmp_path):
    from Backend.Core.france.pipeline import generate_assessment

    index = tmp_path / "sources.sqlite"
    make_index(index)
    checkpoint = tmp_path / "checkpoint.json"
    client = ContractFrenchClient(stop_on_part="B")
    with pytest.raises(KeyboardInterrupt):
        generate_assessment(
            index_path=index,
            client=client,
            seed=270100,
            checkpoint=checkpoint,
            contract_graph_tree=True,
            contract_authoring_version="v11",
        )
    assert client.part_calls == ["A"]
    state = json.loads(checkpoint.read_text())
    assert state["accepted"] == {}
    assert state["failed_attempts"][0]["cancelled"] is True
    client.stop_on_part = None
    package = generate_assessment(
        index_path=index,
        client=client,
        seed=270100,
        checkpoint=checkpoint,
        contract_graph_tree=True,
        contract_authoring_version="v11",
    )
    assert client.part_calls == ["A", "B", "C"]
    assert package["identity"]["prompt_version"] == "fr-nsi-written-2027-v11"


def test_v11_contract_package_rejects_stale_digest_and_printed_graph(tmp_path):
    from copy import deepcopy

    from Backend.Core.france.pipeline import (
        digest,
        generate_assessment,
        validate_package,
    )

    index = tmp_path / "sources.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=ContractFrenchClient(),
        seed=270100,
        checkpoint=tmp_path / "checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v11",
    )
    changed = deepcopy(package)
    changed["identity"]["graph_tree_contract_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="contrat"):
        validate_package(changed)
    changed = deepcopy(package)
    changed["exercises"][0]["materials"][0]["edges"][0][2] += 1
    changed["content_sha256"] = digest(changed["exercises"])
    changed["evidence"][0]["exercise_sha256"] = digest(changed["exercises"][0])
    with pytest.raises(ValueError):
        validate_package(changed)


def make_legacy_structural_package(tmp_path, monkeypatch):
    """Generate fixture content against the actual pre-v7 question blueprint."""
    from copy import deepcopy

    from Backend.Core.france import pipeline

    index = tmp_path / "sources.sqlite"
    make_index(index)
    original = pipeline._tasks_for_seed
    legacy = pipeline._legacy_tasks_for_seed(5)
    current = original(5)
    authoring_tasks = deepcopy(legacy)
    for old_task, new_task in zip(authoring_tasks, current, strict=True):
        for field in ("archetype_id", "scenario_brief", "part_briefs"):
            old_task[field] = new_task[field]
    monkeypatch.setattr(pipeline, "_tasks_for_seed", lambda seed: authoring_tasks)
    try:
        package = pipeline.generate_assessment(
            index_path=index,
            client=FrenchClient(),
            seed=5,
            checkpoint=tmp_path / "checkpoint.json",
        )
    finally:
        monkeypatch.setattr(pipeline, "_tasks_for_seed", original)
    package["identity"]["blueprint"] = legacy
    return package


@pytest.mark.parametrize("field", ["materials", "material_ids", "verification"])
def test_authoring_rejects_missing_required_raw_fields(tmp_path, field):
    from Backend.Core.france.pipeline import generate_assessment

    class OmittedFieldClient(FrenchClient):
        def generate_json(self, prompt):
            result = super().generate_json(prompt)
            if prompt.startswith("Rédige directement en français académique"):
                if field == "materials":
                    del result["materials"]
                else:
                    del result["questions"][0][field]
            return result

    index = tmp_path / "sources.sqlite"
    make_index(index)
    checkpoint = tmp_path / "checkpoint.json"
    with pytest.raises(ValueError, match="Exercice 1 refusé"):
        generate_assessment(
            index_path=index,
            client=OmittedFieldClient(),
            seed=5,
            checkpoint=checkpoint,
        )
    state = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert len(state["failed_attempts"]) == 3
    assert all(field in item["error"] for item in state["failed_attempts"])


def test_v6_package_rechecks_authoring_fields_in_raw_evidence(tmp_path):
    from copy import deepcopy

    from Backend.Core.france.pipeline import generate_assessment, validate_package

    index = tmp_path / "sources.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=FrenchClient(),
        seed=5,
        checkpoint=tmp_path / "checkpoint.json",
    )
    changed = deepcopy(package)
    del changed["evidence"][0]["candidate"]["questions"][0]["verification"]
    from Backend.Core.france.pipeline import digest

    changed["evidence"][0]["candidate_sha256"] = digest(
        changed["evidence"][0]["candidate"]
    )
    with pytest.raises(ValueError, match="verification"):
        validate_package(changed)


def test_missing_reference_never_calls_model(tmp_path):
    from Backend.Core.france.pipeline import generate_assessment

    index_path = tmp_path / "empty.sqlite"
    with ReferenceIndex(index_path):
        pass
    client = FrenchClient()
    with pytest.raises(ValueError):
        generate_assessment(
            index_path=index_path,
            client=client,
            seed=5,
            checkpoint=tmp_path / "checkpoint.json",
        )
    assert client.calls == 0


def test_generation_is_french_scoped_and_resume_does_not_repeat_model_work(tmp_path):
    from Backend.Core.france.pipeline import generate_assessment, validate_package

    index = tmp_path / "sources.sqlite"
    make_index(index)
    index_digest = sha256(index.read_bytes()).hexdigest()
    client = FrenchClient()
    package = generate_assessment(
        index_path=index, client=client, seed=5, checkpoint=tmp_path / "checkpoint.json"
    )
    assert sha256(index.read_bytes()).hexdigest() == index_digest
    assert len(package["exercises"]) == 3
    assert package["education_context"] == asdict(NSI_CONTEXT)
    assert package["teacher_review"]["state"] == "not_run"
    assert package["empirical_calibration"]["state"] == "not_run"
    assert package["status"] == "unreviewed_draft"
    assert [item["target_points"] for item in package["exercises"]] != [
        "6",
        "6",
        "6",
    ]
    assert sum(
        Decimal(item["target_points"]) for item in package["exercises"]
    ) == Decimal("18")
    assert all(item["materials"] for item in package["exercises"])
    assert all(
        any(question["material_ids"] for question in item["questions"])
        for item in package["exercises"]
    )
    assert all(
        set(task["required_curriculum_codes"])
        <= {
            code
            for question in exercise["questions"]
            for code in question["curriculum_codes"]
        }
        for task, exercise in zip(
            package["identity"]["blueprint"], package["exercises"], strict=True
        )
    )
    assert package["language_rubric"]["allocation_status"] == (
        "indicative_product_profile"
    )
    validate_package(package)
    assert client.calls == 12
    again = generate_assessment(
        index_path=index, client=client, seed=5, checkpoint=tmp_path / "checkpoint.json"
    )
    assert again == package
    assert client.calls == 12
    package["exercises"][0]["questions"][0]["answer"] = "changed"
    with pytest.raises(ValueError, match="hash"):
        validate_package(package)


def test_question_alignment_rejects_semantic_mismatch_despite_correct_metadata(
    tmp_path,
):
    from Backend.Core.france.pipeline import generate_assessment

    class MisalignedClient(FrenchClient):
        def generate_json(self, prompt):
            response = super().generate_json(prompt)
            if prompt.startswith("Contrôle indépendant des capacités"):
                response["questions"][0]["aligned"] = False
                response["questions"][0]["issues"] = [
                    "La consigne porte sur le routage, pas sur la représentation d'un graphe."
                ]
            return response

    index = tmp_path / "sources.sqlite"
    make_index(index)
    checkpoint = tmp_path / "checkpoint.json"
    with pytest.raises(ValueError, match="refusé"):
        generate_assessment(
            index_path=index,
            client=MisalignedClient(),
            seed=5,
            checkpoint=checkpoint,
        )
    state = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert state["accepted"] == {}
    assert len(state["failed_attempts"]) == 3
    assert all("question_alignment" in item for item in state["failed_attempts"])


def test_question_alignment_rejects_missing_item_even_with_positive_exercise_review(
    tmp_path,
):
    from Backend.Core.france.pipeline import generate_assessment

    class MissingItemClient(FrenchClient):
        def generate_json(self, prompt):
            response = super().generate_json(prompt)
            if prompt.startswith("Contrôle indépendant des capacités"):
                response["questions"].pop()
            return response

    index = tmp_path / "sources.sqlite"
    make_index(index)
    with pytest.raises(ValueError, match="refusé"):
        generate_assessment(
            index_path=index,
            client=MissingItemClient(),
            seed=5,
            checkpoint=tmp_path / "checkpoint.json",
        )


def test_question_alignment_evidence_is_required_on_replay(tmp_path):
    from copy import deepcopy

    from Backend.Core.france.pipeline import generate_assessment, validate_package

    index = tmp_path / "sources.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=FrenchClient(),
        seed=5,
        checkpoint=tmp_path / "checkpoint.json",
    )
    missing = deepcopy(package)
    del missing["evidence"][0]["question_alignment"]
    with pytest.raises(ValueError, match="alignement"):
        validate_package(missing)

    contradicted = deepcopy(package)
    contradicted["evidence"][0]["question_alignment"]["review"]["questions"][0][
        "objective_code"
    ] = "ASR-ROUTAGE"
    with pytest.raises(ValueError, match="alignement"):
        validate_package(contradicted)


def test_alignment_reviewer_never_receives_author_answer_or_marking(tmp_path):
    from Backend.Core.france.pipeline import generate_assessment

    class InspectingClient(FrenchClient):
        def generate_json(self, prompt):
            if prompt.startswith("Contrôle indépendant des capacités"):
                request = json.loads(prompt.split("\nDONNÉES_JSON\n", 1)[1])
                for question in request["exercise"]["questions"]:
                    assert "answer" not in question
                    assert "marking" not in question
                    assert "verification" not in question
            return super().generate_json(prompt)

    index = tmp_path / "sources.sqlite"
    make_index(index)
    generate_assessment(
        index_path=index,
        client=InspectingClient(),
        seed=5,
        checkpoint=tmp_path / "checkpoint.json",
    )


def test_failed_question_is_repaired_without_reauthoring_accepted_peers(tmp_path):
    from Backend.Core.france.pipeline import generate_assessment, validate_package

    class RepairingClient(FrenchClient):
        def __init__(self):
            super().__init__()
            self.repairs = 0
            self.alignment_views = []

        def generate_json(self, prompt):
            if prompt.startswith("Répare uniquement la question"):
                self.calls += 1
                self.repairs += 1
                request = json.loads(prompt.split("\nDONNÉES_JSON\n", 1)[1])
                result = dict(request["question"])
                result["prompt"] = "Version corrigée : " + result["prompt"]
                result["answer"] = "Réponse recalculée pour la version corrigée."
                return result
            response = super().generate_json(prompt)
            if prompt.startswith("Contrôle indépendant des capacités"):
                request = json.loads(prompt.split("\nDONNÉES_JSON\n", 1)[1])
                self.alignment_views.append(request["exercise"])
                if (
                    request["exercise"]["id"] == "1"
                    and "Version corrigée"
                    not in request["exercise"]["questions"][1]["prompt"]
                ):
                    response["questions"][1]["aligned"] = False
                    response["questions"][1]["issues"] = [
                        "La première formulation ne permet pas d'établir la capacité."
                    ]
            return response

    index = tmp_path / "sources.sqlite"
    make_index(index)
    client = RepairingClient()
    package = generate_assessment(
        index_path=index,
        client=client,
        seed=5,
        checkpoint=tmp_path / "checkpoint.json",
    )
    evidence = package["evidence"][0]
    assert client.repairs == 1
    assert len(evidence["targeted_repairs"]) == 1
    start = evidence["initial_candidate"]
    final = evidence["candidate"]
    assert start["questions"][1] != final["questions"][1]
    assert start["questions"][:1] == final["questions"][:1]
    assert start["questions"][2:] == final["questions"][2:]
    assert "Version corrigée" in package["exercises"][0]["questions"][1]["prompt"]
    assert len([view for view in client.alignment_views if view["id"] == "1"]) == 2
    validate_package(package)

    tampered = json.loads(json.dumps(package))
    tampered["evidence"][0]["targeted_repairs"][0]["replacement"]["prompt"] = (
        "Une autre consigne modifiée après génération."
    )
    with pytest.raises(ValueError, match="réparation"):
        validate_package(tampered)


@pytest.mark.parametrize("invalid_credit", ["0", "999"])
def test_invalid_marking_is_repaired_without_changing_the_question(
    tmp_path, invalid_credit
):
    from copy import deepcopy

    from Backend.Core.france.pipeline import (
        _replay_targeted_repairs,
        digest,
        generate_assessment,
        validate_package,
    )

    class MarkingClient(FrenchClient):
        def __init__(self):
            super().__init__()
            self.repairs = 0

        def generate_json(self, prompt):
            if prompt.startswith("Répare uniquement le barème"):
                self.repairs += 1
                request = json.loads(prompt.split("\nDONNÉES_JSON\n", 1)[1])
                repaired = dict(request["question"])
                repaired["marking"] = [
                    {
                        "points": request["planned"]["points"],
                        "criterion": "Résultat exact et justification correspondante.",
                    }
                ]
                return repaired
            result = super().generate_json(prompt)
            if (
                prompt.startswith("Rédige directement en français académique")
                and result["id"] == "1"
            ):
                result["questions"][0]["marking"][0]["points"] = invalid_credit
            return result

    index = tmp_path / "sources.sqlite"
    make_index(index)
    client = MarkingClient()
    package = generate_assessment(
        index_path=index,
        client=client,
        seed=5,
        checkpoint=tmp_path / "checkpoint.json",
    )
    evidence = package["evidence"][0]
    assert client.repairs == 1
    assert len(evidence["targeted_repairs"]) == 1
    original = evidence["initial_candidate"]["questions"][0]
    repaired = evidence["candidate"]["questions"][0]
    assert {key: value for key, value in original.items() if key != "marking"} == {
        key: value for key, value in repaired.items() if key != "marking"
    }
    assert (
        evidence["candidate"]["questions"][1:]
        == evidence["initial_candidate"]["questions"][1:]
    )
    validate_package(package)

    tampered = deepcopy(evidence)
    changed = deepcopy(tampered["candidate"])
    changed["questions"][0]["prompt"] = "Une consigne différente mais au même barème."
    tampered["targeted_repairs"][0]["replacement"] = changed["questions"][0]
    tampered["targeted_repairs"][0]["after_sha256"] = digest(changed)
    with pytest.raises(ValueError, match="barème"):
        _replay_targeted_repairs(tampered, changed, package["identity"]["blueprint"][0])
    fabricated = deepcopy(evidence)
    fabricated["initial_candidate"]["questions"][0]["marking"] = deepcopy(
        repaired["marking"]
    )
    fabricated["targeted_repairs"][0]["before_sha256"] = digest(
        fabricated["initial_candidate"]
    )
    with pytest.raises(ValueError, match="barème"):
        _replay_targeted_repairs(
            fabricated, evidence["candidate"], package["identity"]["blueprint"][0]
        )


def test_marking_repair_cannot_rewrite_the_question(tmp_path):
    from Backend.Core.france.pipeline import generate_assessment

    class RewritingClient(FrenchClient):
        def generate_json(self, prompt):
            if prompt.startswith("Répare uniquement le barème"):
                request = json.loads(prompt.split("\nDONNÉES_JSON\n", 1)[1])
                repaired = dict(request["question"])
                repaired["prompt"] = (
                    "Une autre consigne, qui change la tâche du candidat."
                )
                repaired["marking"] = [
                    {
                        "points": request["planned"]["points"],
                        "criterion": "Justification de la réponse attendue.",
                    }
                ]
                return repaired
            result = super().generate_json(prompt)
            if (
                prompt.startswith("Rédige directement en français académique")
                and result["id"] == "1"
            ):
                result["questions"][0]["marking"][0]["points"] = "0"
            return result

    index = tmp_path / "sources.sqlite"
    make_index(index)
    checkpoint = tmp_path / "checkpoint.json"
    with pytest.raises(ValueError, match="Exercice 1 refusé"):
        generate_assessment(
            index_path=index,
            client=RewritingClient(),
            seed=5,
            checkpoint=checkpoint,
        )
    failed = json.loads(checkpoint.read_text())["failed_attempts"]
    assert len(failed) == 3
    assert all("changé la question" in item["error"] for item in failed)
    assert all(item["repair_responses"] for item in failed)


def test_invalid_marking_repair_is_bounded_and_never_published(tmp_path):
    from Backend.Core.france.pipeline import generate_assessment

    class UnhelpfulClient(FrenchClient):
        def __init__(self):
            super().__init__()
            self.repairs = 0

        def generate_json(self, prompt):
            if prompt.startswith("Répare uniquement le barème"):
                self.repairs += 1
                request = json.loads(prompt.split("\nDONNÉES_JSON\n", 1)[1])
                return request["question"]
            result = super().generate_json(prompt)
            if (
                prompt.startswith("Rédige directement en français académique")
                and result["id"] == "1"
            ):
                result["questions"][0]["marking"][0]["points"] = "0"
            return result

    index = tmp_path / "sources.sqlite"
    make_index(index)
    checkpoint = tmp_path / "checkpoint.json"
    client = UnhelpfulClient()
    with pytest.raises(ValueError, match="Exercice 1 refusé"):
        generate_assessment(
            index_path=index,
            client=client,
            seed=5,
            checkpoint=checkpoint,
        )
    saved = json.loads(checkpoint.read_text())
    assert client.repairs == 6
    assert saved["accepted"] == {}
    assert len(saved["failed_attempts"]) == 3
    assert all(len(item["targeted_repairs"]) == 2 for item in saved["failed_attempts"])


def test_targeted_repair_is_bounded_and_preserves_failed_drafts(tmp_path):
    from Backend.Core.france.pipeline import generate_assessment

    class PersistentMismatchClient(FrenchClient):
        def __init__(self):
            super().__init__()
            self.repairs = 0

        def generate_json(self, prompt):
            if prompt.startswith("Répare uniquement la question"):
                self.calls += 1
                self.repairs += 1
                request = json.loads(prompt.split("\nDONNÉES_JSON\n", 1)[1])
                result = dict(request["question"])
                result["prompt"] = (
                    f"Nouvelle version {self.repairs} : " + result["prompt"]
                )
                return result
            response = super().generate_json(prompt)
            if prompt.startswith("Contrôle indépendant des capacités"):
                response["questions"][1]["aligned"] = False
                response["questions"][1]["issues"] = ["Objectif non évalué."]
            return response

    index = tmp_path / "sources.sqlite"
    make_index(index)
    checkpoint = tmp_path / "checkpoint.json"
    client = PersistentMismatchClient()
    with pytest.raises(ValueError, match="refusé"):
        generate_assessment(
            index_path=index, client=client, seed=5, checkpoint=checkpoint
        )
    state = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert client.repairs == 6
    assert len(state["failed_attempts"]) == 3
    assert all(len(item["targeted_repairs"]) == 2 for item in state["failed_attempts"])
    assert state["accepted"] == {}


@pytest.mark.parametrize("cancel_type", [KeyboardInterrupt, InterruptedError])
def test_cancellation_during_repair_keeps_evidence_and_no_partial_acceptance(
    tmp_path, cancel_type
):
    from Backend.Core.france.pipeline import generate_assessment

    class InterruptingClient(FrenchClient):
        def generate_json(self, prompt):
            if prompt.startswith("Répare uniquement la question"):
                raise cancel_type("Création annulée")
            response = super().generate_json(prompt)
            if prompt.startswith("Contrôle indépendant des capacités"):
                response["questions"][0]["aligned"] = False
                response["questions"][0]["issues"] = ["Question hors capacité."]
            return response

    index = tmp_path / "sources.sqlite"
    make_index(index)
    checkpoint = tmp_path / "checkpoint.json"
    with pytest.raises(cancel_type):
        generate_assessment(
            index_path=index,
            client=InterruptingClient(),
            seed=5,
            checkpoint=checkpoint,
        )
    state = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert state["accepted"] == {}
    assert state["failed_attempts"][0]["cancelled"] is True
    assert state["failed_attempts"][0]["candidate"]["questions"]

    resumed = generate_assessment(
        index_path=index,
        client=FrenchClient(),
        seed=5,
        checkpoint=checkpoint,
    )
    assert len(resumed["exercises"]) == 3
    assert json.loads(checkpoint.read_text())["failed_attempts"][0]["cancelled"]


def test_invalid_repair_response_is_recorded_before_rejection(tmp_path):
    from Backend.Core.france.pipeline import generate_assessment

    class WrongIdentityClient(FrenchClient):
        def generate_json(self, prompt):
            if prompt.startswith("Répare uniquement la question"):
                self.calls += 1
                request = json.loads(prompt.split("\nDONNÉES_JSON\n", 1)[1])
                return {**request["question"], "id": "9z"}
            response = super().generate_json(prompt)
            if prompt.startswith("Contrôle indépendant des capacités"):
                response["questions"][0]["aligned"] = False
                response["questions"][0]["issues"] = ["Capacité non évaluée."]
            return response

    index = tmp_path / "sources.sqlite"
    make_index(index)
    checkpoint = tmp_path / "checkpoint.json"
    with pytest.raises(ValueError, match="refusé"):
        generate_assessment(
            index_path=index,
            client=WrongIdentityClient(),
            seed=5,
            checkpoint=checkpoint,
        )
    failed = json.loads(checkpoint.read_text())["failed_attempts"]
    assert len(failed) == 3
    assert all(item["repair_responses"][0]["response"]["id"] == "9z" for item in failed)


def test_repair_invalidates_downstream_solution_dependencies(tmp_path):
    from Backend.Core.france.pipeline import generate_assessment

    class DependencyClient(FrenchClient):
        def generate_json(self, prompt):
            if prompt.startswith("Répare uniquement la question"):
                self.calls += 1
                request = json.loads(prompt.split("\nDONNÉES_JSON\n", 1)[1])
                return {
                    **request["question"],
                    "prompt": "Version corrigée : " + request["question"]["prompt"],
                }
            response = super().generate_json(prompt)
            if prompt.startswith("Contrôle indépendant des capacités"):
                request = json.loads(prompt.split("\nDONNÉES_JSON\n", 1)[1])
                if (
                    request["exercise"]["id"] == "1"
                    and "Version corrigée"
                    not in request["exercise"]["questions"][0]["prompt"]
                ):
                    response["questions"][0]["aligned"] = False
                    response["questions"][0]["issues"] = ["Capacité non évaluée."]
            if prompt.startswith("Résous indépendamment"):
                request = json.loads(prompt.split("\n", 1)[1])
                if request["id"] == "1" and request["questions"][0][
                    "prompt"
                ].startswith("Version corrigée"):
                    response["issues"] = [
                        "La réponse de 1b dépend de l'ancien résultat de 1a."
                    ]
            return response

    index = tmp_path / "sources.sqlite"
    make_index(index)
    checkpoint = tmp_path / "checkpoint.json"
    with pytest.raises(ValueError, match="refusé"):
        generate_assessment(
            index_path=index,
            client=DependencyClient(),
            seed=5,
            checkpoint=checkpoint,
        )
    state = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert state["accepted"] == {}
    assert len(state["failed_attempts"]) == 3
    assert all(item["targeted_repairs"] for item in state["failed_attempts"])
    assert all(
        item["independent_solution"]["issues"] for item in state["failed_attempts"]
    )


def test_failed_review_keeps_attempt_evidence_and_never_accepts(tmp_path):
    from Backend.Core.france.pipeline import generate_assessment

    index = tmp_path / "sources.sqlite"
    make_index(index)
    checkpoint = tmp_path / "checkpoint.json"
    with pytest.raises(ValueError, match="refusé"):
        generate_assessment(
            index_path=index,
            client=FrenchClient(reject=True),
            seed=5,
            checkpoint=checkpoint,
        )
    saved = json.loads(checkpoint.read_text())
    assert len(saved["failed_attempts"]) == 3
    assert saved["accepted"] == {}


def test_generation_rejects_relational_drift_from_the_question_blueprint(tmp_path):
    from Backend.Core.france.pipeline import generate_assessment

    class DriftingBlueprintClient(FrenchClient):
        def generate_json(self, prompt):
            result = super().generate_json(prompt)
            if prompt.startswith("Rédige directement en français académique"):
                first, second = result["questions"][:2]
                first["points"], second["points"] = second["points"], first["points"]
                first["marking"][0]["points"] = first["points"]
                second["marking"][0]["points"] = second["points"]
            return result

    index = tmp_path / "sources.sqlite"
    make_index(index)

    with pytest.raises(ValueError, match="plan"):
        generate_assessment(
            index_path=index,
            client=DriftingBlueprintClient(),
            seed=5,
            checkpoint=tmp_path / "checkpoint.json",
        )


def test_checkpoint_rejects_changed_model_identity(tmp_path):
    from Backend.Core.france.pipeline import generate_assessment

    index = tmp_path / "sources.sqlite"
    make_index(index)
    client = FrenchClient()
    checkpoint = tmp_path / "checkpoint.json"
    generate_assessment(index_path=index, client=client, seed=5, checkpoint=checkpoint)
    client.model_digest = "changed"
    with pytest.raises(ValueError, match="identité"):
        generate_assessment(
            index_path=index, client=client, seed=5, checkpoint=checkpoint
        )


def test_checkpoint_rejects_changed_source_identity(tmp_path, monkeypatch):
    from Backend.Core.france import pipeline

    index = tmp_path / "sources.sqlite"
    make_index(index)
    checkpoint = tmp_path / "checkpoint.json"
    pipeline.generate_assessment(
        index_path=index, client=FrenchClient(), seed=5, checkpoint=checkpoint
    )
    monkeypatch.setattr(pipeline, "implementation_identity", lambda: "changed")
    with pytest.raises(ValueError, match="identité"):
        pipeline.generate_assessment(
            index_path=index, client=FrenchClient(), seed=5, checkpoint=checkpoint
        )


def test_common_package_reader_dispatches_french_without_uk_policy(tmp_path):
    from Backend.Core.assessment_package import load_assessment_package
    from Backend.Core.france.pipeline import generate_assessment

    index = tmp_path / "sources.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=FrenchClient(),
        seed=5,
        checkpoint=tmp_path / "checkpoint.json",
    )
    path = tmp_path / "assessment.json"
    path.write_text(json.dumps(package))
    assert load_assessment_package(path) == package


def test_package_cannot_change_reference_or_claim_teacher_approval(tmp_path):
    from copy import deepcopy

    from Backend.Core.france.pipeline import generate_assessment, validate_package

    index = tmp_path / "sources.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=FrenchClient(),
        seed=7,
        checkpoint=tmp_path / "checkpoint.json",
    )
    changed = deepcopy(package)
    changed["evidence"][0]["references"][0]["text"] = "Unrelated source"
    with pytest.raises(ValueError, match="références"):
        validate_package(changed)
    changed = deepcopy(package)
    changed["teacher_review"]["state"] = "passed"
    with pytest.raises(ValueError, match="enseignant"):
        validate_package(changed)

    for field in ("empirical_calibration", "visual_calibration"):
        changed = deepcopy(package)
        changed[field] = {"state": "passed"}
        with pytest.raises(ValueError, match="calibration"):
            validate_package(changed)
    changed = deepcopy(package)
    changed["evidence"][0]["originality"] = {"state": "passed"}
    with pytest.raises(ValueError, match="originalité"):
        validate_package(changed)
    changed = deepcopy(package)
    changed["language_rubric"]["indicative_points"]["satisfaisant"] = "2"
    with pytest.raises(ValueError, match="langue"):
        validate_package(changed)


def test_previous_generation_text_is_identity_bound_and_rejected_when_reused(tmp_path):
    from Backend.Core.france.pipeline import generate_assessment

    index = tmp_path / "sources.sqlite"
    make_index(index)
    client = FrenchClient()
    first = generate_assessment(
        index_path=index,
        client=client,
        seed=5,
        checkpoint=tmp_path / "first.json",
    )
    exercise = first["exercises"][0]
    previous_text = "\n".join(
        [
            exercise["title"],
            exercise["context"],
            *(question["prompt"] for question in exercise["questions"]),
        ]
    )
    with pytest.raises(ValueError, match="génération précédente"):
        generate_assessment(
            index_path=index,
            client=FrenchClient(),
            seed=5,
            checkpoint=tmp_path / "second.json",
            previous_texts=[previous_text],
        )


def test_only_explicit_material_ids_are_recovered_from_omitted_links():
    from Backend.Core.france.pipeline import bind_explicit_material_ids

    raw = {
        "materials": [{"id": "map_ville"}, {"id": "road_network"}],
        "questions": [
            {"id": "1a", "prompt": "Analyser le graphe `map_ville`."},
            {"id": "1b", "prompt": "Comparer la variable map_ville_2."},
            {"id": "1c", "prompt": "Analyser le graphe G."},
            {"id": "1d", "prompt": "Utiliser road_network.", "material_ids": []},
        ],
    }
    bound, evidence = bind_explicit_material_ids(raw)

    assert bound["questions"][0]["material_ids"] == ["map_ville"]
    assert "material_ids" not in bound["questions"][1]
    assert "material_ids" not in bound["questions"][2]
    assert bound["questions"][3]["material_ids"] == ["road_network"]
    assert evidence == [
        {"question_id": "1a", "material_ids": ["map_ville"]},
        {"question_id": "1d", "material_ids": ["road_network"]},
    ]
    assert "material_ids" not in raw["questions"][0]


def test_empty_material_links_recover_only_exact_declared_identifiers():
    from Backend.Core.france.pipeline import bind_explicit_material_ids

    raw = {
        "materials": [{"id": "support_1"}, {"id": "support_2"}],
        "questions": [
            {"id": "1a", "prompt": "Lire `support_1`.", "material_ids": []},
            {
                "id": "1b",
                "prompt": "Comparer support_1 et support_2.",
                "material_ids": [],
            },
            {"id": "1c", "prompt": "Lire le tableau.", "material_ids": []},
        ],
    }

    bound, evidence = bind_explicit_material_ids(raw)

    assert [item["material_ids"] for item in bound["questions"]] == [
        ["support_1"],
        ["support_1", "support_2"],
        [],
    ]
    assert evidence == [
        {"question_id": "1a", "material_ids": ["support_1"]},
        {"question_id": "1b", "material_ids": ["support_1", "support_2"]},
    ]
    assert raw["questions"][0]["material_ids"] == []


def test_material_link_conflicting_with_explicit_prompt_identifier_is_rejected():
    from Backend.Core.france.pipeline import bind_explicit_material_ids

    raw = {
        "materials": [{"id": "support_1"}, {"id": "support_2"}],
        "questions": [
            {"id": "1a", "prompt": "Lire `support_1`.", "material_ids": ["support_2"]}
        ],
    }
    with pytest.raises(ValueError, match=r"liaison|identifiant"):
        bind_explicit_material_ids(raw)


def test_unknown_explicit_figure_identifier_is_not_bound_to_other_material():
    from Backend.Core.france.pipeline import bind_explicit_material_ids

    raw = {
        "materials": [{"id": "support_1"}],
        "questions": [
            {
                "id": "1a",
                "prompt": "Lire le graphe `unknown_graph` pour trouver un chemin.",
                "material_ids": [],
            }
        ],
    }
    with pytest.raises(ValueError, match="Identifiant"):
        bind_explicit_material_ids(raw)


@pytest.mark.parametrize(
    "reference",
    (
        "les figures `support_1` et `unknown_graph`",
        "les figures «support_1» et «unknown_graph»",
        "les figures support_1 et unknown_graph",
    ),
)
def test_one_known_figure_does_not_hide_unknown_coordinated_figure(reference):
    from Backend.Core.france.pipeline import bind_explicit_material_ids

    raw = {
        "materials": [{"id": "support_1"}],
        "questions": [
            {
                "id": "1a",
                "prompt": f"Comparer {reference} pour répondre au besoin.",
                "material_ids": [],
            }
        ],
    }
    with pytest.raises(ValueError, match="Identifiant"):
        bind_explicit_material_ids(raw)


def test_duplicate_declared_material_identifier_is_rejected_before_binding():
    from Backend.Core.france.pipeline import bind_explicit_material_ids

    raw = {
        "materials": [{"id": "support"}, {"id": "support"}],
        "questions": [{"id": "1a", "prompt": "Lire `support`.", "material_ids": []}],
    }
    with pytest.raises(ValueError, match="dupliqu"):
        bind_explicit_material_ids(raw)


def test_unknown_second_figure_rejected_during_generation_and_package_replay(tmp_path):
    from copy import deepcopy

    from Backend.Core.france.pipeline import (
        digest,
        generate_assessment,
        validate_package,
    )

    class UnknownFigureClient(FrenchClient):
        def generate_json(self, prompt):
            result = super().generate_json(prompt)
            if prompt.startswith("Rédige directement en français académique"):
                result["questions"][0]["prompt"] = (
                    "Comparer les figures `support` et `unknown_graph`."
                )
                result["questions"][0]["material_ids"] = []
            return result

    index = tmp_path / "sources.sqlite"
    make_index(index)
    with pytest.raises(ValueError, match="Identifiant de figure inconnu"):
        generate_assessment(
            index_path=index,
            client=UnknownFigureClient(),
            seed=5,
            checkpoint=tmp_path / "rejected.json",
        )

    package = generate_assessment(
        index_path=index,
        client=FrenchClient(),
        seed=5,
        checkpoint=tmp_path / "accepted.json",
    )
    changed = deepcopy(package)
    candidate = changed["evidence"][0]["candidate"]
    candidate["questions"][0]["prompt"] = (
        "Comparer les figures `support` et `unknown_graph`."
    )
    candidate["questions"][0]["material_ids"] = []
    changed["evidence"][0]["candidate_sha256"] = digest(candidate)
    with pytest.raises(ValueError, match="Identifiant de figure inconnu"):
        validate_package(changed)


def test_planned_question_rejects_authored_metadata_drift_without_mutating_raw():
    from copy import deepcopy

    from Backend.Core.france.pipeline import assemble_planned_question

    plan = {
        "id": "1a",
        "points": "0.5",
        "estimated_minutes": 6,
        "operation": "apply",
        "difficulty": 2,
        "required_curriculum_code": "SD-GRAPHE",
    }
    authored = {
        "id": "1a",
        "prompt": "Lire la valeur de l'arête AB dans le graphe fourni.",
        "points": "0.5",
        "answer": "La valeur est 2.",
        "marking": [{"points": "0.5", "criterion": "Valeur correcte."}],
        "material_ids": [],
        "curriculum_codes": ["SD-GRAPHE"],
        "operation": "apply",
        "difficulty": 2,
        "estimated_minutes": 6,
        "verification": {"kind": "human"},
    }
    original = deepcopy(authored)
    question = assemble_planned_question(plan, authored)
    assert question.id == "1a" and question.points == "0.5"
    assert authored == original
    for field, changed_value in (
        ("id", "1b"),
        ("points", "1"),
        ("operation", "recall"),
        ("difficulty", 4),
    ):
        drifted = deepcopy(authored)
        drifted[field] = changed_value
        with pytest.raises(ValueError, match="plan"):
            assemble_planned_question(plan, drifted)


def test_planned_question_accepts_equivalent_exact_decimal_credit():
    from Backend.Core.france.pipeline import assemble_planned_question

    plan = {
        "id": "1a",
        "points": "1",
        "estimated_minutes": 6,
        "operation": "apply",
        "difficulty": 2,
        "required_curriculum_code": "SD-GRAPHE",
    }
    authored = {
        "id": "1a",
        "prompt": "Lire la valeur d'une arête du graphe fourni.",
        "points": "1.0",
        "answer": "La valeur est deux.",
        "marking": [{"points": "1.0", "criterion": "Valeur correcte."}],
        "material_ids": [],
        "curriculum_codes": ["SD-GRAPHE"],
        "operation": "apply",
        "difficulty": 2,
        "estimated_minutes": 6,
        "verification": {"kind": "human"},
    }
    question = assemble_planned_question(plan, authored)
    assert question.points == "1"
    assert authored["points"] == "1.0"


def test_planned_question_cannot_inject_missing_curriculum_evidence():
    from Backend.Core.france.pipeline import assemble_planned_question

    plan = {
        "id": "1a",
        "points": "0.5",
        "estimated_minutes": 6,
        "operation": "apply",
        "difficulty": 2,
        "required_curriculum_code": "SD-GRAPHE",
    }
    authored = {
        "id": "1a",
        "prompt": "Écrire une requête SQL pour calculer les commandes reçues.",
        "points": "0.5",
        "answer": "SELECT COUNT(*) FROM commandes;",
        "marking": [{"points": "0.5", "criterion": "Requête correcte."}],
        "material_ids": [],
        "curriculum_codes": ["BDD-SQL-SELECT"],
        "operation": "apply",
        "difficulty": 2,
        "estimated_minutes": 6,
        "verification": {"kind": "human"},
    }
    with pytest.raises(ValueError, match="plan"):
        assemble_planned_question(plan, authored)


def test_current_package_records_and_replays_question_plan_assembly(tmp_path):
    from copy import deepcopy

    from Backend.Core.france.pipeline import generate_assessment, validate_package

    index = tmp_path / "sources.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=FrenchClient(),
        seed=5,
        checkpoint=tmp_path / "checkpoint.json",
    )
    assembly = package["evidence"][0]["plan_assembly"]
    assert len(assembly) == 6
    assert assembly[0]["question_id"] == "1a"
    assert all(len(item["authored_sha256"]) == 64 for item in assembly)
    validate_package(package)

    changed = deepcopy(package)
    changed["evidence"][0]["plan_assembly"][0]["authored_sha256"] = "0" * 64
    with pytest.raises(ValueError, match=r"plan|assemblage"):
        validate_package(changed)


def test_recorded_v7_package_does_not_require_new_assembly_evidence(tmp_path):
    from Backend.Core.france.pipeline import generate_assessment, validate_package

    index = tmp_path / "sources.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=FrenchClient(),
        seed=5,
        checkpoint=tmp_path / "checkpoint.json",
    )
    package["identity"]["prompt_version"] = "fr-nsi-written-2027-v7"
    package["identity"]["implementation_sha256"] = (
        "20c0a8fa1f53825d6598ae1f1af59a1cee2ddbc946c4a0fd7c49233e79e0bcdf"
    )
    for evidence in package["evidence"]:
        evidence.pop("plan_assembly", None)
    validate_package(package)


def test_v6_explicit_material_link_evidence_cannot_hide_drift(tmp_path):
    from copy import deepcopy

    from Backend.Core.france.pipeline import generate_assessment, validate_package

    class ExplicitLinkClient(FrenchClient):
        def generate_json(self, prompt):
            result = super().generate_json(prompt)
            if prompt.startswith("Rédige directement en français académique"):
                result["questions"][0]["prompt"] += " Voir `support`."
            return result

    index = tmp_path / "sources.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=ExplicitLinkClient(),
        seed=5,
        checkpoint=tmp_path / "checkpoint.json",
    )
    assert package["exercises"][0]["questions"][0]["material_ids"] == ["support"]
    assert package["evidence"][0]["material_bindings"] == []
    validate_package(package)

    changed = deepcopy(package)
    changed["evidence"][0]["material_bindings"] = [
        {"question_id": "1a", "material_ids": ["support"]}
    ]
    with pytest.raises(ValueError, match="liaison"):
        validate_package(changed)

    changed = deepcopy(package)
    changed["evidence"][0]["candidate"]["questions"][0]["prompt"] = (
        "Expliquer le graphe G et ses sommets."
    )
    with pytest.raises(ValueError, match=r"liaison|assemblage"):
        validate_package(changed)

    changed = deepcopy(package)
    changed["evidence"][0]["candidate"]["questions"][0]["material_ids"] = []
    with pytest.raises(ValueError, match=r"liaison|assemblage"):
        validate_package(changed)

    changed = deepcopy(package)
    changed["identity"]["prompt_version"] = "fr-nsi-written-2027-v4"
    for evidence in changed["evidence"]:
        del evidence["candidate"]
        del evidence["material_bindings"]
    with pytest.raises(ValueError, match="historique"):
        validate_package(changed)


def test_legacy_french_package_without_candidate_binding_evidence_remains_readable(
    tmp_path,
    monkeypatch,
):
    from Backend.Core.france.pipeline import validate_package

    package = make_legacy_structural_package(tmp_path, monkeypatch)
    package["identity"]["prompt_version"] = "fr-nsi-written-2027-v4"
    package["identity"]["implementation_sha256"] = (
        "bd1468ca74a1dbe501e5eedc306d26531fb52ff9a6271b20fc13607cbfafbfbb"
    )
    for evidence in package["evidence"]:
        del evidence["candidate"]
        del evidence["material_bindings"]
        del evidence["candidate_sha256"]
    validate_package(package)


def test_recorded_v5_package_keeps_its_candidate_evidence(tmp_path, monkeypatch):
    from copy import deepcopy

    from Backend.Core.france.pipeline import validate_package

    package = make_legacy_structural_package(tmp_path, monkeypatch)
    relabelled = deepcopy(package)
    relabelled["identity"]["prompt_version"] = "fr-nsi-written-2027-v5"
    with pytest.raises(ValueError, match="historique"):
        validate_package(relabelled)
    package["identity"]["prompt_version"] = "fr-nsi-written-2027-v5"
    package["identity"]["implementation_sha256"] = (
        "2e603cc84d59c48553b7c4a8e31129a3a337092b62188391f276c20125cef9a5"
    )
    validate_package(package)

    changed = deepcopy(package)
    del changed["evidence"][0]["candidate_sha256"]
    with pytest.raises(ValueError, match="liaison"):
        validate_package(changed)


def test_recorded_v6_reader_keeps_required_raw_fields(tmp_path, monkeypatch):
    from copy import deepcopy

    from Backend.Core.france.pipeline import digest, validate_package

    package = make_legacy_structural_package(tmp_path, monkeypatch)
    package["identity"]["prompt_version"] = "fr-nsi-written-2027-v6"
    package["identity"]["implementation_sha256"] = (
        "cba1b74b98c236608d983242778de8db6c3e891142e4ea635ebb0c7fd776c69d"
    )
    validate_package(package)

    changed = deepcopy(package)
    del changed["evidence"][0]["candidate"]["questions"][0]["verification"]
    changed["evidence"][0]["candidate_sha256"] = digest(
        changed["evidence"][0]["candidate"]
    )
    with pytest.raises(ValueError, match="verification"):
        validate_package(changed)


def test_package_replay_rejects_rehashed_question_blueprint_drift(tmp_path):
    from copy import deepcopy

    from Backend.Core.france.pipeline import (
        digest,
        generate_assessment,
        validate_package,
    )

    index = tmp_path / "sources.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=FrenchClient(),
        seed=5,
        checkpoint=tmp_path / "checkpoint.json",
    )
    changed = deepcopy(package)
    changed["exercises"][0]["questions"][0]["difficulty"] = 4
    changed["evidence"][0]["candidate"]["questions"][0]["difficulty"] = 4
    changed["evidence"][0]["candidate_sha256"] = digest(
        changed["evidence"][0]["candidate"]
    )
    changed["evidence"][0]["exercise_sha256"] = digest(changed["exercises"][0])
    changed["content_sha256"] = digest(changed["exercises"])
    with pytest.raises(ValueError, match="plan détaillé"):
        validate_package(changed)


@pytest.mark.parametrize(
    "unlinked_prompt",
    [
        "En utilisant le graphe G fourni, expliquer le résultat obtenu.",
        "À partir des arêtes de G, calculer la distance du trajet.",
        "Lire le graphe pour déterminer un trajet réalisable.",
    ],
)
def test_one_linked_question_cannot_hide_another_unlinked_figure_question(
    tmp_path, unlinked_prompt
):
    from Backend.Core.france.pipeline import generate_assessment

    class VagueFigureClient(FrenchClient):
        def generate_json(self, prompt):
            result = super().generate_json(prompt)
            if prompt.startswith("Rédige directement en français académique"):
                result["questions"][1]["prompt"] = unlinked_prompt
                result["questions"][1]["material_ids"] = []
            return result

    index = tmp_path / "sources.sqlite"
    make_index(index)
    with pytest.raises(ValueError, match="figure non reliée"):
        generate_assessment(
            index_path=index,
            client=VagueFigureClient(),
            seed=5,
            checkpoint=tmp_path / "checkpoint.json",
        )


def test_constructing_a_new_graph_does_not_require_link_to_supplied_graph(tmp_path):
    from Backend.Core.france.pipeline import generate_assessment

    class NewGraphClient(FrenchClient):
        def generate_json(self, prompt):
            result = super().generate_json(prompt)
            if prompt.startswith("Rédige directement en français académique"):
                result["questions"][1]["prompt"] = (
                    "Construire le graphe des dépendances de votre algorithme."
                )
                result["questions"][1]["material_ids"] = []
            return result

    index = tmp_path / "sources.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=NewGraphClient(),
        seed=5,
        checkpoint=tmp_path / "checkpoint.json",
    )
    assert package["status"] == "unreviewed_draft"


def test_unlinked_table_use_is_rejected_when_another_question_links_it(tmp_path):
    from Backend.Core.france.pipeline import generate_assessment

    class VagueTableClient(FrenchClient):
        def generate_json(self, prompt):
            result = super().generate_json(prompt)
            if prompt.startswith("Rédige directement en français académique"):
                task = json.loads(prompt.split("DONNÉES_JSON\n", 1)[1])
                if task["required_material_kind"] == "table":
                    result["questions"][1]["prompt"] = (
                        "Utiliser le tableau pour calculer la réponse."
                    )
                    result["questions"][1]["material_ids"] = []
            return result

    index = tmp_path / "sources.sqlite"
    make_index(index)
    with pytest.raises(ValueError, match="figure non reliée"):
        generate_assessment(
            index_path=index,
            client=VagueTableClient(),
            seed=5,
            checkpoint=tmp_path / "checkpoint.json",
        )


@pytest.mark.parametrize("field", ["prompt", "answer"])
def test_sql_questions_cannot_name_relations_absent_from_supplied_materials(field):
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.pipeline import require_declared_relations

    raw = FrenchClient().generate_json(
        'DONNÉES_JSON\n{"exercise_id":"2","topics":["bases-donnees","langages-programmation"],'
        '"minutes":70,"technical_points":"6","required_material_kind":"table",'
        '"question_blueprint":['
        + ",".join(
            json.dumps(
                {
                    "id": f"2{chr(97 + index)}",
                    "points": "1",
                    "estimated_minutes": minutes,
                    "operation": operation,
                    "difficulty": difficulty,
                    "required_curriculum_code": code,
                }
            )
            for index, (minutes, operation, difficulty, code) in enumerate(
                [
                    (10, "apply", 2, "BDD-ANOMALIES"),
                    (10, "analyse", 2, "BDD-SQL-SELECT"),
                    (10, "debug", 3, "BDD-SQL-SELECT"),
                    (10, "apply", 3, "BDD-SQL-MUTATION"),
                    (15, "design", 4, "LP-DEBUG"),
                    (15, "justify", 4, "LP-DEBUG"),
                ]
            )
        )
        + "]}"
    )
    raw["materials"][0]["id"] = "technicien"
    raw["questions"][0]["material_ids"] = ["technicien"]
    raw["questions"][1][field] = (
        "Écrire SELECT nom FROM technicien JOIN intervention "
        "ON technicien.id = intervention.id_tech."
    )
    raw["questions"][1]["material_ids"] = ["technicien"]
    exercise = NSIExercise.model_validate(raw)

    with pytest.raises(ValueError, match=r"relation.*absente"):
        require_declared_relations(exercise)


@pytest.mark.parametrize(
    "bad",
    [
        "Un arbre binaire de recherche : 10 est racine, 20 à gauche.",
        "Un arbre binaire de recherche : 10 est la racine; 20 est à gauche de 10.",
        "Dans cet ABR, la racine est 10 et 20 se trouve à gauche de la racine.",
    ],
)
def test_invalid_binary_search_tree_premise_is_rejected(bad):
    from Backend.Core.france.pipeline import require_consistent_tree_premises

    with pytest.raises(ValueError, match="arbre binaire de recherche"):
        require_consistent_tree_premises(bad)


def test_valid_binary_search_tree_descendant_positions_are_not_compared_to_root():
    from Backend.Core.france.pipeline import require_consistent_tree_premises

    require_consistent_tree_premises(
        "Un ABR contient les clés [10, 20, 30] "
        "(20 est racine, 10 à gauche, 30 à droite)."
    )
    require_consistent_tree_premises(
        "Un ABR : la racine est 10; 30 à droite de 10; 20 est à gauche de 30."
    )
    require_consistent_tree_premises(
        "Un ABR : 10 est la racine; 30 à droite de 10; "
        "20 à gauche d’un nœud de valeur 30."
    )


def test_live_style_invalid_tree_cannot_reach_automated_review(tmp_path):
    from Backend.Core.france.pipeline import generate_assessment

    class InvalidTreeClient(FrenchClient):
        def generate_json(self, prompt):
            result = super().generate_json(prompt)
            if prompt.startswith("Rédige directement en français académique"):
                task = json.loads(prompt.split("DONNÉES_JSON\n", 1)[1])
                if task["exercise_id"] == "1":
                    result["questions"][4]["prompt"] = (
                        "Un arbre binaire de recherche contient les clés "
                        "[10, 20, 30, 40] (10 est racine, 20 à gauche, "
                        "30 à droite). Écrire l'insertion de 25."
                    )
            return result

    index = tmp_path / "sources.sqlite"
    make_index(index)
    client = InvalidTreeClient()
    with pytest.raises(ValueError, match="Exercice 1 refusé"):
        generate_assessment(
            index_path=index,
            client=client,
            seed=5,
            checkpoint=tmp_path / "checkpoint.json",
        )
    state = json.loads((tmp_path / "checkpoint.json").read_text(encoding="utf-8"))
    assert len(state["failed_attempts"]) == 3
    assert all(
        "arbre binaire de recherche" in attempt["error"]
        for attempt in state["failed_attempts"]
    )
    assert client.calls == 3


def test_sql_relation_absent_from_printed_tables_rejects_draft(tmp_path):
    from Backend.Core.france.pipeline import generate_assessment

    class MissingRelationClient(FrenchClient):
        def generate_json(self, prompt):
            result = super().generate_json(prompt)
            if prompt.startswith("Rédige directement en français académique"):
                task = json.loads(prompt.split("DONNÉES_JSON\n", 1)[1])
                if task["exercise_id"] == "2":
                    result["questions"][1]["prompt"] = (
                        "Corriger SELECT nom FROM support JOIN intervention "
                        "ON support.id = intervention.id."
                    )
            return result

    index = tmp_path / "sources.sqlite"
    make_index(index)
    checkpoint = tmp_path / "checkpoint.json"
    with pytest.raises(ValueError, match="Exercice 2 refusé"):
        generate_assessment(
            index_path=index,
            client=MissingRelationClient(),
            seed=5,
            checkpoint=checkpoint,
        )
    state = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert list(state["accepted"]) == ["1"]
    assert all(
        "relation SQL absente" in attempt["error"]
        for attempt in state["failed_attempts"]
    )


def test_claimed_cycle_does_not_make_standard_breadth_first_search_stop_early():
    from Backend.Core.france.pipeline import require_algorithm_premises

    prompt = (
        "```python\n"
        "def parcourir_largeur(adj, start):\n"
        "    visites = []\n"
        "    file = [start]\n"
        "    while file:\n"
        "        sommet = file.pop(0)\n"
        "        if sommet not in visites:\n"
        "            visites.append(sommet)\n"
        "            file.extend(adj[sommet])\n"
        "    return visites\n"
        "```\n"
        "Le programme s'arrête prématurément si une boucle existe. "
        "Identifiez la faille logique."
    )
    with pytest.raises(ValueError, match="parcours en largeur"):
        require_algorithm_premises(prompt, "La boucle provoque un arrêt prématuré.")


def test_breadth_first_search_false_claim_can_be_the_question_to_refute():
    from Backend.Core.france.pipeline import require_algorithm_premises

    prompt = (
        "Un élève affirme qu'une boucle fait que ce parcours en largeur "
        "s'arrête prématurément. Cette affirmation est-elle exacte ?\n"
        "```python\n"
        "while file:\n"
        "    sommet = file.pop(0)\n"
        "    if sommet not in visites:\n"
        "        visites.append(sommet)\n"
        "        file.extend(adj[sommet])\n"
        "```"
    )
    require_algorithm_premises(
        prompt,
        "Non. Le parcours peut mettre deux fois un sommet dans la file, "
        "mais la boucle ne le fait pas s'arrêter prématurément.",
    )


def test_early_return_on_repeat_can_really_stop_breadth_first_search():
    from Backend.Core.france.pipeline import require_algorithm_premises

    prompt = (
        "```python\n"
        "while file:\n"
        "    sommet = file.pop(0)\n"
        "    if sommet in visites:\n"
        "        return visites\n"
        "    if sommet not in visites:\n"
        "        visites.append(sommet)\n"
        "        file.extend(adj[sommet])\n"
        "```\n"
        "Le programme s'arrête prématurément si une boucle existe. "
        "Expliquez la faute."
    )
    require_algorithm_premises(
        prompt, "Le return quitte la fonction dès qu'un sommet est revu."
    )


def test_break_in_nested_loop_does_not_stop_queue_traversal():
    from Backend.Core.france.pipeline import require_algorithm_premises

    prompt = (
        "```python\n"
        "while file:\n"
        "    sommet = file.pop(0)\n"
        "    if sommet not in visites:\n"
        "        visites.append(sommet)\n"
        "        for voisin in adj[sommet]:\n"
        "            break\n"
        "        file.extend(adj[sommet])\n"
        "```\n"
        "Le programme s'arrête prématurément si une boucle existe."
    )
    with pytest.raises(ValueError, match="parcours en largeur"):
        require_algorithm_premises(prompt, "La boucle provoque l'arrêt prématuré.")


def test_tree_constructor_must_be_defined_in_candidate_facing_material():
    from Backend.Core.france.pipeline import require_tree_constructor_context

    prompt = (
        "Écrivez une fonction inserer(arbre, valeur) pour cet arbre. "
        "Si le nœud est vide, créez un nouvel objet."
    )
    answer = "if arbre is None: return Noeud(valeur)"
    with pytest.raises(ValueError, match="Noeud"):
        require_tree_constructor_context(prompt, answer, "Un ABR indexe les incidents.")

    require_tree_constructor_context(
        "La classe Noeud possède le constructeur Noeud(valeur). " + prompt,
        answer,
        "Un ABR indexe les incidents.",
    )


def test_merely_naming_tree_constructor_does_not_define_its_api():
    from Backend.Core.france.pipeline import require_tree_constructor_context

    with pytest.raises(ValueError, match="Noeud"):
        require_tree_constructor_context(
            "Utilisez Noeud(valeur) pour créer un nouveau nœud.",
            "return Noeud(valeur)",
            "Un ABR indexe les incidents.",
        )


def test_false_breadth_first_debug_premise_cannot_be_accepted(tmp_path):
    from Backend.Core.france.pipeline import generate_assessment

    class FalsePremiseClient(FrenchClient):
        def generate_json(self, prompt):
            result = super().generate_json(prompt)
            if prompt.startswith("Rédige directement en français académique"):
                task = json.loads(prompt.split("DONNÉES_JSON\n", 1)[1])
                if task["exercise_id"] == "1":
                    result["questions"][2]["prompt"] = (
                        "```python\n"
                        "def parcourir_largeur(adj, start):\n"
                        "    visites = []\n"
                        "    file = [start]\n"
                        "    while file:\n"
                        "        sommet = file.pop(0)\n"
                        "        if sommet not in visites:\n"
                        "            visites.append(sommet)\n"
                        "            file.extend(adj[sommet])\n"
                        "    return visites\n"
                        "```\n"
                        "Le programme s'arrête prématurément si une boucle existe."
                    )
                    result["questions"][2]["answer"] = (
                        "Une boucle provoque un arrêt prématuré."
                    )
            return result

    index = tmp_path / "sources.sqlite"
    make_index(index)
    checkpoint = tmp_path / "checkpoint.json"
    with pytest.raises(ValueError, match="Exercice 1 refusé"):
        generate_assessment(
            index_path=index,
            client=FalsePremiseClient(),
            seed=5,
            checkpoint=checkpoint,
        )
    state = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert list(state["accepted"]) == []
    assert all(
        "parcours en largeur" in attempt["error"]
        for attempt in state["failed_attempts"]
    )


def test_tree_logarithmic_advantage_needs_a_visible_balance_assumption():
    from Backend.Core.france.pipeline import require_tree_complexity_premise

    prompt = (
        "Un ABR contient les clés 10, 20, 30, 40 et 50. On recherche 40. "
        "Justifiez pourquoi cette opération est plus efficace qu'une recherche "
        "linéaire dans une liste non triée de 1000 éléments."
    )
    answer = "Dans un arbre équilibré, la recherche coûte O(log n)."
    with pytest.raises(ValueError, match="équilibre"):
        require_tree_complexity_premise(prompt, answer, "")

    require_tree_complexity_premise(
        "On suppose que cet ABR de 1000 clés est équilibré. " + prompt,
        answer,
        "",
    )


def test_negated_tree_balance_is_not_a_logarithmic_premise():
    from Backend.Core.france.pipeline import require_tree_complexity_premise

    with pytest.raises(ValueError, match="équilibre"):
        require_tree_complexity_premise(
            "Cet ABR non équilibré est-il plus efficace qu'une liste ?",
            "La recherche coûte O(log n).",
            "",
        )


def test_current_balanced_tree_premise_overrides_earlier_unbalanced_case():
    from Backend.Core.france.pipeline import require_tree_complexity_premise

    require_tree_complexity_premise(
        "On suppose maintenant cet ABR équilibré. Pourquoi est-il plus efficace ?",
        "La recherche dans cet arbre équilibré coûte O(log n).",
        "La question précédente portait sur un ABR non équilibré.",
    )


def test_current_question_can_transition_from_unbalanced_to_balanced_tree():
    from Backend.Core.france.pipeline import require_tree_complexity_premise

    require_tree_complexity_premise(
        "Après un ABR non équilibré, on suppose maintenant cet ABR équilibré. "
        "Pourquoi est-il plus efficace ?",
        "Pour un arbre équilibré, la recherche coûte O(log n).",
        "",
    )


def test_negated_balance_and_unrelated_tree_do_not_license_logarithmic_claim():
    from Backend.Core.france.pipeline import require_tree_complexity_premise

    answer = "La recherche coûte O(log n)."
    with pytest.raises(ValueError, match="équilibre"):
        require_tree_complexity_premise(
            "Cet ABR ne peut pas être équilibré. Pourquoi est-il plus efficace ?",
            answer,
            "",
        )
    with pytest.raises(ValueError, match="équilibre"):
        require_tree_complexity_premise(
            "Pourquoi cet ABR est-il plus efficace qu'une liste ?",
            answer,
            "Un autre ABR utilisé auparavant est équilibré.",
        )
    with pytest.raises(ValueError, match="équilibre"):
        require_tree_complexity_premise(
            "Ce n'est pas vrai que cet ABR est équilibré. "
            "Pourquoi est-il plus efficace ?",
            answer,
            "",
        )
    with pytest.raises(ValueError, match="équilibre"):
        require_tree_complexity_premise(
            "Cet ABR est équilibré ? Pourquoi est-il plus efficace ?",
            answer,
            "",
        )


def test_authoring_prompt_explains_the_balanced_tree_assumption():
    from Backend.Core.france.pipeline import _prompt, _tasks_for_seed

    prompt = _prompt(_tasks_for_seed(270100)[0], [], 270100, 1, "")
    assert "O(log n)" in prompt
    assert "on suppose que cet ABR est équilibré" in prompt
