"""Candidate-grounded verification for the bounded AQA SQL construction tasks."""

from __future__ import annotations

import copy
import json

import cspapergen.ollama_client as subject
import pymupdf
import pytest
from cspapergen.generator import build_paper2_blueprint, build_topic_question_bank
from cspapergen.ollama_client import (
    SQLProgramValidationError,
    _difficulty_solution,
    _part_solver_projection,
    _solve_part_with_sql_validation,
)
from cspapergen.render_pdf import candidate_stimulus_data, render_question_paper
from cspapergen.syllabus import load_syllabus

from Backend.Core.assessment_package import _extract_items
from Backend.Core.computer_science_authoring import question_content_sha256
from Backend.Core.independent_solver import IndependentSolver
from Backend.Core.model_review import require_difficulty_review
from Backend.Core.reference_demand import build_item_demand_target, profile_for
from Backend.Core.subjects.sql_contracts import (
    SQL_VALIDATION_VERSION,
    SQLSourceContract,
    render_sql_schema,
    sql_source_intent_sha256,
    validate_sql_response,
)
from tests.support.solver_responses import complete_solver_response


def _sql_question(*, bank: bool = False):
    syllabus = load_syllabus()
    blueprint = (
        build_topic_question_bank(syllabus, topic_id="4.10", seed=26083134)
        if bank
        else build_paper2_blueprint(syllabus, seed=26083134)
    )
    return next(question for question in blueprint.questions if question.style_id == "sql_normalisation")


def _contract_and_intent(label: str):
    question = _sql_question()
    assert question.stimulus is not None and question.stimulus.sql_contract is not None
    return question.stimulus.sql_contract, label


class Replay:
    def __init__(self, responses):
        self.responses = list(responses)
        self.prompts: list[str] = []

    def generate_json(self, prompt: str):
        self.prompts.append(prompt)
        return copy.deepcopy(self.responses.pop(0))


CAPTURED_COUNT_BOOKING_RESPONSE = {
    "steps": [
        "Identify the required columns: 'Activity' from the SESSION table and a count of bookings.",
        "Join the SESSION and BOOKING tables on the common field 'SessionID'.",
        "Group the results by the activity name to aggregate the counts.",
        "Apply a HAVING clause to filter groups where the count of bookings is greater than or equal to 5.",
        "Sort the final result set in descending order based on the booking count.",
    ],
    "answer": (
        "SELECT Activity, COUNT(Booking) FROM SESSION JOIN BOOKING ON "
        "SESSION.SessionID = BOOKING.SessionID GROUP BY Activity HAVING "
        "COUNT(Booking) >= 5 ORDER BY COUNT(Booking) DESC;"
    ),
    "mark_points": [
        "SELECT Activity, COUNT(*) FROM SESSION JOIN BOOKING ON "
        "SESSION.SessionID = BOOKING.SessionID GROUP BY Activity HAVING "
        "COUNT(*) >= 5 ORDER BY COUNT(*) DESC"
    ],
    "evidence_ids": [],
    "alternatives": [],
    "partial_credit_boundaries": [],
    "follow_through_rules": [],
}


def _response(answer: str, source_id: str, *, points: list[str] | None = None):
    return complete_solver_response({
        "steps": ["Use the supplied schema and requested relational operation."],
        "answer": answer,
        "mark_points": points if points is not None else [answer],
        "evidence_ids": [source_id],
    })


@pytest.mark.parametrize(
    ("part_index", "answer", "mark_points"),
    [
        (
            0,
            "The use of the equal sign (=) with NULL.",
            {"the use of the equal sign (=) with NULL": 1},
        ),
        (
            1,
            (
                "SELECT Activity, COUNT(*) FROM SESSION JOIN BOOKING ON "
                "SESSION.SessionID = BOOKING.SessionID GROUP BY Activity "
                "HAVING COUNT(*) >= 5 ORDER BY COUNT(*) DESC;"
            ),
            {
                "selection": (
                    "SELECT Activity, COUNT(*) FROM SESSION JOIN BOOKING ON "
                    "SESSION.SessionID = BOOKING.SessionID GROUP BY Activity "
                    "HAVING COUNT(*) >= 5 ORDER BY COUNT(*) DESC;"
                )
            },
        ),
    ],
)
def test_actual_object_mark_point_shapes_fail_the_raw_solver_envelope(
    part_index, answer, mark_points
):
    question = _sql_question()
    projection = _part_solver_projection(question, question.parts[part_index])
    client = Replay(
        [
            {
                "steps": ["Use the supplied schema and rows."],
                "answer": answer,
                "mark_points": mark_points,
                "evidence_ids": [projection.evidence[0].id],
                "alternatives": [],
                "partial_credit_boundaries": [],
                "follow_through_rules": [],
            }
        ]
    )

    with pytest.raises(ValueError, match="invalid solver response envelope"):
        IndependentSolver(client).solve(projection.item, projection.evidence)
    assert len(client.prompts) == 1


def test_public_sql_contract_is_one_render_solver_export_and_hash_source(tmp_path):
    question = _sql_question()
    stimulus = question.stimulus
    assert stimulus is not None and stimulus.sql_contract is not None
    public = candidate_stimulus_data(stimulus)
    projection = _part_solver_projection(question, question.parts[1])
    contract = stimulus.sql_contract

    assert json.loads(projection.evidence[0].text) == public
    assert projection.evidence[0].id == contract.source_id == public["source_id"]
    assert projection.item["authoring_context"]["sql_answer_contract"]["intent"] == contract.intents["2"].model_dump(mode="json")
    assert projection.item["authoring_context"]["sql_source_intent_sha256"] == sql_source_intent_sha256(contract, "2")
    assert all(
        _part_solver_projection(question, part).evidence[0].id == contract.source_id
        for part in question.parts
    )
    rendered_source = render_sql_schema(contract)
    assert "BOOKING.MemberID -> MEMBER.MemberID" in rendered_source
    assert "BOOKING.SessionID -> SESSION.SessionID" in rendered_source
    assert "Activity NOT NULL" in rendered_source
    assert "BookedAt NULL" in rendered_source
    assert "Attended NOT NULL" in rendered_source
    assert "1842, 27, FALSE" in rendered_source
    assert "1844, 27, TRUE" in rendered_source
    bank_contract = _sql_question(bank=True).stimulus.sql_contract
    assert bank_contract.sample_tables == []

    path = tmp_path / "paper.pdf"
    paper = build_paper2_blueprint(load_syllabus(), seed=26083134)
    render_question_paper(paper, path)
    with pymupdf.open(path) as document:
        text = " ".join(page.get_text() for page in document)
    for name in ("MEMBER", "SESSION", "BOOKING", "MemberID", "SessionID", "Activity"):
        assert name in text
    assert "Activity NOT NULL" in text
    assert "BookedAt NULL" in text

    items = _extract_items(paper.model_dump(mode="json"), subject="computer_science", paper_number="2")
    select_item = next(item for item in items if item["prompt"] == question.parts[1].prompt)
    assert select_item["candidate_source_contract"]["source_id"] == contract.source_id
    assert select_item["answer_intent"] == contract.intents["2"].model_dump(mode="json")
    assert select_item["source_intent_sha256"] == sql_source_intent_sha256(contract, "2")

    original_hash = question_content_sha256(question.model_dump(mode="json"))
    mutated = question.model_copy(deep=True)
    changed_intent = mutated.stimulus.sql_contract.intents["2"].model_copy(
        update={"minimum_count": 6}
    )
    mutated.stimulus = mutated.stimulus.model_copy(
        update={"sql_contract": mutated.stimulus.sql_contract.model_copy(
            update={"intents": {**mutated.stimulus.sql_contract.intents, "2": changed_intent}}
        )}
    )
    assert question_content_sha256(mutated.model_dump(mode="json")) != original_hash


@pytest.mark.parametrize(
    "mutation",
    ["schema-key", "threshold", "order", "target-row", "closed-analysis"],
)
def test_sql_source_intent_and_linked_closed_analysis_mutations_stale_review_identity(mutation):
    question = _sql_question()
    raw = question.model_dump(mode="json")
    changed = copy.deepcopy(raw)
    contract = changed["stimulus"]["sql_contract"]
    if mutation == "schema-key":
        contract["tables"][0]["primary_key"] = ["Email"]
    elif mutation == "threshold":
        contract["intents"]["2"]["minimum_count"] = 6
    elif mutation == "order":
        contract["intents"]["2"]["order"] = "ascending"
    elif mutation == "target-row":
        contract["intents"]["3"]["values"]["MemberID"]["value"] = 1901
    else:
        changed["parts"][3]["marking"]["closed_answers"]["first-booking"] = ["(1842,28)"]
    assert question_content_sha256(changed) != question_content_sha256(raw)


@pytest.mark.parametrize(
    "query",
    [
        "SELECT S.Activity, COUNT(*) FROM SESSION S JOIN BOOKING B ON S.SessionID = B.SessionID GROUP BY S.Activity HAVING COUNT(*) >= 5 ORDER BY COUNT(*) DESC;",
        "SELECT Activity, COUNT(B.MemberID) AS BookingCount FROM BOOKING AS B INNER JOIN SESSION AS S ON B.SessionID=S.SessionID GROUP BY Activity HAVING COUNT(B.MemberID)>4 ORDER BY BookingCount DESC",
        "SELECT S.Activity, COUNT(S.SessionID) FROM SESSION S, BOOKING B WHERE S.SessionID=B.SessionID GROUP BY S.Activity HAVING COUNT(S.SessionID) >= 5 ORDER BY COUNT(S.SessionID) DESC;",
    ],
)
def test_select_accepts_only_supported_alias_join_count_threshold_and_order_variants(query):
    contract, intent = _contract_and_intent("2")
    result = validate_sql_response(query, [query], contract, intent)
    assert result.passed
    assert result.version == SQL_VALIDATION_VERSION
    assert result.source_intent_sha256 == sql_source_intent_sha256(contract, intent)


def test_count_credit_uses_candidate_visible_nullability_only():
    contract, intent = _contract_and_intent("2")
    visible_non_null = (
        "SELECT S.Activity, COUNT(B.Attended) FROM SESSION S JOIN BOOKING B "
        "ON S.SessionID=B.SessionID GROUP BY S.Activity "
        "HAVING COUNT(B.Attended)>=5 ORDER BY COUNT(B.Attended) DESC"
    )
    visible_nullable = visible_non_null.replace("B.Attended", "B.BookedAt")

    assert validate_sql_response(
        visible_non_null, [visible_non_null], contract, intent
    ).passed
    rejected = validate_sql_response(
        visible_nullable, [visible_nullable], contract, intent
    )
    assert not rejected.passed
    assert {finding.code for finding in rejected.findings} == {"nullable-count"}


@pytest.mark.parametrize(
    "query,code",
    [
        ("SELECT S.Activity, COUNT(*) FROM SESSION S JOIN BOOKING B ON S.SessionID=B.SessionID GROUP BY S.StartsAt HAVING COUNT(*)>=5 ORDER BY COUNT(*) DESC", "wrong-group"),
        ("SELECT S.Activity, COUNT(*) FROM SESSION S JOIN BOOKING B ON S.SessionID=B.MemberID GROUP BY S.Activity HAVING COUNT(*)>=5 ORDER BY COUNT(*) DESC", "wrong-join"),
        ("SELECT S.Activity, COUNT(B.NoSuchField) FROM SESSION S JOIN BOOKING B ON S.SessionID=B.SessionID GROUP BY S.Activity HAVING COUNT(B.NoSuchField)>=5 ORDER BY COUNT(B.NoSuchField) DESC", "unknown-column"),
        ("SELECT S.Activity, COUNT(B.BookedAt) FROM SESSION S JOIN BOOKING B ON S.SessionID=B.SessionID GROUP BY S.Activity HAVING COUNT(B.BookedAt)>=5 ORDER BY COUNT(B.BookedAt) DESC", "nullable-count"),
        ("SELECT S.Activity, COUNT(*) FROM SESSION S JOIN BOOKING B ON S.SessionID=B.SessionID GROUP BY S.Activity HAVING COUNT(*)>=6 ORDER BY COUNT(*) DESC", "wrong-threshold"),
        ("SELECT S.Activity, COUNT(*) FROM SESSION S JOIN BOOKING B ON S.SessionID=B.SessionID GROUP BY S.Activity HAVING COUNT(*)>=5 ORDER BY COUNT(*) ASC", "wrong-order"),
        ("SELECT S.Activity, COUNT(B) FROM SESSION S JOIN BOOKING B ON S.SessionID=B.SessionID GROUP BY S.Activity HAVING COUNT(B)>=5 ORDER BY COUNT(B) DESC", "unsupported-whole-row-count"),
    ],
)
def test_select_rejects_wrong_group_join_identifier_count_predicate_or_order(query, code):
    contract, intent = _contract_and_intent("2")
    result = validate_sql_response(query, [query], contract, intent)
    assert not result.passed
    assert code in {finding.code for finding in result.findings}


@pytest.mark.parametrize(
    "query",
    [
        "SELECT DISTINCT S.Activity, COUNT(*) FROM SESSION S JOIN BOOKING B ON S.SessionID=B.SessionID GROUP BY S.Activity HAVING COUNT(*)>=5 ORDER BY COUNT(*) DESC",
        "SELECT S.Activity, COUNT(*), S.StartsAt FROM SESSION S JOIN BOOKING B ON S.SessionID=B.SessionID GROUP BY S.Activity HAVING COUNT(*)>=5 ORDER BY COUNT(*) DESC",
        "SELECT S.Activity, COUNT(*) FROM SESSION S, BOOKING B GROUP BY S.Activity HAVING COUNT(*)>=5 ORDER BY COUNT(*) DESC",
        "SELECT S.Activity, COUNT(*) FROM SESSION S JOIN BOOKING B ON S.SessionID=B.SessionID GROUP BY S.Activity HAVING COUNT(DISTINCT B.MemberID)>=5 ORDER BY COUNT(*) DESC",
    ],
)
def test_select_rejects_distinct_extra_projection_and_missing_or_changed_join(query):
    contract, intent = _contract_and_intent("2")
    assert not validate_sql_response(query, [query], contract, intent).passed


@pytest.mark.parametrize(
    "query",
    [
        "SELECT S.Activity, COUNT(*) FROM SESSION S JOIN BOOKING B ON S.SessionID=B.SessionID GROUP BY S.Activity HAVING COUNT(*)>=5 ORDER BY COUNT(*) DESC; DROP TABLE MEMBER;",
        "SELECT S.Activity, COUNT(*) FROM SESSION S JOIN BOOKING B ON S.SessionID=B.SessionID GROUP BY S.Activity HAVING COUNT(*)>=5 ORDER BY COUNT(*) DESC nonsense",
        "SELECT S.Activity, COUNT(*) FROM SESSION S JOIN BOOKING B ON S.SessionID=B.SessionID GROUP BY S.Activity HAVING COUNT(*)>=5 ORDER BY COUNT(*) DESC /* trailing */",
        "This is not SQL.",
        "SELECT S.Activity, COUNT(*) FROM SESSION S JOIN BOOKING B ON S.SessionID=B.SessionID GROUP BY S.Activity HAVING COUNT(*)>=5 ORDER BY COUNT(*) DESC)"
    ],
)
def test_parser_consumes_the_whole_bounded_input_and_rejects_suffixes(query):
    contract, intent = _contract_and_intent("2")
    result = validate_sql_response(query, [query], contract, intent)
    assert not result.passed


@pytest.mark.parametrize(
    "query",
    [
        "INSERT INTO MEMBER (MemberID, FullName, Email) VALUES (1900, 'Amira Khan', 'amira@example.org');",
        "insert into member (Email, MemberID, FullName) values ('amira@example.org', 1900, 'Amira Khan')",
        "INSERT INTO MEMBER (FullName, Email, MemberID) VALUES ('Amira Khan', 'amira@example.org', 1900);",
        "INSERT INTO MEMBER VALUES (1900, 'Amira Khan', 'amira@example.org');",
    ],
)
def test_insert_accepts_reordered_columns_and_preserves_literal_values(query):
    contract, intent = _contract_and_intent("3")
    assert validate_sql_response(query, [query], contract, intent).passed


@pytest.mark.parametrize(
    "query,code",
    [
        ("INSERT INTO BOOKING (MemberID, SessionID, Attended) VALUES (1900, 27, 'TRUE')", "wrong-target"),
        ("INSERT INTO MEMBER (MemberID, FullName, Email) VALUES (1901, 'Amira Khan', 'amira@example.org')", "wrong-literal"),
        ("INSERT INTO MEMBER (MemberID, FullName, Email) VALUES (1842, 'Amira Khan', 'amira@example.org')", "wrong-literal"),
        ("INSERT INTO MEMBER (MemberID, FullName, Email) VALUES (1900, 'amira khan', 'amira@example.org')", "wrong-literal"),
        ("INSERT INTO MEMBER (MemberID, FullName, Email) VALUES (1900, 'Amira Khan', 'AMIRA@example.org')", "wrong-literal"),
        ("INSERT INTO MEMBER (MemberID, FullName) VALUES (1900, 'Amira Khan')", "column-map"),
        ("INSERT INTO MEMBER (MemberID, FullName, Email) VALUES (1900, 'Amira Khan', 'amira@example.org'); SELECT 1", "trailing-input"),
    ],
)
def test_insert_rejects_wrong_target_map_literals_and_incomplete_or_extra_input(query, code):
    contract, intent = _contract_and_intent("3")
    result = validate_sql_response(query, [query], contract, intent)
    assert not result.passed
    assert code in {finding.code for finding in result.findings}


@pytest.mark.parametrize(
    "query",
    [
        "INSERT INTO MEMBER (MemberID, FullName, Email) VALUES (1900, 'Amira Khan', 'amira@example.org'), (1901, 'Other', 'other@example.org')",
        "UPDATE MEMBER SET FullName = 'Amira Khan' WHERE MemberID = 1900",
        "DELETE FROM MEMBER WHERE MemberID = 1900",
        "INSERT INTO MEMBER (MemberID, FullName, Email) VALUES (1900, 'Amira Khan', 'amira@example.org'",
        "INSERT INTO MEMBER (MemberID, FullName, Email) VALUES (1900, 'Amira Kh''an', 'amira@example.org')",
    ],
)
def test_insert_rejects_extra_rows_substituted_statements_and_incomplete_or_changed_escaping(query):
    contract, intent = _contract_and_intent("3")
    assert not validate_sql_response(query, [query], contract, intent).passed


def test_answer_and_each_full_sql_mark_point_are_validated_without_overwrite():
    contract, intent = _contract_and_intent("2")
    valid = "SELECT S.Activity, COUNT(*) FROM SESSION S JOIN BOOKING B ON S.SessionID=B.SessionID GROUP BY S.Activity HAVING COUNT(*)>=5 ORDER BY COUNT(*) DESC"
    wrong = valid.replace("S.Activity HAVING", "S.StartsAt HAVING")
    assert not validate_sql_response(wrong, [valid], contract, intent).passed
    assert not validate_sql_response(valid, [wrong], contract, intent).passed
    assert not validate_sql_response(wrong, [wrong], contract, intent).passed
    assert validate_sql_response(valid, ["Join the declared tables.", valid], contract, intent).passed


@pytest.mark.parametrize(
    "bad_point",
    [
        "DELETE FROM MEMBER; {valid}",
        "DELETE FROM MEMBER",
        "UPDATE MEMBER SET FullName = 'Other' WHERE MemberID = 1900",
        "DROP TABLE MEMBER",
        "WITH ignored AS note {valid}",
        "{valid}; {valid}",
    ],
)
def test_every_executable_looking_mark_point_is_validated_without_prefix_discard(
    bad_point,
):
    contract, intent = _contract_and_intent("2")
    valid = (
        "SELECT S.Activity, COUNT(*) FROM SESSION S JOIN BOOKING B "
        "ON S.SessionID=B.SessionID GROUP BY S.Activity "
        "HAVING COUNT(*)>=5 ORDER BY COUNT(*) DESC"
    )

    result = validate_sql_response(
        valid, [bad_point.format(valid=valid)], contract, intent
    )

    assert not result.passed
    assert {finding.location for finding in result.findings} == {"mark_points[1]"}


@pytest.mark.parametrize("wrapper", ["SQL: {valid}", "Query:\n{valid}", "```sql\n{valid}\n```"])
def test_only_bounded_non_executable_labels_or_fences_may_wrap_a_mark_point(
    wrapper,
):
    contract, intent = _contract_and_intent("2")
    valid = (
        "SELECT S.Activity, COUNT(*) FROM SESSION S JOIN BOOKING B "
        "ON S.SessionID=B.SessionID GROUP BY S.Activity "
        "HAVING COUNT(*)>=5 ORDER BY COUNT(*) DESC"
    )
    assert validate_sql_response(
        valid, [wrapper.format(valid=valid)], contract, intent
    ).passed


@pytest.mark.parametrize(
    "bad_point",
    [
        "Answer:\n```sql\nDELETE FROM MEMBER\n```",
        "SQL: ```sql\nDELETE FROM MEMBER\n```",
        "Query:\n```sql\nUPDATE MEMBER SET FullName = 'Other' WHERE MemberID = 1900\n```",
        "ANSWER: ```sql\nDROP TABLE MEMBER\n```",
        "SQL:\n```sql\nWITH ignored AS note {valid}\n```",
        "QUERY: ```sql\n{valid}; DELETE FROM MEMBER\n```",
    ],
)
def test_label_plus_one_fence_never_hides_wrong_or_multiple_sql(bad_point):
    contract, intent = _contract_and_intent("2")
    valid = (
        "SELECT S.Activity, COUNT(*) FROM SESSION S JOIN BOOKING B "
        "ON S.SessionID=B.SessionID GROUP BY S.Activity "
        "HAVING COUNT(*)>=5 ORDER BY COUNT(*) DESC"
    )

    result = validate_sql_response(
        valid, [bad_point.format(valid=valid)], contract, intent
    )

    assert not result.passed
    assert {finding.location for finding in result.findings} == {"mark_points[1]"}


@pytest.mark.parametrize(
    "bad_point",
    [
        "SQL: SELECT Activity",
        "```sql\nSELECT Activity\n```",
        "Answer:\n```sql\nSELECT Activity\n```",
        "Query: INSERT INTO MEMBER",
        "```sql\nWITH x AS (VALUES (1))\n```",
    ],
)
def test_explicit_sql_wrapper_never_hides_an_incomplete_statement(bad_point):
    contract, intent = _contract_and_intent("2")
    valid = (
        "SELECT S.Activity, COUNT(*) FROM SESSION S JOIN BOOKING B "
        "ON S.SessionID=B.SessionID GROUP BY S.Activity "
        "HAVING COUNT(*)>=5 ORDER BY COUNT(*) DESC"
    )

    result = validate_sql_response(valid, [bad_point], contract, intent)

    assert not result.passed
    assert {finding.location for finding in result.findings} == {"mark_points[1]"}


@pytest.mark.parametrize(
    "prose",
    [
        "Select the Activity and number of bookings.",
        "Insert the supplied member values into MEMBER.",
    ],
)
def test_natural_language_sql_imperatives_remain_semantic_prose(prose):
    contract, intent = _contract_and_intent("2")
    valid = (
        "SELECT S.Activity, COUNT(*) FROM SESSION S JOIN BOOKING B "
        "ON S.SessionID=B.SessionID GROUP BY S.Activity "
        "HAVING COUNT(*)>=5 ORDER BY COUNT(*) DESC"
    )

    assert validate_sql_response(valid, [prose], contract, intent).passed


def test_select_rejects_count_alias_collision_with_projected_output_name():
    contract, intent = _contract_and_intent("2")
    ambiguous = (
        "SELECT S.Activity, COUNT(*) AS Activity FROM SESSION S JOIN BOOKING B "
        "ON S.SessionID=B.SessionID GROUP BY S.Activity "
        "HAVING COUNT(*)>=5 ORDER BY Activity DESC"
    )
    unambiguous = ambiguous.replace("AS Activity", "AS BookingCount").replace(
        "ORDER BY Activity", "ORDER BY BookingCount"
    )

    result = validate_sql_response(ambiguous, [ambiguous], contract, intent)
    assert not result.passed
    assert {finding.code for finding in result.findings} == {"ambiguous-alias"}
    assert validate_sql_response(unambiguous, [unambiguous], contract, intent).passed


@pytest.mark.parametrize(
    "mutation",
    ["projection", "group", "sources", "join"],
)
def test_real_solver_projection_rejects_mutated_select_contract_relationships(
    mutation,
):
    question = _sql_question()
    contract = question.stimulus.sql_contract
    intent = contract.intents["2"]
    if mutation == "projection":
        changed_intent = intent.model_copy(update={"projection_field": "SESSION.StartsAt"})
        changed_contract = contract.model_copy(
            update={"intents": {**contract.intents, "2": changed_intent}}
        )
    elif mutation == "group":
        changed_intent = intent.model_copy(update={"group_field": "SESSION.StartsAt"})
        changed_contract = contract.model_copy(
            update={"intents": {**contract.intents, "2": changed_intent}}
        )
    elif mutation == "sources":
        changed_intent = intent.model_copy(update={"source_tables": ["SESSION", "MEMBER"]})
        changed_contract = contract.model_copy(
            update={"intents": {**contract.intents, "2": changed_intent}}
        )
    else:
        changed_contract = contract.model_copy(update={"joins": []})
    changed_question = question.model_copy(
        update={
            "stimulus": question.stimulus.model_copy(
                update={"sql_contract": changed_contract}
            )
        }
    )

    with pytest.raises(ValueError, match="public SQL"):
        _part_solver_projection(changed_question, question.parts[1])


def test_raw_select_contract_requires_the_exact_supported_v1_relationship():
    contract, _ = _contract_and_intent("2")
    raw = contract.model_dump(mode="json")
    raw["intents"]["2"]["projection_field"] = "SESSION.StartsAt"

    with pytest.raises(ValueError, match="SELECT intent"):
        SQLSourceContract.model_validate(raw, strict=True)


def test_projection_rejects_source_intent_mutation_and_blind_prompt_has_no_private_query():
    question = _sql_question()
    projection = _part_solver_projection(question, question.parts[1])
    contract = question.stimulus.sql_contract
    changed_intent = contract.intents["2"].model_copy(update={"minimum_count": 6})
    changed_contract = contract.model_copy(
        update={"intents": {**contract.intents, "2": changed_intent}}
    )
    changed_question = question.model_copy(
        update={"stimulus": question.stimulus.model_copy(
            update={"sql_contract": changed_contract}
        )}
    )
    with pytest.raises(ValueError, match="public SQL"):
        _part_solver_projection(changed_question, question.parts[1])

    valid = "SELECT S.Activity, COUNT(*) FROM SESSION S JOIN BOOKING B ON S.SessionID=B.SessionID GROUP BY S.Activity HAVING COUNT(*)>=5 ORDER BY COUNT(*) DESC"
    client = Replay([_response(valid, projection.evidence[0].id)])
    solution = _solve_part_with_sql_validation(client, projection)
    payload = json.loads(client.prompts[0].split("\n", 1)[1])
    assert payload["item"]["stimulus"] == json.loads(payload["sources"][0]["text"])
    assert "marking" not in payload["item"]
    assert "worked exemplar" not in client.prompts[0].casefold()
    assert valid not in payload["item"]["authoring_context"]["sql_answer_contract"].values()
    assert solution.solution_source == "independent-model"
    assert solution.verified_scope == "bounded-declarative-sql"
    assert solution.program_validation_version == SQL_VALIDATION_VERSION
    assert solution.program_validation_scope == "bounded-declarative-sql"
    assert solution.source_intent_sha256 == sql_source_intent_sha256(question.stimulus.sql_contract, "2")


def test_one_structured_solver_correction_preserves_first_failure_and_stops_if_still_wrong():
    question = _sql_question()
    projection = _part_solver_projection(question, question.parts[1])
    source_id = projection.evidence[0].id
    wrong = "SELECT BOOKING.NoSuchField FROM BOOKING"
    valid = "SELECT S.Activity, COUNT(*) FROM SESSION S JOIN BOOKING B ON S.SessionID=B.SessionID GROUP BY S.Activity HAVING COUNT(*)>=5 ORDER BY COUNT(*) DESC"
    client = Replay([_response(wrong, source_id), _response(valid, source_id)])
    solution = _solve_part_with_sql_validation(client, projection)

    assert len(client.prompts) == 2
    assert solution.program_first_failure is not None
    assert solution.program_first_failure.answer == wrong
    assert solution.program_first_failure.mark_points == [wrong]
    assert solution.program_first_failure.evidence_ids == [source_id]
    assert not solution.program_first_failure.validation_result.passed
    assert (
        solution.program_first_failure.validation_result.source_intent_sha256
        == sql_source_intent_sha256(projection.sql_contract, projection.sql_intent_id)
    )
    assert solution.program_first_failure.validation_result.findings
    assert {
        finding.location
        for finding in solution.program_first_failure.validation_result.findings
    } == {"answer", "mark_points[1]"}
    assert "program_first_failure" not in _difficulty_solution(solution)
    assert "SQL_VALIDATION_FINDINGS=" in client.prompts[1]
    assert wrong not in client.prompts[1]
    assert valid not in client.prompts[1].split("SQL_VALIDATION_FINDINGS=", 1)[1].split("\n", 1)[0]
    assert json.loads(client.prompts[0].split("\n", 1)[1])["sources"] == json.loads(client.prompts[1].split("\n", 1)[1])["sources"]

    failed = Replay([_response(wrong, source_id), _response("Still not SQL", source_id)])
    with pytest.raises(
        SQLProgramValidationError,
        match="failed bounded SQL verification after one correction",
    ) as captured:
        _solve_part_with_sql_validation(failed, projection)
    assert len(failed.prompts) == 2
    assert captured.value.first_attempt.answer == wrong
    assert captured.value.replacement_attempt.answer == "Still not SQL"


def test_actual_captured_count_table_response_is_unsupported_not_silently_accepted():
    question = _sql_question()
    projection = _part_solver_projection(question, question.parts[1])
    direct = validate_sql_response(
        CAPTURED_COUNT_BOOKING_RESPONSE["answer"],
        CAPTURED_COUNT_BOOKING_RESPONSE["mark_points"],
        projection.sql_contract,
        projection.sql_intent_id,
    )
    assert any(
        finding.code == "unsupported-whole-row-count"
        and finding.classification == "unsupported"
        for finding in direct.findings
    )
    client = Replay([
        CAPTURED_COUNT_BOOKING_RESPONSE,
        CAPTURED_COUNT_BOOKING_RESPONSE,
    ])
    with pytest.raises(ValueError, match="unsupported-whole-row-count"):
        _solve_part_with_sql_validation(client, projection)
    assert len(client.prompts) == 2


@pytest.mark.parametrize("failure", ["unknown-field", "non-sql", "disagreeing-fields"])
def test_real_difficulty_adapter_rejects_sql_failures_before_difficulty(monkeypatch, failure):
    question = _sql_question()
    part = question.parts[1]
    projection = _part_solver_projection(question, part)
    source_id = projection.evidence[0].id
    valid = "SELECT S.Activity, COUNT(*) FROM SESSION S JOIN BOOKING B ON S.SessionID=B.SessionID GROUP BY S.Activity HAVING COUNT(*)>=5 ORDER BY COUNT(*) DESC"
    if failure == "unknown-field":
        answer, points = "SELECT BOOKING.NoSuchField FROM BOOKING", None
    elif failure == "non-sql":
        answer, points = "There are at least five bookings.", None
    else:
        answer, points = valid, [valid.replace("COUNT(*)>=5", "COUNT(*)>=6")]
    client = Replay([
        _response(answer, source_id, points=points),
        _response(answer, source_id, points=points),
    ])
    reached_difficulty = []
    monkeypatch.setattr(
        subject,
        "require_difficulty_review",
        lambda *_args, **_kwargs: reached_difficulty.append(True),
    )
    one_part = question.model_copy(update={"parts": [part]})
    blueprint = build_paper2_blueprint(load_syllabus(), seed=26083134).model_copy(
        update={"questions": [one_part]}
    )

    with pytest.raises(ValueError, match="after one correction"):
        subject.review_blueprint_difficulty(client, blueprint, load_syllabus())
    assert not reached_difficulty
    assert len(client.prompts) == 2


def _difficulty_payload(target, *, operations):
    return {
        "approved": True,
        "estimated_demand": target.demand_band,
        "reasoning_steps": target.minimum_reasoning_steps,
        "tariff_fit": True,
        "command_word_fit": True,
        "context_fit": True,
        "profile_fit": True,
        "observed_cognitive_operations": operations,
        "cognitive_operations_fit": True,
        "reasoning_range_fit": True,
        "shortcut_resistant": True,
        "timing_fit": True,
        "scaffolding_fit": True,
        "estimated_minutes": target.expected_minutes_min,
        "issues": [],
    }


class LiteralTaskFactAwareClient:
    def __init__(self, solver_response, target, statement_kind: str):
        self.solver_response = solver_response
        self.target = target
        self.statement_kind = statement_kind
        self.prompts: list[str] = []

    def generate_json(self, prompt: str):
        self.prompts.append(prompt)
        if "difficulty calibration specialist" not in prompt:
            return copy.deepcopy(self.solver_response)
        has_literal_fact = (
            '"candidate_authors_declarative_sql": true' in prompt
            and (
                '"declarative_sql_statement_kind": '
                f'"{self.statement_kind}"'
            )
            in prompt
        )
        operations = list(self.target.required_cognitive_operations)
        if not has_literal_fact:
            operations.remove("program")
        return _difficulty_payload(self.target, operations=operations)


@pytest.mark.parametrize(
    ("part_index", "statement_kind", "answer"),
    [
        (
            1,
            "SELECT",
            "SELECT S.Activity, COUNT(*) FROM SESSION S JOIN BOOKING B "
            "ON S.SessionID=B.SessionID GROUP BY S.Activity "
            "HAVING COUNT(*)>=5 ORDER BY COUNT(*) DESC",
        ),
        (
            2,
            "INSERT",
            "INSERT INTO MEMBER (MemberID, FullName, Email) "
            "VALUES (1900, 'Amira Khan', 'amira@example.org')",
        ),
    ],
)
def test_real_pipeline_exposes_literal_declarative_sql_construction_to_judge(
    part_index, statement_kind, answer
):
    question = _sql_question()
    part = question.parts[part_index]
    target = build_item_demand_target(
        subject._part_demand_item(question, part),
        profile_for("aqa/computer-science", "2"),
    )
    projection = _part_solver_projection(question, part)
    client = LiteralTaskFactAwareClient(
        _response(answer, projection.evidence[0].id),
        target,
        statement_kind,
    )
    one_part = question.model_copy(update={"parts": [part]})
    blueprint = build_paper2_blueprint(load_syllabus(), seed=26083134).model_copy(
        update={"questions": [one_part]}
    )

    reviewed = subject.review_blueprint_difficulty(client, blueprint, load_syllabus())

    evidence = reviewed.questions[0].parts[0].difficulty_evidence
    assert "program" in evidence["observed_cognitive_operations"]
    assert len(client.prompts) == 2
    difficulty_prompt = client.prompts[1]
    assert "LITERAL_CANDIDATE_TASK_FACTS=" in difficulty_prompt
    assert '"candidate_authors_declarative_sql": true' in difficulty_prompt
    assert f'"declarative_sql_statement_kind": "{statement_kind}"' in difficulty_prompt


def test_demand_guidance_balances_declarative_construction_and_supplied_query_analysis():
    question = _sql_question()
    select_part = question.parts[1]
    select_target = build_item_demand_target(
        subject._part_demand_item(question, select_part),
        profile_for("aqa/computer-science", "2"),
    )
    assert "program" in select_target.required_cognitive_operations
    missing_program = Replay([_difficulty_payload(select_target, operations=["apply"])])
    with pytest.raises(ValueError, match="missing required cognitive operations: program"):
        require_difficulty_review(
            missing_program,
            item_id="sql-select",
            subject="AQA A-level Computer Science",
            target=select_target,
            candidate={},
            specification={},
        )
    prompt = missing_program.prompts[0]
    assert "declarative SQL SELECT or INSERT" in prompt
    assert "already supplied SQL statement is not automatically programming" in prompt

    correct = Replay([_difficulty_payload(select_target, operations=["program", "apply"])])
    assert require_difficulty_review(
        correct,
        item_id="sql-select",
        subject="AQA A-level Computer Science",
        target=select_target,
        candidate={},
        specification={},
    ).approved

    supplied_part = question.parts[0]
    supplied_target = build_item_demand_target(
        subject._part_demand_item(question, supplied_part),
        profile_for("aqa/computer-science", "2"),
    )
    assert supplied_target.required_cognitive_operations == ["analyse"]
    assert "program" not in supplied_target.required_cognitive_operations
