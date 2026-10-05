import json

import pytest

from Backend.Core.france.graph_tree_contract import build_graph_tree_contract
from Backend.Core.france.pipeline import _tasks_for_seed


def _question(plan, result):
    material = "arbre" if plan["id"] in {"1e", "1f"} else "reseau"
    return {
        "id": plan["id"],
        "contract_task_id": plan["id"],
        "claimed_result": result,
        "prompt": f"Analysez le support `{material}` et justifiez votre réponse.",
        "points": plan["points"],
        "answer": "Une réponse argumentée fondée sur les données fournies.",
        "marking": [{"points": plan["points"], "criterion": "Démarche correcte"}],
        "material_ids": [material],
        "curriculum_codes": [plan["required_curriculum_code"]],
        "operation": plan["operation"],
        "difficulty": plan["difficulty"],
        "estimated_minutes": plan["estimated_minutes"],
        "verification": {"kind": "human"},
    }


class PartClient:
    def __init__(self, stop_after=None):
        self.calls = []
        self.stop_after = stop_after

    def generate_json(self, prompt):
        if self.stop_after is not None and len(self.calls) == self.stop_after:
            raise KeyboardInterrupt
        request = json.loads(prompt.split("\nDONNÉES_JSON\n", 1)[1])
        self.calls.append(request)
        questions = [
            _question(plan, request["expected"][plan["id"]])
            for plan in request["question_blueprint"]
        ]
        if request["part"] == "A":
            return {
                "title": "Réseau et interventions",
                "context": "Une équipe étudie les trajets et les demandes d'intervention.",
                "questions": questions,
            }
        return {"questions": questions}


def _setup():
    return _tasks_for_seed(270100)[0], build_graph_tree_contract(270100, "1")


def test_part_authoring_exposes_only_part_facts_and_resumes_after_cancel(tmp_path):
    from Backend.Core.france.graph_tree_authoring import author_graph_tree_parts

    task, contract = _setup()
    draft = tmp_path / "draft.json"
    first = PartClient(stop_after=1)
    with pytest.raises(KeyboardInterrupt):
        author_graph_tree_parts(first, task, contract, [], draft)
    saved = json.loads(draft.read_text())
    assert [item["part"] for item in saved["parts"]] == ["A"]
    assert saved["contract_sha256"] == contract.digest
    assert "graph" in first.calls[0]["facts"]
    assert "tree" not in first.calls[0]["facts"]

    resumed = PartClient()
    raw, evidence = author_graph_tree_parts(resumed, task, contract, [], draft)
    assert [item["part"] for item in resumed.calls] == ["B", "C"]
    assert "tree" not in resumed.calls[0]["facts"]
    assert "graph" not in resumed.calls[1]["facts"]
    assert [item["id"] for item in raw["questions"]] == contract.to_dict()["task_ids"]
    assert evidence["contract_sha256"] == contract.digest
    assert len(evidence["parts"]) == 3
    assert all("response_sha256" in item for item in evidence["parts"])


def test_bounded_repair_rejects_changes_to_locked_fields_and_peers():
    from Backend.Core.france.graph_tree_authoring import apply_graph_tree_repair

    task, contract = _setup()
    client = PartClient()
    raw, _ = author_parts_without_draft(client, task, contract)
    original = raw["questions"][0]
    replacement = {
        **original,
        "prompt": "Justifiez le résultat à partir du graphe `reseau`.",
    }
    revised, record = apply_graph_tree_repair(raw, "1a", replacement, contract)
    assert revised["questions"][0]["prompt"] == replacement["prompt"]
    assert raw["questions"][0]["prompt"] == original["prompt"]
    assert revised["questions"][1:] == raw["questions"][1:]
    assert record["before_sha256"] != record["after_sha256"]
    for field, value in (
        ("claimed_result", {}),
        ("contract_task_id", "1b"),
        ("points", "99"),
        ("id", "1b"),
    ):
        with pytest.raises(ValueError):
            apply_graph_tree_repair(raw, "1a", {**replacement, field: value}, contract)
    with pytest.raises(ValueError):
        apply_graph_tree_repair(
            {**raw, "materials": [{"kind": "table"}]}, "1a", replacement, contract
        )


def author_parts_without_draft(client, task, contract):
    from Backend.Core.france.graph_tree_authoring import author_graph_tree_parts

    return author_graph_tree_parts(client, task, contract, [], None)


def test_part_transport_schema_matches_prompt_and_locks_two_contract_items():
    from Backend.Core.france.graph_tree_authoring import (
        part_prompt,
        part_response_schema,
    )
    from Backend.Core.france.provider import response_policy

    task, contract = _setup()
    for part in "ABC":
        prompt = part_prompt(part, task, contract, [])
        schema, budget = response_policy(prompt)
        embedded = json.loads(
            prompt.split("schéma :\n", 1)[1].split("\nDONNÉES_JSON", 1)[0]
        )
        assert schema == embedded == part_response_schema(part)
        assert budget >= 3072
        question = schema["properties"]["questions"]["items"]
        assert {
            "contract_task_id",
            "claimed_result",
            "material_ids",
            "verification",
        } <= set(question["required"])
        assert schema["properties"]["questions"]["minItems"] == 2
        assert schema["properties"]["questions"]["maxItems"] == 2


def test_bounded_repair_transport_includes_only_target_and_its_locked_facts():
    from Backend.Core.france.provider import response_policy
    from Backend.Core.france.question_review import graph_tree_repair_prompt

    task, contract = _setup()
    raw, _ = author_parts_without_draft(PartClient(), task, contract)
    prompt = graph_tree_repair_prompt(
        raw, task, contract, "1e", {"issues": ["ambiguous"]}
    )
    schema, _ = response_policy(prompt)
    request = json.loads(prompt.split("\nDONNÉES_JSON\n", 1)[1])
    assert request["question"]["id"] == "1e"
    assert "tree" in request["facts"] and "graph" not in request["facts"]
    assert "questions" not in request
    assert "claimed_result" in schema["required"]
    assert "contract_task_id" in schema["required"]


def test_resumed_part_rejects_changed_prompt_or_extra_saved_part(tmp_path):
    from Backend.Core.france.graph_tree_authoring import author_graph_tree_parts

    task, contract = _setup()
    draft = tmp_path / "draft.json"
    author_graph_tree_parts(PartClient(), task, contract, [], draft)
    saved = json.loads(draft.read_text())
    original_hash = saved["parts"][0]["prompt_sha256"]
    saved["parts"][0]["prompt_sha256"] = "0" * 64
    draft.write_text(json.dumps(saved))
    with pytest.raises(ValueError, match="Preuve de partie"):
        author_graph_tree_parts(PartClient(), task, contract, [], draft)
    saved["parts"][0]["prompt_sha256"] = original_hash
    saved["parts"].append(saved["parts"][2])
    draft.write_text(json.dumps(saved))
    with pytest.raises(ValueError, match="brouillon"):
        author_graph_tree_parts(PartClient(), task, contract, [], draft)


class ReviewClient:
    def __init__(self, corrupt_repair=False):
        self.alignment_calls = 0
        self.corrupt_repair = corrupt_repair

    def generate_json(self, prompt):
        if prompt.startswith("Contrôle indépendant des capacités"):
            self.alignment_calls += 1
            request = json.loads(prompt.split("\nDONNÉES_JSON\n", 1)[1])
            return {
                "questions": [
                    {
                        "question_id": plan["id"],
                        "objective_code": plan["required_curriculum_code"],
                        "aligned": self.alignment_calls > 1 or plan["id"] != "1a",
                        "rationale": "La consigne mobilise la capacité attendue et les données affichées dans l'exercice.",
                        "issues": ["Préciser la consigne"]
                        if self.alignment_calls == 1 and plan["id"] == "1a"
                        else [],
                    }
                    for plan in request["question_blueprint"]
                ]
            }
        if prompt.startswith("Répare la question verrouillée"):
            question = json.loads(prompt.split("\nDONNÉES_JSON\n", 1)[1])["question"]
            changed = {
                **question,
                "prompt": "À partir du support `reseau`, calculez et justifiez le plus court chemin demandé.",
            }
            if self.corrupt_repair:
                changed["points"] = "99"
            return changed
        if prompt.startswith("Résous indépendamment"):
            exercise = json.loads(prompt.split("\n", 1)[1])
            return {
                "answers": {
                    item["id"]: "Résultat contrôlé." for item in exercise["questions"]
                },
                "issues": [],
                "minutes": 70,
            }
        if prompt.startswith("Vérifie ce sujet"):
            exercise = json.loads(prompt.split("\n", 1)[1])["exercise"]
            return {
                "correct": True,
                "native_french": True,
                "curriculum_aligned": True,
                "difficulty_appropriate": True,
                "marking_consistent": True,
                "context_consistent": True,
                "issues": [],
                "rationale": "Chaque question et son barème ont été vérifiés contre les données et la résolution.",
                "question_ids": [item["id"] for item in exercise["questions"]],
            }
        raise AssertionError("Unexpected model prompt")


def test_contract_review_rechecks_all_gates_after_one_bounded_repair(monkeypatch):
    from Backend.Core.france import pipeline

    task, contract = _setup()
    raw, _ = author_parts_without_draft(PartClient(), task, contract)
    original = pipeline._prepare_candidate
    calls = []

    def observe(*args, **kwargs):
        calls.append(args[0])
        return original(*args, **kwargs)

    monkeypatch.setattr(pipeline, "_prepare_candidate", observe)
    record = {}
    client = ReviewClient()
    exercise, evidence = pipeline.evaluate_graph_tree_draft(
        raw, task, contract, [], [], client, record
    )
    assert client.alignment_calls == 2
    assert len(calls) == 2
    assert exercise.questions[0].prompt != raw["questions"][0]["prompt"]
    assert evidence["contract_binding"]["contract_sha256"] == contract.digest
    assert len(evidence["targeted_repairs"]) == 1
    assert evidence["question_alignment"]["review"]["questions"][0]["aligned"]
    assert len(evidence["deterministic"]) == 6
    assert evidence["independent_solution"]["issues"] == []


def test_contract_review_preserves_rejected_repair_response():
    from Backend.Core.france.pipeline import evaluate_graph_tree_draft

    task, contract = _setup()
    raw, _ = author_parts_without_draft(PartClient(), task, contract)
    record = {}
    with pytest.raises(ValueError, match="verrouillé"):
        evaluate_graph_tree_draft(
            raw, task, contract, [], [], ReviewClient(True), record
        )
    assert record["repair_responses"][0]["response"]["points"] == "99"
    assert record["candidate"] == raw
