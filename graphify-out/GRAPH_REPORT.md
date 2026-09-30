# Graph Report - Past Paper Creation  (2026-09-30)

## Corpus Check
- 415 files · ~761,552 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 6866 nodes · 19270 edges · 274 communities (246 shown, 28 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 1122 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7d6a2c00`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- String
- GeneratedQuestion
- paper_fidelity_audit.py
- ai_assessment.py
- load_syllabus
- pastpapergen/ollama_client.py
- Text
- cspapergen/render_pdf.py
- build_paper_blueprint
- test_ocr_economics.py
- psychometrics.py
- ocregen/render_pdf.py
- pastpapergen/generator.py
- live_generation_matrix.py
- require_difficulty_review
- QualityInspector
- paper1_assets.py
- add_page_structure_tree
- ApplicationCoordinator
- RecentDocumentStore
- open_credit.py
- build_question
- Paragraph
- AssessmentContract
- properties
- ocrcsgen/render_pdf.py
- sql_contracts.py
- _mark_scheme_rows
- CodingKeys
- build_item_demand_target
- formatted_generation_date
- test_aqa_business.py
- test_shared_numeric_integrity.py
- CanonicalSolution
- aqabizgen/render_pdf.py
- AssessmentCheckpointStore
- solve_selected_response
- test_render_pdf.py
- test_source_credit_integrity.py
- .generate
- required
- assessment_package.py
- .load
- properties
- test_open_credit_reconciliation.py
- IndependentSolver
- providers.py
- reference_corpus.py
- cspapergen/ollama_client.py
- test_mlx_setup.py
- test_computer_science_objectives.py
- aqaecongen/render_pdf.py
- CodingKeys
- independent_solver.py
- reference_demand_profiles.py
- test_aqa_economics.py
- type
- draw_barcode
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
- pastpapergen/models.py
- aqa_section_intro
- Rect
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
- test_solver_source_adapter.py
- exam_blueprints.py
- .body
- test_coverage_matrix.py
- conform_generated_documents
- Question
- reference-demand-profile.schema.json
- NonCurrentAssetCase
- properties
- generator_registry.py
- generation.py
- PartnershipCase
- _normalise_font
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
- BackendClient
- required
- GeneratedPaper
- validate_generator_migration.py
- validate_mark_scheme_item
- subject_plugins.py
- test_generator_migration.py
- CandidateResponse
- cspapergen/notes.py
- test_computer_science_subject.py
- EvidenceRecord
- PathSection
- properties
- properties
- properties
- inspect_release_compliance
- SalesLedgerCase
- test_layout_master.py
- enum
- IncomeStatementCase
- ModelCoordinator
- properties
- configuredgen/generator.py
- test_topic_reference_evidence.py
- SubjectPlugin
- build_layout_masters.py
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
- test_aqa_business_calibration.py
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
- paper1_reference_code
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
- test_humanities_overlay.py
- model
- enum
- pastpapergen/render_pdf.py
- CostingCase
- CoverProfile
- ocrcsgen/generator.py
- qualification-schema.json
- _written
- test_ocr_computer_science_calibration.py
- generate_package
- cspapergen/cli.py
- generator_working_directory
- Cambridge International engineering foundation — 26 August 2026
- pull_request_template.md
- xcbuild.sh
- enum
- capabilities
- section_features
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
- event_id
- test_source_candidate_paths.py
- 31 August continued qualification findings
- Teacher-feedback follow-up — 27 September 2026
- Selected-response label integrity implementation plan
- _draw_cover
- Examiner-readiness standard
- test_ocr_economics_calibration.py
- test_aqa_accounting_calibration.py
- _scheme_answer
- _normalise_command_word
- _draw_source_content_page

## God Nodes (most connected - your core abstractions)
1. `GeneratedQuestion` - 213 edges
2. `build_paper_blueprint()` - 182 edges
3. `load_syllabus()` - 172 edges
4. `load_builtin_paper_config()` - 166 edges
5. `IndependentSolver` - 152 edges
6. `ApplicationCoordinator` - 144 edges
7. `GeneratedOption` - 125 edges
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

## Communities (274 total, 28 thin omitted)

### Community 0 - "String"
Cohesion: 0.03
Nodes (100): Decodable, Hashable, Identifiable, AIProvider, anthropic, apple, .backendID, .id (+92 more)

### Community 1 - "GeneratedQuestion"
Cohesion: 0.09
Nodes (78): _candidate_question(), _canonical_objective_allocation(), _clean_generated_prompt(), GenerationPolicy, _is_examiner_meta_guidance(), _normalise_calculation_guidance(), _normalise_level_allocations(), _normalise_multiple_choice_answer() (+70 more)

### Community 2 - "paper_fidelity_audit.py"
Cohesion: 0.05
Nodes (103): Pixmap, parametrize, Path, test_compact_profile_omits_raster_geometry(), test_contact_sheets_make_visual_review_artifacts(), test_generated_document_falls_back_to_nested_transaction_output(), test_generated_document_supports_app_per_paper_directories(), test_metric_callout_names_print_resolution_comparison_dimensions() (+95 more)

### Community 3 - "ai_assessment.py"
Cohesion: 0.11
Nodes (40): AssessmentLLMClient, _batches_for_client(), _bounded_text(), _demand_item(), _difficulty_candidate(), _difficulty_specification(), _effective_batch_size(), _generate_batch() (+32 more)

### Community 4 - "load_syllabus"
Cohesion: 0.06
Nodes (91): _build(), build_paper1_blueprint(), build_paper2_blueprint(), build_topic_question_bank(), PaperBlueprint, Syllabus, _clean(), improve_questions_with_ollama() (+83 more)

### Community 5 - "pastpapergen/ollama_client.py"
Cohesion: 0.06
Nodes (76): Reject common exchange-rate reversals before model review., validate_economics_causal_direction(), assert_materially_new(), OllamaClient, Standalone subject generators use the same transport as the app., QuestionBlueprint, SyllabusTopic, build_question_prompt() (+68 more)

### Community 6 - "Text"
Cohesion: 0.04
Nodes (82): CaseIterable, Charts, KeyPath, View, PanelEmptyState, .body, String, value (+74 more)

### Community 7 - "cspapergen/render_pdf.py"
Cohesion: 0.10
Nodes (78): _artifacts(), _answer_line_count(), _answer_lines_paginated(), _candidate_fields(), _cover_page(), _cover_section(), _draw_adjacency_matrix_answers(), _draw_arrow() (+70 more)

### Community 8 - "build_paper_blueprint"
Cohesion: 0.08
Nodes (81): build_paper_blueprint(), PaperBlueprint, Syllabus, load_builtin_paper_config(), review_table_rows(), load_syllabus(), Path, Syllabus (+73 more)

### Community 9 - "test_ocr_economics.py"
Cohesion: 0.08
Nodes (50): Return the immutable rules for one printed option (one-based)., resolve_question_rules(), percentage_change_context(), Candidate chart endpoints and the requested one-decimal percentage output., generate_package(), Path, build_paper(), _evaluation_scheme() (+42 more)

### Community 10 - "psychometrics.py"
Cohesion: 0.08
Nodes (56): CalibrationMetadata, CalibrationStore, ConsentRecord, _normalise_row(), Any, Path, Encrypted local storage for row-level calibration evidence. Keys are…, _read_rows() (+48 more)

### Community 11 - "ocregen/render_pdf.py"
Cohesion: 0.10
Nodes (55): OCRAnswerLines, OCR dotted writing rules inside the existing allocated answer area. Reviewed…, _add_economics_diagram(), _add_firm_objectives_diagram(), _add_ppf_diagram(), _annotation_conventions_page(), _answer_mark(), _assessment_allocation() (+47 more)

### Community 12 - "pastpapergen/generator.py"
Cohesion: 0.06
Nodes (72): MultipleChoiceOption, _adapt_paper_three_case_guidance(), _best_section_a_context_point(), _build_part(), _build_parts(), _choice_group_name(), _choice_lookup(), _choose_topic() (+64 more)

### Community 13 - "live_generation_matrix.py"
Cohesion: 0.06
Nodes (71): Release qualification evidence and policy models., ArtifactEvidence, EvidenceRecord, GateState, ModelIdentity, BaseModel, field_validator, Path (+63 more)

### Community 14 - "require_difficulty_review"
Cohesion: 0.07
Nodes (77): _export_difficulty_candidate_projection(), candidate_review_content(), CandidateContentIdentity, difficulty_candidate_projection(), DifficultyCandidateProjection, edexcel_difficulty_candidate_projection(), ensure_difficulty_candidate_projection(), _mapping() (+69 more)

### Community 15 - "QualityInspector"
Cohesion: 0.07
Nodes (34): App, GenerationQualityState, PaperCreator, GenerationProgress, .accessibilityValue, .body, GenerationQualityState, .color (+26 more)

### Community 16 - "paper1_assets.py"
Cohesion: 0.44
Nodes (12): _supporting(), _page_footer(), _paragraph(), _practice_header(), Canvas, PaperBlueprint, Path, render_electronic_answer_document() (+4 more)

### Community 17 - "add_page_structure_tree"
Cohesion: 0.31
Nodes (9): add_page_structure_tree(), has_logical_page_order(), _has_structure_tree(), _new_object(), Document, Page, Path, Attach a deterministic page-level structure tree and marked content. Each page… (+1 more)

### Community 18 - "ApplicationCoordinator"
Cohesion: 0.04
Nodes (50): AnyCancellable, Commands, DateFormatter, AppCommands, .body, .body, GeneratedFilesTable, .body (+42 more)

### Community 19 - "RecentDocumentStore"
Cohesion: 0.07
Nodes (30): Codable, FileManager, GenerationJobState, ExamCatalog, GenerationConfiguration, GenerationJobRecord, .missingArtifactCount, GenerationJobState (+22 more)

### Community 20 - "open_credit.py"
Cohesion: 0.13
Nodes (30): cpu_credit_allocations(), cpu_credit_contract(), _cpu_quote_supports_criterion(), CreditJudgement, CriterionDecision, _has_unambiguous_instruction_antecedent(), _normalise_cpu_clauses(), _passive_relation_patterns() (+22 more)

### Community 21 - "build_question"
Cohesion: 0.17
Nodes (65): model_validator, Stimulus, ao_for_marks(), _assembly_program_question(), _assembly_trace_question(), _big_data_question(), _big_data_short_question(), _binary_short_question() (+57 more)

### Community 22 - "Paragraph"
Cohesion: 0.12
Nodes (62): AQAAnswerLines, Paragraph, _accounting_marking_guidance_pages(), _accounting_system_case(), _additional_answer_page(), _appropriation_answer_table(), _assessment_objectives_page(), _chrome() (+54 more)

### Community 23 - "AssessmentContract"
Cohesion: 0.08
Nodes (50): AssessmentContract, contract_for_question(), GeneratedNumericField, GraphContract, _numeric_contracts(), NumericRole, NumericValueContract, Any (+42 more)

### Community 24 - "properties"
Cohesion: 0.04
Nodes (60): printed-conflicting, published-item-allocation, reconciled-published-aggregate, unknown, anyOf, default, title, const (+52 more)

### Community 25 - "ocrcsgen/render_pdf.py"
Cohesion: 0.06
Nodes (51): ExamPage, Flowable, A full-page shell that can also live inside a Platypus story., AnswerLineFlowable, AQACompactAnswerLines, OCRComputerScienceAnswerLines, Flowable, Return a Table subclass whose raw string cells use the controlled font.… (+43 more)

### Community 26 - "sql_contracts.py"
Cohesion: 0.11
Nodes (41): _contract_column(), _Count, _equality(), _Field, _finding(), fitness_centre_sql_contract(), _Frozen, _has_sql_statement_shape() (+33 more)

### Community 27 - "_mark_scheme_rows"
Cohesion: 0.15
Nodes (26): _brief_source_evidence(), _calculation_answer_lines(), _mark_point_relevance(), _mark_scheme_rows(), _normalise_mark_point(), _one_mark_points(), _paper_one_fifteen_mark_scheme_lines(), _paper_one_five_mark_diagram_lines() (+18 more)

### Community 28 - "CodingKeys"
Cohesion: 0.04
Nodes (57): CodingKey, CodingKeys, assessmentKind, backendVersion, capabilities, checks, code, command (+49 more)

### Community 29 - "build_item_demand_target"
Cohesion: 0.06
Nodes (67): objective_policy_for(), Subject meaning for AO labels, independent of item tariffs and renderers., Resolve family IDs, subject names or qualification codes., audit_candidate_paths(), CS component policy audit over candidate-answerable paths, not printed totals., assessment_objectives_for_item(), audit_form_demand(), build_item_demand_target() (+59 more)

### Community 30 - "formatted_generation_date"
Cohesion: 0.21
Nodes (20): formatted_generation_date(), formatted_generation_series(), generation_date(), date, Return the month/year form used on mark-scheme covers., _extract_source_questions(), render_source_booklet(), _source_sections() (+12 more)

### Community 31 - "test_aqa_business.py"
Cohesion: 0.06
Nodes (48): generate_package(), Path, FinancialPosition, format_number(), The single source of truth for Paper 1 financial-statement figures., Format an exam answer without meaningless trailing zeroes., build_paper(), _extract() (+40 more)

### Community 32 - "test_shared_numeric_integrity.py"
Cohesion: 0.14
Nodes (34): accounting_tasks(), GivenRateClient, parametrize, test_abc_checks_every_asserted_intermediate_without_rounding_into_final(), test_all_p2_closed_calculations_are_source_derived_and_exhaustively_reconciled(), test_chart_percentage_shared_families_have_independent_typed_contracts(), test_checkpoint_resume_rejects_changed_preserved_numeric_prompt(), test_conditional_follow_through_is_not_an_unconditional_numeric_alternative() (+26 more)

### Community 33 - "CanonicalSolution"
Cohesion: 0.16
Nodes (22): _bounded(), GenerationEvidenceError, Any, Path, ValueError, Private, bounded evidence for rejected generation; never approved checkpoints., Save only explicitly supplied evidence, not arbitrary errors or prompts.…, save_failure_diagnostic() (+14 more)

### Community 34 - "aqabizgen/render_pdf.py"
Cohesion: 0.12
Nodes (46): aqa_front_matter_pages(), Flowable, SelectedResponseContract, _artifacts(), _additional_answer_page(), _ao_summary(), _assessment_objectives_page(), _break_even_diagram() (+38 more)

### Community 35 - "AssessmentCheckpointStore"
Cohesion: 0.12
Nodes (33): AssessmentCheckpointStore, CheckpointCorrupt, CheckpointIdentity, CheckpointMismatch, identity_for_blueprint(), Any, BaseModel, Path (+25 more)

### Community 36 - "solve_selected_response"
Cohesion: 0.09
Nodes (46): _better_than_target(), _decimal(), _display_decimal(), _money_choice(), _numeric_choice(), _percent_choice(), _plain_decimal(), Any (+38 more)

### Community 37 - "test_render_pdf.py"
Cohesion: 0.12
Nodes (51): _apply_edexcel_page_boxes(), Path, Match Pearson question-paper bleed and crop boxes without changing A4 content., render_question_paper(), _answer_rule_count(), _blank_axis_lines(), _blueprint_with_section_a_question(), _dark_pixels() (+43 more)

### Community 38 - "test_source_credit_integrity.py"
Cohesion: 0.08
Nodes (44): calculation(), calculation_label(), calculation_prompt(), calculation_working(), EconomicsSource, BaseModel, Decimal, model_validator (+36 more)

### Community 39 - ".generate"
Cohesion: 0.06
Nodes (24): AppDefaults, AppLinks, AppStorageKey, SecretAccount, Bool, String, URL, MLXRecoveryState (+16 more)

### Community 40 - "required"
Cohesion: 0.11
Nodes (25): assessment_objectives, cognitive_operation, command_word, demand_band, demand_basis, historical_engineering_demand_proxy, item_ids, learner_demand (+17 more)

### Community 41 - "assessment_package.py"
Cohesion: 0.13
Nodes (38): _assessment_contract(), AssessmentPackageCompatibilityError, _authoring_provenance(), _contains_non_finite(), _evidence_ids(), _extract_items(), _form_id(), _level_policies() (+30 more)

### Community 42 - ".load"
Cohesion: 0.12
Nodes (16): LocalizedError, CatalogLoader, CatalogLoadError, duplicateBoard, duplicateImplementation, emptyImplementation, .errorDescription, implementationMissingFromCatalog (+8 more)

### Community 43 - "properties"
Cohesion: 0.05
Nodes (43): 1, 2, 4.10, 4.12, 4.2, context-incomplete, core, mixed (+35 more)

### Community 44 - "test_open_credit_reconciliation.py"
Cohesion: 0.14
Nodes (40): alternative_permission(), Any, Only known host-authored permissions can bypass answer-value checking., credit_identity(), credit_item_projection(), review_open_credit(), validate_open_credit_review(), adjudication_response() (+32 more)

### Community 45 - "IndependentSolver"
Cohesion: 0.19
Nodes (29): IndependentSolver, Solve an item in a context that deliberately excludes its draft scheme., NoModelArithmetic, parametrize, test_closed_accounting_solutions_ignore_the_draft_answer_key(), closed_item(), parametrize, ResponseClient (+21 more)

### Community 46 - "providers.py"
Cohesion: 0.08
Nodes (43): _hosted_client(), _aqa_cs_part_count(), _edexcel_part_count(), hosted_client(), HostedLLMClient, _normalise_base_url(), _ollama_json_schema(), _ollama_output_budget() (+35 more)

### Community 47 - "reference_corpus.py"
Cohesion: 0.13
Nodes (45): MonkeyPatch, Path, test_document_path_requires_filename(), test_document_path_stays_inside_corpus(), test_download_manifest_records_failure_and_continues(), test_parse_aqa_resources_filters_modified_papers(), test_parse_ocr_resources_uses_a_level_tab_only(), test_parse_ocr_specifications_keeps_a_level_not_as_level() (+37 more)

### Community 48 - "cspapergen/ollama_client.py"
Cohesion: 0.07
Nodes (74): aqa_cs_difficulty_candidate(), aqa_cs_solver_item(), authoring_route(), Any, question_content_sha256(), AQA CS source-coupled review identity, shared by authoring/resume/export. This…, Bind one AQA part review to the complete evidence-free parent question., One adapter/reuse projection; caller supplies candidate-visible figure data.… (+66 more)

### Community 49 - "test_mlx_setup.py"
Cohesion: 0.08
Nodes (45): _available_cache_bytes(), ensure_mlx_ready(), handle_mlx_status(), handle_setup_mlx(), install_mlx_runtime(), is_managed_development_environment(), load_mlx_model(), mlx_runtime_available() (+37 more)

### Community 50 - "test_computer_science_objectives.py"
Cohesion: 0.07
Nodes (60): generate_package(), Path, load_rule(), build_paper(), Syllabus, _flatten(), Path, Generic examiner rules belong in front matter, not every table row. (+52 more)

### Community 51 - "aqaecongen/render_pdf.py"
Cohesion: 0.14
Nodes (39): _artifacts(), _assessment_objectives_table(), _context_data_table(), _context_first_page(), _context_second_page(), _cover_profile(), _document(), _economic_diagram() (+31 more)

### Community 52 - "CodingKeys"
Cohesion: 0.07
Nodes (36): CodingKeys, appContextWindow, contextWindow, defaultModel, detail, downloadSizeGB, id, maximumMemoryGB (+28 more)

### Community 53 - "independent_solver.py"
Cohesion: 0.10
Nodes (32): collect_credit_rules(), credit_rule(), CreditRule, declared_rule_metadata_present(), BaseModel, Origin-preserving open credit rules; never promote model advice to authority., Preserve numerical caps/dependencies, not just their descriptive prose.…, _as_mapping() (+24 more)

### Community 54 - "reference_demand_profiles.py"
Cohesion: 0.12
Nodes (34): Pattern, build_document(), CorpusFamily, _distribution(), extract_reference_features(), extract_reference_items(), _fingerprint(), _item_demand() (+26 more)

### Community 55 - "test_aqa_economics.py"
Cohesion: 0.08
Nodes (37): generate_package(), main(), Path, build_paper(), Syllabus, _section_instructions(), Independent AQA 7136-aligned A-level Economics practice-paper generator., load_syllabus() (+29 more)

### Community 56 - "type"
Cohesion: 0.06
Nodes (40): type, additionalProperties, $ref, title, type, additionalProperties, title, type (+32 more)

### Community 57 - "draw_barcode"
Cohesion: 0.25
Nodes (16): CanvasBarcodeStyle, draw_barcode(), draw_glyph_answer_rules(), draw_solid_answer_rules(), GlyphRuleStyle, Canvas, Draw a fixed number of solid response rules and return the next baseline., Draw selectable glyph-based response rules and return the next baseline. (+8 more)

### Community 58 - "properties"
Cohesion: 0.04
Nodes (52): anyOf, title, minLength, title, type, SourcePath, const, title (+44 more)

### Community 59 - "generator/tests/test_assessment_contracts.py"
Cohesion: 0.12
Nodes (37): _question_solver_item(), paper(), parametrize, test_actual_level_tariffs_have_distinct_usable_band_descriptors(), test_all_seeded_styles_have_contract_credit_not_topic_note_filler(), test_business_expansion_short_credit_marks_one_complete_route(), test_complete_declared_numeric_operations_have_literal_answers(), test_content_driven_scheme_policy_rejects_missing_printed_assessment() (+29 more)

### Community 60 - "PaperCreatorTests"
Cohesion: 0.04
Nodes (51): Equatable, AuthoringProvenanceKind, aiAuthoredOnly, mixed, reviewedFixedOnly, unknown, unreviewed, AuthoringProvenanceSummary (+43 more)

### Community 61 - "PaperBlueprint"
Cohesion: 0.23
Nodes (19): _count_pages(), _draw_answer_lines_until(), _draw_answer_page_header(), _draw_continuation_lines(), _draw_paper_3_pages(), _draw_question_footer(), _draw_question_pages(), _draw_section_b_source_pages() (+11 more)

### Community 62 - "DocumentPreviewView"
Cohesion: 0.04
Nodes (52): AppKit, Combine, DocumentPreviewView, .body, .exportAlertBinding, .provenanceRecord, .selectedBinding, .selectedFile (+44 more)

### Community 63 - "pdf_validation.py"
Cohesion: 0.15
Nodes (26): compare_page_evidence(), _contrast_against_white(), _contrast_ratio(), _count_score(), GlyphMetric, _is_decorative_bleed(), _is_margin_furniture(), _leading() (+18 more)

### Community 64 - "ObjectivePolicy"
Cohesion: 0.22
Nodes (4): ObjectivePolicy, Any, Reject unsupported labels in new or persisted qualified contracts., CS tasks are not classified from their tariff or AO3 label alone.

### Community 65 - "properties"
Cohesion: 0.06
Nodes (36): aqa-topic-operation-records-v3, edition-leaf-path-features-v2, full-paper, question-bank, unqualified-reference-v1, enum, minLength, type (+28 more)

### Community 66 - "NumericOutput"
Cohesion: 0.14
Nodes (34): BaseModel, ReconciliationResult, check_numeric_alternatives(), check_published_outputs(), CheckedNumericOutput, CheckedTextOutput, display(), _equivalent_quantity() (+26 more)

### Community 67 - ".baseQuery"
Cohesion: 0.39
Nodes (4): SecretStore, Any, String, Security

### Community 68 - "benchmark.py"
Cohesion: 0.12
Nodes (33): apple_cpu_core_split(), available_memory_gb(), avg(), clamp(), cpu_brand(), cpu_load_percent(), cpu_probe(), disk_probe() (+25 more)

### Community 69 - "pastpapergen/models.py"
Cohesion: 0.12
Nodes (21): validate_assessment_contract(), CandidateSectionRule, ChoiceSelection, MultipleChoiceOption, PaperBlueprint, PaperConfig, BaseModel, QuestionPart (+13 more)

### Community 70 - "aqa_section_intro"
Cohesion: 0.10
Nodes (25): aqa_lozenge(), aqa_section_intro(), AQAQuestionHeaderFactory, flowable_question_block(), independent_practice_page(), OCRQuestionHeaderFactory, page_sequence(), Color (+17 more)

### Community 71 - "Rect"
Cohesion: 0.17
Nodes (16): _clamp_fitz_rect(), conform_pdf_page_boxes(), _fitz_rect_close(), load_layout_master(), _page_from_payload(), _page_matches_box_set(), PageMaster, PaperMaster (+8 more)

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
Cohesion: 0.06
Nodes (88): AnswerSpace, BaseComponent, BlankPage, Component, ContinuationPage, Cover, Diagram, Graph (+80 more)

### Community 78 - "test_mark_scheme_layout.py"
Cohesion: 0.15
Nodes (36): pdf_font_names(), Path, Return the font families actually used by visible text spans., _cleanup_graph_cache(), Render each contract criterion as a discrete, visible examiner point., render_mark_scheme(), _source_backed_mark_scheme_lines(), _assert_complete_contract_scheme() (+28 more)

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
Nodes (28): module(), profile_payload(), parametrize, Path, test_calculation_reasoning_ceiling_scales_with_tariff(), test_committed_profiles_cover_every_advertised_assessment_without_source_text(), test_committed_profiles_include_unadvertised_aqa_mathematics_evidence(), test_empty_context_does_not_create_an_application_requirement() (+20 more)

### Community 83 - "graphs.py"
Cohesion: 0.30
Nodes (26): Axes, ad_as_diagram(), _arrow_axes(), _ax(), circular_flow_diagram(), consumer_producer_surplus(), demand_supply_diagram(), _ensure_style() (+18 more)

### Community 84 - "reference_evidence.py"
Cohesion: 0.08
Nodes (40): CandidatePath, CandidateTopology, enumerate_candidate_paths(), identity(), path_metrics(), PathOption, PathSection, Any (+32 more)

### Community 85 - "AQA Computer Science bank-item reference support"
Cohesion: 0.13
Nodes (12): OCR question-paper ruling and final-page correction, Live matrix integrity, Qualification boundary, Reference support, live qualification and PDF repairs, Renderer repairs, Verification record, Admission rule, AQA Computer Science bank-item reference support (+4 more)

### Community 86 - "test_solver_source_adapter.py"
Cohesion: 0.15
Nodes (30): candidate_content_identity(), _assert_public_stimulus(), _difficulty_candidate(), EvidenceRecord, PaperBlueprint, QuestionPart, Syllabus, _question_solver_projection() (+22 more)

### Community 87 - "exam_blueprints.py"
Cohesion: 0.22
Nodes (22): _demand_band(), _hydrate_assessment_metadata(), _objective_allocation(), _prompt_uses_command_word(), _structured_scheme(), validate_generated_paper(), validate_rule(), test_all_paper_rules_have_exact_candidate_marks_and_syllabus_scope() (+14 more)

### Community 88 - ".body"
Cohesion: 0.08
Nodes (18): CGFloat, Bool, WorkspaceLayoutMode, compact, expanded, .showsInspector, .showsSidebar, standard (+10 more)

### Community 89 - "test_coverage_matrix.py"
Cohesion: 0.20
Nodes (24): family(), matrix(), Path, test_catalog_availability_is_owned_only_by_registry(), test_checked_in_matrix_is_deterministic_and_current(), test_existing_generators_are_reported_without_false_verification(), test_matrix_exactly_covers_layout_profiles(), test_no_verified_paper_has_a_failed_gate() (+16 more)

### Community 90 - "conform_generated_documents"
Cohesion: 0.17
Nodes (21): _aqa_cs_printed_credit(), conform_generated_documents(), _edexcel_printed_credit(), Path, Generated-content policy is not an observed reference-count range., Content-driven pagination must preserve every published marking statement., runtime_page_count_policy(), conform_pdf_to_box_template() (+13 more)

### Community 91 - "Question"
Cohesion: 0.09
Nodes (48): Render only public schema facts; no worked query is present., render_sql_schema(), SQLSampleTableContract, SQLSourceContract, derive_task_semantics(), Any, BaseModel, Strict, deterministic task contracts for AQA CS topic-reference evidence. (+40 more)

### Community 92 - "reference-demand-profile.schema.json"
Cohesion: 0.08
Nodes (25): derived_aggregate_only, profiles, purpose, retains_source_text, additionalProperties, const, $id, additionalProperties (+17 more)

### Community 94 - "properties"
Cohesion: 0.08
Nodes (25): type, pattern, type, pattern, pattern, type, type, pattern (+17 more)

### Community 95 - "generator_registry.py"
Cohesion: 0.24
Nodes (15): _capability(), generator_capabilities(), generator_subjects(), _paper_qualification(), PaperQualification, Any, _relative_path(), test_backend_bundle_script_is_registry_driven() (+7 more)

### Community 96 - "generation.py"
Cohesion: 0.21
Nodes (21): progress_emitter(), _atomic_publish(), _cancel_generation(), checkpoint_path_for_job(), emit_generated_files(), finalize_generated_documents(), GenerationCancelled, _generator_version() (+13 more)

### Community 98 - "_normalise_font"
Cohesion: 0.33
Nodes (7): _font_embedding(), _font_evidence(), _normalise_font(), Document, parametrize, test_metric_compatible_open_fonts_share_reference_family_identity(), test_open_sans_weights_and_static_instance_share_family_identity()

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
Nodes (25): type, type, type, null, string, type, maximum, minimum (+17 more)

### Community 103 - "mark_scheme_enrichment.py"
Cohesion: 0.22
Nodes (22): _answer_form(), _application_label(), _clean_text(), _compact_technical_guidance(), _deduplicate(), enrich_paper(), _enrich_question(), _level_guidance() (+14 more)

### Community 104 - "test_pdf_validation.py"
Cohesion: 0.17
Nodes (28): extract_pdf_evidence(), _layout_profiles(), _overlapping_text_pairs(), Counter, Path, Fail closed on malformed, substituted, annotated, or low-resolution PDFs., Extract print and accessibility evidence without retaining source prose. Glyph…, _text_occupancy() (+20 more)

### Community 105 - ".initialEstimate"
Cohesion: 0.19
Nodes (11): EstimateFactor, GenerationEstimate, .etaDate, .remainingText, TimeInterval, GenerationEstimator, Bool, Date (+3 more)

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
Cohesion: 0.10
Nodes (21): items, items, minItems, $ref, title, type, items, maxItems (+13 more)

### Community 110 - "required"
Cohesion: 0.10
Nodes (22): differential_item_functioning, discrimination, facility, item_id, median_time_seconds, responses, minimum, type (+14 more)

### Community 111 - "pastpapergen/cli.py"
Cohesion: 0.11
Nodes (31): ArtifactSpec, BuildResult, FamilyAdapter, Path, run_family_adapter(), default_ollama_model(), model_recommendations(), OllamaModelRecommendations (+23 more)

### Community 112 - "accounting.py"
Cohesion: 0.28
Nodes (22): _accounting_endings(), accounting_outputs(), _appropriation(), _assets(), derive_accounting_open_response_context(), _exact(), _income(), _ledger() (+14 more)

### Community 113 - "reconcile_solution"
Cohesion: 0.11
Nodes (39): reconcile_solution(), parametrize, solve(), test_assembly_trace_checks_every_register_series_and_stored_value(), test_finite_outputs_are_keyed_and_reject_a_changed_value(), test_full_truth_table_requires_every_input_combination(), test_functional_list_trace_is_derived_without_model_arithmetic(), test_graph_matrix_vectors_accept_clear_space_separated_cells_only() (+31 more)

### Community 114 - "pastpapergen/notes.py"
Cohesion: 0.20
Nodes (19): _clean_chunk(), essay_capable_topic_ids(), _flush_note_chunk(), _is_exam_point(), _is_note_noise(), _looks_like_heading(), _note_chunks(), note_context_for_topic() (+11 more)

### Community 115 - "properties"
Cohesion: 0.10
Nodes (21): minLength, type, minLength, type, minLength, type, format, type (+13 more)

### Community 116 - "aqa_accounting_calibration.py"
Cohesion: 0.34
Nodes (14): _band(), build_generated_profile(), build_reference_profile(), build_report(), _command(), _fingerprint(), _inventory(), main() (+6 more)

### Community 117 - "BackendClient"
Cohesion: 0.16
Nodes (14): BackendClient, BackendClientError, backendMissing, .errorDescription, pythonMissing, pythonVenvUnreadable, BackendFile, LaunchConfiguration (+6 more)

### Community 118 - "required"
Cohesion: 0.12
Nodes (20): comparable_metrics, extraction_policy, feature_basis, non_comparable_features, objective_basis, paths, printed_marks, source_sha256 (+12 more)

### Community 119 - "GeneratedPaper"
Cohesion: 0.08
Nodes (59): AppliedMCQSource, GeneratedPaper, GeneratedSection, PaperRule, BaseModel, model_validator, QuestionRule, SectionRule (+51 more)

### Community 120 - "validate_generator_migration.py"
Cohesion: 0.24
Nodes (10): build_parser(), _layout_board(), main(), MigrationIssue, MigrationReport, MigrationValidator, Any, ArgumentParser (+2 more)

### Community 121 - "validate_mark_scheme_item"
Cohesion: 0.25
Nodes (17): _contains_any(), MarkSchemeQuality, _normalise(), Any, validate_mark_scheme_item(), _item(), test_accounting_follow_through_metadata_counts_as_method_guidance(), test_calculation_requires_method_or_working() (+9 more)

### Community 122 - "subject_plugins.py"
Cohesion: 0.18
Nodes (19): board_profile(), board_profile_ids(), BoardProfile, _normalise_identifier(), discover_subject_plugin(), _normalise_identifier(), register_subject_plugin(), subject_plugin_ids() (+11 more)

### Community 123 - "test_generator_migration.py"
Cohesion: 0.23
Nodes (13): Path, test_all_current_families_pass_declarative_migration_validation(), test_broken_fixture_reports_every_onboarding_surface(), test_scaffold_emits_complete_unadvertised_family_and_refuses_overwrite(), build_parser(), _cli_template(), main(), ArgumentParser (+5 more)

### Community 124 - "CandidateResponse"
Cohesion: 0.12
Nodes (24): BoardLevelPolicy, LevelDescriptor, LevelOfResponseEngine, load_level_policies(), MarkAnnotation, MarkDecision, BaseModel, model_validator (+16 more)

### Community 125 - "cspapergen/notes.py"
Cohesion: 0.38
Nodes (9): cache_notes(), discover_note_pdfs(), _extract_text(), note_context_for_topic(), NotesManifest, Path, _topic_prefixes(), test_cache_notes_extracts_text_into_project_cache() (+1 more)

### Community 126 - "test_computer_science_subject.py"
Cohesion: 0.21
Nodes (12): ComputerSciencePlugin, _evaluate_boolean(), normalise_pseudocode(), pseudocode_equivalent(), Any, truth_table(), test_four_mark_boolean_tasks_have_equivalent_explicit_working(), test_computer_science_uses_the_specialised_plugin() (+4 more)

### Community 127 - "EvidenceRecord"
Cohesion: 0.25
Nodes (20): _tasks(), EvidenceRecord, CapturedSolverPrompt, CaptureSolverClient, model_sources(), Exception, parametrize, solver_payload() (+12 more)

### Community 128 - "PathSection"
Cohesion: 0.09
Nodes (22): answer_options, candidate_marks, options, exclusiveMinimum, title, type, exclusiveMinimum, title (+14 more)

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

### Community 134 - "test_layout_master.py"
Cohesion: 0.15
Nodes (15): draw_text_slot(), PageCountPolicy, Draw in a PyMuPDF-style top-origin slot on a ReportLab canvas. Returns the font…, TextSlot, parametrize, Path, _sample_pdf(), test_box_conformance_is_no_op_when_boxes_already_match() (+7 more)

### Community 135 - "enum"
Cohesion: 0.12
Nodes (16): algorithm-trace, calculation, computational-analysis, computational-design, constructed-response, extended-evaluation, mathematical-argument, multi-stage-calculation (+8 more)

### Community 136 - "IncomeStatementCase"
Cohesion: 0.17
Nodes (4): IncomeStatementCase, Decimal, Complete, internally consistent source for the Paper 1 company statement., _round_pounds()

### Community 137 - "ModelCoordinator"
Cohesion: 0.05
Nodes (35): Foundation, OllamaState, EstimateTuning, AppClock, KeychainSecretStore, SecretStoring, Date, String (+27 more)

### Community 138 - "properties"
Cohesion: 0.12
Nodes (16): minLength, type, minLength, type, minLength, type, blueprint, contract (+8 more)

### Community 139 - "configuredgen/generator.py"
Cohesion: 0.15
Nodes (26): generate_package(), Path, _answer_form(), build_paper(), _mathematics_question(), _prompt(), Random, Topic (+18 more)

### Community 140 - "test_topic_reference_evidence.py"
Cohesion: 0.19
Nodes (23): bank_items(), module(), parametrize, A serialised hint must never override the question that will be printed., Only the versioned contract may establish a reference comparison., test_actual_same_topic_operation_and_mode_still_matches(), test_bank_support_rejects_changed_work_not_just_matching_topic_words(), test_forged_or_sparse_source_inventory_cannot_qualify_bank() (+15 more)

### Community 141 - "SubjectPlugin"
Cohesion: 0.39
Nodes (3): Any, Protocol, SubjectPlugin

### Community 142 - "build_layout_masters.py"
Cohesion: 0.26
Nodes (19): _box(), _colour(), _content_box(), _drawing_kind(), _drawings(), extract_layout_master(), _furniture_signature(), _images() (+11 more)

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
Cohesion: 0.34
Nodes (14): _band(), build_generated_profile(), build_reference_profile(), build_report(), _command(), _fingerprint(), _inventory(), main() (+6 more)

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
Cohesion: 0.07
Nodes (27): duration_minutes, sections, total_marks, additionalProperties, properties, required, title, type (+19 more)

### Community 166 - "difficulty_calibration.py"
Cohesion: 0.23
Nodes (16): report(), test_calibration_retains_no_official_text_or_paths(), test_difficulty_is_not_promoted_without_human_and_psychometric_evidence(), test_every_paper_has_multi_seed_structural_evidence(), build_generated_profile(), build_reference_profile(), build_report(), _command() (+8 more)

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

### Community 181 - "test_aqa_business_calibration.py"
Cohesion: 0.53
Nodes (4): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence()

### Community 182 - "profile_for"
Cohesion: 0.27
Nodes (17): profile_for(), items(), paths_module(), parametrize, test_complete_pairs_produce_six_eighty_mark_paths_not_cross_pairs(), test_correlated_source_vectors_cannot_pass_by_coordinatewise_bounds(), test_edexcel_leaf_only_marks_and_choice_groups(), test_explicit_selected_operation_is_not_relabelled_retrieval_in_audit() (+9 more)

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

### Community 193 - "paper1_reference_code"
Cohesion: 0.33
Nodes (9): paper1_reference_code(), Shared reference snippets used by the renderer and publication integrity gate., parametrize, test_add_example_constructs_the_scenario_record_type(), test_adjustment_example_implements_the_actual_function_contract(), test_reference_functions_integrate_with_the_generated_skeleton(), test_report_example_is_one_pass_and_preserves_empty_categories_and_ties(), test_timing_example_uses_supplied_functions_and_fresh_equal_trials() (+1 more)

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

### Community 206 - "test_humanities_overlay.py"
Cohesion: 0.55
Nodes (9): map_diagram(), MapFeature, MapSpec, Drawing, timeline_diagram(), TimelineEvent, TimelineSpec, test_humanities_diagrams_reject_misleading_or_invalid_inputs() (+1 more)

### Community 207 - "model"
Cohesion: 0.29
Nodes (7): digest, name, provider, additionalProperties, required, type, model

### Community 208 - "enum"
Cohesion: 0.29
Nodes (7): high, low, standard, enum, title, type, historical_engineering_demand_proxy

### Community 209 - "pastpapergen/render_pdf.py"
Cohesion: 0.08
Nodes (73): BoardLayout, GraphParams, _answer_line_count(), _axis_labels_for_draw_prompt(), _bar_label(), _draw_answer_lines(), _draw_axis_arrow(), _draw_bar_chart() (+65 more)

### Community 211 - "CoverProfile"
Cohesion: 0.07
Nodes (43): aqa_question_cover(), CoverProfile, _draw_aqa_mark_scheme_cover(), _draw_cover_barcode(), draw_mark_scheme_cover(), _draw_ocr_mark_scheme_cover(), mark_scheme_cover(), MarkSchemeCover (+35 more)

### Community 212 - "ocrcsgen/generator.py"
Cohesion: 0.17
Nodes (18): _analysis_prompt(), _levels(), _programming_prompt(), _programming_scheme(), Random, Topic, _question(), _representation_calculation() (+10 more)

### Community 213 - "qualification-schema.json"
Cohesion: 0.33
Nodes (5): additionalProperties, $id, $schema, title, type

### Community 214 - "_written"
Cohesion: 0.32
Nodes (8): _nearest_hundred(), _levels(), Topic, _written(), test_company_and_partnership_schemes_expose_complete_working_data(), test_locked_calculation_schemes_are_exactly_derived_from_the_case_data(), test_locked_calculation_schemes_include_final_answers_and_all_case_numbers(), test_seeded_partnership_allocations_balance_without_rounding_losses()

### Community 215 - "test_ocr_computer_science_calibration.py"
Cohesion: 0.53
Nodes (4): report(), test_difficulty_remains_external_evidence_gated(), test_multi_seed_structural_demand_passes(), test_reference_evidence_is_aggregate_only()

### Community 216 - "generate_package"
Cohesion: 0.29
Nodes (12): generate_package(), Path, page_count(), Path, test_both_packages_render_36_page_question_papers(), test_invalid_paper_is_rejected(), test_paper_one_mark_scheme_matches_reference_question_sequence(), test_paper_one_section_a_matches_measured_case_and_account_pages() (+4 more)

### Community 217 - "cspapergen/cli.py"
Cohesion: 0.09
Nodes (35): extract_pdf_text(), Extract stable reading-order text without a Poppler CLI dependency., default_output_dir(), generate_package(), _improve(), main(), Path, _logic_gate_names() (+27 more)

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

### Community 225 - "section_features"
Cohesion: 0.40
Nodes (5): $ref, section_features, additionalProperties, title, type

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

### Community 262 - "event_id"
Cohesion: 0.67
Nodes (3): minimum, type, event_id

### Community 264 - "test_source_candidate_paths.py"
Cohesion: 0.23
Nodes (13): _fixture_pdf(), module(), fixture, Original synthetic text, with the audited editions' page/mark structure., source_corpus(), test_aqa_selected_source_operations_do_not_manufacture_objective_tags(), test_business_edition_does_not_assume_same_question_numbers(), test_clean_ocr_mcq_rows_keep_published_ao_and_non_retrieval_operations() (+5 more)

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
Cohesion: 0.18
Nodes (16): economics_exam_schedule(), ExamSchedule, formatted_economics_exam_date(), date, _draw_boxes(), _draw_cover(), _draw_crop_marks(), _draw_front_section() (+8 more)

### Community 271 - "Examiner-readiness standard"
Cohesion: 0.50
Nodes (3): Current findings and delivery order, Examiner-readiness standard, Release criteria for every advertised route

### Community 274 - "test_ocr_economics_calibration.py"
Cohesion: 0.53
Nodes (4): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence()

### Community 276 - "test_aqa_accounting_calibration.py"
Cohesion: 0.53
Nodes (4): report(), test_both_papers_pass_multi_seed_automated_checks(), test_external_difficulty_gates_remain_false(), test_reference_evidence_is_aggregate_only()

### Community 277 - "_scheme_answer"
Cohesion: 0.40
Nodes (5): _credited_scheme_points(), _observable_credit_points(), Keep credit-bearing content in the answer column, once and in full., Keep a closed answer exhaustive while excluding examiner-only notes., _scheme_answer()

### Community 278 - "_normalise_command_word"
Cohesion: 0.50
Nodes (4): _contains_command_word(), _normalise_command_word(), Replace only a leading alternative exam command with the blueprint command., test_equivalent_leading_command_is_normalised_to_blueprint_word()

### Community 279 - "_draw_source_content_page"
Cohesion: 0.67
Nodes (4): _draw_source_content_page(), Syllabus, _source_reading_prompt(), _source_title()

## Knowledge Gaps
- **1140 isolated node(s):** `BoardLayout`, `examforge-aqa-accounting`, `$schema`, `$id`, `title` (+1135 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `IndependentSolver` connect `IndependentSolver` to `GeneratedQuestion`, `ai_assessment.py`, `load_syllabus`, `pastpapergen/ollama_client.py`, `test_aqa_business.py`, `test_shared_numeric_integrity.py`, `CanonicalSolution`, `AssessmentCheckpointStore`, `solve_selected_response`, `test_source_credit_integrity.py`, `test_open_credit_reconciliation.py`, `cspapergen/ollama_client.py`, `test_computer_science_objectives.py`, `independent_solver.py`, `test_aqa_economics.py`, `generator/tests/test_assessment_contracts.py`, `NumericOutput`, `test_aqa_accounting.py`, `test_solver_source_adapter.py`, `Question`, `reconcile_solution`, `EvidenceRecord`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `GeneratedQuestion` connect `GeneratedQuestion` to `ai_assessment.py`, `test_ocr_economics.py`, `configuredgen/generator.py`, `ocregen/render_pdf.py`, `_scheme_answer`, `Paragraph`, `AssessmentContract`, `ocrcsgen/render_pdf.py`, `test_aqa_business.py`, `aqabizgen/render_pdf.py`, `AssessmentCheckpointStore`, `solve_selected_response`, `assessment_package.py`, `aqaecongen/render_pdf.py`, `profile_for`, `test_aqa_economics.py`, `test_reference_demand.py`, `ocrcsgen/generator.py`, `_written`, `exam_blueprints.py`, `mark_scheme_enrichment.py`, `GeneratedPaper`, `EvidenceRecord`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Why does `_extract_items()` connect `assessment_package.py` to `load_syllabus`, `pastpapergen/ollama_client.py`, `test_source_credit_integrity.py`, `test_layout_master.py`, `solve_selected_response`, `generator/tests/test_assessment_contracts.py`, `test_topic_reference_evidence.py`, `require_difficulty_review`, `cspapergen/ollama_client.py`, `test_computer_science_objectives.py`, `test_reference_demand.py`, `test_solver_source_adapter.py`, `test_aqa_economics.py`, `profile_for`, `conform_generated_documents`, `Question`, `build_item_demand_target`, `test_aqa_business.py`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Are the 25 inferred relationships involving `GeneratedQuestion` (e.g. with `AssessmentLLMClient` and `GenerationPolicy`) actually correct?**
  _`GeneratedQuestion` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `IndependentSolver` (e.g. with `AssessmentLLMClient` and `GenerationPolicy`) actually correct?**
  _`IndependentSolver` has 26 INFERRED edges - model-reasoned connections that need verification._
- **What connects `BoardLayout`, `examforge-aqa-accounting`, `$schema` to the rest of the system?**
  _1140 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `String` be split into smaller, more focused modules?**
  _Cohesion score 0.03173354314188303 - nodes in this community are weakly interconnected._