from __future__ import annotations

import argparse
import json
import re
import signal

import pymupdf
import pytest

from Backend.Core.cli import build_parser
from Backend.Core.france import occitanie_case_study as case


def test_native_status_mapping_tracks_actual_cli_event_messages(tmp_path, monkeypatch):
    messages = []
    monkeypatch.setattr(
        case, "emit_progress", lambda message, **_: messages.append(message)
    )
    monkeypatch.setattr(
        case,
        "emit",
        lambda kind, **values: (
            messages.append(values["message"]) if kind == "done" else None
        ),
    )
    monkeypatch.setattr(case, "generate_case_study", lambda _: {})
    assert (
        case.handle_generate_case_study(argparse.Namespace(output=str(tmp_path))) == 0
    )

    def cancel(_):
        raise InterruptedError

    monkeypatch.setattr(case, "generate_case_study", cancel)
    assert (
        case.handle_generate_case_study(argparse.Namespace(output=str(tmp_path))) == 130
    )
    assert len(set(messages)) == 3
    native = (
        case.Path(__file__).resolve().parents[1]
        / "macOS/Keldin/Domain/GenerationPresentation.swift"
    ).read_text()
    for message in set(messages):
        assert message in native, (
            f"The native status map is missing the CLI message: {message}"
        )


def test_curated_values_and_licence_are_source_pinned():
    data = case.load_case_data()
    rows = data["records"]
    assert len(rows) == len({row["codeetab"] for row in rows}) == 12
    assert data["license_id"] == "etalab-2.0"
    assert data["source_last_updated"] == "2026-05-12T12:46:56+00:00"
    assert data["retrieved_on"] == "2026-10-29"
    assert {row["commune"] for row in rows} == {
        "TOULOUSE",
        "CAHORS",
        "Montpellier",
        "Nîmes",
    }
    duplicate = [row for row in rows if row["denomination_lycee"] == "CLEMENT MAROT"]
    assert [(row["codeetab"], row["internat"]) for row in duplicate] == [
        ("0460007H", "oui"),
        ("0460051F", "non"),
    ]
    assert all(set(row) == set(data["selection"]["fields"]) for row in rows)


@pytest.mark.parametrize(
    "field,value",
    [
        ("license_id", "unknown"),
        ("publisher", "Other"),
        ("source_last_updated", "2026-10-29"),
        ("source_attributions", ["Other"]),
    ],
)
def test_forged_provenance_refuses(tmp_path, field, value):
    data = case.load_case_data()
    data[field] = value
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        case.load_case_data(path)


def test_changed_rows_refuse_even_if_resource_hash_is_rewritten(tmp_path):
    data = case.load_case_data()
    data["records"][0]["internat"] = "non"
    data["selection"]["rows_sha256"] = case.rows_sha256(data["records"])
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        case.load_case_data(path)


def test_sql_and_python_answers_agree_on_actual_rows():
    result = case.solve_case_study(case.load_case_data())
    assert result["indexed_count"] == 12
    assert result["bad_index_count"] == 11
    assert result["uppercase_montpellier"] == []
    assert result["normalised_montpellier"] == ["0340038G", "0340040J"]
    assert result["boarding_by_commune"] == {
        "Nîmes": 2,
        "TOULOUSE": 1,
        "Montpellier": 2,
        "CAHORS": 2,
    }
    assert result["sql_lot"] == [
        ("CLEMENT MAROT", "CAHORS"),
        ("GASTON MONNERVILLE", "CAHORS"),
    ]
    assert result["sql_join"] == [("JOFFRE", "Hérault"), ("JULES GUESDE", "Hérault")]


def test_printed_python_solutions_execute_on_the_pinned_rows():
    namespace = {}
    for code in (case.BAD_INDEX, case.FILTER, case.CORRECTED_FILTER, case.COUNT_CODE):
        exec(code, namespace)
        if code == case.FILTER:
            assert (
                namespace["filtrer"](case.load_case_data()["records"], "MONTPELLIER")
                == []
            )
    rows = case.load_case_data()["records"]
    assert len(namespace["indexer"](rows)) == 11
    assert namespace["indexer"](rows)["CLEMENT MAROT"]["codeetab"] == "0460051F"
    assert namespace["filtrer"](rows, "MONTPELLIER") == ["0340038G", "0340040J"]
    assert namespace["filtrer"](rows, "Montpellier") == ["0340038G", "0340040J"]
    assert (
        namespace["compter_internats"](rows)
        == case.solve_case_study(case.load_case_data())["boarding_by_commune"]
    )
    for sql in (case.SQL_LOT, case.SQL_JOIN):
        assert not any(
            token in sql.upper()
            for token in ("GROUP BY", "HAVING", "LEFT JOIN", "COALESCE")
        )


def test_cli_has_no_model_or_seed_requirement():
    args = build_parser().parse_args(
        ["generate-occitanie-case-study", "--output", "/tmp/case-fixture"]
    )
    assert args.handler is case.handle_generate_case_study
    assert not hasattr(args, "model") and not hasattr(args, "seed")


def test_existing_activity_is_not_overwritten(tmp_path):
    target = tmp_path / case.OUTPUT_FOLDER
    target.mkdir()
    previous = target / case.WORKSHEET_FILENAME
    previous.write_bytes(b"keep this existing PDF unchanged")
    before = previous.read_bytes()
    with pytest.raises(FileExistsError):
        case.generate_case_study(tmp_path)
    assert previous.read_bytes() == before
    assert not (target / case.CORRECTION_FILENAME).exists()


def test_failed_second_render_publishes_neither_pdf(tmp_path, monkeypatch):
    calls = []
    original = case.render_pdf_atomically

    def render(destination, renderer, **kwargs):
        calls.append(destination)
        if len(calls) == 2:
            raise ValueError("injected second render failure")
        return original(destination, renderer, **kwargs)

    monkeypatch.setattr(case, "render_pdf_atomically", render)
    with pytest.raises(ValueError, match="injected"):
        case.generate_case_study(tmp_path)
    assert not (tmp_path / case.OUTPUT_FOLDER).exists()
    assert list(tmp_path.iterdir()) == []


def test_competing_publication_preserves_existing_documents(tmp_path, monkeypatch):
    original = case.validate_case_pdf
    target = tmp_path / case.OUTPUT_FOLDER

    def validate(path, *, correction):
        original(path, correction=correction)
        if correction:
            target.mkdir()
            (target / case.WORKSHEET_FILENAME).write_bytes(b"other operation")

    monkeypatch.setattr(case, "validate_case_pdf", validate)
    with pytest.raises(FileExistsError):
        case.generate_case_study(tmp_path)
    assert (target / case.WORKSHEET_FILENAME).read_bytes() == b"other operation"
    assert not (target / case.CORRECTION_FILENAME).exists()
    assert list(tmp_path.iterdir()) == [target]


def test_invalid_source_does_not_create_output(tmp_path, monkeypatch):
    output = tmp_path / "not-created"
    monkeypatch.setattr(
        case,
        "load_case_data",
        lambda: (_ for _ in ()).throw(ValueError("invalid source")),
    )
    with pytest.raises(ValueError, match="invalid source"):
        case.generate_case_study(output)
    assert not output.exists()


def test_generation_exports_only_two_verified_pdfs(tmp_path):
    paths = case.generate_case_study(tmp_path)
    assert set(paths) == {"question_paper", "mark_scheme"}
    assert {path.name for path in paths.values()} == {
        case.WORKSHEET_FILENAME,
        case.CORRECTION_FILENAME,
    }
    for role, path in paths.items():
        case.validate_case_pdf(path, correction=role == "mark_scheme")
        with pymupdf.open(path) as pdf:
            assert len(pdf) == 3
            text = "\n".join(page.get_text() for page in pdf)
            positions = [
                re.search(rf"^{number}\. ", text, re.MULTILINE).start()
                for number in range(1, 9)
            ]
            assert positions == sorted(positions)
            if role == "mark_scheme":
                compact = "".join(text.split())
                for code in (
                    case.BAD_INDEX,
                    case.CORRECTED_FILTER,
                    case.COUNT_CODE,
                    case.SQL_LOT,
                    case.SQL_JOIN,
                ):
                    assert "".join(code.split()) in compact
    assert sorted(
        path.suffix for path in (tmp_path / case.OUTPUT_FOLDER).iterdir()
    ) == [".pdf", ".pdf"]


def test_cli_emits_only_success_files_after_pair_publication(tmp_path, monkeypatch):
    events = []
    monkeypatch.setattr(
        case, "emit", lambda kind, **values: events.append((kind, values))
    )
    assert (
        case.handle_generate_case_study(argparse.Namespace(output=str(tmp_path))) == 0
    )
    assert [kind for kind, _ in events] == ["file", "file", "done"]
    assert {values["role"] for kind, values in events if kind == "file"} == {
        "question_paper",
        "mark_scheme",
    }
    assert all(
        case.Path(values["path"]).is_file() for kind, values in events if kind == "file"
    )


def test_cli_cancellation_restores_signal_and_publishes_no_success(
    monkeypatch, tmp_path
):
    events = []
    previous = signal.getsignal(signal.SIGTERM)
    monkeypatch.setattr(
        case,
        "generate_case_study",
        lambda output: (_ for _ in ()).throw(InterruptedError()),
    )
    monkeypatch.setattr(case, "emit", lambda kind, **values: events.append(kind))
    assert (
        case.handle_generate_case_study(argparse.Namespace(output=str(tmp_path))) == 130
    )
    assert signal.getsignal(signal.SIGTERM) is previous
    assert events == []


def test_file_output_and_dangling_destination_symlink_refuse(tmp_path):
    output_file = tmp_path / "not-a-directory"
    output_file.write_bytes(b"preserved")
    with pytest.raises(OSError):
        case.generate_case_study(output_file)
    assert output_file.read_bytes() == b"preserved"
    target = tmp_path / case.OUTPUT_FOLDER
    target.symlink_to(tmp_path / "missing-directory")
    with pytest.raises(FileExistsError):
        case.generate_case_study(tmp_path)
    assert target.is_symlink()
