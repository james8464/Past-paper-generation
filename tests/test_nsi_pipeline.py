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


def test_question_alignment_rejects_semantic_mismatch_despite_correct_metadata(tmp_path):
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
                result["prompt"] = f"Nouvelle version {self.repairs} : " + result["prompt"]
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
    assert all(
        item["repair_responses"][0]["response"]["id"] == "9z" for item in failed
    )


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
                if request["id"] == "1" and request["questions"][0]["prompt"].startswith(
                    "Version corrigée"
                ):
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
            {"id": "1b", "prompt": "Comparer support_1 et support_2.", "material_ids": []},
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
        "questions": [
            {"id": "1a", "prompt": "Lire `support`.", "material_ids": []}
        ],
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
