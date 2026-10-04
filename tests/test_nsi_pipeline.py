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

    with pytest.raises(ValueError, match="plan détaillé"):
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
            {"id": "1b", "prompt": "Analyser le graphe map_ville_2."},
            {"id": "1c", "prompt": "Analyser le graphe G."},
            {"id": "1d", "prompt": "Utiliser road_network.", "material_ids": []},
        ],
    }
    bound, evidence = bind_explicit_material_ids(raw)

    assert bound["questions"][0]["material_ids"] == ["map_ville"]
    assert "material_ids" not in bound["questions"][1]
    assert "material_ids" not in bound["questions"][2]
    assert bound["questions"][3]["material_ids"] == []
    assert evidence == [{"question_id": "1a", "material_ids": ["map_ville"]}]
    assert "material_ids" not in raw["questions"][0]


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
    changed["evidence"][0]["candidate"]["questions"][0]["prompt"] = "Voir G."
    with pytest.raises(ValueError, match="liaison"):
        validate_package(changed)

    changed = deepcopy(package)
    changed["evidence"][0]["candidate"]["questions"][0]["material_ids"] = []
    with pytest.raises(ValueError, match="liaison"):
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
