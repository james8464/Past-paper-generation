# Graph Report - Past Paper Creation  (2026-08-30)

## Corpus Check
- 342 files · ~551,379 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 5045 nodes · 13648 edges · 256 communities (200 shown, 56 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 786 edges (avg confidence: 0.67)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `36b17630`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cspapergen/render_pdf.py
- document_dsl/__init__.py
- ApplicationCoordinator
- HelpTopic
- Paragraph
- ocregen/render_pdf.py
- Table
- test_render_pdf.py
- aqabizgen/generator.py
- pastpapergen/generator.py
- build_paper_blueprint
- GeneratedPaper
- paper_fidelity_audit.py
- reference_corpus.py
- aqaecongen/render_pdf.py
- test_coverage_matrix.py
- CodingKeys
- exam_blueprints.py
- Rect
- test_ocr_economics.py
- live_generation_matrix.py
- Text
- benchmark.py
- configuredgen/render_pdf.py
- mark_scheme_enrichment.py
- Size
- AssessmentContract
- ModelCoordinator
- assessment_package.py
- CatalogStore
- Paper creator: deep project analysis
- Q: Which Ollama model and live validation path does the project use for all supported papers?
- graphs.py
- mathematics.py
- generation.py
- pastpapergen/notes.py
- properties
- render_pdf_atomically
- test_mark_scheme_layout.py
- AssessmentCheckpointStore
- Approved-Improvement Traceability
- test_app_backend.py
- ReviewResult
- ExamPageProfile
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
- aqa_accounting_calibration.py
- Q: How is the macOS backend bundle kept complete?
- File Structure
- BackendClient
- .validate_distribution
- RecentDocumentStore
- aqa_section_intro
- Rendering and Mark-Scheme Reliability Implementation Plan
- Architecture
- build_layout_masters.py
- JobHistoryView
- Glossy Black Fountain Pen App Icon Master
- pastpapergen/ollama_client.py
- enum
- Assessment quality and originality
- reference_demand.py
- macOS interaction and HIG compliance
- layout_master.py
- test_pdf_validation.py
- Q: how can we make even more improvements to get the highest similarity in terms of structure and layout and quality of questions etc. and maybe all of the files in the project can be better organised. and the UI can be made to be much better and more geometrically apple-like by strictly following every single rule they outline in their HIG
- Paper creator
- reconcile_solution
- pull_request_template.md
- test_ocr_computer_science.py
- required
- backend-protocol.schema.json
- properties
- test_science_overlay.py
- generator_working_directory
- xcbuild.sh
- psychometrics.py
- capabilities
- formatted_generation_date
- BackendEvent
- diagnose.sh
- move_to_trash.sh
- inspect_release_compliance
- run_app_macos.sh
- test_humanities_overlay.py
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
- PartnershipCase
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
- family_adapter.py
- Canvas
- properties
- _call_name
- Q: How does the paper fidelity audit produce per-document and per-role scores, and where should release thresholds integrate?
- required
- NonCurrentAssetCase
- qualification_levels
- CoverProfile
- validate_mark_scheme_item
- required
- properties
- test_document_dsl.py
- required
- ComputerSciencePlugin
- sample
- cspapergen/notes.py
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
- _draw_ms_row
- tool_versions
- BenchmarkCoordinator
- String
- test_aqa_accounting.py
- enum
- required
- backend_subject
- app_board
- app_subject
- response_simulation.py
- independent_solver.py
- ocr_computer_science_calibration.py
- aqa_business_calibration.py
- _BooleanParser
- test_repository_hygiene.py
- _draw_source_content_page
- required
- subject_plugins.py
- BenchmarkChart
- pastpapergen/render_pdf.py
- Current-family visual qualification — 26 August 2026
- test_reference_demand.py
- empirical-calibration.schema.json
- .baseQuery
- SubjectValidation
- assessment_quality.py
- _draw_cover
- Reference-Demand Calibration Design
- ocrcsgen/generator.py
- entry_point
- Cambridge International engineering foundation — 26 August 2026
- README.md
- specification_version
- subjects/__init__.py
- configuredgen/__init__.py
- paper-creator-configured-generators
- QuestionPaperCover
- PhysicsPlugin
- properties
- reference-demand-profile.schema.json
- Reference-Demand Calibration Implementation Plan
- distribution
- validate_cross_paper_quality
- pastpapergen/cli.py
- enum
- blueprint_version
- package
- generate_package
- subject_plugin
- comparison_basis
- family_id
- SubjectPlugin
- subject
- ReportLabBackend
- source_fingerprint
- cspapergen/ollama_client.py
- aqaaccountgen/generator.py
- paper1_assets.py
- AnswerSpace
- IncomeStatementCase
- generate_package
- _draw_paper_3_source_page
- add_page_structure_tree
- parse_model_recommendations
- aqaaccountgen/syllabus.py
- ChemistryPlugin
- cspapergen/cli.py
- CostingCase
- SalesLedgerCase
- validate_economics_causal_direction
- test_configured_family.py

## God Nodes (most connected - your core abstractions)
1. `GeneratedQuestion` - 189 edges
2. `build_paper_blueprint()` - 167 edges
3. `load_builtin_paper_config()` - 151 edges
4. `load_syllabus()` - 150 edges
5. `ApplicationCoordinator` - 138 edges
6. `GeneratedOption` - 100 edges
7. `GeneratedPaper` - 83 edges
8. `Table` - 78 edges
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

## Communities (256 total, 56 thin omitted)

### Community 0 - "cspapergen/render_pdf.py"
Cohesion: 0.08
Nodes (98): CanvasBarcodeStyle, draw_barcode(), draw_glyph_answer_rules(), draw_solid_answer_rules(), GlyphRuleStyle, Canvas, Draw a fixed number of solid response rules and return the next baseline., Draw selectable glyph-based response rules and return the next baseline. (+90 more)

### Community 1 - "document_dsl/__init__.py"
Cohesion: 0.16
Nodes (21): BoardProfile, DocumentRole, FontToken, FontTokens, Frame, LayoutBox, LayoutPage, PageRole (+13 more)

### Community 2 - "ApplicationCoordinator"
Cohesion: 0.03
Nodes (57): AnyCancellable, DateFormatter, .body, AppDefaults, AppLinks, Bool, String, URL (+49 more)

### Community 3 - "HelpTopic"
Cohesion: 0.06
Nodes (34): App, AppKit, CaseIterable, Commands, AppCommands, PaperCreator, .body, HelpTopic (+26 more)

### Community 4 - "Paragraph"
Cohesion: 0.16
Nodes (48): AQAAnswerLines, Paragraph, _accounting_marking_guidance_pages(), _accounting_system_case(), _additional_answer_page(), _appropriation_answer_table(), _company_statement_case(), _completed_appropriation_scheme() (+40 more)

### Community 5 - "ocregen/render_pdf.py"
Cohesion: 0.09
Nodes (68): OCRAnswerLines, _add_economics_diagram(), _add_firm_objectives_diagram(), _add_ppf_diagram(), _annotation_conventions_page(), _answer_mark(), _assessment_allocation(), _assessment_grid_groups() (+60 more)

### Community 6 - "Table"
Cohesion: 0.09
Nodes (55): Table, AQAQuestionHeaderFactory, Measured AQA question-number, prompt, and tariff flowables., aqa_front_matter_pages(), Flowable, _artifacts(), _additional_answer_page(), _ao_summary() (+47 more)

### Community 7 - "test_render_pdf.py"
Cohesion: 0.12
Nodes (48): _apply_edexcel_page_boxes(), Path, Match Pearson question-paper bleed and crop boxes without changing A4 content., render_question_paper(), _answer_rule_count(), _blank_axis_lines(), _blueprint_with_section_a_question(), _dark_pixels() (+40 more)

### Community 8 - "aqabizgen/generator.py"
Cohesion: 0.09
Nodes (36): GeneratedSection, generate_package(), Path, FinancialPosition, format_number(), Format an exam answer without meaningless trailing zeroes., The single source of truth for Paper 1 financial-statement figures., build_paper() (+28 more)

### Community 9 - "pastpapergen/generator.py"
Cohesion: 0.06
Nodes (72): MultipleChoiceOption, _adapt_paper_three_case_guidance(), _best_section_a_context_point(), _build_part(), _build_parts(), _choice_group_name(), _choice_lookup(), _choose_topic() (+64 more)

### Community 10 - "build_paper_blueprint"
Cohesion: 0.09
Nodes (78): build_paper_blueprint(), PaperBlueprint, Syllabus, load_builtin_paper_config(), line_chart_data(), load_syllabus(), Path, Syllabus (+70 more)

### Community 11 - "GeneratedPaper"
Cohesion: 0.12
Nodes (33): GeneratedPaper, ExamPage, Flowable, A full-page shell that can also live inside a Platypus story., OCRComputerScienceAnswerLines, _assessment_objectives_page(), _chrome(), _cover_profile() (+25 more)

### Community 12 - "paper_fidelity_audit.py"
Cohesion: 0.05
Nodes (103): Pixmap, parametrize, Path, test_compact_profile_omits_raster_geometry(), test_contact_sheets_make_visual_review_artifacts(), test_generated_document_falls_back_to_nested_transaction_output(), test_generated_document_supports_app_per_paper_directories(), test_metric_callout_names_print_resolution_comparison_dimensions() (+95 more)

### Community 13 - "reference_corpus.py"
Cohesion: 0.13
Nodes (45): MonkeyPatch, Path, test_document_path_requires_filename(), test_document_path_stays_inside_corpus(), test_download_manifest_records_failure_and_continues(), test_parse_aqa_resources_filters_modified_papers(), test_parse_ocr_resources_uses_a_level_tab_only(), test_parse_ocr_specifications_keeps_a_level_not_as_level() (+37 more)

### Community 14 - "aqaecongen/render_pdf.py"
Cohesion: 0.10
Nodes (41): AnswerLineFlowable, AQACompactAnswerLines, Flowable, Return a Table subclass whose raw string cells use the controlled font.…, Shared, measured answer-line primitive used by every board renderer., themed_table_class(), _artifacts(), _context_data_table() (+33 more)

### Community 15 - "test_coverage_matrix.py"
Cohesion: 0.07
Nodes (57): family(), matrix(), Path, test_catalog_availability_is_owned_only_by_registry(), test_checked_in_matrix_is_deterministic_and_current(), test_existing_generators_are_reported_without_false_verification(), test_matrix_exactly_covers_layout_profiles(), test_no_verified_paper_has_a_failed_gate() (+49 more)

### Community 16 - "CodingKeys"
Cohesion: 0.04
Nodes (57): CodingKey, CodingKeys, assessmentKind, backendVersion, capabilities, checks, code, command (+49 more)

### Community 17 - "exam_blueprints.py"
Cohesion: 0.11
Nodes (47): _demand_band(), _hydrate_assessment_metadata(), _objective_allocation(), PaperRule, _prompt_uses_command_word(), BaseModel, QuestionRule, SectionRule (+39 more)

### Community 18 - "Rect"
Cohesion: 0.12
Nodes (35): Rect, compare_page_evidence(), _contrast_against_white(), _contrast_ratio(), _count_score(), _font_embedding(), _font_evidence(), _is_decorative_bleed() (+27 more)

### Community 19 - "test_ocr_economics.py"
Cohesion: 0.10
Nodes (39): generate_package(), Path, build_paper(), _evaluation_scheme(), _extract(), _extract_number(), _instructions(), _mcq() (+31 more)

### Community 20 - "live_generation_matrix.py"
Cohesion: 0.08
Nodes (49): Release qualification evidence and policy models., ArtifactEvidence, EvidenceRecord, GateState, ModelIdentity, BaseModel, field_validator, Path (+41 more)

### Community 21 - "Text"
Cohesion: 0.03
Nodes (98): View, PanelEmptyState, .body, String, BenchmarkVerdict, .body, BenchmarkMetricGrid, .body (+90 more)

### Community 22 - "benchmark.py"
Cohesion: 0.12
Nodes (33): apple_cpu_core_split(), available_memory_gb(), avg(), clamp(), cpu_brand(), cpu_load_percent(), cpu_probe(), disk_probe() (+25 more)

### Community 23 - "configuredgen/render_pdf.py"
Cohesion: 0.17
Nodes (23): Cover, SchemeGrid, DocumentMetadata, DocumentSpec, PageSpec, Paginator, ConfiguredSyllabus, load_syllabus() (+15 more)

### Community 24 - "mark_scheme_enrichment.py"
Cohesion: 0.24
Nodes (19): _answer_form(), _application_label(), _clean_text(), _compact_technical_guidance(), _deduplicate(), enrich_paper(), _enrich_question(), _level_guidance() (+11 more)

### Community 25 - "Size"
Cohesion: 0.15
Nodes (15): BaseComponent, BlankPage, Component, ContinuationPage, InstructionBlock, LevelTable, MarkBox, BoardProfile (+7 more)

### Community 26 - "AssessmentContract"
Cohesion: 0.13
Nodes (28): AssessmentContract, contract_for_question(), GeneratedNumericField, GraphContract, _numeric_contracts(), NumericRole, NumericValueContract, Any (+20 more)

### Community 27 - "ModelCoordinator"
Cohesion: 0.05
Nodes (34): Foundation, AppStorageKey, SecretAccount, OllamaState, EstimateTuning, AppClock, KeychainSecretStore, SecretStoring (+26 more)

### Community 28 - "assessment_package.py"
Cohesion: 0.21
Nodes (25): _assessment_contract(), AssessmentPackageCompatibilityError, _contains_non_finite(), _evidence_ids(), _extract_items(), _form_id(), _level_policies(), load_assessment_package() (+17 more)

### Community 29 - "CatalogStore"
Cohesion: 0.08
Nodes (29): CatalogSubject, SidebarItem, benchmark, documents, history, BoardRow, .body, CatalogSidebarSections (+21 more)

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
Cohesion: 0.15
Nodes (21): AnswerComparison, compare_mathematical_answers(), FurtherMathematicsPlugin, MarkAward, _marking_rules(), MarkingRule, MathematicalAnswer, MathematicsPlugin (+13 more)

### Community 34 - "generation.py"
Cohesion: 0.21
Nodes (21): progress_emitter(), _atomic_publish(), _cancel_generation(), checkpoint_path_for_job(), emit_generated_files(), finalize_generated_documents(), GenerationCancelled, _generator_version() (+13 more)

### Community 35 - "pastpapergen/notes.py"
Cohesion: 0.20
Nodes (19): _clean_chunk(), essay_capable_topic_ids(), _flush_note_chunk(), _is_exam_point(), _is_note_noise(), _looks_like_heading(), _note_chunks(), note_context_for_topic() (+11 more)

### Community 36 - "properties"
Cohesion: 0.09
Nodes (23): ai-assisted, deterministic, type, pattern, type, enum, pattern, type (+15 more)

### Community 37 - "render_pdf_atomically"
Cohesion: 0.15
Nodes (23): InvalidRenderOutput, Path, RuntimeError, A document role could not be rendered safely., Rendering exceeded its bounded qualification window., A renderer returned without producing a readable PDF., Render one PDF role under a deadline and promote it atomically., _readable_page_count() (+15 more)

### Community 38 - "test_mark_scheme_layout.py"
Cohesion: 0.18
Nodes (30): pdf_font_names(), Path, Return the font families actually used by visible text spans., _cleanup_graph_cache(), render_mark_scheme(), _blueprint_with_section_a_calculation(), _blueprint_with_section_b_topic(), _pdf_page_count() (+22 more)

### Community 39 - "AssessmentCheckpointStore"
Cohesion: 0.15
Nodes (25): AssessmentCheckpointStore, CheckpointCorrupt, CheckpointIdentity, CheckpointMismatch, identity_for_blueprint(), Any, BaseModel, Path (+17 more)

### Community 40 - "Approved-Improvement Traceability"
Cohesion: 0.07
Nodes (26): Approved-Improvement Traceability, Current-Paper Gate, Expansion Gate, Foundation Gate, Global Constraints, Paper Creator Excellence Programme Implementation Plan, Phase Completion Gates, Plan Verification Checklist (+18 more)

### Community 41 - "test_app_backend.py"
Cohesion: 0.16
Nodes (28): _safe_provider_detail(), CaptureFixture, CompletedProcess, Path, run_bridge(), run_bridge_raw(), test_aqa_accounting_all_papers_generate_expected_files(), test_aqa_business_all_papers_generate_expected_files() (+20 more)

### Community 42 - "ReviewResult"
Cohesion: 0.18
Nodes (21): numeric_tokens(), Extract quantities exactly enough to catch broken data/source rewrites., assert_materially_new(), difficulty_review(), DifficultyReviewResult, independent_review(), JSONClient, Any (+13 more)

### Community 43 - "ExamPageProfile"
Cohesion: 0.20
Nodes (26): _draw_aqa_footer(), _draw_aqa_page(), _draw_barcode(), draw_exam_page(), _draw_independent_notice(), _draw_ocr_notice(), _draw_ocr_page(), _draw_ocr_rules() (+18 more)

### Community 44 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Measured Paper Fidelity Implementation Plan, Task 1: Page-role-aware fidelity evidence, Task 2: Shared board answer-page geometry, Task 3: OCR response and blank-page grammar, Task 4: Shared mark-scheme cover calibration, Task 5: Full visual qualification and regression gate

### Community 45 - "load_syllabus"
Cohesion: 0.08
Nodes (62): _build(), build_paper1_blueprint(), build_paper2_blueprint(), build_topic_question_bank(), PaperBlueprint, Syllabus, improve_questions_with_ollama(), load_syllabus() (+54 more)

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
Cohesion: 0.21
Nodes (58): Stimulus, _assembly_program_question(), _assembly_trace_question(), _big_data_question(), _big_data_short_question(), _binary_short_question(), _bitmap_question(), _bitmap_storage_question() (+50 more)

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
Cohesion: 0.11
Nodes (36): _improve(), _clean_prompt(), generate_questions_with_ollama(), _merge_question_text(), _merge_source_text(), PaperBlueprint, Syllabus, Run an independent demand-only gate over every rendered question item. (+28 more)

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
Cohesion: 0.14
Nodes (27): _brief_source_evidence(), _calculation_answer_lines(), _mark_point_relevance(), _mark_scheme_rows(), _normalise_mark_point(), _one_mark_points(), _paper_one_fifteen_mark_scheme_lines(), _paper_one_five_mark_diagram_lines() (+19 more)

### Community 59 - "aqa_accounting_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_both_papers_pass_multi_seed_automated_checks(), test_external_difficulty_gates_remain_false(), test_reference_evidence_is_aggregate_only(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 60 - "Q: How is the macOS backend bundle kept complete?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: How is the macOS backend bundle kept complete?, Source Nodes

### Community 61 - "File Structure"
Cohesion: 0.17
Nodes (11): Assessment Reliability Core Implementation Plan, File Structure, Global Constraints, Subsequent Phase Plans, Task 1: Typed Item Contracts, Task 2: Role-Aware Numeric and Evidence Validation, Task 3: Item-Scoped Draft, Review, and Repair, Task 4: Atomic Checkpoints and Resume (+3 more)

### Community 62 - "BackendClient"
Cohesion: 0.16
Nodes (14): BackendClient, BackendClientError, backendMissing, .errorDescription, pythonMissing, pythonVenvUnreadable, BackendFile, LaunchConfiguration (+6 more)

### Community 64 - "RecentDocumentStore"
Cohesion: 0.07
Nodes (37): Codable, Equatable, FileManager, GenerationJobState, LocalizedError, GenerationConfiguration, GenerationJobRecord, .missingArtifactCount (+29 more)

### Community 65 - "aqa_section_intro"
Cohesion: 0.12
Nodes (22): aqa_lozenge(), aqa_section_intro(), flowable_question_block(), independent_practice_page(), OCRQuestionHeaderFactory, page_sequence(), Color, Drawing (+14 more)

### Community 66 - "Rendering and Mark-Scheme Reliability Implementation Plan"
Cohesion: 0.25
Nodes (7): Rendering and Mark-Scheme Reliability Implementation Plan, Task 1: Bounded atomic render transactions, Task 2: Route every generator family through the transaction, Task 3: Artifact containment, collision, and density evidence, Task 4: Mark-scheme depth contracts, Task 5: OCR Economics pagination regression, Task 6: Phase qualification

### Community 67 - "Architecture"
Cohesion: 0.17
Nodes (11): Architecture, Canonical registry, Extension contract, Failure containment, Fidelity qualification boundary, Package transaction, PDF portability and accessibility, Product boundary (+3 more)

### Community 68 - "build_layout_masters.py"
Cohesion: 0.26
Nodes (19): _box(), _colour(), _content_box(), _drawing_kind(), _drawings(), extract_layout_master(), _furniture_signature(), _images() (+11 more)

### Community 69 - "JobHistoryView"
Cohesion: 0.25
Nodes (9): GenerationJobState, .systemImage, .title, JobHistoryView, .body, .selectedRecord, GenerationJobRecord, Set (+1 more)

### Community 70 - "Glossy Black Fountain Pen App Icon Master"
Cohesion: 0.18
Nodes (11): Glossy Black Fountain Pen App Icon Master, Paper Creator App Icon AppIcon-128x128@1x, Paper Creator App Icon AppIcon-128x128@2x, Paper Creator App Icon AppIcon-16x16@1x, Paper Creator App Icon AppIcon-16x16@2x, Paper Creator App Icon AppIcon-256x256@1x, Paper Creator App Icon AppIcon-256x256@2x, Paper Creator App Icon AppIcon-32x32@1x (+3 more)

### Community 71 - "pastpapergen/ollama_client.py"
Cohesion: 0.08
Nodes (44): MultipleChoiceOption, PaperBlueprint, PaperConfig, BaseModel, QuestionBlueprint, QuestionPart, SectionConfig, Syllabus (+36 more)

### Community 72 - "enum"
Cohesion: 0.18
Nodes (11): benchmark_done, benchmark_metric, benchmark_sample, done, error, file, hello, models (+3 more)

### Community 73 - "Assessment quality and originality"
Cohesion: 0.14
Nodes (13): AQA Computer Science examiner-feedback contract, Assessment quality and originality, Difficulty claims, Human release review, Independent solution and response-band qualification, Item transactions and two-pass generation, Mark-scheme quality, Measured visual qualification (+5 more)

### Community 74 - "reference_demand.py"
Cohesion: 0.05
Nodes (63): board_profile(), BoardProfile, _normalise_identifier(), audit_form_demand(), build_item_demand_target(), _collapse_command_distribution(), _command_family(), _distribution() (+55 more)

### Community 75 - "macOS interaction and HIG compliance"
Cohesion: 0.22
Nodes (8): Accessibility verification, Commands and state, File workflow, Geometry and visual language, Information architecture, macOS interaction and HIG compliance, Onboarding and help, Settings

### Community 76 - "layout_master.py"
Cohesion: 0.10
Nodes (31): conform_generated_documents(), Path, _clamp_fitz_rect(), conform_pdf_page_boxes(), conform_pdf_to_box_template(), draw_text_slot(), _fitz_rect_close(), LayoutConformanceError (+23 more)

### Community 77 - "test_pdf_validation.py"
Cohesion: 0.20
Nodes (23): extract_pdf_evidence(), GlyphMetric, A compact, serialisable sample of one rendered PDF glyph., Extract print and accessibility evidence without retaining source prose. Glyph…, Canvas, Path, _release_canvas(), test_duplicate_text_at_the_same_position_is_rejected() (+15 more)

### Community 78 - "Q: how can we make even more improvements to get the highest similarity in terms of structure and layout and quality of questions etc. and maybe all of the files in the project can be better organised. and the UI can be made to be much better and more geometrically apple-like by strictly following every single rule they outline in their HIG"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: how can we make even more improvements to get the highest similarity in terms of structure and layout and quality of questions etc. and maybe all of the files in the project can be better organised. and the UI can be made to be much better and more geometrically apple-like by strictly following every single rule they outline in their HIG, Source Nodes

### Community 79 - "Paper creator"
Cohesion: 0.25
Nodes (8): Architecture and quality analysis, Build Checks, CLI, Development Reference Corpus, Paper creator, Privacy, Run, Structure

### Community 80 - "reconcile_solution"
Cohesion: 0.22
Nodes (20): EvidenceRecord, CanonicalSolution, IndependentSolver, _numbers(), BaseModel, Solve an item in a context that deliberately excludes its draft scheme., reconcile_solution(), ReconciliationIssue (+12 more)

### Community 81 - "pull_request_template.md"
Cohesion: 0.50
Nodes (3): Risk, Verification, What changed

### Community 82 - "test_ocr_computer_science.py"
Cohesion: 0.15
Nodes (24): generate_package(), Path, build_paper(), Syllabus, _flatten(), Path, test_blank_leaf_matches_ocr_heading_and_message_baselines(), test_boolean_calculation_parts_are_distinct_and_topic_aligned() (+16 more)

### Community 83 - "required"
Cohesion: 0.09
Nodes (22): advertised, app_board, app_subject, backend_subject, blueprint_version, board, board_profile, content_mode (+14 more)

### Community 84 - "backend-protocol.schema.json"
Cohesion: 0.15
Nodes (12): event_id, job_id, protocol, timestamp, type, additionalProperties, allOf, $id (+4 more)

### Community 85 - "properties"
Cohesion: 0.12
Nodes (17): type, pattern, type, minLength, type, minLength, type, minLength (+9 more)

### Community 86 - "test_science_overlay.py"
Cohesion: 0.35
Nodes (16): apparatus_diagram(), ApparatusSpec, Atom, Bond, circuit_diagram(), CircuitComponent, CircuitSpec, molecule_diagram() (+8 more)

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

### Community 91 - "formatted_generation_date"
Cohesion: 0.21
Nodes (20): formatted_generation_date(), formatted_generation_series(), generation_date(), date, Return the month/year form used on mark-scheme covers., _extract_source_questions(), render_source_booklet(), _source_sections() (+12 more)

### Community 92 - "BackendEvent"
Cohesion: 0.06
Nodes (25): BackendEvent, benchmarkDone, benchmarkMetric, benchmarkSample, done, error, file, hello (+17 more)

### Community 95 - "inspect_release_compliance"
Cohesion: 0.27
Nodes (14): Path, test_release_compliance_detects_a_tracked_secret_signature(), test_release_compliance_passes_for_the_repository(), test_release_compliance_rejects_unbounded_runtime_dependencies(), _check_dependencies(), _check_entitlements(), _check_font_licences(), _check_privacy_manifest() (+6 more)

### Community 97 - "test_humanities_overlay.py"
Cohesion: 0.55
Nodes (9): map_diagram(), MapFeature, MapSpec, Drawing, timeline_diagram(), TimelineEvent, TimelineSpec, test_humanities_diagrams_reject_misleading_or_invalid_inputs() (+1 more)

### Community 99 - "properties"
Cohesion: 0.12
Nodes (17): type, properties, type, type, type, type, type, type (+9 more)

### Community 101 - "build_backend.sh"
Cohesion: 0.29
Nodes (5): MPLCONFIGDIR, PYINSTALLER_CONFIG_DIR, PYTHONPATH, build_backend.sh script, XDG_CACHE_HOME

### Community 104 - "CodingKeys"
Cohesion: 0.07
Nodes (35): CodingKeys, appContextWindow, contextWindow, defaultModel, detail, downloadSizeGB, id, maximumMemoryGB (+27 more)

### Community 106 - "test_science_subjects.py"
Cohesion: 0.18
Nodes (16): equation_is_balanced(), _equation_side(), Formula, _multiplier(), _parse_group(), Counter, compare_physical_answers(), _normalise_unit() (+8 more)

### Community 115 - "required"
Cohesion: 0.10
Nodes (22): differential_item_functioning, discrimination, facility, item_id, median_time_seconds, responses, minimum, type (+14 more)

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
Nodes (37): Combine, DocumentPreviewView, .body, .exportAlertBinding, .provenanceRecord, .selectedBinding, .selectedFile, PDFDocumentView (+29 more)

### Community 155 - "GeneratedQuestion"
Cohesion: 0.07
Nodes (101): AssessmentLLMClient, _batches_for_client(), _bounded_text(), _candidate_question(), _canonical_objective_allocation(), _clean_generated_prompt(), _contains_command_word(), _demand_item() (+93 more)

### Community 156 - "family_adapter.py"
Cohesion: 0.21
Nodes (16): ArtifactSpec, FamilyAdapter, Path, run_family_adapter(), default_ollama_model(), model_recommendations(), OllamaModelRecommendations, ProgressCallback (+8 more)

### Community 157 - "Canvas"
Cohesion: 0.16
Nodes (35): _count_pages(), _draw_answer_lines_until(), _draw_answer_page_header(), _draw_centred_instruction_line(), _draw_continuation_lines(), _draw_crop_marks(), _draw_do_not_write_rail(), _draw_hatched_rail() (+27 more)

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

### Community 164 - "CoverProfile"
Cohesion: 0.14
Nodes (22): aqa_question_cover(), CoverProfile, _draw_aqa_mark_scheme_cover(), _draw_cover_barcode(), draw_mark_scheme_cover(), _draw_ocr_mark_scheme_cover(), mark_scheme_cover(), MarkSchemeCover (+14 more)

### Community 165 - "validate_mark_scheme_item"
Cohesion: 0.27
Nodes (16): _contains_any(), MarkSchemeQuality, _normalise(), Any, validate_mark_scheme_item(), _item(), test_accounting_follow_through_metadata_counts_as_method_guidance(), test_calculation_requires_method_or_working() (+8 more)

### Community 166 - "required"
Cohesion: 0.17
Nodes (12): difficulty_independently_verified, evidence_fingerprint, family, form_id, paper, policy, provenance, sample (+4 more)

### Community 167 - "properties"
Cohesion: 0.12
Nodes (16): minLength, type, minLength, type, minLength, type, blueprint, contract (+8 more)

### Community 168 - "test_document_dsl.py"
Cohesion: 0.24
Nodes (19): Diagram, Graph, AccountingTable, EconomicCurve, LogicCircuit, MathematicalPlot, Molecule, ProgramTraceTable (+11 more)

### Community 169 - "required"
Cohesion: 0.15
Nodes (13): artifacts, created_at, evidence, gate_results, generator_id, model, reviewer_identity_class, seed (+5 more)

### Community 170 - "ComputerSciencePlugin"
Cohesion: 0.25
Nodes (10): ComputerSciencePlugin, _evaluate_boolean(), normalise_pseudocode(), pseudocode_equivalent(), Any, truth_table(), test_programming_paper_accepts_only_declared_languages_and_evidence(), test_pseudocode_normalisation_preserves_tokens_not_formatting() (+2 more)

### Community 171 - "sample"
Cohesion: 0.25
Nodes (8): candidates, groups, items, response_rows, sample, additionalProperties, required, type

### Community 172 - "cspapergen/notes.py"
Cohesion: 0.38
Nodes (9): cache_notes(), discover_note_pdfs(), _extract_text(), note_context_for_topic(), NotesManifest, Path, _topic_prefixes(), test_cache_notes_extracts_text_into_project_cache() (+1 more)

### Community 173 - "properties"
Cohesion: 0.12
Nodes (17): $ref, $ref, exclusiveMinimum, maximum, type, properties, $ref, minLength (+9 more)

### Community 174 - "aqaecongen/generator.py"
Cohesion: 0.12
Nodes (28): _build_mcq_option(), build_paper(), _build_written_option(), _case_depth(), _paper_three_indicative_content(), policy_name(), Random, Syllabus (+20 more)

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

### Community 184 - "_draw_ms_row"
Cohesion: 0.27
Nodes (10): _draw_ms_blank_page(), _draw_ms_header_box(), _draw_ms_row(), _draw_ms_table_header(), _ms_bold_line(), _ms_centered_line(), _ms_italic_line(), _ms_row_height() (+2 more)

### Community 185 - "tool_versions"
Cohesion: 0.50
Nodes (4): type, tool_versions, additionalProperties, type

### Community 186 - "BenchmarkCoordinator"
Cohesion: 0.13
Nodes (14): Identifiable, BenchmarkMetric, .displayValue, BenchmarkSample, .networkLatencyDisplayMS, .thermalSpeedLimitDisplayPercent, BenchmarkCoordinator, Bool (+6 more)

### Community 187 - "String"
Cohesion: 0.04
Nodes (78): Decodable, Hashable, AIProvider, anthropic, apple, .backendID, .id, ollama (+70 more)

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

### Community 195 - "independent_solver.py"
Cohesion: 0.18
Nodes (17): content_similarity(), Weighted token-shingle Jaccard similarity in the closed interval 0...1., _as_mapping(), _concept_coverage(), _concept_tokens(), _format_number(), _normalise(), _normalise_choice_answer() (+9 more)

### Community 196 - "ocr_computer_science_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_difficulty_remains_external_evidence_gated(), test_multi_seed_structural_demand_passes(), test_reference_evidence_is_aggregate_only(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 197 - "aqa_business_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 199 - "test_repository_hygiene.py"
Cohesion: 0.23
Nodes (12): type, path, test_committed_inventory_matches_the_current_repository(), test_every_tracked_file_has_a_durable_classification(), test_generated_and_binary_outputs_are_rejected(), test_maintained_visual_assets_are_classified_without_allowing_arbitrary_pngs(), test_root_lint_configuration_is_release_configuration(), Classification (+4 more)

### Community 200 - "_draw_source_content_page"
Cohesion: 0.67
Nodes (4): _draw_source_content_page(), Syllabus, _source_reading_prompt(), _source_title()

### Community 201 - "required"
Cohesion: 0.14
Nodes (14): assessment_kind, command_word_distribution, comparison_basis, demand_distribution, distribution_tolerance, family_id, mark_band_distribution, source_document_count (+6 more)

### Community 202 - "subject_plugins.py"
Cohesion: 0.20
Nodes (16): board_profile_ids(), discover_subject_plugin(), _normalise_identifier(), register_subject_plugin(), subject_plugin_ids(), test_computer_science_uses_the_specialised_plugin(), parametrize, test_authorised_extract_with_option_route_and_level_policy_passes() (+8 more)

### Community 203 - "BenchmarkChart"
Cohesion: 0.07
Nodes (29): CGFloat, Charts, KeyPath, Bool, WorkspaceLayoutMode, compact, expanded, .showsInspector (+21 more)

### Community 204 - "pastpapergen/render_pdf.py"
Cohesion: 0.08
Nodes (44): BoardLayout, GraphParams, _answer_line_count(), _axis_labels_for_draw_prompt(), _bar_chart_data(), _bar_label(), _draw_answer_lines(), _draw_axis_arrow() (+36 more)

### Community 205 - "Current-family visual qualification — 26 August 2026"
Cohesion: 0.22
Nodes (8): 30 August Paper 2 mark-scheme regression check, 30 August shared-renderer and economics-scheme qualification, Automated evidence, Current-family visual qualification — 26 August 2026, Evidence locations, Manual review, Outstanding non-visual gates, Scope and claim

### Community 206 - "test_reference_demand.py"
Cohesion: 0.29
Nodes (13): module(), profile_payload(), Path, test_committed_profiles_cover_every_advertised_assessment_without_source_text(), test_form_audit_rejects_distribution_drift(), test_item_target_distinguishes_multistage_calculation_from_recall(), test_item_target_turns_high_demand_into_observable_requirements(), test_profile_rejects_missing_aggregate_evidence() (+5 more)

### Community 207 - "empirical-calibration.schema.json"
Cohesion: 0.25
Nodes (7): additionalProperties, $id, not, anyOf, $schema, title, type

### Community 208 - ".baseQuery"
Cohesion: 0.39
Nodes (4): SecretStore, Any, String, Security

### Community 209 - "SubjectValidation"
Cohesion: 0.23
Nodes (6): SubjectValidation, BiologyPlugin, Any, EssaySubjectPlugin, Any, _validate_provenance()

### Community 210 - "assessment_quality.py"
Cohesion: 0.14
Nodes (18): _ignored_candidate_quantities(), _is_subsequence(), _items(), _load_package(), normalise_item_text(), _normalise_quantity(), _precision_digit_tokens(), _precision_instructions() (+10 more)

### Community 211 - "_draw_cover"
Cohesion: 0.23
Nodes (13): economics_exam_schedule(), ExamSchedule, formatted_economics_exam_date(), date, _draw_boxes(), _draw_cover(), _draw_front_section(), _draw_source_cover() (+5 more)

### Community 212 - "Reference-Demand Calibration Design"
Cohesion: 0.15
Nodes (12): 1. Copyright-safe reference-demand profiles, 2. Item-level demand contracts, 3. Separate difficulty review, 4. Deterministic form-level demand audit, 5. App experience and evidence wording, Current Problem, Design, Failure Handling (+4 more)

### Community 213 - "ocrcsgen/generator.py"
Cohesion: 0.21
Nodes (15): _analysis_prompt(), _levels(), _programming_prompt(), _programming_scheme(), Random, Topic, _question(), _representation_calculation() (+7 more)

### Community 214 - "entry_point"
Cohesion: 0.67
Nodes (3): pattern, type, entry_point

### Community 215 - "Cambridge International engineering foundation — 26 August 2026"
Cohesion: 0.40
Nodes (4): Cambridge International engineering foundation — 26 August 2026, Deliberate release gate, Implemented evidence, Scope

### Community 217 - "specification_version"
Cohesion: 0.67
Nodes (3): specification_version, minLength, type

### Community 221 - "QuestionPaperCover"
Cohesion: 0.24
Nodes (5): QuestionPaperCover, Fixed-grid, board-shaped front page without copying protected artwork., Return the renderer-neutral representation used for qualification., _wrap(), test_legacy_cover_and_special_pages_expose_dsl_components()

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

### Community 228 - "pastpapergen/cli.py"
Cohesion: 0.23
Nodes (11): BuildResult, _artifacts(), _build(), default_output_dir(), generate_package(), _load_rule(), main(), _normalise_paper_id() (+3 more)

### Community 229 - "enum"
Cohesion: 0.50
Nodes (4): full-paper, question-bank, enum, assessment_kind

### Community 230 - "blueprint_version"
Cohesion: 0.67
Nodes (3): minLength, type, blueprint_version

### Community 231 - "package"
Cohesion: 0.67
Nodes (3): pattern, type, package

### Community 232 - "generate_package"
Cohesion: 0.12
Nodes (26): extract_pdf_text(), Extract stable reading-order text without a Poppler CLI dependency., generate_package(), _logic_gate_names(), PaperBlueprint, Syllabus, validate_blueprint(), _validate_question_bank_identity() (+18 more)

### Community 233 - "subject_plugin"
Cohesion: 0.67
Nodes (3): subject_plugin, pattern, type

### Community 234 - "comparison_basis"
Cohesion: 0.67
Nodes (3): minLength, type, comparison_basis

### Community 235 - "family_id"
Cohesion: 0.67
Nodes (3): minLength, type, family_id

### Community 236 - "SubjectPlugin"
Cohesion: 0.21
Nodes (5): ContractSubjectPlugin, Any, Protocol, Safe baseline plugin for families with validation in their own contracts., SubjectPlugin

### Community 237 - "subject"
Cohesion: 0.67
Nodes (3): subject, pattern, type

### Community 238 - "ReportLabBackend"
Cohesion: 0.36
Nodes (5): LayoutPlan, RenderEvidence, Canvas, Path, ReportLabBackend

### Community 239 - "source_fingerprint"
Cohesion: 0.67
Nodes (3): source_fingerprint, pattern, type

### Community 240 - "cspapergen/ollama_client.py"
Cohesion: 0.10
Nodes (33): profile_for(), _align_paper1_structure(), _build_paper1_context(), _build_paper1_questions(), _paper1_part(), _paper1_question(), QuestionPart, Random (+25 more)

### Community 241 - "aqaaccountgen/generator.py"
Cohesion: 0.25
Nodes (13): _extract(), _gbp(), _gbp_decimal(), _levels(), _management_calculation(), _mcq(), _number(), Random (+5 more)

### Community 242 - "paper1_assets.py"
Cohesion: 0.44
Nodes (12): _supporting(), _page_footer(), _paragraph(), _practice_header(), Canvas, PaperBlueprint, Path, render_electronic_answer_document() (+4 more)

### Community 243 - "AnswerSpace"
Cohesion: 0.32
Nodes (9): AnswerSpace, QuestionBlock, RuleSet, test_every_component_has_deterministic_positive_geometry(), _document(), test_paginator_fails_fast_for_unsplittable_oversize_component(), test_paginator_keeps_heading_with_minimum_body_lines(), test_paginator_splits_answer_space_only_at_deterministic_line_boundary() (+1 more)

### Community 245 - "generate_package"
Cohesion: 0.29
Nodes (12): generate_package(), Path, page_count(), Path, test_both_packages_render_36_page_question_papers(), test_invalid_paper_is_rejected(), test_paper_one_mark_scheme_matches_reference_question_sequence(), test_paper_one_section_a_matches_measured_case_and_account_pages() (+4 more)

### Community 246 - "_draw_paper_3_source_page"
Cohesion: 0.38
Nodes (7): _draw_paper_3_bar_figure(), _draw_paper_3_extract(), _draw_paper_3_line_figure(), _draw_paper_3_series(), _draw_paper_3_source_page(), _draw_paper_3_table_figure(), _paper_3_values()

### Community 247 - "add_page_structure_tree"
Cohesion: 0.31
Nodes (9): add_page_structure_tree(), has_logical_page_order(), _has_structure_tree(), _new_object(), Document, Page, Path, Attach a deterministic page-level structure tree and marked content. Each page… (+1 more)

### Community 248 - "parse_model_recommendations"
Cohesion: 0.42
Nodes (8): OllamaModelTier, parse_model_recommendations(), Any, _required_text(), payload(), test_default_model_must_be_a_declared_recommendation(), test_recommendation_registry_is_contiguous_and_owns_cli_default(), test_recommendation_registry_rejects_memory_gaps()

### Community 249 - "aqaaccountgen/syllabus.py"
Cohesion: 0.28
Nodes (6): load_syllabus(), BaseModel, field_validator, Path, Syllabus, Topic

### Community 250 - "ChemistryPlugin"
Cohesion: 0.43
Nodes (3): ChemistryPlugin, Any, test_chemistry_rejects_an_unbalanced_canonical_equation()

### Community 251 - "cspapergen/cli.py"
Cohesion: 0.36
Nodes (5): _artifacts(), default_output_dir(), _improve(), main(), Path

### Community 254 - "validate_economics_causal_direction"
Cohesion: 0.40
Nodes (5): Reject common exchange-rate reversals before model review., validate_economics_causal_direction(), parametrize, test_economics_direction_validator_accepts_correct_import_effect(), test_economics_direction_validator_rejects_reversed_import_effects()

### Community 255 - "test_configured_family.py"
Cohesion: 0.80
Nodes (4): Path, _syllabus(), test_cambridge_computer_science_preview_covers_theory_and_practical_roles(), test_cambridge_economics_preview_covers_all_official_components()

## Knowledge Gaps
- **831 isolated node(s):** `BoardLayout`, `examforge-aqa-accounting`, `$schema`, `$id`, `title` (+826 more)
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

- **Why does `GeneratedQuestion` connect `GeneratedQuestion` to `Paragraph`, `ocregen/render_pdf.py`, `Table`, `AssessmentCheckpointStore`, `aqabizgen/generator.py`, `GeneratedPaper`, `aqaecongen/generator.py`, `aqaecongen/render_pdf.py`, `test_reference_demand.py`, `exam_blueprints.py`, `aqaaccountgen/generator.py`, `test_ocr_economics.py`, `ocrcsgen/generator.py`, `mark_scheme_enrichment.py`, `AssessmentContract`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Why does `load_builtin_paper_config()` connect `build_paper_blueprint` to `pastpapergen/cli.py`, `test_mark_scheme_layout.py`, `test_render_pdf.py`, `pastpapergen/ollama_client.py`, `test_ollama_generation.py`, `formatted_generation_date`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Why does `GeneratedPaper` connect `GeneratedPaper` to `Paragraph`, `ocregen/render_pdf.py`, `Table`, `AssessmentCheckpointStore`, `aqabizgen/generator.py`, `aqaecongen/generator.py`, `aqaecongen/render_pdf.py`, `test_reference_demand.py`, `exam_blueprints.py`, `aqaaccountgen/generator.py`, `test_ocr_computer_science.py`, `test_ocr_economics.py`, `ocrcsgen/generator.py`, `configuredgen/render_pdf.py`, `mark_scheme_enrichment.py`, `AssessmentContract`, `GeneratedQuestion`, `test_aqa_accounting.py`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `GeneratedQuestion` (e.g. with `AssessmentLLMClient` and `GenerationPolicy`) actually correct?**
  _`GeneratedQuestion` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `ApplicationCoordinator` (e.g. with `PaperCreator` and `.body`) actually correct?**
  _`ApplicationCoordinator` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `BoardLayout`, `examforge-aqa-accounting`, `$schema` to the rest of the system?**
  _831 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `cspapergen/render_pdf.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07500475918522749 - nodes in this community are weakly interconnected._