# Graph Report - .  (2026-09-30)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 6718 nodes · 19555 edges · 246 communities (215 shown, 31 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 1193 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `690cce3f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ApplicationCoordinator
- GeneratedQuestion
- Text
- paper_fidelity_audit.py
- build_paper_blueprint
- live_generation_matrix.py
- String
- load_syllabus
- AssessmentContract
- cspapergen/render_pdf.py
- RecentDocumentStore
- psychometrics.py
- pastpapergen/generator.py
- pastpapergen/render_pdf.py
- .body
- test_reference_evidence_validation.py
- Paragraph
- GeneratedPaper
- build_question
- require_difficulty_review
- Question
- test_aqa_business.py
- ocrcsgen/render_pdf.py
- ocregen/render_pdf.py
- pastpapergen/ollama_client.py
- AssessmentCheckpointStore
- sql_contracts.py
- CodingKeys
- test_aqa_economics.py
- CoverProfile
- test_sql_answer_verification.py
- ExamBoardOption
- properties
- providers.py
- test_ocr_economics.py
- test_render_pdf.py
- aqabizgen/render_pdf.py
- render_pdf_atomically
- solve_selected_response
- generator/tests/test_assessment_contracts.py
- HelpTopic
- EconomicsSource
- properties
- aqaecongen/render_pdf.py
- reference_corpus.py
- DocumentPreviewView
- test_mlx_setup.py
- NumericOutput
- properties
- objective_policy_for
- test_open_credit_reconciliation.py
- test_layout_master.py
- CodingKeys
- assessment_package.py
- test_mark_scheme_layout.py
- PaperCreatorTests
- BackendClient
- pastpapergen/cli.py
- reconcile_solution
- build_item_demand_target
- type
- test_shared_numeric_integrity.py
- test_assessment_checkpoints.py
- independent_solver.py
- test_computer_science_objectives.py
- test_document_dsl.py
- exam_blueprints.py
- Foundation
- properties
- required
- cspapergen/ollama_client.py
- benchmark.py
- ExamPageProfile
- runtime.py
- CandidateResponse
- IndependentSolver
- Rect
- Size
- aqa_section_intro
- open_credit.py
- properties
- build_paper
- test_solver_source_adapter.py
- configuredgen/render_pdf.py
- document_dsl/__init__.py
- test_aqa_accounting.py
- pdf_validation.py
- SubjectValidation
- mathematics.py
- test_reference_demand.py
- test_pdf_validation.py
- test_app_backend.py
- graphs.py
- test_science_subjects.py
- $defs
- _mark_scheme_rows
- test_coverage_matrix.py
- ReferenceIndex
- nsi.py
- mark_scheme_enrichment.py
- generation.py
- properties
- test_topic_reference_evidence.py
- subject_plugins.py
- emit
- accounting.py
- AIProvider
- required
- ShareholderCase
- AnswerSpace
- corpus.py
- PathSection
- properties
- required
- pastpapergen/notes.py
- properties
- ocr_computer_science_calibration.py
- _written
- test_accounting_objectives.py
- validate_generator_migration.py
- provider.py
- NSIExercise
- generator_registry.py
- validate_mark_scheme_item
- test_computer_science_subject.py
- build_layout_masters.py
- draw_barcode
- test_science_overlay.py
- required
- generate_package
- PaperBlueprint
- candidate_identity.py
- points
- register_fonts
- generator/tests/test_closed_response_integrity.py
- reference-demand-profile.schema.json
- properties
- properties
- test_candidate_paths.py
- inspect_release_compliance
- enum
- CandidateTopology
- IncomeStatementCase
- SalesLedgerCase
- _draw_cover
- properties
- paths
- test_generator_migration.py
- required
- NonCurrentAssetCase
- test_repository_hygiene.py
- ocrcsgen/generator.py
- additionalProperties
- id
- aqa_accounting_calibration.py
- aqa_business_calibration.py
- ocr_economics_calibration.py
- ReportLabBackend
- enum
- properties
- qualification_levels
- PartnershipCase
- test_source_candidate_paths.py
- backend-protocol.schema.json
- properties
- difficulty_calibration.py
- topic_reference_evidence.py
- required
- topic_id
- required
- string
- render_source_booklet
- generator-capability.schema.json
- paper1_reference_code
- record_review
- test_humanities_overlay.py
- _BooleanParser
- enum
- required
- required
- cspapergen/notes.py
- ObjectivePolicy
- properties
- enum
- save_failure_diagnostic
- required
- SubjectPlugin
- PhysicsPlugin
- .baseQuery
- sample
- enum
- objective_basis
- candidate_stimulus_data
- empirical-calibration.schema.json
- _call_name
- build_backend.sh
- enum
- specification_version
- model
- enum
- ocrcsgen/syllabus.py
- CostingCase
- non_comparable_features
- test_aqa_accounting_calibration.py
- test_aqa_business_calibration.py
- test_difficulty_calibration.py
- test_ocr_economics_calibration.py
- generator_working_directory
- section_features
- xcbuild.sh
- capabilities
- .model_operations_must_be_unique
- diagnose.sh
- move_to_trash.sh
- run_app_macos.sh
- GraphParams
- app_board
- backend_subject
- blueprint_version
- entry_point
- id
- subject_plugin
- france/__init__.py
- Core/__init__.py
- layouts.py
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

## God Nodes (most connected - your core abstractions)
1. `GeneratedQuestion` - 216 edges
2. `build_paper_blueprint()` - 182 edges
3. `load_syllabus()` - 172 edges
4. `load_builtin_paper_config()` - 166 edges
5. `ApplicationCoordinator` - 153 edges
6. `IndependentSolver` - 152 edges
7. `GeneratedOption` - 124 edges
8. `reconcile_solution()` - 98 edges
9. `GeneratedPaper` - 96 edges
10. `load_syllabus()` - 85 edges

## Surprising Connections (you probably didn't know these)
- `test_renderer_rejects_unsupported_indicative_label()` --calls--> `_indicative_objective()`  [INFERRED]
  tests/test_accounting_objectives.py → Resources/accounting/aqa/generator/aqaaccountgen/render_pdf.py
- `test_paraphrased_cpu_credit_still_prints_its_actual_typed_one_mark_allocations()` --calls--> `build_paper2_blueprint()`  [INFERRED]
  tests/test_open_credit_reconciliation.py → Resources/computer-science/aqa/generator/cspapergen/generator.py
- `test_preview_seed_database_bank_preserves_required_sql_error_analysis()` --calls--> `build_topic_question_bank()`  [INFERRED]
  tests/test_topic_reference_evidence.py → Resources/computer-science/aqa/generator/cspapergen/generator.py
- `FirstPassClient` --uses--> `GenerationPolicy`  [INFERRED]
  tests/test_assessment_checkpoints.py → Backend/Core/ai_assessment.py
- `FirstPassDifficultyClient` --uses--> `GenerationPolicy`  [INFERRED]
  tests/test_assessment_checkpoints.py → Backend/Core/ai_assessment.py

## Import Cycles
- None detected.

## Communities (246 total, 31 thin omitted)

### Community 0 - "ApplicationCoordinator"
Cohesion: 0.03
Nodes (60): AnyCancellable, DateFormatter, .body, AppDefaults, AppLinks, Bool, String, URL (+52 more)

### Community 1 - "GeneratedQuestion"
Cohesion: 0.05
Nodes (132): AssessmentLLMClient, _batches_for_client(), _bounded_text(), _candidate_question(), _canonical_objective_allocation(), _clean_generated_prompt(), _contains_command_word(), _demand_item() (+124 more)

### Community 2 - "Text"
Cohesion: 0.03
Nodes (106): Charts, GenerationQualityState, KeyPath, View, GeneratedFilesTable, PanelEmptyState, .body, String (+98 more)

### Community 3 - "paper_fidelity_audit.py"
Cohesion: 0.05
Nodes (103): Pixmap, parametrize, Path, test_compact_profile_omits_raster_geometry(), test_contact_sheets_make_visual_review_artifacts(), test_generated_document_falls_back_to_nested_transaction_output(), test_generated_document_supports_app_per_paper_directories(), test_metric_callout_names_print_resolution_comparison_dimensions() (+95 more)

### Community 4 - "build_paper_blueprint"
Cohesion: 0.07
Nodes (103): build_paper_blueprint(), PaperBlueprint, Syllabus, load_builtin_paper_config(), review_table_rows(), load_syllabus(), Path, Syllabus (+95 more)

### Community 5 - "live_generation_matrix.py"
Cohesion: 0.05
Nodes (82): default_ollama_model(), model_recommendations(), OllamaModelRecommendations, OllamaModelTier, parse_model_recommendations(), Any, _required_text(), Release qualification evidence and policy models. (+74 more)

### Community 6 - "String"
Cohesion: 0.04
Nodes (88): Decodable, Equatable, Hashable, Identifiable, AssessmentKind, fullPaper, questionBank, .title (+80 more)

### Community 7 - "load_syllabus"
Cohesion: 0.06
Nodes (84): identity_for_blueprint(), _build(), build_paper1_blueprint(), build_paper2_blueprint(), build_topic_question_bank(), PaperBlueprint, Syllabus, improve_questions_with_ollama() (+76 more)

### Community 8 - "AssessmentContract"
Cohesion: 0.06
Nodes (70): AssessmentContract, contract_for_question(), EvidenceRecord, GeneratedNumericField, GraphContract, _numeric_contracts(), NumericRole, NumericValueContract (+62 more)

### Community 9 - "cspapergen/render_pdf.py"
Cohesion: 0.10
Nodes (77): printed_credit_points(), Same actual text/allocation projection for renderer and adjudicator., _answer_line_count(), _answer_lines_paginated(), _candidate_fields(), _cover_page(), _cover_section(), _draw_adjacency_matrix_answers() (+69 more)

### Community 10 - "RecentDocumentStore"
Cohesion: 0.06
Nodes (38): Codable, FileManager, GenerationJobState, LocalizedError, ExamCatalog, GenerationConfiguration, GenerationJobRecord, .missingArtifactCount (+30 more)

### Community 11 - "psychometrics.py"
Cohesion: 0.08
Nodes (56): CalibrationMetadata, CalibrationStore, ConsentRecord, _normalise_row(), Any, Path, Encrypted local storage for row-level calibration evidence. Keys are…, _read_rows() (+48 more)

### Community 12 - "pastpapergen/generator.py"
Cohesion: 0.06
Nodes (72): MultipleChoiceOption, _adapt_paper_three_case_guidance(), _best_section_a_context_point(), _build_part(), _build_parts(), _choice_group_name(), _choice_lookup(), _choose_topic() (+64 more)

### Community 13 - "pastpapergen/render_pdf.py"
Cohesion: 0.08
Nodes (71): _answer_line_count(), _axis_labels_for_draw_prompt(), _draw_answer_lines(), _draw_answer_lines_until(), _draw_axis_arrow(), _draw_bar_chart(), _draw_blank_answer_axes(), _draw_calculate_part_with_working_lines() (+63 more)

### Community 14 - ".body"
Cohesion: 0.04
Nodes (50): App, CGFloat, Commands, AppCommands, PaperCreator, .body, Bool, WorkspaceLayoutMode (+42 more)

### Community 15 - "test_reference_evidence_validation.py"
Cohesion: 0.06
Nodes (53): audit_candidate_paths(), CandidatePath, CandidateTopology, enumerate_candidate_paths(), identity(), path_metrics(), PathOption, PathSection (+45 more)

### Community 16 - "Paragraph"
Cohesion: 0.11
Nodes (63): Paragraph, _artifacts(), _accounting_marking_guidance_pages(), _accounting_system_case(), _additional_answer_page(), _appropriation_answer_table(), _assessment_objectives_page(), _candidate_verification_rows() (+55 more)

### Community 17 - "GeneratedPaper"
Cohesion: 0.09
Nodes (53): AppliedMCQSource, GeneratedPaper, GeneratedSection, PaperRule, BaseModel, QuestionRule, mcqs(), q() (+45 more)

### Community 18 - "build_question"
Cohesion: 0.17
Nodes (64): model_validator, Stimulus, _assembly_program_question(), _assembly_trace_question(), _big_data_question(), _big_data_short_question(), _binary_short_question(), _bitmap_question() (+56 more)

### Community 19 - "require_difficulty_review"
Cohesion: 0.10
Nodes (58): CandidateContentIdentity, _candidate_task_facts(), difficulty_review(), DifficultyReviewResult, independent_review(), JSONClient, _public_task_operation_evidence(), PublicTaskOperationEvidence (+50 more)

### Community 20 - "Question"
Cohesion: 0.08
Nodes (52): OllamaClient, Standalone subject generators use the same transport as the app., Render only public schema facts; no worked query is present., render_sql_schema(), SQLSourceContract, derive_task_semantics(), Any, BaseModel (+44 more)

### Community 21 - "test_aqa_business.py"
Cohesion: 0.06
Nodes (48): generate_package(), Path, FinancialPosition, format_number(), The single source of truth for Paper 1 financial-statement figures., Format an exam answer without meaningless trailing zeroes., build_paper(), _extract() (+40 more)

### Community 22 - "ocrcsgen/render_pdf.py"
Cohesion: 0.06
Nodes (51): ExamPage, Flowable, A full-page shell that can also live inside a Platypus story., AnswerLineFlowable, AQACompactAnswerLines, OCRComputerScienceAnswerLines, Flowable, Return a Table subclass whose raw string cells use the controlled font.… (+43 more)

### Community 23 - "ocregen/render_pdf.py"
Cohesion: 0.09
Nodes (56): OCRAnswerLines, OCR dotted writing rules inside the existing allocated answer area. Reviewed…, _artifacts(), _add_economics_diagram(), _add_firm_objectives_diagram(), _add_ppf_diagram(), _annotation_conventions_page(), _answer_mark() (+48 more)

### Community 24 - "pastpapergen/ollama_client.py"
Cohesion: 0.08
Nodes (52): QuestionBlueprint, SyllabusTopic, build_question_prompt(), _clean_prompt(), generate_questions_with_ollama(), _has_word_starts(), _matches_expected_question_style(), _merge_part_prompt() (+44 more)

### Community 25 - "AssessmentCheckpointStore"
Cohesion: 0.07
Nodes (39): AssessmentCheckpointStore, CheckpointCorrupt, Any, Path, ValueError, Persist independently accepted questions without partial JSON writes., ArtifactSpec, BuildResult (+31 more)

### Community 26 - "sql_contracts.py"
Cohesion: 0.10
Nodes (42): _contract_column(), _Count, _equality(), _Field, _finding(), fitness_centre_sql_contract(), _Frozen, _has_sql_statement_shape() (+34 more)

### Community 27 - "CodingKeys"
Cohesion: 0.04
Nodes (57): CodingKey, CodingKeys, assessmentKind, backendVersion, capabilities, checks, code, command (+49 more)

### Community 28 - "test_aqa_economics.py"
Cohesion: 0.07
Nodes (48): _tasks(), Return the immutable rules for one printed option (one-based)., resolve_question_rules(), generate_package(), main(), Path, build_paper(), Syllabus (+40 more)

### Community 29 - "CoverProfile"
Cohesion: 0.08
Nodes (37): aqa_question_cover(), CoverProfile, _draw_aqa_mark_scheme_cover(), _draw_cover_barcode(), draw_mark_scheme_cover(), _draw_ocr_mark_scheme_cover(), mark_scheme_cover(), MarkSchemeCover (+29 more)

### Community 30 - "test_sql_answer_verification.py"
Cohesion: 0.11
Nodes (50): profile_for(), Validate the answer and every model-presented full statement separately., sql_source_intent_sha256(), validate_sql_response(), _difficulty_candidate(), _difficulty_solution(), _part_demand_item(), _part_solver_projection() (+42 more)

### Community 31 - "ExamBoardOption"
Cohesion: 0.07
Nodes (37): CatalogSubject, ExamBoardOption, .fullPapers, .isReady, .questionBanks, .usesAI, .defaultBoard, SidebarItem (+29 more)

### Community 32 - "properties"
Cohesion: 0.04
Nodes (55): anyOf, default, title, QuarantinedForm, const, title, type, minLength (+47 more)

### Community 33 - "providers.py"
Cohesion: 0.08
Nodes (45): _hosted_client(), _aqa_cs_part_count(), _edexcel_part_count(), hosted_client(), HostedLLMClient, _normalise_base_url(), _ollama_json_schema(), _ollama_output_budget() (+37 more)

### Community 34 - "test_ocr_economics.py"
Cohesion: 0.08
Nodes (47): percentage_change_context(), Candidate chart endpoints and the requested one-decimal percentage output., generate_package(), Path, build_paper(), _evaluation_scheme(), _extract(), _extract_number() (+39 more)

### Community 35 - "test_render_pdf.py"
Cohesion: 0.13
Nodes (49): render_question_paper(), _answer_rule_count(), _blank_axis_lines(), _blueprint_with_section_a_question(), _dark_pixels(), _first_page_containing(), _normalised(), _pdf_page_count() (+41 more)

### Community 36 - "aqabizgen/render_pdf.py"
Cohesion: 0.12
Nodes (48): aqa_front_matter_pages(), Flowable, AQAAnswerLines, SelectedResponseContract, _artifacts(), _additional_answer_page(), _ao_summary(), _assessment_objectives_page() (+40 more)

### Community 37 - "render_pdf_atomically"
Cohesion: 0.09
Nodes (44): add_page_structure_tree(), has_logical_page_order(), _has_structure_tree(), _new_object(), Document, Page, Path, Attach a deterministic page-level structure tree and marked content. Each page… (+36 more)

### Community 38 - "solve_selected_response"
Cohesion: 0.09
Nodes (47): _better_than_target(), _decimal(), _display_decimal(), _money_choice(), _numeric_choice(), _percent_choice(), _plain_decimal(), Any (+39 more)

### Community 39 - "generator/tests/test_assessment_contracts.py"
Cohesion: 0.09
Nodes (48): _question_solver_item(), paper(), parametrize, test_actual_level_tariffs_have_distinct_usable_band_descriptors(), test_all_seeded_styles_have_contract_credit_not_topic_note_filler(), test_business_expansion_short_credit_marks_one_complete_route(), test_complete_declared_numeric_operations_have_literal_answers(), test_content_driven_policy_is_reproducible_and_does_not_reclassify_other_documents() (+40 more)

### Community 40 - "HelpTopic"
Cohesion: 0.17
Nodes (12): CaseIterable, HelpTopic, checkingQuality, choosingAModel, creatingAPaper, gettingStarted, .id, privacy (+4 more)

### Community 41 - "EconomicsSource"
Cohesion: 0.09
Nodes (35): calculation(), calculation_label(), calculation_prompt(), calculation_working(), EconomicsSource, BaseModel, Decimal, model_validator (+27 more)

### Community 42 - "properties"
Cohesion: 0.05
Nodes (48): anyOf, title, minLength, title, type, const, title, type (+40 more)

### Community 43 - "aqaecongen/render_pdf.py"
Cohesion: 0.11
Nodes (45): _artifacts(), level_guidance(), level_rows(), LevelRow, Return the AQA Economics response bands for a supported tariff., _assessment_objectives_table(), _context_data_table(), _context_first_page() (+37 more)

### Community 44 - "reference_corpus.py"
Cohesion: 0.13
Nodes (45): MonkeyPatch, Path, test_document_path_requires_filename(), test_document_path_stays_inside_corpus(), test_download_manifest_records_failure_and_continues(), test_parse_aqa_resources_filters_modified_papers(), test_parse_ocr_resources_uses_a_level_tab_only(), test_parse_ocr_specifications_keeps_a_level_not_as_level() (+37 more)

### Community 45 - "DocumentPreviewView"
Cohesion: 0.05
Nodes (38): AppKit, Combine, DocumentPreviewView, .body, .exportAlertBinding, .provenanceRecord, .selectedBinding, .selectedFile (+30 more)

### Community 46 - "test_mlx_setup.py"
Cohesion: 0.09
Nodes (44): _available_cache_bytes(), ensure_mlx_ready(), handle_mlx_status(), handle_setup_mlx(), install_mlx_runtime(), is_managed_development_environment(), load_mlx_model(), mlx_runtime_available() (+36 more)

### Community 47 - "NumericOutput"
Cohesion: 0.12
Nodes (40): BaseModel, Private durable record of one model-presented SQL attempt., Exact raw-provider shape; semantic validation remains item-specific below., ReconciliationIssue, ReconciliationResult, SolverResponseEnvelope, SQLProgramAttemptAudit, check_numeric_alternatives() (+32 more)

### Community 48 - "properties"
Cohesion: 0.05
Nodes (41): aqa-topic-operation-records-v3, edition-leaf-path-features-v2, full-paper, question-bank, unqualified-reference-v1, enum, minLength, type (+33 more)

### Community 49 - "objective_policy_for"
Cohesion: 0.10
Nodes (38): objective_policy_for(), Subject meaning for AO labels, independent of item tariffs and renderers., Resolve family IDs, subject names or qualification codes., CS component policy audit over candidate-answerable paths, not printed totals., Pattern, build_document(), CorpusFamily, _distribution() (+30 more)

### Community 50 - "test_open_credit_reconciliation.py"
Cohesion: 0.14
Nodes (39): alternative_permission(), Only known host-authored permissions can bypass answer-value checking., review_open_credit(), _calculation_item(), adjudication_response(), cpu_fixture(), open_item(), parametrize (+31 more)

### Community 51 - "test_layout_master.py"
Cohesion: 0.10
Nodes (32): _aqa_cs_printed_credit(), conform_generated_documents(), _edexcel_printed_credit(), Path, Generated-content policy is not an observed reference-count range., Content-driven pagination must preserve every published marking statement., runtime_page_count_policy(), conform_pdf_to_box_template() (+24 more)

### Community 52 - "CodingKeys"
Cohesion: 0.07
Nodes (36): CodingKeys, appContextWindow, contextWindow, defaultModel, detail, downloadSizeGB, id, maximumMemoryGB (+28 more)

### Community 53 - "assessment_package.py"
Cohesion: 0.13
Nodes (38): _assessment_contract(), AssessmentPackageCompatibilityError, _authoring_provenance(), _contains_non_finite(), _evidence_ids(), _extract_items(), _form_id(), _level_policies() (+30 more)

### Community 54 - "test_mark_scheme_layout.py"
Cohesion: 0.13
Nodes (39): extract_pdf_text(), pdf_font_names(), Path, Extract stable reading-order text without a Poppler CLI dependency., Return the font families actually used by visible text spans., _cleanup_graph_cache(), Render each contract criterion as a discrete, visible examiner point., render_mark_scheme() (+31 more)

### Community 55 - "PaperCreatorTests"
Cohesion: 0.09
Nodes (15): CatalogLoader, CatalogLoadError, duplicateBoard, duplicateImplementation, emptyImplementation, .errorDescription, implementationMissingFromCatalog, missingResource (+7 more)

### Community 56 - "BackendClient"
Cohesion: 0.09
Nodes (22): BackendClient, BackendClientError, backendMissing, .errorDescription, pythonMissing, pythonVenvUnreadable, BackendFile, LaunchConfiguration (+14 more)

### Community 57 - "pastpapergen/cli.py"
Cohesion: 0.09
Nodes (28): validate_assessment_contract(), _artifacts(), _build(), default_output_dir(), generate_package(), _improve(), _load_rule(), main() (+20 more)

### Community 58 - "reconcile_solution"
Cohesion: 0.12
Nodes (36): reconcile_solution(), parametrize, solve(), test_assembly_trace_checks_every_register_series_and_stored_value(), test_finite_outputs_are_keyed_and_reject_a_changed_value(), test_full_truth_table_requires_every_input_combination(), test_graph_matrix_vectors_accept_clear_space_separated_cells_only(), test_graph_route_accepts_equivalent_ordered_vertex_notation() (+28 more)

### Community 59 - "build_item_demand_target"
Cohesion: 0.11
Nodes (39): assessment_objectives_for_item(), audit_form_demand(), build_item_demand_target(), _checked_in_profile_fingerprint(), _cognitive_operations(), _collapse_command_distribution(), _command_family(), _difficulty_evidence() (+31 more)

### Community 60 - "type"
Cohesion: 0.06
Nodes (40): type, additionalProperties, $ref, title, type, additionalProperties, title, type (+32 more)

### Community 61 - "test_shared_numeric_integrity.py"
Cohesion: 0.14
Nodes (37): _independently_validate_candidate(), accounting_tasks(), GivenRateClient, parametrize, test_abc_checks_every_asserted_intermediate_without_rounding_into_final(), test_all_p2_closed_calculations_are_source_derived_and_exhaustively_reconciled(), test_chart_percentage_shared_families_have_independent_typed_contracts(), test_checkpoint_resume_rejects_changed_preserved_numeric_prompt() (+29 more)

### Community 62 - "test_assessment_checkpoints.py"
Cohesion: 0.16
Nodes (23): CheckpointIdentity, CheckpointMismatch, BaseModel, model_validator, SectionRule, FirstPassClient, FirstPassDifficultyClient, identity() (+15 more)

### Community 63 - "independent_solver.py"
Cohesion: 0.11
Nodes (31): collect_credit_rules(), credit_rule(), CreditRule, declared_rule_metadata_present(), Any, BaseModel, Origin-preserving open credit rules; never promote model advice to authority., Preserve numerical caps/dependencies, not just their descriptive prose.… (+23 more)

### Community 64 - "test_computer_science_objectives.py"
Cohesion: 0.11
Nodes (36): load_rule(), _assessment_objective_guidance(), Collect the authoritative AO definitions used by this paper in first-use order., render_mark_scheme(), parametrize, test_all_ocr_ao1_explanation_rubrics_credit_concrete_knowledge_features(), test_aqa_boolean_scheme_preserves_operator_glyphs_and_visible_ink(), test_aqa_current_or_saved_blueprints_fail_closed_on_invalid_policy() (+28 more)

### Community 65 - "test_document_dsl.py"
Cohesion: 0.21
Nodes (26): BaseComponent, BlankPage, ContinuationPage, Diagram, Graph, LevelTable, MarkBox, RuleSet (+18 more)

### Community 66 - "exam_blueprints.py"
Cohesion: 0.16
Nodes (33): _demand_band(), _hydrate_assessment_metadata(), _objective_allocation(), _prompt_uses_command_word(), _structured_scheme(), validate_generated_paper(), validate_rule(), _answer_form() (+25 more)

### Community 67 - "Foundation"
Cohesion: 0.04
Nodes (35): Foundation, AppStorageKey, SecretAccount, OllamaState, AssessmentBundleExporter, URL, FrenchAssessmentRequest, .arguments (+27 more)

### Community 68 - "properties"
Cohesion: 0.06
Nodes (36): 1, 2, context-incomplete, core, mixed, title, type, TopicRecord (+28 more)

### Community 69 - "required"
Cohesion: 0.08
Nodes (35): assessment_objectives, cognitive_operation, command_word, comparable_metrics, demand_band, demand_basis, extraction_policy, feature_basis (+27 more)

### Community 70 - "cspapergen/ollama_client.py"
Cohesion: 0.13
Nodes (32): numeric_tokens(), Extract quantities exactly enough to catch broken data/source rewrites., aqa_cs_difficulty_candidate(), aqa_cs_solver_item(), authoring_route(), Any, question_content_sha256(), AQA CS source-coupled review identity, shared by authoring/resume/export. This… (+24 more)

### Community 71 - "benchmark.py"
Cohesion: 0.12
Nodes (33): apple_cpu_core_split(), available_memory_gb(), avg(), clamp(), cpu_brand(), cpu_load_percent(), cpu_probe(), disk_probe() (+25 more)

### Community 72 - "ExamPageProfile"
Cohesion: 0.17
Nodes (31): _draw_aqa_footer(), _draw_aqa_page(), _draw_barcode(), draw_exam_page(), _draw_independent_notice(), _draw_ocr_notice(), _draw_ocr_page(), _draw_ocr_rules() (+23 more)

### Community 73 - "runtime.py"
Cohesion: 0.16
Nodes (27): atomic_json(), _check_review(), generate_assessment(), _originality(), Path, Source-scoped French authoring with hash-bound reviews and resumable drafts., validate_package(), handle_generate_assessment() (+19 more)

### Community 74 - "CandidateResponse"
Cohesion: 0.12
Nodes (25): BoardLevelPolicy, LevelDescriptor, LevelOfResponseEngine, load_level_policies(), MarkAnnotation, MarkDecision, BaseModel, model_validator (+17 more)

### Community 75 - "IndependentSolver"
Cohesion: 0.18
Nodes (30): IndependentSolver, Solve an item in a context that deliberately excludes its draft scheme., NoModelArithmetic, parametrize, test_closed_accounting_solutions_ignore_the_draft_answer_key(), closed_item(), parametrize, ResponseClient (+22 more)

### Community 76 - "Rect"
Cohesion: 0.12
Nodes (25): _clamp_fitz_rect(), conform_pdf_page_boxes(), draw_text_slot(), _fitz_rect_close(), load_layout_master(), _page_from_payload(), _page_matches_box_set(), PageMaster (+17 more)

### Community 77 - "Size"
Cohesion: 0.15
Nodes (8): Component, InstructionBlock, BoardProfile, Protocol, _text_lines(), Length, A measured distance stored in PDF points., Size

### Community 78 - "aqa_section_intro"
Cohesion: 0.10
Nodes (25): aqa_lozenge(), aqa_section_intro(), AQAQuestionHeaderFactory, flowable_question_block(), independent_practice_page(), OCRQuestionHeaderFactory, page_sequence(), Color (+17 more)

### Community 79 - "open_credit.py"
Cohesion: 0.13
Nodes (31): cpu_credit_allocations(), cpu_credit_contract(), _cpu_quote_supports_criterion(), credit_identity(), credit_item_projection(), CreditJudgement, CriterionDecision, _has_unambiguous_instruction_antecedent() (+23 more)

### Community 80 - "properties"
Cohesion: 0.06
Nodes (32): ai-assisted, deterministic, type, minLength, type, pattern, pattern, type (+24 more)

### Community 81 - "build_paper"
Cohesion: 0.12
Nodes (29): generate_package(), Path, build_paper(), Syllabus, _flatten(), Path, Generic examiner rules belong in front matter, not every table row., Consolidation must not erase per-question AO or marker instructions. (+21 more)

### Community 82 - "test_solver_source_adapter.py"
Cohesion: 0.17
Nodes (28): candidate_content_identity(), _assert_public_stimulus(), _difficulty_candidate(), EvidenceRecord, QuestionPart, _question_solver_projection(), Run an independent demand-only gate over every rendered question item., review_blueprint_difficulty() (+20 more)

### Community 83 - "configuredgen/render_pdf.py"
Cohesion: 0.15
Nodes (23): Cover, Return the renderer-neutral representation used for qualification., _adapter(), generate_package(), Path, ConfiguredSyllabus, load_syllabus(), PaperSpecification (+15 more)

### Community 84 - "document_dsl/__init__.py"
Cohesion: 0.16
Nodes (23): DocumentRole, FontToken, FontTokens, Frame, LayoutBox, LayoutPage, PageRole, StrEnum (+15 more)

### Community 85 - "test_aqa_accounting.py"
Cohesion: 0.12
Nodes (27): build_paper(), _extract(), _number(), Random, Syllabus, _values(), Independent AQA 7127 practice-paper generator., parametrize (+19 more)

### Community 86 - "pdf_validation.py"
Cohesion: 0.13
Nodes (30): compare_page_evidence(), _contrast_against_white(), _contrast_ratio(), _count_score(), _font_embedding(), _font_evidence(), GlyphMetric, _is_decorative_bleed() (+22 more)

### Community 87 - "SubjectValidation"
Cohesion: 0.14
Nodes (11): Shared subject interfaces, independent of plugin implementations and discovery., SubjectValidation, ContractSubjectPlugin, Any, Safe baseline plugin for families with validation in their own contracts., BiologyPlugin, Any, EssaySubjectPlugin (+3 more)

### Community 88 - "mathematics.py"
Cohesion: 0.15
Nodes (21): AnswerComparison, compare_mathematical_answers(), FurtherMathematicsPlugin, MarkAward, _marking_rules(), MarkingRule, MathematicalAnswer, MathematicsPlugin (+13 more)

### Community 89 - "test_reference_demand.py"
Cohesion: 0.17
Nodes (28): module(), profile_payload(), parametrize, Path, test_calculation_reasoning_ceiling_scales_with_tariff(), test_committed_profiles_cover_every_advertised_assessment_without_source_text(), test_committed_profiles_include_unadvertised_aqa_mathematics_evidence(), test_empty_context_does_not_create_an_application_requirement() (+20 more)

### Community 90 - "test_pdf_validation.py"
Cohesion: 0.17
Nodes (26): extract_pdf_evidence(), Counter, Extract print and accessibility evidence without retaining source prose. Glyph…, _validate_typography_profile(), Canvas, parametrize, Path, _release_canvas() (+18 more)

### Community 91 - "test_app_backend.py"
Cohesion: 0.16
Nodes (27): CaptureFixture, CompletedProcess, Path, run_bridge(), run_bridge_raw(), test_aqa_accounting_all_papers_generate_expected_files(), test_aqa_business_all_papers_generate_expected_files(), test_aqa_economics_all_papers_generate_expected_files() (+19 more)

### Community 92 - "graphs.py"
Cohesion: 0.30
Nodes (26): Axes, ad_as_diagram(), _arrow_axes(), _ax(), circular_flow_diagram(), consumer_producer_surplus(), demand_supply_diagram(), _ensure_style() (+18 more)

### Community 93 - "test_science_subjects.py"
Cohesion: 0.14
Nodes (18): ChemistryPlugin, equation_is_balanced(), _equation_side(), Formula, _multiplier(), _parse_group(), Any, Counter (+10 more)

### Community 94 - "$defs"
Cohesion: 0.07
Nodes (27): maximum, minimum, $defs, distribution, Observations, SourceForm, SourceItem, SourcePath (+19 more)

### Community 95 - "_mark_scheme_rows"
Cohesion: 0.15
Nodes (26): _brief_source_evidence(), _calculation_answer_lines(), _mark_point_relevance(), _mark_scheme_rows(), _normalise_mark_point(), _one_mark_points(), _paper_one_fifteen_mark_scheme_lines(), _paper_one_five_mark_diagram_lines() (+18 more)

### Community 96 - "test_coverage_matrix.py"
Cohesion: 0.20
Nodes (24): family(), matrix(), Path, test_catalog_availability_is_owned_only_by_registry(), test_checked_in_matrix_is_deterministic_and_current(), test_existing_generators_are_reported_without_false_verification(), test_matrix_exactly_covers_layout_profiles(), test_no_verified_paper_has_a_failed_gate() (+16 more)

### Community 97 - "ReferenceIndex"
Cohesion: 0.16
Nodes (14): EducationContext, EvidenceGap, Path, ValueError, Local reference retrieval: scope first, text ranking second, no fallback., No eligible source supports a requested reference query., ReferenceHit, ReferenceIndex (+6 more)

### Community 98 - "nsi.py"
Cohesion: 0.12
Nodes (16): Native French NSI authoring records and prompts, not translated A-level items., code_listing(), NumberedCanvas, Canvas, ParagraphStyle, Path, Provisional French paper layout measured from the 2026 Métropole NSI paper., Never rewrite executable text to make it fit a page. (+8 more)

### Community 99 - "mark_scheme_enrichment.py"
Cohesion: 0.22
Nodes (23): _answer_form(), _application_label(), _clean_text(), _compact_technical_guidance(), _deduplicate(), enrich_paper(), _enrich_question(), _level_guidance() (+15 more)

### Community 100 - "generation.py"
Cohesion: 0.21
Nodes (21): progress_emitter(), _atomic_publish(), _cancel_generation(), checkpoint_path_for_job(), emit_generated_files(), finalize_generated_documents(), GenerationCancelled, _generator_version() (+13 more)

### Community 101 - "properties"
Cohesion: 0.08
Nodes (24): type, type, minimum, type, type, type, maximum, minimum (+16 more)

### Community 102 - "test_topic_reference_evidence.py"
Cohesion: 0.19
Nodes (23): bank_items(), module(), parametrize, A serialised hint must never override the question that will be printed., Only the versioned contract may establish a reference comparison., test_actual_same_topic_operation_and_mode_still_matches(), test_bank_support_rejects_changed_work_not_just_matching_topic_words(), test_forged_or_sparse_source_inventory_cannot_qualify_bank() (+15 more)

### Community 103 - "subject_plugins.py"
Cohesion: 0.18
Nodes (19): board_profile(), board_profile_ids(), BoardProfile, _normalise_identifier(), discover_subject_plugin(), _normalise_identifier(), register_subject_plugin(), subject_plugin_ids() (+11 more)

### Community 104 - "emit"
Cohesion: 0.23
Nodes (19): build_parser(), handle_bundle_check(), handle_framework_generate(), handle_french_references(), main(), ArgumentParser, Namespace, Fail fast when a packaged backend is missing a dynamic generator. (+11 more)

### Community 105 - "accounting.py"
Cohesion: 0.28
Nodes (22): _accounting_endings(), accounting_outputs(), _appropriation(), _assets(), derive_accounting_open_response_context(), _exact(), _income(), _ledger() (+14 more)

### Community 106 - "AIProvider"
Cohesion: 0.08
Nodes (29): AIProvider, anthropic, apple, .backendID, .id, ollama, openAI, .sendsPromptsOffDevice (+21 more)

### Community 107 - "required"
Cohesion: 0.13
Nodes (23): assessment_kind, cognitive_operation_distribution, command_family_distribution, command_word_distribution, comparison_basis, demand_distribution, evidence_gaps, evidence_policy_id (+15 more)

### Community 108 - "ShareholderCase"
Cohesion: 0.09
Nodes (4): Candidate-visible source contract for the Paper 1 shareholder decision., Return only facts and units printed on the candidate source page., ShareholderCase, test_shareholder_case_keeps_equity_and_investor_figures_in_consistent_units()

### Community 109 - "AnswerSpace"
Cohesion: 0.23
Nodes (18): AnswerSpace, QuestionBlock, DocumentMetadata, DocumentSpec, PageSpec, Paginator, Path, test_cover_fits_long_paper_titles_inside_the_page() (+10 more)

### Community 110 - "corpus.py"
Cohesion: 0.17
Nodes (18): assign_splits(), check_download(), check_url(), discover_links(), download_with_system_trust(), ingest(), main(), OfficialRedirects (+10 more)

### Community 111 - "PathSection"
Cohesion: 0.09
Nodes (22): answer_options, candidate_marks, options, exclusiveMinimum, title, type, exclusiveMinimum, title (+14 more)

### Community 112 - "properties"
Cohesion: 0.09
Nodes (22): type, type, format, type, type, minLength, type, minLength (+14 more)

### Community 113 - "required"
Cohesion: 0.10
Nodes (21): advertised, app_board, app_subject, backend_subject, blueprint_version, board, board_profile, content_mode (+13 more)

### Community 114 - "pastpapergen/notes.py"
Cohesion: 0.20
Nodes (19): _clean_chunk(), essay_capable_topic_ids(), _flush_note_chunk(), _is_exam_point(), _is_note_noise(), _looks_like_heading(), _note_chunks(), note_context_for_topic() (+11 more)

### Community 115 - "properties"
Cohesion: 0.10
Nodes (21): minLength, type, minLength, type, minLength, type, format, type (+13 more)

### Community 116 - "ocr_computer_science_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_difficulty_remains_external_evidence_gated(), test_multi_seed_structural_demand_passes(), test_reference_evidence_is_aggregate_only(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 117 - "_written"
Cohesion: 0.15
Nodes (16): _nearest_hundred(), _decision_levels(), _gbp(), _gbp_decimal(), _levels(), _management_calculation(), Topic, Build a complete, internally solved data contract for each numeric task. (+8 more)

### Community 118 - "test_accounting_objectives.py"
Cohesion: 0.22
Nodes (19): load_rule(), paper_for(), parametrize, test_accounting_ao3_short_analysis_does_not_imply_judgement(), test_accounting_does_not_offer_unallocated_objectives_in_guidance(), test_accounting_rejects_invalid_ao_even_if_marks_still_add_up(), test_accounting_rule_cannot_fall_back_to_generic_allocation(), test_accounting_uses_official_item_budgets_and_component_totals() (+11 more)

### Community 119 - "validate_generator_migration.py"
Cohesion: 0.24
Nodes (10): build_parser(), _layout_board(), main(), MigrationIssue, MigrationReport, MigrationValidator, Any, ArgumentParser (+2 more)

### Community 120 - "provider.py"
Cohesion: 0.17
Nodes (13): NoRedirects, ollama_request(), open_ollama_request(), HTTPRedirectHandler, Keep French inference on the explicitly selected server, without proxy routing., _prompt(), FrenchOllamaClient, Explicit French transport policy; UK prompt detection remains unchanged. (+5 more)

### Community 121 - "NSIExercise"
Cohesion: 0.20
Nodes (16): NSIExercise, solver_prompt(), _review_prompt(), Small, bounded verification contracts. Never execute model-supplied Python., _shortest_path(), _sql(), _trace(), verify_contract() (+8 more)

### Community 122 - "generator_registry.py"
Cohesion: 0.23
Nodes (15): _capability(), generator_capabilities(), generator_subjects(), _paper_qualification(), PaperQualification, Any, _relative_path(), test_backend_bundle_script_is_registry_driven() (+7 more)

### Community 123 - "validate_mark_scheme_item"
Cohesion: 0.25
Nodes (17): _contains_any(), MarkSchemeQuality, _normalise(), Any, validate_mark_scheme_item(), _item(), test_accounting_follow_through_metadata_counts_as_method_guidance(), test_calculation_requires_method_or_working() (+9 more)

### Community 124 - "test_computer_science_subject.py"
Cohesion: 0.21
Nodes (12): ComputerSciencePlugin, _evaluate_boolean(), normalise_pseudocode(), pseudocode_equivalent(), Any, truth_table(), test_four_mark_boolean_tasks_have_equivalent_explicit_working(), test_computer_science_uses_the_specialised_plugin() (+4 more)

### Community 125 - "build_layout_masters.py"
Cohesion: 0.29
Nodes (18): _box(), _colour(), _content_box(), _drawing_kind(), _drawings(), extract_layout_master(), _furniture_signature(), _images() (+10 more)

### Community 126 - "draw_barcode"
Cohesion: 0.25
Nodes (16): CanvasBarcodeStyle, draw_barcode(), draw_glyph_answer_rules(), draw_solid_answer_rules(), GlyphRuleStyle, Canvas, Draw a fixed number of solid response rules and return the next baseline., Draw selectable glyph-based response rules and return the next baseline. (+8 more)

### Community 127 - "test_science_overlay.py"
Cohesion: 0.35
Nodes (16): apparatus_diagram(), ApparatusSpec, Atom, Bond, circuit_diagram(), CircuitComponent, CircuitSpec, molecule_diagram() (+8 more)

### Community 128 - "required"
Cohesion: 0.11
Nodes (17): artifacts, created_at, evidence, gate_results, generator_id, model, reviewer_identity_class, seed (+9 more)

### Community 129 - "generate_package"
Cohesion: 0.20
Nodes (16): Rehydrate the renderer's case only from the published source data., generate_package(), Path, page_count(), Path, test_both_packages_render_36_page_question_papers(), test_invalid_paper_is_rejected(), test_paper_one_mark_scheme_matches_reference_question_sequence() (+8 more)

### Community 130 - "PaperBlueprint"
Cohesion: 0.24
Nodes (18): _count_pages(), _draw_answer_page_header(), _draw_continuation_lines(), _draw_paper_3_pages(), _draw_question_footer(), _draw_question_pages(), _draw_section_b_source_pages(), _draw_section_c_answer_pages() (+10 more)

### Community 131 - "candidate_identity.py"
Cohesion: 0.26
Nodes (16): _export_difficulty_candidate_projection(), candidate_review_content(), difficulty_candidate_projection(), DifficultyCandidateProjection, edexcel_difficulty_candidate_projection(), ensure_difficulty_candidate_projection(), _mapping(), Any (+8 more)

### Community 132 - "points"
Cohesion: 0.10
Nodes (15): AssessmentDefinition, CurriculumVersion, points(), Decimal, Education-system identity, independent of interface locale and UK board models., Read exact, non-negative decimal credit from a JSON string., Credit, NSIQuestion (+7 more)

### Community 133 - "register_fonts"
Cohesion: 0.22
Nodes (13): register_font(), register_fonts(), _standard_fallback(), _check_cover_and_body(), parametrize, _spans(), test_aqa_cover_faces_are_embedded_and_body_fonts_unchanged(), test_shared_mark_scheme_cover_embeds_measured_open_sans_roles() (+5 more)

### Community 134 - "generator/tests/test_closed_response_integrity.py"
Cohesion: 0.26
Nodes (16): require_solution_matches_scheme(), _part_solver_item(), candidate_stimulus_data(), _draw_classification_diagram(), Describe visible figure content for text-only independent solvers., classification(), parametrize, test_authoring_merge_preserves_closed_key_through_final_solver() (+8 more)

### Community 135 - "reference-demand-profile.schema.json"
Cohesion: 0.08
Nodes (23): derived_aggregate_only, profiles, purpose, retains_source_text, test_written_diagram_renderer_prints_the_declared_economic_structure(), schema_version, additionalProperties, const (+15 more)

### Community 136 - "properties"
Cohesion: 0.12
Nodes (17): type, properties, type, type, type, type, type, type (+9 more)

### Community 137 - "properties"
Cohesion: 0.12
Nodes (17): type, pattern, type, minLength, type, minLength, type, minLength (+9 more)

### Community 138 - "test_candidate_paths.py"
Cohesion: 0.26
Nodes (16): items(), paths_module(), parametrize, test_complete_pairs_produce_six_eighty_mark_paths_not_cross_pairs(), test_correlated_source_vectors_cannot_pass_by_coordinatewise_bounds(), test_edexcel_leaf_only_marks_and_choice_groups(), test_explicit_selected_operation_is_not_relabelled_retrieval_in_audit(), test_good_printed_average_cannot_rescue_a_failed_correlated_path() (+8 more)

### Community 139 - "inspect_release_compliance"
Cohesion: 0.27
Nodes (14): Path, test_release_compliance_detects_a_tracked_secret_signature(), test_release_compliance_passes_for_the_repository(), test_release_compliance_rejects_unbounded_runtime_dependencies(), _check_dependencies(), _check_entitlements(), _check_font_licences(), _check_privacy_manifest() (+6 more)

### Community 140 - "enum"
Cohesion: 0.12
Nodes (16): algorithm-trace, calculation, computational-analysis, computational-design, constructed-response, extended-evaluation, mathematical-argument, multi-stage-calculation (+8 more)

### Community 141 - "CandidateTopology"
Cohesion: 0.12
Nodes (16): approval_evidence, approved_by_identity_class, duration_minutes, sections, total_marks, policy_id, status, additionalProperties (+8 more)

### Community 142 - "IncomeStatementCase"
Cohesion: 0.17
Nodes (4): IncomeStatementCase, Decimal, Complete, internally consistent source for the Paper 1 company statement., _round_pounds()

### Community 143 - "SalesLedgerCase"
Cohesion: 0.15
Nodes (6): AccountingSystemCase, _gbp(), Single source of truth for the Paper 1 sales-ledger case. The question paper,…, Candidate-visible source for the bookkeeping-system decision., Return one exact, independently checkable award point per mark., SalesLedgerCase

### Community 144 - "_draw_cover"
Cohesion: 0.21
Nodes (14): economics_exam_schedule(), ExamSchedule, formatted_economics_exam_date(), date, _draw_boxes(), _draw_cover(), _draw_front_section(), _draw_mark_scheme_qualification_page() (+6 more)

### Community 145 - "properties"
Cohesion: 0.08
Nodes (25): blueprint, contract, prompt, renderer, syllabus, minLength, type, minLength (+17 more)

### Community 146 - "paths"
Cohesion: 0.11
Nodes (19): items, minItems, $ref, title, items, maxItems, minItems, title (+11 more)

### Community 147 - "test_generator_migration.py"
Cohesion: 0.23
Nodes (13): Path, test_all_current_families_pass_declarative_migration_validation(), test_broken_fixture_reports_every_onboarding_surface(), test_scaffold_emits_complete_unadvertised_family_and_refuses_overwrite(), build_parser(), _cli_template(), main(), ArgumentParser (+5 more)

### Community 148 - "required"
Cohesion: 0.13
Nodes (15): maximum_acceptable_facility, maximum_dif_gap, minimum_acceptable_facility, minimum_candidates, minimum_discrimination, minimum_double_marked_pairs, minimum_facility_coverage, minimum_group_responses (+7 more)

### Community 150 - "test_repository_hygiene.py"
Cohesion: 0.23
Nodes (12): type, path, test_committed_inventory_matches_the_current_repository(), test_every_tracked_file_has_a_durable_classification(), test_generated_and_binary_outputs_are_rejected(), test_maintained_visual_assets_are_classified_without_allowing_arbitrary_pngs(), test_root_lint_configuration_is_release_configuration(), Classification (+4 more)

### Community 151 - "ocrcsgen/generator.py"
Cohesion: 0.27
Nodes (13): _analysis_prompt(), _levels(), _programming_prompt(), _programming_scheme(), Random, Topic, _question(), _representation_calculation() (+5 more)

### Community 152 - "additionalProperties"
Cohesion: 0.13
Nodes (15): items, minItems, type, uniqueItems, items, minItems, type, uniqueItems (+7 more)

### Community 153 - "id"
Cohesion: 0.13
Nodes (15): PathOption, minLength, title, type, items, minItems, title, type (+7 more)

### Community 154 - "aqa_accounting_calibration.py"
Cohesion: 0.34
Nodes (14): _band(), build_generated_profile(), build_reference_profile(), build_report(), _command(), _fingerprint(), _inventory(), main() (+6 more)

### Community 155 - "aqa_business_calibration.py"
Cohesion: 0.34
Nodes (14): _band(), build_generated_profile(), build_reference_profile(), build_report(), _command(), _fingerprint(), _inventory(), main() (+6 more)

### Community 156 - "ocr_economics_calibration.py"
Cohesion: 0.34
Nodes (14): _band(), build_generated_profile(), build_reference_profile(), build_report(), _command(), _fingerprint(), main(), _page_count() (+6 more)

### Community 157 - "ReportLabBackend"
Cohesion: 0.36
Nodes (5): LayoutPlan, RenderEvidence, Canvas, Path, ReportLabBackend

### Community 158 - "enum"
Cohesion: 0.14
Nodes (14): analyse, contextualise, describe, design, explain, judge, program, retrieve (+6 more)

### Community 159 - "properties"
Cohesion: 0.15
Nodes (14): approved, draft, retired, type, type, null, minLength, type (+6 more)

### Community 160 - "qualification_levels"
Cohesion: 0.14
Nodes (14): empirically_calibrated, engineering_validated, visually_calibrated, type, type, empirically_calibrated, engineering_validated, qualification_levels (+6 more)

### Community 162 - "test_source_candidate_paths.py"
Cohesion: 0.23
Nodes (13): _fixture_pdf(), module(), fixture, Original synthetic text, with the audited editions' page/mark structure., source_corpus(), test_aqa_selected_source_operations_do_not_manufacture_objective_tags(), test_business_edition_does_not_assume_same_question_numbers(), test_clean_ocr_mcq_rows_keep_published_ao_and_non_retrieval_operations() (+5 more)

### Community 163 - "backend-protocol.schema.json"
Cohesion: 0.15
Nodes (12): event_id, job_id, protocol, timestamp, type, additionalProperties, allOf, $id (+4 more)

### Community 164 - "properties"
Cohesion: 0.11
Nodes (18): properties, exclusiveMinimum, title, type, minLength, title, type, duration_minutes (+10 more)

### Community 165 - "difficulty_calibration.py"
Cohesion: 0.40
Nodes (12): build_generated_profile(), build_reference_profile(), build_report(), _command(), _fingerprint(), main(), _page_count(), _pdf_text() (+4 more)

### Community 166 - "topic_reference_evidence.py"
Cohesion: 0.29
Nodes (11): audit_topic_bank(), matching_records(), Any, Reviewed feature-only AQA topic subsets, never topic AO targets. Admission is…, Conservative semantic selectors for reviewed bank tasks; hints cannot override…, Conservative dependencies for the reviewed bank forms, not a language solver.…, Require task/context membership and an evidenced response form. A stimulus…, reviewed_topic_records() (+3 more)

### Community 167 - "required"
Cohesion: 0.17
Nodes (12): candidate_sample, facility_range, group_fairness_screen, independent_manual_review, internal_consistency, item_coverage, marker_standardisation, policy_approved (+4 more)

### Community 168 - "topic_id"
Cohesion: 0.29
Nodes (7): 4.10, 4.12, 4.2, topic_id, enum, title, type

### Community 169 - "required"
Cohesion: 0.18
Nodes (12): differential_item_functioning, discrimination, facility, item_id, median_time_seconds, responses, items, minimum (+4 more)

### Community 170 - "string"
Cohesion: 0.23
Nodes (12): null, stage, type, type, null, string, properties, type (+4 more)

### Community 171 - "render_source_booklet"
Cohesion: 0.21
Nodes (12): _apply_edexcel_page_boxes(), _draw_crop_marks(), _draw_source_content_page(), _extract_source_questions(), _pad_pdf_pages(), Path, Syllabus, Match Pearson question-paper bleed and crop boxes without changing A4 content. (+4 more)

### Community 172 - "generator-capability.schema.json"
Cohesion: 0.17
Nodes (11): additionalProperties, $defs, safePath, $id, pattern, minLength, not, type (+3 more)

### Community 173 - "paper1_reference_code"
Cohesion: 0.33
Nodes (9): paper1_reference_code(), Shared reference snippets used by the renderer and publication integrity gate., parametrize, test_add_example_constructs_the_scenario_record_type(), test_adjustment_example_implements_the_actual_function_contract(), test_reference_functions_integrate_with_the_generated_skeleton(), test_report_example_is_one_pass_and_preserves_empty_categories_and_ties(), test_timing_example_uses_supplied_functions_and_fresh_equal_trials() (+1 more)

### Community 174 - "record_review"
Cohesion: 0.36
Nodes (9): digest(), artifact_identity(), Path, Self-attested human review records; hashes bind scope, not reviewer credentials., record_review(), review_status(), parametrize, test_review_is_bound_to_all_artifacts_and_becomes_stale() (+1 more)

### Community 175 - "test_humanities_overlay.py"
Cohesion: 0.55
Nodes (9): map_diagram(), MapFeature, MapSpec, Drawing, timeline_diagram(), TimelineEvent, TimelineSpec, test_humanities_diagrams_reject_misleading_or_invalid_inputs() (+1 more)

### Community 177 - "enum"
Cohesion: 0.18
Nodes (11): benchmark_done, benchmark_metric, benchmark_sample, done, error, file, hello, models (+3 more)

### Community 178 - "required"
Cohesion: 0.18
Nodes (11): collected_at, collector_role, consent_basis, dataset_id, row_level_data, source, provenance, additionalProperties (+3 more)

### Community 179 - "required"
Cohesion: 0.18
Nodes (11): difficulty_independently_verified, evidence_fingerprint, family, form_id, paper, policy, provenance, sample (+3 more)

### Community 180 - "cspapergen/notes.py"
Cohesion: 0.38
Nodes (9): cache_notes(), discover_note_pdfs(), _extract_text(), note_context_for_topic(), NotesManifest, Path, _topic_prefixes(), test_cache_notes_extracts_text_into_project_cache() (+1 more)

### Community 181 - "ObjectivePolicy"
Cohesion: 0.22
Nodes (4): ObjectivePolicy, Any, Reject unsupported labels in new or persisted qualified contracts., CS tasks are not classified from their tariff or AO3 label alone.

### Community 182 - "properties"
Cohesion: 0.20
Nodes (10): minimum, type, items, type, candidates, groups, response_rows, minimum (+2 more)

### Community 183 - "enum"
Cohesion: 0.22
Nodes (9): anthropic, apple, ollama, openai, enum, supported_providers, items, type (+1 more)

### Community 184 - "save_failure_diagnostic"
Cohesion: 0.29
Nodes (7): _bounded(), Any, Path, Save only explicitly supplied evidence, not arbitrary errors or prompts.…, save_failure_diagnostic(), BaseException, test_diagnostics_are_bounded_redacted_and_do_not_follow_symlinks()

### Community 185 - "required"
Cohesion: 0.22
Nodes (9): detail, qualification, title, required, checks, id, items, type (+1 more)

### Community 186 - "SubjectPlugin"
Cohesion: 0.39
Nodes (3): Any, Protocol, SubjectPlugin

### Community 187 - "PhysicsPlugin"
Cohesion: 0.43
Nodes (3): PhysicsPlugin, Any, test_physics_requires_uncertainty_for_uncertainty_items()

### Community 188 - ".baseQuery"
Cohesion: 0.39
Nodes (4): SecretStore, Any, String, Security

### Community 189 - "sample"
Cohesion: 0.25
Nodes (8): candidates, groups, response_rows, items, sample, additionalProperties, required, type

### Community 190 - "enum"
Cohesion: 0.25
Nodes (8): failed, not_applicable, not_run, passed, enum, additionalProperties, type, gate_results

### Community 191 - "objective_basis"
Cohesion: 0.25
Nodes (8): printed-conflicting, published-item-allocation, reconciled-published-aggregate, unknown, enum, title, type, objective_basis

### Community 192 - "candidate_stimulus_data"
Cohesion: 0.32
Nodes (8): _bar_chart_data(), _bar_label(), candidate_stimulus_data(), Expose the same source values and dispatch rules used to draw a figure., _table_rows(), table_rows(), parametrize, test_review_stimulus_uses_rendered_defaults()

### Community 193 - "empirical-calibration.schema.json"
Cohesion: 0.25
Nodes (7): additionalProperties, $id, not, anyOf, $schema, title, type

### Community 194 - "_call_name"
Cohesion: 0.38
Nodes (6): Call, _call_name(), parametrize, Path, test_production_pdf_renderers_run_inside_atomic_transactions(), test_shared_family_adapter_owns_atomic_pdf_transaction()

### Community 195 - "build_backend.sh"
Cohesion: 0.29
Nodes (5): MPLCONFIGDIR, PYINSTALLER_CONFIG_DIR, PYTHONPATH, build_backend.sh script, XDG_CACHE_HOME

### Community 196 - "enum"
Cohesion: 0.29
Nodes (7): automation, examiner, internal_reviewer, psychometrician, subject_specialist, reviewer_identity_class, enum

### Community 197 - "specification_version"
Cohesion: 0.67
Nodes (3): specification_version, minLength, type

### Community 198 - "model"
Cohesion: 0.29
Nodes (7): digest, name, provider, additionalProperties, required, type, model

### Community 199 - "enum"
Cohesion: 0.29
Nodes (7): high, low, standard, enum, title, type, historical_engineering_demand_proxy

### Community 200 - "ocrcsgen/syllabus.py"
Cohesion: 0.38
Nodes (5): load_syllabus(), BaseModel, Path, Syllabus, Topic

### Community 202 - "non_comparable_features"
Cohesion: 0.33
Nodes (6): const, additionalProperties, propertyNames, title, type, non_comparable_features

### Community 203 - "test_aqa_accounting_calibration.py"
Cohesion: 0.53
Nodes (4): report(), test_both_papers_pass_multi_seed_automated_checks(), test_external_difficulty_gates_remain_false(), test_reference_evidence_is_aggregate_only()

### Community 204 - "test_aqa_business_calibration.py"
Cohesion: 0.53
Nodes (4): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence()

### Community 205 - "test_difficulty_calibration.py"
Cohesion: 0.53
Nodes (4): report(), test_calibration_retains_no_official_text_or_paths(), test_difficulty_is_not_promoted_without_human_and_psychometric_evidence(), test_every_paper_has_multi_seed_structural_evidence()

### Community 206 - "test_ocr_economics_calibration.py"
Cohesion: 0.53
Nodes (4): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence()

### Community 208 - "generator_working_directory"
Cohesion: 0.40
Nodes (4): generator_working_directory(), fixture, MonkeyPatch, FixtureRequest

### Community 209 - "section_features"
Cohesion: 0.40
Nodes (5): $ref, section_features, additionalProperties, title, type

### Community 210 - "xcbuild.sh"
Cohesion: 0.67
Nodes (3): HOME, xcbuild.sh script, usage()

### Community 211 - "capabilities"
Cohesion: 0.50
Nodes (4): items, type, type, capabilities

### Community 217 - "app_board"
Cohesion: 0.67
Nodes (3): minLength, type, app_board

### Community 218 - "backend_subject"
Cohesion: 0.67
Nodes (3): pattern, type, backend_subject

### Community 219 - "blueprint_version"
Cohesion: 0.67
Nodes (3): minLength, type, blueprint_version

### Community 220 - "entry_point"
Cohesion: 0.67
Nodes (3): pattern, type, entry_point

### Community 221 - "id"
Cohesion: 0.67
Nodes (3): pattern, type, id

### Community 223 - "subject_plugin"
Cohesion: 0.67
Nodes (3): subject_plugin, pattern, type

## Knowledge Gaps
- **850 isolated node(s):** `CurriculumVersion`, `BoardLayout`, `examforge-aqa-accounting`, `$schema`, `$id` (+845 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **31 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `test_written_diagram_renderer_prints_the_declared_economic_structure()` connect `reference-demand-profile.schema.json` to `aqaecongen/render_pdf.py`, `test_aqa_economics.py`?**
  _High betweenness centrality (0.119) - this node is a cross-community bridge._
- **Why does `profiles` connect `reference-demand-profile.schema.json` to `properties`?**
  _High betweenness centrality (0.119) - this node is a cross-community bridge._
- **Why does `properties` connect `reference-demand-profile.schema.json` to `properties`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Are the 25 inferred relationships involving `GeneratedQuestion` (e.g. with `AssessmentLLMClient` and `GenerationPolicy`) actually correct?**
  _`GeneratedQuestion` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `ApplicationCoordinator` (e.g. with `PaperCreator` and `.body`) actually correct?**
  _`ApplicationCoordinator` has 20 INFERRED edges - model-reasoned connections that need verification._
- **What connects `CurriculumVersion`, `BoardLayout`, `examforge-aqa-accounting` to the rest of the system?**
  _850 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ApplicationCoordinator` be split into smaller, more focused modules?**
  _Cohesion score 0.030042512990080303 - nodes in this community are weakly interconnected._