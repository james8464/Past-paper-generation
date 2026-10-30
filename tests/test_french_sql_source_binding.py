"""SQL evidence must use exactly the candidate-visible data, not a private twin."""

import pytest
from jsonschema.exceptions import ValidationError as SchemaValidationError

from Backend.Core.france import llm_pipeline as pipeline
from Backend.Core.france.nsi import NSITableMaterial
from Backend.Core.france.verification import verify_contract
from tests.test_french_llm_pipeline import raw_exercise
from tests.test_french_llm_runtime import publication as _runtime_publication

publication = _runtime_publication


def material():
    return {
        "kind": "table",
        "id": "donnees",
        "title": "Clients inscrits",
        "columns": ["id_client", "nom_client"],
        "rows": [["1", "Alice"], ["2", "Bob"], ["3", "Claire"]],
        "sql": {
            "table_name": "clients",
            "column_types": ["INTEGER", "TEXT"],
            "nullable": [False, False],
        },
    }


def contract():
    return {
        "kind": "sql",
        "source_material_ids": ["donnees"],
        "schema": "CREATE TABLE clients(id_client INTEGER, nom_client TEXT);"
        "INSERT INTO clients VALUES(1,'Alice'),(2,'Bob'),(3,'Claire');",
        "query": "SELECT nom_client FROM clients WHERE id_client = 3",
        "expected": [["Claire"]],
    }


def test_private_fixture_cannot_replace_printed_claire_with_bob():
    raw = raw_exercise("2")
    raw["materials"][0] = material()
    raw["questions"][0]["verification"] = contract()
    raw["questions"][0]["verification"]["schema"] = contract()["schema"].replace(
        "Claire", "Bob"
    )
    raw["questions"][0]["verification"]["expected"] = [["Bob"]]
    with pytest.raises(ValueError, match=r"source|imprim|SQL"):
        pipeline.validate_authored_exercise(raw, "2", large_print=False)


def test_bound_source_uses_the_same_database_as_query():
    public = NSITableMaterial.model_validate(material())
    result = verify_contract(contract(), sql_materials=[public])
    assert result["passed"] is True and result["actual"] == [["Claire"]]


@pytest.mark.parametrize(
    "suffix",
    [
        "DELETE FROM clients WHERE id_client=3;",
        "INSERT INTO clients VALUES(3,'Claire');",
        "INSERT INTO clients VALUES(4,'Lina');",
        "CREATE TABLE extra(x INTEGER);",
        "CREATE TEMP TABLE extra(x INTEGER);",
        "CREATE VIEW extra AS SELECT * FROM clients;",
        "CREATE INDEX extra ON clients(nom_client);",
    ],
)
def test_missing_extra_duplicate_or_unbound_objects_refuse(suffix):
    data = contract()
    data["schema"] += suffix
    assert (
        verify_contract(
            data, sql_materials=[NSITableMaterial.model_validate(material())]
        )["passed"]
        is False
    )


@pytest.mark.parametrize(
    "query",
    [
        "DELETE FROM clients",
        "UPDATE clients SET nom_client='Bob'",
        "INSERT INTO clients VALUES(4,'Lina')",
        "DROP TABLE clients",
        "SELECT rowid FROM clients",
        "SELECT name FROM sqlite_schema",
        "PRAGMA table_info(clients)",
        "ATTACH DATABASE ':memory:' AS extra",
        "SELECT load_extension('not-a-library')",
    ],
)
def test_bound_queries_cannot_mutate_or_read_unprinted_metadata(query):
    data = contract()
    data.update(query=query, expected=[])
    assert (
        verify_contract(
            data, sql_materials=[NSITableMaterial.model_validate(material())]
        )["passed"]
        is False
    )


@pytest.mark.parametrize(
    "change",
    [
        lambda value: value["sql"].update(table_name="other"),
        lambda value: value["sql"].update(column_types=["TEXT", "TEXT"]),
        lambda value: value.update(columns=["client_id", "nom_client"]),
        lambda value: value["rows"][2].__setitem__(1, "claire"),
        lambda value: value["rows"][2].__setitem__(1, "Clairé"),
    ],
)
def test_exact_public_table_columns_storage_and_text_are_not_normalized(change):
    public = material()
    change(public)
    assert (
        verify_contract(
            contract(), sql_materials=[NSITableMaterial.model_validate(public)]
        )["passed"]
        is False
    )


def test_reordering_rows_is_not_a_sql_table_change_but_duplicates_are_preserved():
    public = material()
    public["rows"].reverse()
    assert (
        verify_contract(
            contract(), sql_materials=[NSITableMaterial.model_validate(public)]
        )["passed"]
        is True
    )
    public["rows"].append(["3", "Claire"])
    data = contract()
    data["schema"] += "INSERT INTO clients VALUES(3,'Claire');"
    data["expected"] = [["Claire"], ["Claire"]]
    assert (
        verify_contract(data, sql_materials=[NSITableMaterial.model_validate(public)])[
            "passed"
        ]
        is True
    )


@pytest.mark.parametrize(
    "kind,nullable,printed,literal,passed",
    [
        ("TEXT", False, "001", "'001'", True),
        ("TEXT", False, "NULL", "'NULL'", True),
        ("TEXT", True, "NULL", "NULL", True),
        ("TEXT", True, "NULL", "'NULL'", False),
        ("TEXT", False, "NULL", "NULL", False),
        ("INTEGER", False, "01", "1", False),
        ("INTEGER", False, "-0", "0", False),
        ("INTEGER", False, "9223372036854775808", "9223372036854775808", False),
        ("INTEGER", False, "-9223372036854775808", "-9223372036854775808", True),
        ("REAL", False, "0.25", "0.25", True),
        ("REAL", False, "-2.5", "-2.5", True),
        ("REAL", True, "NULL", "NULL", True),
        ("REAL", False, "1e2", "100.0", False),
        ("REAL", False, "NaN", "0.0", False),
        ("REAL", False, "1,25", "1.25", False),
        ("REAL", False, "1.23456789012345", "1.23456789012345", True),
        ("REAL", False, "123456789012345.12", "123456789012345.12", True),
        ("REAL", False, "123456789012345.13", "123456789012345.13", False),
    ],
)
def test_scalar_policy_has_explicit_type_null_and_precision_semantics(
    kind, nullable, printed, literal, passed
):
    public = material()
    public.update(columns=["id_client", "valeur"], rows=[["1", printed]])
    public["sql"].update(column_types=["INTEGER", kind], nullable=[False, nullable])
    data = contract()
    data.update(
        schema=f"CREATE TABLE clients(id_client INTEGER, valeur {kind}); INSERT INTO clients VALUES(1,{literal});",
        query="SELECT id_client FROM clients",
        expected=[[1]],
    )
    assert (
        verify_contract(data, sql_materials=[NSITableMaterial.model_validate(public)])[
            "passed"
        ]
        is passed
    )


@pytest.mark.parametrize(
    "schema",
    [
        "CREATE TABLE clients(id_client INTEGER, nom_client TEXT COLLATE NOCASE); INSERT INTO clients VALUES(1,'Alice'),(2,'Bob'),(3,'Claire');",
        "CREATE TABLE clients(id_client INTEGER, nom_client TEXT, secret INTEGER GENERATED ALWAYS AS (1)); INSERT INTO clients(id_client,nom_client) VALUES(1,'Alice'),(2,'Bob'),(3,'Claire');",
    ],
)
def test_hidden_semantics_not_in_descriptor_are_refused(schema):
    data = contract()
    data["schema"] = schema
    assert (
        verify_contract(
            data, sql_materials=[NSITableMaterial.model_validate(material())]
        )["passed"]
        is False
    )


def test_binding_is_explicit_referenced_unique_and_not_a_human_fallback():
    for ids in ([], ["donnees", "donnees"], ["other"]):
        raw = raw_exercise("2")
        raw["materials"][0] = material()
        raw["questions"][0]["verification"] = contract()
        raw["questions"][0]["verification"]["source_material_ids"] = ids
        with pytest.raises((ValueError, SchemaValidationError)):
            pipeline.validate_authored_exercise(raw, "2")
    raw = raw_exercise("2")
    raw["materials"][0] = material()
    raw["questions"][0]["material_ids"] = []
    raw["questions"][0]["verification"] = contract()
    with pytest.raises(ValueError, match="Sources SQL"):
        pipeline.validate_authored_exercise(raw, "2")


def test_optional_descriptor_preserves_legacy_material_serialization_and_schema():
    from Backend.Core.france.nsi import authoring_schema

    public = material()
    public.pop("sql")
    assert NSITableMaterial.model_validate(public).model_dump(mode="json") == public
    assert "sql" not in authoring_schema()["$defs"]["NSITableMaterial"]["properties"]
    old = contract()
    old.pop("source_material_ids")
    assert verify_contract(old)["passed"] is True
    old.update(query="UPDATE clients SET nom_client='Lina'", expected=[])
    assert verify_contract(old)["passed"] is True


def test_historical_unbound_contract_reading_is_explicit_not_new_job_default():
    raw = raw_exercise("2")
    old = contract()
    old.pop("source_material_ids")
    raw["questions"][0]["verification"] = old
    assert pipeline.validate_authored_exercise(raw, "2", sql_source_binding=False)
    with pytest.raises(SchemaValidationError):
        pipeline.validate_authored_exercise(raw, "2")


def test_multiple_relations_and_foreign_key_source_require_complete_binding():
    first = NSITableMaterial.model_validate(material())
    second = material()
    second.update(
        id="commandes",
        title="Commandes passées",
        columns=["id_commande", "id_client"],
        rows=[["10", "3"]],
    )
    second["sql"].update(table_name="commandes", column_types=["INTEGER", "INTEGER"])
    second = NSITableMaterial.model_validate(second)
    data = contract()
    data["schema"] += (
        "CREATE TABLE commandes(id_commande INTEGER, id_client INTEGER REFERENCES clients(id_client)); INSERT INTO commandes VALUES(10,3);"
    )
    data.update(
        query="SELECT nom_client FROM clients JOIN commandes ON clients.id_client=commandes.id_client ORDER BY id_commande",
        expected=[["Claire"]],
    )
    assert verify_contract(data, sql_materials=[first, second])["passed"] is True
    assert verify_contract(data, sql_materials=[first])["passed"] is False


@pytest.mark.parametrize(
    "change",
    [
        lambda value: value["sql"].update(nullable=[0, False]),
        lambda value: value["sql"].update(nullable=[False]),
        lambda value: value["sql"].update(column_types=["INTEGER", "NUMERIC"]),
        lambda value: value["sql"].update(table_name="sqlite_private"),
        lambda value: value.update(columns=["id_client", "ID_CLIENT"]),
    ],
)
def test_malformed_descriptor_refuses(change):
    public = material()
    change(public)
    with pytest.raises(ValueError):
        NSITableMaterial.model_validate(public)


def test_source_mismatch_is_not_a_retry_or_implicit_downgrade():
    from tests.test_french_llm_pipeline import Client

    def mutate(raw):
        raw["materials"][0] = material()
        raw["questions"][0]["verification"] = contract()
        raw["questions"][0]["verification"]["schema"] = contract()["schema"].replace(
            "Claire", "Bob"
        )
        raw["questions"][0]["verification"]["expected"] = [["Bob"]]

    client = Client(mutate=mutate)
    with pytest.raises(ValueError, match="source imprimée"):
        pipeline._author(client, pipeline.exercise_request("2", 42, []), "2")
    assert len(client.requests) == 1


def test_package_rechecks_source_even_after_hashes_are_recomputed(tmp_path):
    from Backend.Core.france.sql_sources import SQL_SOURCE_POLICY
    from tests.test_french_llm_pipeline import Client
    from tests.test_nsi_pipeline import make_index

    path = tmp_path / "references.sqlite"
    make_index(path)

    def mutate(raw):
        if raw["id"] == "2":
            raw["materials"][0] = material()
            raw["questions"][0]["verification"] = contract()

    package = pipeline.generate(index_path=path, client=Client(mutate=mutate), seed=42)
    assert package["identity"]["sql_source_policy"] == SQL_SOURCE_POLICY
    assert pipeline.validate_package(package)
    package["exercises"][1]["materials"][0]["rows"][2][1] = "Lina"
    package["identity"]["content_sha256"] = pipeline._digest(
        {key: value for key, value in package.items() if key != "identity"}
    )
    with pytest.raises(ValueError, match="source imprimée"):
        pipeline.validate_package(package)


@pytest.mark.parametrize("policy", [None, "forged", True, 1, ""])
def test_current_package_requires_policy_even_without_sql(tmp_path, policy):
    from tests.test_french_llm_pipeline import Client
    from tests.test_nsi_pipeline import make_index

    path = tmp_path / "references.sqlite"
    make_index(path)
    package = pipeline.generate(index_path=path, client=Client(), seed=42)
    if policy is None:
        package["identity"].pop("sql_source_policy")
    else:
        package["identity"]["sql_source_policy"] = policy
    package["identity"]["content_sha256"] = pipeline._digest(
        {key: value for key, value in package.items() if key != "identity"}
    )
    with pytest.raises(ValueError, match="Politique de source SQL"):
        pipeline.validate_package(package)


def test_policy_and_bindings_cannot_be_stripped_and_laundered_with_new_hash(tmp_path):
    from tests.test_french_llm_pipeline import Client
    from tests.test_nsi_pipeline import make_index

    path = tmp_path / "references.sqlite"
    make_index(path)

    def mutate(raw):
        raw["materials"][0] = material()
        raw["questions"][0]["verification"] = contract()

    package = pipeline.generate(index_path=path, client=Client(mutate=mutate), seed=42)
    package["identity"].pop("sql_source_policy")
    for exercise in package["exercises"]:
        exercise["materials"][0].pop("sql")
        exercise["questions"][0]["verification"].pop("source_material_ids")
    package["identity"]["content_sha256"] = pipeline._digest(
        {key: value for key, value in package.items() if key != "identity"}
    )
    with pytest.raises(ValueError, match="Politique de source SQL"):
        pipeline.validate_package(package)


@pytest.mark.parametrize("field", ["sql", "source_material_ids"])
def test_individual_source_fields_cannot_be_stripped_under_current_policy(
    tmp_path, field
):
    from tests.test_french_llm_pipeline import Client
    from tests.test_nsi_pipeline import make_index

    path = tmp_path / "references.sqlite"
    make_index(path)

    def mutate(raw):
        raw["materials"][0] = material()
        raw["questions"][0]["verification"] = contract()

    package = pipeline.generate(index_path=path, client=Client(mutate=mutate), seed=42)
    if field == "sql":
        package["exercises"][0]["materials"][0].pop(field)
    else:
        package["exercises"][0]["questions"][0]["verification"].pop(field)
    package["identity"]["content_sha256"] = pipeline._digest(
        {key: value for key, value in package.items() if key != "identity"}
    )
    with pytest.raises((ValueError, SchemaValidationError)):
        pipeline.validate_package(package)


@pytest.mark.parametrize("missing", [True, False])
def test_live_runtime_requires_current_source_binding_policy(
    publication, monkeypatch, missing
):
    subject, args, events = publication
    original = subject.llm_pipeline.generate

    def wrong_policy(**kwargs):
        package = original(**kwargs)
        if missing:
            package["identity"].pop("sql_source_policy")
        else:
            package["identity"]["sql_source_policy"] = "invented"
        return package

    monkeypatch.setattr(subject.llm_pipeline, "generate", wrong_policy)
    assert subject.handle_generate_llm_assessment(args) == 1
    assert not any(event["type"] in {"file", "done"} for event in events)


@pytest.mark.parametrize("large_print", [False, True])
@pytest.mark.parametrize("correction", [False, True])
def test_real_pdf_preserves_owned_sql_caption_and_all_public_rows(
    tmp_path, large_print, correction
):
    import pymupdf

    from Backend.Core.france import llm_pdf
    from Backend.Core.france.sql_sources import sql_caption
    from tests.test_french_llm_pdf import render

    exercises = []
    for identifier in ("1", "2", "3"):
        raw = raw_exercise(identifier)
        if identifier == "2":
            raw["materials"][0] = material()
            raw["questions"][0]["verification"] = contract()
        exercises.append(
            pipeline.validate_authored_exercise(
                raw, identifier, large_print=large_print
            )
        )
    path = tmp_path / "sql.pdf"
    render(path, exercises, correction=correction, large_print=large_print)
    llm_pdf.validate_llm_pdf(
        path, exercises, correction=correction, large_print=large_print
    )
    with pymupdf.open(path) as doc:
        text = " ".join(page.get_text() for page in doc)

    def compact(value):
        return "".join(value.split())

    assert compact(sql_caption(exercises[1].materials[0])) in compact(text)
    assert "Claire" in text


@pytest.mark.parametrize("large_print", [False, True])
def test_real_pdf_distinguishes_text_identifiers_real_and_null(tmp_path, large_print):
    from Backend.Core.france import llm_pdf
    from tests.test_french_llm_pdf import render

    exercises = []
    for identifier in ("1", "2", "3"):
        raw = raw_exercise(identifier)
        if identifier == "2":
            public = material()
            public.update(
                columns=["id", "code", "prix", "note"],
                rows=[["1", "001", "0.25", "NULL"]],
            )
            public["sql"].update(
                column_types=["INTEGER", "TEXT", "REAL", "TEXT"],
                nullable=[False, False, False, True],
            )
            raw["materials"][0] = public
            data = contract()
            data.update(
                schema="CREATE TABLE clients(id INTEGER, code TEXT, prix REAL, note TEXT); INSERT INTO clients VALUES(1,'001',0.25,NULL);",
                query="SELECT code,prix,note FROM clients ORDER BY id",
                expected=[["001", 0.25, None]],
            )
            raw["questions"][0]["verification"] = data
        exercises.append(
            pipeline.validate_authored_exercise(
                raw, identifier, large_print=large_print
            )
        )
    path = tmp_path / "typed-values.pdf"
    render(path, exercises, large_print=large_print)
    llm_pdf.validate_llm_pdf(path, exercises, correction=False, large_print=large_print)


def test_pdf_gate_refuses_missing_type_null_caption(tmp_path, monkeypatch):
    from Backend.Core.france import llm_pdf, sql_sources
    from tests.test_french_llm_pdf import render

    exercises = []
    for identifier in ("1", "2", "3"):
        raw = raw_exercise(identifier)
        raw["materials"][0] = material()
        exercises.append(pipeline.validate_authored_exercise(raw, identifier))
    monkeypatch.setattr(sql_sources, "sql_caption", lambda _: "")
    path = tmp_path / "missing-caption.pdf"
    render(path, exercises)
    with pytest.raises(ValueError):
        llm_pdf.validate_llm_pdf(path, exercises, correction=False)


@pytest.mark.parametrize("constraint", ["PRIMARY KEY", "UNIQUE"])
def test_sqlite_owned_text_key_indexes_do_not_create_private_relations(constraint):
    public = material()
    public.update(columns=["code", "nom_client"], rows=[["A", "Alice"], ["B", "Bob"]])
    public["sql"].update(column_types=["TEXT", "TEXT"])
    data = contract()
    data.update(
        schema=f"CREATE TABLE clients(code TEXT {constraint}, nom_client TEXT); INSERT INTO clients VALUES('A','Alice'),('B','Bob');",
        query="SELECT nom_client FROM clients WHERE code='B'",
        expected=[["Bob"]],
    )
    assert (
        verify_contract(data, sql_materials=[NSITableMaterial.model_validate(public)])[
            "passed"
        ]
        is True
    )
    data.update(query="SELECT name FROM sqlite_schema", expected=[])
    assert (
        verify_contract(data, sql_materials=[NSITableMaterial.model_validate(public)])[
            "passed"
        ]
        is False
    )


def test_sqlite_composite_key_and_foreign_key_tables_are_bound_exactly():
    public = material()
    public.update(columns=["code", "version"], rows=[["A", "1"], ["A", "2"]])
    public["sql"].update(column_types=["TEXT", "INTEGER"])
    related = material()
    related.update(id="commandes", columns=["code", "version"], rows=[["A", "2"]])
    related["sql"].update(table_name="commandes", column_types=["TEXT", "INTEGER"])
    data = contract()
    data.update(
        schema="CREATE TABLE clients(code TEXT, version INTEGER, PRIMARY KEY(code,version)); INSERT INTO clients VALUES('A',1),('A',2); CREATE TABLE commandes(code TEXT, version INTEGER, PRIMARY KEY(code,version), FOREIGN KEY(code,version) REFERENCES clients(code,version)); INSERT INTO commandes VALUES('A',2);",
        query="SELECT c.code,c.version FROM clients c JOIN commandes q ON c.code=q.code AND c.version=q.version",
        expected=[["A", 2]],
    )
    sources = [NSITableMaterial.model_validate(value) for value in (public, related)]
    assert verify_contract(data, sql_materials=sources)["passed"] is True
    assert verify_contract(data, sql_materials=sources[:1])["passed"] is False


@pytest.mark.parametrize(
    "decoration",
    [
        "/* COLLATE NOCASE */",
        "-- COLLATE RTRIM\n",
        "DEFAULT 'COLLATE'",
        "DEFAULT 'one''COLLATE two'",
    ],
)
def test_quoted_collate_column_comments_and_default_strings_are_not_collations(
    decoration,
):
    public = material()
    public.update(columns=["id_client", "COLLATE"], rows=[["1", "Claire"]])
    data = contract()
    data.update(
        schema=f"CREATE TABLE clients(id_client INTEGER, \"COLLATE\" TEXT {decoration}); INSERT INTO clients VALUES(1,'Claire');",
        query='SELECT "COLLATE" FROM clients WHERE id_client=1',
        expected=[["Claire"]],
    )
    assert (
        verify_contract(data, sql_materials=[NSITableMaterial.model_validate(public)])[
            "passed"
        ]
        is True
    )


@pytest.mark.parametrize("collation", ["NOCASE", "RTRIM", '"NOCASE"', "[RTRIM]"])
def test_actual_collation_on_autoindexed_keys_still_refuses(collation):
    public = material()
    data = contract()
    data["schema"] = data["schema"].replace(
        "nom_client TEXT", f"nom_client TEXT UNIQUE COLLATE {collation}"
    )
    result = verify_contract(
        data, sql_materials=[NSITableMaterial.model_validate(public)]
    )
    assert result["passed"] is False
    assert "Collation SQL" in result["reason"]


@pytest.mark.parametrize(
    "declaration",
    [
        'CREATE TABLE clients(id INTEGER, "COLLATE" TEXT)',
        "CREATE TABLE clients(id INTEGER, [COLLATE] TEXT)",
        "CREATE TABLE clients(id INTEGER, `COLLATE` TEXT)",
        "CREATE TABLE clients(id INTEGER, name TEXT DEFAULT 'one''COLLATE two')",
        'CREATE TABLE clients(id INTEGER, "one""COLLATE two" TEXT)',
        "CREATE TABLE clients(id INTEGER, name TEXT /* COLLATE NOCASE */)",
    ],
)
def test_collation_detection_skips_only_quoted_or_commented_words(declaration):
    from Backend.Core.france.sql_sources import _has_collation

    assert _has_collation(declaration) is False
    assert (
        _has_collation(declaration[:-1] + ', other TEXT COLLATE /* gap */ "NOCASE")')
        is True
    )


def test_sqlite_discards_trailing_unterminated_comment_before_source_inspection():
    import sqlite3

    declaration = "CREATE TABLE clients(id_client INTEGER, nom_client TEXT) /* COLLATE"
    with sqlite3.connect(":memory:") as db:
        db.execute(declaration)
        stored = db.execute(
            "SELECT sql FROM sqlite_schema WHERE name='clients'"
        ).fetchone()[0]
    assert stored == "CREATE TABLE clients(id_client INTEGER, nom_client TEXT)"
    data = contract()
    data["schema"] += " /* COLLATE"
    assert (
        verify_contract(
            data, sql_materials=[NSITableMaterial.model_validate(material())]
        )["passed"]
        is True
    )
