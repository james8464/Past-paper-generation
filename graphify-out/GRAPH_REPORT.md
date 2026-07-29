# Graph Report - .  (2026-07-29)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 2199 nodes · 6695 edges · 116 communities (88 shown, 28 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 420 edges (avg confidence: 0.74)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1ec477eb`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- benchmark.py
- cspapergen/render_pdf.py
- AppViewModel
- Paragraph
- TerminalProgressReporter
- question_bank.py
- String
- GeneratedPaper
- pastpapergen/generator.py
- ValueError
- BenchmarkChart
- pastpapergen/render_pdf.py
- build_paper_blueprint
- test_render_pdf.py
- reference_corpus.py
- aqaecongen/render_pdf.py
- pastpapergen/ollama_client.py
- test_coverage_matrix.py
- pastpapergen/cli.py
- AppViewModel.swift
- CodingKeys
- TableStyle
- ocrcsgen/generator.py
- PaperCreatorTests
- ocrcsgen/render_pdf.py
- ocregen/generator.py
- aqaecongen/generator.py
- aqaaccountgen/generator.py
- paper_fidelity_audit.py
- generate_package
- test_ollama_generation.py
- PaperBlueprint
- graphs.py
- View
- aqabizgen/generator.py
- BackendClient
- .initialEstimate
- PlainProgressReporter
- test_mark_scheme_layout.py
- pastpapergen/notes.py
- _mark_scheme_rows
- aqa_accounting_calibration.py
- aqa_business_calibration.py
- ocr_economics_calibration.py
- exam_blueprints.py
- _wrap
- difficulty_calibration.py
- progress_reporter
- render_source_booklet
- cspapergen/cli.py
- HeaderPanel
- AIProvider
- cspapergen/generator.py
- mark_scheme_enrichment.py
- cspapergen/notes.py
- paper1_assets.py
- validate_generated_paper
- source_cases.py
- build_layout_masters.py
- NotificationPresenter
- cspapergen/exam_dates.py
- economics_exam_schedule
- generator_working_directory
- _ms_row_height
- xcbuild.sh
- diagnose.sh
- move_to_trash.sh
- run_app_ios_sim.sh
- run_app_macos.sh
- Core/__init__.py
- bootstrap_backend.sh
- build_backend.sh
- clean.sh
- resolve_agent_name.sh
- resolve_sim_destination.sh
- aqaaccountgen/__init__.py
- aqabizgen/__init__.py
- cspapergen/__init__.py
- ocrcsgen/__init__.py
- aqaecongen/__init__.py
- pastpapergen/__init__.py
- ocregen/__init__.py
- tools/__init__.py
- aqa-economics-practice-generator
- cspapergen
- examforge-aqa-accounting
- examforge-aqa-business
- examforge-ocr-computer-science
- ocr-economics-practice-generator
- pastpapergen
- Todo Checkpoint Draft
- _build_part
- TerminalProgressReporter
- ocr_computer_science_calibration.py
- Evidence Bundle Draft
- test_tui.py
- Task Intent Draft
- End-to-end runtime
- Paper creator: deep project analysis
- P1: macOS information architecture and interaction
- Paper creator
- P1: backend and repository architecture
- PlainProgressReporter
- Improvement roadmap
- P0/P1: assessment quality and difficulty
- macOS user-experience audit
- test_aqa_accounting_calibration.py
- test_ocr_computer_science_calibration.py
- P0: make capability and evidence truthful
- P0: visual fidelity
- AGENTS.md
- 95-drift.md
- ExamBoardOption
- .load

## God Nodes (most connected - your core abstractions)
1. `build_paper_blueprint()` - 133 edges
2. `load_builtin_paper_config()` - 119 edges
3. `load_syllabus()` - 118 edges
4. `GeneratedQuestion` - 104 edges
5. `AppViewModel` - 99 edges
6. `GeneratedPaper` - 69 edges
7. `GeneratedOption` - 64 edges
8. `build_question()` - 53 edges
9. `QuestionStyle` - 52 edges
10. `_question()` - 48 edges

## Surprising Connections (you probably didn't know these)
- `generate_package()` --calls--> `emit()`  [INFERRED]
  Resources/business/aqa/generator/aqabizgen/cli.py → Backend/Core/events.py
- `generate_package()` --calls--> `emit()`  [INFERRED]
  Resources/computer-science/aqa/generator/cspapergen/cli.py → Backend/Core/events.py
- `improve_questions_with_ollama()` --calls--> `emit()`  [INFERRED]
  Resources/computer-science/aqa/generator/cspapergen/ollama_client.py → Backend/Core/events.py
- `generate_package()` --calls--> `emit()`  [INFERRED]
  Resources/computer-science/ocr/generator/ocrcsgen/cli.py → Backend/Core/events.py
- `generate_package()` --calls--> `emit()`  [INFERRED]
  Resources/economics/aqa/generator/aqaecongen/cli.py → Backend/Core/events.py

## Import Cycles
- None detected.

## Communities (116 total, 28 thin omitted)

### Community 0 - "benchmark.py"
Cohesion: 0.06
Nodes (86): apple_cpu_core_split(), available_memory_gb(), avg(), clamp(), cpu_brand(), cpu_load_percent(), cpu_probe(), disk_probe() (+78 more)

### Community 1 - "cspapergen/render_pdf.py"
Cohesion: 0.09
Nodes (82): generation_date(), date, Question, _answer_line_count(), _answer_lines(), _answer_lines_paginated(), _candidate_fields(), _continuation_guidance_lines() (+74 more)

### Community 2 - "AppViewModel"
Cohesion: 0.05
Nodes (30): AnyCancellable, DateFormatter, Error, Int32, .body, GeneratedFile, .title, ProgressEntry (+22 more)

### Community 3 - "Paragraph"
Cohesion: 0.11
Nodes (65): GeneratedQuestion, Paragraph, _add_economics_diagram(), _add_firm_objectives_diagram(), _add_ppf_diagram(), _annotation_conventions_page(), AnswerLines, _assessment_allocation() (+57 more)

### Community 4 - "TerminalProgressReporter"
Cohesion: 0.20
Nodes (6): _format_elapsed(), _progress_bar(), ProgressSnapshot, ProgressState, _question_label(), TerminalProgressReporter

### Community 5 - "question_bank.py"
Cohesion: 0.23
Nodes (53): Stimulus, _assembly_program_question(), _assembly_trace_question(), _big_data_question(), _big_data_short_question(), _binary_short_question(), _bitmap_question(), _boolean_question() (+45 more)

### Community 6 - "String"
Cohesion: 0.09
Nodes (40): Decodable, Equatable, Int, BackendEvent, benchmarkDone, benchmarkMetric, benchmarkSample, done (+32 more)

### Community 7 - "GeneratedPaper"
Cohesion: 0.12
Nodes (52): GeneratedPaper, aqa_front_matter_pages(), Flowable, _additional_answer_page(), AnswerLines, _assessment_objectives_page(), _banner(), _box() (+44 more)

### Community 8 - "pastpapergen/generator.py"
Cohesion: 0.11
Nodes (34): _best_section_a_context_point(), _choice_group_name(), _choice_lookup(), _data_response_extract(), _essay_question_prompt(), _exam_context(), _exam_focus(), _first_sentence() (+26 more)

### Community 9 - "ValueError"
Cohesion: 0.13
Nodes (25): _clamp_fitz_rect(), conform_pdf_page_boxes(), conform_pdf_to_box_template(), draw_text_slot(), LayoutConformanceError, load_layout_master(), _page_from_payload(), PageMaster (+17 more)

### Community 10 - "BenchmarkChart"
Cohesion: 0.09
Nodes (33): Charts, KeyPath, BenchmarkChart, .body, BenchmarkLiveCharts, .body, .cpuChart, .cpuThroughputChart (+25 more)

### Community 11 - "pastpapergen/render_pdf.py"
Cohesion: 0.10
Nodes (49): BoardLayout, _axis_labels_for_draw_prompt(), _bar_chart_data(), _bar_label(), _cleanup_graph_cache(), _count_pages(), _draw_axis_arrow(), _draw_bar_chart() (+41 more)

### Community 12 - "build_paper_blueprint"
Cohesion: 0.15
Nodes (45): build_paper_blueprint(), PaperBlueprint, Syllabus, load_builtin_paper_config(), load_syllabus(), Path, Syllabus, test_blueprint_contains_structured_mcq_and_mark_scheme_content() (+37 more)

### Community 13 - "test_render_pdf.py"
Cohesion: 0.14
Nodes (42): render_question_paper(), _blank_axis_lines(), _blueprint_with_section_a_question(), _dark_pixels(), _first_page_containing(), _long_horizontal_line_count(), _normalised(), _pdf_page_count() (+34 more)

### Community 14 - "reference_corpus.py"
Cohesion: 0.14
Nodes (44): MonkeyPatch, Path, test_document_path_requires_filename(), test_document_path_stays_inside_corpus(), test_download_manifest_records_failure_and_continues(), test_parse_aqa_resources_filters_modified_papers(), test_parse_ocr_resources_uses_a_level_tab_only(), test_parse_ocr_specifications_keeps_a_level_not_as_level() (+36 more)

### Community 15 - "aqaecongen/render_pdf.py"
Cohesion: 0.14
Nodes (42): formatted_generation_date(), AnswerLines, _assessment_objectives_table(), _context_data_table(), _context_first_page(), _context_second_page(), _cover(), _document() (+34 more)

### Community 16 - "pastpapergen/ollama_client.py"
Cohesion: 0.13
Nodes (25): MultipleChoiceOption, _mcq_options(), GraphParams, MultipleChoiceOption, PaperBlueprint, BaseModel, QuestionBlueprint, QuestionPart (+17 more)

### Community 17 - "test_coverage_matrix.py"
Cohesion: 0.22
Nodes (21): family(), matrix(), Path, test_catalog_availability_is_owned_only_by_registry(), test_checked_in_matrix_is_deterministic_and_current(), test_existing_generators_are_reported_without_false_verification(), test_matrix_exactly_covers_layout_profiles(), test_no_verified_paper_has_a_failed_gate() (+13 more)

### Community 18 - "pastpapergen/cli.py"
Cohesion: 0.11
Nodes (19): generate_package(), _normalise_paper_id(), _theme_plan(), PaperConfig, PaperBlueprint, Syllabus, _reject_mark_text(), validate_blueprint() (+11 more)

### Community 19 - "AppViewModel.swift"
Cohesion: 0.08
Nodes (17): AppKit, Combine, Foundation, AppDefaults, AppLinks, AppStorageKey, SecretAccount, Bool (+9 more)

### Community 20 - "CodingKeys"
Cohesion: 0.06
Nodes (35): CodingKey, CodingKeys, command, cpuLoad, cpuMBs, detail, diskFreeGB, diskReadMBs (+27 more)

### Community 21 - "TableStyle"
Cohesion: 0.12
Nodes (65): GeneratedOption, BaseModel, _accounting_marking_guidance_pages(), _accounting_system_case(), _accounting_table(), _additional_answer_page(), AnswerLines, _appropriation_answer_table() (+57 more)

### Community 22 - "ocrcsgen/generator.py"
Cohesion: 0.13
Nodes (25): GeneratedSection, generate_package(), Path, load_rule(), _analysis_prompt(), build_paper(), _levels(), _programming_prompt() (+17 more)

### Community 23 - "PaperCreatorTests"
Cohesion: 0.12
Nodes (5): .selectedBoard, PaperCreatorTests, PaperCreator, XCTest, XCTestCase

### Community 24 - "ocrcsgen/render_pdf.py"
Cohesion: 0.14
Nodes (29): register_font(), register_fonts(), _additional_answer_page(), _additional_pages(), AnswerLines, _banner(), _box(), _chrome() (+21 more)

### Community 25 - "ocregen/generator.py"
Cohesion: 0.13
Nodes (27): generate_package(), Path, load_rule(), build_paper(), _evaluation_scheme(), _extract(), _instructions(), _mcq() (+19 more)

### Community 26 - "aqaecongen/generator.py"
Cohesion: 0.15
Nodes (24): generate_package(), main(), Path, load_rule(), _build_mcq_option(), build_paper(), _build_written_option(), _case_depth() (+16 more)

### Community 27 - "aqaaccountgen/generator.py"
Cohesion: 0.14
Nodes (26): field_validator, generate_package(), Path, build_paper(), _extract(), _levels(), _mcq(), _number() (+18 more)

### Community 28 - "paper_fidelity_audit.py"
Cohesion: 0.15
Nodes (27): Document, Pixmap, Path, test_generated_document_supports_app_per_paper_directories(), test_render_diagnostics_are_tolerated_only_for_reference_papers(), test_render_similarity_is_independent_of_pdf_primitive_type(), audit(), compare() (+19 more)

### Community 29 - "generate_package"
Cohesion: 0.10
Nodes (38): generate_package(), build_paper2_blueprint(), load_syllabus(), Path, Syllabus, PaperBlueprint, Syllabus, validate_blueprint() (+30 more)

### Community 30 - "test_ollama_generation.py"
Cohesion: 0.12
Nodes (20): generate_questions_with_ollama(), PaperBlueprint, Syllabus, DriftedPartsOllamaClient, FakeOllamaClient, FigureReferencePartsClient, LabelledVaguePartsClient, NoisyOllamaClient (+12 more)

### Community 31 - "PaperBlueprint"
Cohesion: 0.14
Nodes (28): _answer_line_count(), _draw_answer_lines_until(), _draw_answer_page_header(), _draw_centred_instruction_line(), _draw_continuation_lines(), _draw_paper_3_choice_header(), _draw_paper_3_choice_prompt(), _draw_paper_3_pages() (+20 more)

### Community 32 - "graphs.py"
Cohesion: 0.30
Nodes (26): Axes, ad_as_diagram(), _arrow_axes(), _ax(), circular_flow_diagram(), consumer_producer_surplus(), demand_supply_diagram(), _ensure_style() (+18 more)

### Community 33 - "View"
Cohesion: 0.08
Nodes (28): App, Commands, AppCommands, ContentView, .body, View, PaperCreator, .body (+20 more)

### Community 34 - "aqabizgen/generator.py"
Cohesion: 0.14
Nodes (26): generate_package(), Path, build_paper(), _extract(), _instructions(), _levels(), _mcq(), _number() (+18 more)

### Community 35 - "BackendClient"
Cohesion: 0.17
Nodes (15): LocalizedError, BackendClient, BackendClientError, backendMissing, .errorDescription, pythonMissing, pythonVenvUnreadable, BackendFile (+7 more)

### Community 36 - ".initialEstimate"
Cohesion: 0.19
Nodes (12): EstimateFactor, GenerationEstimate, .etaDate, .remainingText, Date, GenerationEstimator, Bool, Date (+4 more)

### Community 37 - "PlainProgressReporter"
Cohesion: 0.19
Nodes (7): default_output_dir(), main(), Path, PlainProgressReporter, progress_reporter(), TextIO, main()

### Community 38 - "test_mark_scheme_layout.py"
Cohesion: 0.29
Nodes (21): render_mark_scheme(), _blueprint_with_section_a_calculation(), _blueprint_with_section_b_topic(), _pdf_page_count(), _pdf_text(), Path, test_mark_scheme_calculation_rows_include_specific_working(), test_mark_scheme_cover_title_uses_reference_scale_and_position() (+13 more)

### Community 39 - "pastpapergen/notes.py"
Cohesion: 0.20
Nodes (19): _clean_chunk(), essay_capable_topic_ids(), _flush_note_chunk(), _is_exam_point(), _is_note_noise(), _looks_like_heading(), _note_chunks(), note_context_for_topic() (+11 more)

### Community 40 - "_mark_scheme_rows"
Cohesion: 0.16
Nodes (21): _brief_source_evidence(), _calculation_answer_lines(), _draw_source_content_page(), _mark_scheme_rows(), _normalise_mark_point(), _one_mark_points(), _part_mark_scheme_lines(), Syllabus (+13 more)

### Community 41 - "aqa_accounting_calibration.py"
Cohesion: 0.34
Nodes (14): _band(), build_generated_profile(), build_reference_profile(), build_report(), _command(), _fingerprint(), _inventory(), main() (+6 more)

### Community 42 - "aqa_business_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 43 - "ocr_economics_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 44 - "exam_blueprints.py"
Cohesion: 0.26
Nodes (12): PaperRule, QuestionRule, SectionRule, load_rule(), mcqs(), q(), load_rule(), q() (+4 more)

### Community 45 - "_wrap"
Cohesion: 0.17
Nodes (20): _draw_answer_lines(), _draw_calculate_part_with_working_lines(), _draw_compact_part(), _draw_inline_context(), _draw_mcq_part(), _draw_part_prompt(), _draw_section_a_question(), _draw_section_a_total() (+12 more)

### Community 46 - "difficulty_calibration.py"
Cohesion: 0.23
Nodes (16): report(), test_calibration_retains_no_official_text_or_paths(), test_difficulty_is_not_promoted_without_human_and_psychometric_evidence(), test_every_paper_has_multi_seed_structural_evidence(), build_generated_profile(), build_reference_profile(), build_report(), _command() (+8 more)

### Community 47 - "progress_reporter"
Cohesion: 0.27
Nodes (6): main(), default_output_dir(), main(), Path, progress_reporter(), test_default_output_dir_is_downloads()

### Community 48 - "render_source_booklet"
Cohesion: 0.28
Nodes (15): _apply_edexcel_page_boxes(), _extract_source_questions(), Path, Match Pearson question-paper bleed and crop boxes without changing A4 content., render_source_booklet(), _source_sections(), _pdf_page_count(), _pdf_text() (+7 more)

### Community 49 - "cspapergen/cli.py"
Cohesion: 0.18
Nodes (16): MarkingGuidance, MultipleChoiceOption, PaperBlueprint, BaseModel, QuestionPart, Syllabus, SyllabusTopic, _clean() (+8 more)

### Community 50 - "HeaderPanel"
Cohesion: 0.12
Nodes (20): ActivityPanel, .body, DocumentsPanel, .body, GeneratorWorkspace, .body, HeaderPanel, .body (+12 more)

### Community 51 - "AIProvider"
Cohesion: 0.14
Nodes (13): CaseIterable, AIProvider, anthropic, apple, .backendID, .id, ollama, openAI (+5 more)

### Community 52 - "cspapergen/generator.py"
Cohesion: 0.27
Nodes (15): _align_paper1_structure(), build_paper1_blueprint(), _build_paper1_context(), _build_paper1_questions(), _paper1_part(), _paper1_question(), _paper2_marking_checks(), PaperBlueprint (+7 more)

### Community 53 - "mark_scheme_enrichment.py"
Cohesion: 0.38
Nodes (10): _application_label(), _clean_text(), _compact_technical_guidance(), _deduplicate(), enrich_paper(), _enrich_question(), _level_guidance(), _objective_guidance() (+2 more)

### Community 54 - "cspapergen/notes.py"
Cohesion: 0.38
Nodes (9): cache_notes(), discover_note_pdfs(), _extract_text(), note_context_for_topic(), NotesManifest, Path, _topic_prefixes(), test_cache_notes_extracts_text_into_project_cache() (+1 more)

### Community 55 - "paper1_assets.py"
Cohesion: 0.51
Nodes (10): _page_footer(), _paragraph(), _practice_header(), Canvas, PaperBlueprint, Path, render_electronic_answer_document(), render_preliminary_material() (+2 more)

### Community 56 - "validate_generated_paper"
Cohesion: 0.44
Nodes (9): validate_generated_paper(), validate_rule(), test_all_paper_rules_have_exact_candidate_marks_and_syllabus_scope(), paper(), rule(), test_choice_marks_are_candidate_marks_not_all_printed_marks(), test_generated_paper_matches_contract(), test_generated_paper_rejects_duplicate_prompts() (+1 more)

### Community 57 - "source_cases.py"
Cohesion: 0.42
Nodes (8): _article_length_extract(), data_response_extract(), _is_macro_title(), _macro_fallback(), _micro_fallback(), _normalise(), section_c_extract(), _section_c_fallback()

### Community 58 - "build_layout_masters.py"
Cohesion: 0.26
Nodes (19): _box(), _colour(), _content_box(), _drawing_kind(), _drawings(), extract_layout_master(), _furniture_signature(), _images() (+11 more)

### Community 59 - "NotificationPresenter"
Cohesion: 0.25
Nodes (6): NotificationPresenter, NSObject, UNNotification, UNNotificationPresentationOptions, UNUserNotificationCenter, UNUserNotificationCenterDelegate

### Community 60 - "cspapergen/exam_dates.py"
Cohesion: 0.57
Nodes (6): formatted_paper1_exam_date(), formatted_paper2_exam_date(), paper1_exam_date(), paper2_exam_date(), date, test_paper2_exam_date_uses_june_exam_season()

### Community 61 - "economics_exam_schedule"
Cohesion: 0.46
Nodes (6): economics_exam_schedule(), ExamSchedule, formatted_economics_exam_date(), date, _draw_mark_scheme_qualification_page(), test_edexcel_9ec0_2026_timetable_dates()

### Community 62 - "generator_working_directory"
Cohesion: 0.40
Nodes (4): generator_working_directory(), MonkeyPatch, fixture, FixtureRequest

### Community 63 - "_ms_row_height"
Cohesion: 0.70
Nodes (5): _draw_ms_row(), _ms_bold_line(), _ms_centered_line(), _ms_row_height(), _ms_wrap_width()

### Community 64 - "xcbuild.sh"
Cohesion: 0.67
Nodes (3): HOME, xcbuild.sh script, usage()

### Community 92 - "Todo Checkpoint Draft"
Cohesion: 0.12
Nodes (15): Active slice, Blocked on, Completed, Completed AQA Accounting vertical slice, Completed AQA Business vertical slice, Completed calibration slice, Completed OCR Computer Science vertical slice, Completed OCR Economics vertical slice (+7 more)

### Community 93 - "_build_part"
Cohesion: 0.15
Nodes (16): _build_part(), _build_parts(), _choose_topic(), _compatible_stimulus_kind(), _group_prompt(), _indicative_content(), _mark_breakdown(), _mark_scheme() (+8 more)

### Community 94 - "TerminalProgressReporter"
Cohesion: 0.23
Nodes (5): _format_elapsed(), _progress_bar(), ProgressSnapshot, _question_label(), TerminalProgressReporter

### Community 95 - "ocr_computer_science_calibration.py"
Cohesion: 0.34
Nodes (14): _band(), build_generated_profile(), build_reference_profile(), build_report(), _command(), _fingerprint(), _inventory(), main() (+6 more)

### Community 96 - "Evidence Bundle Draft"
Cohesion: 0.14
Nodes (13): AQA Accounting 7127 slice, AQA Business 7132 slice, Coverage slice evidence, Current slice evidence, Difficulty calibration evidence, Evidence Bundle Draft, Evidence limits, Fixed-layout finalisation pass — 27 July 2026 (+5 more)

### Community 97 - "test_tui.py"
Cohesion: 0.27
Nodes (8): ProgressState, test_progress_reporter_uses_plain_output_when_not_tty(), test_progress_reporter_uses_terminal_dashboard_when_tty(), test_progress_state_tracks_overall_process_steps(), test_progress_state_tracks_seed_stage_and_questions(), test_terminal_progress_reporter_renders_fps_dashboard(), TtyBuffer, StringIO

### Community 98 - "Task Intent Draft"
Cohesion: 0.18
Nodes (10): Baseline read set hint, Compatibility boundary, Execution Readiness View, Goal and stop conditions, Impact statement draft, Non-goals, Requested outcome, Retirement boundary (+2 more)

### Community 99 - "End-to-end runtime"
Cohesion: 0.18
Nodes (11): 10. Completion and file handling, 1. Catalogue and selection, 2. Swift state and command construction, 3. Process bridge and event protocol, 4. Backend validation and dispatch, 5. Two different generation architectures, 6. Blueprint construction, 7. Provider behavior (+3 more)

### Community 100 - "Paper creator: deep project analysis"
Cohesion: 0.18
Nodes (11): Architectural pressure points, Current support and readiness, Difficulty and assessment validity, Executive assessment, Fidelity system: strengths and limits, Graphify project map, Paper creator: deep project analysis, Purpose and product boundary (+3 more)

### Community 101 - "P1: macOS information architecture and interaction"
Cohesion: 0.22
Nodes (9): 20. Make the sidebar a true source list, 21. Turn creation into one coherent flow, 22. Use standard Mac commands, 23. Simplify the running state, 24. Implement real recents and document affordances, 25. Restore windows and selection, 26. Make Settings consistent, 27. Complete the accessibility pass (+1 more)

### Community 102 - "Paper creator"
Cohesion: 0.25
Nodes (8): Architecture and quality analysis, Build Checks, CLI, Development Reference Corpus, Paper creator, Privacy, Run, Structure

### Community 103 - "P1: backend and repository architecture"
Cohesion: 0.29
Nodes (7): 14. Introduce a generator plugin API, 15. Split the Swift state owner, 16. Version the bridge protocol, 17. Make output transactional and reproducible, 18. Harden provider adapters, 19. Strengthen dependency and build discipline, P1: backend and repository architecture

### Community 105 - "Improvement roadmap"
Cohesion: 0.33
Nodes (3): Improvement roadmap, P2: high-leverage product improvements, Recommended delivery sequence

### Community 106 - "P0/P1: assessment quality and difficulty"
Cohesion: 0.33
Nodes (6): 10. Constrain paper-level assessment design, 11. Make mark schemes examiner-usable, 12. Calibrate actual difficulty, 13. Create an item bank and exposure controls, 9. Build a specification knowledge model, P0/P1: assessment quality and difficulty

### Community 107 - "macOS user-experience audit"
Cohesion: 0.33
Nodes (6): HIG-specific findings, macOS user-experience audit, Observed first-use sheet, Observed generation state, Observed workspace, What is already Apple-like

### Community 108 - "test_aqa_accounting_calibration.py"
Cohesion: 0.53
Nodes (4): report(), test_both_papers_pass_multi_seed_automated_checks(), test_external_difficulty_gates_remain_false(), test_reference_evidence_is_aggregate_only()

### Community 109 - "test_ocr_computer_science_calibration.py"
Cohesion: 0.53
Nodes (4): report(), test_difficulty_remains_external_evidence_gated(), test_multi_seed_structural_demand_passes(), test_reference_evidence_is_aggregate_only()

### Community 110 - "P0: make capability and evidence truthful"
Cohesion: 0.40
Nodes (5): 1. One generator manifest, 2. Separate “implemented” from “verified”, 3. Freeze the blueprint before generative work, 4. Prove question/scheme consistency, P0: make capability and evidence truthful

### Community 111 - "P0: visual fidelity"
Cohesion: 0.40
Nodes (5): 5. Turn layout masters into composition masters, 6. Use controlled fonts and metrics, 7. Upgrade the fidelity audit, 8. Validate print and PDF behavior, P0: visual fidelity

### Community 114 - "ExamBoardOption"
Cohesion: 0.15
Nodes (18): Hashable, Identifiable, CatalogSubject, ExamBoardOption, .isReady, ExamCatalog, .defaultBoard, .readyBoards (+10 more)

### Community 115 - ".load"
Cohesion: 0.20
Nodes (11): Bundle, CatalogLoader, CatalogLoadError, duplicateBoard, duplicateImplementation, emptyImplementation, .errorDescription, implementationMissingFromCatalog (+3 more)

## Knowledge Gaps
- **223 isolated node(s):** `BoardLayout`, `examforge-aqa-accounting`, `examforge-aqa-business`, `cspapergen`, `examforge-ocr-computer-science` (+218 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `formatted_generation_date()` connect `aqaecongen/render_pdf.py` to `cspapergen/render_pdf.py`, `Paragraph`, `test_mark_scheme_layout.py`, `GeneratedPaper`, `pastpapergen/render_pdf.py`, `test_render_pdf.py`, `render_source_booklet`, `TableStyle`, `paper1_assets.py`, `ocrcsgen/render_pdf.py`, `generate_package`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Why does `build_paper_blueprint()` connect `build_paper_blueprint` to `test_mark_scheme_layout.py`, `pastpapergen/notes.py`, `pastpapergen/generator.py`, `ValueError`, `test_render_pdf.py`, `pastpapergen/ollama_client.py`, `render_source_booklet`, `pastpapergen/cli.py`, `_build_part`, `test_ollama_generation.py`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Why does `emit()` connect `benchmark.py` to `aqabizgen/generator.py`, `cspapergen/cli.py`, `pastpapergen/cli.py`, `ocrcsgen/generator.py`, `ocregen/generator.py`, `aqaecongen/generator.py`, `generate_package`, `test_ollama_generation.py`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Are the 127 inferred relationships involving `Paragraph` (e.g. with `aqa_front_matter_pages()` and `_accounting_marking_guidance_pages()`) actually correct?**
  _`Paragraph` has 127 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `GeneratedQuestion` (e.g. with `AnswerLines` and `AnswerLines`) actually correct?**
  _`GeneratedQuestion` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `BoardLayout`, `examforge-aqa-accounting`, `examforge-aqa-business` to the rest of the system?**
  _223 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `benchmark.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05656565656565657 - nodes in this community are weakly interconnected._
