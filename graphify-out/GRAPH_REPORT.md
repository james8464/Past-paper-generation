# Graph Report - Past Paper Creation  (2026-08-23)

## Corpus Check
- 241 files · ~450,631 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3101 nodes · 9145 edges · 162 communities (108 shown, 54 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 515 edges (avg confidence: 0.69)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c96a1267`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cspapergen/render_pdf.py
- formatted_generation_date
- AppViewModel
- View
- Paragraph
- ocregen/render_pdf.py
- GeneratedPaper
- test_render_pdf.py
- aqabizgen/generator.py
- build_paper_blueprint
- load_builtin_paper_config
- ocrcsgen/render_pdf.py
- paper_fidelity_audit.py
- reference_corpus.py
- aqaecongen/render_pdf.py
- test_coverage_matrix.py
- CodingKeys
- AssessmentCheckpointStore
- model_recommendations.py
- Rect
- cspapergen/generator.py
- render_pdf_atomically
- benchmark.py
- AppViewModel.swift
- pastpapergen/cli.py
- BackendEvent
- SwiftUI
- BenchmarkChart
- QualityState
- String
- Paper creator: deep project analysis
- Q: Which Ollama model and live validation path does the project use for all supported papers?
- graphs.py
- pastpapergen/ollama_client.py
- generation.py
- OllamaModelRecommendation
- exam_blueprints.py
- BackendClient
- test_mark_scheme_layout.py
- GeneratedFile
- aqa_accounting_calibration.py
- test_app_backend.py
- pastpapergen/notes.py
- Canvas
- Global Constraints
- generate_package
- ocr_computer_science_calibration.py
- Foundation
- Q: How does the generation quality pipeline connect?
- question_bank.py
- providers.py
- Q: Where should performance and generated-paper accuracy fixes be made?
- Contract-First Paper Generation and Release Qualification
- emit
- generator_capabilities
- properties
- _mark_scheme_rows
- AssessmentContract
- Q: How is the macOS backend bundle kept complete?
- File Structure
- test_aqa_accounting.py
- model_review.py
- Rendering and Mark-Scheme Reliability Implementation Plan
- Architecture
- _draw_cover
- mark_scheme_enrichment.py
- Glossy Black Fountain Pen App Icon Master
- test_ollama_generation.py
- enum
- Assessment quality and originality
- .initialEstimate
- macOS interaction and HIG compliance
- write_assessment_package
- Q: how can we make even more improvements to get the highest similarity in terms of structure and layout and quality of questions etc. and maybe all of the files in the project can be better organised. and the UI can be made to be much better and more geometrically apple-like by strictly following every single rule they outline in their HIG
- Paper creator
- cspapergen/exam_dates.py
- pull_request_template.md
- ocrcsgen/generator.py
- backend-protocol.schema.json
- pastpapergen/render_pdf.py
- HelpTopic
- generator_working_directory
- xcbuild.sh
- psychometrics.py
- capabilities
- CoverProfile
- ocr_economics_calibration.py
- diagnose.sh
- move_to_trash.sh
- run_app_ios_sim.sh
- run_app_macos.sh
- required
- Core/__init__.py
- Sidebar
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
- render_source_booklet
- IncomeStatementCase
- SalesLedgerCase
- GeneratedQuestion
- cspapergen/ollama_client.py
- NonCurrentAssetCase
- PartnershipCase
- test_production_pdf_renderers_run_inside_atomic_transactions
- Q: How does the paper fidelity audit produce per-document and per-role scores, and where should release thresholds integrate?
- CostingCase
- aqaaccountgen/cli.py
- aqaaccountgen/generator.py
- cspapergen/notes.py
- CodingKeys
- .load
- backend_version
- source_cases.py
- OllamaModelGuideError

## God Nodes (most connected - your core abstractions)
1. `GeneratedQuestion` - 181 edges
2. `build_paper_blueprint()` - 125 edges
3. `AppViewModel` - 116 edges
4. `load_builtin_paper_config()` - 111 edges
5. `load_syllabus()` - 111 edges
6. `GeneratedOption` - 96 edges
7. `GeneratedPaper` - 85 edges
8. `AssessmentCheckpointStore` - 53 edges
9. `build_question()` - 53 edges
10. `QuestionStyle` - 51 edges

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

## Communities (162 total, 54 thin omitted)

### Community 0 - "cspapergen/render_pdf.py"
Cohesion: 0.06
Nodes (110): _draw_aqa_footer(), _draw_aqa_page(), _draw_barcode(), draw_exam_page(), _draw_independent_notice(), _draw_ocr_notice(), _draw_ocr_page(), _draw_ocr_rules() (+102 more)

### Community 1 - "formatted_generation_date"
Cohesion: 0.14
Nodes (22): QuestionPaperCover, Fixed-grid, board-shaped front page without copying protected artwork., _wrap(), formatted_generation_date(), formatted_generation_series(), generation_date(), date, Return the month/year form used on mark-scheme covers. (+14 more)

### Community 2 - "AppViewModel"
Cohesion: 0.05
Nodes (31): AnyCancellable, Binding, DateFormatter, Error, Int32, .body, .body, ProgressEntry (+23 more)

### Community 3 - "View"
Cohesion: 0.10
Nodes (31): View, HelpCallout, .body, HelpScreenshot, .body, HelpSection, .body, HelpSheet (+23 more)

### Community 4 - "Paragraph"
Cohesion: 0.11
Nodes (68): Paragraph, _nearest_hundred(), _written(), _accounting_marking_guidance_pages(), _accounting_system_case(), _accounting_table(), _additional_answer_page(), AnswerLines (+60 more)

### Community 5 - "ocregen/render_pdf.py"
Cohesion: 0.08
Nodes (75): _add_economics_diagram(), _add_firm_objectives_diagram(), _add_ppf_diagram(), _annotation_conventions_page(), _answer_mark(), AnswerLines, _assessment_allocation(), _assessment_grid_groups() (+67 more)

### Community 6 - "GeneratedPaper"
Cohesion: 0.11
Nodes (56): GeneratedPaper, aqa_front_matter_pages(), Flowable, _additional_answer_page(), AnswerLines, _ao_summary(), _assessment_objectives_page(), _banner() (+48 more)

### Community 7 - "test_render_pdf.py"
Cohesion: 0.12
Nodes (47): _extra_answer_pages(), render_question_paper(), _table_rows(), _blank_axis_lines(), _blueprint_with_section_a_question(), _dark_pixels(), _first_page_containing(), _long_horizontal_line_count() (+39 more)

### Community 8 - "aqabizgen/generator.py"
Cohesion: 0.09
Nodes (32): generate_package(), Path, FinancialPosition, format_number(), Format an exam answer without meaningless trailing zeroes., The single source of truth for Paper 1 financial-statement figures., build_paper(), _extract() (+24 more)

### Community 9 - "build_paper_blueprint"
Cohesion: 0.08
Nodes (61): MultipleChoiceOption, _best_section_a_context_point(), build_paper_blueprint(), _build_part(), _build_parts(), _choice_group_name(), _choice_lookup(), _choose_topic() (+53 more)

### Community 10 - "load_builtin_paper_config"
Cohesion: 0.11
Nodes (46): load_builtin_paper_config(), load_syllabus(), Path, Syllabus, test_blueprint_contains_structured_mcq_and_mark_scheme_content(), test_blueprint_is_deterministic_for_seed(), test_blueprint_uses_only_allowed_theme_topics(), test_blueprint_varies_topics_within_section_when_enough_topics_exist() (+38 more)

### Community 11 - "ocrcsgen/render_pdf.py"
Cohesion: 0.12
Nodes (34): ExamPage, Flowable, A full-page shell that can also live inside a Platypus story., Return a Table subclass whose raw string cells use the controlled font.…, themed_table_class(), _additional_answer_page(), _additional_pages(), AnswerLines (+26 more)

### Community 12 - "paper_fidelity_audit.py"
Cohesion: 0.07
Nodes (77): Image, Pixmap, parametrize, Path, test_compact_profile_omits_raster_geometry(), test_contact_sheets_make_visual_review_artifacts(), test_generated_document_falls_back_to_nested_transaction_output(), test_generated_document_supports_app_per_paper_directories() (+69 more)

### Community 13 - "reference_corpus.py"
Cohesion: 0.14
Nodes (44): MonkeyPatch, Path, test_document_path_requires_filename(), test_document_path_stays_inside_corpus(), test_download_manifest_records_failure_and_continues(), test_parse_aqa_resources_filters_modified_papers(), test_parse_ocr_resources_uses_a_level_tab_only(), test_parse_ocr_specifications_keeps_a_level_not_as_level() (+36 more)

### Community 14 - "aqaecongen/render_pdf.py"
Cohesion: 0.13
Nodes (42): AnswerLines, _assessment_objectives_table(), _context_data_table(), _context_first_page(), _context_second_page(), _cover(), _cover_profile(), _document() (+34 more)

### Community 15 - "test_coverage_matrix.py"
Cohesion: 0.07
Nodes (55): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence(), family(), matrix(), Path, test_catalog_availability_is_owned_only_by_registry() (+47 more)

### Community 16 - "CodingKeys"
Cohesion: 0.05
Nodes (40): CodingKeys, backendVersion, capabilities, command, cpuLoad, cpuMBs, detail, diskFreeGB (+32 more)

### Community 17 - "AssessmentCheckpointStore"
Cohesion: 0.13
Nodes (26): AssessmentCheckpointStore, CheckpointCorrupt, CheckpointIdentity, CheckpointMismatch, identity_for_blueprint(), Any, BaseModel, Path (+18 more)

### Community 18 - "model_recommendations.py"
Cohesion: 0.16
Nodes (24): default_ollama_model(), model_recommendations(), OllamaModelRecommendations, OllamaModelTier, parse_model_recommendations(), Any, _required_text(), jobs() (+16 more)

### Community 19 - "Rect"
Cohesion: 0.06
Nodes (68): conform_generated_documents(), Path, _clamp_fitz_rect(), conform_pdf_page_boxes(), conform_pdf_to_box_template(), draw_text_slot(), _fitz_rect_close(), LayoutConformanceError (+60 more)

### Community 20 - "cspapergen/generator.py"
Cohesion: 0.27
Nodes (15): _align_paper1_structure(), build_paper1_blueprint(), _build_paper1_context(), _build_paper1_questions(), _paper1_part(), _paper1_question(), _paper2_marking_checks(), PaperBlueprint (+7 more)

### Community 21 - "render_pdf_atomically"
Cohesion: 0.07
Nodes (56): InvalidRenderOutput, Path, A document role could not be rendered safely., Rendering exceeded its bounded qualification window., A renderer returned without producing a readable PDF., Render one PDF role under a deadline and promote it atomically., _readable_page_count(), _render_deadline (+48 more)

### Community 22 - "benchmark.py"
Cohesion: 0.14
Nodes (30): apple_cpu_core_split(), available_memory_gb(), avg(), clamp(), cpu_brand(), cpu_load_percent(), cpu_probe(), disk_probe() (+22 more)

### Community 23 - "AppViewModel.swift"
Cohesion: 0.18
Nodes (9): AppKit, Combine, RunningOperation, generation, modelPull, none, PaperCreator, UserNotifications (+1 more)

### Community 24 - "pastpapergen/cli.py"
Cohesion: 0.13
Nodes (17): default_output_dir(), generate_package(), main(), _normalise_paper_id(), Path, OllamaClient, PaperBlueprint, Syllabus (+9 more)

### Community 25 - "BackendEvent"
Cohesion: 0.08
Nodes (14): BackendEvent, benchmarkDone, benchmarkMetric, benchmarkSample, done, error, file, hello (+6 more)

### Community 26 - "SwiftUI"
Cohesion: 0.09
Nodes (22): App, Commands, Context, AppCommands, PaperCreator, .body, AISettingsTab, PrivacySettingsTab (+14 more)

### Community 27 - "BenchmarkChart"
Cohesion: 0.09
Nodes (30): Charts, KeyPath, PanelEmptyState, .body, String, BenchmarkVerdict, BenchmarkChart, .body (+22 more)

### Community 28 - "QualityState"
Cohesion: 0.11
Nodes (23): Color, GenerationProgress, .body, GeneratorWorkspace, .body, .generateHelp, .workspace, PaperConfiguration (+15 more)

### Community 29 - "String"
Cohesion: 0.06
Nodes (63): Codable, Decodable, Equatable, Hashable, Identifiable, AIProvider, anthropic, apple (+55 more)

### Community 30 - "Paper creator: deep project analysis"
Cohesion: 0.05
Nodes (42): Implementation and fidelity report, Full-matrix validation, Highest-value next engineering work, Implemented changes, Manual PDF review, Outcome, What code cannot honestly prove, 10. Completion and file handling (+34 more)

### Community 31 - "Q: Which Ollama model and live validation path does the project use for all supported papers?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Which Ollama model and live validation path does the project use for all supported papers?, Source Nodes

### Community 32 - "graphs.py"
Cohesion: 0.30
Nodes (26): Axes, ad_as_diagram(), _arrow_axes(), _ax(), circular_flow_diagram(), consumer_producer_surplus(), demand_supply_diagram(), _ensure_style() (+18 more)

### Community 33 - "pastpapergen/ollama_client.py"
Cohesion: 0.16
Nodes (21): assert_materially_new(), _validate_ai_question(), QuestionBlueprint, Syllabus, SyllabusTopic, build_question_prompt(), _clean_prompt(), _has_word_starts() (+13 more)

### Community 34 - "generation.py"
Cohesion: 0.19
Nodes (22): progress_emitter(), _atomic_publish(), _cancel_generation(), checkpoint_path_for_job(), emit_generated_files(), finalize_generated_documents(), GenerationCancelled, _generator_version() (+14 more)

### Community 35 - "OllamaModelRecommendation"
Cohesion: 0.16
Nodes (13): tiers, OllamaModelGuide, .currentRecommendation, OllamaModelGuideDocument, OllamaModelRecommendation, .downloadDescription, Bool, Bundle (+5 more)

### Community 36 - "exam_blueprints.py"
Cohesion: 0.08
Nodes (53): _demand_band(), _hydrate_assessment_metadata(), _objective_allocation(), PaperRule, _prompt_uses_command_word(), QuestionRule, _structured_scheme(), validate_generated_paper() (+45 more)

### Community 37 - "BackendClient"
Cohesion: 0.18
Nodes (15): LocalizedError, BackendClient, BackendClientError, backendMissing, .errorDescription, pythonMissing, pythonVenvUnreadable, BackendFile (+7 more)

### Community 38 - "test_mark_scheme_layout.py"
Cohesion: 0.20
Nodes (27): pdf_font_names(), Path, Return the font families actually used by visible text spans., _cleanup_graph_cache(), render_mark_scheme(), _blueprint_with_section_a_calculation(), _blueprint_with_section_b_topic(), _pdf_page_count() (+19 more)

### Community 39 - "GeneratedFile"
Cohesion: 0.21
Nodes (8): GeneratedFilesTable, GeneratedFile, .exists, .paperDescription, .title, Date, URL, UUID

### Community 40 - "aqa_accounting_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_both_papers_pass_multi_seed_automated_checks(), test_external_difficulty_gates_remain_false(), test_reference_evidence_is_aggregate_only(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 41 - "test_app_backend.py"
Cohesion: 0.16
Nodes (27): absolute_user_path(), Path, Expand a user path without resolving sandbox-approved symlinks., _safe_provider_detail(), CompletedProcess, Path, run_bridge(), run_bridge_raw() (+19 more)

### Community 42 - "pastpapergen/notes.py"
Cohesion: 0.20
Nodes (19): _clean_chunk(), essay_capable_topic_ids(), _flush_note_chunk(), _is_exam_point(), _is_note_noise(), _looks_like_heading(), _note_chunks(), note_context_for_topic() (+11 more)

### Community 43 - "Canvas"
Cohesion: 0.10
Nodes (54): _answer_line_count(), _count_pages(), _draw_answer_lines(), _draw_answer_lines_until(), _draw_answer_page_header(), _draw_calculate_part_with_working_lines(), _draw_centred_instruction_line(), _draw_compact_part() (+46 more)

### Community 44 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Measured Paper Fidelity Implementation Plan, Task 1: Page-role-aware fidelity evidence, Task 2: Shared board answer-page geometry, Task 3: OCR response and blank-page grammar, Task 4: Shared mark-scheme cover calibration, Task 5: Full visual qualification and regression gate

### Community 45 - "generate_package"
Cohesion: 0.08
Nodes (48): extract_pdf_text(), Extract stable reading-order text without a Poppler CLI dependency., default_output_dir(), generate_package(), main(), Path, build_paper2_blueprint(), load_syllabus() (+40 more)

### Community 47 - "ocr_computer_science_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_difficulty_remains_external_evidence_gated(), test_multi_seed_structural_demand_passes(), test_reference_evidence_is_aggregate_only(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 48 - "Foundation"
Cohesion: 0.08
Nodes (15): Foundation, AppDefaults, AppLinks, AppStorageKey, SecretAccount, Bool, String, URL (+7 more)

### Community 49 - "Q: How does the generation quality pipeline connect?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: How does the generation quality pipeline connect?, Source Nodes

### Community 50 - "question_bank.py"
Cohesion: 0.23
Nodes (53): Stimulus, _assembly_program_question(), _assembly_trace_question(), _big_data_question(), _big_data_short_question(), _binary_short_question(), _bitmap_question(), _boolean_question() (+45 more)

### Community 51 - "providers.py"
Cohesion: 0.11
Nodes (29): hosted_client(), HostedLLMClient, _normalise_base_url(), _ollama_json_schema(), _ollama_output_budget(), _ollama_seed(), _ollama_temperature(), _openai_output_text() (+21 more)

### Community 52 - "Q: Where should performance and generated-paper accuracy fixes be made?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Where should performance and generated-paper accuracy fixes be made?, Source Nodes

### Community 53 - "Contract-First Paper Generation and Release Qualification"
Cohesion: 0.06
Nodes (31): 1. Assessment Contract, 2. Deterministic Assessment Data, 3. Item-Level AI Workflow, 4. Evidence Binding and Factual Quality, 5. Mark-Scheme Quality, 6. Board Layout Adapters, 7. Bounded Rendering, 8. Progress, Cancellation, and Resume (+23 more)

### Community 55 - "emit"
Cohesion: 0.26
Nodes (16): build_parser(), handle_bundle_check(), main(), ArgumentParser, Namespace, Fail fast when a packaged backend is missing a dynamic generator., emit(), emit_progress() (+8 more)

### Community 56 - "generator_capabilities"
Cohesion: 0.30
Nodes (11): _capability(), generator_capabilities(), generator_capability(), generator_subjects(), Any, _relative_path(), test_backend_bundle_script_is_registry_driven(), test_every_advertised_generator_creates_unique_ai_content() (+3 more)

### Community 57 - "properties"
Cohesion: 0.12
Nodes (17): type, minimum, type, type, type, type, properties, code (+9 more)

### Community 58 - "_mark_scheme_rows"
Cohesion: 0.13
Nodes (29): _brief_source_evidence(), _calculation_answer_lines(), _draw_source_content_page(), _mark_scheme_rows(), _normalise_mark_point(), _one_mark_points(), _paper_one_fifteen_mark_scheme_lines(), _paper_one_five_mark_diagram_lines() (+21 more)

### Community 59 - "AssessmentContract"
Cohesion: 0.08
Nodes (48): AssessmentContract, contract_for_question(), EvidenceRecord, GeneratedNumericField, GraphContract, _numeric_contracts(), NumericRole, NumericValueContract (+40 more)

### Community 60 - "Q: How is the macOS backend bundle kept complete?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: How is the macOS backend bundle kept complete?, Source Nodes

### Community 61 - "File Structure"
Cohesion: 0.17
Nodes (11): Assessment Reliability Core Implementation Plan, File Structure, Global Constraints, Subsequent Phase Plans, Task 1: Typed Item Contracts, Task 2: Role-Aware Numeric and Evidence Validation, Task 3: Item-Scoped Draft, Review, and Repair, Task 4: Atomic Checkpoints and Resume (+3 more)

### Community 62 - "test_aqa_accounting.py"
Cohesion: 0.22
Nodes (20): generate_package(), Path, build_paper(), Syllabus, page_count(), Path, test_both_packages_render_36_page_question_papers(), test_contribution_question_uses_a_complete_costing_identity() (+12 more)

### Community 65 - "model_review.py"
Cohesion: 0.28
Nodes (10): independent_review(), JSONClient, Any, Protocol, require_independent_review(), _serialise(), ReviewClient, test_independent_review_rejects_approval_with_reported_issues() (+2 more)

### Community 66 - "Rendering and Mark-Scheme Reliability Implementation Plan"
Cohesion: 0.25
Nodes (7): Rendering and Mark-Scheme Reliability Implementation Plan, Task 1: Bounded atomic render transactions, Task 2: Route every generator family through the transaction, Task 3: Artifact containment, collision, and density evidence, Task 4: Mark-scheme depth contracts, Task 5: OCR Economics pagination regression, Task 6: Phase qualification

### Community 67 - "Architecture"
Cohesion: 0.22
Nodes (8): Architecture, Canonical registry, Extension contract, Fidelity qualification boundary, Package transaction, Product boundary, Repository map, Trust boundaries

### Community 68 - "_draw_cover"
Cohesion: 0.18
Nodes (16): economics_exam_schedule(), ExamSchedule, formatted_economics_exam_date(), date, _draw_boxes(), _draw_cover(), _draw_fake_barcode(), _draw_front_section() (+8 more)

### Community 69 - "mark_scheme_enrichment.py"
Cohesion: 0.24
Nodes (17): _application_label(), _clean_text(), _compact_technical_guidance(), _deduplicate(), enrich_paper(), _enrich_question(), _level_guidance(), _objective_guidance() (+9 more)

### Community 70 - "Glossy Black Fountain Pen App Icon Master"
Cohesion: 0.18
Nodes (11): Glossy Black Fountain Pen App Icon Master, Paper Creator App Icon AppIcon-128x128@1x, Paper Creator App Icon AppIcon-128x128@2x, Paper Creator App Icon AppIcon-16x16@1x, Paper Creator App Icon AppIcon-16x16@2x, Paper Creator App Icon AppIcon-256x256@1x, Paper Creator App Icon AppIcon-256x256@2x, Paper Creator App Icon AppIcon-32x32@1x (+3 more)

### Community 71 - "test_ollama_generation.py"
Cohesion: 0.21
Nodes (16): generate_questions_with_ollama(), _merge_source_text(), PaperBlueprint, Syllabus, BlueprintAwareClient, EmptyClient, _line(), _new_question() (+8 more)

### Community 72 - "enum"
Cohesion: 0.18
Nodes (11): benchmark_done, benchmark_metric, benchmark_sample, done, error, file, hello, models (+3 more)

### Community 73 - "Assessment quality and originality"
Cohesion: 0.22
Nodes (8): Assessment quality and originality, Difficulty claims, Human release review, Item transactions and two-pass generation, Mark-scheme quality, Measured visual qualification, Novelty and exposure, Release invariants

### Community 74 - ".initialEstimate"
Cohesion: 0.21
Nodes (11): EstimateFactor, GenerationEstimate, .etaDate, .remainingText, GenerationEstimator, Bool, Date, Double (+3 more)

### Community 75 - "macOS interaction and HIG compliance"
Cohesion: 0.22
Nodes (8): Accessibility verification, Commands and state, File workflow, Geometry and visual language, Information architecture, macOS interaction and HIG compliance, Onboarding and help, Settings

### Community 76 - "write_assessment_package"
Cohesion: 0.15
Nodes (29): _evidence_ids(), _extract_items(), _form_id(), Any, Path, Write the renderer-independent item record used by release validation., _scheme_text(), _serialise() (+21 more)

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

### Community 82 - "ocrcsgen/generator.py"
Cohesion: 0.11
Nodes (30): generate_package(), Path, load_rule(), _question(), _sections(), _analysis_prompt(), build_paper(), _levels() (+22 more)

### Community 84 - "backend-protocol.schema.json"
Cohesion: 0.29
Nodes (6): additionalProperties, allOf, $id, $schema, title, type

### Community 85 - "pastpapergen/render_pdf.py"
Cohesion: 0.10
Nodes (37): BoardLayout, GraphParams, _axis_labels_for_draw_prompt(), _bar_chart_data(), _bar_label(), _draw_axis_arrow(), _draw_bar_chart(), _draw_blank_answer_axes() (+29 more)

### Community 86 - "HelpTopic"
Cohesion: 0.17
Nodes (12): CaseIterable, HelpTopic, checkingQuality, choosingAModel, creatingAPaper, gettingStarted, .id, privacy (+4 more)

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

### Community 91 - "CoverProfile"
Cohesion: 0.14
Nodes (22): aqa_question_cover(), CoverProfile, _draw_aqa_mark_scheme_cover(), _draw_cover_barcode(), draw_mark_scheme_cover(), _draw_ocr_mark_scheme_cover(), mark_scheme_cover(), MarkSchemeCover (+14 more)

### Community 92 - "ocr_economics_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 97 - "required"
Cohesion: 0.33
Nodes (6): event_id, job_id, protocol, timestamp, type, required

### Community 99 - "Sidebar"
Cohesion: 0.25
Nodes (8): BoardRow, .body, Sidebar, .body, .expandedSubjects, Bool, String, Set

### Community 101 - "build_backend.sh"
Cohesion: 0.29
Nodes (5): MPLCONFIGDIR, PYINSTALLER_CONFIG_DIR, PYTHONPATH, build_backend.sh script, XDG_CACHE_HOME

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

### Community 152 - "render_source_booklet"
Cohesion: 0.28
Nodes (15): _apply_edexcel_page_boxes(), _extract_source_questions(), Path, Match Pearson question-paper bleed and crop boxes without changing A4 content., render_source_booklet(), _source_sections(), _pdf_page_count(), _pdf_text() (+7 more)

### Community 155 - "GeneratedQuestion"
Cohesion: 0.09
Nodes (76): AssessmentLLMClient, _batches_for_client(), _bounded_text(), _candidate_question(), _canonical_objective_allocation(), _clean_generated_prompt(), _contains_command_word(), _effective_batch_size() (+68 more)

### Community 156 - "cspapergen/ollama_client.py"
Cohesion: 0.16
Nodes (17): MarkingGuidance, MultipleChoiceOption, PaperBlueprint, BaseModel, QuestionPart, Syllabus, SyllabusTopic, _clean() (+9 more)

### Community 159 - "test_production_pdf_renderers_run_inside_atomic_transactions"
Cohesion: 0.40
Nodes (5): Call, _call_name(), parametrize, Path, test_production_pdf_renderers_run_inside_atomic_transactions()

### Community 160 - "Q: How does the paper fidelity audit produce per-document and per-role scores, and where should release thresholds integrate?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: How does the paper fidelity audit produce per-document and per-role scores, and where should release thresholds integrate?, Source Nodes

### Community 162 - "aqaaccountgen/cli.py"
Cohesion: 0.24
Nodes (7): field_validator, load_rule(), load_syllabus(), BaseModel, Path, Syllabus, Topic

### Community 163 - "aqaaccountgen/generator.py"
Cohesion: 0.39
Nodes (7): _extract(), _levels(), _mcq(), _number(), Random, Topic, _values()

### Community 165 - "cspapergen/notes.py"
Cohesion: 0.38
Nodes (9): cache_notes(), discover_note_pdfs(), _extract_text(), note_context_for_topic(), NotesManifest, Path, _topic_prefixes(), test_cache_notes_extracts_text_into_project_cache() (+1 more)

### Community 166 - "CodingKeys"
Cohesion: 0.11
Nodes (18): CodingKey, CodingKeys, appContextWindow, contextWindow, defaultModel, detail, downloadSizeGB, id (+10 more)

### Community 167 - ".load"
Cohesion: 0.21
Nodes (12): CatalogLoader, CatalogLoadError, duplicateBoard, duplicateImplementation, emptyImplementation, .errorDescription, implementationMissingFromCatalog, missingResource (+4 more)

### Community 169 - "source_cases.py"
Cohesion: 0.36
Nodes (9): _section_c_extract(), _article_length_extract(), data_response_extract(), _is_macro_title(), _macro_fallback(), _micro_fallback(), _normalise(), section_c_extract() (+1 more)

### Community 170 - "OllamaModelGuideError"
Cohesion: 0.33
Nodes (6): OllamaModelGuideError, .errorDescription, invalidDefault, missingResource, unsupportedSchema, String

## Knowledge Gaps
- **388 isolated node(s):** `BoardLayout`, `examforge-aqa-accounting`, `$schema`, `$id`, `title` (+383 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **54 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Work-memory lessons

**Preferred sources** — corroborated by past sessions; start here.
- `AppViewModel` (2× useful, score=1.166012741)
- `generation.py` (2× useful, score=1.164559792)
- `exam_blueprints.py` (2× useful, score=1.127080899)
- `layout_master.py` (2× useful, score=1.127080899)
- `paper_fidelity_audit.py` (2× useful, score=1.127080899) _(code changed — re-verify)_

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Rect` connect `Rect` to `cspapergen/render_pdf.py`, `Paragraph`, `ocregen/render_pdf.py`, `GeneratedPaper`, `paper_fidelity_audit.py`, `aqaecongen/render_pdf.py`, `CoverProfile`?**
  _High betweenness centrality (0.208) - this node is a cross-community bridge._
- **Why does `_block_mask()` connect `paper_fidelity_audit.py` to `Rect`?**
  _High betweenness centrality (0.184) - this node is a cross-community bridge._
- **Why does `AppViewModel` connect `AppViewModel` to `View`, `Sidebar`, `OllamaModelRecommendation`, `BackendClient`, `GeneratedFile`, `.initialEstimate`, `Foundation`, `AppViewModel.swift`, `BackendEvent`, `SwiftUI`, `BenchmarkChart`, `QualityState`, `String`?**
  _High betweenness centrality (0.098) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `GeneratedQuestion` (e.g. with `AssessmentLLMClient` and `GenerationPolicy`) actually correct?**
  _`GeneratedQuestion` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 123 inferred relationships involving `Paragraph` (e.g. with `aqa_front_matter_pages()` and `_accounting_marking_guidance_pages()`) actually correct?**
  _`Paragraph` has 123 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `AppViewModel` (e.g. with `PaperCreator` and `.body`) actually correct?**
  _`AppViewModel` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `BoardLayout`, `examforge-aqa-accounting`, `$schema` to the rest of the system?**
  _388 weakly-connected nodes found - possible documentation gaps or missing edges._