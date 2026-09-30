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


class FrenchClient:
    provider = "ollama"
    model = "fixture"
    model_digest = "fixture-digest"

    def __init__(self, reject=False):
        self.calls = 0
        self.reject = reject

    def generate_json(self, prompt):
        self.calls += 1
        if prompt.startswith("Résous indépendamment"):
            return {
                "answers": {str(i): str(i) for i in range(1, 7)},
                "issues": [],
                "minutes": 60,
            }
        if prompt.startswith("Vérifie ce sujet"):
            return {
                "correct": not self.reject,
                "native_french": True,
                "curriculum_aligned": True,
                "difficulty_appropriate": True,
                "marking_consistent": True,
                "context_consistent": True,
                "issues": [],
                "rationale": "Analyse détaillée de chaque réponse et de son barème.",
                "question_ids": [str(i) for i in range(1, 7)],
            }
        task = json.loads(prompt.split("DONNÉES_JSON\n", 1)[1])
        number = task["exercise_id"]
        allocations = {
            "5.5": ["1", "1", "1", "1", "1", "0.5"],
            "6": ["1", "1", "1", "1", "1", "1"],
            "6.5": ["1.5", "1", "1", "1", "1", "1"],
        }[task["technical_points"]]
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
                    id=str(i),
                    prompt=prompt.format(i=i),
                    points=allocations[i - 1],
                    answer=str(i),
                    marking=[
                        {
                            "points": allocations[i - 1],
                            "criterion": f"Résultat {i} et justification.",
                        }
                    ],
                    material_ids=["support"] if i == 1 else [],
                    curriculum_codes=[task["required_curriculum_codes"][(i - 1) % len(task["required_curriculum_codes"])]],
                    operation=("apply", "analyse", "design", "debug", "justify", "analyse")[i - 1],
                    difficulty=(2, 2, 3, 3, 4, 4)[i - 1],
                    estimated_minutes=task["minutes"] // 6 + (1 if i <= task["minutes"] % 6 else 0),
                    verification={
                        "kind": "binary",
                        "input": format(i, "b"),
                        "expected": i,
                    },
                )
                for i in range(1, 7)
            ],
        }


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
        for task, exercise in zip(package["identity"]["blueprint"], package["exercises"], strict=True)
    )
    assert package["language_rubric"]["allocation_status"] == (
        "indicative_product_profile"
    )
    validate_package(package)
    assert client.calls == 9
    again = generate_assessment(
        index_path=index, client=client, seed=5, checkpoint=tmp_path / "checkpoint.json"
    )
    assert again == package
    assert client.calls == 9
    package["exercises"][0]["questions"][0]["answer"] = "changed"
    with pytest.raises(ValueError, match="hash"):
        validate_package(package)


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
