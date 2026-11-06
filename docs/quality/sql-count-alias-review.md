# SQL aggregate alias review

The bounded SELECT parser accepted a declared aggregate alias named `Count`,
but then treated `ORDER BY Count DESC` as the start of a function call. The
otherwise equivalent `BookingCount` alias passed. An owned parser-only
reproduction therefore exposed a false refusal within the existing alias
support, not a wrong answer from a model.

SQLite's [keyword list](https://www.sqlite.org/lang_keywords.html) does not
classify `COUNT` as a keyword, and its
[ORDER BY documentation](https://www.sqlite.org/lang_select.html#orderby)
describes resolving a declared output alias. These references establish the
specific spelling's validity in SQLite; they are not a claim that this module
implements every SQL dialect or all SQLite syntax.

The repair uses the next token to distinguish `COUNT(...)` from a bare output
alias. Only the parenthesised form enters the existing aggregate parser. A
bare name still has to match the declared count alias, and all existing source,
join, projection, grouping, nullability, threshold, descending-order and final
statement checks remain in force. No SQL is executed by this module.

The initial tests produced 19 failures and 22 passing controls against the old
parser. The new 41-test matrix covers all case combinations of `Count`, `count`
and `COUNT`, explicit and implicit `AS`, existing `BookingCount` aliases,
actual aggregate calls, malformed or unsupported functions, undeclared and
ambiguous aliases, nullable operands, wrong thresholds/order, multiple
statements, marked-answer suffixes and the existing input bounds. The focused
SQL, AQA checkpoint, source-fidelity and objective suite passed 280 tests.
Ruff checking and formatting and the diff check passed. The configured type
gate passed its four existing infrastructure modules, not a new static-type
certification of the whole SQL implementation.

`SQL_VALIDATION_VERSION` remains `aqa-candidate-sql-v4`. The candidate source and
intent have not changed, and their canonical digest remains
`fcbfce91b6c6b4cce13dcf7bf47e5ac0fcaafbf215898f1bc61dd2345ecef18b`.
Existing successful spellings retain their meaning; this change allows a
previously refused equivalent alias. No historical failed result is rewritten
as a successful review, and no schema, prompt, answer key or admission bound was
changed.

| Reviewed file | SHA-256 |
| --- | --- |
| `Backend/Core/subjects/sql_contracts.py` | `943aa3c19936efa33de6d4f823961a5f79beccc324437f843b81387f50aad644` |
| `tests/test_sql_count_alias.py` | `79d644c71ef5107331631ebeb185736f1147fafe7b689bcc995f50f0775e24cd` |

The prior complete 1,052-line implementation audit and this six-line extension
are bounded source-review evidence. No SQL engine, model, GUI, full suite or
release build was run for this repair. Paper quality, all dependency behaviour,
official equivalence and complete-project qualification are not implied.
