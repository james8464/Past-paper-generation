from dataclasses import make_dataclass

import pytest

from Backend.Core.computer_science_reference_solutions import paper1_reference_code


def test_timing_example_uses_supplied_functions_and_fresh_equal_trials(capsys):
    samples = []

    def run(data):
        samples.append(data.copy())
        data.clear()

    ticks = iter(range(20))
    namespace = {
        "run_X": run,
        "run_Y": run,
        "make_data": lambda n: list(range(n)),
        "timer": lambda: next(ticks),
        "input": lambda _: "3",
    }
    exec(paper1_reference_code(4), namespace)
    assert samples == [[0, 1, 2]] * 10
    assert capsys.readouterr().out.strip() == "tie 1.0 1.0"


def test_validation_example_uses_supplied_categories():
    namespace = {"CATEGORIES": ["SOLAR", "WIND", "HYDRO"]}
    exec(paper1_reference_code(9), namespace)
    validate = namespace["valid_entry"]
    assert validate(" solar ", "0")
    assert validate("WIND", "100")
    assert not validate("WOODLAND", "50")
    assert not validate("HYDRO", "101")
    assert not validate("HYDRO", None)


def test_adjustment_example_implements_the_actual_function_contract():
    namespace = {"THRESHOLD": 40, "MULTIPLIER": 3}
    exec(paper1_reference_code(10), namespace)
    adjust = namespace["parse_adjusted_value"]
    assert [adjust(value) for value in ("39", "40", "41", "bad", None)] == [
        39,
        120,
        123,
        None,
        None,
    ]


@pytest.mark.parametrize(
    "record_name", ["Observation", "LoanRecord", "SiteReading", "MatchRecord"]
)
def test_add_example_constructs_the_scenario_record_type(record_name):
    record_type = make_dataclass(
        record_name, [("identifier", int), ("category", str), ("value", int)]
    )
    entries = iter(["1", "solar", "50"])
    namespace = {
        record_name: record_type,
        "CATEGORIES": ["SOLAR"],
        "input": lambda _: next(entries),
    }
    exec(paper1_reference_code(11, record_name=record_name), namespace)
    records = []
    namespace["add_record"](records)
    assert records == [record_type(1, "SOLAR", 50)]


def test_report_example_is_one_pass_and_preserves_empty_categories_and_ties(capsys):
    record_type = make_dataclass(
        "Record", [("identifier", int), ("category", str), ("value", int)]
    )

    class Records(list):
        visits = 0

        def __iter__(self):
            self.visits += 1
            return super().__iter__()

    records = Records(
        [record_type(1, "B", 10), record_type(2, "A", 5), record_type(3, "A", 5)]
    )
    namespace = {
        "CATEGORIES": ["B", "EMPTY", "A"],
        "adjusted_value": lambda record: record.value * 2,
    }
    exec(paper1_reference_code(12), namespace)
    namespace["print_report"](records)
    assert records.visits == 1
    assert capsys.readouterr().out.splitlines() == ["A 20 2", "B 20 1", "EMPTY 0 -"]
    assert records[0].value == 10


@pytest.mark.parametrize("seed", [0, 1, 2, 5])
def test_reference_functions_integrate_with_the_generated_skeleton(seed, capsys):
    from pathlib import Path

    from cspapergen.generator import build_paper1_blueprint
    from cspapergen.syllabus import load_syllabus

    syllabus = load_syllabus(
        Path("Resources/computer-science/aqa/generator/data/syllabus_seed.json")
    )
    blueprint, context = build_paper1_blueprint(syllabus, seed=seed)
    namespace = {"__name__": __name__}
    exec(context.skeleton_program, namespace)
    assert blueprint.program_record_name == context.record_name
    for number in (9, 10, 11, 12):
        exec(
            paper1_reference_code(number, record_name=blueprint.program_record_name),
            namespace,
        )
    record = namespace[context.record_name](1, context.category_names[0], 50)
    records = [record]
    assert namespace["parse_adjusted_value"]("50") == namespace["adjusted_value"](
        record
    )
    namespace["print_report"](records)
    assert len(capsys.readouterr().out.splitlines()) == len(context.category_names)
