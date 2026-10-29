import pytest

from Backend.Core.topic_task_contract import derive_task_semantics


@pytest.mark.parametrize(
    "prompt",
    [
        "Write a Python program using selection.",
        "Write a function to select the largest value in a list.",
        "Write code to return the preselected item.",
        "Write a Python function named select_student.",
        "Write a Python function to select records from a list.",
    ],
)
def test_ordinary_programming_selection_is_not_a_sql_query(prompt):
    assert derive_task_semantics(task_operation="program", prompt=prompt) == (
        "program",
        "code",
    )


@pytest.mark.parametrize(
    "prompt",
    [
        "Write one SELECT query for this relational database.",
        "Write an SQL query to retrieve the student names.",
        "Complete the statement: SELECT Name FROM STUDENT WHERE Year = 12;",
        "Complete the statement: select Name from STUDENT where Year = 12;",
    ],
)
def test_explicit_sql_remains_a_query_response(prompt):
    assert derive_task_semantics(task_operation="program", prompt=prompt) == (
        "program",
        "query",
    )


@pytest.mark.parametrize(
    "prompt",
    [
        "Write an SQL statement to insert the new student.",
        "Write an SQL UPDATE statement to change the value.",
        "Write one INSERT statement to add the booking.",
        "Write one UPDATE statement to change the booking.",
    ],
)
def test_sql_modification_statements_keep_their_existing_code_response_mode(prompt):
    assert derive_task_semantics(task_operation="program", prompt=prompt) == (
        "program",
        "code",
    )


def test_explicit_response_slots_and_options_keep_their_precedence():
    prompt = "Select the SQL query."
    assert derive_task_semantics(
        task_operation="program", prompt=prompt, options=["A", "B"]
    ) == ("program", "selected")
    assert derive_task_semantics(
        task_operation="program", prompt=prompt, response_slots=["answer"]
    ) == ("program", "result")
