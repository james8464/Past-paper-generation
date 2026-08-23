# Graph Report - Past Paper Creation  (2026-08-23)

## Corpus Check
- 228 files · ~439,781 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2927 nodes · 8649 edges · 167 communities (113 shown, 54 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 493 edges (avg confidence: 0.69)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fedc7433`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cspapergen/render_pdf.py
- QuestionPaperCover
- AppViewModel
- View
- Paragraph
- ocregen/render_pdf.py
- GeneratedPaper
- test_render_pdf.py
- aqabizgen/generator.py
- pastpapergen/generator.py
- build_paper_blueprint
- ocrcsgen/render_pdf.py
- paper_fidelity_audit.py
- reference_corpus.py
- aqaecongen/render_pdf.py
- test_coverage_matrix.py
- CodingKeys
- AssessmentCheckpointStore
- model_recommendations.py
- Rect
- cspapergen/cli.py
- ocregen/generator.py
- benchmark.py
- ai_assessment.py
- test_aqa_accounting.py
- BackendEvent
- SwiftUI
- GenerationEstimator
- QualityState
- String
- Paper creator: deep project analysis
- GeneratedQuestion
- graphs.py
- pastpapergen/ollama_client.py
- generation.py
- OllamaModelRecommendation
- aqaecongen/generator.py
- BackendClient
- test_mark_scheme_layout.py
- GeneratedFile
- aqa_accounting_calibration.py
- test_app_backend.py
- pastpapergen/notes.py
- cspapergen/generator.py
- aqa_business_calibration.py
- CodingKeys
- Foundation
- BenchmarkChart
- AppDefaults
- Q: How does the generation quality pipeline connect?
- question_bank.py
- providers.py
- Q: Where should performance and generated-paper accuracy fixes be made?
- Contract-First Paper Generation and Release Qualification
- ocrcsgen/generator.py
- emit
- generator_capabilities
- properties
- _mark_scheme_rows
- AssessmentContract
- Q: How is the macOS backend bundle kept complete?
- File Structure
- assessment_quality.py
- test_ollama_generation.py
- ocr_computer_science_calibration.py
- ReviewResult
- HelpTopic
- Architecture
- _draw_cover
- mark_scheme_enrichment.py
- Glossy Black Fountain Pen App Icon Master
- OllamaModelGuideError
- enum
- Assessment quality and originality
- validate_pdf_for_release
- macOS interaction and HIG compliance
- backend_version
- NonCurrentAssetCase
- Q: how can we make even more improvements to get the highest similarity in terms of structure and layout and quality of questions etc. and maybe all of the files in the project can be better organised. and the UI can be made to be much better and more geometrically apple-like by strictly following every single rule they outline in their HIG
- Paper creator
- cspapergen/exam_dates.py
- pull_request_template.md
- .board
- _draw_section_a_question
- backend-protocol.schema.json
- pastpapergen/render_pdf.py
- exam_blueprints.py
- generator_working_directory
- xcbuild.sh
- psychometrics.py
- capabilities
- register_fonts
- ocr_economics_calibration.py
- diagnose.sh
- move_to_trash.sh
- run_app_ios_sim.sh
- run_app_macos.sh
- required
- Core/__init__.py
- render_source_booklet
- bootstrap_backend.sh
- build_backend.sh
- clean.sh
- resolve_agent_name.sh
- resolve_sim_destination.sh
- aqaaccountgen/__init__.py
- Canvas
- aqabizgen/__init__.py
- cspapergen/__init__.py
- ocrcsgen/__init__.py
- aqaecongen/__init__.py
- pastpapergen/__init__.py
- ocregen/__init__.py
- tools/__init__.py
- graphify
- NotificationPresenter
- type
- progress
- timestamp
- PaperCreator Xcode Project Configuration
- aqa-economics-practice-generator
- cspapergen
- examforge-aqa-accounting
- examforge-aqa-business
- examforge-ocr-computer-science
- ocr-economics-practice-generator
- pastpapergen
- PyInstaller Build Dependency
- paper1_assets.py
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
- .load
- IncomeStatementCase
- PartnershipCase
- cspapergen/notes.py
- aqaaccountgen/syllabus.py
- write_assessment_package
- aqaaccountgen/generator.py
- SalesLedgerCase
- pastpapergen/cli.py
- test_source_booklet.py
- CostingCase
- _build_part
- source_cases.py
- test_paper_configs.py
- _apply_edexcel_page_boxes

## God Nodes (most connected - your core abstractions)
1. `GeneratedQuestion` - 174 edges
2. `build_paper_blueprint()` - 125 edges
3. `AppViewModel` - 116 edges
4. `load_builtin_paper_config()` - 111 edges
5. `load_syllabus()` - 111 edges
6. `GeneratedOption` - 94 edges
7. `GeneratedPaper` - 85 edges
8. `build_question()` - 53 edges
9. `QuestionStyle` - 51 edges
10. `AssessmentCheckpointStore` - 50 edges

## Surprising Connections (you probably didn't know these)
- `FirstPassClient` --uses--> `GenerationPolicy`  [INFERRED]
  tests/test_assessment_checkpoints.py → Backend/Core/ai_assessment.py
- `NoCallsClient` --uses--> `GenerationPolicy`  [INFERRED]
  tests/test_assessment_checkpoints.py → Backend/Core/ai_assessment.py
- `JSONGenerationClient` --uses--> `AssessmentCheckpointStore`  [INFERRED]
  Resources/computer-science/aqa/generator/cspapergen/ollama_client.py → Backend/Core/assessment_checkpoints.py
- `OllamaClient` --uses--> `AssessmentCheckpointStore`  [INFERRED]
  Resources/computer-science/aqa/generator/cspapergen/ollama_client.py → Backend/Core/assessment_checkpoints.py
- `OllamaClient` --uses--> `AssessmentCheckpointStore`  [INFERRED]
  Resources/economics/edexcel-a/generator/pastpapergen/ollama_client.py → Backend/Core/assessment_checkpoints.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Edexcel A Economics Knowledge Corpus** — resources_economics_edexcel_a_generator_data_notes_text_1_1_nature_of_economics_nature_of_economics, resources_economics_edexcel_a_generator_data_notes_text_1_2_how_markets_work_how_markets_work, resources_economics_edexcel_a_generator_data_notes_text_1_3_market_failure_market_failure, resources_economics_edexcel_a_generator_data_notes_text_1_4_government_intervention_government_intervention, resources_economics_edexcel_a_generator_data_notes_text_2_1_measures_of_economic_performance_measures_of_economic_performance, resources_economics_edexcel_a_generator_data_notes_text_2_2_aggregate_demand_aggregate_demand, resources_economics_edexcel_a_generator_data_notes_text_2_3_aggregate_supply_aggregate_supply, resources_economics_edexcel_a_generator_data_notes_text_2_4_national_income_national_income, resources_economics_edexcel_a_generator_data_notes_text_2_5_economic_growth_economic_growth, resources_economics_edexcel_a_generator_data_notes_text_2_6_macroeconomic_objectives_and_policies_macroeconomic_objectives_and_policies, resources_economics_edexcel_a_generator_data_notes_text_3_1_business_growth_business_growth, resources_economics_edexcel_a_generator_data_notes_text_3_2_business_objectives_business_objectives, resources_economics_edexcel_a_generator_data_notes_text_3_3_revenues_costs_and_profits_revenues_costs_and_profits, resources_economics_edexcel_a_generator_data_notes_text_3_4_market_structures_market_structures, resources_economics_edexcel_a_generator_data_notes_text_3_5_labour_markets_labour_markets, resources_economics_edexcel_a_generator_data_notes_text_4_1_international_economics_international_economics, resources_economics_edexcel_a_generator_data_notes_text_4_2_poverty_and_inequality_poverty_and_inequality, resources_economics_edexcel_a_generator_data_notes_text_4_3_emerging_and_developing_economies_emerging_and_developing_economies, resources_economics_edexcel_a_generator_data_notes_text_4_4_the_financial_sector_the_financial_sector, resources_economics_edexcel_a_generator_data_notes_text_4_5_role_of_the_state_in_the_macroeconomy_role_of_the_state_in_the_macroeconomy [EXTRACTED 1.00]

## Communities (167 total, 54 thin omitted)

### Community 0 - "cspapergen/render_pdf.py"
Cohesion: 0.08
Nodes (92): formatted_generation_series(), generation_date(), date, Return the month/year form used on mark-scheme covers., Question, _validate_ai_question(), _answer_line_count(), _answer_lines() (+84 more)

### Community 1 - "QuestionPaperCover"
Cohesion: 0.21
Nodes (4): MarkSchemeCover, QuestionPaperCover, Fixed-grid, board-shaped front page without copying protected artwork., _wrap()

### Community 2 - "AppViewModel"
Cohesion: 0.04
Nodes (34): AnyCancellable, Binding, DateFormatter, Error, Int32, ProgressEntry, .body, .body (+26 more)

### Community 3 - "View"
Cohesion: 0.17
Nodes (22): View, HelpCallout, HelpScreenshot, HelpSection, .body, HelpSheet, .body, HelpSteps (+14 more)

### Community 4 - "Paragraph"
Cohesion: 0.13
Nodes (67): GeneratedOption, Paragraph, _accounting_marking_guidance_pages(), _accounting_system_case(), _accounting_table(), _additional_answer_page(), AnswerLines, _appropriation_answer_table() (+59 more)

### Community 5 - "ocregen/render_pdf.py"
Cohesion: 0.09
Nodes (70): _add_economics_diagram(), _add_firm_objectives_diagram(), _add_ppf_diagram(), _annotation_conventions_page(), _answer_mark(), AnswerLines, _assessment_allocation(), _assessment_grid_groups() (+62 more)

### Community 6 - "GeneratedPaper"
Cohesion: 0.11
Nodes (56): GeneratedPaper, aqa_front_matter_pages(), Flowable, _additional_answer_page(), AnswerLines, _ao_summary(), _assessment_objectives_page(), _banner() (+48 more)

### Community 7 - "test_render_pdf.py"
Cohesion: 0.14
Nodes (41): render_question_paper(), _blank_axis_lines(), _blueprint_with_section_a_question(), _dark_pixels(), _first_page_containing(), _long_horizontal_line_count(), _normalised(), _pdf_page_count() (+33 more)

### Community 8 - "aqabizgen/generator.py"
Cohesion: 0.09
Nodes (35): identity_for_blueprint(), generate_package(), Path, load_rule(), FinancialPosition, format_number(), Format an exam answer without meaningless trailing zeroes., The single source of truth for Paper 1 financial-statement figures. (+27 more)

### Community 9 - "pastpapergen/generator.py"
Cohesion: 0.11
Nodes (34): _best_section_a_context_point(), _choice_group_name(), _choice_lookup(), _data_response_extract(), _essay_question_prompt(), _exam_context(), _exam_focus(), _first_sentence() (+26 more)

### Community 10 - "build_paper_blueprint"
Cohesion: 0.15
Nodes (45): build_paper_blueprint(), PaperBlueprint, Syllabus, load_builtin_paper_config(), load_syllabus(), Path, Syllabus, test_blueprint_contains_structured_mcq_and_mark_scheme_content() (+37 more)

### Community 11 - "ocrcsgen/render_pdf.py"
Cohesion: 0.13
Nodes (31): Return a Table subclass whose raw string cells use the controlled font.…, themed_table_class(), _additional_answer_page(), _additional_pages(), AnswerLines, _banner(), _box(), _chrome() (+23 more)

### Community 12 - "paper_fidelity_audit.py"
Cohesion: 0.08
Nodes (64): Image, .body, .body, .body, .body, Pixmap, Path, test_compact_profile_omits_raster_geometry() (+56 more)

### Community 13 - "reference_corpus.py"
Cohesion: 0.14
Nodes (44): MonkeyPatch, Path, test_document_path_requires_filename(), test_document_path_stays_inside_corpus(), test_download_manifest_records_failure_and_continues(), test_parse_aqa_resources_filters_modified_papers(), test_parse_ocr_resources_uses_a_level_tab_only(), test_parse_ocr_specifications_keeps_a_level_not_as_level() (+36 more)

### Community 14 - "aqaecongen/render_pdf.py"
Cohesion: 0.10
Nodes (51): aqa_question_cover(), CoverProfile, mark_scheme_cover(), ocr_question_cover(), Flowable, generate_package(), main(), Path (+43 more)

### Community 15 - "test_coverage_matrix.py"
Cohesion: 0.11
Nodes (37): family(), matrix(), Path, test_catalog_availability_is_owned_only_by_registry(), test_checked_in_matrix_is_deterministic_and_current(), test_existing_generators_are_reported_without_false_verification(), test_matrix_exactly_covers_layout_profiles(), test_no_verified_paper_has_a_failed_gate() (+29 more)

### Community 16 - "CodingKeys"
Cohesion: 0.05
Nodes (40): CodingKeys, backendVersion, capabilities, command, cpuLoad, cpuMBs, detail, diskFreeGB (+32 more)

### Community 17 - "AssessmentCheckpointStore"
Cohesion: 0.16
Nodes (20): AssessmentCheckpointStore, CheckpointCorrupt, CheckpointIdentity, CheckpointMismatch, Any, BaseModel, Path, ValueError (+12 more)

### Community 18 - "model_recommendations.py"
Cohesion: 0.16
Nodes (24): default_ollama_model(), model_recommendations(), OllamaModelRecommendations, OllamaModelTier, parse_model_recommendations(), Any, _required_text(), jobs() (+16 more)

### Community 19 - "Rect"
Cohesion: 0.09
Nodes (47): _clamp_fitz_rect(), conform_pdf_page_boxes(), conform_pdf_to_box_template(), draw_text_slot(), _fitz_rect_close(), LayoutConformanceError, load_layout_master(), _page_from_payload() (+39 more)

### Community 20 - "cspapergen/cli.py"
Cohesion: 0.09
Nodes (45): default_output_dir(), generate_package(), main(), Path, build_paper1_blueprint(), build_paper2_blueprint(), PaperBlueprint, Syllabus (+37 more)

### Community 21 - "ocregen/generator.py"
Cohesion: 0.12
Nodes (31): generate_package(), Path, load_rule(), build_paper(), _evaluation_scheme(), _extract(), _extract_number(), _instructions() (+23 more)

### Community 22 - "benchmark.py"
Cohesion: 0.14
Nodes (30): apple_cpu_core_split(), available_memory_gb(), avg(), clamp(), cpu_brand(), cpu_load_percent(), cpu_probe(), disk_probe() (+22 more)

### Community 23 - "ai_assessment.py"
Cohesion: 0.14
Nodes (31): AssessmentLLMClient, _batches_for_client(), _bounded_text(), _contains_command_word(), _effective_batch_size(), _generate_batch(), _generate_item_transaction(), generate_unique_paper() (+23 more)

### Community 24 - "test_aqa_accounting.py"
Cohesion: 0.37
Nodes (12): generate_package(), Path, page_count(), Path, test_both_packages_render_36_page_question_papers(), test_invalid_paper_is_rejected(), test_non_current_asset_question_and_mark_scheme_use_the_same_figures(), test_paper_one_mark_scheme_matches_reference_question_sequence() (+4 more)

### Community 25 - "BackendEvent"
Cohesion: 0.08
Nodes (13): BackendEvent, benchmarkDone, benchmarkMetric, benchmarkSample, done, error, file, hello (+5 more)

### Community 26 - "SwiftUI"
Cohesion: 0.09
Nodes (22): App, Commands, Context, AppCommands, PaperCreator, .body, AISettingsTab, PrivacySettingsTab (+14 more)

### Community 27 - "GenerationEstimator"
Cohesion: 0.27
Nodes (6): GenerationEstimator, Date, Double, String, model, ProcessInfo

### Community 28 - "QualityState"
Cohesion: 0.11
Nodes (23): Color, GenerationProgress, .body, GeneratorWorkspace, .body, .generateHelp, .workspace, PaperConfiguration (+15 more)

### Community 29 - "String"
Cohesion: 0.06
Nodes (70): Codable, Decodable, Equatable, Hashable, Identifiable, AIProvider, anthropic, apple (+62 more)

### Community 30 - "Paper creator: deep project analysis"
Cohesion: 0.05
Nodes (42): Implementation and fidelity report, Full-matrix validation, Highest-value next engineering work, Implemented changes, Manual PDF review, Outcome, What code cannot honestly prove, 10. Completion and file handling (+34 more)

### Community 31 - "GeneratedQuestion"
Cohesion: 0.14
Nodes (39): _candidate_question(), _canonical_objective_allocation(), _clean_generated_prompt(), GenerationPolicy, _normalise_level_allocations(), _normalise_multiple_choice_answer(), _parse_batch(), Remove model-added presentation labels that the renderer already owns. (+31 more)

### Community 32 - "graphs.py"
Cohesion: 0.30
Nodes (26): Axes, ad_as_diagram(), _arrow_axes(), _ax(), circular_flow_diagram(), consumer_producer_surplus(), demand_supply_diagram(), _ensure_style() (+18 more)

### Community 33 - "pastpapergen/ollama_client.py"
Cohesion: 0.15
Nodes (24): MultipleChoiceOption, PaperBlueprint, BaseModel, QuestionBlueprint, QuestionPart, SectionConfig, Syllabus, SyllabusTopic (+16 more)

### Community 34 - "generation.py"
Cohesion: 0.19
Nodes (23): progress_emitter(), _atomic_publish(), _cancel_generation(), checkpoint_path_for_job(), emit_generated_files(), finalize_generated_documents(), GenerationCancelled, _generator_version() (+15 more)

### Community 35 - "OllamaModelRecommendation"
Cohesion: 0.16
Nodes (13): tiers, OllamaModelGuide, .currentRecommendation, OllamaModelGuideDocument, OllamaModelRecommendation, .downloadDescription, Bool, Bundle (+5 more)

### Community 36 - "aqaecongen/generator.py"
Cohesion: 0.15
Nodes (23): _build_mcq_option(), build_paper(), _build_written_option(), _case_depth(), _paper_three_indicative_content(), policy_name(), Random, Syllabus (+15 more)

### Community 37 - "BackendClient"
Cohesion: 0.18
Nodes (15): LocalizedError, BackendClient, BackendClientError, backendMissing, .errorDescription, pythonMissing, pythonVenvUnreadable, BackendFile (+7 more)

### Community 38 - "test_mark_scheme_layout.py"
Cohesion: 0.16
Nodes (32): formatted_generation_date(), extract_pdf_text(), pdf_font_names(), Path, Extract stable reading-order text without a Poppler CLI dependency., Return the font families actually used by visible text spans., test_paper1_rendered_documents_use_correct_identity(), _cleanup_graph_cache() (+24 more)

### Community 39 - "GeneratedFile"
Cohesion: 0.13
Nodes (14): .body, GeneratedFilesTable, .body, PanelEmptyState, .body, String, GeneratedFile, .exists (+6 more)

### Community 40 - "aqa_accounting_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_both_papers_pass_multi_seed_automated_checks(), test_external_difficulty_gates_remain_false(), test_reference_evidence_is_aggregate_only(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 41 - "test_app_backend.py"
Cohesion: 0.15
Nodes (29): absolute_user_path(), Path, Expand a user path without resolving sandbox-approved symlinks., _safe_provider_detail(), CaptureFixture, CompletedProcess, Path, run_bridge() (+21 more)

### Community 42 - "pastpapergen/notes.py"
Cohesion: 0.22
Nodes (18): _clean_chunk(), _flush_note_chunk(), _is_exam_point(), _is_note_noise(), _looks_like_heading(), _note_chunks(), note_context_for_topic(), note_file_for_topic() (+10 more)

### Community 43 - "cspapergen/generator.py"
Cohesion: 0.11
Nodes (29): _align_paper1_structure(), _build_paper1_context(), _build_paper1_questions(), _paper1_part(), _paper1_question(), _paper2_marking_checks(), QuestionPart, Random (+21 more)

### Community 44 - "aqa_business_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 45 - "CodingKeys"
Cohesion: 0.12
Nodes (17): CodingKey, CodingKeys, appContextWindow, contextWindow, defaultModel, detail, downloadSizeGB, id (+9 more)

### Community 46 - "Foundation"
Cohesion: 0.13
Nodes (11): AppKit, Combine, Foundation, EstimateTuning, SecretStore, Any, String, PaperCreator (+3 more)

### Community 47 - "BenchmarkChart"
Cohesion: 0.11
Nodes (25): Charts, KeyPath, BenchmarkChart, BenchmarkLiveCharts, .body, .cpuChart, .cpuThroughputChart, .diskWriteChart (+17 more)

### Community 48 - "AppDefaults"
Cohesion: 0.16
Nodes (8): AppDefaults, AppLinks, AppStorageKey, SecretAccount, Bool, String, URL, .outputFolderDisplayPath

### Community 49 - "Q: How does the generation quality pipeline connect?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: How does the generation quality pipeline connect?, Source Nodes

### Community 50 - "question_bank.py"
Cohesion: 0.23
Nodes (53): Stimulus, _assembly_program_question(), _assembly_trace_question(), _big_data_question(), _big_data_short_question(), _binary_short_question(), _bitmap_question(), _boolean_question() (+45 more)

### Community 51 - "providers.py"
Cohesion: 0.11
Nodes (28): hosted_client(), HostedLLMClient, _normalise_base_url(), _ollama_json_schema(), _ollama_output_budget(), _ollama_seed(), _ollama_temperature(), _openai_output_text() (+20 more)

### Community 52 - "Q: Where should performance and generated-paper accuracy fixes be made?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Where should performance and generated-paper accuracy fixes be made?, Source Nodes

### Community 53 - "Contract-First Paper Generation and Release Qualification"
Cohesion: 0.06
Nodes (31): 1. Assessment Contract, 2. Deterministic Assessment Data, 3. Item-Level AI Workflow, 4. Evidence Binding and Factual Quality, 5. Mark-Scheme Quality, 6. Board Layout Adapters, 7. Bounded Rendering, 8. Progress, Cancellation, and Resume (+23 more)

### Community 54 - "ocrcsgen/generator.py"
Cohesion: 0.14
Nodes (24): generate_package(), Path, load_rule(), _analysis_prompt(), build_paper(), _levels(), _programming_prompt(), Random (+16 more)

### Community 55 - "emit"
Cohesion: 0.26
Nodes (16): build_parser(), handle_bundle_check(), main(), ArgumentParser, Namespace, Fail fast when a packaged backend is missing a dynamic generator., emit(), emit_progress() (+8 more)

### Community 56 - "generator_capabilities"
Cohesion: 0.32
Nodes (10): _capability(), generator_capabilities(), generator_subjects(), Any, _relative_path(), test_backend_bundle_script_is_registry_driven(), test_every_advertised_generator_creates_unique_ai_content(), test_every_entry_point_and_declared_resource_is_loadable() (+2 more)

### Community 57 - "properties"
Cohesion: 0.12
Nodes (17): type, minimum, type, type, type, type, properties, code (+9 more)

### Community 58 - "_mark_scheme_rows"
Cohesion: 0.16
Nodes (25): _brief_source_evidence(), _calculation_answer_lines(), _mark_scheme_rows(), _normalise_mark_point(), _one_mark_points(), _paper_one_fifteen_mark_scheme_lines(), _paper_one_five_mark_diagram_lines(), _paper_one_section_a_mark_scheme_lines() (+17 more)

### Community 59 - "AssessmentContract"
Cohesion: 0.11
Nodes (31): AssessmentContract, contract_for_question(), EvidenceRecord, GeneratedNumericField, GraphContract, _numeric_contracts(), NumericRole, NumericValueContract (+23 more)

### Community 60 - "Q: How is the macOS backend bundle kept complete?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: How is the macOS backend bundle kept complete?, Source Nodes

### Community 61 - "File Structure"
Cohesion: 0.17
Nodes (11): Assessment Reliability Core Implementation Plan, File Structure, Global Constraints, Subsequent Phase Plans, Task 1: Typed Item Contracts, Task 2: Role-Aware Numeric and Evidence Validation, Task 3: Item-Scoped Draft, Review, and Repair, Task 4: Atomic Checkpoints and Resume (+3 more)

### Community 62 - "assessment_quality.py"
Cohesion: 0.15
Nodes (21): assert_distinct_items(), content_similarity(), _ignored_candidate_quantities(), _is_subsequence(), _items(), _load_package(), normalise_item_text(), _normalise_quantity() (+13 more)

### Community 63 - "test_ollama_generation.py"
Cohesion: 0.15
Nodes (17): generate_questions_with_ollama(), _merge_source_text(), OllamaClient, PaperBlueprint, Syllabus, BlueprintAwareClient, EmptyClient, _line() (+9 more)

### Community 64 - "ocr_computer_science_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_difficulty_remains_external_evidence_gated(), test_multi_seed_structural_demand_passes(), test_reference_evidence_is_aggregate_only(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 65 - "ReviewResult"
Cohesion: 0.24
Nodes (12): independent_review(), JSONClient, Any, BaseModel, Protocol, require_independent_review(), ReviewResult, _serialise() (+4 more)

### Community 66 - "HelpTopic"
Cohesion: 0.17
Nodes (12): CaseIterable, HelpTopic, checkingQuality, choosingAModel, creatingAPaper, gettingStarted, .id, privacy (+4 more)

### Community 67 - "Architecture"
Cohesion: 0.25
Nodes (7): Architecture, Canonical registry, Extension contract, Package transaction, Product boundary, Repository map, Trust boundaries

### Community 68 - "_draw_cover"
Cohesion: 0.20
Nodes (15): economics_exam_schedule(), ExamSchedule, formatted_economics_exam_date(), date, _draw_boxes(), _draw_cover(), _draw_fake_barcode(), _draw_front_section() (+7 more)

### Community 69 - "mark_scheme_enrichment.py"
Cohesion: 0.24
Nodes (17): _application_label(), _clean_text(), _compact_technical_guidance(), _deduplicate(), enrich_paper(), _enrich_question(), _level_guidance(), _objective_guidance() (+9 more)

### Community 70 - "Glossy Black Fountain Pen App Icon Master"
Cohesion: 0.18
Nodes (11): Glossy Black Fountain Pen App Icon Master, Paper Creator App Icon AppIcon-128x128@1x, Paper Creator App Icon AppIcon-128x128@2x, Paper Creator App Icon AppIcon-16x16@1x, Paper Creator App Icon AppIcon-16x16@2x, Paper Creator App Icon AppIcon-256x256@1x, Paper Creator App Icon AppIcon-256x256@2x, Paper Creator App Icon AppIcon-32x32@1x (+3 more)

### Community 71 - "OllamaModelGuideError"
Cohesion: 0.33
Nodes (6): OllamaModelGuideError, .errorDescription, invalidDefault, missingResource, unsupportedSchema, String

### Community 72 - "enum"
Cohesion: 0.18
Nodes (11): benchmark_done, benchmark_metric, benchmark_sample, done, error, file, hello, models (+3 more)

### Community 73 - "Assessment quality and originality"
Cohesion: 0.25
Nodes (7): Assessment quality and originality, Difficulty claims, Human release review, Item transactions and two-pass generation, Mark-scheme quality, Novelty and exposure, Release invariants

### Community 74 - "validate_pdf_for_release"
Cohesion: 0.28
Nodes (11): _layout_profiles(), _normalise_font(), Any, Counter, Path, Fail closed on malformed, substituted, annotated, or low-resolution PDFs., validate_pdf_for_release(), _validate_typography_profile() (+3 more)

### Community 75 - "macOS interaction and HIG compliance"
Cohesion: 0.22
Nodes (8): Accessibility verification, Commands and state, File workflow, Geometry and visual language, Information architecture, macOS interaction and HIG compliance, Onboarding and help, Settings

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

### Community 82 - ".board"
Cohesion: 0.13
Nodes (14): ContentView, .body, ContentViewPreview, .previews, BoardRow, .body, Sidebar, .body (+6 more)

### Community 83 - "_draw_section_a_question"
Cohesion: 0.18
Nodes (17): _draw_answer_lines(), _draw_calculate_part_with_working_lines(), _draw_compact_part(), _draw_inline_context(), _draw_mcq_part(), _draw_part_prompt(), _draw_section_a_question(), _draw_section_a_total() (+9 more)

### Community 84 - "backend-protocol.schema.json"
Cohesion: 0.29
Nodes (6): additionalProperties, allOf, $id, $schema, title, type

### Community 85 - "pastpapergen/render_pdf.py"
Cohesion: 0.08
Nodes (42): BoardLayout, GraphParams, _answer_line_count(), _axis_labels_for_draw_prompt(), _bar_chart_data(), _bar_label(), _draw_axis_arrow(), _draw_bar_chart() (+34 more)

### Community 86 - "exam_blueprints.py"
Cohesion: 0.15
Nodes (28): _demand_band(), _hydrate_assessment_metadata(), _objective_allocation(), PaperRule, _prompt_uses_command_word(), QuestionRule, SectionRule, _structured_scheme() (+20 more)

### Community 87 - "generator_working_directory"
Cohesion: 0.40
Nodes (4): generator_working_directory(), MonkeyPatch, fixture, FixtureRequest

### Community 88 - "xcbuild.sh"
Cohesion: 0.67
Nodes (3): HOME, xcbuild.sh script, usage()

### Community 89 - "psychometrics.py"
Cohesion: 0.19
Nodes (27): calibrate_responses(), _candidate_item_means(), _cronbach_alpha(), _dif(), _fingerprint(), _item_statistics(), load_responses(), _marker_agreement() (+19 more)

### Community 90 - "capabilities"
Cohesion: 0.50
Nodes (4): items, type, type, capabilities

### Community 91 - "register_fonts"
Cohesion: 0.52
Nodes (5): register_font(), register_fonts(), _standard_fallback(), test_fallback_family_supports_bold_paragraph_markup(), test_missing_font_uses_registered_standard_font_alias()

### Community 92 - "ocr_economics_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 97 - "required"
Cohesion: 0.33
Nodes (6): event_id, job_id, protocol, timestamp, type, required

### Community 99 - "render_source_booklet"
Cohesion: 0.38
Nodes (7): _draw_source_content_page(), _extract_source_questions(), Syllabus, render_source_booklet(), _source_reading_prompt(), _source_sections(), _source_title()

### Community 101 - "build_backend.sh"
Cohesion: 0.29
Nodes (5): MPLCONFIGDIR, PYINSTALLER_CONFIG_DIR, PYTHONPATH, build_backend.sh script, XDG_CACHE_HOME

### Community 106 - "Canvas"
Cohesion: 0.16
Nodes (37): _count_pages(), _draw_answer_lines_until(), _draw_answer_page_header(), _draw_centred_instruction_line(), _draw_continuation_lines(), _draw_crop_marks(), _draw_do_not_write_rail(), _draw_formula_appendix() (+29 more)

### Community 115 - "NotificationPresenter"
Cohesion: 0.25
Nodes (6): NotificationPresenter, NSObject, UNNotification, UNNotificationPresentationOptions, UNUserNotificationCenter, UNUserNotificationCenterDelegate

### Community 116 - "type"
Cohesion: 0.50
Nodes (4): null, string, stage, type

### Community 117 - "progress"
Cohesion: 0.50
Nodes (4): maximum, minimum, type, progress

### Community 120 - "timestamp"
Cohesion: 0.67
Nodes (3): timestamp, format, type

### Community 130 - "paper1_assets.py"
Cohesion: 0.50
Nodes (11): _page_footer(), _paragraph(), _practice_header(), Canvas, PaperBlueprint, Path, render_electronic_answer_document(), render_preliminary_material() (+3 more)

### Community 152 - ".load"
Cohesion: 0.21
Nodes (12): CatalogLoader, CatalogLoadError, duplicateBoard, duplicateImplementation, emptyImplementation, .errorDescription, implementationMissingFromCatalog, missingResource (+4 more)

### Community 155 - "cspapergen/notes.py"
Cohesion: 0.38
Nodes (9): cache_notes(), discover_note_pdfs(), _extract_text(), note_context_for_topic(), NotesManifest, Path, _topic_prefixes(), test_cache_notes_extracts_text_into_project_cache() (+1 more)

### Community 156 - "aqaaccountgen/syllabus.py"
Cohesion: 0.28
Nodes (6): field_validator, load_syllabus(), BaseModel, Path, Syllabus, Topic

### Community 157 - "write_assessment_package"
Cohesion: 0.42
Nodes (10): _extract_items(), _form_id(), Any, Path, Write the renderer-independent item record used by release validation., _scheme_text(), _serialise(), validate_assessment_package() (+2 more)

### Community 158 - "aqaaccountgen/generator.py"
Cohesion: 0.23
Nodes (15): build_paper(), _extract(), _levels(), _mcq(), _number(), Random, Syllabus, Topic (+7 more)

### Community 160 - "pastpapergen/cli.py"
Cohesion: 0.12
Nodes (20): default_output_dir(), generate_package(), main(), _normalise_paper_id(), Path, _theme_plan(), PaperConfig, PaperBlueprint (+12 more)

### Community 161 - "test_source_booklet.py"
Cohesion: 0.49
Nodes (9): _pdf_page_count(), _pdf_text(), Path, test_paper_2_source_cover_uses_generation_date_and_official_session(), test_source_booklet_extracts_have_reference_style_line_numbers(), test_source_booklet_for_paper_1_only_uses_section_b(), test_source_booklet_for_paper_3_uses_both_sections(), test_source_booklet_has_figure_extracts_and_source_attributions() (+1 more)

### Community 163 - "_build_part"
Cohesion: 0.13
Nodes (18): MultipleChoiceOption, _build_part(), _build_parts(), _choose_topic(), _compatible_stimulus_kind(), _group_prompt(), _indicative_content(), _mark_breakdown() (+10 more)

### Community 164 - "source_cases.py"
Cohesion: 0.36
Nodes (9): _section_c_extract(), _article_length_extract(), data_response_extract(), _is_macro_title(), _macro_fallback(), _micro_fallback(), _normalise(), section_c_extract() (+1 more)

### Community 165 - "test_paper_configs.py"
Cohesion: 0.50
Nodes (3): test_paper_1_matches_core_edexcel_structure(), test_paper_2_matches_the_reference_section_a_part_plan(), test_paper_3_uses_all_themes_and_two_data_response_sections()

### Community 166 - "_apply_edexcel_page_boxes"
Cohesion: 0.67
Nodes (3): _apply_edexcel_page_boxes(), Path, Match Pearson question-paper bleed and crop boxes without changing A4 content.

## Knowledge Gaps
- **370 isolated node(s):** `BoardLayout`, `examforge-aqa-accounting`, `$schema`, `$id`, `title` (+365 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **54 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Work-memory lessons

**Preferred sources** — corroborated by past sessions; start here.
- `AppViewModel` (2× useful, score=1.93771633) _(code changed — re-verify)_
- `generation.py` (2× useful, score=1.935301773) _(code changed — re-verify)_
- `exam_blueprints.py` (2× useful, score=1.87301818) _(code changed — re-verify)_
- `layout_master.py` (2× useful, score=1.87301818) _(code changed — re-verify)_
- `paper_fidelity_audit.py` (2× useful, score=1.87301818) _(code changed — re-verify)_

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Rect` connect `Rect` to `Paragraph`, `ocregen/render_pdf.py`, `GeneratedPaper`, `paper_fidelity_audit.py`, `aqaecongen/render_pdf.py`?**
  _High betweenness centrality (0.208) - this node is a cross-community bridge._
- **Why does `_block_mask()` connect `paper_fidelity_audit.py` to `Rect`?**
  _High betweenness centrality (0.192) - this node is a cross-community bridge._
- **Why does `AppViewModel` connect `AppViewModel` to `View`, `OllamaModelRecommendation`, `BackendClient`, `GeneratedFile`, `Foundation`, `BenchmarkChart`, `AppDefaults`, `.board`, `SwiftUI`, `QualityState`, `String`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `GeneratedQuestion` (e.g. with `AssessmentLLMClient` and `GenerationPolicy`) actually correct?**
  _`GeneratedQuestion` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 126 inferred relationships involving `Paragraph` (e.g. with `aqa_front_matter_pages()` and `_accounting_marking_guidance_pages()`) actually correct?**
  _`Paragraph` has 126 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `AppViewModel` (e.g. with `PaperCreator` and `.body`) actually correct?**
  _`AppViewModel` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `BoardLayout`, `examforge-aqa-accounting`, `$schema` to the rest of the system?**
  _370 weakly-connected nodes found - possible documentation gaps or missing edges._