# Graph Report - Past Paper Creation  (2026-08-26)

## Corpus Check
- 302 files · ~518,087 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 4502 nodes · 12371 edges · 216 communities (164 shown, 52 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 732 edges (avg confidence: 0.68)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `83926012`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cspapergen/render_pdf.py
- validate_generator_migration.py
- ApplicationCoordinator
- Foundation
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
- pdf_validation.py
- test_ocr_economics.py
- live_generation_matrix.py
- formatted_generation_date
- benchmark.py
- AppDefaults
- mark_scheme_enrichment.py
- test_document_dsl.py
- CatalogStore
- render_pdf_atomically
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
- ocr_computer_science_calibration.py
- Approved-Improvement Traceability
- test_app_backend.py
- pastpapergen/notes.py
- ocrcsgen/generator.py
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
- _source_application_points
- AssessmentContract
- Q: How is the macOS backend bundle kept complete?
- File Structure
- reportlab_theme.py
- Text
- RecentDocumentStore
- cspapergen/ollama_client.py
- Rendering and Mark-Scheme Reliability Implementation Plan
- Architecture
- _draw_ms_row
- test_ollama_generation.py
- Glossy Black Fountain Pen App Icon Master
- pastpapergen/cli.py
- enum
- Assessment quality and originality
- test_aqa_accounting.py
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
- NonCurrentAssetCase
- generator_working_directory
- xcbuild.sh
- psychometrics.py
- capabilities
- cspapergen/generator.py
- BackendClient
- diagnose.sh
- move_to_trash.sh
- cspapergen/cli.py
- run_app_macos.sh
- String
- Core/__init__.py
- properties
- bootstrap_backend.sh
- build_backend.sh
- clean.sh
- resolve_agent_name.sh
- model_recommendations.py
- aqaaccountgen/__init__.py
- family_adapter.py
- aqabizgen/__init__.py
- cspapergen/__init__.py
- ocrcsgen/__init__.py
- aqaecongen/__init__.py
- pastpapergen/__init__.py
- ocregen/__init__.py
- tools/__init__.py
- graphify
- required
- BenchmarkCoordinator
- progress
- IncomeStatementCase
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
- render_source_booklet
- aqa_business_calibration.py
- DocumentPreviewView
- GeneratedQuestion
- PartnershipCase
- _draw_cover
- properties
- _call_name
- Q: How does the paper fidelity audit produce per-document and per-role scores, and where should release thresholds integrate?
- required
- event_id
- qualification_levels
- add_page_structure_tree
- CodingKeys
- required
- properties
- properties
- required
- aqaaccountgen/syllabus.py
- sample
- empirical-calibration.schema.json
- PaperBlueprint
- exam_blueprints.py
- required
- qualification-schema.json
- properties
- enum
- enum
- model
- .apply
- additionalProperties
- generator-capability.schema.json
- register_fonts
- tool_versions
- NotificationPresenter
- ocregen/syllabus.py
- aqaaccountgen/generator.py
- enum
- required
- backend_subject
- app_board
- app_subject
- board
- JobHistoryView
- required
- entry_point
- SettingsPane.swift
- test_repository_hygiene.py
- cspapergen/notes.py
- id
- board_profile
- CostingCase
- pastpapergen/render_pdf.py
- Current-family visual qualification — 26 August 2026
- properties
- SalesLedgerCase
- .baseQuery
- type
- timestamp
- _table_rows
- enum
- subject_plugin
- layouts.py
- README.md

## God Nodes (most connected - your core abstractions)
1. `GeneratedQuestion` - 189 edges
2. `build_paper_blueprint()` - 163 edges
3. `load_builtin_paper_config()` - 147 edges
4. `load_syllabus()` - 146 edges
5. `ApplicationCoordinator` - 137 edges
6. `Table` - 96 edges
7. `GeneratedOption` - 95 edges
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

## Communities (216 total, 52 thin omitted)

### Community 0 - "cspapergen/render_pdf.py"
Cohesion: 0.06
Nodes (112): _draw_aqa_footer(), _draw_aqa_page(), _draw_barcode(), draw_exam_page(), _draw_independent_notice(), _draw_ocr_notice(), _draw_ocr_page(), _draw_ocr_rules() (+104 more)

### Community 1 - "validate_generator_migration.py"
Cohesion: 0.06
Nodes (41): board_profile(), board_profile_ids(), BoardProfile, _normalise_identifier(), ContractSubjectPlugin, discover_subject_plugin(), _normalise_identifier(), Any (+33 more)

### Community 2 - "ApplicationCoordinator"
Cohesion: 0.04
Nodes (49): AnyCancellable, DateFormatter, .body, GeneratedFilesTable, .body, GeneratedFile, .exists, .paperDescription (+41 more)

### Community 3 - "Foundation"
Cohesion: 0.07
Nodes (23): Foundation, KeychainSecretStore, SecretStoring, Date, String, URL, SystemAppClock, .now (+15 more)

### Community 4 - "Paragraph"
Cohesion: 0.12
Nodes (66): Table, AQAAnswerLines, Paragraph, _accounting_marking_guidance_pages(), _accounting_system_case(), _accounting_table(), _additional_answer_page(), _appropriation_answer_table() (+58 more)

### Community 5 - "ocregen/render_pdf.py"
Cohesion: 0.08
Nodes (78): ExamPage, Flowable, A full-page shell that can also live inside a Platypus story., OCRAnswerLines, _add_economics_diagram(), _add_firm_objectives_diagram(), _add_ppf_diagram(), _annotation_conventions_page() (+70 more)

### Community 6 - "GeneratedPaper"
Cohesion: 0.11
Nodes (54): GeneratedPaper, aqa_front_matter_pages(), Flowable, _artifacts(), _additional_answer_page(), _ao_summary(), _assessment_objectives_page(), _banner() (+46 more)

### Community 7 - "test_render_pdf.py"
Cohesion: 0.14
Nodes (44): render_question_paper(), _answer_rule_count(), _blank_axis_lines(), _blueprint_with_section_a_question(), _dark_pixels(), _first_page_containing(), _normalised(), _pdf_page_count() (+36 more)

### Community 8 - "aqabizgen/generator.py"
Cohesion: 0.09
Nodes (35): generate_package(), Path, FinancialPosition, format_number(), Format an exam answer without meaningless trailing zeroes., The single source of truth for Paper 1 financial-statement figures., build_paper(), _extract() (+27 more)

### Community 9 - "pastpapergen/generator.py"
Cohesion: 0.06
Nodes (72): MultipleChoiceOption, _adapt_paper_three_case_guidance(), _best_section_a_context_point(), _build_part(), _build_parts(), _choice_group_name(), _choice_lookup(), _choose_topic() (+64 more)

### Community 10 - "build_paper_blueprint"
Cohesion: 0.08
Nodes (81): build_paper_blueprint(), PaperBlueprint, Syllabus, load_builtin_paper_config(), load_syllabus(), Path, Syllabus, test_blueprint_contains_structured_mcq_and_mark_scheme_content() (+73 more)

### Community 11 - "ocrcsgen/render_pdf.py"
Cohesion: 0.09
Nodes (48): aqa_question_cover(), CoverProfile, _draw_aqa_mark_scheme_cover(), _draw_cover_barcode(), draw_mark_scheme_cover(), _draw_ocr_mark_scheme_cover(), mark_scheme_cover(), MarkSchemeCover (+40 more)

### Community 12 - "paper_fidelity_audit.py"
Cohesion: 0.05
Nodes (103): Pixmap, parametrize, Path, test_compact_profile_omits_raster_geometry(), test_contact_sheets_make_visual_review_artifacts(), test_generated_document_falls_back_to_nested_transaction_output(), test_generated_document_supports_app_per_paper_directories(), test_metric_callout_names_print_resolution_comparison_dimensions() (+95 more)

### Community 13 - "reference_corpus.py"
Cohesion: 0.13
Nodes (45): MonkeyPatch, Path, test_document_path_requires_filename(), test_document_path_stays_inside_corpus(), test_download_manifest_records_failure_and_continues(), test_parse_aqa_resources_filters_modified_papers(), test_parse_ocr_resources_uses_a_level_tab_only(), test_parse_ocr_specifications_keeps_a_level_not_as_level() (+37 more)

### Community 14 - "aqaecongen/render_pdf.py"
Cohesion: 0.13
Nodes (42): _artifacts(), _assessment_objectives_table(), _context_data_table(), _context_first_page(), _context_second_page(), _cover(), _cover_profile(), _document() (+34 more)

### Community 15 - "test_coverage_matrix.py"
Cohesion: 0.07
Nodes (56): report(), test_both_papers_pass_multi_seed_automated_checks(), test_external_difficulty_gates_remain_false(), test_reference_evidence_is_aggregate_only(), family(), matrix(), Path, test_catalog_availability_is_owned_only_by_registry() (+48 more)

### Community 16 - "CodingKeys"
Cohesion: 0.04
Nodes (57): CodingKey, CodingKeys, backendVersion, capabilities, checks, code, command, cpuLoad (+49 more)

### Community 17 - "AssessmentCheckpointStore"
Cohesion: 0.14
Nodes (26): AssessmentCheckpointStore, CheckpointCorrupt, CheckpointIdentity, CheckpointMismatch, identity_for_blueprint(), Any, BaseModel, Path (+18 more)

### Community 18 - "pdf_validation.py"
Cohesion: 0.15
Nodes (28): compare_page_evidence(), _contrast_against_white(), _contrast_ratio(), _count_score(), _font_embedding(), _font_evidence(), _is_decorative_bleed(), _is_margin_furniture() (+20 more)

### Community 19 - "test_ocr_economics.py"
Cohesion: 0.16
Nodes (23): generate_package(), Path, build_paper(), Syllabus, Path, test_all_packages_render_reference_page_geometry(), test_business_objectives_use_cost_and_revenue_diagrams(), test_compact_guidance_terminates_when_generated_points_are_exhausted() (+15 more)

### Community 20 - "live_generation_matrix.py"
Cohesion: 0.08
Nodes (49): Release qualification evidence and policy models., ArtifactEvidence, EvidenceRecord, GateState, ModelIdentity, BaseModel, field_validator, Path (+41 more)

### Community 21 - "formatted_generation_date"
Cohesion: 0.12
Nodes (24): QuestionPaperCover, Fixed-grid, board-shaped front page without copying protected artwork., Return the renderer-neutral representation used for qualification., _wrap(), formatted_generation_date(), formatted_generation_series(), generation_date(), date (+16 more)

### Community 22 - "benchmark.py"
Cohesion: 0.12
Nodes (33): apple_cpu_core_split(), available_memory_gb(), avg(), clamp(), cpu_brand(), cpu_load_percent(), cpu_probe(), disk_probe() (+25 more)

### Community 23 - "AppDefaults"
Cohesion: 0.12
Nodes (10): AppDefaults, AppLinks, AppStorageKey, SecretAccount, Bool, String, URL, .mlxSetupExplanation (+2 more)

### Community 24 - "mark_scheme_enrichment.py"
Cohesion: 0.22
Nodes (20): _answer_form(), _application_label(), _clean_text(), _compact_technical_guidance(), _deduplicate(), enrich_paper(), _enrich_question(), _level_guidance() (+12 more)

### Community 25 - "test_document_dsl.py"
Cohesion: 0.07
Nodes (74): AnswerSpace, BaseComponent, BlankPage, Component, ContinuationPage, Cover, Diagram, Graph (+66 more)

### Community 26 - "CatalogStore"
Cohesion: 0.06
Nodes (36): SidebarItem, benchmark, documents, history, ContentView, .body, .columnVisibility, ContentViewPreview (+28 more)

### Community 27 - "render_pdf_atomically"
Cohesion: 0.15
Nodes (23): InvalidRenderOutput, Path, RuntimeError, A document role could not be rendered safely., Rendering exceeded its bounded qualification window., A renderer returned without producing a readable PDF., Render one PDF role under a deadline and promote it atomically., _readable_page_count() (+15 more)

### Community 28 - "assessment_package.py"
Cohesion: 0.06
Nodes (70): _assessment_contract(), AssessmentPackageCompatibilityError, _contains_non_finite(), _evidence_ids(), _extract_items(), _form_id(), _level_policies(), load_assessment_package() (+62 more)

### Community 29 - "BackendEvent"
Cohesion: 0.06
Nodes (25): BackendEvent, benchmarkDone, benchmarkMetric, benchmarkSample, done, error, file, hello (+17 more)

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
Cohesion: 0.09
Nodes (40): MultipleChoiceOption, PaperBlueprint, PaperConfig, BaseModel, QuestionBlueprint, QuestionPart, SectionConfig, Syllabus (+32 more)

### Community 34 - "generation.py"
Cohesion: 0.21
Nodes (21): progress_emitter(), _atomic_publish(), _cancel_generation(), checkpoint_path_for_job(), emit_generated_files(), finalize_generated_documents(), GenerationCancelled, _generator_version() (+13 more)

### Community 35 - "generate_package"
Cohesion: 0.17
Nodes (19): extract_pdf_text(), Extract stable reading-order text without a Poppler CLI dependency., generate_package(), test_final_additional_answer_page_reserves_independent_notice(), test_generate_package_writes_rendered_and_assessment_outputs(), test_generated_pdfs_are_a4(), test_paper_two_transition_leaf_uses_do_not_write_diagonal(), test_question_cover_includes_the_independent_wordmark() (+11 more)

### Community 36 - "properties"
Cohesion: 0.09
Nodes (23): type, minLength, type, const, pattern, type, properties, advertised (+15 more)

### Community 37 - "ocr_economics_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 38 - "test_mark_scheme_layout.py"
Cohesion: 0.17
Nodes (32): pdf_font_names(), Path, Return the font families actually used by visible text spans., _cleanup_graph_cache(), _mark_scheme_rows(), Syllabus, render_mark_scheme(), _blueprint_with_section_a_calculation() (+24 more)

### Community 39 - "ocr_computer_science_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_difficulty_remains_external_evidence_gated(), test_multi_seed_structural_demand_passes(), test_reference_evidence_is_aggregate_only(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 40 - "Approved-Improvement Traceability"
Cohesion: 0.07
Nodes (26): Approved-Improvement Traceability, Current-Paper Gate, Expansion Gate, Foundation Gate, Global Constraints, Paper Creator Excellence Programme Implementation Plan, Phase Completion Gates, Plan Verification Checklist (+18 more)

### Community 41 - "test_app_backend.py"
Cohesion: 0.16
Nodes (28): _safe_provider_detail(), CaptureFixture, CompletedProcess, Path, run_bridge(), run_bridge_raw(), test_aqa_accounting_all_papers_generate_expected_files(), test_aqa_business_all_papers_generate_expected_files() (+20 more)

### Community 42 - "pastpapergen/notes.py"
Cohesion: 0.20
Nodes (19): _clean_chunk(), essay_capable_topic_ids(), _flush_note_chunk(), _is_exam_point(), _is_note_noise(), _looks_like_heading(), _note_chunks(), note_context_for_topic() (+11 more)

### Community 43 - "ocrcsgen/generator.py"
Cohesion: 0.21
Nodes (15): _analysis_prompt(), _levels(), _programming_prompt(), _programming_scheme(), Random, Topic, _question(), _representation_calculation() (+7 more)

### Community 44 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Measured Paper Fidelity Implementation Plan, Task 1: Page-role-aware fidelity evidence, Task 2: Shared board answer-page geometry, Task 3: OCR response and blank-page grammar, Task 4: Shared mark-scheme cover calibration, Task 5: Full visual qualification and regression gate

### Community 45 - "load_syllabus"
Cohesion: 0.09
Nodes (53): build_paper1_blueprint(), build_paper2_blueprint(), PaperBlueprint, Syllabus, improve_questions_with_ollama(), Syllabus, load_syllabus(), Path (+45 more)

### Community 46 - "test_mlx_setup.py"
Cohesion: 0.10
Nodes (39): _available_cache_bytes(), ensure_mlx_ready(), handle_setup_mlx(), install_mlx_runtime(), is_managed_development_environment(), load_mlx_model(), mlx_runtime_available(), MLXModelSetupRequired (+31 more)

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
Cohesion: 0.20
Nodes (20): build_parser(), handle_bundle_check(), main(), ArgumentParser, Namespace, Fail fast when a packaged backend is missing a dynamic generator., emit(), emit_progress() (+12 more)

### Community 56 - "generator_registry.py"
Cohesion: 0.23
Nodes (15): _capability(), generator_capabilities(), generator_subjects(), _paper_qualification(), PaperQualification, Any, _relative_path(), test_backend_bundle_script_is_registry_driven() (+7 more)

### Community 57 - "properties"
Cohesion: 0.14
Nodes (14): type, type, type, type, properties, backend_version, code, job_id (+6 more)

### Community 58 - "_source_application_points"
Cohesion: 0.14
Nodes (24): _brief_source_evidence(), _calculation_answer_lines(), _normalise_mark_point(), _one_mark_points(), _paper_one_fifteen_mark_scheme_lines(), _paper_one_five_mark_diagram_lines(), _paper_one_section_a_mark_scheme_lines(), _paper_two_extended_mark_scheme_lines() (+16 more)

### Community 59 - "AssessmentContract"
Cohesion: 0.07
Nodes (54): AssessmentContract, contract_for_question(), GeneratedNumericField, GraphContract, _numeric_contracts(), NumericRole, NumericValueContract, Any (+46 more)

### Community 60 - "Q: How is the macOS backend bundle kept complete?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: How is the macOS backend bundle kept complete?, Source Nodes

### Community 61 - "File Structure"
Cohesion: 0.17
Nodes (11): Assessment Reliability Core Implementation Plan, File Structure, Global Constraints, Subsequent Phase Plans, Task 1: Typed Item Contracts, Task 2: Role-Aware Numeric and Evidence Validation, Task 3: Item-Scoped Draft, Review, and Repair, Task 4: Atomic Checkpoints and Resume (+3 more)

### Community 62 - "reportlab_theme.py"
Cohesion: 0.14
Nodes (9): AnswerLineFlowable, AQACompactAnswerLines, Flowable, Return a Table subclass whose raw string cells use the controlled font.…, Shared, measured answer-line primitive used by every board renderer., themed_table_class(), TableType, test_board_answer_line_presets_own_repeated_renderer_geometry() (+1 more)

### Community 63 - "Text"
Cohesion: 0.04
Nodes (95): CaseIterable, Charts, Color, View, PanelEmptyState, .body, String, HelpTopic (+87 more)

### Community 64 - "RecentDocumentStore"
Cohesion: 0.05
Nodes (44): Codable, Equatable, FileManager, GenerationJobState, LocalizedError, ProgressEntry, AppClock, GenerationCoordinator (+36 more)

### Community 65 - "cspapergen/ollama_client.py"
Cohesion: 0.16
Nodes (20): numeric_tokens(), Extract quantities exactly enough to catch broken data/source rewrites., assert_materially_new(), independent_review(), JSONClient, Any, Protocol, require_independent_review() (+12 more)

### Community 66 - "Rendering and Mark-Scheme Reliability Implementation Plan"
Cohesion: 0.25
Nodes (7): Rendering and Mark-Scheme Reliability Implementation Plan, Task 1: Bounded atomic render transactions, Task 2: Route every generator family through the transaction, Task 3: Artifact containment, collision, and density evidence, Task 4: Mark-scheme depth contracts, Task 5: OCR Economics pagination regression, Task 6: Phase qualification

### Community 67 - "Architecture"
Cohesion: 0.18
Nodes (10): Architecture, Canonical registry, Extension contract, Failure containment, Fidelity qualification boundary, Package transaction, PDF portability and accessibility, Product boundary (+2 more)

### Community 68 - "_draw_ms_row"
Cohesion: 0.43
Nodes (7): _draw_ms_row(), _ms_bold_line(), _ms_centered_line(), _ms_italic_line(), _ms_row_height(), _ms_wrap_width(), _split_mark_scheme_row()

### Community 69 - "test_ollama_generation.py"
Cohesion: 0.14
Nodes (30): _improve(), generate_questions_with_ollama(), _merge_source_text(), PaperBlueprint, Syllabus, _validate_ai_question(), BlueprintAwareClient, EmptyClient (+22 more)

### Community 70 - "Glossy Black Fountain Pen App Icon Master"
Cohesion: 0.18
Nodes (11): Glossy Black Fountain Pen App Icon Master, Paper Creator App Icon AppIcon-128x128@1x, Paper Creator App Icon AppIcon-128x128@2x, Paper Creator App Icon AppIcon-16x16@1x, Paper Creator App Icon AppIcon-16x16@2x, Paper Creator App Icon AppIcon-256x256@1x, Paper Creator App Icon AppIcon-256x256@2x, Paper Creator App Icon AppIcon-32x32@1x (+3 more)

### Community 71 - "pastpapergen/cli.py"
Cohesion: 0.24
Nodes (10): _artifacts(), _build(), default_output_dir(), generate_package(), _load_rule(), main(), _normalise_paper_id(), Path (+2 more)

### Community 72 - "enum"
Cohesion: 0.18
Nodes (11): benchmark_done, benchmark_metric, benchmark_sample, done, error, file, hello, models (+3 more)

### Community 73 - "Assessment quality and originality"
Cohesion: 0.17
Nodes (11): Assessment quality and originality, Difficulty claims, Human release review, Independent solution and response-band qualification, Item transactions and two-pass generation, Mark-scheme quality, Measured visual qualification, Novelty and exposure (+3 more)

### Community 74 - "test_aqa_accounting.py"
Cohesion: 0.37
Nodes (12): generate_package(), Path, page_count(), Path, test_both_packages_render_36_page_question_papers(), test_invalid_paper_is_rejected(), test_non_current_asset_question_and_mark_scheme_use_the_same_figures(), test_paper_one_mark_scheme_matches_reference_question_sequence() (+4 more)

### Community 75 - "macOS interaction and HIG compliance"
Cohesion: 0.22
Nodes (8): Accessibility verification, Commands and state, File workflow, Geometry and visual language, Information architecture, macOS interaction and HIG compliance, Onboarding and help, Settings

### Community 76 - "Rect"
Cohesion: 0.10
Nodes (32): conform_generated_documents(), Path, _clamp_fitz_rect(), conform_pdf_page_boxes(), conform_pdf_to_box_template(), draw_text_slot(), _fitz_rect_close(), LayoutConformanceError (+24 more)

### Community 77 - "test_pdf_validation.py"
Cohesion: 0.15
Nodes (29): extract_pdf_evidence(), GlyphMetric, _overlapping_text_pairs(), Counter, Path, Fail closed on malformed, substituted, annotated, or low-resolution PDFs., A compact, serialisable sample of one rendered PDF glyph., Extract print and accessibility evidence without retaining source prose. Glyph… (+21 more)

### Community 78 - "Q: how can we make even more improvements to get the highest similarity in terms of structure and layout and quality of questions etc. and maybe all of the files in the project can be better organised. and the UI can be made to be much better and more geometrically apple-like by strictly following every single rule they outline in their HIG"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: how can we make even more improvements to get the highest similarity in terms of structure and layout and quality of questions etc. and maybe all of the files in the project can be better organised. and the UI can be made to be much better and more geometrically apple-like by strictly following every single rule they outline in their HIG, Source Nodes

### Community 79 - "Paper creator"
Cohesion: 0.25
Nodes (8): Architecture and quality analysis, Build Checks, CLI, Development Reference Corpus, Paper creator, Privacy, Run, Structure

### Community 80 - "independent_solver.py"
Cohesion: 0.12
Nodes (36): _independently_validate_candidate(), EvidenceRecord, _as_mapping(), CanonicalSolution, _concept_coverage(), _concept_tokens(), _format_number(), IndependentSolver (+28 more)

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
Cohesion: 0.29
Nodes (6): additionalProperties, allOf, $id, $schema, title, type

### Community 85 - "properties"
Cohesion: 0.11
Nodes (19): type, pattern, type, minLength, type, minLength, type, minLength (+11 more)

### Community 86 - "NonCurrentAssetCase"
Cohesion: 0.15
Nodes (3): _nearest_hundred(), NonCurrentAssetCase, test_non_current_asset_question_and_scheme_share_verified_case_data()

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
Cohesion: 0.11
Nodes (23): _align_paper1_structure(), _build_paper1_context(), _build_paper1_questions(), _paper1_part(), _paper1_question(), _paper2_marking_checks(), QuestionPart, Random (+15 more)

### Community 92 - "BackendClient"
Cohesion: 0.17
Nodes (14): BackendClient, BackendClientError, backendMissing, .errorDescription, pythonMissing, pythonVenvUnreadable, BackendFile, LaunchConfiguration (+6 more)

### Community 95 - "cspapergen/cli.py"
Cohesion: 0.23
Nodes (9): BuildResult, type, path, _artifacts(), _build(), default_output_dir(), _improve(), main() (+1 more)

### Community 97 - "String"
Cohesion: 0.05
Nodes (76): Decodable, Hashable, Identifiable, AIProvider, anthropic, apple, .backendID, .id (+68 more)

### Community 99 - "properties"
Cohesion: 0.13
Nodes (15): type, properties, type, type, type, type, type, type (+7 more)

### Community 101 - "build_backend.sh"
Cohesion: 0.29
Nodes (5): MPLCONFIGDIR, PYINSTALLER_CONFIG_DIR, PYTHONPATH, build_backend.sh script, XDG_CACHE_HOME

### Community 104 - "model_recommendations.py"
Cohesion: 0.36
Nodes (10): model_recommendations(), OllamaModelRecommendations, OllamaModelTier, parse_model_recommendations(), Any, _required_text(), payload(), test_default_model_must_be_a_declared_recommendation() (+2 more)

### Community 106 - "family_adapter.py"
Cohesion: 0.25
Nodes (11): ArtifactSpec, FamilyAdapter, Path, run_family_adapter(), default_ollama_model(), ProgressCallback, _artifacts(), generate_package() (+3 more)

### Community 115 - "required"
Cohesion: 0.17
Nodes (13): differential_item_functioning, discrimination, facility, item_id, median_time_seconds, responses, items, items (+5 more)

### Community 116 - "BenchmarkCoordinator"
Cohesion: 0.09
Nodes (25): KeyPath, BenchmarkSample, .networkLatencyDisplayMS, .thermalSpeedLimitDisplayPercent, BenchmarkChart, BenchmarkLiveCharts, .body, .cpuChart (+17 more)

### Community 117 - "progress"
Cohesion: 0.50
Nodes (4): maximum, minimum, type, progress

### Community 130 - "required"
Cohesion: 0.18
Nodes (11): candidate_sample, facility_range, group_fairness_screen, independent_manual_review, internal_consistency, item_coverage, marker_standardisation, additionalProperties (+3 more)

### Community 152 - "render_source_booklet"
Cohesion: 0.28
Nodes (15): _apply_edexcel_page_boxes(), _extract_source_questions(), Path, Match Pearson question-paper bleed and crop boxes without changing A4 content., render_source_booklet(), _source_sections(), _pdf_page_count(), _pdf_text() (+7 more)

### Community 153 - "aqa_business_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 154 - "DocumentPreviewView"
Cohesion: 0.07
Nodes (26): AppKit, Combine, DocumentPreviewView, .body, .exportAlertBinding, .provenanceRecord, .selectedBinding, .selectedFile (+18 more)

### Community 155 - "GeneratedQuestion"
Cohesion: 0.08
Nodes (94): AssessmentLLMClient, _batches_for_client(), _bounded_text(), _candidate_question(), _canonical_objective_allocation(), _clean_generated_prompt(), _contains_command_word(), _effective_batch_size() (+86 more)

### Community 157 - "_draw_cover"
Cohesion: 0.14
Nodes (20): economics_exam_schedule(), ExamSchedule, formatted_economics_exam_date(), date, _draw_boxes(), _draw_cover(), _draw_crop_marks(), _draw_fake_barcode() (+12 more)

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

### Community 162 - "event_id"
Cohesion: 0.67
Nodes (3): minimum, type, event_id

### Community 163 - "qualification_levels"
Cohesion: 0.29
Nodes (7): empirically_calibrated, engineering_validated, visually_calibrated, qualification_levels, additionalProperties, required, type

### Community 164 - "add_page_structure_tree"
Cohesion: 0.31
Nodes (9): add_page_structure_tree(), has_logical_page_order(), _has_structure_tree(), _new_object(), Document, Page, Path, Attach a deterministic page-level structure tree and marked content. Each page… (+1 more)

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

### Community 170 - "aqaaccountgen/syllabus.py"
Cohesion: 0.28
Nodes (6): load_syllabus(), BaseModel, field_validator, Path, Syllabus, Topic

### Community 171 - "sample"
Cohesion: 0.25
Nodes (8): candidates, groups, items, response_rows, sample, additionalProperties, required, type

### Community 172 - "empirical-calibration.schema.json"
Cohesion: 0.25
Nodes (7): additionalProperties, $id, not, anyOf, $schema, title, type

### Community 173 - "PaperBlueprint"
Cohesion: 0.20
Nodes (21): _count_pages(), _draw_answer_page_header(), _draw_centred_instruction_line(), _draw_continuation_lines(), _draw_formula_appendix(), _draw_paper_3_choice_header(), _draw_paper_3_pages(), _draw_question_footer() (+13 more)

### Community 174 - "exam_blueprints.py"
Cohesion: 0.07
Nodes (68): _demand_band(), GeneratedSection, _hydrate_assessment_metadata(), _objective_allocation(), PaperRule, _prompt_uses_command_word(), BaseModel, QuestionRule (+60 more)

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

### Community 181 - ".apply"
Cohesion: 0.17
Nodes (9): MLXRecoveryState, OllamaState, ModelCoordinator, .modelOptions, .recommendation, Bool, Date, String (+1 more)

### Community 182 - "additionalProperties"
Cohesion: 0.13
Nodes (15): items, minItems, type, uniqueItems, items, minItems, type, uniqueItems (+7 more)

### Community 183 - "generator-capability.schema.json"
Cohesion: 0.17
Nodes (11): additionalProperties, $defs, safePath, $id, pattern, minLength, not, type (+3 more)

### Community 184 - "register_fonts"
Cohesion: 0.43
Nodes (6): register_font(), register_fonts(), _standard_fallback(), ParagraphStyle, test_fallback_family_supports_bold_paragraph_markup(), test_missing_font_uses_registered_standard_font_alias()

### Community 185 - "tool_versions"
Cohesion: 0.50
Nodes (4): type, tool_versions, additionalProperties, type

### Community 186 - "NotificationPresenter"
Cohesion: 0.25
Nodes (6): NotificationPresenter, NSObject, UNNotification, UNNotificationPresentationOptions, UNUserNotificationCenter, UNUserNotificationCenterDelegate

### Community 187 - "ocregen/syllabus.py"
Cohesion: 0.38
Nodes (5): load_syllabus(), BaseModel, Path, Syllabus, Topic

### Community 188 - "aqaaccountgen/generator.py"
Cohesion: 0.20
Nodes (17): build_paper(), _extract(), _levels(), _management_calculation(), _mcq(), _number(), Random, Syllabus (+9 more)

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

### Community 196 - "required"
Cohesion: 0.33
Nodes (6): event_id, job_id, protocol, timestamp, type, required

### Community 197 - "entry_point"
Cohesion: 0.67
Nodes (3): pattern, type, entry_point

### Community 198 - "SettingsPane.swift"
Cohesion: 0.09
Nodes (21): App, Commands, AppCommands, PaperCreator, .body, AISettingsTab, PrivacySettingsTab, .body (+13 more)

### Community 199 - "test_repository_hygiene.py"
Cohesion: 0.30
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

### Community 204 - "pastpapergen/render_pdf.py"
Cohesion: 0.09
Nodes (62): GraphParams, _answer_line_count(), _axis_labels_for_draw_prompt(), _bar_chart_data(), _bar_label(), _draw_answer_lines(), _draw_answer_lines_until(), _draw_axis_arrow() (+54 more)

### Community 205 - "Current-family visual qualification — 26 August 2026"
Cohesion: 0.29
Nodes (6): Automated evidence, Current-family visual qualification — 26 August 2026, Evidence locations, Manual review, Outstanding non-visual gates, Scope and claim

### Community 206 - "properties"
Cohesion: 0.29
Nodes (7): type, type, empirically_calibrated, engineering_validated, visually_calibrated, properties, type

### Community 208 - ".baseQuery"
Cohesion: 0.39
Nodes (4): SecretStore, Any, String, Security

### Community 209 - "type"
Cohesion: 0.50
Nodes (4): null, string, stage, type

### Community 210 - "timestamp"
Cohesion: 0.67
Nodes (3): timestamp, format, type

### Community 211 - "_table_rows"
Cohesion: 0.67
Nodes (3): _table_rows(), table_rows(), test_new_section_a_visual_stimuli_have_renderer_rows()

### Community 212 - "enum"
Cohesion: 0.50
Nodes (4): ai-assisted, deterministic, enum, content_mode

### Community 213 - "subject_plugin"
Cohesion: 0.67
Nodes (3): subject_plugin, pattern, type

## Knowledge Gaps
- **710 isolated node(s):** `BoardLayout`, `examforge-aqa-accounting`, `$schema`, `$id`, `title` (+705 more)
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

- **Why does `GeneratedQuestion` connect `GeneratedQuestion` to `Paragraph`, `ocregen/render_pdf.py`, `GeneratedPaper`, `aqabizgen/generator.py`, `ocrcsgen/generator.py`, `ocrcsgen/render_pdf.py`, `exam_blueprints.py`, `aqaecongen/render_pdf.py`, `independent_solver.py`, `AssessmentCheckpointStore`, `mark_scheme_enrichment.py`, `AssessmentContract`, `aqaaccountgen/generator.py`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Why does `formatted_generation_date()` connect `formatted_generation_date` to `cspapergen/render_pdf.py`, `generate_package`, `GeneratedPaper`, `test_mark_scheme_layout.py`, `test_render_pdf.py`, `ocrcsgen/render_pdf.py`, `pastpapergen/render_pdf.py`, `aqaecongen/render_pdf.py`, `render_source_booklet`, `_draw_cover`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Why does `DocumentRole` connect `test_document_dsl.py` to `cspapergen/render_pdf.py`, `Paragraph`, `ocregen/render_pdf.py`, `GeneratedPaper`, `ocrcsgen/render_pdf.py`, `pastpapergen/render_pdf.py`, `aqaecongen/render_pdf.py`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `GeneratedQuestion` (e.g. with `AssessmentLLMClient` and `GenerationPolicy`) actually correct?**
  _`GeneratedQuestion` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 124 inferred relationships involving `Paragraph` (e.g. with `aqa_front_matter_pages()` and `_accounting_marking_guidance_pages()`) actually correct?**
  _`Paragraph` has 124 INFERRED edges - model-reasoned connections that need verification._
- **What connects `BoardLayout`, `examforge-aqa-accounting`, `$schema` to the rest of the system?**
  _710 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `cspapergen/render_pdf.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06288515406162465 - nodes in this community are weakly interconnected._