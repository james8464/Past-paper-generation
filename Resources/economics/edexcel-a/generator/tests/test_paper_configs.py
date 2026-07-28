from pastpapergen.paper_configs import load_builtin_paper_config


def test_paper_1_matches_core_edexcel_structure():
    config = load_builtin_paper_config("paper_1")

    assert config.code == "9EC0/01"
    assert config.allowed_themes == {1, 3}
    assert config.duration_minutes == 120
    assert config.total_marks == 100
    assert [section.name for section in config.sections] == ["A", "B", "C"]
    assert sum(section.marks for section in config.sections) == 100
    assert config.sections[0].question_marks == [5, 5, 5, 5, 5]
    assert config.sections[0].part_marks == [[4, 1]] * 5
    assert config.sections[1].question_marks == [5, 8, 10, 12, 15]
    assert config.sections[2].question_marks == [25, 25]
    assert config.sections[2].answer_marks == 25


def test_paper_3_uses_all_themes_and_two_data_response_sections():
    config = load_builtin_paper_config("paper_3")

    assert config.code == "9EC0/03"
    assert config.allowed_themes == {1, 2, 3, 4}
    assert config.duration_minutes == 120
    assert config.total_marks == 100
    assert [section.name for section in config.sections] == ["A", "B"]
    assert [section.marks for section in config.sections] == [50, 50]
    assert [section.answer_marks for section in config.sections] == [50, 50]
    assert [section.question_marks for section in config.sections] == [
        [5, 8, 12, 25, 25],
        [5, 8, 12, 25, 25],
    ]


def test_paper_2_matches_the_reference_section_a_part_plan():
    config = load_builtin_paper_config("paper_2")

    assert config.sections[0].part_marks == [
        [1, 2, 2],
        [1, 4],
        [4, 1],
        [1, 4],
        [4, 1],
    ]
    assert config.sections[1].question_marks == [5, 8, 10, 12, 15]
