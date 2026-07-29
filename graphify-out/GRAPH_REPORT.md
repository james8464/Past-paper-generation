# Graph Report - .  (2026-07-29)

## Corpus Check
- 238 files · ~398,774 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2473 nodes · 6862 edges · 154 communities (95 shown, 59 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 404 edges (avg confidence: 0.74)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- AQA CS PDF Rendering
- AQA CS Blueprint Generation
- App Generation State
- App Domain Models
- AQA Accounting Rendering
- OCR Economics Rendering
- AQA Business Rendering
- Edexcel PDF Layout Tests
- Workspace Navigation Views
- Edexcel Question Generation
- Edexcel Blueprint Assembly
- Shared Exam Covers
- Fidelity Audit Tooling
- Reference Corpus Tooling
- AQA Economics Rendering
- Coverage and Calibration
- Backend Event Models
- Improvement Roadmap
- Layout Conformance
- Edexcel Terminal Progress
- OCR Economics Generation
- Backend Benchmarking
- AQA Accounting Generation
- Edexcel Diagram Rendering
- AQA Business Generation
- macOS App Commands
- Benchmark Event Models
- Edexcel Answer Layout
- Benchmark Charts
- Project Runtime Analysis
- Edexcel AI Generation
- Economics Diagram Library
- Edexcel Data Models
- Transactional Generation
- Blueprint Validation
- AQA CS Progress UI
- AQA Economics Generation
- Backend Process Bridge
- Edexcel Mark Schemes
- Generation Estimates
- App Configuration
- Assessment Metadata
- Backend Integration Tests
- Edexcel Notes Parsing
- AQA Accounting Calibration
- AQA Business Calibration
- OCR CS Calibration
- OCR Economics Calibration
- Layout Master Extraction
- Provider Adapters
- macOS App Tests
- Edexcel CLI Pipeline
- Edexcel Source Booklets
- Sidebar and Settings
- OCR CS Generation
- Edexcel Page Composition
- Generator Registry
- Backend Protocol Schema
- Bridge Commands and Events
- Aegis Delivery Checkpoint
- Edexcel Scheme Composition
- Shared Font Assets
- Aegis Evidence Bundle
- Exam Cover Details
- AQA CS CLI Pipeline
- Generation Dates
- Edexcel Validation
- Edexcel AI Validation
- AQA CS Validation
- Edexcel Cover Furniture
- Mark Scheme Enrichment
- App Icon Assets
- Aegis Delivery Intent
- Protocol Event Types
- AQA CS Notes
- AQA CS AI Adapter
- Edexcel Source Cases
- UI Audit Evidence
- Edexcel Scheme Tables
- macOS Notifications
- Secure Secret Storage
- Repository Guide
- AQA CS Exam Dates
- Implementation Evidence
- Protocol Root Schema
- Edexcel Exam Dates
- Protocol Event Envelope
- Test Fixture Setup
- Xcode Build Script
- Protocol Stage Fields
- Protocol Capability List
- Protocol Progress Fields
- mark scheme front matter py
- diagnose sh
- move to trash sh
- run app ios sim sh
- run app macos sh
- Protocol Timestamp
- Core init py
- 95 drift md
- bootstrap backend sh
- build backend sh
- clean sh
- resolve agent name sh
- resolve sim destination sh
- aqaaccountgen init py
- backend version
- aqabizgen init py
- cspapergen init py
- ocrcsgen init py
- aqaecongen init py
- pastpapergen init py
- ocregen init py
- tools init py
- graphify Concept
- ArgumentParser Concept
- BaseModel Concept
- Namespace Concept
- Process Concept
- PaperCreator Xcode Project Configuration
- aqa economics practice generator
- cspapergen Concept
- examforge aqa accounting
- examforge aqa business
- examforge ocr computer science
- ocr economics practice generator
- pastpapergen Concept
- PyInstaller Build Dependency
- QuestionPart Concept
- Nature of Economics
- How Markets Work
- Market Failure
- Government Intervention
- Measures of Economic Performance
- Aggregate Demand
- Aggregate Supply
- National Income
- Economic Growth
- Macroeconomic Objectives and Policies
- Business Growth
- Business Objectives
- Revenues Costs and Profits
- Market Structures
- Labour Markets
- Government Intervention in Business
- International Economics
- Poverty and Inequality
- Emerging and Developing Economies
- The Financial Sector
- Role of the State in
- range Concept
- Page Concept

## God Nodes (most connected - your core abstractions)
1. `GeneratedQuestion` - 108 edges
2. `AppViewModel` - 104 edges
3. `build_paper_blueprint()` - 85 edges
4. `GeneratedPaper` - 74 edges
5. `GeneratedOption` - 64 edges
6. `load_builtin_paper_config()` - 63 edges
7. `load_syllabus()` - 62 edges
8. `build_question()` - 53 edges
9. `QuestionStyle` - 52 edges
10. `_question()` - 48 edges

## Surprising Connections (you probably didn't know these)
- `generate_package()` --calls--> `emit()`  [INFERRED]
  Resources/business/aqa/generator/aqabizgen/cli.py → Backend/Core/events.py
- `generate_package()` --calls--> `emit()`  [INFERRED]
  Resources/computer-science/aqa/generator/cspapergen/cli.py → Backend/Core/events.py
- `generate_package()` --calls--> `emit()`  [INFERRED]
  Resources/computer-science/ocr/generator/ocrcsgen/cli.py → Backend/Core/events.py
- `generate_package()` --calls--> `emit()`  [INFERRED]
  Resources/economics/aqa/generator/aqaecongen/cli.py → Backend/Core/events.py
- `generate_package()` --calls--> `emit()`  [INFERRED]
  Resources/economics/edexcel-a/generator/pastpapergen/cli.py → Backend/Core/events.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Edexcel A Economics Knowledge Corpus** — resources_economics_edexcel_a_generator_data_notes_text_1_1_nature_of_economics_nature_of_economics, resources_economics_edexcel_a_generator_data_notes_text_1_2_how_markets_work_how_markets_work, resources_economics_edexcel_a_generator_data_notes_text_1_3_market_failure_market_failure, resources_economics_edexcel_a_generator_data_notes_text_1_4_government_intervention_government_intervention, resources_economics_edexcel_a_generator_data_notes_text_2_1_measures_of_economic_performance_measures_of_economic_performance, resources_economics_edexcel_a_generator_data_notes_text_2_2_aggregate_demand_aggregate_demand, resources_economics_edexcel_a_generator_data_notes_text_2_3_aggregate_supply_aggregate_supply, resources_economics_edexcel_a_generator_data_notes_text_2_4_national_income_national_income, resources_economics_edexcel_a_generator_data_notes_text_2_5_economic_growth_economic_growth, resources_economics_edexcel_a_generator_data_notes_text_2_6_macroeconomic_objectives_and_policies_macroeconomic_objectives_and_policies, resources_economics_edexcel_a_generator_data_notes_text_3_1_business_growth_business_growth, resources_economics_edexcel_a_generator_data_notes_text_3_2_business_objectives_business_objectives, resources_economics_edexcel_a_generator_data_notes_text_3_3_revenues_costs_and_profits_revenues_costs_and_profits, resources_economics_edexcel_a_generator_data_notes_text_3_4_market_structures_market_structures, resources_economics_edexcel_a_generator_data_notes_text_3_5_labour_markets_labour_markets, resources_economics_edexcel_a_generator_data_notes_text_4_1_international_economics_international_economics, resources_economics_edexcel_a_generator_data_notes_text_4_2_poverty_and_inequality_poverty_and_inequality, resources_economics_edexcel_a_generator_data_notes_text_4_3_emerging_and_developing_economies_emerging_and_developing_economies, resources_economics_edexcel_a_generator_data_notes_text_4_4_the_financial_sector_the_financial_sector, resources_economics_edexcel_a_generator_data_notes_text_4_5_role_of_the_state_in_the_macroeconomy_role_of_the_state_in_the_macroeconomy [EXTRACTED 1.00]
- **Project Analysis and Improvement Evidence** — docs_project_analysis_project_analysis_document, docs_project_analysis_improvement_roadmap_document, docs_project_analysis_implementation_and_fidelity_report_document, docs_project_analysis_ui_audit_document [EXTRACTED 1.00]

## Communities (154 total, 59 thin omitted)

### Community 0 - "AQA CS PDF Rendering"
Cohesion: 0.07
Nodes (91): PaperBlueprint, Path, Canvas, date, extract_pdf_text(), Path, pdf_font_names(), Extract stable reading-order text without a Poppler CLI dependency. (+83 more)

### Community 1 - "AQA CS Blueprint Generation"
Cohesion: 0.10
Nodes (89): build_paper2_blueprint(), Syllabus, PaperBlueprint, _repartition_paper2_question(), _paper2_marking_checks(), build_paper1_blueprint(), _build_paper1_context(), Random (+81 more)

### Community 2 - "App Generation State"
Cohesion: 0.05
Nodes (34): Date, URL, ObservableObject, Double, String, AnyCancellable, URL, Bool (+26 more)

### Community 3 - "App Domain Models"
Cohesion: 0.06
Nodes (65): String, Identifiable, Hashable, Bool, Bundle, Data, Decodable, CaseIterable (+57 more)

### Community 4 - "AQA Accounting Rendering"
Cohesion: 0.13
Nodes (66): Path, Flowable, Table, Drawing, BaseDocTemplate, TableStyle, GeneratedQuestion, GeneratedOption (+58 more)

### Community 5 - "OCR Economics Rendering"
Cohesion: 0.10
Nodes (65): Paragraph, Path, Flowable, Table, Drawing, BaseDocTemplate, render_question_paper(), render_mark_scheme() (+57 more)

### Community 6 - "AQA Business Rendering"
Cohesion: 0.13
Nodes (51): Path, Flowable, Table, Drawing, BaseDocTemplate, GeneratedPaper, render_question_paper(), render_source_booklet() (+43 more)

### Community 7 - "Edexcel PDF Layout Tests"
Cohesion: 0.12
Nodes (48): Path, render_question_paper(), _extra_answer_pages(), _cleanup_graph_cache(), _table_rows(), _blueprint_with_section_a_question(), _normalised(), test_render_question_paper_writes_pdf() (+40 more)

### Community 8 - "Workspace Navigation Views"
Cohesion: 0.07
Nodes (43): .body, String, String, String, SwiftUI, ContentView, View, .body (+35 more)

### Community 9 - "Edexcel Question Generation"
Cohesion: 0.08
Nodes (52): _choice_lookup(), _choose_topic(), Random, _theme_plan(), _paper_3_context_plan(), _topics_for_theme(), _section_templates(), _stimulus_pool() (+44 more)

### Community 10 - "Edexcel Blueprint Assembly"
Cohesion: 0.13
Nodes (47): build_paper_blueprint(), Syllabus, PaperBlueprint, load_builtin_paper_config(), load_syllabus(), Path, Syllabus, test_blueprint_is_deterministic_for_seed() (+39 more)

### Community 11 - "Shared Exam Covers"
Cohesion: 0.10
Nodes (40): generate_package(), Path, load_rule(), Path, Flowable, Table, BaseDocTemplate, CoverProfile (+32 more)

### Community 12 - "Fidelity Audit Tooling"
Cohesion: 0.11
Nodes (44): Path, Document, Any, Pixmap, Path, .body, test_generated_document_supports_app_per_paper_directories(), test_render_similarity_is_independent_of_pdf_primitive_type() (+36 more)

### Community 13 - "Reference Corpus Tooling"
Cohesion: 0.14
Nodes (44): test_parse_aqa_resources_filters_modified_papers(), test_document_path_stays_inside_corpus(), Path, test_document_path_requires_filename(), test_parse_ocr_resources_uses_a_level_tab_only(), test_parse_ocr_specifications_keeps_a_level_not_as_level(), test_parse_pearson_resource_keeps_public_question_paper(), test_parse_pearson_resource_rejects_secure_and_quotes_public_paths() (+36 more)

### Community 14 - "AQA Economics Rendering"
Cohesion: 0.13
Nodes (42): Path, Flowable, Table, BaseDocTemplate, Drawing, render_question_paper(), render_source_booklet(), render_mark_scheme() (+34 more)

### Community 15 - "Coverage and Calibration"
Cohesion: 0.11
Nodes (37): matrix(), family(), test_matrix_exactly_covers_layout_profiles(), test_existing_generators_are_reported_without_false_verification(), test_unimplemented_family_is_reference_profiled(), test_checked_in_matrix_is_deterministic_and_current(), test_registry_rejects_unknown_layout_family(), test_registry_rejects_missing_gate() (+29 more)

### Community 16 - "Backend Event Models"
Cohesion: 0.05
Nodes (41): CodingKey, CodingKeys, protocolVersion, type, eventID, timestamp, jobID, backendVersion (+33 more)

### Community 17 - "Improvement Roadmap"
Cohesion: 0.11
Nodes (30): _question(), _sections(), Path, Path, BaseModel, SectionRule, PaperRule, MarkSchemePoint (+22 more)

### Community 18 - "Layout Conformance"
Cohesion: 0.06
Nodes (36): Improvement roadmap, Implementation status — 29 July 2026, P0: make capability and evidence truthful, 1. One generator manifest, 2. Separate “implemented” from “verified”, 3. Freeze the blueprint before generative work, 4. Prove question/scheme consistency, P0: visual fidelity (+28 more)

### Community 19 - "Edexcel Terminal Progress"
Cohesion: 0.13
Nodes (26): Path, Path, Any, Path, conform_generated_documents(), LayoutConformanceError, Rect, TextSlot (+18 more)

### Community 20 - "OCR Economics Generation"
Cohesion: 0.11
Nodes (16): ProgressSnapshot, ProgressState, PlainProgressReporter, TextIO, TerminalProgressReporter, progress_reporter(), _question_label(), _progress_bar() (+8 more)

### Community 21 - "Backend Benchmarking"
Cohesion: 0.11
Nodes (25): generate_package(), Path, q(), load_rule(), build_paper(), Syllabus, _written_option(), Topic (+17 more)

### Community 22 - "AQA Accounting Generation"
Cohesion: 0.12
Nodes (33): handle_benchmark(), Namespace, emit_static_metrics(), emit_final_metrics(), Sample, cpu_probe(), disk_probe(), Path (+25 more)

### Community 23 - "Edexcel Diagram Rendering"
Cohesion: 0.11
Nodes (32): BoardLayout, _draw_paper_3_source_page(), _draw_paper_3_extract(), _paper_3_values(), _draw_paper_3_line_figure(), _draw_paper_3_bar_figure(), _draw_paper_3_series(), _draw_paper_3_table_figure() (+24 more)

### Community 24 - "AQA Business Generation"
Cohesion: 0.13
Nodes (27): generate_package(), Path, load_rule(), build_paper(), Syllabus, _number(), _values(), Random (+19 more)

### Community 25 - "macOS App Commands"
Cohesion: 0.13
Nodes (27): generate_package(), Path, load_rule(), build_paper(), Syllabus, _values(), Random, _number() (+19 more)

### Community 26 - "Benchmark Event Models"
Cohesion: 0.09
Nodes (23): Commands, App, Scene, AppCommands, PaperCreator, .body, SettingsPane, .body (+15 more)

### Community 27 - "Edexcel Answer Layout"
Cohesion: 0.10
Nodes (26): Equatable, Double, Int, BenchmarkVerdictSummary, .body, .scoreGauge, .verdictText, OllamaState (+18 more)

### Community 28 - "Benchmark Charts"
Cohesion: 0.17
Nodes (29): Canvas, _draw_paper_3_question_summary(), _draw_paper_3_choice_header(), _draw_paper_3_choice_prompt(), _draw_section_b_prompt_page(), _draw_section_b_extract_block(), _draw_section_c_choice_page(), _draw_centred_instruction_line() (+21 more)

### Community 29 - "Project Runtime Analysis"
Cohesion: 0.12
Nodes (24): Charts, BenchmarkWorkspace, .body, BenchmarkOverviewPanel, .body, BenchmarkLiveCharts, .body, .cpuChart (+16 more)

### Community 30 - "Edexcel AI Generation"
Cohesion: 0.07
Nodes (28): Paper creator: deep project analysis, Executive assessment, Purpose and product boundary, End-to-end runtime, 1. Catalogue and selection, 2. Swift state and command construction, 3. Process bridge and event protocol, 4. Backend validation and dispatch (+20 more)

### Community 31 - "Economics Diagram Library"
Cohesion: 0.12
Nodes (20): PaperBlueprint, Syllabus, FakeOllamaClient, NoisyOllamaClient, DriftedPartsOllamaClient, OverlongSectionASourceClient, ShortSectionBSourceClient, LabelledVaguePartsClient (+12 more)

### Community 32 - "Edexcel Data Models"
Cohesion: 0.30
Nodes (26): _ensure_style(), _save(), _ax(), Axes, _arrow_axes(), _label(), _eq_point(), _gp() (+18 more)

### Community 33 - "Transactional Generation"
Cohesion: 0.14
Nodes (16): SyllabusTopic, BaseModel, Syllabus, SectionConfig, QuestionPart, MultipleChoiceOption, GraphParams, PaperConfig (+8 more)

### Community 34 - "Blueprint Validation"
Cohesion: 0.18
Nodes (23): Path, progress_emitter(), GenerationCancelled, Exception, _cancel_generation(), Any, handle_generate(), Namespace (+15 more)

### Community 35 - "AQA CS Progress UI"
Cohesion: 0.13
Nodes (8): ProgressSnapshot, ProgressState, PlainProgressReporter, TextIO, TerminalProgressReporter, _question_label(), _progress_bar(), _format_elapsed()

### Community 36 - "AQA Economics Generation"
Cohesion: 0.19
Nodes (21): generate_package(), Path, main(), load_rule(), build_paper(), Syllabus, _build_written_option(), Topic (+13 more)

### Community 37 - "Backend Process Bridge"
Cohesion: 0.17
Nodes (15): LocalizedError, BackendClientError, backendMissing, pythonMissing, pythonVenvUnreadable, String, .errorDescription, BackendClient (+7 more)

### Community 38 - "Edexcel Mark Schemes"
Cohesion: 0.25
Nodes (23): Path, render_mark_scheme(), _pad_mark_scheme_pages(), _draw_mark_scheme_end_page(), test_mark_scheme_uses_reference_style_sections(), test_mark_scheme_has_subquestion_tables_mcq_explanations_and_levels(), test_mark_scheme_front_matter_matches_reference_structure(), test_mark_scheme_cover_uses_reference_serif_face() (+15 more)

### Community 39 - "Generation Estimates"
Cohesion: 0.19
Nodes (11): TimeInterval, String, Bool, Double, Date, ProcessInfo, EstimateFactor, GenerationEstimate (+3 more)

### Community 40 - "App Configuration"
Cohesion: 0.11
Nodes (12): Foundation, URL, String, Bool, AppDefaults, AppStorageKey, SecretAccount, AppLinks (+4 more)

### Community 41 - "Assessment Metadata"
Cohesion: 0.23
Nodes (20): CompletedProcess, Path, run_bridge(), run_bridge_raw(), test_relative_output_is_resolved_from_callers_working_directory(), test_output_path_preserves_sandbox_style_symlink(), test_ollama_status_emits_json(), test_economics_dry_run_generates_expected_files() (+12 more)

### Community 42 - "Backend Integration Tests"
Cohesion: 0.20
Nodes (19): note_file_for_topic(), Path, note_context_for_topic(), note_points_for_topic(), essay_capable_topic_ids(), _note_prefix(), _note_text(), _ranked_note_chunks() (+11 more)

### Community 43 - "Edexcel Notes Parsing"
Cohesion: 0.21
Nodes (18): report(), test_reference_evidence_is_aggregate_only(), test_both_papers_pass_multi_seed_automated_checks(), test_external_difficulty_gates_remain_false(), _command(), _text(), Path, _pages() (+10 more)

### Community 44 - "AQA Accounting Calibration"
Cohesion: 0.21
Nodes (18): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_every_paper_has_multi_seed_structural_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), _command(), _page_count(), Path, _pdf_text() (+10 more)

### Community 45 - "AQA Business Calibration"
Cohesion: 0.21
Nodes (18): report(), test_reference_evidence_is_aggregate_only(), test_multi_seed_structural_demand_passes(), test_difficulty_remains_external_evidence_gated(), _command(), _page_count(), Path, _pdf_text() (+10 more)

### Community 46 - "OCR CS Calibration"
Cohesion: 0.21
Nodes (18): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_every_paper_has_multi_seed_structural_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), _command(), _page_count(), Path, _pdf_text() (+10 more)

### Community 47 - "OCR Economics Calibration"
Cohesion: 0.26
Nodes (19): _round_rect(), _colour(), Any, _line_role(), Page, _text_lines(), _drawing_kind(), _drawings() (+11 more)

### Community 48 - "Layout Master Extraction"
Cohesion: 0.11
Nodes (5): XCTestCase, .selectedBoard, XCTest, PaperCreator, PaperCreatorTests

### Community 49 - "Provider Adapters"
Cohesion: 0.19
Nodes (10): main(), default_output_dir(), Path, main(), generate_package(), _normalise_paper_id(), test_generate_package_without_seed_does_not_write_audit(), test_generate_package_reports_rendering_progress() (+2 more)

### Community 50 - "macOS App Tests"
Cohesion: 0.21
Nodes (19): Path, Syllabus, Path, _apply_edexcel_page_boxes(), render_source_booklet(), _extract_source_questions(), _draw_source_content_page(), _source_sections() (+11 more)

### Community 51 - "Edexcel CLI Pipeline"
Cohesion: 0.20
Nodes (13): Any, HostedLLMClient, hosted_client(), provider_title(), urllib_request(), parse_json_object(), _read_json_response(), _retry_delay() (+5 more)

### Community 52 - "Edexcel Source Booklets"
Cohesion: 0.15
Nodes (11): .body, .body, Sidebar, .body, String, Binding, Bool, Set (+3 more)

### Community 53 - "Sidebar and Settings"
Cohesion: 0.21
Nodes (15): _technical_focus(), _analysis_prompt(), _programming_prompt(), build_paper(), Syllabus, _stimulus(), Topic, Random (+7 more)

### Community 54 - "OCR CS Generation"
Cohesion: 0.24
Nodes (18): PaperBlueprint, _count_pages(), _draw_question_pages(), _draw_paper_3_pages(), _draw_trailing_blank_pages(), _draw_formula_appendix(), _force_new_page_after_question(), _draw_section_b_source_pages() (+10 more)

### Community 55 - "Edexcel Page Composition"
Cohesion: 0.29
Nodes (13): Any, api_models(), ollama_command(), handle_ollama_status(), Namespace, handle_list_models(), handle_pull_model(), build_parser() (+5 more)

### Community 56 - "Generator Registry"
Cohesion: 0.25
Nodes (12): ValueError, generator_capabilities(), generator_capability(), generator_subjects(), _capability(), Any, _relative_path(), test_registry_is_the_canonical_backend_subject_list() (+4 more)

### Community 57 - "Backend Protocol Schema"
Cohesion: 0.12
Nodes (17): properties, protocol, const, type, event_id, type, minimum, job_id (+9 more)

### Community 58 - "Bridge Commands and Events"
Cohesion: 0.21
Nodes (17): _mark_scheme_rows(), _split_mark_scheme_row(), _part_mark_scheme_lines(), _question_mark_scheme_lines(), _one_mark_points(), _source_application_points(), _twelve_mark_knowledge_lines(), _twelve_mark_evaluation_lines() (+9 more)

### Community 59 - "Aegis Delivery Checkpoint"
Cohesion: 0.12
Nodes (15): Todo Checkpoint Draft, Current todo, Completed, Completed slices, Completed vertical slice, Completed calibration slice, Completed OCR Economics vertical slice, Completed OCR Computer Science vertical slice (+7 more)

### Community 60 - "Edexcel Scheme Composition"
Cohesion: 0.35
Nodes (12): register_font(), register_fonts(), write_paper1_supporting_files(), PaperBlueprint, Path, render_preliminary_material(), render_electronic_answer_document(), _practice_header() (+4 more)

### Community 61 - "Shared Font Assets"
Cohesion: 0.14
Nodes (13): Evidence Bundle Draft, Fixed-layout finalisation pass — 27 July 2026, Retained verified evidence, Coverage slice evidence, Current slice evidence, Paper 1 slice evidence, Evidence limits, Shared blueprint and AQA Economics slice (+5 more)

### Community 62 - "Aegis Evidence Bundle"
Cohesion: 0.31
Nodes (3): QuestionPaperCover, _wrap(), Fixed-grid, board-shaped front page without copying protected artwork.

### Community 63 - "Exam Cover Details"
Cohesion: 0.33
Nodes (9): default_output_dir(), Path, main(), generate_package(), progress_reporter(), main(), test_generate_package_writes_question_paper_and_mark_scheme_only(), test_generated_pdfs_are_a4() (+1 more)

### Community 64 - "AQA CS CLI Pipeline"
Cohesion: 0.32
Nodes (8): date, generation_date(), formatted_generation_date(), formatted_generation_series(), Return the month/year form used on mark-scheme covers., test_generation_date_defaults_to_today(), test_generation_date_accepts_iso_override(), test_generation_date_rejects_invalid_override()

### Community 65 - "Generation Dates"
Cohesion: 0.27
Nodes (10): PaperBlueprint, Syllabus, test_validate_blueprint_accepts_generated_paper(), test_validate_blueprint_rejects_topic_outside_paper_themes(), test_validate_blueprint_rejects_unstructured_mcq(), test_validate_blueprint_rejects_llm_mark_text_in_prompt(), validate_blueprint(), PaperConfig (+2 more)

### Community 66 - "Edexcel Validation"
Cohesion: 0.33
Nodes (11): QuestionBlueprint, _parts_for_prompt(), _merge_parts(), _merge_text_list(), _clean_prompt(), _merge_part_prompt(), _strip_part_label(), _merge_question_text() (+3 more)

### Community 67 - "Edexcel AI Validation"
Cohesion: 0.20
Nodes (5): PaperBlueprint, Syllabus, validate_blueprint(), test_validation_rejects_missing_part_mark_scheme(), test_paper1_blueprint_is_deterministic_and_totals_100()

### Community 68 - "AQA CS Validation"
Cohesion: 0.23
Nodes (12): _draw_cover(), _draw_turn_over(), _exam_date_line(), _exam_session(), _draw_boxes(), _draw_front_section(), _draw_crop_marks(), _encode_barcode() (+4 more)

### Community 69 - "Edexcel Cover Furniture"
Cohesion: 0.38
Nodes (10): enrich_paper(), Any, _enrich_question(), _compact_technical_guidance(), _objective_guidance(), _level_guidance(), _application_label(), _clean_text() (+2 more)

### Community 70 - "Mark Scheme Enrichment"
Cohesion: 0.18
Nodes (11): Glossy Black Fountain Pen App Icon Master, Paper Creator App Icon AppIcon-128x128@1x, Paper Creator App Icon AppIcon-128x128@2x, Paper Creator App Icon AppIcon-16x16@1x, Paper Creator App Icon AppIcon-16x16@2x, Paper Creator App Icon AppIcon-256x256@1x, Paper Creator App Icon AppIcon-256x256@2x, Paper Creator App Icon AppIcon-32x32@1x (+3 more)

### Community 71 - "App Icon Assets"
Cohesion: 0.18
Nodes (10): Task Intent Draft, Requested outcome, Scope, Non-goals, Goal and stop conditions, Compatibility boundary, Retirement boundary, Baseline read set hint (+2 more)

### Community 72 - "Aegis Delivery Intent"
Cohesion: 0.18
Nodes (11): enum, hello, progress, file, done, error, models, ollama_status (+3 more)

### Community 73 - "Protocol Event Types"
Cohesion: 0.38
Nodes (9): NotesManifest, discover_note_pdfs(), Path, cache_notes(), note_context_for_topic(), _topic_prefixes(), _extract_text(), test_discovers_local_cs_notes_folder() (+1 more)

### Community 74 - "AQA CS Notes"
Cohesion: 0.33
Nodes (9): PaperBlueprint, Syllabus, OllamaClient, improve_questions_with_ollama(), _prompt(), Question, _merge_question(), _text_list() (+1 more)

### Community 75 - "AQA CS AI Adapter"
Cohesion: 0.36
Nodes (9): _section_c_extract(), data_response_extract(), section_c_extract(), _normalise(), _is_macro_title(), _article_length_extract(), _micro_fallback(), _macro_fallback() (+1 more)

### Community 76 - "Edexcel Source Cases"
Cohesion: 0.22
Nodes (9): macOS UI audit, Scope, Step 1 — deterministic paper workspace, Step 2 — AI-assisted paper blocked on Ollama, Step 3 — Settings, Apple HIG alignment, Evidence limits, Paper Creator Deterministic Workspace Screenshot (+1 more)

### Community 77 - "UI Audit Evidence"
Cohesion: 0.25
Nodes (6): NSObject, UNUserNotificationCenterDelegate, UNUserNotificationCenter, UNNotification, UNNotificationPresentationOptions, NotificationPresenter

### Community 78 - "Edexcel Scheme Tables"
Cohesion: 0.39
Nodes (4): Security, SecretStore, String, Any

### Community 79 - "macOS Notifications"
Cohesion: 0.25
Nodes (8): Paper creator, Run, Build Checks, Development Reference Corpus, CLI, Structure, Architecture and quality analysis, Privacy

### Community 80 - "Secure Secret Storage"
Cohesion: 0.57
Nodes (6): paper2_exam_date(), date, formatted_paper2_exam_date(), paper1_exam_date(), formatted_paper1_exam_date(), test_paper2_exam_date_uses_june_exam_season()

### Community 81 - "Repository Guide"
Cohesion: 0.36
Nodes (8): _draw_ms_blank_page(), _draw_ms_table_header(), _draw_ms_row(), _draw_ms_header_box(), _ms_row_height(), _ms_wrap_width(), _ms_centered_line(), _ms_bold_line()

### Community 82 - "AQA CS Exam Dates"
Cohesion: 0.48
Nodes (5): q(), mcqs(), q(), _q(), QuestionRule

### Community 83 - "Implementation Evidence"
Cohesion: 0.29
Nodes (7): Implementation and fidelity report, Outcome, Implemented changes, Full-matrix validation, Manual PDF review, What code cannot honestly prove, Highest-value next engineering work

### Community 84 - "Protocol Root Schema"
Cohesion: 0.29
Nodes (6): $schema, $id, title, type, allOf, additionalProperties

### Community 85 - "Edexcel Exam Dates"
Cohesion: 0.57
Nodes (5): ExamSchedule, economics_exam_schedule(), formatted_economics_exam_date(), date, test_edexcel_9ec0_2026_timetable_dates()

### Community 86 - "Protocol Event Envelope"
Cohesion: 0.33
Nodes (6): required, protocol, type, event_id, timestamp, job_id

### Community 87 - "Test Fixture Setup"
Cohesion: 0.40
Nodes (4): fixture, generator_working_directory(), FixtureRequest, MonkeyPatch

### Community 88 - "Xcode Build Script"
Cohesion: 0.67
Nodes (3): xcbuild.sh script, usage(), HOME

### Community 89 - "Protocol Stage Fields"
Cohesion: 0.50
Nodes (4): stage, type, string, null

### Community 90 - "Protocol Capability List"
Cohesion: 0.50
Nodes (4): capabilities, type, items, type

### Community 91 - "Protocol Progress Fields"
Cohesion: 0.50
Nodes (4): progress, type, minimum, maximum

### Community 97 - "Protocol Timestamp"
Cohesion: 0.67
Nodes (3): timestamp, type, format

## Knowledge Gaps
- **334 isolated node(s):** `BoardLayout`, `examforge-aqa-accounting`, `examforge-aqa-business`, `cspapergen`, `examforge-ocr-computer-science` (+329 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **59 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AppViewModel` connect `App Generation State` to `App Domain Models`, `Generation Estimates`, `App Configuration`, `Workspace Navigation Views`, `Layout Master Extraction`, `Edexcel Source Booklets`, `Benchmark Event Models`, `Edexcel Answer Layout`, `Project Runtime Analysis`?**
  _High betweenness centrality (0.111) - this node is a cross-community bridge._
- **Why does `formatted_generation_date()` connect `AQA CS CLI Pipeline` to `AQA CS PDF Rendering`, `Edexcel AI Validation`, `AQA Accounting Rendering`, `AQA CS Validation`, `AQA Business Rendering`, `Edexcel Mark Schemes`, `Edexcel PDF Layout Tests`, `OCR Economics Rendering`, `Shared Exam Covers`, `AQA Economics Rendering`, `macOS App Tests`, `Edexcel Diagram Rendering`, `Edexcel Scheme Composition`, `Aegis Evidence Bundle`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Why does `LayoutConformanceError` connect `Edexcel Terminal Progress` to `Generator Registry`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Are the 120 inferred relationships involving `Paragraph` (e.g. with `aqa_front_matter_pages()` and `_accounting_marking_guidance_pages()`) actually correct?**
  _`Paragraph` has 120 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `GeneratedQuestion` (e.g. with `AnswerLines` and `AnswerLines`) actually correct?**
  _`GeneratedQuestion` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `AppViewModel` (e.g. with `OllamaState` and `PaperCreator`) actually correct?**
  _`AppViewModel` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `BoardLayout`, `examforge-aqa-accounting`, `examforge-aqa-business` to the rest of the system?**
  _334 weakly-connected nodes found - possible documentation gaps or missing edges._