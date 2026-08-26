# Graph Report - Past Paper Creation  (2026-08-26)

## Corpus Check
- 321 files · ~524,013 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 4698 nodes · 12807 edges · 211 communities (162 shown, 49 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 755 edges (avg confidence: 0.67)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `32ea770d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cspapergen/render_pdf.py
- paths.py
- ApplicationCoordinator
- ModelCoordinator
- aqaaccountgen/render_pdf.py
- ocregen/render_pdf.py
- aqabizgen/render_pdf.py
- test_render_pdf.py
- aqabizgen/generator.py
- pastpapergen/generator.py
- build_paper_blueprint
- Paragraph
- paper_fidelity_audit.py
- reference_corpus.py
- aqaecongen/render_pdf.py
- test_coverage_matrix.py
- CodingKeys
- AssessmentCheckpointStore
- pdf_validation.py
- test_ocr_economics.py
- live_generation_matrix.py
- pastpapergen/cli.py
- benchmark.py
- family_adapter.py
- mark_scheme_enrichment.py
- test_document_dsl.py
- CatalogStore
- CoverProfile
- assessment_package.py
- String
- Paper creator: deep project analysis
- Q: Which Ollama model and live validation path does the project use for all supported papers?
- graphs.py
- mathematics.py
- generation.py
- cspapergen/cli.py
- properties
- render_pdf_atomically
- test_mark_scheme_layout.py
- HelpTopic
- Approved-Improvement Traceability
- test_app_backend.py
- pastpapergen/notes.py
- GeneratedPaper
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
- ExamPageProfile
- emit
- generator_registry.py
- properties
- _mark_scheme_rows
- AssessmentContract
- Q: How is the macOS backend bundle kept complete?
- File Structure
- aqa_accounting_calibration.py
- Text
- RecentDocumentStore
- ocr_economics_calibration.py
- Rendering and Mark-Scheme Reliability Implementation Plan
- Architecture
- pastpapergen/render_pdf.py
- test_ollama_generation.py
- Glossy Black Fountain Pen App Icon Master
- pastpapergen/ollama_client.py
- enum
- Assessment quality and originality
- ContentView
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
- model_review.py
- BackendEvent
- diagnose.sh
- move_to_trash.sh
- inspect_release_compliance
- run_app_macos.sh
- test_generator_migration.py
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
- Question
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
- .initialEstimate
- DocumentPreviewView
- GeneratedQuestion
- PartnershipCase
- render_source_booklet
- properties
- _call_name
- Q: How does the paper fidelity audit produce per-document and per-role scores, and where should release thresholds integrate?
- required
- aqa_business_calibration.py
- qualification_levels
- AppDefaults
- paper1_assets.py
- required
- properties
- generation_date.py
- required
- ComputerSciencePlugin
- sample
- empirical-calibration.schema.json
- PaperBlueprint
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
- test_source_booklet.py
- tool_versions
- required
- add_page_structure_tree
- aqaaccountgen/generator.py
- enum
- required
- backend_subject
- app_board
- app_subject
- board
- JobHistoryView
- GlyphMetric
- entry_point
- test_repository_hygiene.py
- id
- subject_plugins.py
- SubjectValidation
- Canvas
- Current-family visual qualification — 26 August 2026
- .baseQuery
- generate_package
- EssaySubjectPlugin
- enum
- README.md
- subject_plugin
- subjects/__init__.py

## God Nodes (most connected - your core abstractions)
1. `GeneratedQuestion` - 186 edges
2. `build_paper_blueprint()` - 163 edges
3. `load_builtin_paper_config()` - 147 edges
4. `load_syllabus()` - 146 edges
5. `ApplicationCoordinator` - 137 edges
6. `GeneratedOption` - 95 edges
7. `Table` - 92 edges
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

## Communities (211 total, 49 thin omitted)

### Community 0 - "cspapergen/render_pdf.py"
Cohesion: 0.10
Nodes (80): _answer_line_count(), _answer_lines(), _answer_lines_paginated(), _candidate_fields(), _continuation_guidance_lines(), _cover_page(), _cover_section(), _draw_adjacency_matrix_answers() (+72 more)

### Community 1 - "paths.py"
Cohesion: 0.18
Nodes (13): board_profile(), BoardProfile, _normalise_identifier(), build_parser(), _layout_board(), main(), MigrationIssue, MigrationReport (+5 more)

### Community 2 - "ApplicationCoordinator"
Cohesion: 0.03
Nodes (57): AnyCancellable, DateFormatter, .body, GeneratedFilesTable, .body, GeneratedFile, .exists, .paperDescription (+49 more)

### Community 3 - "ModelCoordinator"
Cohesion: 0.05
Nodes (33): Foundation, EstimateTuning, AppClock, KeychainSecretStore, SecretStoring, Date, String, URL (+25 more)

### Community 4 - "aqaaccountgen/render_pdf.py"
Cohesion: 0.11
Nodes (52): AQAAnswerLines, _levels(), _management_calculation(), Topic, Build a complete, internally solved data contract for each numeric task., _written(), _accounting_marking_guidance_pages(), _additional_answer_page() (+44 more)

### Community 5 - "ocregen/render_pdf.py"
Cohesion: 0.08
Nodes (73): OCRAnswerLines, _artifacts(), _add_economics_diagram(), _add_firm_objectives_diagram(), _add_ppf_diagram(), _annotation_conventions_page(), _answer_mark(), _assessment_objectives_guidance_page() (+65 more)

### Community 6 - "aqabizgen/render_pdf.py"
Cohesion: 0.11
Nodes (51): aqa_front_matter_pages(), Flowable, _artifacts(), _additional_answer_page(), _ao_summary(), _assessment_objectives_page(), _banner(), _break_even_diagram() (+43 more)

### Community 7 - "test_render_pdf.py"
Cohesion: 0.12
Nodes (48): _apply_edexcel_page_boxes(), _cleanup_graph_cache(), Path, Match Pearson question-paper bleed and crop boxes without changing A4 content., render_question_paper(), _answer_rule_count(), _blank_axis_lines(), _blueprint_with_section_a_question() (+40 more)

### Community 8 - "aqabizgen/generator.py"
Cohesion: 0.09
Nodes (35): generate_package(), Path, FinancialPosition, format_number(), Format an exam answer without meaningless trailing zeroes., The single source of truth for Paper 1 financial-statement figures., build_paper(), _extract() (+27 more)

### Community 9 - "pastpapergen/generator.py"
Cohesion: 0.06
Nodes (71): MultipleChoiceOption, _adapt_paper_three_case_guidance(), _best_section_a_context_point(), _build_part(), _build_parts(), _choice_group_name(), _choice_lookup(), _choose_topic() (+63 more)

### Community 10 - "build_paper_blueprint"
Cohesion: 0.09
Nodes (76): build_paper_blueprint(), PaperBlueprint, Syllabus, load_builtin_paper_config(), line_chart_data(), load_syllabus(), Path, Syllabus (+68 more)

### Community 11 - "Paragraph"
Cohesion: 0.12
Nodes (52): Table, OCRComputerScienceAnswerLines, Paragraph, _accounting_system_case(), _accounting_table(), _appropriation_answer_table(), _banner(), _company_statement_case() (+44 more)

### Community 12 - "paper_fidelity_audit.py"
Cohesion: 0.05
Nodes (103): Pixmap, parametrize, Path, test_compact_profile_omits_raster_geometry(), test_contact_sheets_make_visual_review_artifacts(), test_generated_document_falls_back_to_nested_transaction_output(), test_generated_document_supports_app_per_paper_directories(), test_metric_callout_names_print_resolution_comparison_dimensions() (+95 more)

### Community 13 - "reference_corpus.py"
Cohesion: 0.13
Nodes (45): MonkeyPatch, Path, test_document_path_requires_filename(), test_document_path_stays_inside_corpus(), test_download_manifest_records_failure_and_continues(), test_parse_aqa_resources_filters_modified_papers(), test_parse_ocr_resources_uses_a_level_tab_only(), test_parse_ocr_specifications_keeps_a_level_not_as_level() (+37 more)

### Community 14 - "aqaecongen/render_pdf.py"
Cohesion: 0.09
Nodes (46): AnswerLineFlowable, AQACompactAnswerLines, Flowable, Return a Table subclass whose raw string cells use the controlled font.…, Shared, measured answer-line primitive used by every board renderer., themed_table_class(), _artifacts(), _assessment_objectives_table() (+38 more)

### Community 15 - "test_coverage_matrix.py"
Cohesion: 0.07
Nodes (56): family(), matrix(), Path, test_catalog_availability_is_owned_only_by_registry(), test_checked_in_matrix_is_deterministic_and_current(), test_existing_generators_are_reported_without_false_verification(), test_matrix_exactly_covers_layout_profiles(), test_no_verified_paper_has_a_failed_gate() (+48 more)

### Community 16 - "CodingKeys"
Cohesion: 0.04
Nodes (56): CodingKey, CodingKeys, backendVersion, capabilities, checks, code, command, cpuLoad (+48 more)

### Community 17 - "AssessmentCheckpointStore"
Cohesion: 0.09
Nodes (42): AssessmentCheckpointStore, CheckpointCorrupt, CheckpointIdentity, CheckpointMismatch, identity_for_blueprint(), Any, BaseModel, Path (+34 more)

### Community 18 - "pdf_validation.py"
Cohesion: 0.12
Nodes (32): compare_page_evidence(), _contrast_against_white(), _contrast_ratio(), _count_score(), _font_embedding(), _font_evidence(), _is_decorative_bleed(), _is_margin_furniture() (+24 more)

### Community 19 - "test_ocr_economics.py"
Cohesion: 0.10
Nodes (37): generate_package(), Path, build_paper(), _evaluation_scheme(), _extract(), _extract_number(), _instructions(), _mcq() (+29 more)

### Community 20 - "live_generation_matrix.py"
Cohesion: 0.08
Nodes (49): Release qualification evidence and policy models., ArtifactEvidence, EvidenceRecord, GateState, ModelIdentity, BaseModel, field_validator, Path (+41 more)

### Community 21 - "pastpapergen/cli.py"
Cohesion: 0.14
Nodes (16): _artifacts(), _build(), _improve(), _load_rule(), _normalise_paper_id(), PaperBlueprint, Syllabus, _reject_mark_text() (+8 more)

### Community 22 - "benchmark.py"
Cohesion: 0.12
Nodes (33): apple_cpu_core_split(), available_memory_gb(), avg(), clamp(), cpu_brand(), cpu_load_percent(), cpu_probe(), disk_probe() (+25 more)

### Community 23 - "family_adapter.py"
Cohesion: 0.17
Nodes (21): ArtifactSpec, FamilyAdapter, Path, run_family_adapter(), default_ollama_model(), model_recommendations(), OllamaModelRecommendations, OllamaModelTier (+13 more)

### Community 24 - "mark_scheme_enrichment.py"
Cohesion: 0.22
Nodes (20): _answer_form(), _application_label(), _clean_text(), _compact_technical_guidance(), _deduplicate(), enrich_paper(), _enrich_question(), _level_guidance() (+12 more)

### Community 25 - "test_document_dsl.py"
Cohesion: 0.07
Nodes (75): AnswerSpace, BaseComponent, BlankPage, Component, ContinuationPage, Cover, Diagram, Graph (+67 more)

### Community 26 - "CatalogStore"
Cohesion: 0.07
Nodes (30): CatalogSubject, SidebarItem, benchmark, board, documents, history, BoardRow, .body (+22 more)

### Community 27 - "CoverProfile"
Cohesion: 0.10
Nodes (26): aqa_question_cover(), CoverProfile, _draw_aqa_mark_scheme_cover(), _draw_cover_barcode(), draw_mark_scheme_cover(), _draw_ocr_mark_scheme_cover(), mark_scheme_cover(), MarkSchemeCover (+18 more)

### Community 28 - "assessment_package.py"
Cohesion: 0.06
Nodes (70): _assessment_contract(), AssessmentPackageCompatibilityError, _contains_non_finite(), _evidence_ids(), _extract_items(), _form_id(), _level_policies(), load_assessment_package() (+62 more)

### Community 29 - "String"
Cohesion: 0.05
Nodes (71): Decodable, Hashable, AIProvider, anthropic, apple, .backendID, .id, ollama (+63 more)

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

### Community 35 - "cspapergen/cli.py"
Cohesion: 0.08
Nodes (36): BuildResult, _artifacts(), _build(), default_output_dir(), generate_package(), _improve(), main(), Path (+28 more)

### Community 36 - "properties"
Cohesion: 0.09
Nodes (23): type, minLength, type, const, pattern, type, properties, advertised (+15 more)

### Community 37 - "render_pdf_atomically"
Cohesion: 0.15
Nodes (23): InvalidRenderOutput, Path, RuntimeError, A document role could not be rendered safely., Rendering exceeded its bounded qualification window., A renderer returned without producing a readable PDF., Render one PDF role under a deadline and promote it atomically., _readable_page_count() (+15 more)

### Community 38 - "test_mark_scheme_layout.py"
Cohesion: 0.16
Nodes (33): formatted_generation_date(), extract_pdf_text(), pdf_font_names(), Path, Extract stable reading-order text without a Poppler CLI dependency., Return the font families actually used by visible text spans., test_paper1_rendered_documents_use_correct_identity(), render_mark_scheme() (+25 more)

### Community 39 - "HelpTopic"
Cohesion: 0.07
Nodes (28): CaseIterable, HelpTopic, checkingQuality, choosingAModel, creatingAPaper, gettingStarted, .id, privacy (+20 more)

### Community 40 - "Approved-Improvement Traceability"
Cohesion: 0.07
Nodes (26): Approved-Improvement Traceability, Current-Paper Gate, Expansion Gate, Foundation Gate, Global Constraints, Paper Creator Excellence Programme Implementation Plan, Phase Completion Gates, Plan Verification Checklist (+18 more)

### Community 41 - "test_app_backend.py"
Cohesion: 0.18
Nodes (26): _safe_provider_detail(), CompletedProcess, Path, run_bridge(), run_bridge_raw(), test_aqa_accounting_all_papers_generate_expected_files(), test_aqa_business_all_papers_generate_expected_files(), test_aqa_economics_all_papers_generate_expected_files() (+18 more)

### Community 42 - "pastpapergen/notes.py"
Cohesion: 0.20
Nodes (19): _clean_chunk(), essay_capable_topic_ids(), _flush_note_chunk(), _is_exam_point(), _is_note_noise(), _looks_like_heading(), _note_chunks(), note_context_for_topic() (+11 more)

### Community 43 - "GeneratedPaper"
Cohesion: 0.21
Nodes (22): _demand_band(), GeneratedPaper, _hydrate_assessment_metadata(), _objective_allocation(), _prompt_uses_command_word(), _structured_scheme(), validate_generated_paper(), validate_rule() (+14 more)

### Community 44 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Measured Paper Fidelity Implementation Plan, Task 1: Page-role-aware fidelity evidence, Task 2: Shared board answer-page geometry, Task 3: OCR response and blank-page grammar, Task 4: Shared mark-scheme cover calibration, Task 5: Full visual qualification and regression gate

### Community 45 - "load_syllabus"
Cohesion: 0.09
Nodes (51): build_paper1_blueprint(), build_paper2_blueprint(), PaperBlueprint, Syllabus, improve_questions_with_ollama(), PaperBlueprint, Syllabus, load_syllabus() (+43 more)

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
Cohesion: 0.22
Nodes (54): QuestionPart, Stimulus, _assembly_program_question(), _assembly_trace_question(), _big_data_question(), _big_data_short_question(), _binary_short_question(), _bitmap_question() (+46 more)

### Community 51 - "providers.py"
Cohesion: 0.10
Nodes (35): _hosted_client(), _aqa_cs_part_count(), _edexcel_part_count(), hosted_client(), HostedLLMClient, _normalise_base_url(), _ollama_json_schema(), _ollama_output_budget() (+27 more)

### Community 52 - "Q: Where should performance and generated-paper accuracy fixes be made?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Where should performance and generated-paper accuracy fixes be made?, Source Nodes

### Community 53 - "Contract-First Paper Generation and Release Qualification"
Cohesion: 0.06
Nodes (31): 1. Assessment Contract, 2. Deterministic Assessment Data, 3. Item-Level AI Workflow, 4. Evidence Binding and Factual Quality, 5. Mark-Scheme Quality, 6. Board Layout Adapters, 7. Bounded Rendering, 8. Progress, Cancellation, and Resume (+23 more)

### Community 54 - "ExamPageProfile"
Cohesion: 0.16
Nodes (29): _draw_aqa_footer(), _draw_aqa_page(), _draw_barcode(), draw_exam_page(), _draw_independent_notice(), _draw_ocr_notice(), _draw_ocr_page(), _draw_ocr_rules() (+21 more)

### Community 55 - "emit"
Cohesion: 0.26
Nodes (16): build_parser(), handle_bundle_check(), main(), ArgumentParser, Namespace, Fail fast when a packaged backend is missing a dynamic generator., emit(), emit_progress() (+8 more)

### Community 56 - "generator_registry.py"
Cohesion: 0.24
Nodes (15): _capability(), generator_capabilities(), generator_subjects(), _paper_qualification(), PaperQualification, Any, _relative_path(), test_backend_bundle_script_is_registry_driven() (+7 more)

### Community 57 - "properties"
Cohesion: 0.08
Nodes (24): type, type, minimum, type, type, null, string, type (+16 more)

### Community 58 - "_mark_scheme_rows"
Cohesion: 0.16
Nodes (25): _brief_source_evidence(), _calculation_answer_lines(), _mark_scheme_rows(), _normalise_mark_point(), _one_mark_points(), _paper_one_fifteen_mark_scheme_lines(), _paper_one_five_mark_diagram_lines(), _paper_one_section_a_mark_scheme_lines() (+17 more)

### Community 59 - "AssessmentContract"
Cohesion: 0.07
Nodes (52): AssessmentContract, contract_for_question(), EvidenceRecord, GeneratedNumericField, GraphContract, _numeric_contracts(), NumericRole, NumericValueContract (+44 more)

### Community 60 - "Q: How is the macOS backend bundle kept complete?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: How is the macOS backend bundle kept complete?, Source Nodes

### Community 61 - "File Structure"
Cohesion: 0.17
Nodes (11): Assessment Reliability Core Implementation Plan, File Structure, Global Constraints, Subsequent Phase Plans, Task 1: Typed Item Contracts, Task 2: Role-Aware Numeric and Evidence Validation, Task 3: Item-Scoped Draft, Review, and Repair, Task 4: Atomic Checkpoints and Resume (+3 more)

### Community 62 - "aqa_accounting_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_both_papers_pass_multi_seed_automated_checks(), test_external_difficulty_gates_remain_false(), test_reference_evidence_is_aggregate_only(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 63 - "Text"
Cohesion: 0.04
Nodes (98): Charts, Color, KeyPath, View, PanelEmptyState, .body, String, BenchmarkVerdict (+90 more)

### Community 64 - "RecentDocumentStore"
Cohesion: 0.06
Nodes (37): Codable, Equatable, FileManager, GenerationJobState, LocalizedError, GenerationConfiguration, GenerationJobRecord, .missingArtifactCount (+29 more)

### Community 65 - "ocr_economics_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 66 - "Rendering and Mark-Scheme Reliability Implementation Plan"
Cohesion: 0.25
Nodes (7): Rendering and Mark-Scheme Reliability Implementation Plan, Task 1: Bounded atomic render transactions, Task 2: Route every generator family through the transaction, Task 3: Artifact containment, collision, and density evidence, Task 4: Mark-scheme depth contracts, Task 5: OCR Economics pagination regression, Task 6: Phase qualification

### Community 67 - "Architecture"
Cohesion: 0.18
Nodes (10): Architecture, Canonical registry, Extension contract, Failure containment, Fidelity qualification boundary, Package transaction, PDF portability and accessibility, Product boundary (+2 more)

### Community 68 - "pastpapergen/render_pdf.py"
Cohesion: 0.08
Nodes (38): BoardLayout, GraphParams, _answer_line_count(), _axis_labels_for_draw_prompt(), _bar_chart_data(), _bar_label(), _draw_bar_chart(), _draw_do_not_write_rail() (+30 more)

### Community 69 - "test_ollama_generation.py"
Cohesion: 0.13
Nodes (31): generate_questions_with_ollama(), _merge_source_text(), PaperBlueprint, Syllabus, _validate_ai_question(), _validate_content_lists(), BlueprintAwareClient, EmptyClient (+23 more)

### Community 70 - "Glossy Black Fountain Pen App Icon Master"
Cohesion: 0.18
Nodes (11): Glossy Black Fountain Pen App Icon Master, Paper Creator App Icon AppIcon-128x128@1x, Paper Creator App Icon AppIcon-128x128@2x, Paper Creator App Icon AppIcon-16x16@1x, Paper Creator App Icon AppIcon-16x16@2x, Paper Creator App Icon AppIcon-256x256@1x, Paper Creator App Icon AppIcon-256x256@2x, Paper Creator App Icon AppIcon-32x32@1x (+3 more)

### Community 71 - "pastpapergen/ollama_client.py"
Cohesion: 0.11
Nodes (33): MultipleChoiceOption, PaperBlueprint, PaperConfig, BaseModel, QuestionBlueprint, QuestionPart, SectionConfig, Syllabus (+25 more)

### Community 72 - "enum"
Cohesion: 0.18
Nodes (11): benchmark_done, benchmark_metric, benchmark_sample, done, error, file, hello, models (+3 more)

### Community 73 - "Assessment quality and originality"
Cohesion: 0.17
Nodes (11): Assessment quality and originality, Difficulty claims, Human release review, Independent solution and response-band qualification, Item transactions and two-pass generation, Mark-scheme quality, Measured visual qualification, Novelty and exposure (+3 more)

### Community 74 - "ContentView"
Cohesion: 0.12
Nodes (13): App, Commands, AppCommands, PaperCreator, .body, ContentView, .columnVisibility, ContentViewPreview (+5 more)

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
Cohesion: 0.12
Nodes (34): _as_mapping(), CanonicalSolution, _concept_coverage(), _concept_tokens(), _format_number(), IndependentSolver, _normalise(), _normalise_choice_answer() (+26 more)

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

### Community 86 - "NonCurrentAssetCase"
Cohesion: 0.07
Nodes (6): IncomeStatementCase, _nearest_hundred(), NonCurrentAssetCase, Complete, internally consistent source for the Paper 1 company statement., Single source of truth for the Paper 1 sales-ledger case. The question paper,…, SalesLedgerCase

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

### Community 91 - "model_review.py"
Cohesion: 0.28
Nodes (10): independent_review(), JSONClient, Any, Protocol, require_independent_review(), _serialise(), ReviewClient, test_independent_review_rejects_approval_with_reported_issues() (+2 more)

### Community 92 - "BackendEvent"
Cohesion: 0.05
Nodes (40): Identifiable, BackendEvent, benchmarkDone, benchmarkMetric, benchmarkSample, done, error, file (+32 more)

### Community 95 - "inspect_release_compliance"
Cohesion: 0.27
Nodes (14): Path, test_release_compliance_detects_a_tracked_secret_signature(), test_release_compliance_passes_for_the_repository(), test_release_compliance_rejects_unbounded_runtime_dependencies(), _check_dependencies(), _check_entitlements(), _check_font_licences(), _check_privacy_manifest() (+6 more)

### Community 97 - "test_generator_migration.py"
Cohesion: 0.23
Nodes (13): Path, test_all_current_families_pass_declarative_migration_validation(), test_broken_fixture_reports_every_onboarding_surface(), test_scaffold_emits_complete_unadvertised_family_and_refuses_overwrite(), build_parser(), _cli_template(), main(), ArgumentParser (+5 more)

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

### Community 116 - "Question"
Cohesion: 0.10
Nodes (34): numeric_tokens(), Extract quantities exactly enough to catch broken data/source rewrites., assert_materially_new(), _align_paper1_structure(), _build_paper1_context(), _build_paper1_questions(), _paper1_part(), _paper1_question() (+26 more)

### Community 117 - "progress"
Cohesion: 0.50
Nodes (4): maximum, minimum, type, progress

### Community 120 - "properties"
Cohesion: 0.15
Nodes (15): approved, draft, retired, type, type, null, string, minLength (+7 more)

### Community 130 - "required"
Cohesion: 0.17
Nodes (12): candidate_sample, facility_range, group_fairness_screen, independent_manual_review, internal_consistency, item_coverage, marker_standardisation, policy_approved (+4 more)

### Community 152 - "required"
Cohesion: 0.13
Nodes (15): maximum_acceptable_facility, maximum_dif_gap, minimum_acceptable_facility, minimum_candidates, minimum_discrimination, minimum_double_marked_pairs, minimum_facility_coverage, minimum_group_responses (+7 more)

### Community 153 - ".initialEstimate"
Cohesion: 0.19
Nodes (11): EstimateFactor, GenerationEstimate, .etaDate, .remainingText, TimeInterval, GenerationEstimator, Bool, Date (+3 more)

### Community 154 - "DocumentPreviewView"
Cohesion: 0.06
Nodes (32): AppKit, Combine, DocumentPreviewView, .body, .exportAlertBinding, .provenanceRecord, .selectedBinding, .selectedFile (+24 more)

### Community 155 - "GeneratedQuestion"
Cohesion: 0.07
Nodes (100): AssessmentLLMClient, _batches_for_client(), _bounded_text(), _candidate_question(), _canonical_objective_allocation(), _clean_generated_prompt(), _contains_command_word(), _effective_batch_size() (+92 more)

### Community 157 - "render_source_booklet"
Cohesion: 0.13
Nodes (24): economics_exam_schedule(), ExamSchedule, formatted_economics_exam_date(), date, _draw_boxes(), _draw_cover(), _draw_crop_marks(), _draw_fake_barcode() (+16 more)

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

### Community 162 - "aqa_business_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 163 - "qualification_levels"
Cohesion: 0.14
Nodes (14): empirically_calibrated, engineering_validated, visually_calibrated, type, type, empirically_calibrated, engineering_validated, qualification_levels (+6 more)

### Community 164 - "AppDefaults"
Cohesion: 0.12
Nodes (10): AppDefaults, AppLinks, AppStorageKey, SecretAccount, Bool, String, URL, .mlxSetupExplanation (+2 more)

### Community 165 - "paper1_assets.py"
Cohesion: 0.50
Nodes (11): _page_footer(), _paragraph(), _practice_header(), Canvas, PaperBlueprint, Path, render_electronic_answer_document(), render_preliminary_material() (+3 more)

### Community 166 - "required"
Cohesion: 0.17
Nodes (12): difficulty_independently_verified, evidence_fingerprint, family, form_id, paper, policy, provenance, sample (+4 more)

### Community 167 - "properties"
Cohesion: 0.12
Nodes (16): minLength, type, minLength, type, minLength, type, blueprint, contract (+8 more)

### Community 168 - "generation_date.py"
Cohesion: 0.31
Nodes (9): formatted_generation_series(), generation_date(), date, Return the month/year form used on mark-scheme covers., _exam_date(), date, test_generation_date_accepts_iso_override(), test_generation_date_defaults_to_today() (+1 more)

### Community 169 - "required"
Cohesion: 0.15
Nodes (13): artifacts, created_at, evidence, gate_results, generator_id, model, paper_id, reviewer_identity_class (+5 more)

### Community 170 - "ComputerSciencePlugin"
Cohesion: 0.22
Nodes (12): AST, ComputerSciencePlugin, _evaluate_boolean(), normalise_pseudocode(), pseudocode_equivalent(), Any, truth_table(), _validate_boolean_tree() (+4 more)

### Community 171 - "sample"
Cohesion: 0.25
Nodes (8): candidates, groups, items, response_rows, sample, additionalProperties, required, type

### Community 172 - "empirical-calibration.schema.json"
Cohesion: 0.25
Nodes (7): additionalProperties, $id, not, anyOf, $schema, title, type

### Community 173 - "PaperBlueprint"
Cohesion: 0.24
Nodes (18): _count_pages(), _draw_answer_page_header(), _draw_continuation_lines(), _draw_paper_3_pages(), _draw_question_footer(), _draw_question_pages(), _draw_section_b_source_pages(), _draw_section_c_answer_pages() (+10 more)

### Community 174 - "aqaecongen/generator.py"
Cohesion: 0.15
Nodes (24): _build_mcq_option(), build_paper(), _build_written_option(), _case_depth(), _paper_three_indicative_content(), policy_name(), Random, Syllabus (+16 more)

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

### Community 184 - "test_source_booklet.py"
Cohesion: 0.49
Nodes (9): _pdf_page_count(), _pdf_text(), Path, test_paper_2_source_cover_uses_generation_date_and_official_session(), test_source_booklet_extracts_have_reference_style_line_numbers(), test_source_booklet_for_paper_1_only_uses_section_b(), test_source_booklet_for_paper_3_uses_both_sections(), test_source_booklet_has_figure_extracts_and_source_attributions() (+1 more)

### Community 185 - "tool_versions"
Cohesion: 0.50
Nodes (4): type, tool_versions, additionalProperties, type

### Community 186 - "required"
Cohesion: 0.25
Nodes (8): approval_evidence, approved_by_identity_class, policy_id, status, additionalProperties, required, type, policy

### Community 187 - "add_page_structure_tree"
Cohesion: 0.31
Nodes (9): add_page_structure_tree(), has_logical_page_order(), _has_structure_tree(), _new_object(), Document, Page, Path, Attach a deterministic page-level structure tree and marked content. Each page… (+1 more)

### Community 188 - "aqaaccountgen/generator.py"
Cohesion: 0.10
Nodes (33): CostingCase, generate_package(), Path, build_paper(), _extract(), _mcq(), _number(), Random (+25 more)

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

### Community 196 - "GlyphMetric"
Cohesion: 0.67
Nodes (3): GlyphMetric, A compact, serialisable sample of one rendered PDF glyph., test_glyph_metric_contract_is_immutable()

### Community 197 - "entry_point"
Cohesion: 0.67
Nodes (3): pattern, type, entry_point

### Community 199 - "test_repository_hygiene.py"
Cohesion: 0.30
Nodes (9): test_every_tracked_file_has_a_durable_classification(), test_generated_and_binary_outputs_are_rejected(), test_maintained_visual_assets_are_classified_without_allowing_arbitrary_pngs(), test_root_lint_configuration_is_release_configuration(), Classification, classify_path(), inspect_repository(), main() (+1 more)

### Community 201 - "id"
Cohesion: 0.67
Nodes (3): pattern, type, id

### Community 202 - "subject_plugins.py"
Cohesion: 0.22
Nodes (15): board_profile_ids(), discover_subject_plugin(), _normalise_identifier(), register_subject_plugin(), subject_plugin_ids(), parametrize, test_authorised_extract_with_option_route_and_level_policy_passes(), test_essay_subjects_reject_unprovenanced_evidence() (+7 more)

### Community 203 - "SubjectValidation"
Cohesion: 0.12
Nodes (11): ContractSubjectPlugin, Any, Protocol, Safe baseline plugin for families with validation in their own contracts., SubjectPlugin, SubjectValidation, BiologyPlugin, Any (+3 more)

### Community 204 - "Canvas"
Cohesion: 0.13
Nodes (37): _draw_answer_lines(), _draw_answer_lines_until(), _draw_axis_arrow(), _draw_blank_answer_axes(), _draw_calculate_part_with_working_lines(), _draw_centred_instruction_line(), _draw_compact_part(), _draw_context_box() (+29 more)

### Community 205 - "Current-family visual qualification — 26 August 2026"
Cohesion: 0.29
Nodes (6): Automated evidence, Current-family visual qualification — 26 August 2026, Evidence locations, Manual review, Outstanding non-visual gates, Scope and claim

### Community 208 - ".baseQuery"
Cohesion: 0.39
Nodes (4): SecretStore, Any, String, Security

### Community 210 - "generate_package"
Cohesion: 0.25
Nodes (8): type, path, default_output_dir(), generate_package(), main(), Path, test_generate_package_reports_rendering_progress(), test_generate_package_without_seed_does_not_write_audit()

### Community 211 - "EssaySubjectPlugin"
Cohesion: 0.42
Nodes (3): EssaySubjectPlugin, Any, _validate_provenance()

### Community 212 - "enum"
Cohesion: 0.50
Nodes (4): ai-assisted, deterministic, enum, content_mode

### Community 217 - "subject_plugin"
Cohesion: 0.67
Nodes (3): subject_plugin, pattern, type

## Knowledge Gaps
- **736 isolated node(s):** `BoardLayout`, `examforge-aqa-accounting`, `$schema`, `$id`, `title` (+731 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **49 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Work-memory lessons

**Preferred sources** — corroborated by past sessions; start here.
- `AppViewModel` (2× useful, score=1.166012741) _(code changed — re-verify)_
- `generation.py` (2× useful, score=1.164559792) _(code changed — re-verify)_
- `exam_blueprints.py` (2× useful, score=1.127080899) _(code changed — re-verify)_
- `layout_master.py` (2× useful, score=1.127080899) _(code changed — re-verify)_
- `paper_fidelity_audit.py` (2× useful, score=1.127080899) _(code changed — re-verify)_

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `path` connect `generate_package` to `properties`, `test_repository_hygiene.py`, `cspapergen/cli.py`, `inspect_release_compliance`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `GeneratedQuestion` connect `GeneratedQuestion` to `aqaaccountgen/render_pdf.py`, `ocregen/render_pdf.py`, `aqabizgen/render_pdf.py`, `aqabizgen/generator.py`, `GeneratedPaper`, `Paragraph`, `aqaecongen/generator.py`, `aqaecongen/render_pdf.py`, `AssessmentCheckpointStore`, `test_ocr_computer_science.py`, `test_ocr_economics.py`, `mark_scheme_enrichment.py`, `AssessmentContract`, `aqaaccountgen/generator.py`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Why does `properties` connect `properties` to `qualification_levels`, `generate_package`, `backend-protocol.schema.json`, `progress`, `capabilities`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `GeneratedQuestion` (e.g. with `AssessmentLLMClient` and `GenerationPolicy`) actually correct?**
  _`GeneratedQuestion` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `ApplicationCoordinator` (e.g. with `PaperCreator` and `.body`) actually correct?**
  _`ApplicationCoordinator` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `BoardLayout`, `examforge-aqa-accounting`, `$schema` to the rest of the system?**
  _736 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `cspapergen/render_pdf.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0984643179765131 - nodes in this community are weakly interconnected._