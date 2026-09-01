"""Edexcel's public-source and selected-answer handoff to the shared solver."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pastpapergen.ollama_client as subject
import pytest
from pastpapergen.generator import build_paper_blueprint
from pastpapergen.models import QuestionBlueprint
from pastpapergen.paper_configs import load_builtin_paper_config
from pastpapergen.syllabus import load_syllabus

from Backend.Core.assessment_contracts import EvidenceRecord
from Backend.Core.assessment_package import _extract_items
from Backend.Core.candidate_identity import candidate_content_identity
from Backend.Core.independent_solver import (
    IndependentSolver,
    require_solution_matches_scheme,
)
from tests.support.edexcel import forced_part
from tests.support.solver_responses import complete_solver_response

DATA = Path(__file__).parents[1] / "data" / "syllabus_seed.json"
CAPTURED = json.loads(
    (Path(__file__).parent / "fixtures" / "task7f_solver_responses.json").read_text()
)


def _paper(paper_id: str, seed: int):
    return build_paper_blueprint(
        load_builtin_paper_config(paper_id), load_syllabus(DATA), seed
    )


class Replay:
    def __init__(self, response):
        self.response = response
        self.prompts = []

    def generate_json(self, prompt):
        self.prompts.append(prompt)
        return copy.deepcopy(self.response)


def test_actual_paper_three_partial_solver_shape_is_rejected_before_review() -> None:
    question = _paper("paper_3", 26083051).questions[0]
    projection = subject._question_solver_projection(question, question)
    client = Replay(
        {
            "steps": ["Use Extract A and explain the labour-market factors."],
            "answer": "A source-based analysis without the other envelope fields.",
        }
    )

    with pytest.raises(ValueError, match="invalid solver response envelope"):
        IndependentSolver(client).solve(projection.item, projection.evidence)
    assert len(client.prompts) == 1


def test_edexcel_identity_binds_selected_source_key_credit_and_contract() -> None:
    multipart = _paper("paper_1", 26083049).questions[0]
    mcq = next(part for part in multipart.parts if part.options)
    baseline = candidate_content_identity(subject._difficulty_candidate(multipart, mcq))

    source = multipart.source_instance.model_copy(deep=True)
    rows = copy.deepcopy(source.rows)
    rows[0][0] = rows[0][0].model_copy(update={"text": "Changed public value"})
    changed_source = multipart.model_copy(
        update={"source_instance": source.model_copy(update={"rows": rows})}
    )
    changed_options = mcq.model_copy(
        update={
            "options": [
                *mcq.options[:-1],
                mcq.options[-1].model_copy(update={"text": "Changed distractor"}),
            ]
        }
    )
    changed_key = mcq.model_copy(update={"correct_option": mcq.options[-1].label})
    changed_credit = mcq.model_copy(
        update={"mark_scheme": [*mcq.mark_scheme, "Complete alternative"]}
    )
    changed_contract = mcq.model_copy(
        update={"assessment_contract": {"operation": "changed-contract"}}
    )

    changed_source_part = next(
        part for part in changed_source.parts if part.label == mcq.label
    )
    assert candidate_content_identity(
        subject._difficulty_candidate(changed_source, changed_source_part)
    ) != baseline
    for changed_part in [changed_options, changed_key, changed_credit, changed_contract]:
        assert candidate_content_identity(
            subject._difficulty_candidate(multipart, changed_part)
        ) != baseline


def test_edexcel_multipart_parent_credit_is_not_duplicated_in_part_identity() -> None:
    multipart = _paper("paper_1", 26083049).questions[0]
    part = multipart.parts[0]
    baseline = candidate_content_identity(subject._difficulty_candidate(multipart, part))
    changed_parent = multipart.model_copy(
        update={
            "mark_scheme": ["Duplicate parent guidance must not be part credit"],
            "mark_breakdown": "duplicate",
            "indicative_content": ["duplicate"],
            "assessment_contract": {"duplicate": True},
        }
    )

    assert candidate_content_identity(
        subject._difficulty_candidate(changed_parent, part)
    ) == baseline


@pytest.mark.parametrize("paper_id", ["paper_1", "paper_3"])
def test_edexcel_export_recomputes_standalone_and_multipart_identity(paper_id) -> None:
    blueprint = _paper(paper_id, 26083049)
    items = _extract_items(
        blueprint.model_dump(mode="json"),
        subject="economics_edexcel_a",
        paper_number=paper_id.removeprefix("paper_"),
    )
    live_candidates = [
        subject._difficulty_candidate(question, part)
        for question in blueprint.questions
        for part in (question.parts or [question])
    ]

    assert len(items) == len(live_candidates)
    assert [
        candidate_content_identity(item["difficulty_candidate_projection"])
        for item in items
    ] == [candidate_content_identity(candidate) for candidate in live_candidates]


@pytest.mark.parametrize(
    "paper_id,seed,question_index,response_id",
    [
        ("paper_1", 26083049, 0, "p1"),
        ("paper_2", 26083122, 0, "p2_1"),
        ("paper_2", 26083122, 1, "p2_2"),
        ("paper_3", 26083051, 0, "p3"),
    ],
)
def test_actual_recorded_responses_cross_the_real_source_and_choice_boundary(
    monkeypatch, paper_id, seed, question_index, response_id
):
    blueprint = _paper(paper_id, seed)
    question = blueprint.questions[question_index]
    if question.parts:
        question = question.model_copy(
            update={"parts": [question.parts[0]], "marks": question.parts[0].marks}
        )
    reached = []

    class Reviewed:
        def model_dump(self, **_kwargs):
            return {"approved": True, "reached": "difficulty"}

    def difficulty(_client, **kwargs):
        reached.append(kwargs)
        return Reviewed()

    monkeypatch.setattr(subject, "require_difficulty_review", difficulty)
    client = Replay(CAPTURED[response_id])
    reviewed = subject.review_blueprint_difficulty(
        client,
        blueprint.model_copy(update={"questions": [question]}),
        load_syllabus(DATA),
    )

    evidence = (
        reviewed.questions[0].parts[0].difficulty_evidence
        if question.parts
        else reviewed.questions[0].difficulty_evidence
    )
    assert evidence == {"approved": True, "reached": "difficulty"}
    assert len(reached) == 1


@pytest.mark.parametrize("route", ["multipart", "standalone", "mcq"])
def test_blind_projection_uses_one_public_source_without_private_credit_or_key(route):
    if route == "standalone":
        question = _paper("paper_3", 26083051).questions[0]
        part = question
    else:
        question = _paper("paper_1", 26083049).questions[0]
        part = question.parts[1 if route == "mcq" else 0]
    source = question.source_instance.model_copy(deep=True)
    rows = copy.deepcopy(source.rows)
    rows[0][0] = rows[0][0].model_copy(update={"text": "Public credit column"})
    question = question.model_copy(
        update={"source_instance": source.model_copy(update={"rows": rows})}
    )
    projection = subject._question_solver_projection(question, part)
    private = "PRIVATE_F2_CREDIT"
    projection.item["assessment_contract"]["credit"] = [private]
    answer = projection.expected_choice or "A source-based explanation."
    response = complete_solver_response({
        "steps": ["Use the public source."],
        "answer": answer,
        "mark_points": [answer],
        "evidence_ids": [projection.evidence[0].id],
    })
    client = Replay(response)

    IndependentSolver(client).solve(projection.item, projection.evidence)

    payload = json.loads(client.prompts[0].split("\n", 1)[1])
    assert payload["item"]["stimulus"] == json.loads(payload["sources"][0]["text"])
    assert payload["sources"][0]["id"] == question.source_instance.source_id
    assert payload["item"]["stimulus"]["provenance"] == "illustrative-generated"
    assert "Public credit column" in payload["sources"][0]["text"]
    assert "assessment_contract" not in payload["item"]
    assert "correct_choice" not in payload["item"]
    assert private not in client.prompts[0]
    assert private not in payload["sources"][0]["text"]


def test_standalone_source_and_numeric_candidate_inputs_use_the_same_projection():
    question = forced_part("terms_of_trade_index_chart", "calculate", 2)
    part = question.parts[0]
    projection = subject._question_solver_projection(question, part)
    solution = IndependentSolver().solve(projection.item, projection.evidence)

    require_solution_matches_scheme(solution, projection.item)
    assert json.loads(projection.evidence[0].text) == projection.item["stimulus"]
    assert solution.solution_source == "deterministic-candidate-inputs"
    assert solution.integrity_version == "closed-numeric-v2"


def test_genuinely_source_free_item_keeps_empty_evidence_and_empty_citations(
    monkeypatch,
):
    question = QuestionBlueprint(
        section="A",
        number="1",
        marks=1,
        command_word="state",
        topic_id="1.1",
        prompt="State one economic agent.",
        stimulus_kind="written",
    )
    projection = subject._question_solver_projection(question, question)
    client = Replay(complete_solver_response(
        {"answer": "A household", "mark_points": ["A household"], "evidence_ids": []}
    ))

    class Reviewed:
        def model_dump(self, **_kwargs):
            return {"approved": True}

    monkeypatch.setattr(
        subject,
        "require_difficulty_review",
        lambda *_args, **_kwargs: Reviewed(),
    )

    blueprint = _paper("paper_3", 1).model_copy(update={"questions": [question]})
    reviewed = subject.review_blueprint_difficulty(
        client, blueprint, load_syllabus(DATA)
    )

    assert projection.evidence == ()
    assert reviewed.questions[0].difficulty_evidence == {"approved": True}
    assert json.loads(client.prompts[0].split("\n", 1)[1])["sources"] == []


@pytest.mark.parametrize(
    "mutation",
    [
        "foreign-id",
        "changed-source",
        "stale-fingerprint",
        "duplicate-identity",
        "private-evidence",
    ],
)
def test_source_projection_rejects_foreign_stale_duplicate_or_private_evidence(
    mutation,
):
    question = _paper("paper_1", 26083049).questions[0]
    projection = subject._question_solver_projection(question, question.parts[0])
    item = copy.deepcopy(projection.item)
    evidence = list(projection.evidence)
    if mutation == "foreign-id":
        item["stimulus"]["source_id"] = "26083049-A-2"
    elif mutation == "changed-source":
        item["stimulus"]["rows"][1][1] = "Low"
    elif mutation == "stale-fingerprint":
        item["stimulus"]["source_fingerprint"] = "0" * 64
    elif mutation == "duplicate-identity":
        evidence.append(evidence[0])
    else:
        public = json.loads(evidence[0].text)
        public["assessment_contract"] = {"credit": ["PRIVATE"]}
        item["stimulus"] = public
        evidence = [EvidenceRecord(id=evidence[0].id, text=json.dumps(public))]

    with pytest.raises(ValueError):
        subject._validate_solver_projection(item, evidence)


@pytest.mark.parametrize("ids", [["invented"], ["26083049-A-1", "invented"]])
def test_solver_still_rejects_invented_and_mixed_citation_ids(ids):
    question = _paper("paper_1", 26083049).questions[0]
    projection = subject._question_solver_projection(question, question.parts[0])
    response = {**CAPTURED["p1"], "evidence_ids": ids}

    with pytest.raises(ValueError, match="unavailable evidence"):
        IndependentSolver(Replay(response)).solve(projection.item, projection.evidence)


@pytest.mark.parametrize(
    "mutation", ["empty-source-id", "missing-key", "duplicate-label"]
)
def test_projection_rejects_empty_source_or_non_unique_choice_identity(mutation):
    if mutation == "empty-source-id":
        question = _paper("paper_1", 26083049).questions[0]
        question = question.model_copy(
            update={
                "source_instance": question.source_instance.model_copy(
                    update={"source_id": ""}
                )
            }
        )
        part = question.parts[0]
    else:
        question = _paper("paper_2", 26083122).questions[0]
        part = question.parts[0]
        if mutation == "missing-key":
            part = part.model_copy(update={"correct_option": "Z"})
        else:
            options = list(part.options)
            options[1] = options[1].model_copy(
                update={"label": " " + options[0].label.casefold() + " "}
            )
            part = part.model_copy(update={"options": options})

    with pytest.raises(ValueError):
        subject._question_solver_projection(question, part)


def test_reordered_choice_resolves_one_key_and_wrong_key_still_fails_reconciliation():
    question = _paper("paper_2", 26083122).questions[0]
    part = question.parts[0]
    reordered = part.model_copy(update={"options": list(reversed(part.options))})
    projection = subject._question_solver_projection(question, reordered)
    answer = next(
        option.text
        for option in reordered.options
        if option.label == reordered.correct_option
    )
    solution = IndependentSolver(
        Replay(complete_solver_response(
            {"answer": answer, "mark_points": [answer], "evidence_ids": []}
        ))
    ).solve(projection.item, projection.evidence)

    require_solution_matches_scheme(
        solution, projection.item, expected_choice=projection.expected_choice
    )
    assert projection.item["correct_choice"] == 2
    wrong = copy.deepcopy(projection.item)
    wrong["correct_choice"] = 0
    with pytest.raises(ValueError, match="keyed option"):
        require_solution_matches_scheme(
            solution, wrong, expected_choice=projection.expected_choice
        )
