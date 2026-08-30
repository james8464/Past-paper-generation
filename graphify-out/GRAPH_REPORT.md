# Graph Report - Past Paper Creation  (2026-08-30)

## Corpus Check
- 339 files · ~548,455 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 5008 nodes · 13566 edges · 246 communities (190 shown, 56 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 769 edges (avg confidence: 0.66)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e357a2c7`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cspapergen/render_pdf.py
- reference_demand.py
- ApplicationCoordinator
- reconcile_solution
- Paragraph
- ocregen/render_pdf.py
- aqabizgen/render_pdf.py
- test_render_pdf.py
- aqabizgen/generator.py
- pastpapergen/generator.py
- build_paper_blueprint
- ocrcsgen/render_pdf.py
- paper_fidelity_audit.py
- reference_corpus.py
- GeneratedPaper
- test_coverage_matrix.py
- CodingKeys
- AssessmentCheckpointStore
- pdf_validation.py
- test_ocr_economics.py
- live_generation_matrix.py
- Text
- benchmark.py
- family_adapter.py
- mark_scheme_enrichment.py
- test_document_dsl.py
- AssessmentContract
- ModelCoordinator
- assessment_package.py
- ExamBoardOption
- Paper creator: deep project analysis
- Q: Which Ollama model and live validation path does the project use for all supported papers?
- graphs.py
- mathematics.py
- generation.py
- generate_package
- properties
- render_pdf_atomically
- test_mark_scheme_layout.py
- exam_blueprints.py
- Approved-Improvement Traceability
- test_app_backend.py
- pastpapergen/notes.py
- .generate
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
- test_ollama_generation.py
- emit
- generator_registry.py
- properties
- _mark_scheme_rows
- assessment_quality.py
- Q: How is the macOS backend bundle kept complete?
- File Structure
- BackendClient
- BenchmarkChart
- RecentDocumentStore
- aqa_accounting_calibration.py
- Rendering and Mark-Scheme Reliability Implementation Plan
- Architecture
- ExamPageProfile
- pastpapergen/ollama_client.py
- Glossy Black Fountain Pen App Icon Master
- generate_package
- enum
- Assessment quality and originality
- paths.py
- macOS interaction and HIG compliance
- Rect
- test_pdf_validation.py
- Q: how can we make even more improvements to get the highest similarity in terms of structure and layout and quality of questions etc. and maybe all of the files in the project can be better organised. and the UI can be made to be much better and more geometrically apple-like by strictly following every single rule they outline in their HIG
- Paper creator
- independent_solver.py
- pull_request_template.md
- test_ocr_computer_science.py
- required
- backend-protocol.schema.json
- properties
- .initialEstimate
- generator_working_directory
- xcbuild.sh
- psychometrics.py
- capabilities
- ocr_computer_science_calibration.py
- BackendEvent
- diagnose.sh
- move_to_trash.sh
- inspect_release_compliance
- run_app_macos.sh
- aqa_business_calibration.py
- Core/__init__.py
- properties
- bootstrap_backend.sh
- build_backend.sh
- clean.sh
- resolve_agent_name.sh
- CodingKeys
- aqaaccountgen/__init__.py
- test_science_subjects.py
- aqabizgen/__init__.py
- cspapergen/__init__.py
- ocrcsgen/__init__.py
- aqaecongen/__init__.py
- pastpapergen/__init__.py
- ocregen/__init__.py
- tools/__init__.py
- graphify
- required
- cspapergen/ollama_client.py
- progress
- properties
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
- required
- CandidateResponse
- DocumentPreviewView
- GeneratedQuestion
- PartnershipCase
- Canvas
- properties
- _call_name
- Q: How does the paper fidelity audit produce per-document and per-role scores, and where should release thresholds integrate?
- required
- NonCurrentAssetCase
- qualification_levels
- test_generator_migration.py
- validate_mark_scheme_item
- required
- properties
- pastpapergen/render_pdf.py
- required
- ComputerSciencePlugin
- sample
- aqaaccountgen/generator.py
- properties
- aqaecongen/generator.py
- required
- qualification-schema.json
- properties
- enum
- enum
- model
- board_profile
- additionalProperties
- generator-capability.schema.json
- render_source_booklet
- tool_versions
- generate_package
- String
- test_aqa_accounting.py
- enum
- required
- backend_subject
- app_board
- app_subject
- response_simulation.py
- cspapergen/generator.py
- subject_plugin
- SingleCellPanelFactory
- _BooleanParser
- test_repository_hygiene.py
- IncomeStatementCase
- required
- discover_subject_plugin
- formatted_generation_date
- _draw_ms_row
- Current-family visual qualification — 26 August 2026
- test_reference_demand.py
- JobHistoryView
- .baseQuery
- SubjectValidation
- pastpapergen/cli.py
- _draw_cover
- Reference-Demand Calibration Design
- SalesLedgerCase
- add_page_structure_tree
- Cambridge International engineering foundation — 26 August 2026
- README.md
- aqaaccountgen/syllabus.py
- subjects/__init__.py
- configuredgen/__init__.py
- paper-creator-configured-generators
- empirical-calibration.schema.json
- PhysicsPlugin
- properties
- reference-demand-profile.schema.json
- Reference-Demand Calibration Implementation Plan
- distribution
- validate_cross_paper_quality
- test_configured_family.py
- enum
- blueprint_version
- package
- cspapergen/cli.py
- register_fonts
- comparison_basis
- family_id
- CostingCase
- validate_economics_causal_direction
- source_fingerprint
- _draw_source_content_page
- GlyphMetric
- enum
- CoverProfile
- board
- id
- .validate_distribution

## God Nodes (most connected - your core abstractions)
1. `GeneratedQuestion` - 190 edges
2. `build_paper_blueprint()` - 167 edges
3. `load_builtin_paper_config()` - 151 edges
4. `load_syllabus()` - 150 edges
5. `ApplicationCoordinator` - 138 edges
6. `GeneratedOption` - 100 edges
7. `GeneratedPaper` - 88 edges
8. `Table` - 79 edges
9. `build_question()` - 60 edges
10. `_Task` - 57 edges

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

## Communities (246 total, 56 thin omitted)

### Community 0 - "cspapergen/render_pdf.py"
Cohesion: 0.10
Nodes (84): Question, _answer_line_count(), _answer_lines(), _answer_lines_paginated(), _candidate_fields(), _continuation_guidance_lines(), _cover_page(), _cover_section() (+76 more)

### Community 1 - "reference_demand.py"
Cohesion: 0.11
Nodes (37): audit_form_demand(), build_item_demand_target(), _collapse_command_distribution(), _command_family(), _distribution(), _distribution_distance(), _infer_demand(), ItemDemandTarget (+29 more)

### Community 2 - "ApplicationCoordinator"
Cohesion: 0.03
Nodes (56): AnyCancellable, App, Commands, DateFormatter, AppCommands, .body, PaperCreator, .body (+48 more)

### Community 3 - "reconcile_solution"
Cohesion: 0.22
Nodes (20): EvidenceRecord, CanonicalSolution, IndependentSolver, _numbers(), BaseModel, Solve an item in a context that deliberately excludes its draft scheme., reconcile_solution(), ReconciliationIssue (+12 more)

### Community 4 - "Paragraph"
Cohesion: 0.13
Nodes (59): Table, AQAAnswerLines, Paragraph, _accounting_marking_guidance_pages(), _accounting_system_case(), _additional_answer_page(), _appropriation_answer_table(), _assessment_objectives_page() (+51 more)

### Community 5 - "ocregen/render_pdf.py"
Cohesion: 0.08
Nodes (72): OCRAnswerLines, _add_economics_diagram(), _add_firm_objectives_diagram(), _add_ppf_diagram(), _annotation_conventions_page(), _answer_mark(), _assessment_allocation(), _assessment_grid_groups() (+64 more)

### Community 6 - "aqabizgen/render_pdf.py"
Cohesion: 0.13
Nodes (46): _artifacts(), _additional_answer_page(), _ao_summary(), _assessment_objectives_page(), _break_even_diagram(), _calculation_marking_page(), _chart(), _choice_prompts() (+38 more)

### Community 7 - "test_render_pdf.py"
Cohesion: 0.14
Nodes (45): render_question_paper(), _answer_rule_count(), _blank_axis_lines(), _blueprint_with_section_a_question(), _dark_pixels(), _first_page_containing(), _normalised(), _pdf_page_count() (+37 more)

### Community 8 - "aqabizgen/generator.py"
Cohesion: 0.09
Nodes (35): generate_package(), Path, FinancialPosition, format_number(), Format an exam answer without meaningless trailing zeroes., The single source of truth for Paper 1 financial-statement figures., build_paper(), _extract() (+27 more)

### Community 9 - "pastpapergen/generator.py"
Cohesion: 0.06
Nodes (72): MultipleChoiceOption, _adapt_paper_three_case_guidance(), _best_section_a_context_point(), _build_part(), _build_parts(), _choice_group_name(), _choice_lookup(), _choose_topic() (+64 more)

### Community 10 - "build_paper_blueprint"
Cohesion: 0.09
Nodes (77): build_paper_blueprint(), PaperBlueprint, Syllabus, load_builtin_paper_config(), load_syllabus(), Path, Syllabus, test_blueprint_contains_structured_mcq_and_mark_scheme_content() (+69 more)

### Community 11 - "ocrcsgen/render_pdf.py"
Cohesion: 0.09
Nodes (35): ExamPage, Flowable, A full-page shell that can also live inside a Platypus story., AnswerLineFlowable, AQACompactAnswerLines, OCRComputerScienceAnswerLines, Flowable, Return a Table subclass whose raw string cells use the controlled font.… (+27 more)

### Community 12 - "paper_fidelity_audit.py"
Cohesion: 0.05
Nodes (103): Pixmap, parametrize, Path, test_compact_profile_omits_raster_geometry(), test_contact_sheets_make_visual_review_artifacts(), test_generated_document_falls_back_to_nested_transaction_output(), test_generated_document_supports_app_per_paper_directories(), test_metric_callout_names_print_resolution_comparison_dimensions() (+95 more)

### Community 13 - "reference_corpus.py"
Cohesion: 0.13
Nodes (45): MonkeyPatch, Path, test_document_path_requires_filename(), test_document_path_stays_inside_corpus(), test_download_manifest_records_failure_and_continues(), test_parse_aqa_resources_filters_modified_papers(), test_parse_ocr_resources_uses_a_level_tab_only(), test_parse_ocr_specifications_keeps_a_level_not_as_level() (+37 more)

### Community 14 - "GeneratedPaper"
Cohesion: 0.15
Nodes (38): GeneratedPaper, _artifacts(), _assessment_objectives_table(), _context_data_table(), _context_first_page(), _context_second_page(), _cover(), _cover_profile() (+30 more)

### Community 15 - "test_coverage_matrix.py"
Cohesion: 0.07
Nodes (57): family(), matrix(), Path, test_catalog_availability_is_owned_only_by_registry(), test_checked_in_matrix_is_deterministic_and_current(), test_existing_generators_are_reported_without_false_verification(), test_matrix_exactly_covers_layout_profiles(), test_no_verified_paper_has_a_failed_gate() (+49 more)

### Community 16 - "CodingKeys"
Cohesion: 0.03
Nodes (59): CodingKey, CodingKeys, assessmentKind, backendVersion, capabilities, checks, code, command (+51 more)

### Community 17 - "AssessmentCheckpointStore"
Cohesion: 0.08
Nodes (53): AssessmentCheckpointStore, CheckpointCorrupt, CheckpointIdentity, CheckpointMismatch, identity_for_blueprint(), Any, BaseModel, Path (+45 more)

### Community 18 - "pdf_validation.py"
Cohesion: 0.12
Nodes (32): compare_page_evidence(), _contrast_against_white(), _contrast_ratio(), _count_score(), _font_embedding(), _font_evidence(), _is_decorative_bleed(), _is_margin_furniture() (+24 more)

### Community 19 - "test_ocr_economics.py"
Cohesion: 0.10
Nodes (39): generate_package(), Path, build_paper(), _evaluation_scheme(), _extract(), _extract_number(), _instructions(), _mcq() (+31 more)

### Community 20 - "live_generation_matrix.py"
Cohesion: 0.08
Nodes (49): Release qualification evidence and policy models., ArtifactEvidence, EvidenceRecord, GateState, ModelIdentity, BaseModel, field_validator, Path (+41 more)

### Community 21 - "Text"
Cohesion: 0.04
Nodes (98): Charts, Color, View, GeneratedFilesTable, PanelEmptyState, .body, String, BenchmarkVerdict (+90 more)

### Community 22 - "benchmark.py"
Cohesion: 0.12
Nodes (33): apple_cpu_core_split(), available_memory_gb(), avg(), clamp(), cpu_brand(), cpu_load_percent(), cpu_probe(), disk_probe() (+25 more)

### Community 23 - "family_adapter.py"
Cohesion: 0.12
Nodes (27): ArtifactSpec, FamilyAdapter, Path, run_family_adapter(), default_ollama_model(), model_recommendations(), OllamaModelRecommendations, OllamaModelTier (+19 more)

### Community 24 - "mark_scheme_enrichment.py"
Cohesion: 0.24
Nodes (19): _answer_form(), _application_label(), _clean_text(), _compact_technical_guidance(), _deduplicate(), enrich_paper(), _enrich_question(), _level_guidance() (+11 more)

### Community 25 - "test_document_dsl.py"
Cohesion: 0.05
Nodes (94): AnswerSpace, BaseComponent, BlankPage, Component, ContinuationPage, Cover, Diagram, Graph (+86 more)

### Community 26 - "AssessmentContract"
Cohesion: 0.13
Nodes (28): AssessmentContract, contract_for_question(), GeneratedNumericField, GraphContract, _numeric_contracts(), NumericRole, NumericValueContract, Any (+20 more)

### Community 27 - "ModelCoordinator"
Cohesion: 0.05
Nodes (34): AppKit, Foundation, OllamaState, EstimateTuning, AppClock, KeychainSecretStore, SecretStoring, Date (+26 more)

### Community 28 - "assessment_package.py"
Cohesion: 0.21
Nodes (25): _assessment_contract(), AssessmentPackageCompatibilityError, _contains_non_finite(), _evidence_ids(), _extract_items(), _form_id(), _level_policies(), load_assessment_package() (+17 more)

### Community 29 - "ExamBoardOption"
Cohesion: 0.06
Nodes (48): Hashable, Identifiable, AssessmentKind, fullPaper, questionBank, .title, CatalogSubject, ExamBoardOption (+40 more)

### Community 30 - "Paper creator: deep project analysis"
Cohesion: 0.05
Nodes (42): Implementation and fidelity report, Full-matrix validation, Highest-value next engineering work, Implemented changes, Manual PDF review, Outcome, What code cannot honestly prove, 10. Completion and file handling (+34 more)

### Community 31 - "Q: Which Ollama model and live validation path does the project use for all supported papers?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Which Ollama model and live validation path does the project use for all supported papers?, Source Nodes

### Community 32 - "graphs.py"
Cohesion: 0.30
Nodes (26): Axes, ad_as_diagram(), _arrow_axes(), _ax(), circular_flow_diagram(), consumer_producer_surplus(), demand_supply_diagram(), _ensure_style() (+18 more)

### Community 33 - "mathematics.py"
Cohesion: 0.16
Nodes (20): AnswerComparison, compare_mathematical_answers(), MarkAward, _marking_rules(), MarkingRule, MathematicalAnswer, MathematicsPlugin, _normalise_unit() (+12 more)

### Community 34 - "generation.py"
Cohesion: 0.21
Nodes (21): progress_emitter(), _atomic_publish(), _cancel_generation(), checkpoint_path_for_job(), emit_generated_files(), finalize_generated_documents(), GenerationCancelled, _generator_version() (+13 more)

### Community 35 - "generate_package"
Cohesion: 0.14
Nodes (23): extract_pdf_text(), Path, Extract stable reading-order text without a Poppler CLI dependency., generate_package(), _logic_gate_names(), test_final_additional_answer_page_reserves_independent_notice(), test_generate_package_writes_data_structures_question_bank(), test_generate_package_writes_rendered_and_assessment_outputs() (+15 more)

### Community 36 - "properties"
Cohesion: 0.09
Nodes (22): type, pattern, type, const, properties, advertised, entry_point, manifest_version (+14 more)

### Community 37 - "render_pdf_atomically"
Cohesion: 0.15
Nodes (23): InvalidRenderOutput, Path, RuntimeError, A document role could not be rendered safely., Rendering exceeded its bounded qualification window., A renderer returned without producing a readable PDF., Render one PDF role under a deadline and promote it atomically., _readable_page_count() (+15 more)

### Community 38 - "test_mark_scheme_layout.py"
Cohesion: 0.19
Nodes (29): pdf_font_names(), Return the font families actually used by visible text spans., _cleanup_graph_cache(), render_mark_scheme(), _blueprint_with_section_a_calculation(), _blueprint_with_section_b_topic(), _pdf_page_count(), _pdf_text() (+21 more)

### Community 39 - "exam_blueprints.py"
Cohesion: 0.26
Nodes (20): _demand_band(), _hydrate_assessment_metadata(), _objective_allocation(), _prompt_uses_command_word(), _structured_scheme(), validate_generated_paper(), validate_rule(), paper() (+12 more)

### Community 40 - "Approved-Improvement Traceability"
Cohesion: 0.07
Nodes (26): Approved-Improvement Traceability, Current-Paper Gate, Expansion Gate, Foundation Gate, Global Constraints, Paper Creator Excellence Programme Implementation Plan, Phase Completion Gates, Plan Verification Checklist (+18 more)

### Community 41 - "test_app_backend.py"
Cohesion: 0.16
Nodes (28): _safe_provider_detail(), CaptureFixture, CompletedProcess, Path, run_bridge(), run_bridge_raw(), test_aqa_accounting_all_papers_generate_expected_files(), test_aqa_business_all_papers_generate_expected_files() (+20 more)

### Community 42 - "pastpapergen/notes.py"
Cohesion: 0.11
Nodes (35): difficulty_review(), DifficultyReviewResult, independent_review(), JSONClient, Any, BaseModel, Protocol, require_difficulty_review() (+27 more)

### Community 43 - ".generate"
Cohesion: 0.07
Nodes (24): AppDefaults, AppLinks, AppStorageKey, SecretAccount, Bool, String, URL, MLXRecoveryState (+16 more)

### Community 44 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Measured Paper Fidelity Implementation Plan, Task 1: Page-role-aware fidelity evidence, Task 2: Shared board answer-page geometry, Task 3: OCR response and blank-page grammar, Task 4: Shared mark-scheme cover calibration, Task 5: Full visual qualification and regression gate

### Community 45 - "load_syllabus"
Cohesion: 0.08
Nodes (60): build_paper1_blueprint(), build_paper2_blueprint(), build_topic_question_bank(), PaperBlueprint, Syllabus, improve_questions_with_ollama(), load_syllabus(), Path (+52 more)

### Community 46 - "test_mlx_setup.py"
Cohesion: 0.09
Nodes (38): _available_cache_bytes(), ensure_mlx_ready(), install_mlx_runtime(), is_managed_development_environment(), load_mlx_model(), MLXModelSetupRequired, MLXSetupCancelled, MLXSetupError (+30 more)

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
Cohesion: 0.19
Nodes (63): MarkingGuidance, MultipleChoiceOption, BaseModel, QuestionPart, Stimulus, SyllabusTopic, _assembly_program_question(), _assembly_trace_question() (+55 more)

### Community 51 - "providers.py"
Cohesion: 0.09
Nodes (36): _hosted_client(), _aqa_cs_part_count(), _edexcel_part_count(), hosted_client(), HostedLLMClient, _normalise_base_url(), _ollama_json_schema(), _ollama_output_budget() (+28 more)

### Community 52 - "Q: Where should performance and generated-paper accuracy fixes be made?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Where should performance and generated-paper accuracy fixes be made?, Source Nodes

### Community 53 - "Contract-First Paper Generation and Release Qualification"
Cohesion: 0.06
Nodes (31): 1. Assessment Contract, 2. Deterministic Assessment Data, 3. Item-Level AI Workflow, 4. Evidence Binding and Factual Quality, 5. Mark-Scheme Quality, 6. Board Layout Adapters, 7. Bounded Rendering, 8. Progress, Cancellation, and Resume (+23 more)

### Community 54 - "test_ollama_generation.py"
Cohesion: 0.10
Nodes (35): generate_questions_with_ollama(), _merge_source_text(), OllamaClient, PaperBlueprint, Syllabus, Run an independent demand-only gate over every rendered question item., review_blueprint_difficulty(), _validate_ai_question() (+27 more)

### Community 55 - "emit"
Cohesion: 0.21
Nodes (21): build_parser(), handle_bundle_check(), main(), ArgumentParser, Namespace, Fail fast when a packaged backend is missing a dynamic generator., emit(), emit_progress() (+13 more)

### Community 56 - "generator_registry.py"
Cohesion: 0.24
Nodes (15): _capability(), generator_capabilities(), generator_subjects(), _paper_qualification(), PaperQualification, Any, _relative_path(), test_backend_bundle_script_is_registry_driven() (+7 more)

### Community 57 - "properties"
Cohesion: 0.08
Nodes (24): type, type, minimum, type, type, null, string, type (+16 more)

### Community 58 - "_mark_scheme_rows"
Cohesion: 0.16
Nodes (25): _brief_source_evidence(), _calculation_answer_lines(), _mark_scheme_rows(), _normalise_mark_point(), _one_mark_points(), _paper_one_fifteen_mark_scheme_lines(), _paper_one_five_mark_diagram_lines(), _paper_one_section_a_mark_scheme_lines() (+17 more)

### Community 59 - "assessment_quality.py"
Cohesion: 0.14
Nodes (18): _ignored_candidate_quantities(), _is_subsequence(), _items(), _load_package(), normalise_item_text(), _normalise_quantity(), _precision_digit_tokens(), _precision_instructions() (+10 more)

### Community 60 - "Q: How is the macOS backend bundle kept complete?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: How is the macOS backend bundle kept complete?, Source Nodes

### Community 61 - "File Structure"
Cohesion: 0.17
Nodes (11): Assessment Reliability Core Implementation Plan, File Structure, Global Constraints, Subsequent Phase Plans, Task 1: Typed Item Contracts, Task 2: Role-Aware Numeric and Evidence Validation, Task 3: Item-Scoped Draft, Review, and Repair, Task 4: Atomic Checkpoints and Resume (+3 more)

### Community 62 - "BackendClient"
Cohesion: 0.08
Nodes (27): BenchmarkMetric, .displayValue, BenchmarkSample, .networkLatencyDisplayMS, .thermalSpeedLimitDisplayPercent, BackendClient, BackendClientError, backendMissing (+19 more)

### Community 63 - "BenchmarkChart"
Cohesion: 0.12
Nodes (18): KeyPath, value, BenchmarkChart, .accessibilitySummary, BenchmarkLiveCharts, .body, .cpuChart, .cpuThroughputChart (+10 more)

### Community 64 - "RecentDocumentStore"
Cohesion: 0.06
Nodes (37): Codable, Equatable, FileManager, GenerationJobState, LocalizedError, GenerationConfiguration, GenerationJobRecord, .missingArtifactCount (+29 more)

### Community 65 - "aqa_accounting_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_both_papers_pass_multi_seed_automated_checks(), test_external_difficulty_gates_remain_false(), test_reference_evidence_is_aggregate_only(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 66 - "Rendering and Mark-Scheme Reliability Implementation Plan"
Cohesion: 0.25
Nodes (7): Rendering and Mark-Scheme Reliability Implementation Plan, Task 1: Bounded atomic render transactions, Task 2: Route every generator family through the transaction, Task 3: Artifact containment, collision, and density evidence, Task 4: Mark-scheme depth contracts, Task 5: OCR Economics pagination regression, Task 6: Phase qualification

### Community 67 - "Architecture"
Cohesion: 0.18
Nodes (10): Architecture, Canonical registry, Extension contract, Failure containment, Fidelity qualification boundary, Package transaction, PDF portability and accessibility, Product boundary (+2 more)

### Community 68 - "ExamPageProfile"
Cohesion: 0.20
Nodes (26): _draw_aqa_footer(), _draw_aqa_page(), _draw_barcode(), draw_exam_page(), _draw_independent_notice(), _draw_ocr_notice(), _draw_ocr_page(), _draw_ocr_rules() (+18 more)

### Community 69 - "pastpapergen/ollama_client.py"
Cohesion: 0.11
Nodes (35): MultipleChoiceOption, PaperBlueprint, PaperConfig, BaseModel, QuestionBlueprint, QuestionPart, SectionConfig, Syllabus (+27 more)

### Community 70 - "Glossy Black Fountain Pen App Icon Master"
Cohesion: 0.18
Nodes (11): Glossy Black Fountain Pen App Icon Master, Paper Creator App Icon AppIcon-128x128@1x, Paper Creator App Icon AppIcon-128x128@2x, Paper Creator App Icon AppIcon-16x16@1x, Paper Creator App Icon AppIcon-16x16@2x, Paper Creator App Icon AppIcon-256x256@1x, Paper Creator App Icon AppIcon-256x256@2x, Paper Creator App Icon AppIcon-32x32@1x (+3 more)

### Community 71 - "generate_package"
Cohesion: 0.25
Nodes (8): type, path, default_output_dir(), generate_package(), main(), Path, test_generate_package_reports_rendering_progress(), test_generate_package_without_seed_does_not_write_audit()

### Community 72 - "enum"
Cohesion: 0.18
Nodes (11): benchmark_done, benchmark_metric, benchmark_sample, done, error, file, hello, models (+3 more)

### Community 73 - "Assessment quality and originality"
Cohesion: 0.14
Nodes (13): AQA Computer Science examiner-feedback contract, Assessment quality and originality, Difficulty claims, Human release review, Independent solution and response-band qualification, Item transactions and two-pass generation, Mark-scheme quality, Measured visual qualification (+5 more)

### Community 74 - "paths.py"
Cohesion: 0.18
Nodes (13): board_profile(), BoardProfile, _normalise_identifier(), build_parser(), _layout_board(), main(), MigrationIssue, MigrationReport (+5 more)

### Community 75 - "macOS interaction and HIG compliance"
Cohesion: 0.22
Nodes (8): Accessibility verification, Commands and state, File workflow, Geometry and visual language, Information architecture, macOS interaction and HIG compliance, Onboarding and help, Settings

### Community 76 - "Rect"
Cohesion: 0.05
Nodes (76): conform_generated_documents(), Path, _clamp_fitz_rect(), conform_pdf_page_boxes(), conform_pdf_to_box_template(), draw_text_slot(), _fitz_rect_close(), LayoutConformanceError (+68 more)

### Community 77 - "test_pdf_validation.py"
Cohesion: 0.23
Nodes (22): extract_pdf_evidence(), _overlapping_text_pairs(), Path, Fail closed on malformed, substituted, annotated, or low-resolution PDFs., Extract print and accessibility evidence without retaining source prose. Glyph…, _text_occupancy(), validate_pdf_for_release(), Canvas (+14 more)

### Community 78 - "Q: how can we make even more improvements to get the highest similarity in terms of structure and layout and quality of questions etc. and maybe all of the files in the project can be better organised. and the UI can be made to be much better and more geometrically apple-like by strictly following every single rule they outline in their HIG"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: how can we make even more improvements to get the highest similarity in terms of structure and layout and quality of questions etc. and maybe all of the files in the project can be better organised. and the UI can be made to be much better and more geometrically apple-like by strictly following every single rule they outline in their HIG, Source Nodes

### Community 79 - "Paper creator"
Cohesion: 0.25
Nodes (8): Architecture and quality analysis, Build Checks, CLI, Development Reference Corpus, Paper creator, Privacy, Run, Structure

### Community 80 - "independent_solver.py"
Cohesion: 0.18
Nodes (17): content_similarity(), Weighted token-shingle Jaccard similarity in the closed interval 0...1., _as_mapping(), _concept_coverage(), _concept_tokens(), _format_number(), _normalise(), _normalise_choice_answer() (+9 more)

### Community 81 - "pull_request_template.md"
Cohesion: 0.50
Nodes (3): Risk, Verification, What changed

### Community 82 - "test_ocr_computer_science.py"
Cohesion: 0.09
Nodes (39): generate_package(), Path, _analysis_prompt(), build_paper(), _levels(), _programming_prompt(), _programming_scheme(), Random (+31 more)

### Community 83 - "required"
Cohesion: 0.09
Nodes (22): advertised, app_board, app_subject, backend_subject, blueprint_version, board, board_profile, content_mode (+14 more)

### Community 84 - "backend-protocol.schema.json"
Cohesion: 0.15
Nodes (12): event_id, job_id, protocol, timestamp, type, additionalProperties, allOf, $id (+4 more)

### Community 85 - "properties"
Cohesion: 0.12
Nodes (17): type, pattern, type, minLength, type, minLength, type, minLength (+9 more)

### Community 86 - ".initialEstimate"
Cohesion: 0.18
Nodes (12): EstimateFactor, GenerationEstimate, .etaDate, .remainingText, Double, TimeInterval, GenerationEstimator, Bool (+4 more)

### Community 87 - "generator_working_directory"
Cohesion: 0.40
Nodes (4): generator_working_directory(), MonkeyPatch, fixture, FixtureRequest

### Community 88 - "xcbuild.sh"
Cohesion: 0.67
Nodes (3): HOME, xcbuild.sh script, usage()

### Community 89 - "psychometrics.py"
Cohesion: 0.08
Nodes (56): CalibrationMetadata, CalibrationStore, ConsentRecord, _normalise_row(), Any, Path, Encrypted local storage for row-level calibration evidence. Keys are…, _read_rows() (+48 more)

### Community 90 - "capabilities"
Cohesion: 0.50
Nodes (4): items, type, type, capabilities

### Community 91 - "ocr_computer_science_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_difficulty_remains_external_evidence_gated(), test_multi_seed_structural_demand_passes(), test_reference_evidence_is_aggregate_only(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 92 - "BackendEvent"
Cohesion: 0.06
Nodes (25): BackendEvent, benchmarkDone, benchmarkMetric, benchmarkSample, done, error, file, hello (+17 more)

### Community 95 - "inspect_release_compliance"
Cohesion: 0.27
Nodes (14): Path, test_release_compliance_detects_a_tracked_secret_signature(), test_release_compliance_passes_for_the_repository(), test_release_compliance_rejects_unbounded_runtime_dependencies(), _check_dependencies(), _check_entitlements(), _check_font_licences(), _check_privacy_manifest() (+6 more)

### Community 97 - "aqa_business_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 99 - "properties"
Cohesion: 0.12
Nodes (17): type, properties, type, type, type, type, type, type (+9 more)

### Community 101 - "build_backend.sh"
Cohesion: 0.29
Nodes (5): MPLCONFIGDIR, PYINSTALLER_CONFIG_DIR, PYTHONPATH, build_backend.sh script, XDG_CACHE_HOME

### Community 104 - "CodingKeys"
Cohesion: 0.07
Nodes (36): CodingKeys, appContextWindow, contextWindow, defaultModel, detail, downloadSizeGB, id, maximumMemoryGB (+28 more)

### Community 106 - "test_science_subjects.py"
Cohesion: 0.13
Nodes (19): ChemistryPlugin, equation_is_balanced(), _equation_side(), Formula, _multiplier(), _parse_group(), Any, Counter (+11 more)

### Community 115 - "required"
Cohesion: 0.10
Nodes (22): differential_item_functioning, discrimination, facility, item_id, median_time_seconds, responses, minimum, type (+14 more)

### Community 116 - "cspapergen/ollama_client.py"
Cohesion: 0.10
Nodes (27): numeric_tokens(), Extract quantities exactly enough to catch broken data/source rewrites., assert_materially_new(), profile_for(), PaperBlueprint, Syllabus, _clean(), JSONGenerationClient (+19 more)

### Community 117 - "progress"
Cohesion: 0.50
Nodes (4): maximum, minimum, type, progress

### Community 120 - "properties"
Cohesion: 0.09
Nodes (23): approval_evidence, approved, approved_by_identity_class, draft, policy_id, retired, status, type (+15 more)

### Community 130 - "required"
Cohesion: 0.17
Nodes (12): candidate_sample, facility_range, group_fairness_screen, independent_manual_review, internal_consistency, item_coverage, marker_standardisation, policy_approved (+4 more)

### Community 152 - "required"
Cohesion: 0.13
Nodes (15): maximum_acceptable_facility, maximum_dif_gap, minimum_acceptable_facility, minimum_candidates, minimum_discrimination, minimum_double_marked_pairs, minimum_facility_coverage, minimum_group_responses (+7 more)

### Community 153 - "CandidateResponse"
Cohesion: 0.25
Nodes (14): BoardLevelPolicy, LevelDescriptor, LevelOfResponseEngine, load_level_policies(), MarkAnnotation, MarkDecision, BaseModel, model_validator (+6 more)

### Community 154 - "DocumentPreviewView"
Cohesion: 0.05
Nodes (35): Combine, DocumentPreviewView, .body, .exportAlertBinding, .provenanceRecord, .selectedBinding, .selectedFile, PDFDocumentView (+27 more)

### Community 155 - "GeneratedQuestion"
Cohesion: 0.07
Nodes (102): AssessmentLLMClient, _batches_for_client(), _bounded_text(), _candidate_question(), _canonical_objective_allocation(), _clean_generated_prompt(), _contains_command_word(), _demand_item() (+94 more)

### Community 157 - "Canvas"
Cohesion: 0.11
Nodes (45): _answer_line_count(), _count_pages(), _draw_answer_lines_until(), _draw_answer_page_header(), _draw_centred_instruction_line(), _draw_continuation_lines(), _draw_do_not_write_rail(), _draw_dotted_answer_rule() (+37 more)

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

### Community 162 - "NonCurrentAssetCase"
Cohesion: 0.15
Nodes (3): _nearest_hundred(), NonCurrentAssetCase, test_non_current_asset_question_and_mark_scheme_use_the_same_figures()

### Community 163 - "qualification_levels"
Cohesion: 0.14
Nodes (14): empirically_calibrated, engineering_validated, visually_calibrated, type, type, empirically_calibrated, engineering_validated, qualification_levels (+6 more)

### Community 164 - "test_generator_migration.py"
Cohesion: 0.23
Nodes (13): Path, test_all_current_families_pass_declarative_migration_validation(), test_broken_fixture_reports_every_onboarding_surface(), test_scaffold_emits_complete_unadvertised_family_and_refuses_overwrite(), build_parser(), _cli_template(), main(), ArgumentParser (+5 more)

### Community 165 - "validate_mark_scheme_item"
Cohesion: 0.27
Nodes (16): _contains_any(), MarkSchemeQuality, _normalise(), Any, validate_mark_scheme_item(), _item(), test_accounting_follow_through_metadata_counts_as_method_guidance(), test_calculation_requires_method_or_working() (+8 more)

### Community 166 - "required"
Cohesion: 0.17
Nodes (12): difficulty_independently_verified, evidence_fingerprint, family, form_id, paper, policy, provenance, sample (+4 more)

### Community 167 - "properties"
Cohesion: 0.12
Nodes (16): minLength, type, minLength, type, minLength, type, blueprint, contract (+8 more)

### Community 168 - "pastpapergen/render_pdf.py"
Cohesion: 0.10
Nodes (37): BoardLayout, GraphParams, _axis_labels_for_draw_prompt(), _bar_chart_data(), _bar_label(), _draw_answer_lines(), _draw_axis_arrow(), _draw_bar_chart() (+29 more)

### Community 169 - "required"
Cohesion: 0.15
Nodes (13): artifacts, created_at, evidence, gate_results, generator_id, model, reviewer_identity_class, seed (+5 more)

### Community 170 - "ComputerSciencePlugin"
Cohesion: 0.23
Nodes (11): ComputerSciencePlugin, _evaluate_boolean(), normalise_pseudocode(), pseudocode_equivalent(), Any, truth_table(), test_computer_science_uses_the_specialised_plugin(), test_programming_paper_accepts_only_declared_languages_and_evidence() (+3 more)

### Community 171 - "sample"
Cohesion: 0.25
Nodes (8): candidates, groups, items, response_rows, sample, additionalProperties, required, type

### Community 172 - "aqaaccountgen/generator.py"
Cohesion: 0.25
Nodes (13): _extract(), _gbp(), _gbp_decimal(), _levels(), _management_calculation(), _mcq(), _number(), Random (+5 more)

### Community 173 - "properties"
Cohesion: 0.12
Nodes (17): $ref, $ref, exclusiveMinimum, maximum, type, properties, $ref, minLength (+9 more)

### Community 174 - "aqaecongen/generator.py"
Cohesion: 0.13
Nodes (28): generate_package(), main(), Path, _build_mcq_option(), build_paper(), _build_written_option(), _case_depth(), _paper_three_indicative_content() (+20 more)

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

### Community 181 - "board_profile"
Cohesion: 0.67
Nodes (3): pattern, type, board_profile

### Community 182 - "additionalProperties"
Cohesion: 0.13
Nodes (15): items, minItems, type, uniqueItems, items, minItems, type, uniqueItems (+7 more)

### Community 183 - "generator-capability.schema.json"
Cohesion: 0.17
Nodes (11): additionalProperties, $defs, safePath, $id, pattern, minLength, not, type (+3 more)

### Community 184 - "render_source_booklet"
Cohesion: 0.28
Nodes (15): _apply_edexcel_page_boxes(), _extract_source_questions(), Path, Match Pearson question-paper bleed and crop boxes without changing A4 content., render_source_booklet(), _source_sections(), _pdf_page_count(), _pdf_text() (+7 more)

### Community 185 - "tool_versions"
Cohesion: 0.50
Nodes (4): type, tool_versions, additionalProperties, type

### Community 186 - "generate_package"
Cohesion: 0.29
Nodes (12): generate_package(), Path, page_count(), Path, test_both_packages_render_36_page_question_papers(), test_invalid_paper_is_rejected(), test_paper_one_mark_scheme_matches_reference_question_sequence(), test_paper_one_section_a_matches_measured_case_and_account_pages() (+4 more)

### Community 187 - "String"
Cohesion: 0.05
Nodes (57): CaseIterable, Decodable, AIProvider, anthropic, apple, .backendID, .id, ollama (+49 more)

### Community 188 - "test_aqa_accounting.py"
Cohesion: 0.25
Nodes (14): build_paper(), Syllabus, test_budget_uses_exam_standard_currency_formatting(), test_contribution_question_uses_a_complete_costing_identity(), test_every_management_calculation_has_complete_immutable_source_data(), test_exact_current_mark_sequences_and_totals(), test_income_statement_question_has_a_complete_task_specific_source_contract(), test_management_calculations_group_large_currency_values() (+6 more)

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

### Community 194 - "response_simulation.py"
Cohesion: 0.23
Nodes (10): _band_ratios(), _mapping(), Any, Protocol, Create diagnostic responses without exposing a drafted mark scheme., ResponseSimulator, SimulationClient, _strings() (+2 more)

### Community 195 - "cspapergen/generator.py"
Cohesion: 0.35
Nodes (11): _align_paper1_structure(), _build_paper1_context(), _build_paper1_questions(), _paper1_part(), _paper1_question(), QuestionPart, Random, Match the recurring 7517/1 sub-question and mark pattern. (+3 more)

### Community 196 - "subject_plugin"
Cohesion: 0.67
Nodes (3): subject_plugin, pattern, type

### Community 197 - "SingleCellPanelFactory"
Cohesion: 0.22
Nodes (8): AQAQuestionHeaderFactory, OCRQuestionHeaderFactory, Protocol, QuestionHeaderData, Create measured section banners and information panels., Measured AQA question-number, prompt, and tariff flowables., Measured OCR question-number, prompt, and tariff flowables., SingleCellPanelFactory

### Community 199 - "test_repository_hygiene.py"
Cohesion: 0.30
Nodes (9): test_every_tracked_file_has_a_durable_classification(), test_generated_and_binary_outputs_are_rejected(), test_maintained_visual_assets_are_classified_without_allowing_arbitrary_pngs(), test_root_lint_configuration_is_release_configuration(), Classification, classify_path(), inspect_repository(), main() (+1 more)

### Community 201 - "required"
Cohesion: 0.14
Nodes (14): assessment_kind, command_word_distribution, comparison_basis, demand_distribution, distribution_tolerance, family_id, mark_band_distribution, source_document_count (+6 more)

### Community 202 - "discover_subject_plugin"
Cohesion: 0.24
Nodes (13): board_profile_ids(), discover_subject_plugin(), subject_plugin_ids(), parametrize, test_authorised_extract_with_option_route_and_level_policy_passes(), test_essay_subjects_reject_unprovenanced_evidence(), test_history_rejects_an_inverted_chronology(), test_later_wave_subject_plugins_are_discoverable() (+5 more)

### Community 203 - "formatted_generation_date"
Cohesion: 0.24
Nodes (19): formatted_generation_date(), formatted_generation_series(), generation_date(), date, Return the month/year form used on mark-scheme covers., _page_footer(), _paragraph(), _practice_header() (+11 more)

### Community 204 - "_draw_ms_row"
Cohesion: 0.27
Nodes (10): _draw_ms_blank_page(), _draw_ms_header_box(), _draw_ms_row(), _draw_ms_table_header(), _ms_bold_line(), _ms_centered_line(), _ms_italic_line(), _ms_row_height() (+2 more)

### Community 205 - "Current-family visual qualification — 26 August 2026"
Cohesion: 0.25
Nodes (7): 30 August Paper 2 mark-scheme regression check, Automated evidence, Current-family visual qualification — 26 August 2026, Evidence locations, Manual review, Outstanding non-visual gates, Scope and claim

### Community 206 - "test_reference_demand.py"
Cohesion: 0.29
Nodes (13): module(), profile_payload(), Path, test_committed_profiles_cover_every_advertised_assessment_without_source_text(), test_form_audit_rejects_distribution_drift(), test_item_target_distinguishes_multistage_calculation_from_recall(), test_item_target_turns_high_demand_into_observable_requirements(), test_profile_rejects_missing_aggregate_evidence() (+5 more)

### Community 207 - "JobHistoryView"
Cohesion: 0.25
Nodes (9): GenerationJobState, .systemImage, .title, JobHistoryView, .body, .selectedRecord, GenerationJobRecord, Set (+1 more)

### Community 208 - ".baseQuery"
Cohesion: 0.39
Nodes (4): SecretStore, Any, String, Security

### Community 209 - "SubjectValidation"
Cohesion: 0.12
Nodes (14): ContractSubjectPlugin, _normalise_identifier(), Any, Protocol, Safe baseline plugin for families with validation in their own contracts., register_subject_plugin(), SubjectPlugin, SubjectValidation (+6 more)

### Community 210 - "pastpapergen/cli.py"
Cohesion: 0.14
Nodes (16): _artifacts(), _build(), _improve(), _load_rule(), _normalise_paper_id(), PaperBlueprint, Syllabus, _reject_mark_text() (+8 more)

### Community 211 - "_draw_cover"
Cohesion: 0.16
Nodes (18): economics_exam_schedule(), ExamSchedule, formatted_economics_exam_date(), date, _draw_boxes(), _draw_cover(), _draw_crop_marks(), _draw_fake_barcode() (+10 more)

### Community 212 - "Reference-Demand Calibration Design"
Cohesion: 0.15
Nodes (12): 1. Copyright-safe reference-demand profiles, 2. Item-level demand contracts, 3. Separate difficulty review, 4. Deterministic form-level demand audit, 5. App experience and evidence wording, Current Problem, Design, Failure Handling (+4 more)

### Community 214 - "add_page_structure_tree"
Cohesion: 0.31
Nodes (9): add_page_structure_tree(), has_logical_page_order(), _has_structure_tree(), _new_object(), Document, Page, Path, Attach a deterministic page-level structure tree and marked content. Each page… (+1 more)

### Community 215 - "Cambridge International engineering foundation — 26 August 2026"
Cohesion: 0.40
Nodes (4): Cambridge International engineering foundation — 26 August 2026, Deliberate release gate, Implemented evidence, Scope

### Community 217 - "aqaaccountgen/syllabus.py"
Cohesion: 0.28
Nodes (6): load_syllabus(), BaseModel, field_validator, Path, Syllabus, Topic

### Community 221 - "empirical-calibration.schema.json"
Cohesion: 0.25
Nodes (7): additionalProperties, $id, not, anyOf, $schema, title, type

### Community 222 - "PhysicsPlugin"
Cohesion: 0.43
Nodes (3): PhysicsPlugin, Any, test_physics_requires_uncertainty_for_uncertainty_items()

### Community 223 - "properties"
Cohesion: 0.15
Nodes (13): const, minItems, type, properties, derived_aggregate_only, profiles, purpose, retains_source_text (+5 more)

### Community 224 - "reference-demand-profile.schema.json"
Cohesion: 0.17
Nodes (11): derived_aggregate_only, profiles, purpose, retains_source_text, additionalProperties, $id, schema_version, required (+3 more)

### Community 225 - "Reference-Demand Calibration Implementation Plan"
Cohesion: 0.22
Nodes (8): Reference-Demand Calibration Implementation Plan, Task 1: Specify and validate the profile contract, Task 2: Derive compact profiles from real papers, Task 3: Add deterministic item and form demand audits, Task 4: Separate content review from difficulty review in the shared pipeline, Task 5: Integrate custom AQA Computer Science and Edexcel pipelines, Task 6: Record evidence in registry, manifests and app UI, Task 7: Verify all supported outputs and finish cleanly

### Community 226 - "distribution"
Cohesion: 0.25
Nodes (8): maximum, minimum, type, $defs, distribution, additionalProperties, minProperties, type

### Community 227 - "validate_cross_paper_quality"
Cohesion: 0.43
Nodes (6): Validate cross-item clues and return the paper's assessment balance., validate_cross_paper_quality(), _item(), parametrize, test_cross_paper_quality_fails_closed_on_unintended_clues_and_impossible_data(), test_cross_paper_quality_reports_mark_ao_topic_command_and_demand_balance()

### Community 228 - "test_configured_family.py"
Cohesion: 0.80
Nodes (4): Path, _syllabus(), test_cambridge_computer_science_preview_covers_theory_and_practical_roles(), test_cambridge_economics_preview_covers_all_official_components()

### Community 229 - "enum"
Cohesion: 0.50
Nodes (4): full-paper, question-bank, enum, assessment_kind

### Community 230 - "blueprint_version"
Cohesion: 0.67
Nodes (3): minLength, type, blueprint_version

### Community 231 - "package"
Cohesion: 0.67
Nodes (3): pattern, type, package

### Community 232 - "cspapergen/cli.py"
Cohesion: 0.16
Nodes (17): BuildResult, _artifacts(), _build(), default_output_dir(), _improve(), main(), Path, _supporting() (+9 more)

### Community 233 - "register_fonts"
Cohesion: 0.52
Nodes (5): register_font(), register_fonts(), _standard_fallback(), test_fallback_family_supports_bold_paragraph_markup(), test_missing_font_uses_registered_standard_font_alias()

### Community 234 - "comparison_basis"
Cohesion: 0.67
Nodes (3): minLength, type, comparison_basis

### Community 235 - "family_id"
Cohesion: 0.67
Nodes (3): minLength, type, family_id

### Community 237 - "validate_economics_causal_direction"
Cohesion: 0.40
Nodes (5): Reject common exchange-rate reversals before model review., validate_economics_causal_direction(), parametrize, test_economics_direction_validator_accepts_correct_import_effect(), test_economics_direction_validator_rejects_reversed_import_effects()

### Community 238 - "source_fingerprint"
Cohesion: 0.67
Nodes (3): source_fingerprint, pattern, type

### Community 239 - "_draw_source_content_page"
Cohesion: 0.67
Nodes (4): _draw_source_content_page(), Syllabus, _source_reading_prompt(), _source_title()

### Community 240 - "GlyphMetric"
Cohesion: 0.67
Nodes (3): GlyphMetric, A compact, serialisable sample of one rendered PDF glyph., test_glyph_metric_contract_is_immutable()

### Community 241 - "enum"
Cohesion: 0.50
Nodes (4): ai-assisted, deterministic, enum, content_mode

### Community 242 - "CoverProfile"
Cohesion: 0.11
Nodes (27): aqa_question_cover(), CoverProfile, _draw_aqa_mark_scheme_cover(), _draw_cover_barcode(), draw_mark_scheme_cover(), _draw_ocr_mark_scheme_cover(), mark_scheme_cover(), MarkSchemeCover (+19 more)

### Community 243 - "board"
Cohesion: 0.67
Nodes (3): pattern, type, board

### Community 244 - "id"
Cohesion: 0.67
Nodes (3): pattern, type, id

## Knowledge Gaps
- **823 isolated node(s):** `BoardLayout`, `examforge-aqa-accounting`, `$schema`, `$id`, `title` (+818 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **56 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Work-memory lessons

**Preferred sources** — corroborated by past sessions; start here.
- `AppViewModel` (2× useful, score=1.166012741) _(code changed — re-verify)_
- `generation.py` (2× useful, score=1.164559792) _(code changed — re-verify)_
- `exam_blueprints.py` (2× useful, score=1.127080899) _(code changed — re-verify)_
- `layout_master.py` (2× useful, score=1.127080899) _(code changed — re-verify)_
- `paper_fidelity_audit.py` (2× useful, score=1.127080899) _(code changed — re-verify)_

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `GeneratedQuestion` connect `GeneratedQuestion` to `Paragraph`, `ocregen/render_pdf.py`, `aqabizgen/render_pdf.py`, `exam_blueprints.py`, `aqabizgen/generator.py`, `ocrcsgen/render_pdf.py`, `aqaaccountgen/generator.py`, `aqaecongen/generator.py`, `GeneratedPaper`, `test_reference_demand.py`, `AssessmentCheckpointStore`, `test_ocr_computer_science.py`, `test_ocr_economics.py`, `mark_scheme_enrichment.py`, `AssessmentContract`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Why does `Rect` connect `Rect` to `Paragraph`, `ocregen/render_pdf.py`, `aqabizgen/render_pdf.py`, `ExamPageProfile`, `paper_fidelity_audit.py`, `test_pdf_validation.py`, `GeneratedPaper`, `pdf_validation.py`, `CoverProfile`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Why does `path` connect `generate_package` to `cspapergen/cli.py`, `properties`, `test_repository_hygiene.py`, `inspect_release_compliance`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `GeneratedQuestion` (e.g. with `AssessmentLLMClient` and `GenerationPolicy`) actually correct?**
  _`GeneratedQuestion` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `ApplicationCoordinator` (e.g. with `PaperCreator` and `.body`) actually correct?**
  _`ApplicationCoordinator` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `BoardLayout`, `examforge-aqa-accounting`, `$schema` to the rest of the system?**
  _823 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `cspapergen/render_pdf.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09516172146484897 - nodes in this community are weakly interconnected._