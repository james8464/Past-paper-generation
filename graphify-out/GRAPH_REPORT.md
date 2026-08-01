# Graph Report - .  (2026-08-01)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 2680 nodes · 7830 edges · 145 communities (95 shown, 50 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 509 edges (avg confidence: 0.72)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `08589b12`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cspapergen/render_pdf.py
- formatted_generation_date
- AppViewModel
- AIProvider
- Paragraph
- GeneratedQuestion
- GeneratedPaper
- test_render_pdf.py
- GeneratedFile
- pastpapergen/generator.py
- build_paper_blueprint
- ocrcsgen/render_pdf.py
- paper_fidelity_audit.py
- reference_corpus.py
- aqaecongen/render_pdf.py
- test_coverage_matrix.py
- CodingKeys
- exam_blueprints.py
- Improvement roadmap
- Rect
- .appStoreWorkingFolder
- ocregen/generator.py
- benchmark.py
- Canvas
- aqaaccountgen/generator.py
- aqabizgen/generator.py
- SwiftUI
- String
- View
- ValueError
- Paper creator: deep project analysis
- ai_assessment.py
- graphs.py
- pastpapergen/ollama_client.py
- generation.py
- TerminalProgressReporter
- aqaecongen/generator.py
- BackendClient
- test_mark_scheme_layout.py
- .initialEstimate
- AppViewModel.swift
- test_app_backend.py
- pastpapergen/notes.py
- aqa_accounting_calibration.py
- aqa_business_calibration.py
- pastpapergen/render_pdf.py
- ocr_economics_calibration.py
- Sidebar
- PaperCreatorTests
- Q: How does the generation quality pipeline connect?
- render_source_booklet
- providers.py
- Q: Where should performance and generated-paper accuracy fixes be made?
- ocrcsgen/generator.py
- PaperBlueprint
- emit
- generator_capabilities
- properties
- _mark_scheme_rows
- Todo Checkpoint Draft
- Q: How is the macOS backend bundle kept complete?
- Evidence Bundle Draft
- psychometrics.py
- question_bank.py
- ocr_computer_science_calibration.py
- test_ollama_generation.py
- .load
- Architecture
- _draw_cover
- mark_scheme_enrichment.py
- Glossy Black Fountain Pen App Icon Master
- Task Intent Draft
- enum
- Assessment quality and originality
- validate_pdf_for_release
- macOS interaction and HIG compliance
- macOS UI audit
- NotificationPresenter
- Q: how can we make even more improvements to get the highest similarity in terms of structure and layout and quality of questions etc. and maybe all of the files in the project can be better organised. and the UI can be made to be much better and more geometrically apple-like by strictly following every single rule they outline in their HIG
- Paper creator
- cspapergen/exam_dates.py
- pull_request_template.md
- _draw_source_content_page
- Implementation and fidelity report
- backend-protocol.schema.json
- register_fonts
- required
- generator_working_directory
- xcbuild.sh
- type
- capabilities
- progress
- diagnose.sh
- move_to_trash.sh
- run_app_ios_sim.sh
- run_app_macos.sh
- timestamp
- Core/__init__.py
- 95-drift.md
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
- graphify
- PaperCreator Xcode Project Configuration
- aqa-economics-practice-generator
- cspapergen
- examforge-aqa-accounting
- examforge-aqa-business
- examforge-ocr-computer-science
- ocr-economics-practice-generator
- pastpapergen
- PyInstaller Build Dependency
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
- Revenues, Costs and Profits
- Market Structures
- Labour Markets
- Government Intervention in Business
- International Economics
- Poverty and Inequality
- Emerging and Developing Economies
- The Financial Sector
- Role of the State in the Macroeconomy

## God Nodes (most connected - your core abstractions)
1. `GeneratedQuestion` - 131 edges
2. `build_paper_blueprint()` - 124 edges
3. `load_builtin_paper_config()` - 110 edges
4. `load_syllabus()` - 109 edges
5. `AppViewModel` - 107 edges
6. `GeneratedPaper` - 80 edges
7. `GeneratedOption` - 72 edges
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

## Hyperedges (group relationships)
- **Edexcel A Economics Knowledge Corpus** — resources_economics_edexcel_a_generator_data_notes_text_1_1_nature_of_economics_nature_of_economics, resources_economics_edexcel_a_generator_data_notes_text_1_2_how_markets_work_how_markets_work, resources_economics_edexcel_a_generator_data_notes_text_1_3_market_failure_market_failure, resources_economics_edexcel_a_generator_data_notes_text_1_4_government_intervention_government_intervention, resources_economics_edexcel_a_generator_data_notes_text_2_1_measures_of_economic_performance_measures_of_economic_performance, resources_economics_edexcel_a_generator_data_notes_text_2_2_aggregate_demand_aggregate_demand, resources_economics_edexcel_a_generator_data_notes_text_2_3_aggregate_supply_aggregate_supply, resources_economics_edexcel_a_generator_data_notes_text_2_4_national_income_national_income, resources_economics_edexcel_a_generator_data_notes_text_2_5_economic_growth_economic_growth, resources_economics_edexcel_a_generator_data_notes_text_2_6_macroeconomic_objectives_and_policies_macroeconomic_objectives_and_policies, resources_economics_edexcel_a_generator_data_notes_text_3_1_business_growth_business_growth, resources_economics_edexcel_a_generator_data_notes_text_3_2_business_objectives_business_objectives, resources_economics_edexcel_a_generator_data_notes_text_3_3_revenues_costs_and_profits_revenues_costs_and_profits, resources_economics_edexcel_a_generator_data_notes_text_3_4_market_structures_market_structures, resources_economics_edexcel_a_generator_data_notes_text_3_5_labour_markets_labour_markets, resources_economics_edexcel_a_generator_data_notes_text_4_1_international_economics_international_economics, resources_economics_edexcel_a_generator_data_notes_text_4_2_poverty_and_inequality_poverty_and_inequality, resources_economics_edexcel_a_generator_data_notes_text_4_3_emerging_and_developing_economies_emerging_and_developing_economies, resources_economics_edexcel_a_generator_data_notes_text_4_4_the_financial_sector_the_financial_sector, resources_economics_edexcel_a_generator_data_notes_text_4_5_role_of_the_state_in_the_macroeconomy_role_of_the_state_in_the_macroeconomy [EXTRACTED 1.00]
- **Project Analysis and Improvement Evidence** — docs_project_analysis_project_analysis_document, docs_project_analysis_improvement_roadmap_document, docs_project_analysis_implementation_and_fidelity_report_document, docs_project_analysis_ui_audit_document [EXTRACTED 1.00]

## Communities (145 total, 50 thin omitted)

### Community 0 - "cspapergen/render_pdf.py"
Cohesion: 0.10
Nodes (78): Question, _answer_line_count(), _answer_lines(), _answer_lines_paginated(), _candidate_fields(), _continuation_guidance_lines(), _cover_page(), _cover_section() (+70 more)

### Community 1 - "formatted_generation_date"
Cohesion: 0.12
Nodes (23): MarkSchemeCover, QuestionPaperCover, Fixed-grid, board-shaped front page without copying protected artwork., _wrap(), formatted_generation_date(), formatted_generation_series(), generation_date(), date (+15 more)

### Community 2 - "AppViewModel"
Cohesion: 0.05
Nodes (23): AnyCancellable, Binding, DateFormatter, .body, WelcomeSheet, .body, AISettingsTab, .body (+15 more)

### Community 3 - "AIProvider"
Cohesion: 0.15
Nodes (12): CaseIterable, AIProvider, anthropic, apple, .backendID, .id, ollama, openAI (+4 more)

### Community 4 - "Paragraph"
Cohesion: 0.12
Nodes (67): GeneratedOption, aqa_front_matter_pages(), Flowable, Paragraph, _accounting_marking_guidance_pages(), _accounting_system_case(), _accounting_table(), _additional_answer_page() (+59 more)

### Community 5 - "GeneratedQuestion"
Cohesion: 0.10
Nodes (65): GeneratedQuestion, _add_economics_diagram(), _add_firm_objectives_diagram(), _add_ppf_diagram(), _annotation_conventions_page(), AnswerLines, _assessment_allocation(), _assessment_grid_groups() (+57 more)

### Community 6 - "GeneratedPaper"
Cohesion: 0.13
Nodes (53): GeneratedPaper, _additional_answer_page(), AnswerLines, _ao_summary(), _assessment_objectives_page(), _banner(), _box(), _break_even_diagram() (+45 more)

### Community 7 - "test_render_pdf.py"
Cohesion: 0.12
Nodes (46): _cleanup_graph_cache(), render_question_paper(), _table_rows(), _blank_axis_lines(), _blueprint_with_section_a_question(), _dark_pixels(), _first_page_containing(), _long_horizontal_line_count() (+38 more)

### Community 8 - "GeneratedFile"
Cohesion: 0.10
Nodes (17): Error, Int32, .body, .body, GeneratedFile, .exists, .paperDescription, .title (+9 more)

### Community 9 - "pastpapergen/generator.py"
Cohesion: 0.07
Nodes (61): MultipleChoiceOption, _best_section_a_context_point(), _build_part(), _build_parts(), _choice_group_name(), _choice_lookup(), _choose_topic(), _compatible_stimulus_kind() (+53 more)

### Community 10 - "build_paper_blueprint"
Cohesion: 0.12
Nodes (51): build_paper_blueprint(), PaperBlueprint, Syllabus, load_builtin_paper_config(), load_syllabus(), Path, Syllabus, test_blueprint_contains_structured_mcq_and_mark_scheme_content() (+43 more)

### Community 11 - "ocrcsgen/render_pdf.py"
Cohesion: 0.12
Nodes (36): aqa_question_cover(), CoverProfile, mark_scheme_cover(), ocr_question_cover(), Flowable, Return a Table subclass whose raw string cells use the controlled font.…, themed_table_class(), _additional_answer_page() (+28 more)

### Community 12 - "paper_fidelity_audit.py"
Cohesion: 0.07
Nodes (65): Image, HelpRow, HelpSection, .body, HelpSheet, .body, String, WelcomeRow (+57 more)

### Community 13 - "reference_corpus.py"
Cohesion: 0.14
Nodes (44): MonkeyPatch, Path, test_document_path_requires_filename(), test_document_path_stays_inside_corpus(), test_download_manifest_records_failure_and_continues(), test_parse_aqa_resources_filters_modified_papers(), test_parse_ocr_resources_uses_a_level_tab_only(), test_parse_ocr_specifications_keeps_a_level_not_as_level() (+36 more)

### Community 14 - "aqaecongen/render_pdf.py"
Cohesion: 0.13
Nodes (42): AnswerLines, _assessment_objectives_table(), _context_data_table(), _context_first_page(), _context_second_page(), _cover(), _cover_profile(), _document() (+34 more)

### Community 15 - "test_coverage_matrix.py"
Cohesion: 0.11
Nodes (37): family(), matrix(), Path, test_catalog_availability_is_owned_only_by_registry(), test_checked_in_matrix_is_deterministic_and_current(), test_existing_generators_are_reported_without_false_verification(), test_matrix_exactly_covers_layout_profiles(), test_no_verified_paper_has_a_failed_gate() (+29 more)

### Community 16 - "CodingKeys"
Cohesion: 0.05
Nodes (41): CodingKey, CodingKeys, backendVersion, capabilities, command, cpuLoad, cpuMBs, detail (+33 more)

### Community 17 - "exam_blueprints.py"
Cohesion: 0.13
Nodes (30): _demand_band(), _hydrate_assessment_metadata(), _objective_allocation(), PaperRule, _prompt_uses_command_word(), BaseModel, QuestionRule, SectionRule (+22 more)

### Community 18 - "Improvement roadmap"
Cohesion: 0.06
Nodes (36): 10. Constrain paper-level assessment design, 11. Make mark schemes examiner-usable, 12. Calibrate actual difficulty, 13. Create an item bank and exposure controls, 14. Introduce a generator plugin API, 15. Split the Swift state owner, 16. Version the bridge protocol, 17. Make output transactional and reproducible (+28 more)

### Community 19 - "Rect"
Cohesion: 0.09
Nodes (46): _clamp_fitz_rect(), conform_pdf_page_boxes(), conform_pdf_to_box_template(), draw_text_slot(), _fitz_rect_close(), LayoutConformanceError, load_layout_master(), _page_from_payload() (+38 more)

### Community 20 - ".appStoreWorkingFolder"
Cohesion: 0.19
Nodes (7): AppDefaults, AppLinks, AppStorageKey, SecretAccount, Bool, String, URL

### Community 21 - "ocregen/generator.py"
Cohesion: 0.14
Nodes (26): generate_package(), Path, build_paper(), _evaluation_scheme(), _extract(), _instructions(), _mcq(), Random (+18 more)

### Community 22 - "benchmark.py"
Cohesion: 0.14
Nodes (30): apple_cpu_core_split(), available_memory_gb(), avg(), clamp(), cpu_brand(), cpu_load_percent(), cpu_probe(), disk_probe() (+22 more)

### Community 23 - "Canvas"
Cohesion: 0.13
Nodes (34): GraphParams, _answer_line_count(), _draw_answer_lines(), _draw_answer_lines_until(), _draw_axis_arrow(), _draw_blank_answer_axes(), _draw_calculate_part_with_working_lines(), _draw_compact_part() (+26 more)

### Community 24 - "aqaaccountgen/generator.py"
Cohesion: 0.13
Nodes (27): field_validator, generate_package(), Path, load_rule(), build_paper(), _extract(), _levels(), _mcq() (+19 more)

### Community 25 - "aqabizgen/generator.py"
Cohesion: 0.09
Nodes (32): generate_package(), Path, load_rule(), FinancialPosition, format_number(), Format an exam answer without meaningless trailing zeroes., The single source of truth for Paper 1 financial-statement figures., build_paper() (+24 more)

### Community 26 - "SwiftUI"
Cohesion: 0.09
Nodes (22): App, Commands, Context, AppCommands, PaperCreator, .body, OutputSettingsTab, PrivacySettingsTab (+14 more)

### Community 27 - "String"
Cohesion: 0.06
Nodes (65): Codable, Decodable, Equatable, Hashable, Identifiable, Int, BackendEvent, benchmarkDone (+57 more)

### Community 28 - "View"
Cohesion: 0.05
Nodes (54): Charts, Color, KeyPath, View, GeneratedFilesTable, PanelEmptyState, .body, String (+46 more)

### Community 29 - "ValueError"
Cohesion: 0.12
Nodes (33): _extract_items(), _form_id(), Any, Path, Write the renderer-independent item record used by release validation., _scheme_text(), _serialise(), validate_assessment_package() (+25 more)

### Community 30 - "Paper creator: deep project analysis"
Cohesion: 0.07
Nodes (28): 10. Completion and file handling, 1. Catalogue and selection, 2. Swift state and command construction, 3. Process bridge and event protocol, 4. Backend validation and dispatch, 5. Two different generation architectures, 6. Blueprint construction, 7. Provider behavior (+20 more)

### Community 31 - "ai_assessment.py"
Cohesion: 0.14
Nodes (38): AssessmentLLMClient, _batches_for_client(), _bounded_text(), _candidate_question(), _canonical_objective_allocation(), _clean_generated_prompt(), _contains_command_word(), _effective_batch_size() (+30 more)

### Community 32 - "graphs.py"
Cohesion: 0.30
Nodes (26): Axes, ad_as_diagram(), _arrow_axes(), _ax(), circular_flow_diagram(), consumer_producer_surplus(), demand_supply_diagram(), _ensure_style() (+18 more)

### Community 33 - "pastpapergen/ollama_client.py"
Cohesion: 0.09
Nodes (37): generate_package(), main(), _normalise_paper_id(), Path, MultipleChoiceOption, PaperBlueprint, PaperConfig, BaseModel (+29 more)

### Community 34 - "generation.py"
Cohesion: 0.20
Nodes (21): progress_emitter(), _atomic_publish(), _cancel_generation(), emit_generated_files(), finalize_generated_documents(), GenerationCancelled, _generator_version(), handle_generate() (+13 more)

### Community 35 - "TerminalProgressReporter"
Cohesion: 0.05
Nodes (29): type, path, _format_elapsed(), PlainProgressReporter, _progress_bar(), ProgressSnapshot, ProgressState, TextIO (+21 more)

### Community 36 - "aqaecongen/generator.py"
Cohesion: 0.16
Nodes (23): generate_package(), main(), Path, load_rule(), _build_mcq_option(), build_paper(), _build_written_option(), _case_depth() (+15 more)

### Community 37 - "BackendClient"
Cohesion: 0.17
Nodes (15): LocalizedError, BackendClient, BackendClientError, backendMissing, .errorDescription, pythonMissing, pythonVenvUnreadable, BackendFile (+7 more)

### Community 38 - "test_mark_scheme_layout.py"
Cohesion: 0.30
Nodes (20): render_mark_scheme(), _blueprint_with_section_a_calculation(), _blueprint_with_section_b_topic(), _pdf_page_count(), _pdf_text(), Path, test_mark_scheme_calculation_rows_include_specific_working(), test_mark_scheme_cover_title_uses_reference_scale_and_position() (+12 more)

### Community 39 - ".initialEstimate"
Cohesion: 0.19
Nodes (11): EstimateFactor, GenerationEstimate, .etaDate, .remainingText, GenerationEstimator, Bool, Date, Double (+3 more)

### Community 40 - "AppViewModel.swift"
Cohesion: 0.16
Nodes (9): AppKit, Combine, Foundation, EstimateTuning, SecretStore, Any, String, Security (+1 more)

### Community 41 - "test_app_backend.py"
Cohesion: 0.17
Nodes (26): absolute_user_path(), Path, Expand a user path without resolving sandbox-approved symlinks., _safe_provider_detail(), CompletedProcess, Path, run_bridge(), run_bridge_raw() (+18 more)

### Community 42 - "pastpapergen/notes.py"
Cohesion: 0.20
Nodes (19): _clean_chunk(), essay_capable_topic_ids(), _flush_note_chunk(), _is_exam_point(), _is_note_noise(), _looks_like_heading(), _note_chunks(), note_context_for_topic() (+11 more)

### Community 43 - "aqa_accounting_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_both_papers_pass_multi_seed_automated_checks(), test_external_difficulty_gates_remain_false(), test_reference_evidence_is_aggregate_only(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 44 - "aqa_business_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 45 - "pastpapergen/render_pdf.py"
Cohesion: 0.10
Nodes (35): BoardLayout, _axis_labels_for_draw_prompt(), _bar_chart_data(), _bar_label(), _draw_bar_chart(), _draw_do_not_write_rail(), _draw_hatched_rail(), _draw_line_graph() (+27 more)

### Community 46 - "ocr_economics_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 47 - "Sidebar"
Cohesion: 0.25
Nodes (8): BoardRow, .body, Sidebar, .body, .expandedSubjects, Bool, String, Set

### Community 48 - "PaperCreatorTests"
Cohesion: 0.08
Nodes (10): ContentView, .body, ContentViewPreview, .previews, .selectedBoard, PaperCreatorTests, PaperCreator, PreviewProvider (+2 more)

### Community 49 - "Q: How does the generation quality pipeline connect?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: How does the generation quality pipeline connect?, Source Nodes

### Community 50 - "render_source_booklet"
Cohesion: 0.17
Nodes (21): extract_pdf_text(), pdf_font_names(), Path, Extract stable reading-order text without a Poppler CLI dependency., Return the font families actually used by visible text spans., test_paper1_rendered_documents_use_correct_identity(), _apply_edexcel_page_boxes(), _extract_source_questions() (+13 more)

### Community 51 - "providers.py"
Cohesion: 0.12
Nodes (24): hosted_client(), HostedLLMClient, _normalise_base_url(), _ollama_json_schema(), _ollama_output_budget(), _ollama_seed(), _ollama_temperature(), _openai_output_text() (+16 more)

### Community 52 - "Q: Where should performance and generated-paper accuracy fixes be made?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Where should performance and generated-paper accuracy fixes be made?, Source Nodes

### Community 53 - "ocrcsgen/generator.py"
Cohesion: 0.12
Nodes (25): GeneratedSection, generate_package(), Path, load_rule(), _analysis_prompt(), build_paper(), _levels(), _programming_prompt() (+17 more)

### Community 54 - "PaperBlueprint"
Cohesion: 0.20
Nodes (21): _count_pages(), _draw_answer_page_header(), _draw_centred_instruction_line(), _draw_continuation_lines(), _draw_formula_appendix(), _draw_paper_3_choice_header(), _draw_paper_3_pages(), _draw_question_footer() (+13 more)

### Community 55 - "emit"
Cohesion: 0.26
Nodes (16): build_parser(), handle_bundle_check(), main(), ArgumentParser, Namespace, Fail fast when a packaged backend is missing a dynamic generator., emit(), emit_progress() (+8 more)

### Community 56 - "generator_capabilities"
Cohesion: 0.31
Nodes (11): _capability(), generator_capabilities(), generator_capability(), generator_subjects(), Any, _relative_path(), test_backend_bundle_script_is_registry_driven(), test_every_advertised_generator_creates_unique_ai_content() (+3 more)

### Community 57 - "properties"
Cohesion: 0.12
Nodes (17): type, type, minimum, type, type, type, properties, backend_version (+9 more)

### Community 58 - "_mark_scheme_rows"
Cohesion: 0.23
Nodes (16): _brief_source_evidence(), _calculation_answer_lines(), _mark_scheme_rows(), _normalise_mark_point(), _one_mark_points(), _part_mark_scheme_lines(), _question_mark_scheme_lines(), _scheme_bullets() (+8 more)

### Community 59 - "Todo Checkpoint Draft"
Cohesion: 0.12
Nodes (15): Active slice, Blocked on, Completed, Completed AQA Accounting vertical slice, Completed AQA Business vertical slice, Completed calibration slice, Completed OCR Computer Science vertical slice, Completed OCR Economics vertical slice (+7 more)

### Community 60 - "Q: How is the macOS backend bundle kept complete?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: How is the macOS backend bundle kept complete?, Source Nodes

### Community 61 - "Evidence Bundle Draft"
Cohesion: 0.14
Nodes (13): AQA Accounting 7127 slice, AQA Business 7132 slice, Coverage slice evidence, Current slice evidence, Difficulty calibration evidence, Evidence Bundle Draft, Evidence limits, Fixed-layout finalisation pass — 27 July 2026 (+5 more)

### Community 62 - "psychometrics.py"
Cohesion: 0.19
Nodes (27): calibrate_responses(), _candidate_item_means(), _cronbach_alpha(), _dif(), _fingerprint(), _item_statistics(), load_responses(), _marker_agreement() (+19 more)

### Community 63 - "question_bank.py"
Cohesion: 0.05
Nodes (137): default_output_dir(), generate_package(), main(), Path, _align_paper1_structure(), build_paper1_blueprint(), _build_paper1_context(), _build_paper1_questions() (+129 more)

### Community 64 - "ocr_computer_science_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_difficulty_remains_external_evidence_gated(), test_multi_seed_structural_demand_passes(), test_reference_evidence_is_aggregate_only(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 65 - "test_ollama_generation.py"
Cohesion: 0.15
Nodes (16): generate_questions_with_ollama(), _merge_source_text(), OllamaClient, PaperBlueprint, Syllabus, BlueprintAwareClient, EmptyClient, _line() (+8 more)

### Community 66 - ".load"
Cohesion: 0.21
Nodes (12): Bundle, CatalogLoader, CatalogLoadError, duplicateBoard, duplicateImplementation, emptyImplementation, .errorDescription, implementationMissingFromCatalog (+4 more)

### Community 67 - "Architecture"
Cohesion: 0.25
Nodes (7): Architecture, Canonical registry, Extension contract, Package transaction, Product boundary, Repository map, Trust boundaries

### Community 68 - "_draw_cover"
Cohesion: 0.16
Nodes (18): economics_exam_schedule(), ExamSchedule, formatted_economics_exam_date(), date, _draw_boxes(), _draw_cover(), _draw_crop_marks(), _draw_fake_barcode() (+10 more)

### Community 69 - "mark_scheme_enrichment.py"
Cohesion: 0.38
Nodes (10): _application_label(), _clean_text(), _compact_technical_guidance(), _deduplicate(), enrich_paper(), _enrich_question(), _level_guidance(), _objective_guidance() (+2 more)

### Community 70 - "Glossy Black Fountain Pen App Icon Master"
Cohesion: 0.18
Nodes (11): Glossy Black Fountain Pen App Icon Master, Paper Creator App Icon AppIcon-128x128@1x, Paper Creator App Icon AppIcon-128x128@2x, Paper Creator App Icon AppIcon-16x16@1x, Paper Creator App Icon AppIcon-16x16@2x, Paper Creator App Icon AppIcon-256x256@1x, Paper Creator App Icon AppIcon-256x256@2x, Paper Creator App Icon AppIcon-32x32@1x (+3 more)

### Community 71 - "Task Intent Draft"
Cohesion: 0.18
Nodes (10): Baseline read set hint, Compatibility boundary, Execution Readiness View, Goal and stop conditions, Impact statement draft, Non-goals, Requested outcome, Retirement boundary (+2 more)

### Community 72 - "enum"
Cohesion: 0.18
Nodes (11): benchmark_done, benchmark_metric, benchmark_sample, done, error, file, hello, models (+3 more)

### Community 73 - "Assessment quality and originality"
Cohesion: 0.25
Nodes (7): Assessment quality and originality, Difficulty claims, Human release review, Mark-scheme quality, Novelty and exposure, Release invariants, Two-pass generation

### Community 74 - "validate_pdf_for_release"
Cohesion: 0.29
Nodes (10): _layout_profiles(), _normalise_font(), Any, Counter, Path, Fail closed on malformed, substituted, annotated, or low-resolution PDFs., validate_pdf_for_release(), _validate_typography_profile() (+2 more)

### Community 75 - "macOS interaction and HIG compliance"
Cohesion: 0.25
Nodes (7): Accessibility verification, Commands and state, File workflow, Geometry and visual language, Information architecture, macOS interaction and HIG compliance, Settings

### Community 76 - "macOS UI audit"
Cohesion: 0.22
Nodes (9): Paper Creator Deterministic Workspace Screenshot, Paper Creator AI Provider Blocked-State Screenshot, Apple HIG alignment, macOS UI audit, Evidence limits, Scope, Step 1 — deterministic paper workspace, Step 2 — AI-assisted paper blocked on Ollama (+1 more)

### Community 77 - "NotificationPresenter"
Cohesion: 0.25
Nodes (6): NotificationPresenter, NSObject, UNNotification, UNNotificationPresentationOptions, UNUserNotificationCenter, UNUserNotificationCenterDelegate

### Community 78 - "Q: how can we make even more improvements to get the highest similarity in terms of structure and layout and quality of questions etc. and maybe all of the files in the project can be better organised. and the UI can be made to be much better and more geometrically apple-like by strictly following every single rule they outline in their HIG"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: how can we make even more improvements to get the highest similarity in terms of structure and layout and quality of questions etc. and maybe all of the files in the project can be better organised. and the UI can be made to be much better and more geometrically apple-like by strictly following every single rule they outline in their HIG, Source Nodes

### Community 79 - "Paper creator"
Cohesion: 0.25
Nodes (8): Architecture and quality analysis, Build Checks, CLI, Development Reference Corpus, Paper creator, Privacy, Run, Structure

### Community 80 - "cspapergen/exam_dates.py"
Cohesion: 0.57
Nodes (6): formatted_paper1_exam_date(), formatted_paper2_exam_date(), paper1_exam_date(), paper2_exam_date(), date, test_paper2_exam_date_uses_june_exam_season()

### Community 81 - "pull_request_template.md"
Cohesion: 0.50
Nodes (3): Risk, Verification, What changed

### Community 82 - "_draw_source_content_page"
Cohesion: 0.67
Nodes (4): _draw_source_content_page(), Syllabus, _source_reading_prompt(), _source_title()

### Community 83 - "Implementation and fidelity report"
Cohesion: 0.29
Nodes (7): Implementation and fidelity report, Full-matrix validation, Highest-value next engineering work, Implemented changes, Manual PDF review, Outcome, What code cannot honestly prove

### Community 84 - "backend-protocol.schema.json"
Cohesion: 0.29
Nodes (6): additionalProperties, allOf, $id, $schema, title, type

### Community 86 - "required"
Cohesion: 0.33
Nodes (6): event_id, job_id, protocol, timestamp, type, required

### Community 87 - "generator_working_directory"
Cohesion: 0.40
Nodes (4): generator_working_directory(), MonkeyPatch, fixture, FixtureRequest

### Community 88 - "xcbuild.sh"
Cohesion: 0.67
Nodes (3): HOME, xcbuild.sh script, usage()

### Community 89 - "type"
Cohesion: 0.50
Nodes (4): null, string, stage, type

### Community 90 - "capabilities"
Cohesion: 0.50
Nodes (4): items, type, type, capabilities

### Community 91 - "progress"
Cohesion: 0.50
Nodes (4): maximum, minimum, type, progress

### Community 97 - "timestamp"
Cohesion: 0.67
Nodes (3): timestamp, format, type

### Community 101 - "build_backend.sh"
Cohesion: 0.40
Nodes (4): MPLCONFIGDIR, PYINSTALLER_CONFIG_DIR, build_backend.sh script, XDG_CACHE_HOME

## Knowledge Gaps
- **370 isolated node(s):** `BoardLayout`, `examforge-aqa-accounting`, `$schema`, `$id`, `title` (+365 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **50 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Work-memory lessons

**Preferred sources** — corroborated by past sessions; start here.
- `AppViewModel` (2× useful, score=1.93771633)
- `generation.py` (2× useful, score=1.935301773)
- `exam_blueprints.py` (2× useful, score=1.87301818)
- `layout_master.py` (2× useful, score=1.87301818)
- `paper_fidelity_audit.py` (2× useful, score=1.87301818)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Rect` connect `Rect` to `Paragraph`, `GeneratedQuestion`, `GeneratedPaper`, `paper_fidelity_audit.py`, `aqaecongen/render_pdf.py`?**
  _High betweenness centrality (0.219) - this node is a cross-community bridge._
- **Why does `_block_mask()` connect `paper_fidelity_audit.py` to `Rect`?**
  _High betweenness centrality (0.201) - this node is a cross-community bridge._
- **Why does `.body` connect `AppViewModel` to `View`, `paper_fidelity_audit.py`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Are the 120 inferred relationships involving `Paragraph` (e.g. with `aqa_front_matter_pages()` and `_accounting_marking_guidance_pages()`) actually correct?**
  _`Paragraph` has 120 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `GeneratedQuestion` (e.g. with `AssessmentLLMClient` and `GenerationPolicy`) actually correct?**
  _`GeneratedQuestion` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `BoardLayout`, `examforge-aqa-accounting`, `$schema` to the rest of the system?**
  _370 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `cspapergen/render_pdf.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1011743450767841 - nodes in this community are weakly interconnected._