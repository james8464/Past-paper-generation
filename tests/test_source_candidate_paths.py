import importlib


def module():
    return importlib.import_module("tools.source_candidate_paths")


def test_source_path_weighting_keeps_context_and_whole_pairs_equal_to_generated():
    rows = [
        {
            "id": str(i),
            "marks": m,
            "command_word": "explain",
            "demand_band": "high",
            "response_mode": "structured-reasoning",
            "cognitive_operation": "explain",
        }
        for i, m in enumerate([2, 4, 9, 25, 2, 4, 9, 25, 15, 25, 15, 25, 15, 25])
    ]
    form = module().form_from_items(
        rows,
        family="aqa/economics",
        paper="1",
        year=2025,
        source_id="test",
        source_sha256="a" * 64,
    )
    assert len(form["paths"]) == 6
    assert all(p["marks"] == 80 for p in form["paths"])
    assert all(
        p["observed"]["mark_band_distribution"]
        == {"short": 0.333333, "medium": 0.166667, "extended": 0.5}
        for p in form["paths"]
    )
    assert all(p["assessment_objectives"] is None for p in form["paths"])
    assert form["weighting_basis"] == "equal-path-within-year-equal-year-descriptive"


def test_business_edition_does_not_assume_same_question_numbers():
    for year, marks in [
        (2022, [1] * 15 + [2, 3, 3, 9, 9, 9] + [25] * 4),
        (2025, [1] * 15 + [4, 4, 9, 9, 9] + [25] * 4),
    ]:
        rows = [
            {
                "id": str(i + 1),
                "marks": m,
                "command_word": "explain",
                "demand_band": "high",
                "response_mode": "prose",
                "cognitive_operation": "explain",
            }
            for i, m in enumerate(marks)
        ]
        form = module().form_from_items(
            rows,
            family="aqa/business",
            paper="1",
            year=year,
            source_id="test",
            source_sha256="a" * 64,
        )
        assert len(form["paths"]) == 4
        assert all(p["marks"] == 100 for p in form["paths"])
        assert form["topology"]["sections"][2]["options"][0]["item_ids"] == [
            "22" if year == 2022 else "21"
        ]


def test_ocr_conflicting_grids_are_quarantined_with_original_hashes():
    forms = module().source_forms("ocr/economics", "3")
    conflicts = [f for f in forms if f["status"] == "quarantined"]
    assert {f["year"] for f in conflicts} == {2022, 2023}
    assert all(
        f["paths"] == [] and f["objective_basis"] == "printed-conflicting"
        for f in conflicts
    )
    good = [f for f in forms if f["status"] == "eligible"]
    assert {f["year"] for f in good} == {2024}
    assert good[0]["paths"][0]["assessment_objectives"] == {
        "AO1": 24,
        "AO2": 22,
        "AO3": 18,
        "AO4": 16,
    }


def test_edexcel_source_extraction_does_not_duplicate_overview_and_answer_pages():
    for paper, count, printed in [("1", 2, 125), ("2", 2, 125), ("3", 4, 150)]:
        form = next(
            f
            for f in module().source_forms("pearson-edexcel/economics-a-2015", paper)
            if f["status"] == "eligible"
        )
        assert len(form["paths"]) == count
        assert form["printed_marks"] == printed
        assert all(p["marks"] == 100 for p in form["paths"])


def test_clean_ocr_mcq_rows_keep_published_ao_and_non_retrieval_operations():
    form = next(
        f
        for f in module().source_forms("ocr/economics", "3")
        if f["status"] == "eligible"
    )
    mcqs = form["items"][:30]
    assert {
        ao: sum((row["assessment_objectives"] or {}).get(ao, 0) for row in mcqs)
        for ao in ("AO1", "AO2", "AO3", "AO4")
    } == {"AO1": 15, "AO2": 7, "AO3": 8, "AO4": 0}
    assert mcqs[1]["cognitive_operation"] == "transform"
    assert mcqs[5]["cognitive_operation"] == "analyse"
    assert mcqs[5]["demand_band"] == "unknown"
    assert all(row["learner_demand"] is None for row in form["items"])


def test_aqa_selected_source_operations_do_not_manufacture_objective_tags():
    form = next(
        f for f in module().source_forms("aqa/economics", "3") if f["year"] == 2025
    )
    assert all(i["assessment_objectives"] is None for i in form["items"][:30])
    assert any(i["cognitive_operation"] != "retrieve" for i in form["items"][:30])


def test_source_and_generated_response_modes_use_same_operation_definition():
    from Backend.Core.reference_demand import build_item_demand_target, profile_for

    target = build_item_demand_target(
        {"marks": 9, "command_word": "Explain", "task_operation": "analyse"},
        profile_for("aqa/economics", "1"),
    )
    assert target.response_mode == "structured-reasoning"


def test_edexcel_2024_selected_subparts_use_actual_operations_without_command_leakage():
    form = next(
        f
        for f in module().source_forms("pearson-edexcel/economics-a-2015", "1")
        if f["status"] == "eligible"
    )
    expected = {
        "2": ("1(b)", 3, "transform"),
        "4": ("2(b)", 5, "transform"),
        "6": ("3(b)", 6, "analyse"),
    }
    for row in form["items"]:
        if row["id"] in expected:
            subpart, page, operation = expected[row["id"]]
            assert row["cognitive_operation"] == operation
            assert row["command_word"] == "select"
            assert row["response_mode"] == "selected-response"
            assert row["source_subpart"] == subpart and row["source_page"] == page
            assert row["assessment_objectives"] is None
            assert (
                row["learner_demand"]
                is row["observed_minutes"]
                is row["reasoning_steps"]
                is None
            )
