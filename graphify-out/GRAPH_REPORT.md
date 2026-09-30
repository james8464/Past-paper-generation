# Graph Report - Past Paper Creation  (2026-09-30)

## Corpus Check
- 415 files · ~759,822 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 6852 nodes · 19210 edges · 275 communities (247 shown, 28 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 1119 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d5c746dd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ExamBoardOption
- GeneratedQuestion
- paper_fidelity_audit.py
- required
- load_syllabus
- pastpapergen/ollama_client.py
- Text
- cspapergen/render_pdf.py
- build_paper_blueprint
- pastpapergen/render_pdf.py
- psychometrics.py
- Paragraph
- pastpapergen/generator.py
- live_generation_matrix.py
- require_difficulty_review
- String
- paper1_assets.py
- add_page_structure_tree
- AIProvider
- RecentDocumentStore
- candidate_stimulus_data
- build_question
- aqaaccountgen/render_pdf.py
- AssessmentContract
- properties
- ocrcsgen/render_pdf.py
- sql_contracts.py
- _mark_scheme_rows
- CodingKeys
- test_solver_source_adapter.py
- formatted_generation_date
- test_aqa_business.py
- test_shared_numeric_integrity.py
- OCRAnswerLines
- aqabizgen/render_pdf.py
- open_credit.py
- solve_selected_response
- test_render_pdf.py
- EconomicsSource
- GeneratedFile
- AssessmentCheckpointStore
- assessment_package.py
- test_ocr_economics.py
- properties
- IndependentSolver
- tests/test_closed_response_integrity.py
- providers.py
- reference_corpus.py
- test_sql_answer_verification.py
- test_mlx_setup.py
- test_computer_science_objectives.py
- aqaecongen/render_pdf.py
- CodingKeys
- independent_solver.py
- reference_demand_profiles.py
- test_aqa_economics.py
- type
- reference_demand.py
- properties
- generator/tests/test_assessment_contracts.py
- PaperCreatorTests
- PaperBlueprint
- DocumentPreviewView
- pdf_validation.py
- ObjectivePolicy
- properties
- NumericOutput
- .baseQuery
- benchmark.py
- BackendClient
- aqa_section_intro
- topic_id
- Contract-First Paper Generation and Release Qualification
- test_aqa_accounting.py
- test_accounting_objectives.py
- ExamPageProfile
- test_app_backend.py
- document_dsl/__init__.py
- test_mark_scheme_layout.py
- render_pdf_atomically
- mathematics.py
- Approved-Improvement Traceability
- test_reference_demand.py
- graphs.py
- reference_evidence.py
- AQA Computer Science bank-item reference support
- PathSection
- draw_barcode
- SubjectPlugin
- test_coverage_matrix.py
- test_layout_master.py
- Question
- reference-demand-profile.schema.json
- NonCurrentAssetCase
- properties
- generator_registry.py
- generation.py
- PartnershipCase
- candidate_identity.py
- Paper Creator Excellence Programme Design
- required
- ShareholderCase
- properties
- mark_scheme_enrichment.py
- test_pdf_validation.py
- .initialEstimate
- $defs
- test_science_subjects.py
- required
- paths
- required
- pastpapergen/cli.py
- accounting.py
- reconcile_solution
- pastpapergen/notes.py
- properties
- aqa_accounting_calibration.py
- CanonicalSolution
- required
- GeneratedPaper
- validate_generator_migration.py
- validate_mark_scheme_item
- subject_plugins.py
- stratum
- CandidateResponse
- paper
- test_computer_science_subject.py
- build_layout_masters.py
- Canvas
- properties
- properties
- properties
- inspect_release_compliance
- SalesLedgerCase
- test_aqa_accounting_calibration.py
- enum
- IncomeStatementCase
- ApplicationCoordinator
- properties
- test_generator_migration.py
- test_topic_reference_evidence.py
- BenchmarkChart
- cspapergen/ollama_client.py
- Difficulty Calibration v2 Qualification Report
- Continued qualification — 31 August
- properties
- required
- _BooleanParser
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
- properties
- difficulty_calibration.py
- File Structure
- required
- required
- Q: How does the paper fidelity audit produce per-document and per-role scores, and where should release thresholds integrate?
- Q: Which Ollama model and live validation path does the project use for all supported papers?
- generator-capability.schema.json
- emit
- Architecture
- End-to-end runtime
- Paper creator: deep project analysis
- Architecture
- enum
- required
- PhysicsPlugin
- SettingsPane.swift
- profile_for
- Review focus
- macOS interaction and HIG compliance
- macOS UI audit
- Assessment-objective calibration reference
- Reference-Demand Calibration Implementation Plan
- Paper creator
- enum
- required
- required
- properties
- ocrcsgen/generator.py
- Implementation and fidelity report
- Global Constraints
- Rendering and Mark-Scheme Reliability Implementation Plan
- required
- sample
- enum
- empirical-calibration.schema.json
- SubjectValidation
- _call_name
- build_backend.sh
- test_science_overlay.py
- enum
- ocregen/generator.py
- model
- test_configured_family.py
- Rect
- _written
- CoverProfile
- test_ocr_computer_science_calibration.py
- qualification-schema.json
- test_humanities_overlay.py
- test_difficulty_calibration.py
- generate_package
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
- Open Sans cover fonts
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
- JobHistoryView
- cspapergen/notes.py
- test_source_candidate_paths.py
- paper1_reference_code
- test_ocr_economics_printed_credit.py
- 31 August continued qualification findings
- Teacher-feedback follow-up — 27 September 2026
- Selected-response label integrity implementation plan
- _draw_cover
- Examiner-readiness standard
- parse_model_recommendations
- CostingCase
- test_ocr_economics_calibration.py

## God Nodes (most connected - your core abstractions)
1. `GeneratedQuestion` - 213 edges
2. `build_paper_blueprint()` - 181 edges
3. `load_syllabus()` - 171 edges
4. `load_builtin_paper_config()` - 165 edges
5. `IndependentSolver` - 151 edges
6. `ApplicationCoordinator` - 144 edges
7. `GeneratedOption` - 125 edges
8. `GeneratedPaper` - 96 edges
9. `reconcile_solution()` - 96 edges
10. `load_syllabus()` - 81 edges

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

## Communities (275 total, 28 thin omitted)

### Community 0 - "ExamBoardOption"
Cohesion: 0.07
Nodes (37): CatalogSubject, ExamBoardOption, .fullPapers, .isReady, .questionBanks, .usesAI, .defaultBoard, SidebarItem (+29 more)

### Community 1 - "GeneratedQuestion"
Cohesion: 0.05
Nodes (133): AssessmentLLMClient, _batches_for_client(), _candidate_question(), _canonical_objective_allocation(), _clean_generated_prompt(), _contains_command_word(), _demand_item(), _difficulty_candidate() (+125 more)

### Community 2 - "paper_fidelity_audit.py"
Cohesion: 0.05
Nodes (103): Pixmap, parametrize, Path, test_compact_profile_omits_raster_geometry(), test_contact_sheets_make_visual_review_artifacts(), test_generated_document_falls_back_to_nested_transaction_output(), test_generated_document_supports_app_per_paper_directories(), test_metric_callout_names_print_resolution_comparison_dimensions() (+95 more)

### Community 3 - "required"
Cohesion: 0.11
Nodes (25): assessment_objectives, cognitive_operation, command_word, demand_band, demand_basis, historical_engineering_demand_proxy, item_ids, learner_demand (+17 more)

### Community 4 - "load_syllabus"
Cohesion: 0.05
Nodes (100): identity_for_blueprint(), extract_pdf_text(), Path, Extract stable reading-order text without a Poppler CLI dependency., _build(), build_paper1_blueprint(), build_paper2_blueprint(), build_topic_question_bank() (+92 more)

### Community 5 - "pastpapergen/ollama_client.py"
Cohesion: 0.07
Nodes (68): _improve(), MultipleChoiceOption, QuestionBlueprint, SyllabusTopic, _assert_public_stimulus(), build_question_prompt(), _clean_prompt(), generate_questions_with_ollama() (+60 more)

### Community 6 - "Text"
Cohesion: 0.03
Nodes (112): App, CGFloat, Charts, Commands, GenerationQualityState, AppCommands, PaperCreator, .body (+104 more)

### Community 7 - "cspapergen/render_pdf.py"
Cohesion: 0.10
Nodes (76): _answer_line_count(), _answer_lines_paginated(), _candidate_fields(), _cover_page(), _cover_section(), _draw_adjacency_matrix_answers(), _draw_arrow(), _draw_assembly_support_page() (+68 more)

### Community 8 - "build_paper_blueprint"
Cohesion: 0.08
Nodes (86): build_paper_blueprint(), PaperBlueprint, Syllabus, load_builtin_paper_config(), review_table_rows(), load_syllabus(), Path, Syllabus (+78 more)

### Community 9 - "pastpapergen/render_pdf.py"
Cohesion: 0.09
Nodes (36): BoardLayout, GraphParams, _answer_line_count(), _axis_labels_for_draw_prompt(), _draw_case_source_figure(), _draw_do_not_write_rail(), _draw_economics_graph(), _draw_hatched_rail() (+28 more)

### Community 10 - "psychometrics.py"
Cohesion: 0.08
Nodes (56): CalibrationMetadata, CalibrationStore, ConsentRecord, _normalise_row(), Any, Path, Encrypted local storage for row-level calibration evidence. Keys are…, _read_rows() (+48 more)

### Community 11 - "Paragraph"
Cohesion: 0.11
Nodes (54): Paragraph, _add_economics_diagram(), _add_firm_objectives_diagram(), _add_ppf_diagram(), _annotation_conventions_page(), _answer_mark(), _assessment_allocation(), _assessment_grid_groups() (+46 more)

### Community 12 - "pastpapergen/generator.py"
Cohesion: 0.06
Nodes (71): MultipleChoiceOption, _adapt_paper_three_case_guidance(), _best_section_a_context_point(), _build_part(), _build_parts(), _choice_group_name(), _choice_lookup(), _choose_topic() (+63 more)

### Community 13 - "live_generation_matrix.py"
Cohesion: 0.06
Nodes (71): Release qualification evidence and policy models., ArtifactEvidence, EvidenceRecord, GateState, ModelIdentity, BaseModel, field_validator, Path (+63 more)

### Community 14 - "require_difficulty_review"
Cohesion: 0.10
Nodes (61): CandidateContentIdentity, _candidate_task_facts(), difficulty_review(), DifficultyReviewResult, independent_review(), JSONClient, _public_task_operation_evidence(), PublicTaskOperationEvidence (+53 more)

### Community 15 - "String"
Cohesion: 0.03
Nodes (94): Decodable, Equatable, Hashable, Identifiable, AssessmentKind, fullPaper, questionBank, .title (+86 more)

### Community 16 - "paper1_assets.py"
Cohesion: 0.50
Nodes (11): _page_footer(), _paragraph(), _practice_header(), Canvas, PaperBlueprint, Path, render_electronic_answer_document(), render_preliminary_material() (+3 more)

### Community 17 - "add_page_structure_tree"
Cohesion: 0.31
Nodes (9): add_page_structure_tree(), has_logical_page_order(), _has_structure_tree(), _new_object(), Document, Page, Path, Attach a deterministic page-level structure tree and marked content. Each page… (+1 more)

### Community 18 - "AIProvider"
Cohesion: 0.05
Nodes (38): CaseIterable, AIProvider, anthropic, apple, .backendID, .id, ollama, openAI (+30 more)

### Community 19 - "RecentDocumentStore"
Cohesion: 0.04
Nodes (53): Codable, FileManager, Foundation, GenerationJobState, LocalizedError, AppClock, ModelCoordinator, .isModelListStale (+45 more)

### Community 20 - "candidate_stimulus_data"
Cohesion: 0.18
Nodes (13): _bar_chart_data(), _bar_label(), candidate_stimulus_data(), _draw_bar_chart(), _draw_data_table(), _line_chart_data(), Expose the same source values and dispatch rules used to draw a figure., _table_rows() (+5 more)

### Community 21 - "build_question"
Cohesion: 0.17
Nodes (64): model_validator, Stimulus, _assembly_program_question(), _assembly_trace_question(), _big_data_question(), _big_data_short_question(), _binary_short_question(), _bitmap_question() (+56 more)

### Community 22 - "aqaaccountgen/render_pdf.py"
Cohesion: 0.11
Nodes (62): AQAAnswerLines, _artifacts(), _accounting_marking_guidance_pages(), _accounting_system_case(), _additional_answer_page(), _appropriation_answer_table(), _assessment_objectives_page(), _chrome() (+54 more)

### Community 23 - "AssessmentContract"
Cohesion: 0.07
Nodes (51): AssessmentContract, contract_for_question(), GeneratedNumericField, GraphContract, _numeric_contracts(), NumericRole, NumericValueContract, Any (+43 more)

### Community 24 - "properties"
Cohesion: 0.04
Nodes (59): printed-conflicting, published-item-allocation, reconciled-published-aggregate, unknown, anyOf, default, title, const (+51 more)

### Community 25 - "ocrcsgen/render_pdf.py"
Cohesion: 0.09
Nodes (44): ExamPage, Flowable, A full-page shell that can also live inside a Platypus story., _artifacts(), _additional_answer_page(), _additional_pages(), _annotation_conventions_page(), _assessment_objective_guidance() (+36 more)

### Community 26 - "sql_contracts.py"
Cohesion: 0.11
Nodes (40): _contract_column(), _Count, _equality(), _Field, _finding(), fitness_centre_sql_contract(), _Frozen, _has_sql_statement_shape() (+32 more)

### Community 27 - "_mark_scheme_rows"
Cohesion: 0.15
Nodes (26): _brief_source_evidence(), _calculation_answer_lines(), _mark_point_relevance(), _mark_scheme_rows(), _normalise_mark_point(), _one_mark_points(), _paper_one_fifteen_mark_scheme_lines(), _paper_one_five_mark_diagram_lines() (+18 more)

### Community 28 - "CodingKeys"
Cohesion: 0.04
Nodes (57): CodingKey, CodingKeys, assessmentKind, backendVersion, capabilities, checks, code, command (+49 more)

### Community 29 - "test_solver_source_adapter.py"
Cohesion: 0.19
Nodes (25): candidate_content_identity(), _difficulty_candidate(), EvidenceRecord, QuestionPart, _question_solver_projection(), _validate_solver_projection(), _paper(), parametrize (+17 more)

### Community 30 - "formatted_generation_date"
Cohesion: 0.21
Nodes (20): formatted_generation_date(), formatted_generation_series(), generation_date(), date, Return the month/year form used on mark-scheme covers., _extract_source_questions(), render_source_booklet(), _source_sections() (+12 more)

### Community 31 - "test_aqa_business.py"
Cohesion: 0.06
Nodes (48): generate_package(), Path, FinancialPosition, format_number(), The single source of truth for Paper 1 financial-statement figures., Format an exam answer without meaningless trailing zeroes., build_paper(), _extract() (+40 more)

### Community 32 - "test_shared_numeric_integrity.py"
Cohesion: 0.13
Nodes (38): _independently_validate_candidate(), check_published_outputs(), Bind each asserted result to its role in the published working, never a number…, accounting_tasks(), GivenRateClient, parametrize, test_abc_checks_every_asserted_intermediate_without_rounding_into_final(), test_all_p2_closed_calculations_are_source_derived_and_exhaustively_reconciled() (+30 more)

### Community 33 - "OCRAnswerLines"
Cohesion: 0.13
Nodes (15): AnswerLineFlowable, AQACompactAnswerLines, OCRAnswerLines, OCRComputerScienceAnswerLines, Flowable, Return a Table subclass whose raw string cells use the controlled font.…, Shared, measured answer-line primitive used by every board renderer., OCR dotted writing rules inside the existing allocated answer area. Reviewed… (+7 more)

### Community 34 - "aqabizgen/render_pdf.py"
Cohesion: 0.12
Nodes (46): aqa_front_matter_pages(), Flowable, SelectedResponseContract, _artifacts(), _additional_answer_page(), _ao_summary(), _assessment_objectives_page(), _break_even_diagram() (+38 more)

### Community 35 - "open_credit.py"
Cohesion: 0.13
Nodes (30): cpu_credit_allocations(), cpu_credit_contract(), _cpu_quote_supports_criterion(), CreditJudgement, CriterionDecision, _has_unambiguous_instruction_antecedent(), _normalise_cpu_clauses(), _passive_relation_patterns() (+22 more)

### Community 36 - "solve_selected_response"
Cohesion: 0.09
Nodes (46): _better_than_target(), _decimal(), _display_decimal(), _money_choice(), _numeric_choice(), _percent_choice(), _plain_decimal(), Any (+38 more)

### Community 37 - "test_render_pdf.py"
Cohesion: 0.12
Nodes (51): _apply_edexcel_page_boxes(), Path, Match Pearson question-paper bleed and crop boxes without changing A4 content., render_question_paper(), _answer_rule_count(), _blank_axis_lines(), _blueprint_with_section_a_question(), _dark_pixels() (+43 more)

### Community 38 - "EconomicsSource"
Cohesion: 0.07
Nodes (48): calculation(), calculation_label(), calculation_prompt(), calculation_working(), EconomicsSource, BaseModel, Decimal, model_validator (+40 more)

### Community 39 - "GeneratedFile"
Cohesion: 0.05
Nodes (34): .body, AppDefaults, AppLinks, AppStorageKey, SecretAccount, Bool, String, URL (+26 more)

### Community 40 - "AssessmentCheckpointStore"
Cohesion: 0.11
Nodes (32): generate_unique_paper(), Replace draft items while keeping the authoritative assessment blueprint frozen., AssessmentCheckpointStore, CheckpointCorrupt, CheckpointIdentity, CheckpointMismatch, Any, BaseModel (+24 more)

### Community 41 - "assessment_package.py"
Cohesion: 0.10
Nodes (45): objective_policy_for(), Subject meaning for AO labels, independent of item tariffs and renderers., Resolve family IDs, subject names or qualification codes., _assessment_contract(), AssessmentPackageCompatibilityError, _authoring_provenance(), _contains_non_finite(), _evidence_ids() (+37 more)

### Community 42 - "test_ocr_economics.py"
Cohesion: 0.13
Nodes (28): generate_package(), Path, build_paper(), _instructions(), Syllabus, _candidate_objectives(), Path, test_all_packages_render_reference_page_geometry() (+20 more)

### Community 43 - "properties"
Cohesion: 0.04
Nodes (48): $ref, title, type, SourcePath, TopicRecord, minLength, title, type (+40 more)

### Community 44 - "IndependentSolver"
Cohesion: 0.12
Nodes (47): alternative_permission(), Any, Only known host-authored permissions can bypass answer-value checking., IndependentSolver, Solve an item in a context that deliberately excludes its draft scheme., credit_identity(), credit_item_projection(), review_open_credit() (+39 more)

### Community 45 - "tests/test_closed_response_integrity.py"
Cohesion: 0.21
Nodes (24): closed_item(), parametrize, ResponseClient, scheme(), test_captured_duplicate_partial_points_cannot_pass_closed_classification(), test_closed_numeric_and_truth_rows_compare_by_slot_not_number_bag(), test_closed_numeric_contract_keeps_accepted_frequency_unit_formats(), test_closed_numeric_contract_rejects_wrong_frequency_value_or_scale() (+16 more)

### Community 46 - "providers.py"
Cohesion: 0.08
Nodes (43): _hosted_client(), _aqa_cs_part_count(), _edexcel_part_count(), hosted_client(), HostedLLMClient, _normalise_base_url(), _ollama_json_schema(), _ollama_output_budget() (+35 more)

### Community 47 - "reference_corpus.py"
Cohesion: 0.13
Nodes (45): MonkeyPatch, Path, test_document_path_requires_filename(), test_document_path_stays_inside_corpus(), test_download_manifest_records_failure_and_continues(), test_parse_aqa_resources_filters_modified_papers(), test_parse_ocr_resources_uses_a_level_tab_only(), test_parse_ocr_specifications_keeps_a_level_not_as_level() (+37 more)

### Community 48 - "test_sql_answer_verification.py"
Cohesion: 0.12
Nodes (43): Validate the answer and every model-presented full statement separately., sql_source_intent_sha256(), validate_sql_response(), _part_solver_projection(), EvidenceRecord, ValueError, _validate_sql_solver_projection(), candidate_stimulus_data() (+35 more)

### Community 49 - "test_mlx_setup.py"
Cohesion: 0.08
Nodes (45): _available_cache_bytes(), ensure_mlx_ready(), handle_mlx_status(), handle_setup_mlx(), install_mlx_runtime(), is_managed_development_environment(), load_mlx_model(), mlx_runtime_available() (+37 more)

### Community 50 - "test_computer_science_objectives.py"
Cohesion: 0.06
Nodes (64): generate_package(), Path, load_rule(), build_paper(), Syllabus, load_syllabus(), BaseModel, Path (+56 more)

### Community 51 - "aqaecongen/render_pdf.py"
Cohesion: 0.15
Nodes (37): _artifacts(), _assessment_objectives_table(), _context_data_table(), _context_first_page(), _context_second_page(), _cover_profile(), _document(), _economic_diagram() (+29 more)

### Community 52 - "CodingKeys"
Cohesion: 0.07
Nodes (36): CodingKeys, appContextWindow, contextWindow, defaultModel, detail, downloadSizeGB, id, maximumMemoryGB (+28 more)

### Community 53 - "independent_solver.py"
Cohesion: 0.11
Nodes (31): content_similarity(), Weighted token-shingle Jaccard similarity in the closed interval 0...1., collect_credit_rules(), credit_rule(), CreditRule, declared_rule_metadata_present(), BaseModel, Origin-preserving open credit rules; never promote model advice to authority. (+23 more)

### Community 54 - "reference_demand_profiles.py"
Cohesion: 0.12
Nodes (35): operation_response_mode(), Shared generated/source semantics for non-computational written tasks., Pattern, build_document(), CorpusFamily, _distribution(), extract_reference_features(), extract_reference_items() (+27 more)

### Community 55 - "test_aqa_economics.py"
Cohesion: 0.07
Nodes (55): AppliedMCQSource, _bounded_text(), Any, _tasks(), Return the immutable rules for one printed option (one-based)., resolve_question_rules(), _applied_mcq(), _build_mcq_option() (+47 more)

### Community 56 - "type"
Cohesion: 0.06
Nodes (40): type, additionalProperties, $ref, title, type, additionalProperties, title, type (+32 more)

### Community 57 - "reference_demand.py"
Cohesion: 0.14
Nodes (32): assessment_objectives_for_item(), audit_form_demand(), build_item_demand_target(), _checked_in_profile_fingerprint(), _cognitive_operations(), _collapse_command_distribution(), _command_family(), _difficulty_evidence() (+24 more)

### Community 58 - "properties"
Cohesion: 0.05
Nodes (39): high, low, standard, anyOf, title, minLength, title, type (+31 more)

### Community 59 - "generator/tests/test_assessment_contracts.py"
Cohesion: 0.09
Nodes (47): _question_solver_item(), paper(), parametrize, test_actual_level_tariffs_have_distinct_usable_band_descriptors(), test_all_seeded_styles_have_contract_credit_not_topic_note_filler(), test_business_expansion_short_credit_marks_one_complete_route(), test_complete_declared_numeric_operations_have_literal_answers(), test_content_driven_scheme_policy_rejects_missing_printed_assessment() (+39 more)

### Community 60 - "PaperCreatorTests"
Cohesion: 0.09
Nodes (15): CatalogLoader, CatalogLoadError, duplicateBoard, duplicateImplementation, emptyImplementation, .errorDescription, implementationMissingFromCatalog, missingResource (+7 more)

### Community 61 - "PaperBlueprint"
Cohesion: 0.24
Nodes (18): _count_pages(), _draw_answer_page_header(), _draw_continuation_lines(), _draw_paper_3_pages(), _draw_question_footer(), _draw_question_pages(), _draw_section_b_source_pages(), _draw_section_c_answer_pages() (+10 more)

### Community 62 - "DocumentPreviewView"
Cohesion: 0.06
Nodes (33): AppKit, Combine, DocumentPreviewView, .body, .exportAlertBinding, .provenanceRecord, .selectedBinding, .selectedFile (+25 more)

### Community 63 - "pdf_validation.py"
Cohesion: 0.11
Nodes (33): compare_page_evidence(), _contrast_against_white(), _contrast_ratio(), _count_score(), _font_embedding(), _font_evidence(), GlyphMetric, _is_decorative_bleed() (+25 more)

### Community 64 - "ObjectivePolicy"
Cohesion: 0.22
Nodes (4): ObjectivePolicy, Any, Reject unsupported labels in new or persisted qualified contracts., CS tasks are not classified from their tariff or AO3 label alone.

### Community 65 - "properties"
Cohesion: 0.06
Nodes (36): aqa-topic-operation-records-v3, edition-leaf-path-features-v2, full-paper, question-bank, unqualified-reference-v1, enum, minLength, type (+28 more)

### Community 66 - "NumericOutput"
Cohesion: 0.14
Nodes (31): CS component policy audit over candidate-answerable paths, not printed totals., Exact raw-provider shape; semantic validation remains item-specific below., SolverResponseEnvelope, check_numeric_alternatives(), CheckedNumericOutput, CheckedTextOutput, display(), _equivalent_quantity() (+23 more)

### Community 67 - ".baseQuery"
Cohesion: 0.39
Nodes (4): SecretStore, Any, String, Security

### Community 68 - "benchmark.py"
Cohesion: 0.12
Nodes (33): apple_cpu_core_split(), available_memory_gb(), avg(), clamp(), cpu_brand(), cpu_load_percent(), cpu_probe(), disk_probe() (+25 more)

### Community 69 - "BackendClient"
Cohesion: 0.17
Nodes (14): BackendClient, BackendClientError, backendMissing, .errorDescription, pythonMissing, pythonVenvUnreadable, BackendFile, LaunchConfiguration (+6 more)

### Community 70 - "aqa_section_intro"
Cohesion: 0.10
Nodes (25): aqa_lozenge(), aqa_section_intro(), AQAQuestionHeaderFactory, flowable_question_block(), independent_practice_page(), OCRQuestionHeaderFactory, page_sequence(), Color (+17 more)

### Community 71 - "topic_id"
Cohesion: 0.29
Nodes (7): 4.10, 4.12, 4.2, topic_id, enum, title, type

### Community 72 - "Contract-First Paper Generation and Release Qualification"
Cohesion: 0.06
Nodes (31): 1. Assessment Contract, 2. Deterministic Assessment Data, 3. Item-Level AI Workflow, 4. Evidence Binding and Factual Quality, 5. Mark-Scheme Quality, 6. Board Layout Adapters, 7. Bounded Rendering, 8. Progress, Cancellation, and Resume (+23 more)

### Community 73 - "test_aqa_accounting.py"
Cohesion: 0.11
Nodes (27): build_paper(), _extract(), _number(), Random, Syllabus, _values(), Independent AQA 7127 practice-paper generator., parametrize (+19 more)

### Community 74 - "test_accounting_objectives.py"
Cohesion: 0.23
Nodes (18): load_rule(), paper_for(), parametrize, test_accounting_ao3_short_analysis_does_not_imply_judgement(), test_accounting_does_not_offer_unallocated_objectives_in_guidance(), test_accounting_rejects_invalid_ao_even_if_marks_still_add_up(), test_accounting_rule_cannot_fall_back_to_generic_allocation(), test_accounting_uses_official_item_budgets_and_component_totals() (+10 more)

### Community 75 - "ExamPageProfile"
Cohesion: 0.17
Nodes (31): _draw_aqa_footer(), _draw_aqa_page(), _draw_barcode(), draw_exam_page(), _draw_independent_notice(), _draw_ocr_notice(), _draw_ocr_page(), _draw_ocr_rules() (+23 more)

### Community 76 - "test_app_backend.py"
Cohesion: 0.15
Nodes (29): _safe_provider_detail(), CaptureFixture, CompletedProcess, Path, run_bridge(), run_bridge_raw(), test_aqa_accounting_all_papers_generate_expected_files(), test_aqa_business_all_papers_generate_expected_files() (+21 more)

### Community 77 - "document_dsl/__init__.py"
Cohesion: 0.05
Nodes (92): AnswerSpace, BaseComponent, BlankPage, Component, ContinuationPage, Cover, Diagram, Graph (+84 more)

### Community 78 - "test_mark_scheme_layout.py"
Cohesion: 0.16
Nodes (33): pdf_font_names(), Return the font families actually used by visible text spans., _cleanup_graph_cache(), Render each contract criterion as a discrete, visible examiner point., render_mark_scheme(), _source_backed_mark_scheme_lines(), _assert_complete_contract_scheme(), _blueprint_with_section_a_calculation() (+25 more)

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
Cohesion: 0.07
Nodes (55): load_reference_demand_document(), BaseModel, model_validator, Path, ReferenceDemandDocument, module(), profile_payload(), parametrize (+47 more)

### Community 83 - "graphs.py"
Cohesion: 0.30
Nodes (26): Axes, ad_as_diagram(), _arrow_axes(), _ax(), circular_flow_diagram(), consumer_producer_surplus(), demand_supply_diagram(), _ensure_style() (+18 more)

### Community 84 - "reference_evidence.py"
Cohesion: 0.08
Nodes (39): audit_candidate_paths(), CandidatePath, CandidateTopology, enumerate_candidate_paths(), identity(), path_metrics(), PathOption, PathSection (+31 more)

### Community 85 - "AQA Computer Science bank-item reference support"
Cohesion: 0.13
Nodes (12): OCR question-paper ruling and final-page correction, Live matrix integrity, Qualification boundary, Reference support, live qualification and PDF repairs, Renderer repairs, Verification record, Admission rule, AQA Computer Science bank-item reference support (+4 more)

### Community 86 - "PathSection"
Cohesion: 0.09
Nodes (22): answer_options, candidate_marks, options, exclusiveMinimum, title, type, exclusiveMinimum, title (+14 more)

### Community 87 - "draw_barcode"
Cohesion: 0.25
Nodes (16): CanvasBarcodeStyle, draw_barcode(), draw_glyph_answer_rules(), draw_solid_answer_rules(), GlyphRuleStyle, Canvas, Draw a fixed number of solid response rules and return the next baseline., Draw selectable glyph-based response rules and return the next baseline. (+8 more)

### Community 88 - "SubjectPlugin"
Cohesion: 0.39
Nodes (3): Any, Protocol, SubjectPlugin

### Community 89 - "test_coverage_matrix.py"
Cohesion: 0.20
Nodes (24): family(), matrix(), Path, test_catalog_availability_is_owned_only_by_registry(), test_checked_in_matrix_is_deterministic_and_current(), test_existing_generators_are_reported_without_false_verification(), test_matrix_exactly_covers_layout_profiles(), test_no_verified_paper_has_a_failed_gate() (+16 more)

### Community 90 - "test_layout_master.py"
Cohesion: 0.07
Nodes (45): _aqa_cs_printed_credit(), conform_generated_documents(), _edexcel_printed_credit(), Path, Generated-content policy is not an observed reference-count range., Content-driven pagination must preserve every published marking statement., runtime_page_count_policy(), conform_pdf_to_box_template() (+37 more)

### Community 91 - "Question"
Cohesion: 0.09
Nodes (45): Render only public schema facts; no worked query is present., render_sql_schema(), SQLSourceContract, derive_task_semantics(), Any, BaseModel, Strict, deterministic task contracts for AQA CS topic-reference evidence., The serialised summary is valid only when it agrees with the question. (+37 more)

### Community 92 - "reference-demand-profile.schema.json"
Cohesion: 0.08
Nodes (24): derived_aggregate_only, profiles, purpose, retains_source_text, additionalProperties, const, $id, schema_version (+16 more)

### Community 94 - "properties"
Cohesion: 0.08
Nodes (25): type, pattern, type, pattern, pattern, type, type, pattern (+17 more)

### Community 95 - "generator_registry.py"
Cohesion: 0.24
Nodes (15): _capability(), generator_capabilities(), generator_subjects(), _paper_qualification(), PaperQualification, Any, _relative_path(), test_backend_bundle_script_is_registry_driven() (+7 more)

### Community 96 - "generation.py"
Cohesion: 0.21
Nodes (21): progress_emitter(), _atomic_publish(), _cancel_generation(), checkpoint_path_for_job(), emit_generated_files(), finalize_generated_documents(), GenerationCancelled, _generator_version() (+13 more)

### Community 98 - "candidate_identity.py"
Cohesion: 0.26
Nodes (16): _export_difficulty_candidate_projection(), candidate_review_content(), difficulty_candidate_projection(), DifficultyCandidateProjection, edexcel_difficulty_candidate_projection(), ensure_difficulty_candidate_projection(), _mapping(), Any (+8 more)

### Community 99 - "Paper Creator Excellence Programme Design"
Cohesion: 0.08
Nodes (23): Assessment Validity and Mark Schemes, Baseline on 26 August 2026, Definition of Done, Design Principles, Deterministic Visual Components, Empirical Calibration, Independent Solving, macOS Product Experience (+15 more)

### Community 100 - "required"
Cohesion: 0.13
Nodes (24): assessment_kind, cognitive_operation_distribution, command_family_distribution, command_word_distribution, comparison_basis, demand_distribution, evidence_gaps, evidence_policy_id (+16 more)

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
Cohesion: 0.19
Nodes (26): extract_pdf_evidence(), _layout_profiles(), Counter, Path, Fail closed on malformed, substituted, annotated, or low-resolution PDFs., Extract print and accessibility evidence without retaining source prose. Glyph…, validate_pdf_for_release(), _validate_typography_profile() (+18 more)

### Community 105 - ".initialEstimate"
Cohesion: 0.16
Nodes (12): EstimateFactor, GenerationEstimate, .etaDate, .remainingText, TimeInterval, EstimateTuning, GenerationEstimator, Bool (+4 more)

### Community 106 - "$defs"
Cohesion: 0.09
Nodes (23): maximum, minimum, $defs, distribution, Observations, QuarantinedForm, SourceItem, tolerance (+15 more)

### Community 107 - "test_science_subjects.py"
Cohesion: 0.14
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

### Community 111 - "pastpapergen/cli.py"
Cohesion: 0.14
Nodes (23): ArtifactSpec, BuildResult, FamilyAdapter, Path, run_family_adapter(), default_ollama_model(), model_recommendations(), OllamaModelRecommendations (+15 more)

### Community 112 - "accounting.py"
Cohesion: 0.28
Nodes (22): _accounting_endings(), accounting_outputs(), _appropriation(), _assets(), derive_accounting_open_response_context(), _exact(), _income(), _ledger() (+14 more)

### Community 113 - "reconcile_solution"
Cohesion: 0.12
Nodes (35): reconcile_solution(), parametrize, solve(), test_assembly_trace_checks_every_register_series_and_stored_value(), test_finite_outputs_are_keyed_and_reject_a_changed_value(), test_full_truth_table_requires_every_input_combination(), test_graph_route_accepts_equivalent_ordered_vertex_notation(), test_graph_route_alternatives_use_the_same_ordered_vertex_comparison() (+27 more)

### Community 114 - "pastpapergen/notes.py"
Cohesion: 0.20
Nodes (19): _clean_chunk(), essay_capable_topic_ids(), _flush_note_chunk(), _is_exam_point(), _is_note_noise(), _looks_like_heading(), _note_chunks(), note_context_for_topic() (+11 more)

### Community 115 - "properties"
Cohesion: 0.10
Nodes (21): minLength, type, minLength, type, minLength, type, format, type (+13 more)

### Community 116 - "aqa_accounting_calibration.py"
Cohesion: 0.34
Nodes (14): _band(), build_generated_profile(), build_reference_profile(), build_report(), _command(), _fingerprint(), _inventory(), main() (+6 more)

### Community 117 - "CanonicalSolution"
Cohesion: 0.14
Nodes (25): _bounded(), GenerationEvidenceError, Any, Path, ValueError, Private, bounded evidence for rejected generation; never approved checkpoints., Save only explicitly supplied evidence, not arbitrary errors or prompts.…, save_failure_diagnostic() (+17 more)

### Community 118 - "required"
Cohesion: 0.12
Nodes (20): comparable_metrics, extraction_policy, feature_basis, non_comparable_features, objective_basis, paths, printed_marks, source_sha256 (+12 more)

### Community 119 - "GeneratedPaper"
Cohesion: 0.07
Nodes (76): _demand_band(), GeneratedPaper, GeneratedSection, _hydrate_assessment_metadata(), _objective_allocation(), PaperRule, _prompt_uses_command_word(), BaseModel (+68 more)

### Community 120 - "validate_generator_migration.py"
Cohesion: 0.24
Nodes (10): build_parser(), _layout_board(), main(), MigrationIssue, MigrationReport, MigrationValidator, Any, ArgumentParser (+2 more)

### Community 121 - "validate_mark_scheme_item"
Cohesion: 0.25
Nodes (17): _contains_any(), MarkSchemeQuality, _normalise(), Any, validate_mark_scheme_item(), _item(), test_accounting_follow_through_metadata_counts_as_method_guidance(), test_calculation_requires_method_or_working() (+9 more)

### Community 122 - "subject_plugins.py"
Cohesion: 0.18
Nodes (19): board_profile(), board_profile_ids(), BoardProfile, _normalise_identifier(), discover_subject_plugin(), _normalise_identifier(), register_subject_plugin(), subject_plugin_ids() (+11 more)

### Community 123 - "stratum"
Cohesion: 0.29
Nodes (7): context-incomplete, core, mixed, stratum, enum, title, type

### Community 124 - "CandidateResponse"
Cohesion: 0.12
Nodes (24): BoardLevelPolicy, LevelDescriptor, LevelOfResponseEngine, load_level_policies(), MarkAnnotation, MarkDecision, BaseModel, model_validator (+16 more)

### Community 125 - "paper"
Cohesion: 0.33
Nodes (6): 1, 2, enum, title, type, paper

### Community 126 - "test_computer_science_subject.py"
Cohesion: 0.21
Nodes (12): ComputerSciencePlugin, _evaluate_boolean(), normalise_pseudocode(), pseudocode_equivalent(), Any, truth_table(), test_four_mark_boolean_tasks_have_equivalent_explicit_working(), test_computer_science_uses_the_specialised_plugin() (+4 more)

### Community 127 - "build_layout_masters.py"
Cohesion: 0.29
Nodes (18): _box(), _colour(), _content_box(), _drawing_kind(), _drawings(), extract_layout_master(), _furniture_signature(), _images() (+10 more)

### Community 128 - "Canvas"
Cohesion: 0.12
Nodes (40): _draw_answer_lines(), _draw_answer_lines_until(), _draw_axis_arrow(), _draw_blank_answer_axes(), _draw_calculate_part_with_working_lines(), _draw_centred_instruction_line(), _draw_compact_part(), _draw_context_box() (+32 more)

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

### Community 134 - "test_aqa_accounting_calibration.py"
Cohesion: 0.53
Nodes (4): report(), test_both_papers_pass_multi_seed_automated_checks(), test_external_difficulty_gates_remain_false(), test_reference_evidence_is_aggregate_only()

### Community 135 - "enum"
Cohesion: 0.12
Nodes (16): algorithm-trace, calculation, computational-analysis, computational-design, constructed-response, extended-evaluation, mathematical-argument, multi-stage-calculation (+8 more)

### Community 136 - "IncomeStatementCase"
Cohesion: 0.17
Nodes (4): IncomeStatementCase, Decimal, Complete, internally consistent source for the Paper 1 company statement., _round_pounds()

### Community 137 - "ApplicationCoordinator"
Cohesion: 0.04
Nodes (37): AnyCancellable, DateFormatter, ExamCatalog, .readyBoards, OllamaState, PaperConfiguration, .body, .visibleAssessments (+29 more)

### Community 138 - "properties"
Cohesion: 0.12
Nodes (16): minLength, type, minLength, type, minLength, type, blueprint, contract (+8 more)

### Community 139 - "test_generator_migration.py"
Cohesion: 0.23
Nodes (13): Path, test_all_current_families_pass_declarative_migration_validation(), test_broken_fixture_reports_every_onboarding_surface(), test_scaffold_emits_complete_unadvertised_family_and_refuses_overwrite(), build_parser(), _cli_template(), main(), ArgumentParser (+5 more)

### Community 140 - "test_topic_reference_evidence.py"
Cohesion: 0.19
Nodes (23): bank_items(), module(), parametrize, A serialised hint must never override the question that will be printed., Only the versioned contract may establish a reference comparison., test_actual_same_topic_operation_and_mode_still_matches(), test_bank_support_rejects_changed_work_not_just_matching_topic_words(), test_forged_or_sparse_source_inventory_cannot_qualify_bank() (+15 more)

### Community 141 - "BenchmarkChart"
Cohesion: 0.18
Nodes (16): KeyPath, value, BenchmarkChart, .accessibilitySummary, BenchmarkLiveCharts, .body, .cpuChart, .cpuThroughputChart (+8 more)

### Community 142 - "cspapergen/ollama_client.py"
Cohesion: 0.07
Nodes (57): numeric_tokens(), Extract quantities exactly enough to catch broken data/source rewrites., aqa_cs_difficulty_candidate(), aqa_cs_solver_item(), authoring_route(), Any, question_content_sha256(), AQA CS source-coupled review identity, shared by authoring/resume/export. This… (+49 more)

### Community 143 - "Difficulty Calibration v2 Qualification Report"
Cohesion: 0.25
Nodes (6): Difficulty Calibration v2 Qualification Report, Implemented evidence, Initial 30 August verification, Interpretation, Outcome, Reproduction and local evidence

### Community 144 - "Continued qualification — 31 August"
Cohesion: 0.13
Nodes (14): Continued qualification — 31 August, Difficulty Calibration v2 Implementation Plan, Global Constraints, Task 10: Supported-decision command calibration, Task 11: Visual review correction, Task 1: Reference profile schema v2, Task 2: Observable item demand contracts, Task 3: Solver-grounded difficulty judge (+6 more)

### Community 145 - "properties"
Cohesion: 0.15
Nodes (15): approved, draft, retired, type, type, null, string, minLength (+7 more)

### Community 146 - "required"
Cohesion: 0.13
Nodes (15): maximum_acceptable_facility, maximum_dif_gap, minimum_acceptable_facility, minimum_candidates, minimum_discrimination, minimum_double_marked_pairs, minimum_facility_coverage, minimum_group_responses (+7 more)

### Community 148 - "test_repository_hygiene.py"
Cohesion: 0.23
Nodes (12): type, path, test_committed_inventory_matches_the_current_repository(), test_every_tracked_file_has_a_durable_classification(), test_generated_and_binary_outputs_are_rejected(), test_maintained_visual_assets_are_classified_without_allowing_arbitrary_pngs(), test_root_lint_configuration_is_release_configuration(), Classification (+4 more)

### Community 149 - "additionalProperties"
Cohesion: 0.13
Nodes (15): items, minItems, type, uniqueItems, items, minItems, type, uniqueItems (+7 more)

### Community 150 - "id"
Cohesion: 0.13
Nodes (15): PathOption, minLength, title, type, items, minItems, title, type (+7 more)

### Community 151 - "aqa_business_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 152 - "ocr_computer_science_calibration.py"
Cohesion: 0.34
Nodes (14): _band(), build_generated_profile(), build_reference_profile(), build_report(), _command(), _fingerprint(), _inventory(), main() (+6 more)

### Community 153 - "ocr_economics_calibration.py"
Cohesion: 0.34
Nodes (14): _band(), build_generated_profile(), build_reference_profile(), build_report(), _command(), _fingerprint(), main(), _page_count() (+6 more)

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

### Community 165 - "properties"
Cohesion: 0.09
Nodes (22): duration_minutes, sections, total_marks, additionalProperties, properties, required, title, type (+14 more)

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

### Community 173 - "emit"
Cohesion: 0.26
Nodes (16): build_parser(), handle_bundle_check(), main(), ArgumentParser, Namespace, Fail fast when a packaged backend is missing a dynamic generator., emit(), emit_progress() (+8 more)

### Community 174 - "Architecture"
Cohesion: 0.18
Nodes (11): Architecture, Canonical registry, Extension contract, Failure containment, Fidelity qualification boundary, Package transaction, PDF portability and accessibility, Product boundary (+3 more)

### Community 175 - "End-to-end runtime"
Cohesion: 0.18
Nodes (11): 10. Completion and file handling, 1. Catalogue and selection, 2. Swift state and command construction, 3. Process bridge and event protocol, 4. Backend validation and dispatch, 5. Two different generation architectures, 6. Blueprint construction, 7. Provider behavior (+3 more)

### Community 176 - "Paper creator: deep project analysis"
Cohesion: 0.12
Nodes (17): Architectural pressure points, Current support and readiness, Difficulty and assessment validity, Executive assessment, Fidelity system: strengths and limits, Graphify project map, HIG-specific findings, macOS user-experience audit (+9 more)

### Community 177 - "Architecture"
Cohesion: 0.18
Nodes (10): Acceptance criteria, Architecture, Difficulty Calibration v2 Design, Form-level release gate, Independent calibration, Item targets, Purpose, Reference profiles (+2 more)

### Community 178 - "enum"
Cohesion: 0.18
Nodes (11): benchmark_done, benchmark_metric, benchmark_sample, done, error, file, hello, models (+3 more)

### Community 179 - "required"
Cohesion: 0.18
Nodes (11): collected_at, collector_role, consent_basis, dataset_id, row_level_data, source, specification_version, provenance (+3 more)

### Community 180 - "PhysicsPlugin"
Cohesion: 0.43
Nodes (3): PhysicsPlugin, Any, test_physics_requires_uncertainty_for_uncertainty_items()

### Community 181 - "SettingsPane.swift"
Cohesion: 0.16
Nodes (13): AISettingsTab, PrivacySettingsTab, .body, .body, SettingsPaneID, ai, output, privacy (+5 more)

### Community 182 - "profile_for"
Cohesion: 0.23
Nodes (19): profile_for(), items(), paths_module(), parametrize, test_complete_pairs_produce_six_eighty_mark_paths_not_cross_pairs(), test_correlated_source_vectors_cannot_pass_by_coordinatewise_bounds(), test_edexcel_leaf_only_marks_and_choice_groups(), test_explicit_selected_operation_is_not_relabelled_retrieval_in_audit() (+11 more)

### Community 183 - "Review focus"
Cohesion: 0.22
Nodes (8): Execution notes, Global constraints, Integration and publication, Reference evidence, live validation and PDF fidelity implementation plan, Review focus, Task 1: Source-backed topic-bank evidence, Task 2: Reliable live-matrix evidence and execution, Task 3: Measured visual repairs

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
Cohesion: 0.20
Nodes (10): Architecture and quality analysis, Build Checks, CLI, Development Reference Corpus, Paper creator, Privacy, Recommended Ollama model, Release status (+2 more)

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

### Community 193 - "ocrcsgen/generator.py"
Cohesion: 0.29
Nodes (12): _analysis_prompt(), _levels(), _programming_prompt(), _programming_scheme(), Random, Topic, _question(), _representation_calculation() (+4 more)

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

### Community 201 - "SubjectValidation"
Cohesion: 0.14
Nodes (11): Shared subject interfaces, independent of plugin implementations and discovery., SubjectValidation, ContractSubjectPlugin, Any, Safe baseline plugin for families with validation in their own contracts., BiologyPlugin, Any, EssaySubjectPlugin (+3 more)

### Community 202 - "_call_name"
Cohesion: 0.38
Nodes (6): Call, _call_name(), parametrize, Path, test_production_pdf_renderers_run_inside_atomic_transactions(), test_shared_family_adapter_owns_atomic_pdf_transaction()

### Community 203 - "build_backend.sh"
Cohesion: 0.29
Nodes (5): MPLCONFIGDIR, PYINSTALLER_CONFIG_DIR, PYTHONPATH, build_backend.sh script, XDG_CACHE_HOME

### Community 204 - "test_science_overlay.py"
Cohesion: 0.35
Nodes (16): apparatus_diagram(), ApparatusSpec, Atom, Bond, circuit_diagram(), CircuitComponent, CircuitSpec, molecule_diagram() (+8 more)

### Community 205 - "enum"
Cohesion: 0.29
Nodes (7): automation, examiner, internal_reviewer, psychometrician, subject_specialist, reviewer_identity_class, enum

### Community 206 - "ocregen/generator.py"
Cohesion: 0.39
Nodes (11): percentage_change_context(), Candidate chart endpoints and the requested one-decimal percentage output., _evaluation_scheme(), _extract(), _extract_number(), _mcq(), Random, Topic (+3 more)

### Community 207 - "model"
Cohesion: 0.29
Nodes (7): digest, name, provider, additionalProperties, required, type, model

### Community 208 - "test_configured_family.py"
Cohesion: 0.36
Nodes (10): generate_package(), Path, load_syllabus(), Path, _family_syllabus(), Path, _syllabus(), test_aqa_mathematics_preview_covers_pure_mechanics_and_statistics() (+2 more)

### Community 209 - "Rect"
Cohesion: 0.26
Nodes (10): _clamp_fitz_rect(), conform_pdf_page_boxes(), _fitz_rect_close(), _page_matches_box_set(), Any, Apply measured page boxes without importing any reference artwork or text., Rect, _rect_values() (+2 more)

### Community 210 - "_written"
Cohesion: 0.32
Nodes (8): _nearest_hundred(), _levels(), Topic, _written(), test_company_and_partnership_schemes_expose_complete_working_data(), test_locked_calculation_schemes_are_exactly_derived_from_the_case_data(), test_locked_calculation_schemes_include_final_answers_and_all_case_numbers(), test_seeded_partnership_allocations_balance_without_rounding_losses()

### Community 211 - "CoverProfile"
Cohesion: 0.07
Nodes (42): aqa_question_cover(), CoverProfile, _draw_aqa_mark_scheme_cover(), _draw_cover_barcode(), draw_mark_scheme_cover(), _draw_ocr_mark_scheme_cover(), mark_scheme_cover(), MarkSchemeCover (+34 more)

### Community 212 - "test_ocr_computer_science_calibration.py"
Cohesion: 0.53
Nodes (4): report(), test_difficulty_remains_external_evidence_gated(), test_multi_seed_structural_demand_passes(), test_reference_evidence_is_aggregate_only()

### Community 213 - "qualification-schema.json"
Cohesion: 0.33
Nodes (5): additionalProperties, $id, $schema, title, type

### Community 214 - "test_humanities_overlay.py"
Cohesion: 0.55
Nodes (9): map_diagram(), MapFeature, MapSpec, Drawing, timeline_diagram(), TimelineEvent, TimelineSpec, test_humanities_diagrams_reject_misleading_or_invalid_inputs() (+1 more)

### Community 215 - "test_difficulty_calibration.py"
Cohesion: 0.53
Nodes (4): report(), test_calibration_retains_no_official_text_or_paths(), test_difficulty_is_not_promoted_without_human_and_psychometric_evidence(), test_every_paper_has_multi_seed_structural_evidence()

### Community 216 - "generate_package"
Cohesion: 0.29
Nodes (12): generate_package(), Path, page_count(), Path, test_both_packages_render_36_page_question_papers(), test_invalid_paper_is_rejected(), test_paper_one_mark_scheme_matches_reference_question_sequence(), test_paper_one_section_a_matches_measured_case_and_account_pages() (+4 more)

### Community 217 - "cspapergen/cli.py"
Cohesion: 0.16
Nodes (17): _artifacts(), default_output_dir(), generate_package(), _improve(), main(), Path, _supporting(), test_final_additional_answer_page_reserves_independent_notice() (+9 more)

### Community 218 - "generator_working_directory"
Cohesion: 0.40
Nodes (4): generator_working_directory(), fixture, MonkeyPatch, FixtureRequest

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

### Community 239 - "Open Sans cover fonts"
Cohesion: 0.33
Nodes (4): Medium, Open Sans cover fonts, SemiBold, Bundled examination fonts

### Community 262 - "JobHistoryView"
Cohesion: 0.25
Nodes (9): GenerationJobState, .systemImage, .title, JobHistoryView, .body, .selectedRecord, GenerationJobRecord, Set (+1 more)

### Community 263 - "cspapergen/notes.py"
Cohesion: 0.38
Nodes (9): cache_notes(), discover_note_pdfs(), _extract_text(), note_context_for_topic(), NotesManifest, Path, _topic_prefixes(), test_cache_notes_extracts_text_into_project_cache() (+1 more)

### Community 264 - "test_source_candidate_paths.py"
Cohesion: 0.23
Nodes (13): _fixture_pdf(), module(), fixture, Original synthetic text, with the audited editions' page/mark structure., source_corpus(), test_aqa_selected_source_operations_do_not_manufacture_objective_tags(), test_business_edition_does_not_assume_same_question_numbers(), test_clean_ocr_mcq_rows_keep_published_ao_and_non_retrieval_operations() (+5 more)

### Community 265 - "paper1_reference_code"
Cohesion: 0.33
Nodes (9): paper1_reference_code(), Shared reference snippets used by the renderer and publication integrity gate., parametrize, test_add_example_constructs_the_scenario_record_type(), test_adjustment_example_implements_the_actual_function_contract(), test_reference_functions_integrate_with_the_generated_skeleton(), test_report_example_is_one_pass_and_preserves_empty_categories_and_ties(), test_timing_example_uses_supplied_functions_and_fresh_equal_trials() (+1 more)

### Community 266 - "test_ocr_economics_printed_credit.py"
Cohesion: 0.27
Nodes (8): load_syllabus(), BaseModel, Path, Syllabus, Topic, test_ocr_economics_prints_all_credit_at_reference_body_size(), test_ocr_guidance_retains_distinct_labels_when_credit_wording_is_identical(), test_ocr_long_credit_expands_pages_without_clipping_or_repeated_padding()

### Community 267 - "31 August continued qualification findings"
Cohesion: 0.25
Nodes (8): 31 August continued qualification findings, Accounting objective and credit calibration verified, Closed-response integrity correction, Computer Science implementation — corrective review still open, Computer Science reviewed fix — separate live and layout limits, Further calibration corrections in progress, Shared numeric reconciliation remains a release blocker, Shareholder source correction verified

### Community 268 - "Teacher-feedback follow-up — 27 September 2026"
Cohesion: 0.18
Nodes (11): Clean-runner and live follow-up, Content and rendering follow-through, Corrections made in this pass, Follow-up repairs — 28 September 2026, Output evidence and limitations, Publication follow-up, Remaining work before any “finalised” claim, Status and scope (+3 more)

### Community 269 - "Selected-response label integrity implementation plan"
Cohesion: 0.33
Nodes (5): Global constraints, Review focus, Selected-response label integrity implementation plan, Subsequent bounded work (separate implementation tasks), Task 1: Bind opportunity-cost product labels

### Community 270 - "_draw_cover"
Cohesion: 0.22
Nodes (14): economics_exam_schedule(), ExamSchedule, formatted_economics_exam_date(), date, _draw_boxes(), _draw_cover(), _draw_crop_marks(), _draw_source_cover() (+6 more)

### Community 271 - "Examiner-readiness standard"
Cohesion: 0.50
Nodes (3): Current findings and delivery order, Examiner-readiness standard, Release criteria for every advertised route

### Community 272 - "parse_model_recommendations"
Cohesion: 0.42
Nodes (8): OllamaModelTier, parse_model_recommendations(), Any, _required_text(), payload(), test_default_model_must_be_a_declared_recommendation(), test_recommendation_registry_is_contiguous_and_owns_cli_default(), test_recommendation_registry_rejects_memory_gaps()

### Community 274 - "test_ocr_economics_calibration.py"
Cohesion: 0.53
Nodes (4): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence()

## Knowledge Gaps
- **1140 isolated node(s):** `BoardLayout`, `examforge-aqa-accounting`, `$schema`, `$id`, `title` (+1135 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `IndependentSolver` connect `IndependentSolver` to `GeneratedQuestion`, `load_syllabus`, `pastpapergen/ollama_client.py`, `cspapergen/ollama_client.py`, `test_solver_source_adapter.py`, `test_aqa_business.py`, `test_shared_numeric_integrity.py`, `solve_selected_response`, `tests/test_closed_response_integrity.py`, `test_sql_answer_verification.py`, `test_computer_science_objectives.py`, `independent_solver.py`, `test_aqa_economics.py`, `generator/tests/test_assessment_contracts.py`, `NumericOutput`, `test_aqa_accounting.py`, `Question`, `reconcile_solution`, `CanonicalSolution`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Why does `GeneratedQuestion` connect `GeneratedQuestion` to `Paragraph`, `aqaaccountgen/render_pdf.py`, `AssessmentContract`, `ocrcsgen/render_pdf.py`, `test_aqa_business.py`, `test_shared_numeric_integrity.py`, `aqabizgen/render_pdf.py`, `solve_selected_response`, `AssessmentCheckpointStore`, `assessment_package.py`, `aqaecongen/render_pdf.py`, `profile_for`, `test_aqa_economics.py`, `ocrcsgen/generator.py`, `ocregen/generator.py`, `_written`, `test_reference_demand.py`, `mark_scheme_enrichment.py`, `GeneratedPaper`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Why does `_extract_items()` connect `assessment_package.py` to `candidate_identity.py`, `load_syllabus`, `pastpapergen/ollama_client.py`, `solve_selected_response`, `generator/tests/test_assessment_contracts.py`, `test_topic_reference_evidence.py`, `cspapergen/ollama_client.py`, `test_sql_answer_verification.py`, `test_computer_science_objectives.py`, `test_reference_demand.py`, `profile_for`, `test_aqa_economics.py`, `reference_demand.py`, `test_layout_master.py`, `Question`, `test_solver_source_adapter.py`, `test_aqa_business.py`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Are the 25 inferred relationships involving `GeneratedQuestion` (e.g. with `AssessmentLLMClient` and `GenerationPolicy`) actually correct?**
  _`GeneratedQuestion` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `IndependentSolver` (e.g. with `AssessmentLLMClient` and `GenerationPolicy`) actually correct?**
  _`IndependentSolver` has 26 INFERRED edges - model-reasoned connections that need verification._
- **What connects `BoardLayout`, `examforge-aqa-accounting`, `$schema` to the rest of the system?**
  _1140 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ExamBoardOption` be split into smaller, more focused modules?**
  _Cohesion score 0.06599326599326599 - nodes in this community are weakly interconnected._