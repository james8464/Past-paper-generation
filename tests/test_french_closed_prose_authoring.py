"""Selection-only French authoring preserves rejected responses and replay identity."""

import json
from copy import deepcopy
from hashlib import sha256

import pytest

from Backend.Core.france.graph_tree_contract import build_graph_tree_contract
from Backend.Core.france.pipeline import _tasks_for_seed


def _hash(value):
    return sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


def _setup():
    return _tasks_for_seed(270100)[0], build_graph_tree_contract(270100, "1")


def _identity(model="model-a"):
    return {
        "provider": "ollama",
        "model_digest": model,
        "implementation_sha256": "a" * 64,
    }


def _response(request):
    response = {
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
        response.update(scene_id="service", slots={"activity": "interventions"})
    return response


class SelectionClient:
    def __init__(self, *, invalid=None, stop_after=None):
        self.calls = []
        self.invalid = invalid
        self.stop_after = stop_after

    def generate_json(self, prompt):
        if self.stop_after is not None and len(self.calls) == self.stop_after:
            raise KeyboardInterrupt
        request = json.loads(prompt.split("\nDONNÉES_JSON\n", 1)[1])
        self.calls.append(request)
        response = _response(request)
        if self.invalid is not None and request["part"] == "B":
            self.invalid(response)
            self.invalid_response = deepcopy(response)
        return response


def test_v12_schema_policy_and_parts_replay_exactly(tmp_path):
    from Backend.Core.france.graph_tree_authoring import (
        author_closed_prose_parts,
        part_selection_prompt,
        part_selection_schema,
        replay_closed_prose_parts,
    )
    from Backend.Core.france.graph_tree_prose import (
        PROSE_CONTRACT_VERSION,
        prose_catalogue_digest,
    )
    from Backend.Core.france.provider import response_policy

    task, contract = _setup()
    for part in "ABC":
        prompt = part_selection_prompt(part, task, contract, [])
        schema, _ = response_policy(prompt)
        assert schema == part_selection_schema(part)
        assert schema["additionalProperties"] is False
        assert (
            schema["properties"]["questions"]["items"]["additionalProperties"] is False
        )
    draft = tmp_path / "selection.json"
    raw, evidence = author_closed_prose_parts(
        SelectionClient(), task, contract, [], draft, run_identity=_identity()
    )
    assert evidence["prose_contract_version"] == PROSE_CONTRACT_VERSION
    assert evidence["prose_catalogue_sha256"] == prose_catalogue_digest()
    assert (
        replay_closed_prose_parts(
            task, contract, [], evidence, run_identity=_identity()
        )
        == raw
    )
    assert [q["id"] for q in raw["questions"]] == contract.to_dict()["task_ids"]
    assert "A et F sont directement reliés" not in json.dumps(raw, ensure_ascii=False)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value.update(title="A et F sont directement reliés."),
        lambda value: value["questions"][0].update(
            prompt="A et F sont directement reliés."
        ),
        lambda value: value["questions"][0].update(
            marking="A et F sont directement reliés."
        ),
        lambda value: value["questions"][0].update(question_form_id="1c-unknown"),
        lambda value: value["questions"][0].update(points="99"),
        lambda value: value["questions"][0]["claimed_result"].update(order=["F"]),
        lambda value: value.update(questions=value["questions"][:1]),
    ],
)
def test_rejected_response_is_recorded_with_prompt_and_run_identity(tmp_path, mutate):
    from Backend.Core.france.graph_tree_authoring import author_closed_prose_parts

    task, contract = _setup()
    draft = tmp_path / "selection.json"
    client = SelectionClient(invalid=mutate)
    with pytest.raises(ValueError):
        author_closed_prose_parts(
            client, task, contract, [], draft, run_identity=_identity()
        )
    saved = json.loads(draft.read_text())
    assert [item["part"] for item in saved["parts"]] == ["A"]
    failure = saved["failed_attempts"][-1]
    assert failure["part"] == "B"
    assert failure["response"] == client.invalid_response
    assert failure["response_sha256"] == _hash(failure["response"])
    assert len(failure["prompt_sha256"]) == 64
    assert failure["run_identity_sha256"] == saved["run_identity_sha256"]


def test_resume_keeps_failure_and_rejects_tampering(tmp_path):
    from Backend.Core.france.graph_tree_authoring import (
        author_closed_prose_parts,
        replay_closed_prose_parts,
    )

    task, contract = _setup()
    draft = tmp_path / "selection.json"
    with pytest.raises(ValueError):
        author_closed_prose_parts(
            SelectionClient(
                invalid=lambda response: response.update(
                    context="Le graphe est complet."
                )
            ),
            task,
            contract,
            [],
            draft,
            run_identity=_identity(),
        )
    raw, evidence = author_closed_prose_parts(
        SelectionClient(), task, contract, [], draft, run_identity=_identity()
    )
    assert len(evidence["failed_attempts"]) == 1
    assert [part["part"] for part in evidence["parts"]] == list("ABC")
    for field, value in (
        ("prose_catalogue_sha256", "0" * 64),
        ("prose_contract_version", "other"),
        ("run_identity_sha256", "0" * 64),
    ):
        bad = deepcopy(evidence)
        bad[field] = value
        with pytest.raises(ValueError):
            replay_closed_prose_parts(task, contract, [], bad, run_identity=_identity())
    bad = deepcopy(evidence)
    bad["failed_attempts"][0]["response_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        replay_closed_prose_parts(task, contract, [], bad, run_identity=_identity())
    bad = deepcopy(evidence)
    bad["failed_attempts"][0]["prompt_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        replay_closed_prose_parts(task, contract, [], bad, run_identity=_identity())
    with pytest.raises(ValueError):
        replay_closed_prose_parts(
            task, contract, [], evidence, run_identity=_identity("model-b")
        )
    assert (
        replay_closed_prose_parts(
            task, contract, [], evidence, run_identity=_identity()
        )
        == raw
    )


def test_interruption_keeps_accepted_part_and_targeted_repair_preserves_peers(tmp_path):
    from Backend.Core.france.graph_tree_authoring import (
        apply_closed_prose_repair,
        author_closed_prose_parts,
    )

    task, contract = _setup()
    draft = tmp_path / "selection.json"
    with pytest.raises(KeyboardInterrupt):
        author_closed_prose_parts(
            SelectionClient(stop_after=1),
            task,
            contract,
            [],
            draft,
            run_identity=_identity(),
        )
    saved = json.loads(draft.read_text())
    assert [part["part"] for part in saved["parts"]] == ["A"]
    raw, evidence = author_closed_prose_parts(
        SelectionClient(), task, contract, [], draft, run_identity=_identity()
    )
    selections = [part["response"] for part in evidence["parts"]]
    replacement = deepcopy(selections[0]["questions"][0])
    replacement["question_form_id"] = "1a-q2"
    revised_selections, revised, record = apply_closed_prose_repair(
        selections, "1a", replacement, task, contract
    )
    assert revised["questions"][0]["prompt"] != raw["questions"][0]["prompt"]
    assert revised["questions"][1:] == raw["questions"][1:]
    assert revised["context"] == raw["context"]
    assert revised_selections[1:] == selections[1:]
    assert record["before_sha256"] == _hash(raw)
    with pytest.raises(ValueError):
        apply_closed_prose_repair(
            selections, "1a", {**replacement, "answer": "invented"}, task, contract
        )


def test_targeted_repair_prompt_uses_selection_only_schema():
    from Backend.Core.france.provider import response_policy
    from Backend.Core.france.question_review import closed_prose_repair_prompt

    task, contract = _setup()
    selections = [
        _response(
            {
                "part": part,
                "task_ids": contract.to_dict()["task_ids"][start : start + 2],
                "expected": contract.to_dict()["expected"],
            }
        )
        for part, start in (("A", 0), ("B", 2), ("C", 4))
    ]
    prompt = closed_prose_repair_prompt(
        selections, task, contract, "1e", {"issues": ["consigne ambiguë"]}
    )
    schema, _ = response_policy(prompt)
    assert schema["additionalProperties"] is False
    assert set(schema["properties"]) == {
        "contract_task_id",
        "claimed_result",
        "question_form_id",
        "rubric_form_id",
    }
    request = json.loads(prompt.split("\nDONNÉES_JSON\n", 1)[1])
    assert request["question_id"] == "1e"
    assert "questions" not in request
