# Graph Report - Past Paper Creation  (2026-08-26)

## Corpus Check
- 303 files · ~514,569 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 4470 nodes · 12268 edges · 212 communities (160 shown, 52 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 728 edges (avg confidence: 0.67)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ba787157`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cspapergen/render_pdf.py
- paths.py
- ApplicationCoordinator
- Foundation
- GeneratedQuestion
- Paragraph
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
- pdf_validation.py
- Text
- live_generation_matrix.py
- test_ocr_economics.py
- benchmark.py
- formatted_generation_date
- mark_scheme_enrichment.py
- test_document_dsl.py
- ExamBoardOption
- GeneratedOption
- assessment_package.py
- BackendEvent
- Paper creator: deep project analysis
- Q: Which Ollama model and live validation path does the project use for all supported papers?
- graphs.py
- pastpapergen/ollama_client.py
- generation.py
- generate_package
- properties
- ocr_economics_calibration.py
- test_mark_scheme_layout.py
- ai_assessment.py
- Approved-Improvement Traceability
- test_app_backend.py
- pastpapergen/notes.py
- .load
- Global Constraints
- load_syllabus
- test_mlx_setup.py
- Paper Creator Excellence Programme Design
- properties
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
- aqaecongen/generator.py
- View
- RecentDocumentStore
- ReviewResult
- Rendering and Mark-Scheme Reliability Implementation Plan
- Architecture
- pastpapergen/render_pdf.py
- test_ollama_generation.py
- Glossy Black Fountain Pen App Icon Master
- CoverProfile
- enum
- Assessment quality and originality
- GeneratedFile
- macOS interaction and HIG compliance
- layout_master.py
- test_pdf_validation.py
- Q: how can we make even more improvements to get the highest similarity in terms of structure and layout and quality of questions etc. and maybe all of the files in the project can be better organised. and the UI can be made to be much better and more geometrically apple-like by strictly following every single rule they outline in their HIG
- Paper creator
- independent_solver.py
- pull_request_template.md
- test_ocr_computer_science.py
- required
- backend-protocol.schema.json
- properties
- IncomeStatementCase
- generator_working_directory
- xcbuild.sh
- psychometrics.py
- capabilities
- cspapergen/generator.py
- BackendClient
- diagnose.sh
- move_to_trash.sh
- run_app_ios_sim.sh
- run_app_macos.sh
- String
- Core/__init__.py
- properties
- bootstrap_backend.sh
- build_backend.sh
- clean.sh
- resolve_agent_name.sh
- resolve_sim_destination.sh
- aqaaccountgen/__init__.py
- cspapergen/cli.py
- aqabizgen/__init__.py
- cspapergen/__init__.py
- ocrcsgen/__init__.py
- aqaecongen/__init__.py
- pastpapergen/__init__.py
- ocregen/__init__.py
- tools/__init__.py
- graphify
- required
- type
- progress
- aqa_business_calibration.py
- PaperCreator Xcode Project Configuration
- aqa-economics-practice-generator
- cspapergen
- examforge-aqa-accounting
- examforge-aqa-business
- examforge-ocr-computer-science
- ocr-economics-practice-generator
- pastpapergen
- PyInstaller Build Dependency
- required
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
- test_source_booklet.py
- aqaaccountgen/generator.py
- DocumentPreviewView
- test_ai_assessment.py
- AIProvider
- _draw_cover
- properties
- _call_name
- Q: How does the paper fidelity audit produce per-document and per-role scores, and where should release thresholds integrate?
- required
- .initialEstimate
- qualification_levels
- NonCurrentAssetCase
- CodingKeys
- required
- properties
- properties
- required
- generate_package
- sample
- empirical-calibration.schema.json
- Canvas
- exam_blueprints.py
- required
- qualification-schema.json
- properties
- enum
- enum
- model
- ocr_computer_science_calibration.py
- additionalProperties
- generator-capability.schema.json
- CodingKeys
- tool_versions
- subject_plugin
- BenchmarkChart
- test_aqa_accounting.py
- enum
- required
- backend_subject
- app_board
- app_subject
- board
- JobHistoryView
- ModelCoordinator
- entry_point
- BenchmarkCoordinator
- test_repository_hygiene.py
- cspapergen/notes.py
- id
- board_profile
- SettingsPane.swift
- PaperBlueprint
- PartnershipCase
- aqaaccountgen/syllabus.py
- Rect
- .baseQuery
- SalesLedgerCase
- enum
- README.md

## God Nodes (most connected - your core abstractions)
1. `GeneratedQuestion` - 188 edges
2. `build_paper_blueprint()` - 160 edges
3. `load_builtin_paper_config()` - 144 edges
4. `load_syllabus()` - 143 edges
5. `ApplicationCoordinator` - 137 edges
6. `GeneratedOption` - 95 edges
7. `Table` - 93 edges
8. `GeneratedPaper` - 80 edges
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

## Communities (212 total, 52 thin omitted)

### Community 0 - "cspapergen/render_pdf.py"
Cohesion: 0.06
Nodes (112): _draw_aqa_footer(), _draw_aqa_page(), _draw_barcode(), draw_exam_page(), _draw_independent_notice(), _draw_ocr_notice(), _draw_ocr_page(), _draw_ocr_rules() (+104 more)

### Community 1 - "paths.py"
Cohesion: 0.06
Nodes (41): board_profile(), board_profile_ids(), BoardProfile, _normalise_identifier(), ContractSubjectPlugin, discover_subject_plugin(), _normalise_identifier(), Any (+33 more)

### Community 2 - "ApplicationCoordinator"
Cohesion: 0.04
Nodes (34): AnyCancellable, DateFormatter, .body, .body, AISettingsTab, .body, .providerSettings, OutputSettingsTab (+26 more)

### Community 3 - "Foundation"
Cohesion: 0.06
Nodes (24): Foundation, EstimateTuning, KeychainSecretStore, SecretStoring, Date, String, URL, SystemAppClock (+16 more)

### Community 4 - "GeneratedQuestion"
Cohesion: 0.14
Nodes (47): GeneratedQuestion, _nearest_hundred(), _written(), _accounting_marking_guidance_pages(), _additional_answer_page(), _assessment_objectives_page(), _chrome(), _completed_appropriation_scheme() (+39 more)

### Community 5 - "Paragraph"
Cohesion: 0.09
Nodes (75): OCRAnswerLines, Paragraph, _add_economics_diagram(), _add_firm_objectives_diagram(), _add_ppf_diagram(), _annotation_conventions_page(), _answer_mark(), _assessment_allocation() (+67 more)

### Community 6 - "GeneratedPaper"
Cohesion: 0.13
Nodes (47): GeneratedPaper, aqa_front_matter_pages(), Flowable, AQAAnswerLines, _artifacts(), _additional_answer_page(), _ao_summary(), _assessment_objectives_page() (+39 more)

### Community 7 - "test_render_pdf.py"
Cohesion: 0.12
Nodes (48): _apply_edexcel_page_boxes(), _extra_answer_pages(), Path, Match Pearson question-paper bleed and crop boxes without changing A4 content., render_question_paper(), _blank_axis_lines(), _blueprint_with_section_a_question(), _dark_pixels() (+40 more)

### Community 8 - "aqabizgen/generator.py"
Cohesion: 0.09
Nodes (34): GeneratedSection, generate_package(), Path, FinancialPosition, format_number(), Format an exam answer without meaningless trailing zeroes., The single source of truth for Paper 1 financial-statement figures., build_paper() (+26 more)

### Community 9 - "pastpapergen/generator.py"
Cohesion: 0.06
Nodes (72): MultipleChoiceOption, _adapt_paper_three_case_guidance(), _best_section_a_context_point(), _build_part(), _build_parts(), _choice_group_name(), _choice_lookup(), _choose_topic() (+64 more)

### Community 10 - "build_paper_blueprint"
Cohesion: 0.09
Nodes (79): build_paper_blueprint(), PaperBlueprint, Syllabus, load_builtin_paper_config(), line_chart_data(), load_syllabus(), Path, Syllabus (+71 more)

### Community 11 - "ocrcsgen/render_pdf.py"
Cohesion: 0.09
Nodes (38): ExamPage, Flowable, A full-page shell that can also live inside a Platypus story., AnswerLineFlowable, AQACompactAnswerLines, OCRComputerScienceAnswerLines, Flowable, Return a Table subclass whose raw string cells use the controlled font.… (+30 more)

### Community 12 - "paper_fidelity_audit.py"
Cohesion: 0.05
Nodes (97): Pixmap, parametrize, Path, test_compact_profile_omits_raster_geometry(), test_contact_sheets_make_visual_review_artifacts(), test_generated_document_falls_back_to_nested_transaction_output(), test_generated_document_supports_app_per_paper_directories(), test_open_metric_compatible_fonts_match_reference_families() (+89 more)

### Community 13 - "reference_corpus.py"
Cohesion: 0.13
Nodes (45): MonkeyPatch, Path, test_document_path_requires_filename(), test_document_path_stays_inside_corpus(), test_download_manifest_records_failure_and_continues(), test_parse_aqa_resources_filters_modified_papers(), test_parse_ocr_resources_uses_a_level_tab_only(), test_parse_ocr_specifications_keeps_a_level_not_as_level() (+37 more)

### Community 14 - "aqaecongen/render_pdf.py"
Cohesion: 0.14
Nodes (40): _artifacts(), _assessment_objectives_table(), _context_first_page(), _context_second_page(), _cover(), _cover_profile(), _document(), _economic_diagram() (+32 more)

### Community 15 - "test_coverage_matrix.py"
Cohesion: 0.07
Nodes (56): report(), test_both_papers_pass_multi_seed_automated_checks(), test_external_difficulty_gates_remain_false(), test_reference_evidence_is_aggregate_only(), family(), matrix(), Path, test_catalog_availability_is_owned_only_by_registry() (+48 more)

### Community 16 - "CodingKeys"
Cohesion: 0.04
Nodes (47): CodingKeys, backendVersion, capabilities, checks, code, command, cpuLoad, cpuMBs (+39 more)

### Community 17 - "AssessmentCheckpointStore"
Cohesion: 0.15
Nodes (25): AssessmentCheckpointStore, CheckpointCorrupt, CheckpointIdentity, CheckpointMismatch, identity_for_blueprint(), Any, BaseModel, Path (+17 more)

### Community 18 - "pdf_validation.py"
Cohesion: 0.11
Nodes (34): compare_page_evidence(), _contrast_against_white(), _contrast_ratio(), _count_score(), _font_embedding(), _font_evidence(), GlyphMetric, _is_decorative_bleed() (+26 more)

### Community 19 - "Text"
Cohesion: 0.09
Nodes (41): ModelRecommendationTip, .image, .message, .title, PaperCreationTips, PreviewTip, .image, .message (+33 more)

### Community 20 - "live_generation_matrix.py"
Cohesion: 0.08
Nodes (49): Release qualification evidence and policy models., ArtifactEvidence, EvidenceRecord, GateState, ModelIdentity, BaseModel, field_validator, Path (+41 more)

### Community 21 - "test_ocr_economics.py"
Cohesion: 0.10
Nodes (37): generate_package(), Path, build_paper(), _evaluation_scheme(), _extract(), _extract_number(), _instructions(), _mcq() (+29 more)

### Community 22 - "benchmark.py"
Cohesion: 0.12
Nodes (33): apple_cpu_core_split(), available_memory_gb(), avg(), clamp(), cpu_brand(), cpu_load_percent(), cpu_probe(), disk_probe() (+25 more)

### Community 23 - "formatted_generation_date"
Cohesion: 0.06
Nodes (56): QuestionPaperCover, Fixed-grid, board-shaped front page without copying protected artwork., Return the renderer-neutral representation used for qualification., _wrap(), formatted_generation_date(), formatted_generation_series(), generation_date(), date (+48 more)

### Community 24 - "mark_scheme_enrichment.py"
Cohesion: 0.22
Nodes (20): _answer_form(), _application_label(), _clean_text(), _compact_technical_guidance(), _deduplicate(), enrich_paper(), _enrich_question(), _level_guidance() (+12 more)

### Community 25 - "test_document_dsl.py"
Cohesion: 0.07
Nodes (75): AnswerSpace, BaseComponent, BlankPage, Component, ContinuationPage, Cover, Diagram, Graph (+67 more)

### Community 26 - "ExamBoardOption"
Cohesion: 0.07
Nodes (39): Hashable, Identifiable, CatalogSubject, ExamBoardOption, .isReady, .usesAI, .defaultBoard, PaperOption (+31 more)

### Community 27 - "GeneratedOption"
Cohesion: 0.18
Nodes (31): Table, GeneratedOption, _accounting_system_case(), _accounting_table(), _appropriation_answer_table(), _banner(), _box(), _company_statement_case() (+23 more)

### Community 28 - "assessment_package.py"
Cohesion: 0.06
Nodes (70): _assessment_contract(), AssessmentPackageCompatibilityError, _contains_non_finite(), _evidence_ids(), _extract_items(), _form_id(), _level_policies(), load_assessment_package() (+62 more)

### Community 29 - "BackendEvent"
Cohesion: 0.08
Nodes (13): BackendEvent, benchmarkDone, benchmarkMetric, benchmarkSample, done, error, file, hello (+5 more)

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
Cohesion: 0.07
Nodes (47): _artifacts(), _build(), _improve(), _load_rule(), _normalise_paper_id(), MultipleChoiceOption, PaperBlueprint, PaperConfig (+39 more)

### Community 34 - "generation.py"
Cohesion: 0.21
Nodes (21): progress_emitter(), _atomic_publish(), _cancel_generation(), checkpoint_path_for_job(), emit_generated_files(), finalize_generated_documents(), GenerationCancelled, _generator_version() (+13 more)

### Community 35 - "generate_package"
Cohesion: 0.19
Nodes (17): extract_pdf_text(), Extract stable reading-order text without a Poppler CLI dependency., generate_package(), test_final_additional_answer_page_reserves_independent_notice(), test_generate_package_writes_rendered_and_assessment_outputs(), test_generated_pdfs_are_a4(), test_paper_two_transition_leaf_uses_do_not_write_diagonal(), test_question_paper_uses_realistic_aqa_page_count() (+9 more)

### Community 36 - "properties"
Cohesion: 0.09
Nodes (23): type, minLength, type, const, pattern, type, properties, advertised (+15 more)

### Community 37 - "ocr_economics_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 38 - "test_mark_scheme_layout.py"
Cohesion: 0.20
Nodes (28): pdf_font_names(), Path, Return the font families actually used by visible text spans., _cleanup_graph_cache(), render_mark_scheme(), _blueprint_with_section_a_calculation(), _blueprint_with_section_b_topic(), _pdf_page_count() (+20 more)

### Community 39 - "ai_assessment.py"
Cohesion: 0.12
Nodes (30): AssessmentLLMClient, _bounded_text(), _generate_item_transaction(), generate_unique_paper(), _generation_prompt(), _independently_validate_candidate(), _parse_batch(), Any (+22 more)

### Community 40 - "Approved-Improvement Traceability"
Cohesion: 0.07
Nodes (26): Approved-Improvement Traceability, Current-Paper Gate, Expansion Gate, Foundation Gate, Global Constraints, Paper Creator Excellence Programme Implementation Plan, Phase Completion Gates, Plan Verification Checklist (+18 more)

### Community 41 - "test_app_backend.py"
Cohesion: 0.16
Nodes (28): _safe_provider_detail(), CaptureFixture, CompletedProcess, Path, run_bridge(), run_bridge_raw(), test_aqa_accounting_all_papers_generate_expected_files(), test_aqa_business_all_papers_generate_expected_files() (+20 more)

### Community 42 - "pastpapergen/notes.py"
Cohesion: 0.20
Nodes (19): _clean_chunk(), essay_capable_topic_ids(), _flush_note_chunk(), _is_exam_point(), _is_note_noise(), _looks_like_heading(), _note_chunks(), note_context_for_topic() (+11 more)

### Community 43 - ".load"
Cohesion: 0.17
Nodes (12): CatalogLoader, CatalogLoadError, duplicateBoard, duplicateImplementation, emptyImplementation, .errorDescription, implementationMissingFromCatalog, missingResource (+4 more)

### Community 44 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Measured Paper Fidelity Implementation Plan, Task 1: Page-role-aware fidelity evidence, Task 2: Shared board answer-page geometry, Task 3: OCR response and blank-page grammar, Task 4: Shared mark-scheme cover calibration, Task 5: Full visual qualification and regression gate

### Community 45 - "load_syllabus"
Cohesion: 0.09
Nodes (54): build_paper1_blueprint(), build_paper2_blueprint(), PaperBlueprint, Syllabus, improve_questions_with_ollama(), Syllabus, load_syllabus(), Path (+46 more)

### Community 46 - "test_mlx_setup.py"
Cohesion: 0.09
Nodes (43): _available_cache_bytes(), ensure_mlx_ready(), handle_mlx_status(), handle_setup_mlx(), install_mlx_runtime(), is_managed_development_environment(), load_mlx_model(), mlx_runtime_available() (+35 more)

### Community 47 - "Paper Creator Excellence Programme Design"
Cohesion: 0.08
Nodes (23): Assessment Validity and Mark Schemes, Baseline on 26 August 2026, Definition of Done, Design Principles, Deterministic Visual Components, Empirical Calibration, Independent Solving, macOS Product Experience (+15 more)

### Community 48 - "properties"
Cohesion: 0.10
Nodes (21): minLength, type, minLength, type, minLength, type, format, type (+13 more)

### Community 49 - "Q: How does the generation quality pipeline connect?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: How does the generation quality pipeline connect?, Source Nodes

### Community 50 - "question_bank.py"
Cohesion: 0.23
Nodes (53): Stimulus, _assembly_program_question(), _assembly_trace_question(), _big_data_question(), _big_data_short_question(), _binary_short_question(), _bitmap_question(), _bitmap_storage_question() (+45 more)

### Community 51 - "providers.py"
Cohesion: 0.10
Nodes (35): _hosted_client(), _aqa_cs_part_count(), _edexcel_part_count(), hosted_client(), HostedLLMClient, _normalise_base_url(), _ollama_json_schema(), _ollama_output_budget() (+27 more)

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
Cohesion: 0.26
Nodes (16): build_parser(), handle_bundle_check(), main(), ArgumentParser, Namespace, Fail fast when a packaged backend is missing a dynamic generator., emit(), emit_progress() (+8 more)

### Community 56 - "generator_registry.py"
Cohesion: 0.24
Nodes (15): _capability(), generator_capabilities(), generator_subjects(), _paper_qualification(), PaperQualification, Any, _relative_path(), test_backend_bundle_script_is_registry_driven() (+7 more)

### Community 57 - "properties"
Cohesion: 0.10
Nodes (20): type, type, minimum, type, type, type, properties, backend_version (+12 more)

### Community 58 - "_mark_scheme_rows"
Cohesion: 0.16
Nodes (25): _brief_source_evidence(), _calculation_answer_lines(), _mark_scheme_rows(), _normalise_mark_point(), _one_mark_points(), _paper_one_fifteen_mark_scheme_lines(), _paper_one_five_mark_diagram_lines(), _paper_one_section_a_mark_scheme_lines() (+17 more)

### Community 59 - "AssessmentContract"
Cohesion: 0.08
Nodes (49): AssessmentContract, contract_for_question(), GeneratedNumericField, GraphContract, _numeric_contracts(), NumericRole, NumericValueContract, Any (+41 more)

### Community 60 - "Q: How is the macOS backend bundle kept complete?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: How is the macOS backend bundle kept complete?, Source Nodes

### Community 61 - "File Structure"
Cohesion: 0.17
Nodes (11): Assessment Reliability Core Implementation Plan, File Structure, Global Constraints, Subsequent Phase Plans, Task 1: Typed Item Contracts, Task 2: Role-Aware Numeric and Evidence Validation, Task 3: Item-Scoped Draft, Review, and Repair, Task 4: Atomic Checkpoints and Resume (+3 more)

### Community 62 - "aqaecongen/generator.py"
Cohesion: 0.15
Nodes (24): _build_mcq_option(), build_paper(), _build_written_option(), _case_depth(), _paper_three_indicative_content(), policy_name(), Random, Syllabus (+16 more)

### Community 63 - "View"
Cohesion: 0.06
Nodes (42): App, Color, Commands, AppCommands, PaperCreator, .body, View, GeneratedFilesTable (+34 more)

### Community 64 - "RecentDocumentStore"
Cohesion: 0.07
Nodes (35): Codable, Equatable, FileManager, GenerationJobState, LocalizedError, GenerationConfiguration, GenerationJobRecord, .missingArtifactCount (+27 more)

### Community 65 - "ReviewResult"
Cohesion: 0.24
Nodes (12): independent_review(), JSONClient, Any, BaseModel, Protocol, require_independent_review(), ReviewResult, _serialise() (+4 more)

### Community 66 - "Rendering and Mark-Scheme Reliability Implementation Plan"
Cohesion: 0.25
Nodes (7): Rendering and Mark-Scheme Reliability Implementation Plan, Task 1: Bounded atomic render transactions, Task 2: Route every generator family through the transaction, Task 3: Artifact containment, collision, and density evidence, Task 4: Mark-scheme depth contracts, Task 5: OCR Economics pagination regression, Task 6: Phase qualification

### Community 67 - "Architecture"
Cohesion: 0.18
Nodes (10): Architecture, Canonical registry, Extension contract, Failure containment, Fidelity qualification boundary, Package transaction, PDF portability and accessibility, Product boundary (+2 more)

### Community 68 - "pastpapergen/render_pdf.py"
Cohesion: 0.10
Nodes (34): BoardLayout, GraphParams, _bar_chart_data(), _bar_label(), _draw_bar_chart(), _draw_data_table(), _draw_do_not_write_rail(), _draw_economics_graph() (+26 more)

### Community 69 - "test_ollama_generation.py"
Cohesion: 0.12
Nodes (29): generate_questions_with_ollama(), _merge_source_text(), OllamaClient, PaperBlueprint, Syllabus, BlueprintAwareClient, EmptyClient, _line() (+21 more)

### Community 70 - "Glossy Black Fountain Pen App Icon Master"
Cohesion: 0.18
Nodes (11): Glossy Black Fountain Pen App Icon Master, Paper Creator App Icon AppIcon-128x128@1x, Paper Creator App Icon AppIcon-128x128@2x, Paper Creator App Icon AppIcon-16x16@1x, Paper Creator App Icon AppIcon-16x16@2x, Paper Creator App Icon AppIcon-256x256@1x, Paper Creator App Icon AppIcon-256x256@2x, Paper Creator App Icon AppIcon-32x32@1x (+3 more)

### Community 71 - "CoverProfile"
Cohesion: 0.14
Nodes (22): aqa_question_cover(), CoverProfile, _draw_aqa_mark_scheme_cover(), _draw_cover_barcode(), draw_mark_scheme_cover(), _draw_ocr_mark_scheme_cover(), mark_scheme_cover(), MarkSchemeCover (+14 more)

### Community 72 - "enum"
Cohesion: 0.18
Nodes (11): benchmark_done, benchmark_metric, benchmark_sample, done, error, file, hello, models (+3 more)

### Community 73 - "Assessment quality and originality"
Cohesion: 0.17
Nodes (11): Assessment quality and originality, Difficulty claims, Human release review, Independent solution and response-band qualification, Item transactions and two-pass generation, Mark-scheme quality, Measured visual qualification, Novelty and exposure (+3 more)

### Community 74 - "GeneratedFile"
Cohesion: 0.05
Nodes (32): AppDefaults, AppLinks, AppStorageKey, SecretAccount, Bool, String, URL, .body (+24 more)

### Community 75 - "macOS interaction and HIG compliance"
Cohesion: 0.22
Nodes (8): Accessibility verification, Commands and state, File workflow, Geometry and visual language, Information architecture, macOS interaction and HIG compliance, Onboarding and help, Settings

### Community 76 - "layout_master.py"
Cohesion: 0.11
Nodes (31): conform_generated_documents(), Path, _clamp_fitz_rect(), conform_pdf_page_boxes(), conform_pdf_to_box_template(), draw_text_slot(), _fitz_rect_close(), LayoutConformanceError (+23 more)

### Community 77 - "test_pdf_validation.py"
Cohesion: 0.31
Nodes (17): extract_pdf_evidence(), Extract print and accessibility evidence without retaining source prose. Glyph…, Canvas, Path, _release_canvas(), test_duplicate_text_at_the_same_position_is_rejected(), test_image_only_page_is_not_reported_as_empty(), test_layout_metrics_record_each_page() (+9 more)

### Community 78 - "Q: how can we make even more improvements to get the highest similarity in terms of structure and layout and quality of questions etc. and maybe all of the files in the project can be better organised. and the UI can be made to be much better and more geometrically apple-like by strictly following every single rule they outline in their HIG"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: how can we make even more improvements to get the highest similarity in terms of structure and layout and quality of questions etc. and maybe all of the files in the project can be better organised. and the UI can be made to be much better and more geometrically apple-like by strictly following every single rule they outline in their HIG, Source Nodes

### Community 79 - "Paper creator"
Cohesion: 0.25
Nodes (8): Architecture and quality analysis, Build Checks, CLI, Development Reference Corpus, Paper creator, Privacy, Run, Structure

### Community 80 - "independent_solver.py"
Cohesion: 0.12
Nodes (34): EvidenceRecord, content_similarity(), normalise_item_text(), Weighted token-shingle Jaccard similarity in the closed interval 0...1., Return a stable comparison form without conflating visible output text., _as_mapping(), CanonicalSolution, _format_number() (+26 more)

### Community 81 - "pull_request_template.md"
Cohesion: 0.50
Nodes (3): Risk, Verification, What changed

### Community 82 - "test_ocr_computer_science.py"
Cohesion: 0.09
Nodes (37): generate_package(), Path, _analysis_prompt(), build_paper(), _levels(), _programming_prompt(), _programming_scheme(), Random (+29 more)

### Community 83 - "required"
Cohesion: 0.09
Nodes (22): advertised, app_board, app_subject, backend_subject, blueprint_version, board, board_profile, content_mode (+14 more)

### Community 84 - "backend-protocol.schema.json"
Cohesion: 0.15
Nodes (12): event_id, job_id, protocol, timestamp, type, additionalProperties, allOf, $id (+4 more)

### Community 85 - "properties"
Cohesion: 0.11
Nodes (19): type, pattern, type, minLength, type, minLength, type, minLength (+11 more)

### Community 87 - "generator_working_directory"
Cohesion: 0.40
Nodes (4): generator_working_directory(), MonkeyPatch, fixture, FixtureRequest

### Community 88 - "xcbuild.sh"
Cohesion: 0.67
Nodes (3): HOME, xcbuild.sh script, usage()

### Community 89 - "psychometrics.py"
Cohesion: 0.09
Nodes (51): CalibrationMetadata, CalibrationStore, ConsentRecord, _normalise_row(), Any, Path, Encrypted local storage for row-level calibration evidence. Keys are…, _read_rows() (+43 more)

### Community 90 - "capabilities"
Cohesion: 0.50
Nodes (4): items, type, type, capabilities

### Community 91 - "cspapergen/generator.py"
Cohesion: 0.10
Nodes (32): numeric_tokens(), Extract quantities exactly enough to catch broken data/source rewrites., assert_materially_new(), _align_paper1_structure(), _build_paper1_context(), _build_paper1_questions(), _paper1_part(), _paper1_question() (+24 more)

### Community 92 - "BackendClient"
Cohesion: 0.18
Nodes (14): BackendClient, BackendClientError, backendMissing, .errorDescription, pythonMissing, pythonVenvUnreadable, BackendFile, LaunchConfiguration (+6 more)

### Community 97 - "String"
Cohesion: 0.09
Nodes (39): Decodable, BackendEventPayload, BenchmarkMetric, .displayValue, BenchmarkVerdict, BoardStatus, placeholder, ready (+31 more)

### Community 99 - "properties"
Cohesion: 0.13
Nodes (15): type, properties, type, type, type, type, type, type (+7 more)

### Community 101 - "build_backend.sh"
Cohesion: 0.29
Nodes (5): MPLCONFIGDIR, PYINSTALLER_CONFIG_DIR, PYTHONPATH, build_backend.sh script, XDG_CACHE_HOME

### Community 106 - "cspapergen/cli.py"
Cohesion: 0.12
Nodes (29): ArtifactSpec, BuildResult, FamilyAdapter, Path, run_family_adapter(), default_ollama_model(), model_recommendations(), OllamaModelRecommendations (+21 more)

### Community 115 - "required"
Cohesion: 0.17
Nodes (13): differential_item_functioning, discrimination, facility, item_id, median_time_seconds, responses, items, items (+5 more)

### Community 116 - "type"
Cohesion: 0.50
Nodes (4): null, string, stage, type

### Community 117 - "progress"
Cohesion: 0.50
Nodes (4): maximum, minimum, type, progress

### Community 120 - "aqa_business_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 130 - "required"
Cohesion: 0.18
Nodes (11): candidate_sample, facility_range, group_fairness_screen, independent_manual_review, internal_consistency, item_coverage, marker_standardisation, additionalProperties (+3 more)

### Community 152 - "test_source_booklet.py"
Cohesion: 0.49
Nodes (9): _pdf_page_count(), _pdf_text(), Path, test_paper_2_source_cover_uses_generation_date_and_official_session(), test_source_booklet_extracts_have_reference_style_line_numbers(), test_source_booklet_for_paper_1_only_uses_section_b(), test_source_booklet_for_paper_3_uses_both_sections(), test_source_booklet_has_figure_extracts_and_source_attributions() (+1 more)

### Community 153 - "aqaaccountgen/generator.py"
Cohesion: 0.29
Nodes (9): _extract(), _levels(), _management_calculation(), _mcq(), _number(), Random, Topic, Build a complete, internally solved data contract for each numeric task. (+1 more)

### Community 154 - "DocumentPreviewView"
Cohesion: 0.06
Nodes (32): AppKit, Combine, DocumentPreviewView, .body, .exportAlertBinding, .provenanceRecord, .selectedBinding, .selectedFile (+24 more)

### Community 155 - "test_ai_assessment.py"
Cohesion: 0.09
Nodes (59): _batches_for_client(), _candidate_question(), _canonical_objective_allocation(), _clean_generated_prompt(), _contains_command_word(), _effective_batch_size(), _generate_batch(), GenerationPolicy (+51 more)

### Community 156 - "AIProvider"
Cohesion: 0.08
Nodes (24): CaseIterable, AIProvider, anthropic, apple, .backendID, .id, ollama, openAI (+16 more)

### Community 157 - "_draw_cover"
Cohesion: 0.18
Nodes (16): economics_exam_schedule(), ExamSchedule, formatted_economics_exam_date(), date, _draw_boxes(), _draw_cover(), _draw_fake_barcode(), _draw_front_section() (+8 more)

### Community 158 - "properties"
Cohesion: 0.11
Nodes (18): type, format, type, type, minLength, type, minLength, type (+10 more)

### Community 159 - "_call_name"
Cohesion: 0.38
Nodes (6): Call, _call_name(), parametrize, Path, test_production_pdf_renderers_run_inside_atomic_transactions(), test_shared_family_adapter_owns_atomic_pdf_transaction()

### Community 160 - "Q: How does the paper fidelity audit produce per-document and per-role scores, and where should release thresholds integrate?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: How does the paper fidelity audit produce per-document and per-role scores, and where should release thresholds integrate?, Source Nodes

### Community 161 - "required"
Cohesion: 0.18
Nodes (11): collected_at, collector_role, consent_basis, dataset_id, row_level_data, source, specification_version, provenance (+3 more)

### Community 162 - ".initialEstimate"
Cohesion: 0.21
Nodes (11): EstimateFactor, GenerationEstimate, .etaDate, .remainingText, TimeInterval, GenerationEstimator, Bool, Date (+3 more)

### Community 163 - "qualification_levels"
Cohesion: 0.14
Nodes (14): empirically_calibrated, engineering_validated, visually_calibrated, type, type, empirically_calibrated, engineering_validated, qualification_levels (+6 more)

### Community 165 - "CodingKeys"
Cohesion: 0.07
Nodes (36): CodingKeys, appContextWindow, contextWindow, defaultModel, detail, downloadSizeGB, id, maximumMemoryGB (+28 more)

### Community 166 - "required"
Cohesion: 0.18
Nodes (11): difficulty_independently_verified, evidence_fingerprint, family, form_id, paper, provenance, sample, thresholds (+3 more)

### Community 167 - "properties"
Cohesion: 0.12
Nodes (16): minLength, type, minLength, type, minLength, type, blueprint, contract (+8 more)

### Community 168 - "properties"
Cohesion: 0.22
Nodes (9): minimum, type, type, candidates, groups, response_rows, minimum, type (+1 more)

### Community 169 - "required"
Cohesion: 0.15
Nodes (13): artifacts, created_at, evidence, gate_results, generator_id, model, paper_id, reviewer_identity_class (+5 more)

### Community 170 - "generate_package"
Cohesion: 0.25
Nodes (8): type, path, default_output_dir(), generate_package(), main(), Path, test_generate_package_reports_rendering_progress(), test_generate_package_without_seed_does_not_write_audit()

### Community 171 - "sample"
Cohesion: 0.25
Nodes (8): candidates, groups, items, response_rows, sample, additionalProperties, required, type

### Community 172 - "empirical-calibration.schema.json"
Cohesion: 0.25
Nodes (7): additionalProperties, $id, not, anyOf, $schema, title, type

### Community 173 - "Canvas"
Cohesion: 0.12
Nodes (39): _answer_line_count(), _axis_labels_for_draw_prompt(), _draw_answer_lines(), _draw_answer_lines_until(), _draw_axis_arrow(), _draw_blank_answer_axes(), _draw_calculate_part_with_working_lines(), _draw_centred_instruction_line() (+31 more)

### Community 174 - "exam_blueprints.py"
Cohesion: 0.13
Nodes (33): _demand_band(), _hydrate_assessment_metadata(), _objective_allocation(), PaperRule, _prompt_uses_command_word(), BaseModel, QuestionRule, SectionRule (+25 more)

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

### Community 181 - "ocr_computer_science_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_difficulty_remains_external_evidence_gated(), test_multi_seed_structural_demand_passes(), test_reference_evidence_is_aggregate_only(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 182 - "additionalProperties"
Cohesion: 0.13
Nodes (15): items, minItems, type, uniqueItems, items, minItems, type, uniqueItems (+7 more)

### Community 183 - "generator-capability.schema.json"
Cohesion: 0.17
Nodes (11): additionalProperties, $defs, safePath, $id, pattern, minLength, not, type (+3 more)

### Community 184 - "CodingKeys"
Cohesion: 0.18
Nodes (11): CodingKey, CodingKeys, artifacts, configuration, createdAt, id, provenance, qualification (+3 more)

### Community 185 - "tool_versions"
Cohesion: 0.50
Nodes (4): type, tool_versions, additionalProperties, type

### Community 186 - "subject_plugin"
Cohesion: 0.67
Nodes (3): subject_plugin, pattern, type

### Community 187 - "BenchmarkChart"
Cohesion: 0.10
Nodes (29): Charts, KeyPath, PanelEmptyState, .body, String, BenchmarkChart, .body, BenchmarkLiveCharts (+21 more)

### Community 188 - "test_aqa_accounting.py"
Cohesion: 0.20
Nodes (21): generate_package(), Path, build_paper(), Syllabus, page_count(), Path, test_both_packages_render_36_page_question_papers(), test_contribution_question_uses_a_complete_costing_identity() (+13 more)

### Community 189 - "enum"
Cohesion: 0.22
Nodes (9): anthropic, apple, ollama, openai, enum, supported_providers, items, type (+1 more)

### Community 190 - "required"
Cohesion: 0.22
Nodes (9): detail, id, qualification, title, required, checks, items, type (+1 more)

### Community 191 - "backend_subject"
Cohesion: 0.67
Nodes (3): pattern, type, backend_subject

### Community 192 - "app_board"
Cohesion: 0.67
Nodes (3): minLength, type, app_board

### Community 193 - "app_subject"
Cohesion: 0.67
Nodes (3): minLength, type, app_subject

### Community 194 - "board"
Cohesion: 0.67
Nodes (3): pattern, type, board

### Community 195 - "JobHistoryView"
Cohesion: 0.25
Nodes (9): GenerationJobState, .systemImage, .title, JobHistoryView, .body, .selectedRecord, GenerationJobRecord, Set (+1 more)

### Community 196 - "ModelCoordinator"
Cohesion: 0.17
Nodes (12): OllamaState, AppClock, ModelCoordinator, .isModelListStale, .modelOptions, .recommendation, Bool, Date (+4 more)

### Community 197 - "entry_point"
Cohesion: 0.67
Nodes (3): pattern, type, entry_point

### Community 198 - "BenchmarkCoordinator"
Cohesion: 0.17
Nodes (11): BenchmarkSample, .networkLatencyDisplayMS, .thermalSpeedLimitDisplayPercent, BenchmarkCoordinator, Bool, Double, Error, Int32 (+3 more)

### Community 199 - "test_repository_hygiene.py"
Cohesion: 0.35
Nodes (9): test_every_tracked_file_has_a_durable_classification(), test_generated_and_binary_outputs_are_rejected(), test_maintained_visual_assets_are_classified_without_allowing_arbitrary_pngs(), test_root_lint_configuration_is_release_configuration(), Classification, classify_path(), inspect_repository(), main() (+1 more)

### Community 200 - "cspapergen/notes.py"
Cohesion: 0.38
Nodes (9): cache_notes(), discover_note_pdfs(), _extract_text(), note_context_for_topic(), NotesManifest, Path, _topic_prefixes(), test_cache_notes_extracts_text_into_project_cache() (+1 more)

### Community 201 - "id"
Cohesion: 0.67
Nodes (3): pattern, type, id

### Community 202 - "board_profile"
Cohesion: 0.67
Nodes (3): pattern, type, board_profile

### Community 203 - "SettingsPane.swift"
Cohesion: 0.15
Nodes (14): PrivacySettingsTab, .body, SettingsPane, .body, SettingsPaneID, ai, output, privacy (+6 more)

### Community 204 - "PaperBlueprint"
Cohesion: 0.14
Nodes (28): _count_pages(), _draw_answer_page_header(), _draw_continuation_lines(), _draw_crop_marks(), _draw_formula_appendix(), _draw_paper_3_pages(), _draw_question_footer(), _draw_question_pages() (+20 more)

### Community 206 - "aqaaccountgen/syllabus.py"
Cohesion: 0.28
Nodes (6): load_syllabus(), BaseModel, field_validator, Path, Syllabus, Topic

### Community 207 - "Rect"
Cohesion: 0.28
Nodes (6): Rect, _overlapping_text_pairs(), Path, Fail closed on malformed, substituted, annotated, or low-resolution PDFs., _text_occupancy(), validate_pdf_for_release()

### Community 208 - ".baseQuery"
Cohesion: 0.39
Nodes (4): SecretStore, Any, String, Security

### Community 211 - "SalesLedgerCase"
Cohesion: 0.17
Nodes (3): CostingCase, Single source of truth for the Paper 1 sales-ledger case. The question paper,…, SalesLedgerCase

### Community 212 - "enum"
Cohesion: 0.50
Nodes (4): ai-assisted, deterministic, enum, content_mode

## Knowledge Gaps
- **706 isolated node(s):** `BoardLayout`, `examforge-aqa-accounting`, `$schema`, `$id`, `title` (+701 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **52 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Work-memory lessons

**Preferred sources** — corroborated by past sessions; start here.
- `AppViewModel` (2× useful, score=1.166012741) _(code changed — re-verify)_
- `generation.py` (2× useful, score=1.164559792) _(code changed — re-verify)_
- `exam_blueprints.py` (2× useful, score=1.127080899) _(code changed — re-verify)_
- `layout_master.py` (2× useful, score=1.127080899) _(code changed — re-verify)_
- `paper_fidelity_audit.py` (2× useful, score=1.127080899) _(code changed — re-verify)_

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `GeneratedQuestion` connect `GeneratedQuestion` to `Paragraph`, `GeneratedPaper`, `ai_assessment.py`, `GeneratedOption`, `AssessmentContract`, `aqabizgen/generator.py`, `ocrcsgen/render_pdf.py`, `exam_blueprints.py`, `aqaecongen/render_pdf.py`, `AssessmentCheckpointStore`, `test_ocr_computer_science.py`, `test_ocr_economics.py`, `mark_scheme_enrichment.py`, `aqaaccountgen/generator.py`, `test_ai_assessment.py`, `aqaecongen/generator.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `path` connect `generate_package` to `properties`, `cspapergen/cli.py`, `test_repository_hygiene.py`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Why does `Rect` connect `Rect` to `cspapergen/render_pdf.py`, `GeneratedQuestion`, `Paragraph`, `GeneratedPaper`, `CoverProfile`, `layout_master.py`, `paper_fidelity_audit.py`, `aqaecongen/render_pdf.py`, `pdf_validation.py`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `GeneratedQuestion` (e.g. with `AssessmentLLMClient` and `GenerationPolicy`) actually correct?**
  _`GeneratedQuestion` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `ApplicationCoordinator` (e.g. with `PaperCreator` and `.body`) actually correct?**
  _`ApplicationCoordinator` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `BoardLayout`, `examforge-aqa-accounting`, `$schema` to the rest of the system?**
  _706 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `cspapergen/render_pdf.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06288515406162465 - nodes in this community are weakly interconnected._