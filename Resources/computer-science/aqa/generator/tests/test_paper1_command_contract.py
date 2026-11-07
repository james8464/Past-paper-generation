"""Printed command guidance must match the supplied program, not its CSV data."""

import ast
from pathlib import Path

import pymupdf
import pytest
from cspapergen import render_pdf
from cspapergen.generator import build_paper1_blueprint
from cspapergen.syllabus import load_syllabus

COMMAND_GUIDANCE = "At the Command: prompt, enter ADD, REPORT, BEST or QUIT."
OLD_GUIDANCE = "Input format: COMMAND,param1,param2,param3"


@pytest.mark.parametrize(
    ("seed", "scenario"),
    [
        (0, "Youth Sports League"),
        (1, "Community Library Tracker"),
        (2, "Habitat Survey Manager"),
        (5, "Renewable Energy Monitor"),
    ],
)
def test_supplied_protocol_and_content_only_questions_match_every_scenario(
    tmp_path, seed, scenario
):
    assert (
        Path(render_pdf.__file__).resolve().parent.parent == Path(__file__).parents[1]
    )
    blueprint, context = build_paper1_blueprint(load_syllabus(), seed=seed)
    assert context.scenario_title == scenario
    before = (blueprint.model_dump_json(), context.model_dump_json())
    module = ast.parse(context.skeleton_program)
    main = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "main"
    )
    accepted = {
        comparator.value
        for node in ast.walk(main)
        if isinstance(node, ast.Compare)
        and isinstance(node.left, ast.Name)
        and node.left.id == "command"
        for comparator in node.comparators
        if isinstance(comparator, ast.Constant) and isinstance(comparator.value, str)
    }
    assert accepted == set(context.command_names) == {"ADD", "REPORT", "BEST", "QUIT"}
    destination = tmp_path / "question-paper.pdf"
    render_pdf.render_question_paper(blueprint, destination)
    with pymupdf.open(destination) as document:
        text = "\n".join(page.get_text() for page in document)
        # The supplied program is authoritative; the QP no longer adds a
        # separate, renderer-invented command-information page.
        assert COMMAND_GUIDANCE not in text
        assert OLD_GUIDANCE not in text
        assert "Input format: COMMAND," not in text
    assert (blueprint.model_dump_json(), context.model_dump_json()) == before


def test_supplied_loop_accepts_standalone_commands_not_csv_records(monkeypatch, capsys):
    _, context = build_paper1_blueprint(load_syllabus(), seed=2)
    namespace = {"__name__": "owned_contract_fixture"}
    exec(compile(context.skeleton_program, "owned-skeleton.py", "exec"), namespace)
    records = [namespace["Observation"](1, context.category_names[0], 50)]
    calls = []
    namespace["load_records"] = lambda _filename: records
    namespace["add_record"] = lambda values: calls.append(("ADD", values))
    namespace["print_report"] = lambda values: calls.append(("REPORT", values))
    supplied = iter(["ADD,123,GRASSLAND,70", " add ", "report", "QUIT"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(supplied))
    namespace["main"]()
    assert calls == [("ADD", records), ("REPORT", records)]
    assert capsys.readouterr().out == "Unknown command\n"
