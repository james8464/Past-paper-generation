"""Owned declarative SQL parser controls; no database or model execution."""

import pytest

from Backend.Core.subjects.sql_contracts import (
    SQL_VALIDATION_VERSION,
    fitness_centre_sql_contract,
    sql_source_intent_sha256,
    validate_sql_response,
)


def query(alias="BookingCount", *, explicit_as=True, order=None, count="COUNT(*)"):
    declaration = f"{'AS ' if explicit_as else ''}{alias}" if alias else ""
    return (
        f"SELECT S.Activity, {count} {declaration} FROM SESSION S JOIN BOOKING B "
        "ON S.SessionID=B.SessionID GROUP BY S.Activity HAVING COUNT(*)>=5 "
        f"ORDER BY {alias if order is None else order} DESC"
    )


@pytest.mark.parametrize("alias", ["Count", "count", "COUNT"])
@pytest.mark.parametrize("order", ["Count", "count", "COUNT"])
@pytest.mark.parametrize("explicit_as", [False, True])
def test_count_named_output_alias_is_not_a_function_call(alias, order, explicit_as):
    contract = fitness_centre_sql_contract()
    statement = query(alias, explicit_as=explicit_as, order=order)
    original = contract.model_dump(mode="json")
    result = validate_sql_response(statement, [statement], contract, "2")
    assert result.passed and not result.findings
    assert result.version == SQL_VALIDATION_VERSION == "aqa-candidate-sql-v4"
    assert result.source_intent_sha256 == sql_source_intent_sha256(contract, "2")
    assert (
        result.source_intent_sha256
        == "fcbfce91b6c6b4cce13dcf7bf47e5ac0fcaafbf215898f1bc61dd2345ecef18b"
    )
    assert contract.model_dump(mode="json") == original


@pytest.mark.parametrize("explicit_as", [False, True])
def test_existing_booking_count_alias_control_is_unchanged(explicit_as):
    contract = fitness_centre_sql_contract()
    statement = query(explicit_as=explicit_as)
    assert validate_sql_response(statement, [statement], contract, "2").passed


@pytest.mark.parametrize("aggregate", ["COUNT(*)", "count ( * )", "COUNT(B.MemberID)"])
def test_actual_count_calls_still_take_the_function_path(aggregate):
    contract = fitness_centre_sql_contract()
    statement = query("Count", order=aggregate)
    assert validate_sql_response(statement, [statement], contract, "2").passed


@pytest.mark.parametrize(
    "statement",
    [
        query("Count", order="COUNT()"),
        query("Count", order="COUNT("),
        query("Count", order="COUNT(*) extra"),
        query("Count", order="COUNT(B.NoSuchField)"),
        query("Count", order="COUNT(B.BookedAt)"),
        query("Count", order="SUM(*)"),
        query("Count", order="OtherAlias"),
        query("", order="Count"),
        query("Activity", order="Activity"),
        query("Count").replace(" DESC", " ASC"),
        query("Count").replace("COUNT(*)>=5", "COUNT(*)>=6"),
        query("Count", count="COUNT(B.BookedAt)"),
        query("Count") + "; DELETE FROM MEMBER;",
        query("Count") + " /* unsupported comment */",
    ],
)
def test_alias_disambiguation_does_not_accept_wrong_or_unsupported_sql(statement):
    contract = fitness_centre_sql_contract()
    result = validate_sql_response(statement, [], contract, "2")
    assert not result.passed and result.findings


@pytest.mark.parametrize("suffix", [" " * 2001, " token" * 257, "(" * 9])
def test_existing_sql_resource_admission_bounds_remain(suffix):
    result = validate_sql_response(
        query("Count") + suffix, [], fitness_centre_sql_contract(), "2"
    )
    assert not result.passed
    assert result.findings[0].code == "input-limit"


def test_count_alias_mark_point_is_validated_without_dropping_its_suffix():
    contract = fitness_centre_sql_contract()
    answer = query("Count")
    result = validate_sql_response(
        answer, [answer + "; DROP TABLE MEMBER"], contract, "2"
    )
    assert not result.passed
    assert {finding.location for finding in result.findings} == {"mark_points[1]"}
