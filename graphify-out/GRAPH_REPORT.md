# Graph Report - Past Paper Creation  (2026-09-18)

## Corpus Check
- 392 files · ~734,969 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 6614 nodes · 18569 edges · 269 communities (240 shown, 29 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 1098 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7993e2e0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ExamBoardOption
- GeneratedQuestion
- paper_fidelity_audit.py
- Rect
- load_syllabus
- ApplicationCoordinator
- Text
- cspapergen/render_pdf.py
- build_paper_blueprint
- pastpapergen/render_pdf.py
- psychometrics.py
- ocregen/render_pdf.py
- pastpapergen/generator.py
- live_generation_matrix.py
- require_difficulty_review
- String
- pastpapergen/ollama_client.py
- GeneratedPaper
- DocumentPreviewView
- RecentDocumentStore
- test_ollama_generation.py
- question_bank.py
- Paragraph
- AssessmentContract
- properties
- ocrcsgen/render_pdf.py
- QualityInspector
- _mark_scheme_rows
- CodingKeys
- Canvas
- test_sql_answer_verification.py
- test_aqa_business.py
- reconcile_solution
- sql_contracts.py
- aqabizgen/render_pdf.py
- open_credit.py
- test_task_source_demand.py
- test_render_pdf.py
- test_source_credit_integrity.py
- AIProvider
- AssessmentCheckpointStore
- assessment_package.py
- test_ocr_economics.py
- properties
- test_open_credit_reconciliation.py
- IndependentSolver
- providers.py
- reference_corpus.py
- cspapergen/ollama_client.py
- test_mlx_setup.py
- test_solver_source_adapter.py
- aqaecongen/render_pdf.py
- CodingKeys
- test_finite_response_slots.py
- reference_demand_profiles.py
- test_aqa_economics.py
- type
- reference_demand.py
- properties
- generator/tests/test_assessment_contracts.py
- PaperCreatorTests
- test_reference_evidence_validation.py
- SwiftUI
- pdf_validation.py
- objective_policy_for
- properties
- NumericOutput
- document_dsl/__init__.py
- benchmark.py
- build_layout_masters.py
- aqa_section_intro
- CostingCase
- Contract-First Paper Generation and Release Qualification
- test_aqa_accounting.py
- required
- ExamPageProfile
- test_app_backend.py
- test_computer_science_objectives.py
- test_mark_scheme_layout.py
- render_pdf_atomically
- mathematics.py
- Approved-Improvement Traceability
- test_reference_demand.py
- graphs.py
- reference_evidence.py
- test_science_overlay.py
- PathSection
- BackendClient
- SubjectValidation
- test_coverage_matrix.py
- generate_package
- cspapergen/generator.py
- reference-demand-profile.schema.json
- NonCurrentAssetCase
- properties
- test_generator_registry.py
- generation.py
- PartnershipCase
- family_adapter.py
- Paper Creator Excellence Programme Design
- required
- ShareholderCase
- properties
- mark_scheme_enrichment.py
- test_pdf_validation.py
- topic_id
- $defs
- test_science_subjects.py
- required
- paths
- required
- properties
- accounting.py
- stratum
- pastpapergen/notes.py
- properties
- aqa_accounting_calibration.py
- emit
- required
- test_accounting_objectives.py
- validate_generator_migration.py
- validate_mark_scheme_item
- subject_plugins.py
- test_humanities_overlay.py
- CandidateResponse
- ModelCoordinator
- ComputerSciencePlugin
- generate_package
- _draw_cover
- properties
- properties
- properties
- inspect_release_compliance
- SalesLedgerCase
- draw_barcode
- enum
- IncomeStatementCase
- independent_solver.py
- properties
- test_generator_migration.py
- test_topic_reference_evidence.py
- test_aqa_business_calibration.py
- BiologyPlugin
- 31 August continued qualification findings
- Continued qualification — 31 August
- properties
- required
- paper
- test_repository_hygiene.py
- additionalProperties
- id
- aqa_business_calibration.py
- ocr_computer_science_calibration.py
- ocr_economics_calibration.py
- Q: Where should performance and generated-paper accuracy fixes be made?
- enum
- qualification_levels
- Q: how can we make even more improvements to get the highest similarity in terms of structure and layout and quality of questions etc. and maybe all of the files in the project can be better organised. and the UI can be made to be much better and more geometrically apple-like by strictly following every single rule they outline in their HIG
- Q: How does the generation quality pipeline connect?
- Assessment quality and originality
- Current-family visual qualification — 26 August 2026
- Reference-Demand Calibration Design
- required
- backend-protocol.schema.json
- Q: How is the macOS backend bundle kept complete?
- exam_blueprints.py
- difficulty_calibration.py
- File Structure
- required
- required
- Q: How does the paper fidelity audit produce per-document and per-role scores, and where should release thresholds integrate?
- Q: Which Ollama model and live validation path does the project use for all supported papers?
- generator-capability.schema.json
- _BooleanParser
- Architecture
- End-to-end runtime
- Paper creator: deep project analysis
- Architecture
- enum
- required
- register_fonts
- PaperBlueprint
- enum
- profile_for
- macOS interaction and HIG compliance
- macOS UI audit
- Assessment-objective calibration reference
- Reference-Demand Calibration Implementation Plan
- Paper creator
- enum
- required
- required
- properties
- PhysicsPlugin
- Implementation and fidelity report
- Global Constraints
- Rendering and Mark-Scheme Reliability Implementation Plan
- required
- sample
- enum
- empirical-calibration.schema.json
- Question
- _call_name
- build_backend.sh
- _draw_stimulus
- enum
- .initialEstimate
- model
- generator/tests/test_closed_response_integrity.py
- _written
- macOS user-experience audit
- formatted_generation_date
- test_aqa_accounting_calibration.py
- qualification-schema.json
- QuestionPaperCover
- test_difficulty_calibration.py
- paper1_assets.py
- cspapergen/cli.py
- generator_working_directory
- Cambridge International engineering foundation — 26 August 2026
- pull_request_template.md
- xcbuild.sh
- enum
- capabilities
- progress
- tool_versions
- diagnose.sh
- move_to_trash.sh
- run_app_macos.sh
- app_board
- app_subject
- blueprint_version
- entry_point
- package
- specification_version
- subject
- subject_plugin
- AGENTS.md
- fonts/README.md
- Core/__init__.py
- subjects/__init__.py
- bootstrap_backend.sh
- clean.sh
- resolve_agent_name.sh
- aqabizgen/__init__.py
- cspapergen/__init__.py
- ocrcsgen/__init__.py
- configuredgen/__init__.py
- pastpapergen/__init__.py
- ocregen/__init__.py
- tools/__init__.py
- aqa-economics-practice-generator
- cspapergen
- examforge-aqa-accounting
- examforge-aqa-business
- examforge-ocr-computer-science
- ocr-economics-practice-generator
- paper-creator-configured-generators
- pastpapergen
- add_page_structure_tree
- test_source_candidate_paths.py
- render_source_booklet
- topic_reference_evidence.py
- aqa_front_matter_pages
- test_ocr_computer_science_calibration.py
- WorkspaceLayoutMode

## God Nodes (most connected - your core abstractions)
1. `GeneratedQuestion` - 217 edges
2. `build_paper_blueprint()` - 179 edges
3. `load_syllabus()` - 169 edges
4. `load_builtin_paper_config()` - 163 edges
5. `IndependentSolver` - 150 edges
6. `ApplicationCoordinator` - 144 edges
7. `GeneratedOption` - 117 edges
8. `GeneratedPaper` - 97 edges
9. `reconcile_solution()` - 90 edges
10. `load_syllabus()` - 77 edges

## Surprising Connections (you probably didn't know these)
- `test_renderer_rejects_unsupported_indicative_label()` --calls--> `_indicative_objective()`  [INFERRED]
  tests/test_accounting_objectives.py → Resources/accounting/aqa/generator/aqaaccountgen/render_pdf.py
- `test_paraphrased_cpu_credit_still_prints_its_actual_typed_one_mark_allocations()` --calls--> `build_paper2_blueprint()`  [INFERRED]
  tests/test_open_credit_reconciliation.py → Resources/computer-science/aqa/generator/cspapergen/generator.py
- `FirstPassClient` --uses--> `GenerationPolicy`  [INFERRED]
  tests/test_assessment_checkpoints.py → Backend/Core/ai_assessment.py
- `FirstPassDifficultyClient` --uses--> `GenerationPolicy`  [INFERRED]
  tests/test_assessment_checkpoints.py → Backend/Core/ai_assessment.py
- `NoCallsClient` --uses--> `GenerationPolicy`  [INFERRED]
  tests/test_assessment_checkpoints.py → Backend/Core/ai_assessment.py

## Import Cycles
- None detected.

## Communities (269 total, 29 thin omitted)

### Community 0 - "ExamBoardOption"
Cohesion: 0.07
Nodes (36): CatalogSubject, ExamBoardOption, .fullPapers, .isReady, .questionBanks, .usesAI, .defaultBoard, SidebarItem (+28 more)

### Community 1 - "GeneratedQuestion"
Cohesion: 0.06
Nodes (121): AssessmentLLMClient, _batches_for_client(), _bounded_text(), _candidate_question(), _canonical_objective_allocation(), _clean_generated_prompt(), _contains_command_word(), _demand_item() (+113 more)

### Community 2 - "paper_fidelity_audit.py"
Cohesion: 0.05
Nodes (103): Pixmap, parametrize, Path, test_compact_profile_omits_raster_geometry(), test_contact_sheets_make_visual_review_artifacts(), test_generated_document_falls_back_to_nested_transaction_output(), test_generated_document_supports_app_per_paper_directories(), test_metric_callout_names_print_resolution_comparison_dimensions() (+95 more)

### Community 3 - "Rect"
Cohesion: 0.10
Nodes (35): conform_generated_documents(), _edexcel_printed_credit(), Path, _clamp_fitz_rect(), conform_pdf_page_boxes(), conform_pdf_to_box_template(), draw_text_slot(), _fitz_rect_close() (+27 more)

### Community 4 - "load_syllabus"
Cohesion: 0.06
Nodes (75): _build(), build_paper1_blueprint(), build_paper2_blueprint(), build_topic_question_bank(), PaperBlueprint, Syllabus, calibrate_blueprint(), PaperBlueprint (+67 more)

### Community 5 - "ApplicationCoordinator"
Cohesion: 0.03
Nodes (63): AnyCancellable, DateFormatter, .body, AppDefaults, AppLinks, AppStorageKey, SecretAccount, Bool (+55 more)

### Community 6 - "Text"
Cohesion: 0.04
Nodes (81): Charts, KeyPath, View, PanelEmptyState, .body, String, value, BenchmarkAccessibility (+73 more)

### Community 7 - "cspapergen/render_pdf.py"
Cohesion: 0.15
Nodes (48): _answer_line_count(), _answer_lines_paginated(), _candidate_fields(), _cover_section(), _draw_adjacency_matrix_answers(), _draw_arrow(), _draw_assembly_support_page(), _draw_classification_diagram() (+40 more)

### Community 8 - "build_paper_blueprint"
Cohesion: 0.07
Nodes (95): build_paper_blueprint(), PaperBlueprint, Syllabus, load_builtin_paper_config(), review_table_rows(), load_syllabus(), Path, Syllabus (+87 more)

### Community 9 - "pastpapergen/render_pdf.py"
Cohesion: 0.10
Nodes (39): BoardLayout, _answer_line_count(), _draw_case_source_figure(), _draw_economics_graph(), _draw_mark_scheme_end_page(), _draw_mcq_part(), _draw_ms_blank_page(), _draw_ms_header_box() (+31 more)

### Community 10 - "psychometrics.py"
Cohesion: 0.08
Nodes (56): CalibrationMetadata, CalibrationStore, ConsentRecord, _normalise_row(), Any, Path, Encrypted local storage for row-level calibration evidence. Keys are…, _read_rows() (+48 more)

### Community 11 - "ocregen/render_pdf.py"
Cohesion: 0.09
Nodes (69): OCRAnswerLines, _add_economics_diagram(), _add_firm_objectives_diagram(), _add_ppf_diagram(), _annotation_conventions_page(), _answer_mark(), _assessment_allocation(), _assessment_grid_groups() (+61 more)

### Community 12 - "pastpapergen/generator.py"
Cohesion: 0.06
Nodes (72): MultipleChoiceOption, _adapt_paper_three_case_guidance(), _best_section_a_context_point(), _build_part(), _build_parts(), _choice_group_name(), _choice_lookup(), _choose_topic() (+64 more)

### Community 13 - "live_generation_matrix.py"
Cohesion: 0.08
Nodes (50): Release qualification evidence and policy models., ArtifactEvidence, EvidenceRecord, GateState, ModelIdentity, BaseModel, field_validator, Path (+42 more)

### Community 14 - "require_difficulty_review"
Cohesion: 0.07
Nodes (78): _export_difficulty_candidate_projection(), candidate_review_content(), CandidateContentIdentity, difficulty_candidate_projection(), DifficultyCandidateProjection, edexcel_difficulty_candidate_projection(), ensure_difficulty_candidate_projection(), _mapping() (+70 more)

### Community 15 - "String"
Cohesion: 0.03
Nodes (118): Codable, Decodable, Equatable, Hashable, Identifiable, AssessmentKind, fullPaper, questionBank (+110 more)

### Community 16 - "pastpapergen/ollama_client.py"
Cohesion: 0.08
Nodes (46): validate_assessment_contract(), _artifacts(), _build(), _improve(), _load_rule(), _normalise_paper_id(), CandidateSectionRule, ChoiceSelection (+38 more)

### Community 17 - "GeneratedPaper"
Cohesion: 0.09
Nodes (54): AppliedMCQSource, GeneratedPaper, GeneratedSection, PaperRule, BaseModel, QuestionRule, mcqs(), q() (+46 more)

### Community 18 - "DocumentPreviewView"
Cohesion: 0.06
Nodes (33): AppKit, Combine, DocumentPreviewView, .body, .exportAlertBinding, .provenanceRecord, .selectedBinding, .selectedFile (+25 more)

### Community 19 - "RecentDocumentStore"
Cohesion: 0.06
Nodes (28): FileManager, GenerationJobState, LocalizedError, ExamCatalog, GenerationJobState, .systemImage, .title, JobHistoryView (+20 more)

### Community 20 - "test_ollama_generation.py"
Cohesion: 0.09
Nodes (43): generate_questions_with_ollama(), _merge_question_text(), _merge_source_text(), _validate_ai_question(), _bar_chart_data(), candidate_stimulus_data(), Expose the same source values and dispatch rules used to draw a figure., _table_rows() (+35 more)

### Community 21 - "question_bank.py"
Cohesion: 0.15
Nodes (70): _paper2_sql_task(), Six marks for the compound query; finite row analysis replaces two writes., _repartition_paper2_question(), MarkingGuidance, model_validator, QuestionPart, Attach the immutable marking key separately from candidate slot IDs., Stimulus (+62 more)

### Community 22 - "Paragraph"
Cohesion: 0.13
Nodes (60): AQAAnswerLines, Paragraph, _accounting_marking_guidance_pages(), _accounting_system_case(), _additional_answer_page(), _appropriation_answer_table(), _assessment_objectives_page(), _chrome() (+52 more)

### Community 23 - "AssessmentContract"
Cohesion: 0.07
Nodes (51): AssessmentContract, contract_for_question(), GeneratedNumericField, GraphContract, _numeric_contracts(), NumericRole, NumericValueContract, Any (+43 more)

### Community 24 - "properties"
Cohesion: 0.04
Nodes (60): anyOf, default, title, const, title, type, minLength, title (+52 more)

### Community 25 - "ocrcsgen/render_pdf.py"
Cohesion: 0.06
Nodes (51): ocr_question_cover(), ExamPage, Flowable, A full-page shell that can also live inside a Platypus story., AnswerLineFlowable, AQACompactAnswerLines, OCRComputerScienceAnswerLines, Flowable (+43 more)

### Community 26 - "QualityInspector"
Cohesion: 0.09
Nodes (31): GenerationQualityState, GenerationProgress, .accessibilityValue, .body, GenerationQualityState, .color, .systemImage, GeneratorWorkspace (+23 more)

### Community 27 - "_mark_scheme_rows"
Cohesion: 0.11
Nodes (32): _brief_source_evidence(), _calculation_answer_lines(), _mark_point_relevance(), _mark_scheme_rows(), _normalise_mark_point(), _one_mark_points(), _paper_one_fifteen_mark_scheme_lines(), _paper_one_five_mark_diagram_lines() (+24 more)

### Community 28 - "CodingKeys"
Cohesion: 0.04
Nodes (57): CodingKey, CodingKeys, assessmentKind, backendVersion, capabilities, checks, code, command (+49 more)

### Community 29 - "Canvas"
Cohesion: 0.15
Nodes (38): _axis_labels_for_draw_prompt(), _count_pages(), _draw_answer_lines(), _draw_answer_lines_until(), _draw_answer_page_header(), _draw_calculate_part_with_working_lines(), _draw_centred_instruction_line(), _draw_compact_part() (+30 more)

### Community 30 - "test_sql_answer_verification.py"
Cohesion: 0.12
Nodes (44): Validate the answer and every model-presented full statement separately., validate_sql_response(), _difficulty_candidate(), _difficulty_solution(), _part_demand_item(), _part_solver_projection(), EvidenceRecord, QuestionPart (+36 more)

### Community 31 - "test_aqa_business.py"
Cohesion: 0.07
Nodes (45): Return the immutable rules for one printed option (one-based)., resolve_question_rules(), generate_package(), Path, FinancialPosition, format_number(), Format an exam answer without meaningless trailing zeroes., The single source of truth for Paper 1 financial-statement figures. (+37 more)

### Community 32 - "reconcile_solution"
Cohesion: 0.12
Nodes (43): _independently_validate_candidate(), _tasks(), reconcile_solution(), NoModelArithmetic, parametrize, test_closed_accounting_solutions_ignore_the_draft_answer_key(), Numeric workings support an MCQ key; they do not make it a free response., test_numeric_selected_response_does_not_require_free_entry_output_slots() (+35 more)

### Community 33 - "sql_contracts.py"
Cohesion: 0.11
Nodes (40): _contract_column(), _Count, _equality(), _Field, _finding(), fitness_centre_sql_contract(), _Frozen, _has_sql_statement_shape() (+32 more)

### Community 34 - "aqabizgen/render_pdf.py"
Cohesion: 0.14
Nodes (46): SelectedResponseContract, _artifacts(), _additional_answer_page(), _ao_summary(), _assessment_objectives_page(), _break_even_diagram(), _calculation_marking_page(), _chart() (+38 more)

### Community 35 - "open_credit.py"
Cohesion: 0.13
Nodes (30): cpu_credit_allocations(), cpu_credit_contract(), _cpu_quote_supports_criterion(), CreditJudgement, CriterionDecision, _has_unambiguous_instruction_antecedent(), _normalise_cpu_clauses(), _passive_relation_patterns() (+22 more)

### Community 36 - "test_task_source_demand.py"
Cohesion: 0.09
Nodes (47): _better_than_target(), _decimal(), _display_decimal(), _money_choice(), _numeric_choice(), _percent_choice(), _plain_decimal(), Any (+39 more)

### Community 37 - "test_render_pdf.py"
Cohesion: 0.13
Nodes (48): _apply_edexcel_page_boxes(), Path, Match Pearson question-paper bleed and crop boxes without changing A4 content., render_question_paper(), _answer_rule_count(), _blank_axis_lines(), _blueprint_with_section_a_question(), _dark_pixels() (+40 more)

### Community 38 - "test_source_credit_integrity.py"
Cohesion: 0.08
Nodes (44): calculation(), calculation_label(), calculation_prompt(), calculation_working(), EconomicsSource, BaseModel, Decimal, model_validator (+36 more)

### Community 39 - "AIProvider"
Cohesion: 0.06
Nodes (32): CaseIterable, AIProvider, anthropic, apple, .backendID, .id, ollama, openAI (+24 more)

### Community 40 - "AssessmentCheckpointStore"
Cohesion: 0.14
Nodes (28): AssessmentCheckpointStore, CheckpointCorrupt, CheckpointIdentity, CheckpointMismatch, identity_for_blueprint(), Any, BaseModel, Path (+20 more)

### Community 41 - "assessment_package.py"
Cohesion: 0.12
Nodes (40): _assessment_contract(), AssessmentPackageCompatibilityError, _authoring_provenance(), _contains_non_finite(), _evidence_ids(), _extract_items(), _form_id(), _level_policies() (+32 more)

### Community 42 - "test_ocr_economics.py"
Cohesion: 0.08
Nodes (45): percentage_change_context(), Any, Candidate chart endpoints and the requested one-decimal percentage output., generate_package(), Path, build_paper(), _evaluation_scheme(), _extract() (+37 more)

### Community 43 - "properties"
Cohesion: 0.05
Nodes (43): $ref, title, type, SourcePath, TopicRecord, minLength, title, type (+35 more)

### Community 44 - "test_open_credit_reconciliation.py"
Cohesion: 0.12
Nodes (43): alternative_permission(), Any, Only known host-authored permissions can bypass answer-value checking., credit_identity(), credit_item_projection(), review_open_credit(), validate_open_credit_review(), _calculation_item() (+35 more)

### Community 45 - "IndependentSolver"
Cohesion: 0.12
Nodes (42): CanonicalSolution, IndependentSolver, Solve an item in a context that deliberately excludes its draft scheme., complete_solver_response(), Any, Complete strict solver envelopes for tests exercising later pipeline stages., closed_item(), parametrize (+34 more)

### Community 46 - "providers.py"
Cohesion: 0.09
Nodes (38): _hosted_client(), _aqa_cs_part_count(), _edexcel_part_count(), hosted_client(), HostedLLMClient, _normalise_base_url(), _ollama_json_schema(), _ollama_output_budget() (+30 more)

### Community 47 - "reference_corpus.py"
Cohesion: 0.13
Nodes (45): MonkeyPatch, Path, test_document_path_requires_filename(), test_document_path_stays_inside_corpus(), test_download_manifest_records_failure_and_continues(), test_parse_aqa_resources_filters_modified_papers(), test_parse_ocr_resources_uses_a_level_tab_only(), test_parse_ocr_specifications_keeps_a_level_not_as_level() (+37 more)

### Community 48 - "cspapergen/ollama_client.py"
Cohesion: 0.09
Nodes (46): EvidenceRecord, aqa_cs_solver_item(), authoring_route(), Any, question_content_sha256(), AQA CS source-coupled review identity, shared by authoring/resume/export. This…, One adapter/reuse projection; caller supplies candidate-visible figure data.…, reviewed_question_metadata() (+38 more)

### Community 49 - "test_mlx_setup.py"
Cohesion: 0.09
Nodes (41): _available_cache_bytes(), ensure_mlx_ready(), handle_mlx_status(), handle_setup_mlx(), install_mlx_runtime(), is_managed_development_environment(), load_mlx_model(), mlx_runtime_available() (+33 more)

### Community 50 - "test_solver_source_adapter.py"
Cohesion: 0.15
Nodes (30): candidate_content_identity(), _assert_public_stimulus(), _difficulty_candidate(), EvidenceRecord, PaperBlueprint, QuestionPart, Syllabus, _question_solver_projection() (+22 more)

### Community 51 - "aqaecongen/render_pdf.py"
Cohesion: 0.13
Nodes (40): aqa_question_cover(), mark_scheme_cover(), MarkSchemeCover, Flowable, _assessment_objectives_table(), _context_data_table(), _context_first_page(), _context_second_page() (+32 more)

### Community 52 - "CodingKeys"
Cohesion: 0.07
Nodes (36): CodingKeys, appContextWindow, contextWindow, defaultModel, detail, downloadSizeGB, id, maximumMemoryGB (+28 more)

### Community 53 - "test_finite_response_slots.py"
Cohesion: 0.36
Nodes (10): parametrize, solve(), test_assembly_trace_checks_every_register_series_and_stored_value(), test_finite_outputs_are_keyed_and_reject_a_changed_value(), test_full_truth_table_requires_every_input_combination(), test_paper1_finite_outputs_are_checked_exhaustively(), test_paper1_matrix_keys_do_not_reveal_which_cells_contain_one(), test_rle_encoding_checks_both_ordered_sequences_without_fixing_pair_notation() (+2 more)

### Community 54 - "reference_demand_profiles.py"
Cohesion: 0.12
Nodes (36): Pattern, test_discounted_2025_item_is_not_reference_demand_evidence(), build_document(), CorpusFamily, _distribution(), extract_reference_features(), extract_reference_items(), _fingerprint() (+28 more)

### Community 55 - "test_aqa_economics.py"
Cohesion: 0.09
Nodes (31): generate_package(), main(), Path, build_paper(), Syllabus, _section_instructions(), Independent AQA 7136-aligned A-level Economics practice-paper generator., load_syllabus() (+23 more)

### Community 56 - "type"
Cohesion: 0.06
Nodes (40): type, additionalProperties, $ref, title, type, additionalProperties, title, type (+32 more)

### Community 57 - "reference_demand.py"
Cohesion: 0.11
Nodes (39): assessment_objectives_for_item(), audit_form_demand(), build_item_demand_target(), _checked_in_profile_fingerprint(), _cognitive_operations(), _collapse_command_distribution(), _command_family(), _difficulty_evidence() (+31 more)

### Community 58 - "properties"
Cohesion: 0.05
Nodes (39): high, low, standard, anyOf, title, minLength, title, type (+31 more)

### Community 59 - "generator/tests/test_assessment_contracts.py"
Cohesion: 0.12
Nodes (37): _question_solver_item(), paper(), parametrize, test_actual_level_tariffs_have_distinct_usable_band_descriptors(), test_all_seeded_styles_have_contract_credit_not_topic_note_filler(), test_business_expansion_short_credit_marks_one_complete_route(), test_complete_declared_numeric_operations_have_literal_answers(), test_content_driven_scheme_policy_rejects_missing_printed_assessment() (+29 more)

### Community 60 - "PaperCreatorTests"
Cohesion: 0.09
Nodes (15): CatalogLoader, CatalogLoadError, duplicateBoard, duplicateImplementation, emptyImplementation, .errorDescription, implementationMissingFromCatalog, missingResource (+7 more)

### Community 61 - "test_reference_evidence_validation.py"
Cohesion: 0.11
Nodes (25): load_reference_demand_document(), BaseModel, model_validator, Path, ReferenceDemandDocument, validate_profile_payload(), document(), parametrize (+17 more)

### Community 62 - "SwiftUI"
Cohesion: 0.09
Nodes (21): App, Commands, AppCommands, PaperCreator, .body, AISettingsTab, PrivacySettingsTab, .body (+13 more)

### Community 63 - "pdf_validation.py"
Cohesion: 0.15
Nodes (28): compare_page_evidence(), _contrast_against_white(), _contrast_ratio(), _count_score(), _font_embedding(), _font_evidence(), _is_decorative_bleed(), _is_margin_furniture() (+20 more)

### Community 64 - "objective_policy_for"
Cohesion: 0.13
Nodes (14): objective_policy_for(), ObjectivePolicy, Any, Subject meaning for AO labels, independent of item tariffs and renderers., Resolve family IDs, subject names or qualification codes., Reject unsupported labels in new or persisted qualified contracts., CS tasks are not classified from their tariff or AO3 label alone., PaperBlueprint (+6 more)

### Community 65 - "properties"
Cohesion: 0.06
Nodes (36): aqa-topic-operation-records-v2, edition-leaf-path-features-v2, full-paper, question-bank, unqualified-reference-v1, enum, minLength, type (+28 more)

### Community 66 - "NumericOutput"
Cohesion: 0.13
Nodes (36): CS component policy audit over candidate-answerable paths, not printed totals., BaseModel, Exact raw-provider shape; semantic validation remains item-specific below., ReconciliationIssue, ReconciliationResult, SolverResponseEnvelope, check_numeric_alternatives(), check_published_outputs() (+28 more)

### Community 67 - "document_dsl/__init__.py"
Cohesion: 0.06
Nodes (88): AnswerSpace, BaseComponent, BlankPage, Component, ContinuationPage, Cover, Diagram, Graph (+80 more)

### Community 68 - "benchmark.py"
Cohesion: 0.14
Nodes (30): apple_cpu_core_split(), available_memory_gb(), avg(), clamp(), cpu_brand(), cpu_load_percent(), cpu_probe(), disk_probe() (+22 more)

### Community 69 - "build_layout_masters.py"
Cohesion: 0.21
Nodes (22): Generated-content policy is not an observed reference-count range., runtime_page_count_policy(), test_content_driven_policy_is_reproducible_and_does_not_reclassify_other_documents(), _box(), _colour(), _content_box(), _drawing_kind(), _drawings() (+14 more)

### Community 70 - "aqa_section_intro"
Cohesion: 0.10
Nodes (25): aqa_lozenge(), aqa_section_intro(), AQAQuestionHeaderFactory, flowable_question_block(), independent_practice_page(), OCRQuestionHeaderFactory, page_sequence(), Color (+17 more)

### Community 72 - "Contract-First Paper Generation and Release Qualification"
Cohesion: 0.06
Nodes (31): 1. Assessment Contract, 2. Deterministic Assessment Data, 3. Item-Level AI Workflow, 4. Evidence Binding and Factual Quality, 5. Mark-Scheme Quality, 6. Board Layout Adapters, 7. Bounded Rendering, 8. Progress, Cancellation, and Resume (+23 more)

### Community 73 - "test_aqa_accounting.py"
Cohesion: 0.11
Nodes (27): build_paper(), _extract(), _number(), Random, Syllabus, _values(), Independent AQA 7127 practice-paper generator., parametrize (+19 more)

### Community 74 - "required"
Cohesion: 0.11
Nodes (25): assessment_objectives, cognitive_operation, command_word, demand_band, demand_basis, historical_engineering_demand_proxy, item_ids, learner_demand (+17 more)

### Community 75 - "ExamPageProfile"
Cohesion: 0.20
Nodes (26): _draw_aqa_footer(), _draw_aqa_page(), _draw_barcode(), draw_exam_page(), _draw_independent_notice(), _draw_ocr_notice(), _draw_ocr_page(), _draw_ocr_rules() (+18 more)

### Community 76 - "test_app_backend.py"
Cohesion: 0.15
Nodes (29): progress_emitter(), _safe_provider_detail(), CaptureFixture, CompletedProcess, Path, run_bridge(), run_bridge_raw(), test_aqa_accounting_all_papers_generate_expected_files() (+21 more)

### Community 77 - "test_computer_science_objectives.py"
Cohesion: 0.06
Nodes (72): generate_package(), Path, load_rule(), _analysis_prompt(), build_paper(), _levels(), _programming_prompt(), _programming_scheme() (+64 more)

### Community 78 - "test_mark_scheme_layout.py"
Cohesion: 0.19
Nodes (30): pdf_font_names(), Path, Return the font families actually used by visible text spans., _cleanup_graph_cache(), render_mark_scheme(), _assert_complete_contract_scheme(), _blueprint_with_section_a_calculation(), _blueprint_with_section_b_topic() (+22 more)

### Community 79 - "render_pdf_atomically"
Cohesion: 0.15
Nodes (23): InvalidRenderOutput, Path, RuntimeError, A document role could not be rendered safely., Rendering exceeded its bounded qualification window., A renderer returned without producing a readable PDF., Render one PDF role under a deadline and promote it atomically., _readable_page_count() (+15 more)

### Community 80 - "mathematics.py"
Cohesion: 0.15
Nodes (21): AnswerComparison, compare_mathematical_answers(), FurtherMathematicsPlugin, MarkAward, _marking_rules(), MarkingRule, MathematicalAnswer, MathematicsPlugin (+13 more)

### Community 81 - "Approved-Improvement Traceability"
Cohesion: 0.07
Nodes (27): 31 August qualification corrections, Approved-Improvement Traceability, Current-Paper Gate, Expansion Gate, Foundation Gate, Global Constraints, Paper Creator Excellence Programme Implementation Plan, Phase Completion Gates (+19 more)

### Community 82 - "test_reference_demand.py"
Cohesion: 0.17
Nodes (27): module(), profile_payload(), parametrize, Path, test_calculation_reasoning_ceiling_scales_with_tariff(), test_committed_profiles_cover_every_advertised_assessment_without_source_text(), test_committed_profiles_include_unadvertised_aqa_mathematics_evidence(), test_empty_context_does_not_create_an_application_requirement() (+19 more)

### Community 83 - "graphs.py"
Cohesion: 0.30
Nodes (26): Axes, ad_as_diagram(), _arrow_axes(), _ax(), circular_flow_diagram(), consumer_producer_surplus(), demand_supply_diagram(), _ensure_style() (+18 more)

### Community 84 - "reference_evidence.py"
Cohesion: 0.11
Nodes (28): audit_candidate_paths(), CandidatePath, CandidateTopology, enumerate_candidate_paths(), identity(), path_metrics(), PathOption, PathSection (+20 more)

### Community 85 - "test_science_overlay.py"
Cohesion: 0.35
Nodes (16): apparatus_diagram(), ApparatusSpec, Atom, Bond, circuit_diagram(), CircuitComponent, CircuitSpec, molecule_diagram() (+8 more)

### Community 86 - "PathSection"
Cohesion: 0.09
Nodes (22): answer_options, candidate_marks, options, exclusiveMinimum, title, type, exclusiveMinimum, title (+14 more)

### Community 87 - "BackendClient"
Cohesion: 0.16
Nodes (14): BackendClient, BackendClientError, backendMissing, .errorDescription, pythonMissing, pythonVenvUnreadable, BackendFile, LaunchConfiguration (+6 more)

### Community 88 - "SubjectValidation"
Cohesion: 0.16
Nodes (9): ContractSubjectPlugin, Any, Protocol, Safe baseline plugin for families with validation in their own contracts., SubjectPlugin, SubjectValidation, EssaySubjectPlugin, Any (+1 more)

### Community 89 - "test_coverage_matrix.py"
Cohesion: 0.20
Nodes (24): family(), matrix(), Path, test_catalog_availability_is_owned_only_by_registry(), test_checked_in_matrix_is_deterministic_and_current(), test_existing_generators_are_reported_without_false_verification(), test_matrix_exactly_covers_layout_profiles(), test_no_verified_paper_has_a_failed_gate() (+16 more)

### Community 90 - "generate_package"
Cohesion: 0.25
Nodes (8): type, path, default_output_dir(), generate_package(), main(), Path, test_generate_package_reports_rendering_progress(), test_generate_package_without_seed_does_not_write_audit()

### Community 91 - "cspapergen/generator.py"
Cohesion: 0.14
Nodes (21): derive_task_semantics(), Any, BaseModel, Strict, deterministic task contracts for AQA CS topic-reference evidence., The serialised summary is valid only when it agrees with the question., Derive the comparison form from printed question data, never its hint., ReferenceTaskContract, _align_paper1_structure() (+13 more)

### Community 92 - "reference-demand-profile.schema.json"
Cohesion: 0.08
Nodes (24): derived_aggregate_only, profiles, purpose, retains_source_text, additionalProperties, const, $id, schema_version (+16 more)

### Community 94 - "properties"
Cohesion: 0.08
Nodes (25): type, pattern, type, pattern, pattern, type, type, pattern (+17 more)

### Community 95 - "test_generator_registry.py"
Cohesion: 0.22
Nodes (15): _capability(), generator_capabilities(), generator_subjects(), _paper_qualification(), PaperQualification, Any, _relative_path(), test_backend_bundle_script_is_registry_driven() (+7 more)

### Community 96 - "generation.py"
Cohesion: 0.16
Nodes (25): _atomic_publish(), _cancel_generation(), checkpoint_path_for_job(), emit_generated_files(), finalize_generated_documents(), GenerationCancelled, _generator_version(), handle_generate() (+17 more)

### Community 98 - "family_adapter.py"
Cohesion: 0.07
Nodes (51): model_validator, SectionRule, ArtifactSpec, FamilyAdapter, Path, run_family_adapter(), default_ollama_model(), model_recommendations() (+43 more)

### Community 99 - "Paper Creator Excellence Programme Design"
Cohesion: 0.08
Nodes (23): Assessment Validity and Mark Schemes, Baseline on 26 August 2026, Definition of Done, Design Principles, Deterministic Visual Components, Empirical Calibration, Independent Solving, macOS Product Experience (+15 more)

### Community 100 - "required"
Cohesion: 0.13
Nodes (23): assessment_kind, cognitive_operation_distribution, command_family_distribution, command_word_distribution, comparison_basis, demand_distribution, evidence_gaps, evidence_policy_id (+15 more)

### Community 101 - "ShareholderCase"
Cohesion: 0.09
Nodes (5): Rehydrate the renderer's case only from the published source data., Return only facts and units printed on the candidate source page., Candidate-visible source contract for the Paper 1 shareholder decision., ShareholderCase, test_shareholder_case_keeps_equity_and_investor_figures_in_consistent_units()

### Community 102 - "properties"
Cohesion: 0.08
Nodes (24): type, type, minimum, type, type, null, string, type (+16 more)

### Community 103 - "mark_scheme_enrichment.py"
Cohesion: 0.23
Nodes (21): _answer_form(), _application_label(), _clean_text(), _compact_technical_guidance(), _deduplicate(), enrich_paper(), _enrich_question(), _level_guidance() (+13 more)

### Community 104 - "test_pdf_validation.py"
Cohesion: 0.17
Nodes (27): extract_pdf_evidence(), GlyphMetric, Counter, Path, Fail closed on malformed, substituted, annotated, or low-resolution PDFs., A compact, serialisable sample of one rendered PDF glyph., Extract print and accessibility evidence without retaining source prose. Glyph…, validate_pdf_for_release() (+19 more)

### Community 105 - "topic_id"
Cohesion: 0.29
Nodes (7): 4.10, 4.12, 4.2, topic_id, enum, title, type

### Community 106 - "$defs"
Cohesion: 0.09
Nodes (23): maximum, minimum, $defs, distribution, Observations, QuarantinedForm, SourceItem, tolerance (+15 more)

### Community 107 - "test_science_subjects.py"
Cohesion: 0.13
Nodes (18): ChemistryPlugin, equation_is_balanced(), _equation_side(), Formula, _multiplier(), _parse_group(), Any, Counter (+10 more)

### Community 108 - "required"
Cohesion: 0.09
Nodes (22): advertised, app_board, app_subject, backend_subject, blueprint_version, board, board_profile, content_mode (+14 more)

### Community 109 - "paths"
Cohesion: 0.07
Nodes (27): items, additionalProperties, allOf, items, minItems, $ref, title, type (+19 more)

### Community 110 - "required"
Cohesion: 0.10
Nodes (22): differential_item_functioning, discrimination, facility, item_id, median_time_seconds, responses, minimum, type (+14 more)

### Community 111 - "properties"
Cohesion: 0.09
Nodes (22): duration_minutes, sections, total_marks, additionalProperties, properties, required, title, type (+14 more)

### Community 112 - "accounting.py"
Cohesion: 0.31
Nodes (20): _accounting_endings(), accounting_outputs(), _appropriation(), _assets(), _exact(), _income(), _ledger(), _management() (+12 more)

### Community 113 - "stratum"
Cohesion: 0.29
Nodes (7): context-incomplete, core, mixed, stratum, enum, title, type

### Community 114 - "pastpapergen/notes.py"
Cohesion: 0.20
Nodes (19): _clean_chunk(), essay_capable_topic_ids(), _flush_note_chunk(), _is_exam_point(), _is_note_noise(), _looks_like_heading(), _note_chunks(), note_context_for_topic() (+11 more)

### Community 115 - "properties"
Cohesion: 0.10
Nodes (21): minLength, type, minLength, type, minLength, type, format, type (+13 more)

### Community 116 - "aqa_accounting_calibration.py"
Cohesion: 0.34
Nodes (14): _band(), build_generated_profile(), build_reference_profile(), build_report(), _command(), _fingerprint(), _inventory(), main() (+6 more)

### Community 117 - "emit"
Cohesion: 0.26
Nodes (16): build_parser(), handle_bundle_check(), main(), ArgumentParser, Namespace, Fail fast when a packaged backend is missing a dynamic generator., emit(), emit_progress() (+8 more)

### Community 118 - "required"
Cohesion: 0.12
Nodes (20): comparable_metrics, extraction_policy, feature_basis, non_comparable_features, objective_basis, paths, printed_marks, source_sha256 (+12 more)

### Community 119 - "test_accounting_objectives.py"
Cohesion: 0.22
Nodes (19): load_rule(), paper_for(), parametrize, test_accounting_ao3_short_analysis_does_not_imply_judgement(), test_accounting_does_not_offer_unallocated_objectives_in_guidance(), test_accounting_rejects_invalid_ao_even_if_marks_still_add_up(), test_accounting_rule_cannot_fall_back_to_generic_allocation(), test_accounting_uses_official_item_budgets_and_component_totals() (+11 more)

### Community 120 - "validate_generator_migration.py"
Cohesion: 0.24
Nodes (10): build_parser(), _layout_board(), main(), MigrationIssue, MigrationReport, MigrationValidator, Any, ArgumentParser (+2 more)

### Community 121 - "validate_mark_scheme_item"
Cohesion: 0.25
Nodes (17): _contains_any(), MarkSchemeQuality, _normalise(), Any, validate_mark_scheme_item(), _item(), test_accounting_follow_through_metadata_counts_as_method_guidance(), test_calculation_requires_method_or_working() (+9 more)

### Community 122 - "subject_plugins.py"
Cohesion: 0.19
Nodes (18): board_profile(), board_profile_ids(), BoardProfile, _normalise_identifier(), discover_subject_plugin(), _normalise_identifier(), register_subject_plugin(), subject_plugin_ids() (+10 more)

### Community 123 - "test_humanities_overlay.py"
Cohesion: 0.55
Nodes (9): map_diagram(), MapFeature, MapSpec, Drawing, timeline_diagram(), TimelineEvent, TimelineSpec, test_humanities_diagrams_reject_misleading_or_invalid_inputs() (+1 more)

### Community 124 - "CandidateResponse"
Cohesion: 0.12
Nodes (24): BoardLevelPolicy, LevelDescriptor, LevelOfResponseEngine, load_level_policies(), MarkAnnotation, MarkDecision, BaseModel, model_validator (+16 more)

### Community 125 - "ModelCoordinator"
Cohesion: 0.06
Nodes (27): Foundation, OllamaState, EstimateTuning, SecretStore, Any, String, AppClock, Date (+19 more)

### Community 126 - "ComputerSciencePlugin"
Cohesion: 0.23
Nodes (11): ComputerSciencePlugin, _evaluate_boolean(), normalise_pseudocode(), pseudocode_equivalent(), Any, truth_table(), test_computer_science_uses_the_specialised_plugin(), test_programming_paper_accepts_only_declared_languages_and_evidence() (+3 more)

### Community 127 - "generate_package"
Cohesion: 0.29
Nodes (12): generate_package(), Path, page_count(), Path, test_both_packages_render_36_page_question_papers(), test_invalid_paper_is_rejected(), test_paper_one_mark_scheme_matches_reference_question_sequence(), test_paper_one_section_a_matches_measured_case_and_account_pages() (+4 more)

### Community 128 - "_draw_cover"
Cohesion: 0.18
Nodes (16): economics_exam_schedule(), ExamSchedule, formatted_economics_exam_date(), date, _draw_boxes(), _draw_cover(), _draw_fake_barcode(), _draw_front_section() (+8 more)

### Community 129 - "properties"
Cohesion: 0.11
Nodes (18): type, format, type, type, minLength, type, minLength, type (+10 more)

### Community 130 - "properties"
Cohesion: 0.12
Nodes (17): type, properties, type, type, type, type, type, type (+9 more)

### Community 131 - "properties"
Cohesion: 0.12
Nodes (17): type, pattern, type, minLength, type, minLength, type, minLength (+9 more)

### Community 132 - "inspect_release_compliance"
Cohesion: 0.27
Nodes (14): Path, test_release_compliance_detects_a_tracked_secret_signature(), test_release_compliance_passes_for_the_repository(), test_release_compliance_rejects_unbounded_runtime_dependencies(), _check_dependencies(), _check_entitlements(), _check_font_licences(), _check_privacy_manifest() (+6 more)

### Community 133 - "SalesLedgerCase"
Cohesion: 0.24
Nodes (4): _gbp(), Single source of truth for the Paper 1 sales-ledger case. The question paper,…, Return one exact, independently checkable award point per mark., SalesLedgerCase

### Community 134 - "draw_barcode"
Cohesion: 0.30
Nodes (14): CanvasBarcodeStyle, draw_barcode(), draw_glyph_answer_rules(), draw_solid_answer_rules(), GlyphRuleStyle, Canvas, Draw a fixed number of solid response rules and return the next baseline., Draw selectable glyph-based response rules and return the next baseline. (+6 more)

### Community 135 - "enum"
Cohesion: 0.12
Nodes (16): algorithm-trace, calculation, computational-analysis, computational-design, constructed-response, extended-evaluation, mathematical-argument, multi-stage-calculation (+8 more)

### Community 136 - "IncomeStatementCase"
Cohesion: 0.17
Nodes (4): IncomeStatementCase, Decimal, Complete, internally consistent source for the Paper 1 company statement., _round_pounds()

### Community 137 - "independent_solver.py"
Cohesion: 0.12
Nodes (26): collect_credit_rules(), credit_rule(), CreditRule, declared_rule_metadata_present(), BaseModel, Origin-preserving open credit rules; never promote model advice to authority., Preserve numerical caps/dependencies, not just their descriptive prose.…, _as_mapping() (+18 more)

### Community 138 - "properties"
Cohesion: 0.12
Nodes (16): minLength, type, minLength, type, minLength, type, blueprint, contract (+8 more)

### Community 139 - "test_generator_migration.py"
Cohesion: 0.23
Nodes (13): Path, test_all_current_families_pass_declarative_migration_validation(), test_broken_fixture_reports_every_onboarding_surface(), test_scaffold_emits_complete_unadvertised_family_and_refuses_overwrite(), build_parser(), _cli_template(), main(), ArgumentParser (+5 more)

### Community 140 - "test_topic_reference_evidence.py"
Cohesion: 0.23
Nodes (15): module(), parametrize, A serialised hint must never override the question that will be printed., Only the versioned contract may establish a reference comparison., test_actual_same_topic_operation_and_mode_still_matches(), test_incomplete_context_and_keyword_only_membership_are_ineligible(), test_inherited_metadata_and_incidental_keywords_never_establish_topic_membership(), test_mixed_structure_anchors_are_task_matched_not_pooled() (+7 more)

### Community 141 - "test_aqa_business_calibration.py"
Cohesion: 0.53
Nodes (4): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence()

### Community 142 - "BiologyPlugin"
Cohesion: 0.43
Nodes (3): BiologyPlugin, Any, test_biology_requires_practical_and_data_provenance_when_declared()

### Community 143 - "31 August continued qualification findings"
Cohesion: 0.13
Nodes (14): 31 August continued qualification findings, Accounting objective and credit calibration verified, Closed-response integrity correction, Computer Science implementation — corrective review still open, Computer Science reviewed fix — separate live and layout limits, Difficulty Calibration v2 Qualification Report, Further calibration corrections in progress, Implemented evidence (+6 more)

### Community 144 - "Continued qualification — 31 August"
Cohesion: 0.13
Nodes (14): Continued qualification — 31 August, Difficulty Calibration v2 Implementation Plan, Global Constraints, Task 10: Supported-decision command calibration, Task 11: Visual review correction, Task 1: Reference profile schema v2, Task 2: Observable item demand contracts, Task 3: Solver-grounded difficulty judge (+6 more)

### Community 145 - "properties"
Cohesion: 0.15
Nodes (15): approved, draft, retired, type, type, null, string, minLength (+7 more)

### Community 146 - "required"
Cohesion: 0.13
Nodes (15): maximum_acceptable_facility, maximum_dif_gap, minimum_acceptable_facility, minimum_candidates, minimum_discrimination, minimum_double_marked_pairs, minimum_facility_coverage, minimum_group_responses (+7 more)

### Community 147 - "paper"
Cohesion: 0.33
Nodes (6): 1, 2, enum, title, type, paper

### Community 148 - "test_repository_hygiene.py"
Cohesion: 0.28
Nodes (10): test_committed_inventory_matches_the_current_repository(), test_every_tracked_file_has_a_durable_classification(), test_generated_and_binary_outputs_are_rejected(), test_maintained_visual_assets_are_classified_without_allowing_arbitrary_pngs(), test_root_lint_configuration_is_release_configuration(), Classification, classify_path(), inspect_repository() (+2 more)

### Community 149 - "additionalProperties"
Cohesion: 0.13
Nodes (15): items, minItems, type, uniqueItems, items, minItems, type, uniqueItems (+7 more)

### Community 150 - "id"
Cohesion: 0.13
Nodes (15): PathOption, minLength, title, type, items, minItems, title, type (+7 more)

### Community 151 - "aqa_business_calibration.py"
Cohesion: 0.34
Nodes (14): _band(), build_generated_profile(), build_reference_profile(), build_report(), _command(), _fingerprint(), _inventory(), main() (+6 more)

### Community 152 - "ocr_computer_science_calibration.py"
Cohesion: 0.34
Nodes (14): _band(), build_generated_profile(), build_reference_profile(), build_report(), _command(), _fingerprint(), _inventory(), main() (+6 more)

### Community 153 - "ocr_economics_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 154 - "Q: Where should performance and generated-paper accuracy fixes be made?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Where should performance and generated-paper accuracy fixes be made?, Source Nodes

### Community 155 - "enum"
Cohesion: 0.14
Nodes (14): analyse, contextualise, describe, design, explain, judge, program, retrieve (+6 more)

### Community 156 - "qualification_levels"
Cohesion: 0.14
Nodes (14): empirically_calibrated, engineering_validated, visually_calibrated, type, type, empirically_calibrated, engineering_validated, qualification_levels (+6 more)

### Community 157 - "Q: how can we make even more improvements to get the highest similarity in terms of structure and layout and quality of questions etc. and maybe all of the files in the project can be better organised. and the UI can be made to be much better and more geometrically apple-like by strictly following every single rule they outline in their HIG"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: how can we make even more improvements to get the highest similarity in terms of structure and layout and quality of questions etc. and maybe all of the files in the project can be better organised. and the UI can be made to be much better and more geometrically apple-like by strictly following every single rule they outline in their HIG, Source Nodes

### Community 158 - "Q: How does the generation quality pipeline connect?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: How does the generation quality pipeline connect?, Source Nodes

### Community 159 - "Assessment quality and originality"
Cohesion: 0.15
Nodes (13): AQA Computer Science examiner-feedback contract, Assessment quality and originality, Difficulty claims, Human release review, Independent solution and response-band qualification, Item transactions and two-pass generation, Mark-scheme quality, Measured visual qualification (+5 more)

### Community 160 - "Current-family visual qualification — 26 August 2026"
Cohesion: 0.15
Nodes (12): 1 September H1 task/source/demand qualification, 30 August Paper 2 mark-scheme regression check, 30 August shared-renderer and economics-scheme qualification, 31 August continued qualification, Accounting Paper 1, Automated evidence, Computer Science Paper 2, Current-family visual qualification — 26 August 2026 (+4 more)

### Community 161 - "Reference-Demand Calibration Design"
Cohesion: 0.15
Nodes (12): 1. Copyright-safe reference-demand profiles, 2. Item-level demand contracts, 3. Separate difficulty review, 4. Deterministic form-level demand audit, 5. App experience and evidence wording, Current Problem, Design, Failure Handling (+4 more)

### Community 162 - "required"
Cohesion: 0.15
Nodes (13): artifacts, created_at, evidence, gate_results, generator_id, model, reviewer_identity_class, seed (+5 more)

### Community 163 - "backend-protocol.schema.json"
Cohesion: 0.15
Nodes (12): event_id, job_id, protocol, timestamp, type, additionalProperties, allOf, $id (+4 more)

### Community 164 - "Q: How is the macOS backend bundle kept complete?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: How is the macOS backend bundle kept complete?, Source Nodes

### Community 165 - "exam_blueprints.py"
Cohesion: 0.26
Nodes (20): _demand_band(), _hydrate_assessment_metadata(), _objective_allocation(), _prompt_uses_command_word(), _structured_scheme(), validate_generated_paper(), validate_rule(), paper() (+12 more)

### Community 166 - "difficulty_calibration.py"
Cohesion: 0.40
Nodes (12): build_generated_profile(), build_reference_profile(), build_report(), _command(), _fingerprint(), main(), _page_count(), _pdf_text() (+4 more)

### Community 167 - "File Structure"
Cohesion: 0.17
Nodes (11): Assessment Reliability Core Implementation Plan, File Structure, Global Constraints, Subsequent Phase Plans, Task 1: Typed Item Contracts, Task 2: Role-Aware Numeric and Evidence Validation, Task 3: Item-Scoped Draft, Review, and Repair, Task 4: Atomic Checkpoints and Resume (+3 more)

### Community 168 - "required"
Cohesion: 0.17
Nodes (12): candidate_sample, facility_range, group_fairness_screen, independent_manual_review, internal_consistency, item_coverage, marker_standardisation, policy_approved (+4 more)

### Community 169 - "required"
Cohesion: 0.17
Nodes (12): difficulty_independently_verified, evidence_fingerprint, family, form_id, paper, policy, provenance, sample (+4 more)

### Community 170 - "Q: How does the paper fidelity audit produce per-document and per-role scores, and where should release thresholds integrate?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: How does the paper fidelity audit produce per-document and per-role scores, and where should release thresholds integrate?, Source Nodes

### Community 171 - "Q: Which Ollama model and live validation path does the project use for all supported papers?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Which Ollama model and live validation path does the project use for all supported papers?, Source Nodes

### Community 172 - "generator-capability.schema.json"
Cohesion: 0.17
Nodes (11): additionalProperties, $defs, safePath, $id, pattern, minLength, not, type (+3 more)

### Community 174 - "Architecture"
Cohesion: 0.18
Nodes (11): Architecture, Canonical registry, Extension contract, Failure containment, Fidelity qualification boundary, Package transaction, PDF portability and accessibility, Product boundary (+3 more)

### Community 175 - "End-to-end runtime"
Cohesion: 0.18
Nodes (11): 10. Completion and file handling, 1. Catalogue and selection, 2. Swift state and command construction, 3. Process bridge and event protocol, 4. Backend validation and dispatch, 5. Two different generation architectures, 6. Blueprint construction, 7. Provider behavior (+3 more)

### Community 176 - "Paper creator: deep project analysis"
Cohesion: 0.18
Nodes (11): Architectural pressure points, Current support and readiness, Difficulty and assessment validity, Executive assessment, Fidelity system: strengths and limits, Graphify project map, Paper creator: deep project analysis, Purpose and product boundary (+3 more)

### Community 177 - "Architecture"
Cohesion: 0.18
Nodes (10): Acceptance criteria, Architecture, Difficulty Calibration v2 Design, Form-level release gate, Independent calibration, Item targets, Purpose, Reference profiles (+2 more)

### Community 178 - "enum"
Cohesion: 0.18
Nodes (11): benchmark_done, benchmark_metric, benchmark_sample, done, error, file, hello, models (+3 more)

### Community 179 - "required"
Cohesion: 0.18
Nodes (11): collected_at, collector_role, consent_basis, dataset_id, row_level_data, source, specification_version, provenance (+3 more)

### Community 180 - "register_fonts"
Cohesion: 0.52
Nodes (5): register_font(), register_fonts(), _standard_fallback(), test_fallback_family_supports_bold_paragraph_markup(), test_missing_font_uses_registered_standard_font_alias()

### Community 181 - "PaperBlueprint"
Cohesion: 0.22
Nodes (19): _artifacts(), _cover_page(), _draw_extra_answer_page(), _draw_question_page_header(), _exam_date(), _formatted_exam_date(), _mark_scheme_annotations(), _mark_scheme_examiner_notes() (+11 more)

### Community 182 - "enum"
Cohesion: 0.40
Nodes (5): printed-conflicting, published-item-allocation, reconciled-published-aggregate, unknown, enum

### Community 183 - "profile_for"
Cohesion: 0.19
Nodes (21): profile_for(), items(), paths_module(), parametrize, test_complete_pairs_produce_six_eighty_mark_paths_not_cross_pairs(), test_correlated_source_vectors_cannot_pass_by_coordinatewise_bounds(), test_edexcel_leaf_only_marks_and_choice_groups(), test_explicit_selected_operation_is_not_relabelled_retrieval_in_audit() (+13 more)

### Community 184 - "macOS interaction and HIG compliance"
Cohesion: 0.22
Nodes (8): Accessibility verification, Commands and state, File workflow, Geometry and visual language, Information architecture, macOS interaction and HIG compliance, Onboarding and help, Settings

### Community 185 - "macOS UI audit"
Cohesion: 0.22
Nodes (9): 26 August native-workflow delta, 30 August responsive and accessibility pass, AI Settings, Final workspace, Hands-on verification status, Help and onboarding, HIG findings, macOS UI audit (+1 more)

### Community 186 - "Assessment-objective calibration reference"
Cohesion: 0.22
Nodes (8): Assessment-objective calibration reference, Component versus qualification percentages, Current Accounting form pattern, Economics and Business component audit, Edexcel short-response example, Meaning comes before totals, Qualitative examiner evidence, Verification boundary

### Community 187 - "Reference-Demand Calibration Implementation Plan"
Cohesion: 0.22
Nodes (8): Reference-Demand Calibration Implementation Plan, Task 1: Specify and validate the profile contract, Task 2: Derive compact profiles from real papers, Task 3: Add deterministic item and form demand audits, Task 4: Separate content review from difficulty review in the shared pipeline, Task 5: Integrate custom AQA Computer Science and Edexcel pipelines, Task 6: Record evidence in registry, manifests and app UI, Task 7: Verify all supported outputs and finish cleanly

### Community 188 - "Paper creator"
Cohesion: 0.22
Nodes (9): Architecture and quality analysis, Build Checks, CLI, Development Reference Corpus, Paper creator, Privacy, Recommended Ollama model, Run (+1 more)

### Community 189 - "enum"
Cohesion: 0.22
Nodes (9): anthropic, apple, ollama, openai, enum, supported_providers, items, type (+1 more)

### Community 190 - "required"
Cohesion: 0.22
Nodes (9): blueprint, contract, prompt, renderer, syllabus, versions, additionalProperties, required (+1 more)

### Community 191 - "required"
Cohesion: 0.22
Nodes (9): detail, qualification, title, required, checks, id, items, type (+1 more)

### Community 192 - "properties"
Cohesion: 0.33
Nodes (9): type, null, string, properties, type, digest, name, provider (+1 more)

### Community 193 - "PhysicsPlugin"
Cohesion: 0.43
Nodes (3): PhysicsPlugin, Any, test_physics_requires_uncertainty_for_uncertainty_items()

### Community 194 - "Implementation and fidelity report"
Cohesion: 0.25
Nodes (7): Automated and visual evidence, Implementation and fidelity report, Implemented architecture, Live-model evidence boundary, Model guidance, Publication boundary, Release outcome

### Community 195 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Measured Paper Fidelity Implementation Plan, Task 1: Page-role-aware fidelity evidence, Task 2: Shared board answer-page geometry, Task 3: OCR response and blank-page grammar, Task 4: Shared mark-scheme cover calibration, Task 5: Full visual qualification and regression gate

### Community 196 - "Rendering and Mark-Scheme Reliability Implementation Plan"
Cohesion: 0.25
Nodes (7): Rendering and Mark-Scheme Reliability Implementation Plan, Task 1: Bounded atomic render transactions, Task 2: Route every generator family through the transaction, Task 3: Artifact containment, collision, and density evidence, Task 4: Mark-scheme depth contracts, Task 5: OCR Economics pagination regression, Task 6: Phase qualification

### Community 197 - "required"
Cohesion: 0.25
Nodes (8): approval_evidence, approved_by_identity_class, policy_id, status, additionalProperties, required, type, policy

### Community 198 - "sample"
Cohesion: 0.25
Nodes (8): candidates, groups, response_rows, items, sample, additionalProperties, required, type

### Community 199 - "enum"
Cohesion: 0.25
Nodes (8): failed, not_applicable, not_run, passed, enum, additionalProperties, type, gate_results

### Community 200 - "empirical-calibration.schema.json"
Cohesion: 0.25
Nodes (7): additionalProperties, $id, not, anyOf, $schema, title, type

### Community 201 - "Question"
Cohesion: 0.19
Nodes (17): Question, _continuation_guidance_lines(), _draw_mark_scheme_continuation_frame(), _draw_paper1_reference_solution_page(), _draw_scheme_text(), _draw_validation_evidence_terminal(), _mark_scheme_table_header(), _paper1_reference_code() (+9 more)

### Community 202 - "_call_name"
Cohesion: 0.38
Nodes (6): Call, _call_name(), parametrize, Path, test_production_pdf_renderers_run_inside_atomic_transactions(), test_shared_family_adapter_owns_atomic_pdf_transaction()

### Community 203 - "build_backend.sh"
Cohesion: 0.29
Nodes (5): MPLCONFIGDIR, PYINSTALLER_CONFIG_DIR, PYTHONPATH, build_backend.sh script, XDG_CACHE_HOME

### Community 204 - "_draw_stimulus"
Cohesion: 0.13
Nodes (15): GraphParams, _bar_label(), _draw_axis_arrow(), _draw_bar_chart(), _draw_blank_answer_axes(), _draw_context_box(), _draw_data_table(), _draw_inline_context() (+7 more)

### Community 205 - "enum"
Cohesion: 0.29
Nodes (7): automation, examiner, internal_reviewer, psychometrician, subject_specialist, reviewer_identity_class, enum

### Community 206 - ".initialEstimate"
Cohesion: 0.19
Nodes (11): EstimateFactor, GenerationEstimate, .etaDate, .remainingText, TimeInterval, GenerationEstimator, Bool, Date (+3 more)

### Community 207 - "model"
Cohesion: 0.29
Nodes (7): digest, name, provider, additionalProperties, required, type, model

### Community 208 - "generator/tests/test_closed_response_integrity.py"
Cohesion: 0.28
Nodes (15): require_solution_matches_scheme(), _part_solver_item(), candidate_stimulus_data(), Describe visible figure content for text-only independent solvers., classification(), parametrize, test_authoring_merge_preserves_closed_key_through_final_solver(), test_classification_slot_contract_reaches_solver_without_answers() (+7 more)

### Community 209 - "_written"
Cohesion: 0.36
Nodes (7): _nearest_hundred(), _levels(), Topic, _written(), test_company_and_partnership_schemes_expose_complete_working_data(), test_locked_calculation_schemes_are_exactly_derived_from_the_case_data(), test_locked_calculation_schemes_include_final_answers_and_all_case_numbers()

### Community 210 - "macOS user-experience audit"
Cohesion: 0.33
Nodes (6): HIG-specific findings, macOS user-experience audit, Observed first-use sheet, Observed generation state, Observed workspace, What is already Apple-like

### Community 211 - "formatted_generation_date"
Cohesion: 0.15
Nodes (22): CoverProfile, _draw_aqa_mark_scheme_cover(), _draw_cover_barcode(), draw_mark_scheme_cover(), _draw_ocr_mark_scheme_cover(), _wrap(), formatted_generation_date(), formatted_generation_series() (+14 more)

### Community 212 - "test_aqa_accounting_calibration.py"
Cohesion: 0.53
Nodes (4): report(), test_both_papers_pass_multi_seed_automated_checks(), test_external_difficulty_gates_remain_false(), test_reference_evidence_is_aggregate_only()

### Community 213 - "qualification-schema.json"
Cohesion: 0.33
Nodes (5): additionalProperties, $id, $schema, title, type

### Community 214 - "QuestionPaperCover"
Cohesion: 0.29
Nodes (3): QuestionPaperCover, Fixed-grid, board-shaped front page without copying protected artwork., Return the renderer-neutral representation used for qualification.

### Community 215 - "test_difficulty_calibration.py"
Cohesion: 0.53
Nodes (4): report(), test_calibration_retains_no_official_text_or_paths(), test_difficulty_is_not_promoted_without_human_and_psychometric_evidence(), test_every_paper_has_multi_seed_structural_evidence()

### Community 216 - "paper1_assets.py"
Cohesion: 0.50
Nodes (11): _page_footer(), _paragraph(), _practice_header(), Canvas, PaperBlueprint, Path, render_electronic_answer_document(), render_preliminary_material() (+3 more)

### Community 217 - "cspapergen/cli.py"
Cohesion: 0.09
Nodes (36): BuildResult, extract_pdf_text(), Extract stable reading-order text without a Poppler CLI dependency., default_output_dir(), generate_package(), _improve(), main(), Path (+28 more)

### Community 218 - "generator_working_directory"
Cohesion: 0.40
Nodes (4): generator_working_directory(), MonkeyPatch, fixture, FixtureRequest

### Community 220 - "Cambridge International engineering foundation — 26 August 2026"
Cohesion: 0.40
Nodes (4): Cambridge International engineering foundation — 26 August 2026, Deliberate release gate, Implemented evidence, Scope

### Community 221 - "pull_request_template.md"
Cohesion: 0.50
Nodes (3): Risk, Verification, What changed

### Community 222 - "xcbuild.sh"
Cohesion: 0.67
Nodes (3): HOME, xcbuild.sh script, usage()

### Community 223 - "enum"
Cohesion: 0.50
Nodes (4): ai-assisted, deterministic, enum, content_mode

### Community 224 - "capabilities"
Cohesion: 0.50
Nodes (4): items, type, type, capabilities

### Community 225 - "progress"
Cohesion: 0.50
Nodes (4): maximum, minimum, type, progress

### Community 226 - "tool_versions"
Cohesion: 0.50
Nodes (4): type, tool_versions, additionalProperties, type

### Community 230 - "app_board"
Cohesion: 0.67
Nodes (3): minLength, type, app_board

### Community 231 - "app_subject"
Cohesion: 0.67
Nodes (3): minLength, type, app_subject

### Community 232 - "blueprint_version"
Cohesion: 0.67
Nodes (3): minLength, type, blueprint_version

### Community 233 - "entry_point"
Cohesion: 0.67
Nodes (3): pattern, type, entry_point

### Community 234 - "package"
Cohesion: 0.67
Nodes (3): pattern, type, package

### Community 235 - "specification_version"
Cohesion: 0.67
Nodes (3): specification_version, minLength, type

### Community 236 - "subject"
Cohesion: 0.67
Nodes (3): subject, pattern, type

### Community 237 - "subject_plugin"
Cohesion: 0.67
Nodes (3): subject_plugin, pattern, type

### Community 262 - "add_page_structure_tree"
Cohesion: 0.31
Nodes (9): add_page_structure_tree(), has_logical_page_order(), _has_structure_tree(), _new_object(), Document, Page, Path, Attach a deterministic page-level structure tree and marked content. Each page… (+1 more)

### Community 263 - "test_source_candidate_paths.py"
Cohesion: 0.36
Nodes (9): module(), test_aqa_selected_source_operations_do_not_manufacture_objective_tags(), test_business_edition_does_not_assume_same_question_numbers(), test_clean_ocr_mcq_rows_keep_published_ao_and_non_retrieval_operations(), test_edexcel_2024_selected_subparts_use_actual_operations_without_command_leakage(), test_edexcel_source_extraction_does_not_duplicate_overview_and_answer_pages(), test_ocr_conflicting_grids_are_quarantined_with_original_hashes(), test_source_and_generated_response_modes_use_same_operation_definition() (+1 more)

### Community 264 - "render_source_booklet"
Cohesion: 0.31
Nodes (9): _draw_crop_marks(), _draw_source_content_page(), _extract_source_questions(), _pad_pdf_pages(), Syllabus, render_source_booklet(), _source_reading_prompt(), _source_sections() (+1 more)

### Community 265 - "topic_reference_evidence.py"
Cohesion: 0.43
Nodes (7): audit_topic_bank(), matching_records(), Any, Reviewed feature-only AQA 2022-25 topic subsets, never topic AO targets.…, Require task/context membership and an evidenced response form. A stimulus…, reviewed_topic_records(), task_features()

### Community 266 - "aqa_front_matter_pages"
Cohesion: 0.47
Nodes (4): aqa_front_matter_pages(), Flowable, Shared examiner instructions belong in one introduction, not every section., test_aqa_common_marking_guidance_is_emitted_once_per_scheme()

### Community 267 - "test_ocr_computer_science_calibration.py"
Cohesion: 0.53
Nodes (4): report(), test_difficulty_remains_external_evidence_gated(), test_multi_seed_structural_demand_passes(), test_reference_evidence_is_aggregate_only()

### Community 269 - "WorkspaceLayoutMode"
Cohesion: 0.12
Nodes (11): CGFloat, Bool, WorkspaceLayoutMode, compact, expanded, .showsInspector, .showsSidebar, standard (+3 more)

## Knowledge Gaps
- **1108 isolated node(s):** `BoardLayout`, `examforge-aqa-accounting`, `$schema`, `$id`, `title` (+1103 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **29 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `IndependentSolver` connect `IndependentSolver` to `GeneratedQuestion`, `load_syllabus`, `independent_solver.py`, `pastpapergen/ollama_client.py`, `GeneratedPaper`, `test_ollama_generation.py`, `test_sql_answer_verification.py`, `test_aqa_business.py`, `reconcile_solution`, `test_task_source_demand.py`, `test_source_credit_integrity.py`, `test_open_credit_reconciliation.py`, `cspapergen/ollama_client.py`, `test_solver_source_adapter.py`, `test_finite_response_slots.py`, `test_aqa_economics.py`, `generator/tests/test_assessment_contracts.py`, `NumericOutput`, `test_aqa_accounting.py`, `test_computer_science_objectives.py`, `generator/tests/test_closed_response_integrity.py`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Why does `GeneratedPaper` connect `GeneratedPaper` to `GeneratedQuestion`, `ocregen/render_pdf.py`, `Paragraph`, `AssessmentContract`, `ocrcsgen/render_pdf.py`, `test_aqa_business.py`, `reconcile_solution`, `aqabizgen/render_pdf.py`, `test_task_source_demand.py`, `exam_blueprints.py`, `AssessmentCheckpointStore`, `assessment_package.py`, `test_ocr_economics.py`, `aqaecongen/render_pdf.py`, `test_aqa_economics.py`, `document_dsl/__init__.py`, `test_aqa_accounting.py`, `test_computer_science_objectives.py`, `test_reference_demand.py`, `family_adapter.py`, `mark_scheme_enrichment.py`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Why does `GeneratedQuestion` connect `GeneratedQuestion` to `ocregen/render_pdf.py`, `GeneratedPaper`, `Paragraph`, `AssessmentContract`, `ocrcsgen/render_pdf.py`, `test_aqa_business.py`, `reconcile_solution`, `aqabizgen/render_pdf.py`, `test_task_source_demand.py`, `exam_blueprints.py`, `AssessmentCheckpointStore`, `assessment_package.py`, `test_ocr_economics.py`, `aqaecongen/render_pdf.py`, `test_aqa_economics.py`, `profile_for`, `test_computer_science_objectives.py`, `_written`, `test_reference_demand.py`, `family_adapter.py`, `mark_scheme_enrichment.py`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Are the 21 inferred relationships involving `GeneratedQuestion` (e.g. with `AssessmentLLMClient` and `GenerationPolicy`) actually correct?**
  _`GeneratedQuestion` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `IndependentSolver` (e.g. with `AssessmentLLMClient` and `GenerationPolicy`) actually correct?**
  _`IndependentSolver` has 27 INFERRED edges - model-reasoned connections that need verification._
- **What connects `BoardLayout`, `examforge-aqa-accounting`, `$schema` to the rest of the system?**
  _1108 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ExamBoardOption` be split into smaller, more focused modules?**
  _Cohesion score 0.06708595387840671 - nodes in this community are weakly interconnected._