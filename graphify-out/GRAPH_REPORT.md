# Graph Report - Past Paper Creation  (2026-08-26)

## Corpus Check
- 295 files · ~507,913 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 4257 nodes · 11908 edges · 199 communities (147 shown, 52 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 761 edges (avg confidence: 0.67)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1888185b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cspapergen/render_pdf.py
- paths.py
- AppViewModel
- .load
- Paragraph
- ocregen/render_pdf.py
- GeneratedPaper
- test_render_pdf.py
- aqabizgen/generator.py
- pastpapergen/generator.py
- build_paper_blueprint
- CoverProfile
- paper_fidelity_audit.py
- reference_corpus.py
- aqaecongen/render_pdf.py
- test_coverage_matrix.py
- CodingKeys
- AssessmentCheckpointStore
- pdf_validation.py
- layout_master.py
- live_generation_matrix.py
- test_ocr_economics.py
- benchmark.py
- BackendEvent
- mark_scheme_enrichment.py
- document_dsl/__init__.py
- render_pdf_atomically
- Text
- assessment_package.py
- String
- Paper creator: deep project analysis
- Q: Which Ollama model and live validation path does the project use for all supported papers?
- graphs.py
- _wrap
- generation.py
- pastpapergen/cli.py
- properties
- BackendClient
- test_mark_scheme_layout.py
- ModelCoordinator
- Approved-Improvement Traceability
- test_app_backend.py
- pastpapergen/notes.py
- Canvas
- Global Constraints
- load_syllabus
- CodingKeys
- Paper Creator Excellence Programme Design
- aqa_accounting_calibration.py
- Q: How does the generation quality pipeline connect?
- question_bank.py
- providers.py
- Q: Where should performance and generated-paper accuracy fixes be made?
- Contract-First Paper Generation and Release Qualification
- build_layout_masters.py
- emit
- generator_registry.py
- properties
- _mark_scheme_rows
- AssessmentContract
- Q: How is the macOS backend bundle kept complete?
- File Structure
- BenchmarkChart
- aqaecongen/generator.py
- RecentDocumentStore
- model_review.py
- Rendering and Mark-Scheme Reliability Implementation Plan
- Architecture
- pastpapergen/render_pdf.py
- test_aqa_accounting.py
- Glossy Black Fountain Pen App Icon Master
- pastpapergen/ollama_client.py
- enum
- Assessment quality and originality
- .generate
- macOS interaction and HIG compliance
- test_layout_master.py
- test_pdf_validation.py
- Q: how can we make even more improvements to get the highest similarity in terms of structure and layout and quality of questions etc. and maybe all of the files in the project can be better organised. and the UI can be made to be much better and more geometrically apple-like by strictly following every single rule they outline in their HIG
- Paper creator
- ArtifactSpec
- pull_request_template.md
- test_ocr_computer_science.py
- required
- backend-protocol.schema.json
- IncomeStatementCase
- JobHistoryView
- generator_working_directory
- xcbuild.sh
- psychometrics.py
- capabilities
- aqa_business_calibration.py
- Table
- diagnose.sh
- move_to_trash.sh
- run_app_ios_sim.sh
- run_app_macos.sh
- ocr_computer_science_calibration.py
- Core/__init__.py
- .initialEstimate
- bootstrap_backend.sh
- build_backend.sh
- clean.sh
- resolve_agent_name.sh
- resolve_sim_destination.sh
- aqaaccountgen/__init__.py
- AnswerLineFlowable
- aqabizgen/__init__.py
- cspapergen/__init__.py
- ocrcsgen/__init__.py
- aqaecongen/__init__.py
- pastpapergen/__init__.py
- ocregen/__init__.py
- tools/__init__.py
- graphify
- aqaaccountgen/syllabus.py
- type
- progress
- NonCurrentAssetCase
- PaperCreator Xcode Project Configuration
- aqa-economics-practice-generator
- cspapergen
- examforge-aqa-accounting
- examforge-aqa-business
- examforge-ocr-computer-science
- ocr-economics-practice-generator
- pastpapergen
- PyInstaller Build Dependency
- ExamBoardOption
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
- aqaaccountgen/generator.py
- DocumentPreviewView
- GeneratedQuestion
- cspapergen/generator.py
- economics_exam_schedule
- properties
- _call_name
- Q: How does the paper fidelity audit produce per-document and per-role scores, and where should release thresholds integrate?
- OllamaModelGuideError
- .baseQuery
- qualification_levels
- exam_blueprints.py
- OllamaModelRecommendation
- CostingCase
- properties
- SalesLedgerCase
- required
- event_id
- Rect
- CodingKeys
- generate_package
- PartnershipCase
- required
- qualification-schema.json
- properties
- enum
- enum
- model
- _draw_ms_row
- additionalProperties
- generator-capability.schema.json
- register_fonts
- tool_versions
- formatted_generation_date
- cspapergen/cli.py
- enum
- required
- backend_subject
- app_board
- blueprint_version
- board_profile
- entry_point
- specification_version
- subject_plugin
- enum
- id

## God Nodes (most connected - your core abstractions)
1. `GeneratedQuestion` - 193 edges
2. `build_paper_blueprint()` - 160 edges
3. `AppViewModel` - 145 edges
4. `load_builtin_paper_config()` - 144 edges
5. `load_syllabus()` - 143 edges
6. `GeneratedOption` - 100 edges
7. `Table` - 93 edges
8. `GeneratedPaper` - 85 edges
9. `build_question()` - 54 edges
10. `_Task` - 52 edges

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

## Communities (199 total, 52 thin omitted)

### Community 0 - "cspapergen/render_pdf.py"
Cohesion: 0.06
Nodes (113): _draw_aqa_footer(), _draw_aqa_page(), _draw_barcode(), draw_exam_page(), _draw_independent_notice(), _draw_ocr_notice(), _draw_ocr_page(), _draw_ocr_rules() (+105 more)

### Community 1 - "paths.py"
Cohesion: 0.06
Nodes (41): board_profile(), board_profile_ids(), BoardProfile, _normalise_identifier(), ContractSubjectPlugin, discover_subject_plugin(), _normalise_identifier(), Any (+33 more)

### Community 2 - "AppViewModel"
Cohesion: 0.04
Nodes (45): AnyCancellable, DateFormatter, .body, GeneratedFilesTable, .body, GeneratedFile, .exists, .paperDescription (+37 more)

### Community 3 - ".load"
Cohesion: 0.19
Nodes (12): CatalogLoader, CatalogLoadError, duplicateBoard, duplicateImplementation, emptyImplementation, .errorDescription, implementationMissingFromCatalog, missingResource (+4 more)

### Community 4 - "Paragraph"
Cohesion: 0.16
Nodes (47): Paragraph, _accounting_marking_guidance_pages(), _additional_answer_page(), AnswerLines, _appropriation_answer_table(), _assessment_objectives_page(), _company_statement_case(), _completed_appropriation_scheme() (+39 more)

### Community 5 - "ocregen/render_pdf.py"
Cohesion: 0.08
Nodes (72): _artifacts(), _add_economics_diagram(), _add_firm_objectives_diagram(), _add_ppf_diagram(), _annotation_conventions_page(), _answer_mark(), AnswerLines, _assessment_allocation() (+64 more)

### Community 6 - "GeneratedPaper"
Cohesion: 0.12
Nodes (49): GeneratedPaper, aqa_front_matter_pages(), Flowable, _artifacts(), _additional_answer_page(), AnswerLines, _ao_summary(), _assessment_objectives_page() (+41 more)

### Community 7 - "test_render_pdf.py"
Cohesion: 0.14
Nodes (42): render_question_paper(), _blank_axis_lines(), _blueprint_with_section_a_question(), _dark_pixels(), _first_page_containing(), _long_horizontal_line_count(), _normalised(), _pdf_page_count() (+34 more)

### Community 8 - "aqabizgen/generator.py"
Cohesion: 0.09
Nodes (33): generate_package(), Path, FinancialPosition, format_number(), Format an exam answer without meaningless trailing zeroes., The single source of truth for Paper 1 financial-statement figures., build_paper(), _extract() (+25 more)

### Community 9 - "pastpapergen/generator.py"
Cohesion: 0.06
Nodes (72): MultipleChoiceOption, _adapt_paper_three_case_guidance(), _best_section_a_context_point(), _build_part(), _build_parts(), _choice_group_name(), _choice_lookup(), _choose_topic() (+64 more)

### Community 10 - "build_paper_blueprint"
Cohesion: 0.09
Nodes (76): build_paper_blueprint(), PaperBlueprint, Syllabus, load_builtin_paper_config(), line_chart_data(), load_syllabus(), Path, Syllabus (+68 more)

### Community 11 - "CoverProfile"
Cohesion: 0.17
Nodes (18): CoverProfile, _draw_aqa_mark_scheme_cover(), _draw_cover_barcode(), draw_mark_scheme_cover(), _draw_ocr_mark_scheme_cover(), mark_scheme_cover(), MarkSchemeCover, ocr_question_cover() (+10 more)

### Community 12 - "paper_fidelity_audit.py"
Cohesion: 0.06
Nodes (95): Pixmap, parametrize, Path, test_compact_profile_omits_raster_geometry(), test_contact_sheets_make_visual_review_artifacts(), test_generated_document_falls_back_to_nested_transaction_output(), test_generated_document_supports_app_per_paper_directories(), test_page_role_classification() (+87 more)

### Community 13 - "reference_corpus.py"
Cohesion: 0.13
Nodes (45): MonkeyPatch, Path, test_document_path_requires_filename(), test_document_path_stays_inside_corpus(), test_download_manifest_records_failure_and_continues(), test_parse_aqa_resources_filters_modified_papers(), test_parse_ocr_resources_uses_a_level_tab_only(), test_parse_ocr_specifications_keeps_a_level_not_as_level() (+37 more)

### Community 14 - "aqaecongen/render_pdf.py"
Cohesion: 0.13
Nodes (42): aqa_question_cover(), _artifacts(), AnswerLines, _assessment_objectives_table(), _context_data_table(), _context_first_page(), _context_second_page(), _cover() (+34 more)

### Community 15 - "test_coverage_matrix.py"
Cohesion: 0.07
Nodes (56): family(), matrix(), Path, test_catalog_availability_is_owned_only_by_registry(), test_checked_in_matrix_is_deterministic_and_current(), test_existing_generators_are_reported_without_false_verification(), test_matrix_exactly_covers_layout_profiles(), test_no_verified_paper_has_a_failed_gate() (+48 more)

### Community 16 - "CodingKeys"
Cohesion: 0.04
Nodes (45): CodingKeys, backendVersion, capabilities, checks, code, command, cpuLoad, cpuMBs (+37 more)

### Community 17 - "AssessmentCheckpointStore"
Cohesion: 0.13
Nodes (27): AssessmentCheckpointStore, CheckpointCorrupt, CheckpointIdentity, CheckpointMismatch, identity_for_blueprint(), Any, BaseModel, Path (+19 more)

### Community 18 - "pdf_validation.py"
Cohesion: 0.16
Nodes (26): compare_page_evidence(), _contrast_against_white(), _count_score(), extract_pdf_evidence(), _font_embedding(), _font_evidence(), _layout_profiles(), _leading() (+18 more)

### Community 19 - "layout_master.py"
Cohesion: 0.16
Nodes (19): _clamp_fitz_rect(), conform_pdf_page_boxes(), draw_text_slot(), _fitz_rect_close(), load_layout_master(), _page_from_payload(), _page_matches_box_set(), PageMaster (+11 more)

### Community 20 - "live_generation_matrix.py"
Cohesion: 0.07
Nodes (58): default_ollama_model(), model_recommendations(), OllamaModelRecommendations, OllamaModelTier, parse_model_recommendations(), Any, _required_text(), Release qualification evidence and policy models. (+50 more)

### Community 21 - "test_ocr_economics.py"
Cohesion: 0.10
Nodes (36): generate_package(), Path, build_paper(), _evaluation_scheme(), _extract(), _extract_number(), _instructions(), _mcq() (+28 more)

### Community 22 - "benchmark.py"
Cohesion: 0.12
Nodes (33): apple_cpu_core_split(), available_memory_gb(), avg(), clamp(), cpu_brand(), cpu_load_percent(), cpu_probe(), disk_probe() (+25 more)

### Community 23 - "BackendEvent"
Cohesion: 0.05
Nodes (25): BackendEvent, benchmarkDone, benchmarkMetric, benchmarkSample, done, error, file, hello (+17 more)

### Community 24 - "mark_scheme_enrichment.py"
Cohesion: 0.22
Nodes (20): _answer_form(), _application_label(), _clean_text(), _compact_technical_guidance(), _deduplicate(), enrich_paper(), _enrich_question(), _level_guidance() (+12 more)

### Community 25 - "document_dsl/__init__.py"
Cohesion: 0.07
Nodes (75): AnswerSpace, BaseComponent, BlankPage, Component, ContinuationPage, Cover, Diagram, Graph (+67 more)

### Community 26 - "render_pdf_atomically"
Cohesion: 0.15
Nodes (23): InvalidRenderOutput, Path, RuntimeError, A document role could not be rendered safely., Rendering exceeded its bounded qualification window., A renderer returned without producing a readable PDF., Render one PDF role under a deadline and promote it atomically., _readable_page_count() (+15 more)

### Community 27 - "Text"
Cohesion: 0.03
Nodes (105): App, AppKit, Charts, Color, Commands, AppCommands, PaperCreator, .body (+97 more)

### Community 28 - "assessment_package.py"
Cohesion: 0.06
Nodes (70): _assessment_contract(), AssessmentPackageCompatibilityError, _contains_non_finite(), _evidence_ids(), _extract_items(), _form_id(), _level_policies(), load_assessment_package() (+62 more)

### Community 29 - "String"
Cohesion: 0.04
Nodes (67): CaseIterable, Decodable, AIProvider, anthropic, apple, .backendID, .id, ollama (+59 more)

### Community 30 - "Paper creator: deep project analysis"
Cohesion: 0.05
Nodes (42): Implementation and fidelity report, Full-matrix validation, Highest-value next engineering work, Implemented changes, Manual PDF review, Outcome, What code cannot honestly prove, 10. Completion and file handling (+34 more)

### Community 31 - "Q: Which Ollama model and live validation path does the project use for all supported papers?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Which Ollama model and live validation path does the project use for all supported papers?, Source Nodes

### Community 32 - "graphs.py"
Cohesion: 0.30
Nodes (26): Axes, ad_as_diagram(), _arrow_axes(), _ax(), circular_flow_diagram(), consumer_producer_surplus(), demand_supply_diagram(), _ensure_style() (+18 more)

### Community 33 - "_wrap"
Cohesion: 0.16
Nodes (23): _answer_line_count(), _draw_answer_lines(), _draw_answer_lines_until(), _draw_calculate_part_with_working_lines(), _draw_compact_part(), _draw_inline_context(), _draw_mcq_part(), _draw_part_prompt() (+15 more)

### Community 34 - "generation.py"
Cohesion: 0.21
Nodes (21): progress_emitter(), _atomic_publish(), _cancel_generation(), checkpoint_path_for_job(), emit_generated_files(), finalize_generated_documents(), GenerationCancelled, _generator_version() (+13 more)

### Community 35 - "pastpapergen/cli.py"
Cohesion: 0.11
Nodes (23): _artifacts(), _build(), _improve(), _load_rule(), _normalise_paper_id(), MultipleChoiceOption, PaperBlueprint, PaperConfig (+15 more)

### Community 36 - "properties"
Cohesion: 0.09
Nodes (23): type, minLength, type, pattern, type, const, pattern, type (+15 more)

### Community 37 - "BackendClient"
Cohesion: 0.18
Nodes (14): BackendClient, BackendClientError, backendMissing, .errorDescription, pythonMissing, pythonVenvUnreadable, BackendFile, LaunchConfiguration (+6 more)

### Community 38 - "test_mark_scheme_layout.py"
Cohesion: 0.18
Nodes (30): extract_pdf_text(), pdf_font_names(), Path, Extract stable reading-order text without a Poppler CLI dependency., Return the font families actually used by visible text spans., _cleanup_graph_cache(), render_mark_scheme(), _blueprint_with_section_a_calculation() (+22 more)

### Community 39 - "ModelCoordinator"
Cohesion: 0.05
Nodes (34): Foundation, OllamaState, EstimateTuning, AppClock, KeychainSecretStore, SecretStoring, Date, String (+26 more)

### Community 40 - "Approved-Improvement Traceability"
Cohesion: 0.07
Nodes (26): Approved-Improvement Traceability, Current-Paper Gate, Expansion Gate, Foundation Gate, Global Constraints, Paper Creator Excellence Programme Implementation Plan, Phase Completion Gates, Plan Verification Checklist (+18 more)

### Community 41 - "test_app_backend.py"
Cohesion: 0.16
Nodes (27): _safe_provider_detail(), CaptureFixture, CompletedProcess, Path, run_bridge(), run_bridge_raw(), test_aqa_accounting_all_papers_generate_expected_files(), test_aqa_business_all_papers_generate_expected_files() (+19 more)

### Community 42 - "pastpapergen/notes.py"
Cohesion: 0.20
Nodes (19): _clean_chunk(), essay_capable_topic_ids(), _flush_note_chunk(), _is_exam_point(), _is_note_noise(), _looks_like_heading(), _note_chunks(), note_context_for_topic() (+11 more)

### Community 43 - "Canvas"
Cohesion: 0.10
Nodes (46): _count_pages(), _draw_answer_page_header(), _draw_centred_instruction_line(), _draw_continuation_lines(), _draw_do_not_write_rail(), _draw_formula_appendix(), _draw_hatched_rail(), _draw_mark_scheme_end_page() (+38 more)

### Community 44 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Measured Paper Fidelity Implementation Plan, Task 1: Page-role-aware fidelity evidence, Task 2: Shared board answer-page geometry, Task 3: OCR response and blank-page grammar, Task 4: Shared mark-scheme cover calibration, Task 5: Full visual qualification and regression gate

### Community 45 - "load_syllabus"
Cohesion: 0.09
Nodes (52): _build(), build_paper1_blueprint(), build_paper2_blueprint(), PaperBlueprint, Syllabus, improve_questions_with_ollama(), Syllabus, load_syllabus() (+44 more)

### Community 46 - "CodingKeys"
Cohesion: 0.12
Nodes (17): CodingKeys, appContextWindow, contextWindow, defaultModel, detail, downloadSizeGB, id, maximumMemoryGB (+9 more)

### Community 47 - "Paper Creator Excellence Programme Design"
Cohesion: 0.08
Nodes (23): Assessment Validity and Mark Schemes, Baseline on 26 August 2026, Definition of Done, Design Principles, Deterministic Visual Components, Empirical Calibration, Independent Solving, macOS Product Experience (+15 more)

### Community 48 - "aqa_accounting_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_both_papers_pass_multi_seed_automated_checks(), test_external_difficulty_gates_remain_false(), test_reference_evidence_is_aggregate_only(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 49 - "Q: How does the generation quality pipeline connect?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: How does the generation quality pipeline connect?, Source Nodes

### Community 50 - "question_bank.py"
Cohesion: 0.23
Nodes (53): Stimulus, _assembly_program_question(), _assembly_trace_question(), _big_data_question(), _big_data_short_question(), _binary_short_question(), _bitmap_question(), _bitmap_storage_question() (+45 more)

### Community 51 - "providers.py"
Cohesion: 0.10
Nodes (34): _hosted_client(), _aqa_cs_part_count(), _edexcel_part_count(), hosted_client(), HostedLLMClient, _normalise_base_url(), _ollama_json_schema(), _ollama_output_budget() (+26 more)

### Community 52 - "Q: Where should performance and generated-paper accuracy fixes be made?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Where should performance and generated-paper accuracy fixes be made?, Source Nodes

### Community 53 - "Contract-First Paper Generation and Release Qualification"
Cohesion: 0.06
Nodes (31): 1. Assessment Contract, 2. Deterministic Assessment Data, 3. Item-Level AI Workflow, 4. Evidence Binding and Factual Quality, 5. Mark-Scheme Quality, 6. Board Layout Adapters, 7. Bounded Rendering, 8. Progress, Cancellation, and Resume (+23 more)

### Community 54 - "build_layout_masters.py"
Cohesion: 0.26
Nodes (19): _box(), _colour(), _content_box(), _drawing_kind(), _drawings(), extract_layout_master(), _furniture_signature(), _images() (+11 more)

### Community 55 - "emit"
Cohesion: 0.08
Nodes (53): build_parser(), handle_bundle_check(), main(), ArgumentParser, Namespace, Fail fast when a packaged backend is missing a dynamic generator., emit(), emit_progress() (+45 more)

### Community 56 - "generator_registry.py"
Cohesion: 0.24
Nodes (15): _capability(), generator_capabilities(), generator_subjects(), _paper_qualification(), PaperQualification, Any, _relative_path(), test_backend_bundle_script_is_registry_driven() (+7 more)

### Community 57 - "properties"
Cohesion: 0.12
Nodes (17): type, type, type, type, properties, backend_version, code, job_id (+9 more)

### Community 58 - "_mark_scheme_rows"
Cohesion: 0.16
Nodes (25): _brief_source_evidence(), _calculation_answer_lines(), _mark_scheme_rows(), _normalise_mark_point(), _one_mark_points(), _paper_one_fifteen_mark_scheme_lines(), _paper_one_five_mark_diagram_lines(), _paper_one_section_a_mark_scheme_lines() (+17 more)

### Community 59 - "AssessmentContract"
Cohesion: 0.05
Nodes (80): AssessmentContract, contract_for_question(), EvidenceRecord, GeneratedNumericField, GraphContract, _numeric_contracts(), NumericRole, NumericValueContract (+72 more)

### Community 60 - "Q: How is the macOS backend bundle kept complete?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: How is the macOS backend bundle kept complete?, Source Nodes

### Community 61 - "File Structure"
Cohesion: 0.17
Nodes (11): Assessment Reliability Core Implementation Plan, File Structure, Global Constraints, Subsequent Phase Plans, Task 1: Typed Item Contracts, Task 2: Role-Aware Numeric and Evidence Validation, Task 3: Item-Scoped Draft, Review, and Repair, Task 4: Atomic Checkpoints and Resume (+3 more)

### Community 62 - "BenchmarkChart"
Cohesion: 0.22
Nodes (14): KeyPath, BenchmarkChart, BenchmarkLiveCharts, .body, .cpuChart, .cpuThroughputChart, .diskWriteChart, .memoryChart (+6 more)

### Community 63 - "aqaecongen/generator.py"
Cohesion: 0.13
Nodes (27): generate_package(), main(), Path, _build_mcq_option(), build_paper(), _build_written_option(), _case_depth(), _paper_three_indicative_content() (+19 more)

### Community 64 - "RecentDocumentStore"
Cohesion: 0.07
Nodes (37): Codable, Equatable, FileManager, GenerationJobState, LocalizedError, GenerationConfiguration, GenerationJobRecord, .missingArtifactCount (+29 more)

### Community 65 - "model_review.py"
Cohesion: 0.23
Nodes (12): assert_materially_new(), independent_review(), JSONClient, Any, Protocol, require_independent_review(), _serialise(), _validate_ai_question() (+4 more)

### Community 66 - "Rendering and Mark-Scheme Reliability Implementation Plan"
Cohesion: 0.25
Nodes (7): Rendering and Mark-Scheme Reliability Implementation Plan, Task 1: Bounded atomic render transactions, Task 2: Route every generator family through the transaction, Task 3: Artifact containment, collision, and density evidence, Task 4: Mark-scheme depth contracts, Task 5: OCR Economics pagination regression, Task 6: Phase qualification

### Community 67 - "Architecture"
Cohesion: 0.22
Nodes (8): Architecture, Canonical registry, Extension contract, Fidelity qualification boundary, Package transaction, Product boundary, Repository map, Trust boundaries

### Community 68 - "pastpapergen/render_pdf.py"
Cohesion: 0.10
Nodes (35): BoardLayout, GraphParams, _axis_labels_for_draw_prompt(), _bar_chart_data(), _bar_label(), _draw_axis_arrow(), _draw_bar_chart(), _draw_blank_answer_axes() (+27 more)

### Community 69 - "test_aqa_accounting.py"
Cohesion: 0.37
Nodes (12): generate_package(), Path, page_count(), Path, test_both_packages_render_36_page_question_papers(), test_invalid_paper_is_rejected(), test_non_current_asset_question_and_mark_scheme_use_the_same_figures(), test_paper_one_mark_scheme_matches_reference_question_sequence() (+4 more)

### Community 70 - "Glossy Black Fountain Pen App Icon Master"
Cohesion: 0.18
Nodes (11): Glossy Black Fountain Pen App Icon Master, Paper Creator App Icon AppIcon-128x128@1x, Paper Creator App Icon AppIcon-128x128@2x, Paper Creator App Icon AppIcon-16x16@1x, Paper Creator App Icon AppIcon-16x16@2x, Paper Creator App Icon AppIcon-256x256@1x, Paper Creator App Icon AppIcon-256x256@2x, Paper Creator App Icon AppIcon-32x32@1x (+3 more)

### Community 71 - "pastpapergen/ollama_client.py"
Cohesion: 0.08
Nodes (56): QuestionBlueprint, SyllabusTopic, build_question_prompt(), _clean_prompt(), generate_questions_with_ollama(), _has_word_starts(), _matches_expected_question_style(), _merge_part_prompt() (+48 more)

### Community 72 - "enum"
Cohesion: 0.18
Nodes (11): benchmark_done, benchmark_metric, benchmark_sample, done, error, file, hello, models (+3 more)

### Community 73 - "Assessment quality and originality"
Cohesion: 0.17
Nodes (11): Assessment quality and originality, Difficulty claims, Human release review, Independent solution and response-band qualification, Item transactions and two-pass generation, Mark-scheme quality, Measured visual qualification, Novelty and exposure (+3 more)

### Community 74 - ".generate"
Cohesion: 0.07
Nodes (24): AppDefaults, AppLinks, AppStorageKey, SecretAccount, Bool, String, URL, MLXRecoveryState (+16 more)

### Community 75 - "macOS interaction and HIG compliance"
Cohesion: 0.22
Nodes (8): Accessibility verification, Commands and state, File workflow, Geometry and visual language, Information architecture, macOS interaction and HIG compliance, Onboarding and help, Settings

### Community 76 - "test_layout_master.py"
Cohesion: 0.20
Nodes (12): conform_generated_documents(), Path, conform_pdf_to_box_template(), LayoutConformanceError, PageCountPolicy, Apply measured box sets without importing reference artwork or text. A single…, Path, _sample_pdf() (+4 more)

### Community 77 - "test_pdf_validation.py"
Cohesion: 0.28
Nodes (15): GlyphMetric, A compact, serialisable sample of one rendered PDF glyph., Canvas, Path, _release_canvas(), test_duplicate_text_at_the_same_position_is_rejected(), test_glyph_metric_contract_is_immutable(), test_image_only_page_is_not_reported_as_empty() (+7 more)

### Community 78 - "Q: how can we make even more improvements to get the highest similarity in terms of structure and layout and quality of questions etc. and maybe all of the files in the project can be better organised. and the UI can be made to be much better and more geometrically apple-like by strictly following every single rule they outline in their HIG"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: how can we make even more improvements to get the highest similarity in terms of structure and layout and quality of questions etc. and maybe all of the files in the project can be better organised. and the UI can be made to be much better and more geometrically apple-like by strictly following every single rule they outline in their HIG, Source Nodes

### Community 79 - "Paper creator"
Cohesion: 0.25
Nodes (8): Architecture and quality analysis, Build Checks, CLI, Development Reference Corpus, Paper creator, Privacy, Run, Structure

### Community 80 - "ArtifactSpec"
Cohesion: 0.27
Nodes (11): ArtifactSpec, _artifacts(), _chrome(), _cover(), _cover_profile(), _document(), BaseDocTemplate, Path (+3 more)

### Community 81 - "pull_request_template.md"
Cohesion: 0.50
Nodes (3): Risk, Verification, What changed

### Community 82 - "test_ocr_computer_science.py"
Cohesion: 0.08
Nodes (42): BuildResult, FamilyAdapter, Path, run_family_adapter(), ProgressCallback, generate_package(), Path, _analysis_prompt() (+34 more)

### Community 83 - "required"
Cohesion: 0.09
Nodes (22): advertised, app_board, app_subject, backend_subject, blueprint_version, board, board_profile, content_mode (+14 more)

### Community 84 - "backend-protocol.schema.json"
Cohesion: 0.15
Nodes (12): event_id, job_id, protocol, timestamp, type, additionalProperties, allOf, $id (+4 more)

### Community 86 - "JobHistoryView"
Cohesion: 0.25
Nodes (9): GenerationJobState, .systemImage, .title, JobHistoryView, .body, .selectedRecord, GenerationJobRecord, Set (+1 more)

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

### Community 91 - "aqa_business_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 92 - "Table"
Cohesion: 0.09
Nodes (48): Table, ExamPage, Flowable, A full-page shell that can also live inside a Platypus story., _accounting_system_case(), _accounting_table(), _banner(), _box() (+40 more)

### Community 97 - "ocr_computer_science_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_difficulty_remains_external_evidence_gated(), test_multi_seed_structural_demand_passes(), test_reference_evidence_is_aggregate_only(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 99 - ".initialEstimate"
Cohesion: 0.19
Nodes (11): EstimateFactor, GenerationEstimate, .etaDate, .remainingText, TimeInterval, GenerationEstimator, Bool, Date (+3 more)

### Community 101 - "build_backend.sh"
Cohesion: 0.29
Nodes (5): MPLCONFIGDIR, PYINSTALLER_CONFIG_DIR, PYTHONPATH, build_backend.sh script, XDG_CACHE_HOME

### Community 106 - "AnswerLineFlowable"
Cohesion: 0.22
Nodes (6): AnswerLineFlowable, Flowable, Return a Table subclass whose raw string cells use the controlled font.…, Shared, measured answer-line primitive used by every board renderer., themed_table_class(), TableType

### Community 115 - "aqaaccountgen/syllabus.py"
Cohesion: 0.28
Nodes (6): load_syllabus(), BaseModel, field_validator, Path, Syllabus, Topic

### Community 116 - "type"
Cohesion: 0.50
Nodes (4): null, string, stage, type

### Community 117 - "progress"
Cohesion: 0.50
Nodes (4): maximum, minimum, type, progress

### Community 120 - "NonCurrentAssetCase"
Cohesion: 0.15
Nodes (3): _nearest_hundred(), NonCurrentAssetCase, test_non_current_asset_question_and_scheme_share_verified_case_data()

### Community 130 - "ExamBoardOption"
Cohesion: 0.07
Nodes (39): Hashable, Identifiable, CatalogSubject, ExamBoardOption, .isReady, .usesAI, ExamCatalog, .defaultBoard (+31 more)

### Community 152 - "render_source_booklet"
Cohesion: 0.28
Nodes (15): _apply_edexcel_page_boxes(), _extract_source_questions(), Path, Match Pearson question-paper bleed and crop boxes without changing A4 content., render_source_booklet(), _source_sections(), _pdf_page_count(), _pdf_text() (+7 more)

### Community 153 - "aqaaccountgen/generator.py"
Cohesion: 0.20
Nodes (17): build_paper(), _extract(), _levels(), _management_calculation(), _mcq(), _number(), Random, Syllabus (+9 more)

### Community 154 - "DocumentPreviewView"
Cohesion: 0.05
Nodes (36): Combine, DocumentPreviewView, .body, .exportAlertBinding, .provenanceRecord, .selectedBinding, .selectedFile, PDFDocumentView (+28 more)

### Community 155 - "GeneratedQuestion"
Cohesion: 0.08
Nodes (95): AssessmentLLMClient, _batches_for_client(), _bounded_text(), _candidate_question(), _canonical_objective_allocation(), _clean_generated_prompt(), _contains_command_word(), _effective_batch_size() (+87 more)

### Community 156 - "cspapergen/generator.py"
Cohesion: 0.10
Nodes (29): _align_paper1_structure(), _build_paper1_context(), _build_paper1_questions(), _paper1_part(), _paper1_question(), _paper2_marking_checks(), QuestionPart, Random (+21 more)

### Community 157 - "economics_exam_schedule"
Cohesion: 0.46
Nodes (6): economics_exam_schedule(), ExamSchedule, formatted_economics_exam_date(), date, _draw_mark_scheme_qualification_page(), test_edexcel_9ec0_2026_timetable_dates()

### Community 158 - "properties"
Cohesion: 0.11
Nodes (18): type, format, type, type, minLength, type, minLength, type (+10 more)

### Community 159 - "_call_name"
Cohesion: 0.38
Nodes (6): Call, _call_name(), parametrize, Path, test_production_pdf_renderers_run_inside_atomic_transactions(), test_shared_family_adapter_owns_atomic_pdf_transaction()

### Community 160 - "Q: How does the paper fidelity audit produce per-document and per-role scores, and where should release thresholds integrate?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: How does the paper fidelity audit produce per-document and per-role scores, and where should release thresholds integrate?, Source Nodes

### Community 161 - "OllamaModelGuideError"
Cohesion: 0.33
Nodes (6): OllamaModelGuideError, .errorDescription, invalidDefault, missingResource, unsupportedSchema, String

### Community 162 - ".baseQuery"
Cohesion: 0.39
Nodes (4): SecretStore, Any, String, Security

### Community 163 - "qualification_levels"
Cohesion: 0.14
Nodes (14): empirically_calibrated, engineering_validated, visually_calibrated, type, type, empirically_calibrated, engineering_validated, qualification_levels (+6 more)

### Community 164 - "exam_blueprints.py"
Cohesion: 0.13
Nodes (32): _demand_band(), _hydrate_assessment_metadata(), _objective_allocation(), PaperRule, _prompt_uses_command_word(), QuestionRule, _structured_scheme(), validate_generated_paper() (+24 more)

### Community 165 - "OllamaModelRecommendation"
Cohesion: 0.16
Nodes (13): tiers, OllamaModelGuide, .currentRecommendation, OllamaModelGuideDocument, OllamaModelRecommendation, .downloadDescription, Bool, Bundle (+5 more)

### Community 167 - "properties"
Cohesion: 0.12
Nodes (16): minLength, type, minLength, type, minLength, type, blueprint, contract (+8 more)

### Community 169 - "required"
Cohesion: 0.15
Nodes (13): artifacts, created_at, evidence, gate_results, generator_id, model, paper_id, reviewer_identity_class (+5 more)

### Community 170 - "event_id"
Cohesion: 0.67
Nodes (3): minimum, type, event_id

### Community 171 - "Rect"
Cohesion: 0.24
Nodes (8): Rect, _overlapping_text_pairs(), Path, Fail closed on malformed, substituted, annotated, or low-resolution PDFs., _text_occupancy(), validate_pdf_for_release(), _chart(), _paper_three_figure()

### Community 172 - "CodingKeys"
Cohesion: 0.18
Nodes (11): CodingKey, CodingKeys, artifacts, configuration, createdAt, id, provenance, qualification (+3 more)

### Community 173 - "generate_package"
Cohesion: 0.25
Nodes (8): type, path, default_output_dir(), generate_package(), main(), Path, test_generate_package_reports_rendering_progress(), test_generate_package_without_seed_does_not_write_audit()

### Community 175 - "required"
Cohesion: 0.22
Nodes (9): blueprint, contract, prompt, renderer, syllabus, versions, additionalProperties, required (+1 more)

### Community 176 - "qualification-schema.json"
Cohesion: 0.33
Nodes (5): additionalProperties, $id, $schema, title, type

### Community 177 - "properties"
Cohesion: 0.33
Nodes (9): type, null, string, properties, type, digest, name, provider (+1 more)

### Community 178 - "enum"
Cohesion: 0.25
Nodes (8): failed, not_applicable, not_run, passed, enum, additionalProperties, type, gate_results

### Community 179 - "enum"
Cohesion: 0.29
Nodes (7): automation, examiner, internal_reviewer, psychometrician, subject_specialist, reviewer_identity_class, enum

### Community 180 - "model"
Cohesion: 0.29
Nodes (7): digest, name, provider, additionalProperties, required, type, model

### Community 181 - "_draw_ms_row"
Cohesion: 0.53
Nodes (6): _draw_ms_row(), _ms_bold_line(), _ms_centered_line(), _ms_row_height(), _ms_wrap_width(), _split_mark_scheme_row()

### Community 182 - "additionalProperties"
Cohesion: 0.13
Nodes (15): items, minItems, type, uniqueItems, items, minItems, type, uniqueItems (+7 more)

### Community 183 - "generator-capability.schema.json"
Cohesion: 0.17
Nodes (11): additionalProperties, $defs, safePath, $id, pattern, minLength, not, type (+3 more)

### Community 184 - "register_fonts"
Cohesion: 0.52
Nodes (5): register_font(), register_fonts(), _standard_fallback(), test_fallback_family_supports_bold_paragraph_markup(), test_missing_font_uses_registered_standard_font_alias()

### Community 185 - "tool_versions"
Cohesion: 0.50
Nodes (4): type, tool_versions, additionalProperties, type

### Community 187 - "formatted_generation_date"
Cohesion: 0.12
Nodes (24): QuestionPaperCover, Fixed-grid, board-shaped front page without copying protected artwork., Return the renderer-neutral representation used for qualification., _wrap(), formatted_generation_date(), formatted_generation_series(), generation_date(), date (+16 more)

### Community 188 - "cspapergen/cli.py"
Cohesion: 0.10
Nodes (31): default_output_dir(), generate_package(), _improve(), main(), Path, cache_notes(), discover_note_pdfs(), _extract_text() (+23 more)

### Community 189 - "enum"
Cohesion: 0.22
Nodes (9): anthropic, apple, ollama, openai, enum, supported_providers, items, type (+1 more)

### Community 190 - "required"
Cohesion: 0.22
Nodes (9): checks, detail, id, qualification, title, required, items, type (+1 more)

### Community 191 - "backend_subject"
Cohesion: 0.67
Nodes (3): pattern, type, backend_subject

### Community 192 - "app_board"
Cohesion: 0.67
Nodes (3): minLength, type, app_board

### Community 195 - "blueprint_version"
Cohesion: 0.67
Nodes (3): minLength, type, blueprint_version

### Community 196 - "board_profile"
Cohesion: 0.67
Nodes (3): pattern, type, board_profile

### Community 197 - "entry_point"
Cohesion: 0.67
Nodes (3): pattern, type, entry_point

### Community 198 - "specification_version"
Cohesion: 0.67
Nodes (3): specification_version, minLength, type

### Community 199 - "subject_plugin"
Cohesion: 0.67
Nodes (3): subject_plugin, pattern, type

### Community 200 - "enum"
Cohesion: 0.50
Nodes (4): ai-assisted, deterministic, enum, content_mode

### Community 201 - "id"
Cohesion: 0.67
Nodes (3): pattern, type, id

## Knowledge Gaps
- **625 isolated node(s):** `BoardLayout`, `examforge-aqa-accounting`, `$schema`, `$id`, `title` (+620 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **52 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Work-memory lessons

**Preferred sources** — corroborated by past sessions; start here.
- `AppViewModel` (2× useful, score=1.166012741) _(code changed — re-verify)_
- `generation.py` (2× useful, score=1.164559792) _(code changed — re-verify)_
- `exam_blueprints.py` (2× useful, score=1.127080899)
- `layout_master.py` (2× useful, score=1.127080899) _(code changed — re-verify)_
- `paper_fidelity_audit.py` (2× useful, score=1.127080899) _(code changed — re-verify)_

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `GeneratedQuestion` connect `GeneratedQuestion` to `exam_blueprints.py`, `Paragraph`, `GeneratedPaper`, `ocregen/render_pdf.py`, `aqabizgen/generator.py`, `aqaecongen/render_pdf.py`, `AssessmentCheckpointStore`, `test_ocr_computer_science.py`, `test_ocr_economics.py`, `mark_scheme_enrichment.py`, `aqaaccountgen/generator.py`, `AssessmentContract`, `Table`, `aqaecongen/generator.py`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `DocumentRole` connect `document_dsl/__init__.py` to `cspapergen/render_pdf.py`, `Paragraph`, `pastpapergen/render_pdf.py`, `GeneratedPaper`, `ocregen/render_pdf.py`, `aqaecongen/render_pdf.py`, `Table`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Why does `renderer_contract()` connect `document_dsl/__init__.py` to `cspapergen/render_pdf.py`, `Paragraph`, `pastpapergen/render_pdf.py`, `GeneratedPaper`, `ocregen/render_pdf.py`, `aqaecongen/render_pdf.py`, `Table`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `GeneratedQuestion` (e.g. with `AssessmentLLMClient` and `GenerationPolicy`) actually correct?**
  _`GeneratedQuestion` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `AppViewModel` (e.g. with `PaperCreator` and `.body`) actually correct?**
  _`AppViewModel` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `BoardLayout`, `examforge-aqa-accounting`, `$schema` to the rest of the system?**
  _625 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `cspapergen/render_pdf.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06212121212121212 - nodes in this community are weakly interconnected._