"""Bounded, candidate-grounded SQL verification for the declared AQA tasks.

This module parses a deliberately small SELECT/INSERT subset.  It never executes
SQL and does not claim that unsupported syntax is invalid in every SQL dialect.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SQL_VALIDATION_VERSION = "aqa-candidate-sql-v3"
SQL_VERIFIED_SCOPE = "bounded-declarative-sql"
_MAX_SQL_LENGTH = 2_000
_MAX_SQL_TOKENS = 256
_MAX_PARENTHESES = 8


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class SQLColumnContract(_Frozen):
    name: str = Field(min_length=1)
    nullable: bool
    primary_key: bool = False
    foreign_key: str | None = None


class SQLTableContract(_Frozen):
    name: str = Field(min_length=1)
    columns: list[SQLColumnContract] = Field(min_length=1)
    primary_key: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_columns(self) -> SQLTableContract:
        names = [column.name.casefold() for column in self.columns]
        if len(names) != len(set(names)):
            raise ValueError("SQL table column names must be unique")
        if not {name.casefold() for name in self.primary_key}.issubset(names):
            raise ValueError("SQL primary key must use declared columns")
        return self


class SQLJoinContract(_Frozen):
    left_table: str
    left_column: str
    right_table: str
    right_column: str


class SQLSelectIntent(_Frozen):
    kind: Literal["select-group-count"] = "select-group-count"
    source_tables: list[str] = Field(min_length=2, max_length=2)
    projection_field: str
    group_field: str
    minimum_count: int = Field(gt=0)
    order: Literal["descending"] = "descending"


class SQLLiteralContract(_Frozen):
    kind: Literal["integer", "text"]
    value: int | str

    @model_validator(mode="after")
    def matching_value_type(self) -> SQLLiteralContract:
        if self.kind == "integer" and (not isinstance(self.value, int) or isinstance(self.value, bool)):
            raise ValueError("integer SQL literal requires an integer value")
        if self.kind == "text" and not isinstance(self.value, str):
            raise ValueError("text SQL literal requires a string value")
        return self


class SQLInsertIntent(_Frozen):
    kind: Literal["insert-row"] = "insert-row"
    target_table: str
    values: dict[str, SQLLiteralContract]


class SQLSampleTableContract(_Frozen):
    table: str
    columns: list[str] = Field(min_length=1)
    rows: list[list[int | str | bool]] = Field(min_length=1)

    @model_validator(mode="after")
    def rectangular_rows(self) -> SQLSampleTableContract:
        if len({name.casefold() for name in self.columns}) != len(self.columns):
            raise ValueError("SQL sample columns must be unique")
        if any(len(row) != len(self.columns) for row in self.rows):
            raise ValueError("SQL sample rows must match their visible columns")
        return self


class SQLSourceContract(_Frozen):
    version: Literal[SQL_VALIDATION_VERSION] = SQL_VALIDATION_VERSION
    source_id: str = Field(min_length=1)
    tables: list[SQLTableContract] = Field(min_length=1)
    joins: list[SQLJoinContract] = Field(default_factory=list)
    intents: dict[str, SQLSelectIntent | SQLInsertIntent]
    sample_tables: list[SQLSampleTableContract] = Field(default_factory=list)

    @model_validator(mode="after")
    def coherent_schema_and_intents(self) -> SQLSourceContract:
        tables = {table.name.casefold(): table for table in self.tables}
        if len(tables) != len(self.tables):
            raise ValueError("SQL table names must be unique")
        for join in self.joins:
            left = _contract_column(tables, join.left_table, join.left_column)
            right = _contract_column(tables, join.right_table, join.right_column)
            left_target = f"{join.right_table}.{join.right_column}".casefold()
            right_target = f"{join.left_table}.{join.left_column}".casefold()
            if not (
                (left.foreign_key or "").casefold() == left_target
                or (right.foreign_key or "").casefold() == right_target
            ):
                raise ValueError("SQL join must follow a candidate-visible foreign key")
        for table in self.tables:
            primary_key = {name.casefold() for name in table.primary_key}
            for column in table.columns:
                if column.primary_key != (column.name.casefold() in primary_key):
                    raise ValueError("SQL primary-key field metadata is inconsistent")
                if column.primary_key and column.nullable:
                    raise ValueError("SQL primary-key columns cannot be nullable")
                if column.foreign_key:
                    try:
                        target_table, target_column = column.foreign_key.split(".", 1)
                    except ValueError as error:
                        raise ValueError("SQL foreign key must name table.column") from error
                    target = _contract_column(tables, target_table, target_column)
                    if not target.primary_key:
                        raise ValueError("SQL foreign key must reference a declared key")
        sample_names = [sample.table.casefold() for sample in self.sample_tables]
        if len(sample_names) != len(set(sample_names)):
            raise ValueError("SQL sample tables must be unique")
        for sample in self.sample_tables:
            table = tables.get(sample.table.casefold())
            if table is None:
                raise ValueError("SQL sample rows use an unknown table")
            declared_columns = {column.name.casefold() for column in table.columns}
            if not {name.casefold() for name in sample.columns}.issubset(
                declared_columns
            ):
                raise ValueError("SQL sample rows use missing or unknown columns")
        if not self.intents or any(not label.strip() for label in self.intents):
            raise ValueError("SQL intents require non-empty part labels")
        for intent in self.intents.values():
            if isinstance(intent, SQLSelectIntent):
                _validate_supported_select_intent(intent, tables, self.joins)
            else:
                table = tables.get(intent.target_table.casefold())
                if table is None:
                    raise ValueError("SQL INSERT intent uses an unknown table")
                columns = {column.name.casefold() for column in table.columns}
                if {name.casefold() for name in intent.values} != columns:
                    raise ValueError("SQL INSERT intent must bind every target column")
        return self


class SQLValidationFinding(_Frozen):
    code: str
    message: str
    location: str
    classification: Literal["invalid", "unsupported"] = "invalid"


class SQLValidationResult(_Frozen):
    passed: bool
    version: Literal[SQL_VALIDATION_VERSION] = SQL_VALIDATION_VERSION
    verified_scope: Literal[SQL_VERIFIED_SCOPE] = SQL_VERIFIED_SCOPE
    source_intent_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    findings: list[SQLValidationFinding] = Field(default_factory=list)


def _validate_supported_select_intent(
    intent: SQLSelectIntent,
    tables: dict[str, SQLTableContract],
    joins: list[SQLJoinContract],
) -> None:
    """Fail closed when the public declaration leaves the bounded v2 task."""
    for field_name in (intent.projection_field, intent.group_field):
        try:
            table_name, column_name = field_name.split(".", 1)
        except ValueError as error:
            raise ValueError("SQL SELECT intent fields must name table.column") from error
        _contract_column(tables, table_name, column_name)
    expected_join = frozenset(
        {("session", "sessionid"), ("booking", "sessionid")}
    )
    declared_joins = {
        frozenset(
            {
                (join.left_table.casefold(), join.left_column.casefold()),
                (join.right_table.casefold(), join.right_column.casefold()),
            }
        )
        for join in joins
    }
    if (
        [table.casefold() for table in intent.source_tables]
        != ["session", "booking"]
        or intent.projection_field.casefold() != "session.activity"
        or intent.group_field.casefold() != "session.activity"
        or intent.minimum_count != 5
        or intent.order != "descending"
        or declared_joins != {expected_join}
    ):
        raise ValueError(
            "SQL SELECT intent must use the exact supported v2 "
            "SESSION.Activity grouping and SESSION/BOOKING join"
        )


def fitness_centre_sql_contract() -> SQLSourceContract:
    """Return the public schema and the two declared construction intents."""
    return SQLSourceContract(
        source_id="aqa-7517-fitness-centre-schema-v1",
        tables=[
            SQLTableContract(
                name="MEMBER",
                columns=[
                    SQLColumnContract(name="MemberID", nullable=False, primary_key=True),
                    SQLColumnContract(name="FullName", nullable=False),
                    SQLColumnContract(name="Email", nullable=True),
                ],
                primary_key=["MemberID"],
            ),
            SQLTableContract(
                name="SESSION",
                columns=[
                    SQLColumnContract(name="SessionID", nullable=False, primary_key=True),
                    SQLColumnContract(name="Activity", nullable=False),
                    SQLColumnContract(name="StartsAt", nullable=False),
                    SQLColumnContract(name="Capacity", nullable=False),
                ],
                primary_key=["SessionID"],
            ),
            SQLTableContract(
                name="BOOKING",
                columns=[
                    SQLColumnContract(
                        name="MemberID", nullable=False, primary_key=True,
                        foreign_key="MEMBER.MemberID",
                    ),
                    SQLColumnContract(
                        name="SessionID", nullable=False, primary_key=True,
                        foreign_key="SESSION.SessionID",
                    ),
                    SQLColumnContract(name="BookedAt", nullable=True),
                    SQLColumnContract(name="Attended", nullable=False),
                ],
                primary_key=["MemberID", "SessionID"],
            ),
        ],
        joins=[SQLJoinContract(
            left_table="SESSION", left_column="SessionID",
            right_table="BOOKING", right_column="SessionID",
        )],
        intents={
            "2": SQLSelectIntent(
                source_tables=["SESSION", "BOOKING"],
                projection_field="SESSION.Activity",
                group_field="SESSION.Activity",
                minimum_count=5,
            ),
            "3": SQLInsertIntent(
                target_table="MEMBER",
                values={
                    "MemberID": SQLLiteralContract(kind="integer", value=1900),
                    "FullName": SQLLiteralContract(kind="text", value="Amira Khan"),
                    "Email": SQLLiteralContract(kind="text", value="amira@example.org"),
                },
            ),
        },
    )


def render_sql_schema(contract: SQLSourceContract) -> str:
    """Render only public schema facts; no worked query is present."""
    lines = []
    for table in contract.tables:
        fields = [
            column.name + ("*" if column.foreign_key else "")
            for column in table.columns
        ]
        lines.append(f"{table.name}({', '.join(fields)})")
    lines.extend(
        f"{table.name} primary key: ({', '.join(table.primary_key)})"
        for table in contract.tables
    )
    lines.append("Column nullability:")
    for table in contract.tables:
        declarations = [
            f"{column.name} {'NULL' if column.nullable else 'NOT NULL'}"
            for column in table.columns
        ]
        while declarations:
            line = f"{table.name}: {declarations.pop(0)}"
            while declarations and len(f"{line}; {declarations[0]}") <= 58:
                line += f"; {declarations.pop(0)}"
            lines.append(line)
    foreign_keys = [
        f"{table.name}.{column.name} -> {column.foreign_key}"
        for table in contract.tables
        for column in table.columns
        if column.foreign_key
    ]
    if foreign_keys:
        lines.append("Foreign keys:")
        lines.extend(foreign_keys)
    for sample in contract.sample_tables:
        lines.append(f"{sample.table} rows: {', '.join(sample.columns)}")
        lines.extend(
            ", ".join(
                str(value).upper() if isinstance(value, bool) else str(value)
                for value in row
            )
            for row in sample.rows
        )
    return "\n".join(lines)


def render_sql_intent_prompt(intent: SQLSelectIntent | SQLInsertIntent) -> str:
    """Render the candidate instruction represented by a supported intent."""
    if isinstance(intent, SQLSelectIntent):
        if (
            [table.casefold() for table in intent.source_tables]
            != ["session", "booking"]
            or intent.projection_field.casefold() != "session.activity"
            or intent.group_field.casefold() != "session.activity"
            or intent.minimum_count != 5
            or intent.order != "descending"
        ):
            raise ValueError(
                "the declared SELECT prompt renderer supports only the exact "
                "Activity/SESSION/BOOKING v2 task"
            )
        return (
            "Write one SELECT query that lists each Activity and the number of "
            "bookings for it, including only activities with at least five "
            "bookings. Sort the result from most to fewest bookings."
        )
    values = intent.values
    try:
        member_id = values["MemberID"].value
        full_name = values["FullName"].value
        email = values["Email"].value
    except KeyError as error:
        raise ValueError("the declared INSERT prompt requires MEMBER values") from error
    return (
        f"Write one INSERT statement to add member {member_id}, named "
        f"'{full_name}', with email '{email}' to {intent.target_table}."
    )


def sql_source_intent_sha256(contract: SQLSourceContract, intent_id: str) -> str:
    try:
        intent = contract.intents[intent_id]
    except KeyError as error:
        raise ValueError(f"unknown SQL intent: {intent_id}") from error
    payload = {
        "validator": SQL_VALIDATION_VERSION,
        "source_id": contract.source_id,
        "tables": [table.model_dump(mode="json") for table in contract.tables],
        "joins": [join.model_dump(mode="json") for join in contract.joins],
        "sample_tables": [
            sample.model_dump(mode="json") for sample in contract.sample_tables
        ],
        "intent": intent.model_dump(mode="json"),
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def selected_sql_answer_contract(
    contract: SQLSourceContract, intent_id: str
) -> dict[str, object]:
    """Public solver projection derived from the candidate's one declaration."""
    return {
        "version": contract.version,
        "source_id": contract.source_id,
        "tables": [table.model_dump(mode="json") for table in contract.tables],
        "joins": [join.model_dump(mode="json") for join in contract.joins],
        "sample_tables": [
            sample.model_dump(mode="json") for sample in contract.sample_tables
        ],
        "intent_id": intent_id,
        "intent": contract.intents[intent_id].model_dump(mode="json"),
    }


def validate_sql_response(
    answer: str,
    mark_points: list[str],
    contract: SQLSourceContract,
    intent_id: str,
) -> SQLValidationResult:
    """Validate the answer and every model-presented full statement separately."""
    digest = sql_source_intent_sha256(contract, intent_id)
    try:
        intent = contract.intents[intent_id]
    except KeyError:
        return _result(digest, [_finding("unknown-intent", "The SQL intent is unavailable.", "answer")])
    findings = _validate_one(answer, contract, intent, "answer")
    for index, point in enumerate(mark_points, start=1):
        statement = _purported_statement(point)
        if statement is not None:
            findings.extend(_validate_one(statement, contract, intent, f"mark_points[{index}]") )
    return _result(digest, findings)


def _result(digest: str, findings: list[SQLValidationFinding]) -> SQLValidationResult:
    return SQLValidationResult(
        passed=not findings,
        source_intent_sha256=digest,
        findings=findings,
    )


def _finding(
    code: str,
    message: str,
    location: str,
    *,
    unsupported: bool = False,
) -> SQLValidationFinding:
    return SQLValidationFinding(
        code=code,
        message=message,
        location=location,
        classification="unsupported" if unsupported else "invalid",
    )


def _validate_one(
    sql: str,
    contract: SQLSourceContract,
    intent: SQLSelectIntent | SQLInsertIntent,
    location: str,
) -> list[SQLValidationFinding]:
    try:
        stream = _TokenStream(sql)
        if isinstance(intent, SQLSelectIntent):
            _validate_select(_parse_select(stream), contract, intent)
        else:
            _validate_insert(_parse_insert(stream), contract, intent)
        stream.finish()
        return []
    except _SQLProblem as error:
        return [_finding(error.code, error.message, location, unsupported=error.unsupported)]


def _purported_statement(text: str) -> str | None:
    candidate = text.strip()
    label = re.match(
        r"^(?:SQL|QUERY|ANSWER)\s*:\s*(.*)$",
        candidate,
        re.IGNORECASE | re.DOTALL,
    )
    if label:
        candidate = label.group(1).strip()
        if re.match(r"^(?:SQL|QUERY|ANSWER)\s*:", candidate, re.IGNORECASE):
            return text.strip() if _has_sql_statement_shape(candidate) else None
    if "```" in candidate:
        fence = re.fullmatch(
            r"```(?:sql)?[ \t]*(?:\r?\n)?(.*?)(?:\r?\n)?```",
            candidate,
            re.IGNORECASE | re.DOTALL,
        )
        if fence is None:
            return text.strip() if _has_sql_statement_shape(candidate) else None
        candidate = fence.group(1).strip()
        if "```" in candidate or re.match(
            r"^(?:SQL|QUERY|ANSWER)\s*:", candidate, re.IGNORECASE
        ):
            return text.strip() if _has_sql_statement_shape(candidate) else None
    if _has_sql_statement_shape(candidate):
        return candidate
    return None


_SQL_STATEMENT_SHAPES = (
    r"\bSELECT\b(?=[\s\S]*\bFROM\b)",
    r"\bINSERT\s+INTO\b(?=[\s\S]*\bVALUES\s*\()",
    r"\bDELETE\s+FROM\s+[A-Za-z_]",
    r"\bUPDATE\s+[A-Za-z_][A-Za-z0-9_]*(?:\s+(?:AS\s+)?[A-Za-z_][A-Za-z0-9_]*)?\s+SET\b",
    r"\bDROP\s+(?:TABLE|VIEW|DATABASE|INDEX)\b",
    r"\bWITH\b(?=[\s\S]*\b(?:SELECT|INSERT|UPDATE|DELETE)\b)",
    r"\b(?:ALTER|CREATE|TRUNCATE)\s+(?:TABLE|VIEW|DATABASE|INDEX)\b",
    r"\b(?:MERGE|REPLACE)\s+INTO\b",
    r"\b(?:CALL|EXEC|GRANT|REVOKE|BEGIN)\b",
)


def _has_sql_statement_shape(text: str) -> bool:
    """Recognise executable shapes without extracting a statement substring."""
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in _SQL_STATEMENT_SHAPES)


@dataclass(frozen=True)
class _Token:
    kind: str
    value: str


class _SQLProblem(ValueError):
    def __init__(self, code: str, message: str, *, unsupported: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.unsupported = unsupported


_TOKEN = re.compile(
    r"(?P<space>\s+)|(?P<string>'(?:''|[^'])*')|(?P<number>[0-9]+)|"
    r"(?P<operator>>=|<=|<>|!=|=|>|<)|(?P<symbol>[(),;.*])|"
    r"(?P<identifier>[A-Za-z_][A-Za-z0-9_]*)|(?P<bad>.)",
    re.DOTALL,
)
_KEYWORDS = {
    "AS", "ASC", "BY", "DESC", "FROM", "GROUP", "HAVING", "INNER",
    "INSERT", "INTO", "JOIN", "ON", "ORDER", "SELECT", "VALUES", "WHERE",
}


class _TokenStream:
    def __init__(self, text: str) -> None:
        if not isinstance(text, str) or not text.strip():
            raise _SQLProblem("non-sql", "A complete SQL statement is required.")
        if len(text) > _MAX_SQL_LENGTH:
            raise _SQLProblem("input-limit", "The SQL statement exceeds the verification length limit.", unsupported=True)
        self.tokens: list[_Token] = []
        depth = 0
        for match in _TOKEN.finditer(text):
            kind = match.lastgroup or "bad"
            value = match.group()
            if kind == "space":
                continue
            if kind == "bad":
                raise _SQLProblem("unsupported-token", f"Unsupported SQL token {value!r}.", unsupported=True)
            if value == "(":
                depth += 1
                if depth > _MAX_PARENTHESES:
                    raise _SQLProblem("input-limit", "SQL nesting exceeds the verification limit.", unsupported=True)
            elif value == ")":
                depth -= 1
                if depth < 0:
                    raise _SQLProblem("trailing-input", "The SQL statement has an unmatched closing parenthesis.")
            self.tokens.append(_Token(kind, value))
            if len(self.tokens) > _MAX_SQL_TOKENS:
                raise _SQLProblem("input-limit", "The SQL statement exceeds the token limit.", unsupported=True)
        if depth != 0:
            raise _SQLProblem("incomplete-input", "The SQL statement has an unmatched parenthesis.")
        self.index = 0

    def peek(self, value: str | None = None) -> bool:
        if self.index >= len(self.tokens):
            return False
        return value is None or self.tokens[self.index].value.casefold() == value.casefold()

    def pop(self) -> _Token:
        if self.index >= len(self.tokens):
            raise _SQLProblem("incomplete-input", "The SQL statement ended before the required clauses were complete.")
        token = self.tokens[self.index]
        self.index += 1
        return token

    def keyword(self, value: str) -> None:
        token = self.pop()
        if token.kind != "identifier" or token.value.casefold() != value.casefold():
            raise _SQLProblem("statement-shape", f"Expected {value} in the SQL statement.")

    def accept(self, value: str) -> bool:
        if self.peek(value):
            self.index += 1
            return True
        return False

    def identifier(self) -> str:
        token = self.pop()
        if token.kind != "identifier" or token.value.upper() in _KEYWORDS:
            raise _SQLProblem("identifier", "A declared SQL identifier was expected.")
        return token.value

    def integer(self) -> int:
        token = self.pop()
        if token.kind != "number":
            raise _SQLProblem("literal", "An integer literal was expected.")
        return int(token.value)

    def literal(self) -> int | str:
        token = self.pop()
        if token.kind == "number":
            return int(token.value)
        if token.kind == "string":
            return token.value[1:-1].replace("''", "'")
        raise _SQLProblem("literal", "Only integer and single-quoted text literals are supported.", unsupported=True)

    def finish(self) -> None:
        if self.accept(";") and self.index < len(self.tokens):
            raise _SQLProblem("trailing-input", "SQL input continues after the completed statement.")
        if self.index < len(self.tokens):
            raise _SQLProblem("trailing-input", "SQL input contains an unsupported or incomplete suffix.")


@dataclass(frozen=True)
class _Field:
    qualifier: str | None
    name: str


@dataclass(frozen=True)
class _Count:
    operand: _Field | Literal["*"]


@dataclass(frozen=True)
class _Table:
    name: str
    alias: str


@dataclass(frozen=True)
class _Select:
    field: _Field
    count: _Count
    count_alias: str | None
    tables: tuple[_Table, _Table]
    join: tuple[_Field, _Field]
    group: _Field
    having: tuple[_Count, str, int]
    order: _Count | str
    descending: bool


@dataclass(frozen=True)
class _Insert:
    table: str
    columns: list[str] | None
    values: list[int | str]


def _field(stream: _TokenStream) -> _Field:
    first = stream.identifier()
    if stream.accept("."):
        return _Field(first, stream.identifier())
    return _Field(None, first)


def _count(stream: _TokenStream) -> _Count:
    stream.keyword("COUNT")
    if not stream.accept("("):
        raise _SQLProblem("statement-shape", "COUNT requires parentheses.")
    operand: _Field | Literal["*"] = "*" if stream.accept("*") else _field(stream)
    if not stream.accept(")"):
        raise _SQLProblem("statement-shape", "COUNT has an incomplete operand.")
    return _Count(operand)


def _table(stream: _TokenStream) -> _Table:
    name = stream.identifier()
    alias = name
    if stream.accept("AS") or (stream.peek() and stream.tokens[stream.index].kind == "identifier" and stream.tokens[stream.index].value.upper() not in _KEYWORDS):
        alias = stream.identifier()
    return _Table(name, alias)


def _equality(stream: _TokenStream) -> tuple[_Field, _Field]:
    left = _field(stream)
    if not stream.accept("="):
        raise _SQLProblem("wrong-join", "The supported join requires one declared column equality.")
    return left, _field(stream)


def _parse_select(stream: _TokenStream) -> _Select:
    stream.keyword("SELECT")
    field = _field(stream)
    if not stream.accept(","):
        raise _SQLProblem("projection", "SELECT must project Activity and one booking count.")
    count = _count(stream)
    alias = None
    if stream.accept("AS") or (stream.peek() and stream.tokens[stream.index].kind == "identifier" and stream.tokens[stream.index].value.upper() not in _KEYWORDS):
        alias = stream.identifier()
    stream.keyword("FROM")
    first = _table(stream)
    comma_join = stream.accept(",")
    if comma_join:
        second = _table(stream)
        stream.keyword("WHERE")
        join = _equality(stream)
    else:
        stream.accept("INNER")
        stream.keyword("JOIN")
        second = _table(stream)
        stream.keyword("ON")
        join = _equality(stream)
    stream.keyword("GROUP")
    stream.keyword("BY")
    group = _field(stream)
    stream.keyword("HAVING")
    having_count = _count(stream)
    operator = stream.pop()
    if operator.kind != "operator":
        raise _SQLProblem("wrong-threshold", "HAVING requires a supported integer comparison.")
    threshold = stream.integer()
    stream.keyword("ORDER")
    stream.keyword("BY")
    if stream.peek("COUNT"):
        order: _Count | str = _count(stream)
    else:
        order = stream.identifier()
    descending = stream.accept("DESC")
    if not descending:
        stream.accept("ASC")
    return _Select(field, count, alias, (first, second), join, group,
                   (having_count, operator.value, threshold), order, descending)


def _parse_insert(stream: _TokenStream) -> _Insert:
    stream.keyword("INSERT")
    stream.keyword("INTO")
    table = stream.identifier()
    columns = None
    if stream.accept("("):
        columns = [stream.identifier()]
        while stream.accept(","):
            columns.append(stream.identifier())
        if not stream.accept(")"):
            raise _SQLProblem("column-map", "The INSERT column list is incomplete.")
    stream.keyword("VALUES")
    if not stream.accept("("):
        raise _SQLProblem("column-map", "INSERT VALUES must use one complete row.")
    values = [stream.literal()]
    while stream.accept(","):
        values.append(stream.literal())
    if not stream.accept(")"):
        raise _SQLProblem("column-map", "The INSERT value list is incomplete.")
    return _Insert(table, columns, values)


def _validate_select(parsed: _Select, contract: SQLSourceContract, intent: SQLSelectIntent) -> None:
    schema = {table.name.casefold(): table for table in contract.tables}
    aliases: dict[str, SQLTableContract] = {}
    for table_ref in parsed.tables:
        table = schema.get(table_ref.name.casefold())
        if table is None:
            raise _SQLProblem("unknown-table", f"Unknown table {table_ref.name}.")
        key = table_ref.alias.casefold()
        if key in aliases:
            raise _SQLProblem("duplicate-alias", "Table aliases must be unique.")
        aliases[key] = table
    expected_tables = {name.casefold() for name in intent.source_tables}
    if {table.name.casefold() for table in aliases.values()} != expected_tables:
        raise _SQLProblem("wrong-tables", "SELECT must use exactly the declared SESSION and BOOKING sources.")

    field = _resolve(parsed.field, aliases)
    if field != _normal_field(intent.projection_field):
        raise _SQLProblem("projection", "SELECT does not project the requested Activity field.")
    if (
        parsed.count_alias is not None
        and parsed.count_alias.casefold() == parsed.field.name.casefold()
    ):
        raise _SQLProblem(
            "ambiguous-alias",
            "The booking-count alias collides with the projected Activity output.",
        )
    group = _resolve(parsed.group, aliases)
    if group != _normal_field(intent.group_field):
        raise _SQLProblem("wrong-group", "GROUP BY must combine rows for the requested Activity field.")

    left, right = (_resolve(value, aliases) for value in parsed.join)
    declared = {
        frozenset({_normal_field(f"{join.left_table}.{join.left_column}"),
                   _normal_field(f"{join.right_table}.{join.right_column}")})
        for join in contract.joins
    }
    if frozenset({left, right}) not in declared:
        raise _SQLProblem("wrong-join", "The join does not use the declared SessionID relationship.")

    _validate_count(parsed.count, aliases)
    _validate_count(parsed.having[0], aliases)
    operator, threshold = parsed.having[1:]
    if not ((operator == ">=" and threshold == intent.minimum_count)
            or (operator == ">" and threshold == intent.minimum_count - 1)):
        raise _SQLProblem("wrong-threshold", "HAVING does not express the requested integer minimum.")
    if isinstance(parsed.order, str):
        if parsed.count_alias is None or parsed.order.casefold() != parsed.count_alias.casefold():
            raise _SQLProblem("wrong-order", "ORDER BY uses neither the aggregate nor its declared alias.")
    else:
        _validate_count(parsed.order, aliases)
    if not parsed.descending:
        raise _SQLProblem("wrong-order", "Booking counts must be ordered descending.")


def _validate_count(count: _Count, aliases: dict[str, SQLTableContract]) -> None:
    if count.operand == "*":
        return
    if count.operand.qualifier is None and count.operand.name.casefold() in aliases:
        raise _SQLProblem(
            "unsupported-whole-row-count",
            "Whole-row COUNT(table) is outside the bounded verifier; use COUNT(*) or a declared non-null field.",
            unsupported=True,
        )
    table_name, column_name = _resolve(count.operand, aliases)
    table = next(table for table in aliases.values() if table.name.casefold() == table_name)
    column = next(column for column in table.columns if column.name.casefold() == column_name)
    if column.nullable:
        raise _SQLProblem("nullable-count", "COUNT of a nullable field may not equal the requested row count.")


def _resolve(field: _Field, aliases: dict[str, SQLTableContract]) -> tuple[str, str]:
    if field.qualifier is not None:
        table = aliases.get(field.qualifier.casefold())
        if table is None:
            raise _SQLProblem("unknown-alias", f"Unknown table or alias {field.qualifier}.")
        columns = [column for column in table.columns if column.name.casefold() == field.name.casefold()]
        if not columns:
            raise _SQLProblem("unknown-column", f"Unknown column {field.qualifier}.{field.name}.")
        return table.name.casefold(), columns[0].name.casefold()
    matches = [
        (table.name.casefold(), column.name.casefold())
        for table in aliases.values()
        for column in table.columns
        if column.name.casefold() == field.name.casefold()
    ]
    if not matches:
        raise _SQLProblem("unknown-column", f"Unknown column {field.name}.")
    if len(matches) != 1:
        raise _SQLProblem("ambiguous-column", f"Column {field.name} is ambiguous.")
    return matches[0]


def _validate_insert(parsed: _Insert, contract: SQLSourceContract, intent: SQLInsertIntent) -> None:
    if parsed.table.casefold() != intent.target_table.casefold():
        raise _SQLProblem("wrong-target", "INSERT targets a different table.")
    schema = {table.name.casefold(): table for table in contract.tables}
    table = schema[intent.target_table.casefold()]
    declared = {column.name.casefold(): column.name for column in table.columns}
    names = [
        name.casefold()
        for name in (
            parsed.columns
            if parsed.columns is not None
            else [column.name for column in table.columns]
        )
    ]
    if len(names) != len(set(names)) or set(names) != set(declared) or len(parsed.values) != len(names):
        raise _SQLProblem("column-map", "INSERT must bind every target column exactly once.")
    expected = {name.casefold(): literal for name, literal in intent.values.items()}
    for name, value in zip(names, parsed.values, strict=True):
        if name not in declared:
            raise _SQLProblem("unknown-column", f"Unknown INSERT column {name}.")
        literal = expected[name]
        if type(value) is not type(literal.value) or value != literal.value:
            raise _SQLProblem("wrong-literal", f"INSERT supplies the wrong value for {declared[name]}.")


def _normal_field(value: str) -> tuple[str, str]:
    table, column = value.split(".", 1)
    return table.casefold(), column.casefold()


def _contract_column(
    tables: dict[str, SQLTableContract], table_name: str, column_name: str
) -> SQLColumnContract:
    table = tables.get(table_name.casefold())
    if table is None:
        raise ValueError("SQL relationship uses an unknown table")
    for column in table.columns:
        if column.name.casefold() == column_name.casefold():
            return column
    raise ValueError("SQL relationship uses an unknown column")
