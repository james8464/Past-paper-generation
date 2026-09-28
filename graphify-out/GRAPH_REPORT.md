# Graph Report - .  (2026-09-30)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 6719 nodes · 19556 edges · 242 communities (214 shown, 28 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 1193 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7e37b622`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- document_dsl/__init__.py
- GeneratedQuestion
- GeneratedPaper
- load_syllabus
- String
- paper_fidelity_audit.py
- cspapergen/render_pdf.py
- build_paper_blueprint
- live_generation_matrix.py
- require_difficulty_review
- Text
- ApplicationCoordinator
- GeneratedFile
- AssessmentContract
- test_ollama_generation.py
- psychometrics.py
- pastpapergen/generator.py
- RecentDocumentStore
- CoverProfile
- test_computer_science_objectives.py
- Paragraph
- AIProvider
- test_aqa_business.py
- WorkspaceLayoutMode
- ocregen/render_pdf.py
- properties
- build_question
- test_sql_answer_verification.py
- ExamBoardOption
- test_source_credit_integrity.py
- test_render_pdf.py
- cspapergen/ollama_client.py
- test_ocr_economics.py
- providers.py
- sql_contracts.py
- reconcile_solution
- test_aqa_economics.py
- solve_selected_response
- pastpapergen/cli.py
- ocrcsgen/render_pdf.py
- properties
- reference_corpus.py
- DocumentPreviewView
- test_mlx_setup.py
- Question
- PaperCreatorTests
- CodingKeys
- aqabizgen/render_pdf.py
- type
- AssessmentCheckpointStore
- test_open_credit_reconciliation.py
- family_adapter.py
- assessment_package.py
- reference_evidence.py
- Canvas
- aqaecongen/render_pdf.py
- generator/tests/test_assessment_contracts.py
- NumericOutput
- pastpapergen/render_pdf.py
- required
- properties
- test_shared_numeric_integrity.py
- reference_demand_profiles.py
- independent_solver.py
- pdf_validation.py
- pastpapergen/ollama_client.py
- runtime.py
- test_layout_master.py
- benchmark.py
- aqa_section_intro
- ExamPageProfile
- open_credit.py
- build_item_demand_target
- properties
- test_mark_scheme_layout.py
- IndependentSolver
- test_aqa_accounting.py
- _mark_scheme_rows
- NSIExercise
- layout_master.py
- test_pdf_validation.py
- QualityInspector
- test_reference_evidence_validation.py
- render_pdf_atomically
- SubjectValidation
- mathematics.py
- properties
- test_reference_demand.py
- CanonicalSolution
- test_app_backend.py
- graphs.py
- test_science_subjects.py
- generate_package
- properties
- test_coverage_matrix.py
- ReferenceIndex
- mark_scheme_enrichment.py
- BackendClient
- reference-demand-profile.schema.json
- test_accounting_objectives.py
- render_source_booklet
- $defs
- generation.py
- Foundation
- properties
- discover_subject_plugin
- emit
- accounting.py
- .initialEstimate
- required
- ShareholderCase
- test_topic_reference_evidence.py
- corpus.py
- PathSection
- ocrcsgen/generator.py
- properties
- required
- pastpapergen/notes.py
- properties
- ocr_computer_science_calibration.py
- profile_for
- reportlab_theme.py
- properties
- validate_generator_migration.py
- provider.py
- generator_registry.py
- CandidateResponse
- validate_mark_scheme_item
- test_computer_science_subject.py
- build_layout_masters.py
- test_science_overlay.py
- required
- generate_package
- points
- CodingKeys
- _draw_section_a_question
- properties
- inspect_release_compliance
- OllamaModelGuideDocument
- enum
- IncomeStatementCase
- string
- properties
- paths
- test_generator_migration.py
- audit_candidate_paths
- required
- SalesLedgerCase
- NonCurrentAssetCase
- additionalProperties
- id
- aqa_accounting_calibration.py
- aqa_business_calibration.py
- ocr_economics_calibration.py
- enum
- qualification_levels
- _written
- PartnershipCase
- BiologyPlugin
- test_source_candidate_paths.py
- required
- backend-protocol.schema.json
- test_repository_hygiene.py
- difficulty_calibration.py
- test_french_framework.py
- topic_reference_evidence.py
- required
- paper1_assets.py
- generator-capability.schema.json
- record_review
- test_humanities_overlay.py
- _BooleanParser
- CodingKeys
- JobHistoryView
- enum
- required
- ObjectivePolicy
- add_page_structure_tree
- properties
- OllamaModelRecommendation
- enum
- required
- required
- properties
- subject
- PhysicsPlugin
- .baseQuery
- sample
- required
- enum
- empirical-calibration.schema.json
- _call_name
- build_backend.sh
- topic_id
- enum
- stratum
- model
- test_configured_family.py
- aqa_front_matter_pages
- CostingCase
- non_comparable_features
- test_aqa_accounting_calibration.py
- test_aqa_business_calibration.py
- test_difficulty_calibration.py
- test_ocr_economics_calibration.py
- generator_working_directory
- xcbuild.sh
- capabilities
- diagnose.sh
- move_to_trash.sh
- run_app_macos.sh
- app_board
- app_subject
- backend_subject
- board_profile
- entry_point
- id
- package
- specification_version
- france/__init__.py
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
- `FirstPassClient` --uses--> `GenerationPolicy`  [INFERRED]
  tests/test_assessment_checkpoints.py → Backend/Core/ai_assessment.py
- `FirstPassDifficultyClient` --uses--> `GenerationPolicy`  [INFERRED]
  tests/test_assessment_checkpoints.py → Backend/Core/ai_assessment.py
- `NoCallsClient` --uses--> `GenerationPolicy`  [INFERRED]
  tests/test_assessment_checkpoints.py → Backend/Core/ai_assessment.py
- `GivenRateClient` --uses--> `CheckpointMismatch`  [INFERRED]
  tests/test_shared_numeric_integrity.py → Backend/Core/assessment_checkpoints.py

## Import Cycles
- None detected.

## Communities (242 total, 28 thin omitted)

### Community 0 - "document_dsl/__init__.py"
Cohesion: 0.06
Nodes (88): AnswerSpace, BaseComponent, BlankPage, Component, ContinuationPage, Cover, Diagram, Graph (+80 more)

### Community 1 - "GeneratedQuestion"
Cohesion: 0.06
Nodes (126): AssessmentLLMClient, _batches_for_client(), _bounded_text(), _candidate_question(), _canonical_objective_allocation(), _clean_generated_prompt(), _contains_command_word(), _demand_item() (+118 more)

### Community 2 - "GeneratedPaper"
Cohesion: 0.06
Nodes (94): AppliedMCQSource, _demand_band(), GeneratedPaper, GeneratedSection, _objective_allocation(), PaperRule, _prompt_uses_command_word(), BaseModel (+86 more)

### Community 3 - "load_syllabus"
Cohesion: 0.05
Nodes (99): extract_pdf_text(), Path, Extract stable reading-order text without a Poppler CLI dependency., _artifacts(), _build(), _improve(), _supporting(), build_paper1_blueprint() (+91 more)

### Community 4 - "String"
Cohesion: 0.04
Nodes (92): Decodable, Equatable, AssessmentKind, fullPaper, questionBank, .title, AuthoringProvenanceKind, aiAuthoredOnly (+84 more)

### Community 5 - "paper_fidelity_audit.py"
Cohesion: 0.05
Nodes (103): Pixmap, parametrize, Path, test_compact_profile_omits_raster_geometry(), test_contact_sheets_make_visual_review_artifacts(), test_generated_document_falls_back_to_nested_transaction_output(), test_generated_document_supports_app_per_paper_directories(), test_metric_callout_names_print_resolution_comparison_dimensions() (+95 more)

### Community 6 - "cspapergen/render_pdf.py"
Cohesion: 0.07
Nodes (102): paper1_reference_code(), Shared reference snippets used by the renderer and publication integrity gate., CanvasBarcodeStyle, draw_barcode(), draw_glyph_answer_rules(), draw_solid_answer_rules(), GlyphRuleStyle, Canvas (+94 more)

### Community 7 - "build_paper_blueprint"
Cohesion: 0.07
Nodes (92): build_paper_blueprint(), PaperBlueprint, Syllabus, load_builtin_paper_config(), review_table_rows(), load_syllabus(), Path, Syllabus (+84 more)

### Community 8 - "live_generation_matrix.py"
Cohesion: 0.06
Nodes (71): Release qualification evidence and policy models., ArtifactEvidence, EvidenceRecord, GateState, ModelIdentity, BaseModel, field_validator, Path (+63 more)

### Community 9 - "require_difficulty_review"
Cohesion: 0.07
Nodes (77): _export_difficulty_candidate_projection(), candidate_review_content(), CandidateContentIdentity, difficulty_candidate_projection(), DifficultyCandidateProjection, edexcel_difficulty_candidate_projection(), ensure_difficulty_candidate_projection(), _mapping() (+69 more)

### Community 10 - "Text"
Cohesion: 0.04
Nodes (93): CaseIterable, Charts, KeyPath, View, PanelEmptyState, .body, String, value (+85 more)

### Community 11 - "ApplicationCoordinator"
Cohesion: 0.04
Nodes (36): AnyCancellable, DateFormatter, FrenchAssessmentWorkspace, .body, .body, .body, .providerSettings, OutputSettingsTab (+28 more)

### Community 12 - "GeneratedFile"
Cohesion: 0.06
Nodes (33): .body, AppDefaults, AppLinks, AppStorageKey, SecretAccount, Bool, String, URL (+25 more)

### Community 13 - "AssessmentContract"
Cohesion: 0.06
Nodes (70): AssessmentContract, contract_for_question(), EvidenceRecord, GeneratedNumericField, GraphContract, _numeric_contracts(), NumericRole, NumericValueContract (+62 more)

### Community 14 - "test_ollama_generation.py"
Cohesion: 0.09
Nodes (45): _clean_prompt(), generate_questions_with_ollama(), _merge_question_text(), _merge_source_text(), _validate_ai_question(), _bar_chart_data(), candidate_stimulus_data(), Expose the same source values and dispatch rules used to draw a figure. (+37 more)

### Community 15 - "psychometrics.py"
Cohesion: 0.08
Nodes (56): CalibrationMetadata, CalibrationStore, ConsentRecord, _normalise_row(), Any, Path, Encrypted local storage for row-level calibration evidence. Keys are…, _read_rows() (+48 more)

### Community 16 - "pastpapergen/generator.py"
Cohesion: 0.06
Nodes (72): MultipleChoiceOption, _adapt_paper_three_case_guidance(), _best_section_a_context_point(), _build_part(), _build_parts(), _choice_group_name(), _choice_lookup(), _choose_topic() (+64 more)

### Community 17 - "RecentDocumentStore"
Cohesion: 0.06
Nodes (37): Codable, FileManager, GenerationJobState, LocalizedError, GenerationConfiguration, GenerationJobRecord, .missingArtifactCount, GenerationJobState (+29 more)

### Community 18 - "CoverProfile"
Cohesion: 0.06
Nodes (48): aqa_question_cover(), CoverProfile, _draw_aqa_mark_scheme_cover(), _draw_cover_barcode(), draw_mark_scheme_cover(), _draw_ocr_mark_scheme_cover(), MarkSchemeCover, QuestionPaperCover (+40 more)

### Community 19 - "test_computer_science_objectives.py"
Cohesion: 0.06
Nodes (65): generate_package(), Path, load_rule(), build_paper(), Syllabus, _flatten(), Path, Generic examiner rules belong in front matter, not every table row. (+57 more)

### Community 20 - "Paragraph"
Cohesion: 0.12
Nodes (62): AQAAnswerLines, Paragraph, _accounting_marking_guidance_pages(), _accounting_system_case(), _additional_answer_page(), _appropriation_answer_table(), _assessment_objectives_page(), _candidate_verification_rows() (+54 more)

### Community 21 - "AIProvider"
Cohesion: 0.05
Nodes (37): AIProvider, anthropic, apple, .backendID, .id, ollama, openAI, .sendsPromptsOffDevice (+29 more)

### Community 22 - "test_aqa_business.py"
Cohesion: 0.06
Nodes (48): generate_package(), Path, FinancialPosition, format_number(), The single source of truth for Paper 1 financial-statement figures., Format an exam answer without meaningless trailing zeroes., build_paper(), _extract() (+40 more)

### Community 23 - "WorkspaceLayoutMode"
Cohesion: 0.12
Nodes (11): CGFloat, Bool, WorkspaceLayoutMode, compact, expanded, .showsInspector, .showsSidebar, standard (+3 more)

### Community 24 - "ocregen/render_pdf.py"
Cohesion: 0.10
Nodes (55): OCRAnswerLines, OCR dotted writing rules inside the existing allocated answer area. Reviewed…, _add_economics_diagram(), _add_firm_objectives_diagram(), _add_ppf_diagram(), _annotation_conventions_page(), _answer_mark(), _assessment_allocation() (+47 more)

### Community 25 - "properties"
Cohesion: 0.04
Nodes (59): printed-conflicting, published-item-allocation, reconciled-published-aggregate, unknown, anyOf, default, title, const (+51 more)

### Community 26 - "build_question"
Cohesion: 0.21
Nodes (58): Stimulus, _assembly_program_question(), _assembly_trace_question(), _big_data_question(), _big_data_short_question(), _binary_short_question(), _bitmap_question(), _bitmap_storage_question() (+50 more)

### Community 27 - "test_sql_answer_verification.py"
Cohesion: 0.10
Nodes (52): Render only public schema facts; no worked query is present., Validate the answer and every model-presented full statement separately., render_sql_schema(), sql_source_intent_sha256(), validate_sql_response(), model_validator, _difficulty_candidate(), _difficulty_solution() (+44 more)

### Community 28 - "ExamBoardOption"
Cohesion: 0.07
Nodes (45): Hashable, Identifiable, CatalogSubject, ExamBoardOption, .fullPapers, .isReady, .questionBanks, .usesAI (+37 more)

### Community 29 - "test_source_credit_integrity.py"
Cohesion: 0.08
Nodes (43): calculation(), calculation_label(), calculation_prompt(), calculation_working(), EconomicsSource, BaseModel, Decimal, model_validator (+35 more)

### Community 30 - "test_render_pdf.py"
Cohesion: 0.12
Nodes (51): _apply_edexcel_page_boxes(), Path, Match Pearson question-paper bleed and crop boxes without changing A4 content., render_question_paper(), _answer_rule_count(), _blank_axis_lines(), _blueprint_with_section_a_question(), _dark_pixels() (+43 more)

### Community 31 - "cspapergen/ollama_client.py"
Cohesion: 0.08
Nodes (48): numeric_tokens(), Extract quantities exactly enough to catch broken data/source rewrites., aqa_cs_difficulty_candidate(), aqa_cs_solver_item(), authoring_route(), Any, question_content_sha256(), AQA CS source-coupled review identity, shared by authoring/resume/export. This… (+40 more)

### Community 32 - "test_ocr_economics.py"
Cohesion: 0.08
Nodes (46): percentage_change_context(), Candidate chart endpoints and the requested one-decimal percentage output., generate_package(), Path, build_paper(), _evaluation_scheme(), _extract(), _extract_number() (+38 more)

### Community 33 - "providers.py"
Cohesion: 0.08
Nodes (45): _hosted_client(), _aqa_cs_part_count(), _edexcel_part_count(), hosted_client(), HostedLLMClient, _normalise_base_url(), _ollama_json_schema(), _ollama_output_budget() (+37 more)

### Community 34 - "sql_contracts.py"
Cohesion: 0.11
Nodes (39): _contract_column(), _Count, _equality(), _Field, _finding(), fitness_centre_sql_contract(), _Frozen, _has_sql_statement_shape() (+31 more)

### Community 35 - "reconcile_solution"
Cohesion: 0.10
Nodes (47): reconcile_solution(), _part_solver_item(), test_solver_view_includes_candidate_visible_stimulus_and_hides_answers(), classification(), parametrize, test_authoring_merge_preserves_closed_key_through_final_solver(), test_classification_final_review_rejects_swapped_slots_before_demand_review(), test_classification_slot_contract_reaches_solver_without_answers() (+39 more)

### Community 36 - "test_aqa_economics.py"
Cohesion: 0.07
Nodes (47): _tasks(), Return the immutable rules for one printed option (one-based)., resolve_question_rules(), generate_package(), Path, build_paper(), Syllabus, _section_instructions() (+39 more)

### Community 37 - "solve_selected_response"
Cohesion: 0.09
Nodes (46): _better_than_target(), _decimal(), _display_decimal(), _money_choice(), _numeric_choice(), _percent_choice(), _plain_decimal(), Any (+38 more)

### Community 38 - "pastpapergen/cli.py"
Cohesion: 0.11
Nodes (24): BuildResult, type, path, validate_assessment_contract(), _artifacts(), _build(), default_output_dir(), generate_package() (+16 more)

### Community 39 - "ocrcsgen/render_pdf.py"
Cohesion: 0.09
Nodes (45): mark_scheme_cover(), ocr_question_cover(), Flowable, ExamPage, Flowable, A full-page shell that can also live inside a Platypus story., OCRComputerScienceAnswerLines, _artifacts() (+37 more)

### Community 40 - "properties"
Cohesion: 0.04
Nodes (48): 1, 2, $ref, title, type, minLength, title, type (+40 more)

### Community 41 - "reference_corpus.py"
Cohesion: 0.13
Nodes (45): MonkeyPatch, Path, test_document_path_requires_filename(), test_document_path_stays_inside_corpus(), test_download_manifest_records_failure_and_continues(), test_parse_aqa_resources_filters_modified_papers(), test_parse_ocr_resources_uses_a_level_tab_only(), test_parse_ocr_specifications_keeps_a_level_not_as_level() (+37 more)

### Community 42 - "DocumentPreviewView"
Cohesion: 0.06
Nodes (33): AppKit, Combine, DocumentPreviewView, .body, .exportAlertBinding, .provenanceRecord, .selectedBinding, .selectedFile (+25 more)

### Community 43 - "test_mlx_setup.py"
Cohesion: 0.09
Nodes (44): _available_cache_bytes(), ensure_mlx_ready(), handle_mlx_status(), handle_setup_mlx(), install_mlx_runtime(), is_managed_development_environment(), load_mlx_model(), mlx_runtime_available() (+36 more)

### Community 44 - "Question"
Cohesion: 0.11
Nodes (39): derive_task_semantics(), Any, BaseModel, Strict, deterministic task contracts for AQA CS topic-reference evidence., The serialised summary is valid only when it agrees with the question., Derive the comparison form from printed question data, never its hint., ReferenceTaskContract, _align_paper1_structure() (+31 more)

### Community 45 - "PaperCreatorTests"
Cohesion: 0.07
Nodes (15): CatalogLoader, CatalogLoadError, duplicateBoard, duplicateImplementation, emptyImplementation, .errorDescription, implementationMissingFromCatalog, missingResource (+7 more)

### Community 46 - "CodingKeys"
Cohesion: 0.04
Nodes (46): CodingKeys, assessmentKind, backendVersion, capabilities, checks, code, command, cpuLoad (+38 more)

### Community 47 - "aqabizgen/render_pdf.py"
Cohesion: 0.15
Nodes (44): SelectedResponseContract, _artifacts(), _additional_answer_page(), _ao_summary(), _assessment_objectives_page(), _assessment_route_page(), _break_even_diagram(), _calculation_marking_page() (+36 more)

### Community 48 - "type"
Cohesion: 0.06
Nodes (44): type, additionalProperties, $ref, title, type, additionalProperties, title, type (+36 more)

### Community 49 - "AssessmentCheckpointStore"
Cohesion: 0.14
Nodes (28): AssessmentCheckpointStore, CheckpointCorrupt, CheckpointIdentity, CheckpointMismatch, identity_for_blueprint(), Any, BaseModel, Path (+20 more)

### Community 50 - "test_open_credit_reconciliation.py"
Cohesion: 0.14
Nodes (40): alternative_permission(), Any, Only known host-authored permissions can bypass answer-value checking., review_open_credit(), _calculation_item(), test_independent_solver_recomputes_arithmetic_without_the_draft_scheme(), adjudication_response(), cpu_fixture() (+32 more)

### Community 51 - "family_adapter.py"
Cohesion: 0.12
Nodes (28): ArtifactSpec, FamilyAdapter, Path, run_family_adapter(), default_ollama_model(), model_recommendations(), OllamaModelRecommendations, OllamaModelTier (+20 more)

### Community 52 - "assessment_package.py"
Cohesion: 0.13
Nodes (39): _assessment_contract(), AssessmentPackageCompatibilityError, _authoring_provenance(), _contains_non_finite(), _evidence_ids(), _extract_items(), _form_id(), _level_policies() (+31 more)

### Community 53 - "reference_evidence.py"
Cohesion: 0.19
Nodes (14): CandidateTopology, Observations, BaseModel, model_validator, QualitativeExaminerEvidence, QuarantinedForm, Strict H3 source evidence boundaries; aggregate-v2 is not path qualification., SourceForm (+6 more)

### Community 54 - "Canvas"
Cohesion: 0.13
Nodes (42): _count_pages(), _draw_answer_lines_until(), _draw_answer_page_header(), _draw_case_source_figure(), _draw_centred_instruction_line(), _draw_continuation_lines(), _draw_do_not_write_rail(), _draw_front_section() (+34 more)

### Community 55 - "aqaecongen/render_pdf.py"
Cohesion: 0.14
Nodes (39): _assessment_objectives_table(), _context_data_table(), _context_first_page(), _context_second_page(), _cover_profile(), _document(), _economic_diagram(), _general_marking_page() (+31 more)

### Community 56 - "generator/tests/test_assessment_contracts.py"
Cohesion: 0.11
Nodes (39): _question_solver_item(), paper(), parametrize, test_actual_level_tariffs_have_distinct_usable_band_descriptors(), test_all_seeded_styles_have_contract_credit_not_topic_note_filler(), test_business_expansion_short_credit_marks_one_complete_route(), test_complete_declared_numeric_operations_have_literal_answers(), test_content_driven_policy_is_reproducible_and_does_not_reclassify_other_documents() (+31 more)

### Community 57 - "NumericOutput"
Cohesion: 0.13
Nodes (35): CS component policy audit over candidate-answerable paths, not printed totals., Exact raw-provider shape; semantic validation remains item-specific below., SolverResponseEnvelope, check_numeric_alternatives(), check_published_outputs(), CheckedNumericOutput, CheckedTextOutput, display() (+27 more)

### Community 58 - "pastpapergen/render_pdf.py"
Cohesion: 0.09
Nodes (35): BoardLayout, GraphParams, _answer_line_count(), _bar_label(), _draw_axis_arrow(), _draw_bar_chart(), _draw_blank_answer_axes(), _draw_context_box() (+27 more)

### Community 59 - "required"
Cohesion: 0.07
Nodes (39): assessment_objectives, cognitive_operation, command_word, comparable_metrics, demand_band, demand_basis, extraction_policy, feature_basis (+31 more)

### Community 60 - "properties"
Cohesion: 0.05
Nodes (39): high, low, standard, anyOf, title, minLength, title, type (+31 more)

### Community 61 - "test_shared_numeric_integrity.py"
Cohesion: 0.14
Nodes (36): _independently_validate_candidate(), accounting_tasks(), GivenRateClient, parametrize, test_abc_checks_every_asserted_intermediate_without_rounding_into_final(), test_all_p2_closed_calculations_are_source_derived_and_exhaustively_reconciled(), test_chart_percentage_shared_families_have_independent_typed_contracts(), test_checkpoint_resume_rejects_changed_preserved_numeric_prompt() (+28 more)

### Community 62 - "reference_demand_profiles.py"
Cohesion: 0.12
Nodes (34): Pattern, build_document(), CorpusFamily, _distribution(), extract_reference_features(), extract_reference_items(), _fingerprint(), _item_demand() (+26 more)

### Community 63 - "independent_solver.py"
Cohesion: 0.11
Nodes (30): collect_credit_rules(), credit_rule(), CreditRule, declared_rule_metadata_present(), BaseModel, Origin-preserving open credit rules; never promote model advice to authority., Preserve numerical caps/dependencies, not just their descriptive prose.…, _as_mapping() (+22 more)

### Community 64 - "pdf_validation.py"
Cohesion: 0.11
Nodes (32): Rect, compare_page_evidence(), _contrast_against_white(), _contrast_ratio(), _count_score(), _font_embedding(), _font_evidence(), _is_decorative_bleed() (+24 more)

### Community 65 - "pastpapergen/ollama_client.py"
Cohesion: 0.07
Nodes (64): candidate_content_identity(), CandidateSectionRule, ChoiceSelection, MultipleChoiceOption, PaperBlueprint, PaperConfig, BaseModel, QuestionBlueprint (+56 more)

### Community 66 - "runtime.py"
Cohesion: 0.15
Nodes (28): atomic_json(), _check_review(), generate_assessment(), _originality(), Path, Source-scoped French authoring with hash-bound reviews and resumable drafts., _review_prompt(), validate_package() (+20 more)

### Community 67 - "test_layout_master.py"
Cohesion: 0.12
Nodes (25): _aqa_cs_printed_credit(), conform_generated_documents(), _edexcel_printed_credit(), Path, Generated-content policy is not an observed reference-count range., Content-driven pagination must preserve every published marking statement., runtime_page_count_policy(), LayoutConformanceError (+17 more)

### Community 68 - "benchmark.py"
Cohesion: 0.12
Nodes (33): apple_cpu_core_split(), available_memory_gb(), avg(), clamp(), cpu_brand(), cpu_load_percent(), cpu_probe(), disk_probe() (+25 more)

### Community 69 - "aqa_section_intro"
Cohesion: 0.10
Nodes (25): aqa_lozenge(), aqa_section_intro(), AQAQuestionHeaderFactory, flowable_question_block(), independent_practice_page(), OCRQuestionHeaderFactory, page_sequence(), Color (+17 more)

### Community 70 - "ExamPageProfile"
Cohesion: 0.17
Nodes (31): _draw_aqa_footer(), _draw_aqa_page(), _draw_barcode(), draw_exam_page(), _draw_independent_notice(), _draw_ocr_notice(), _draw_ocr_page(), _draw_ocr_rules() (+23 more)

### Community 71 - "open_credit.py"
Cohesion: 0.12
Nodes (33): cpu_credit_allocations(), cpu_credit_contract(), _cpu_quote_supports_criterion(), credit_identity(), credit_item_projection(), CreditJudgement, CriterionDecision, _has_unambiguous_instruction_antecedent() (+25 more)

### Community 72 - "build_item_demand_target"
Cohesion: 0.11
Nodes (39): assessment_objectives_for_item(), audit_form_demand(), build_item_demand_target(), _checked_in_profile_fingerprint(), _cognitive_operations(), _collapse_command_distribution(), _command_family(), _difficulty_evidence() (+31 more)

### Community 73 - "properties"
Cohesion: 0.06
Nodes (36): aqa-topic-operation-records-v3, edition-leaf-path-features-v2, full-paper, question-bank, unqualified-reference-v1, enum, minLength, type (+28 more)

### Community 74 - "test_mark_scheme_layout.py"
Cohesion: 0.18
Nodes (30): formatted_generation_date(), pdf_font_names(), Return the font families actually used by visible text spans., _cleanup_graph_cache(), render_mark_scheme(), _assert_complete_contract_scheme(), _blueprint_with_section_a_calculation(), _blueprint_with_section_b_topic() (+22 more)

### Community 75 - "IndependentSolver"
Cohesion: 0.19
Nodes (29): IndependentSolver, Solve an item in a context that deliberately excludes its draft scheme., NoModelArithmetic, parametrize, test_closed_accounting_solutions_ignore_the_draft_answer_key(), closed_item(), parametrize, ResponseClient (+21 more)

### Community 76 - "test_aqa_accounting.py"
Cohesion: 0.11
Nodes (27): build_paper(), _extract(), _number(), Random, Syllabus, _values(), Independent AQA 7127 practice-paper generator., parametrize (+19 more)

### Community 77 - "_mark_scheme_rows"
Cohesion: 0.11
Nodes (32): _brief_source_evidence(), _calculation_answer_lines(), _mark_point_relevance(), _mark_scheme_rows(), _normalise_mark_point(), _one_mark_points(), _paper_one_fifteen_mark_scheme_lines(), _paper_one_five_mark_diagram_lines() (+24 more)

### Community 78 - "NSIExercise"
Cohesion: 0.09
Nodes (25): Credit, NSIExercise, NSIQuestion, BaseModel, Decimal, model_validator, Native French NSI authoring records and prompts, not translated A-level items., solver_prompt() (+17 more)

### Community 79 - "layout_master.py"
Cohesion: 0.13
Nodes (26): _clamp_fitz_rect(), conform_pdf_page_boxes(), conform_pdf_to_box_template(), draw_text_slot(), _fitz_rect_close(), load_layout_master(), _page_from_payload(), _page_matches_box_set() (+18 more)

### Community 80 - "test_pdf_validation.py"
Cohesion: 0.16
Nodes (30): extract_pdf_evidence(), GlyphMetric, Counter, Path, Fail closed on malformed, substituted, annotated, or low-resolution PDFs., A compact, serialisable sample of one rendered PDF glyph., Extract print and accessibility evidence without retaining source prose. Glyph…, validate_pdf_for_release() (+22 more)

### Community 81 - "QualityInspector"
Cohesion: 0.05
Nodes (51): App, Commands, GenerationQualityState, AppCommands, PaperCreator, .body, GeneratedFilesTable, GenerationProgress (+43 more)

### Community 82 - "test_reference_evidence_validation.py"
Cohesion: 0.15
Nodes (19): BaseModel, model_validator, ReferenceDemandDocument, validate_profile_payload(), document(), parametrize, `model_copy(update=...)` does not re-run schema-three evidence validation., Calling a public Pydantic validator is not evidence of canonical loading. (+11 more)

### Community 83 - "render_pdf_atomically"
Cohesion: 0.15
Nodes (24): InvalidRenderOutput, Path, RuntimeError, A document role could not be rendered safely., Rendering exceeded its bounded qualification window., A renderer returned without producing a readable PDF., Render one PDF role under a deadline and promote it atomically., _readable_page_count() (+16 more)

### Community 84 - "SubjectValidation"
Cohesion: 0.13
Nodes (13): Any, Protocol, Shared subject interfaces, independent of plugin implementations and discovery., SubjectPlugin, SubjectValidation, ContractSubjectPlugin, _normalise_identifier(), Any (+5 more)

### Community 85 - "mathematics.py"
Cohesion: 0.15
Nodes (21): AnswerComparison, compare_mathematical_answers(), FurtherMathematicsPlugin, MarkAward, _marking_rules(), MarkingRule, MathematicalAnswer, MathematicsPlugin (+13 more)

### Community 86 - "properties"
Cohesion: 0.07
Nodes (29): approval_evidence, approved_by_identity_class, duration_minutes, sections, total_marks, policy_id, status, additionalProperties (+21 more)

### Community 87 - "test_reference_demand.py"
Cohesion: 0.17
Nodes (28): module(), profile_payload(), parametrize, Path, test_calculation_reasoning_ceiling_scales_with_tariff(), test_committed_profiles_cover_every_advertised_assessment_without_source_text(), test_committed_profiles_include_unadvertised_aqa_mathematics_evidence(), test_empty_context_does_not_create_an_application_requirement() (+20 more)

### Community 88 - "CanonicalSolution"
Cohesion: 0.14
Nodes (25): _bounded(), GenerationEvidenceError, Any, Path, ValueError, Private, bounded evidence for rejected generation; never approved checkpoints., Save only explicitly supplied evidence, not arbitrary errors or prompts.…, save_failure_diagnostic() (+17 more)

### Community 89 - "test_app_backend.py"
Cohesion: 0.16
Nodes (27): CaptureFixture, CompletedProcess, Path, run_bridge(), run_bridge_raw(), test_aqa_accounting_all_papers_generate_expected_files(), test_aqa_business_all_papers_generate_expected_files(), test_aqa_economics_all_papers_generate_expected_files() (+19 more)

### Community 90 - "graphs.py"
Cohesion: 0.30
Nodes (26): Axes, ad_as_diagram(), _arrow_axes(), _ax(), circular_flow_diagram(), consumer_producer_surplus(), demand_supply_diagram(), _ensure_style() (+18 more)

### Community 91 - "test_science_subjects.py"
Cohesion: 0.14
Nodes (18): ChemistryPlugin, equation_is_balanced(), _equation_side(), Formula, _multiplier(), _parse_group(), Any, Counter (+10 more)

### Community 92 - "generate_package"
Cohesion: 0.13
Nodes (23): default_output_dir(), generate_package(), main(), Path, cache_notes(), discover_note_pdfs(), _extract_text(), note_context_for_topic() (+15 more)

### Community 93 - "properties"
Cohesion: 0.08
Nodes (26): ai-assisted, deterministic, type, minLength, type, pattern, type, enum (+18 more)

### Community 94 - "test_coverage_matrix.py"
Cohesion: 0.20
Nodes (24): family(), matrix(), Path, test_catalog_availability_is_owned_only_by_registry(), test_checked_in_matrix_is_deterministic_and_current(), test_existing_generators_are_reported_without_false_verification(), test_matrix_exactly_covers_layout_profiles(), test_no_verified_paper_has_a_failed_gate() (+16 more)

### Community 95 - "ReferenceIndex"
Cohesion: 0.16
Nodes (14): EducationContext, EvidenceGap, Path, ValueError, Local reference retrieval: scope first, text ranking second, no fallback., No eligible source supports a requested reference query., ReferenceHit, ReferenceIndex (+6 more)

### Community 96 - "mark_scheme_enrichment.py"
Cohesion: 0.22
Nodes (23): _answer_form(), _application_label(), _clean_text(), _compact_technical_guidance(), _deduplicate(), enrich_paper(), _enrich_question(), _level_guidance() (+15 more)

### Community 97 - "BackendClient"
Cohesion: 0.17
Nodes (14): BackendClient, BackendClientError, backendMissing, .errorDescription, pythonMissing, pythonVenvUnreadable, BackendFile, LaunchConfiguration (+6 more)

### Community 98 - "reference-demand-profile.schema.json"
Cohesion: 0.08
Nodes (24): derived_aggregate_only, profiles, purpose, retains_source_text, schema_version, additionalProperties, const, $id (+16 more)

### Community 99 - "test_accounting_objectives.py"
Cohesion: 0.15
Nodes (24): load_rule(), _gbp(), _gbp_decimal(), _management_calculation(), Build a complete, internally solved data contract for each numeric task., Format whole-pound values in the style used by AQA accounting papers., paper_for(), parametrize (+16 more)

### Community 100 - "render_source_booklet"
Cohesion: 0.13
Nodes (23): economics_exam_schedule(), ExamSchedule, formatted_economics_exam_date(), date, _draw_boxes(), _draw_cover(), _draw_crop_marks(), _draw_fake_barcode() (+15 more)

### Community 101 - "$defs"
Cohesion: 0.08
Nodes (25): maximum, minimum, $defs, distribution, SourceForm, SourceItem, SourcePath, tolerance (+17 more)

### Community 102 - "generation.py"
Cohesion: 0.21
Nodes (21): progress_emitter(), _atomic_publish(), _cancel_generation(), checkpoint_path_for_job(), emit_generated_files(), finalize_generated_documents(), GenerationCancelled, _generator_version() (+13 more)

### Community 103 - "Foundation"
Cohesion: 0.09
Nodes (13): Foundation, AssessmentBundleExporter, URL, FrenchAssessmentRequest, .arguments, Bool, Int, String (+5 more)

### Community 104 - "properties"
Cohesion: 0.08
Nodes (24): type, type, minimum, type, type, type, maximum, minimum (+16 more)

### Community 105 - "discover_subject_plugin"
Cohesion: 0.19
Nodes (17): board_profile(), board_profile_ids(), BoardProfile, _normalise_identifier(), discover_subject_plugin(), subject_plugin_ids(), parametrize, test_authorised_extract_with_option_route_and_level_policy_passes() (+9 more)

### Community 106 - "emit"
Cohesion: 0.23
Nodes (19): build_parser(), handle_bundle_check(), handle_framework_generate(), handle_french_references(), main(), ArgumentParser, Namespace, Fail fast when a packaged backend is missing a dynamic generator. (+11 more)

### Community 107 - "accounting.py"
Cohesion: 0.28
Nodes (22): _accounting_endings(), accounting_outputs(), _appropriation(), _assets(), derive_accounting_open_response_context(), _exact(), _income(), _ledger() (+14 more)

### Community 108 - ".initialEstimate"
Cohesion: 0.19
Nodes (11): EstimateFactor, GenerationEstimate, .etaDate, .remainingText, TimeInterval, GenerationEstimator, Bool, Date (+3 more)

### Community 109 - "required"
Cohesion: 0.13
Nodes (23): assessment_kind, cognitive_operation_distribution, command_family_distribution, command_word_distribution, comparison_basis, demand_distribution, evidence_gaps, evidence_policy_id (+15 more)

### Community 110 - "ShareholderCase"
Cohesion: 0.09
Nodes (4): Candidate-visible source contract for the Paper 1 shareholder decision., Return only facts and units printed on the candidate source page., ShareholderCase, test_shareholder_case_keeps_equity_and_investor_figures_in_consistent_units()

### Community 111 - "test_topic_reference_evidence.py"
Cohesion: 0.20
Nodes (22): bank_items(), module(), parametrize, A serialised hint must never override the question that will be printed., Only the versioned contract may establish a reference comparison., test_actual_same_topic_operation_and_mode_still_matches(), test_bank_support_rejects_changed_work_not_just_matching_topic_words(), test_forged_or_sparse_source_inventory_cannot_qualify_bank() (+14 more)

### Community 112 - "corpus.py"
Cohesion: 0.17
Nodes (18): assign_splits(), check_download(), check_url(), discover_links(), download_with_system_trust(), ingest(), main(), OfficialRedirects (+10 more)

### Community 113 - "PathSection"
Cohesion: 0.09
Nodes (22): answer_options, candidate_marks, options, exclusiveMinimum, title, type, exclusiveMinimum, title (+14 more)

### Community 114 - "ocrcsgen/generator.py"
Cohesion: 0.17
Nodes (18): _analysis_prompt(), _levels(), _programming_prompt(), _programming_scheme(), Random, Topic, _question(), _representation_calculation() (+10 more)

### Community 115 - "properties"
Cohesion: 0.09
Nodes (22): type, type, format, type, type, minLength, type, minLength (+14 more)

### Community 116 - "required"
Cohesion: 0.10
Nodes (21): advertised, app_board, app_subject, backend_subject, blueprint_version, board, board_profile, content_mode (+13 more)

### Community 117 - "pastpapergen/notes.py"
Cohesion: 0.20
Nodes (19): _clean_chunk(), essay_capable_topic_ids(), _flush_note_chunk(), _is_exam_point(), _is_note_noise(), _looks_like_heading(), _note_chunks(), note_context_for_topic() (+11 more)

### Community 118 - "properties"
Cohesion: 0.10
Nodes (21): minLength, type, minLength, type, minLength, type, format, type (+13 more)

### Community 119 - "ocr_computer_science_calibration.py"
Cohesion: 0.21
Nodes (18): report(), test_difficulty_remains_external_evidence_gated(), test_multi_seed_structural_demand_passes(), test_reference_evidence_is_aggregate_only(), _band(), build_generated_profile(), build_reference_profile(), build_report() (+10 more)

### Community 120 - "profile_for"
Cohesion: 0.23
Nodes (19): load_reference_demand_document(), profile_for(), Path, items(), paths_module(), parametrize, test_complete_pairs_produce_six_eighty_mark_paths_not_cross_pairs(), test_correlated_source_vectors_cannot_pass_by_coordinatewise_bounds() (+11 more)

### Community 121 - "reportlab_theme.py"
Cohesion: 0.12
Nodes (12): AnswerLineFlowable, AQACompactAnswerLines, Flowable, Return a Table subclass whose raw string cells use the controlled font.…, Shared, measured answer-line primitive used by every board renderer., themed_table_class(), TableType, test_board_answer_line_presets_own_repeated_renderer_geometry() (+4 more)

### Community 122 - "properties"
Cohesion: 0.10
Nodes (20): type, pattern, type, minLength, type, minLength, type, minLength (+12 more)

### Community 123 - "validate_generator_migration.py"
Cohesion: 0.24
Nodes (10): build_parser(), _layout_board(), main(), MigrationIssue, MigrationReport, MigrationValidator, Any, ArgumentParser (+2 more)

### Community 124 - "provider.py"
Cohesion: 0.17
Nodes (13): NoRedirects, ollama_request(), open_ollama_request(), HTTPRedirectHandler, Keep French inference on the explicitly selected server, without proxy routing., _prompt(), FrenchOllamaClient, Explicit French transport policy; UK prompt detection remains unchanged. (+5 more)

### Community 125 - "generator_registry.py"
Cohesion: 0.23
Nodes (15): _capability(), generator_capabilities(), generator_subjects(), _paper_qualification(), PaperQualification, Any, _relative_path(), test_backend_bundle_script_is_registry_driven() (+7 more)

### Community 126 - "CandidateResponse"
Cohesion: 0.12
Nodes (25): BoardLevelPolicy, LevelDescriptor, LevelOfResponseEngine, load_level_policies(), MarkAnnotation, MarkDecision, BaseModel, model_validator (+17 more)

### Community 127 - "validate_mark_scheme_item"
Cohesion: 0.25
Nodes (17): _contains_any(), MarkSchemeQuality, _normalise(), Any, validate_mark_scheme_item(), _item(), test_accounting_follow_through_metadata_counts_as_method_guidance(), test_calculation_requires_method_or_working() (+9 more)

### Community 128 - "test_computer_science_subject.py"
Cohesion: 0.21
Nodes (12): ComputerSciencePlugin, _evaluate_boolean(), normalise_pseudocode(), pseudocode_equivalent(), Any, truth_table(), test_four_mark_boolean_tasks_have_equivalent_explicit_working(), test_computer_science_uses_the_specialised_plugin() (+4 more)

### Community 129 - "build_layout_masters.py"
Cohesion: 0.29
Nodes (18): _box(), _colour(), _content_box(), _drawing_kind(), _drawings(), extract_layout_master(), _furniture_signature(), _images() (+10 more)

### Community 130 - "test_science_overlay.py"
Cohesion: 0.35
Nodes (16): apparatus_diagram(), ApparatusSpec, Atom, Bond, circuit_diagram(), CircuitComponent, CircuitSpec, molecule_diagram() (+8 more)

### Community 131 - "required"
Cohesion: 0.11
Nodes (17): artifacts, created_at, evidence, gate_results, generator_id, model, reviewer_identity_class, seed (+9 more)

### Community 132 - "generate_package"
Cohesion: 0.20
Nodes (16): Rehydrate the renderer's case only from the published source data., generate_package(), Path, page_count(), Path, test_both_packages_render_36_page_question_papers(), test_invalid_paper_is_rejected(), test_paper_one_mark_scheme_matches_reference_question_sequence() (+8 more)

### Community 133 - "points"
Cohesion: 0.15
Nodes (10): AssessmentDefinition, CurriculumVersion, points(), Decimal, Education-system identity, independent of interface locale and UK board models., Read exact, non-negative decimal credit from a JSON string., field_validator, parametrize (+2 more)

### Community 134 - "CodingKeys"
Cohesion: 0.12
Nodes (17): CodingKeys, appContextWindow, contextWindow, defaultModel, detail, downloadSizeGB, id, maximumMemoryGB (+9 more)

### Community 135 - "_draw_section_a_question"
Cohesion: 0.20
Nodes (17): _axis_labels_for_draw_prompt(), _draw_answer_lines(), _draw_calculate_part_with_working_lines(), _draw_compact_part(), _draw_draw_part_with_axes(), _draw_mcq_part(), _draw_part_prompt(), _draw_section_a_question() (+9 more)

### Community 136 - "properties"
Cohesion: 0.12
Nodes (17): type, properties, type, type, type, type, type, type (+9 more)

### Community 137 - "inspect_release_compliance"
Cohesion: 0.27
Nodes (14): Path, test_release_compliance_detects_a_tracked_secret_signature(), test_release_compliance_passes_for_the_repository(), test_release_compliance_rejects_unbounded_runtime_dependencies(), _check_dependencies(), _check_entitlements(), _check_font_licences(), _check_privacy_manifest() (+6 more)

### Community 138 - "OllamaModelGuideDocument"
Cohesion: 0.16
Nodes (12): OllamaModelGuide, OllamaModelGuideDocument, OllamaModelGuideError, .errorDescription, invalidDefault, missingResource, unsupportedSchema, Bundle (+4 more)

### Community 139 - "enum"
Cohesion: 0.12
Nodes (16): algorithm-trace, calculation, computational-analysis, computational-design, constructed-response, extended-evaluation, mathematical-argument, multi-stage-calculation (+8 more)

### Community 140 - "IncomeStatementCase"
Cohesion: 0.17
Nodes (4): IncomeStatementCase, Decimal, Complete, internally consistent source for the Paper 1 company statement., _round_pounds()

### Community 141 - "string"
Cohesion: 0.17
Nodes (16): null, stage, type, type, type, null, approval_evidence, type (+8 more)

### Community 142 - "properties"
Cohesion: 0.12
Nodes (16): minLength, type, minLength, type, minLength, type, blueprint, contract (+8 more)

### Community 143 - "paths"
Cohesion: 0.07
Nodes (28): test_written_diagram_renderer_prints_the_declared_economic_structure(), items, additionalProperties, allOf, items, minItems, $ref, title (+20 more)

### Community 144 - "test_generator_migration.py"
Cohesion: 0.23
Nodes (13): Path, test_all_current_families_pass_declarative_migration_validation(), test_broken_fixture_reports_every_onboarding_surface(), test_scaffold_emits_complete_unadvertised_family_and_refuses_overwrite(), build_parser(), _cli_template(), main(), ArgumentParser (+5 more)

### Community 145 - "audit_candidate_paths"
Cohesion: 0.16
Nodes (18): audit_candidate_paths(), CandidatePath, enumerate_candidate_paths(), identity(), path_metrics(), PathOption, PathSection, Any (+10 more)

### Community 146 - "required"
Cohesion: 0.13
Nodes (15): maximum_acceptable_facility, maximum_dif_gap, minimum_acceptable_facility, minimum_candidates, minimum_discrimination, minimum_double_marked_pairs, minimum_facility_coverage, minimum_group_responses (+7 more)

### Community 147 - "SalesLedgerCase"
Cohesion: 0.16
Nodes (6): AccountingSystemCase, _gbp(), Single source of truth for the Paper 1 sales-ledger case. The question paper,…, Candidate-visible source for the bookkeeping-system decision., Return one exact, independently checkable award point per mark., SalesLedgerCase

### Community 149 - "additionalProperties"
Cohesion: 0.13
Nodes (15): items, minItems, type, uniqueItems, items, minItems, type, uniqueItems (+7 more)

### Community 150 - "id"
Cohesion: 0.13
Nodes (15): PathOption, minLength, title, type, items, minItems, title, type (+7 more)

### Community 151 - "aqa_accounting_calibration.py"
Cohesion: 0.34
Nodes (14): _band(), build_generated_profile(), build_reference_profile(), build_report(), _command(), _fingerprint(), _inventory(), main() (+6 more)

### Community 152 - "aqa_business_calibration.py"
Cohesion: 0.34
Nodes (14): _band(), build_generated_profile(), build_reference_profile(), build_report(), _command(), _fingerprint(), _inventory(), main() (+6 more)

### Community 153 - "ocr_economics_calibration.py"
Cohesion: 0.34
Nodes (14): _band(), build_generated_profile(), build_reference_profile(), build_report(), _command(), _fingerprint(), main(), _page_count() (+6 more)

### Community 154 - "enum"
Cohesion: 0.14
Nodes (14): analyse, contextualise, describe, design, explain, judge, program, retrieve (+6 more)

### Community 155 - "qualification_levels"
Cohesion: 0.14
Nodes (14): empirically_calibrated, engineering_validated, visually_calibrated, type, type, empirically_calibrated, engineering_validated, qualification_levels (+6 more)

### Community 156 - "_written"
Cohesion: 0.24
Nodes (10): _nearest_hundred(), _decision_levels(), _levels(), Topic, _written(), test_locked_calculation_schemes_are_exactly_derived_from_the_case_data(), test_locked_calculation_schemes_include_final_answers_and_all_case_numbers(), test_non_current_asset_question_and_mark_scheme_use_the_same_figures() (+2 more)

### Community 158 - "BiologyPlugin"
Cohesion: 0.43
Nodes (3): BiologyPlugin, Any, test_biology_requires_practical_and_data_provenance_when_declared()

### Community 159 - "test_source_candidate_paths.py"
Cohesion: 0.23
Nodes (13): _fixture_pdf(), module(), fixture, Original synthetic text, with the audited editions' page/mark structure., source_corpus(), test_aqa_selected_source_operations_do_not_manufacture_objective_tags(), test_business_edition_does_not_assume_same_question_numbers(), test_clean_ocr_mcq_rows_keep_published_ao_and_non_retrieval_operations() (+5 more)

### Community 160 - "required"
Cohesion: 0.17
Nodes (13): differential_item_functioning, discrimination, facility, item_id, median_time_seconds, responses, items, items (+5 more)

### Community 161 - "backend-protocol.schema.json"
Cohesion: 0.15
Nodes (12): event_id, job_id, protocol, timestamp, type, additionalProperties, allOf, $id (+4 more)

### Community 162 - "test_repository_hygiene.py"
Cohesion: 0.28
Nodes (10): test_committed_inventory_matches_the_current_repository(), test_every_tracked_file_has_a_durable_classification(), test_generated_and_binary_outputs_are_rejected(), test_maintained_visual_assets_are_classified_without_allowing_arbitrary_pngs(), test_root_lint_configuration_is_release_configuration(), Classification, classify_path(), inspect_repository() (+2 more)

### Community 163 - "difficulty_calibration.py"
Cohesion: 0.40
Nodes (12): build_generated_profile(), build_reference_profile(), build_report(), _command(), _fingerprint(), main(), _page_count(), _pdf_text() (+4 more)

### Community 164 - "test_french_framework.py"
Cohesion: 0.23
Nodes (11): code_listing(), ParagraphStyle, Path, Never rewrite executable text to make it fit a page., render_assessment(), assessment_framework(), National frameworks are not exam boards and never inherit UK AO policy., test_code_listings_never_silently_wrap_or_change_indentation() (+3 more)

### Community 165 - "topic_reference_evidence.py"
Cohesion: 0.29
Nodes (11): audit_topic_bank(), matching_records(), Any, Reviewed feature-only AQA topic subsets, never topic AO targets. Admission is…, Conservative semantic selectors for reviewed bank tasks; hints cannot override…, Conservative dependencies for the reviewed bank forms, not a language solver.…, Require task/context membership and an evidenced response form. A stimulus…, reviewed_topic_records() (+3 more)

### Community 166 - "required"
Cohesion: 0.17
Nodes (12): candidate_sample, facility_range, group_fairness_screen, independent_manual_review, internal_consistency, item_coverage, marker_standardisation, policy_approved (+4 more)

### Community 167 - "paper1_assets.py"
Cohesion: 0.50
Nodes (11): _page_footer(), _paragraph(), _practice_header(), Canvas, PaperBlueprint, Path, render_electronic_answer_document(), render_preliminary_material() (+3 more)

### Community 168 - "generator-capability.schema.json"
Cohesion: 0.17
Nodes (11): additionalProperties, $defs, safePath, $id, pattern, minLength, not, type (+3 more)

### Community 169 - "record_review"
Cohesion: 0.36
Nodes (9): digest(), artifact_identity(), Path, Self-attested human review records; hashes bind scope, not reviewer credentials., record_review(), review_status(), parametrize, test_review_is_bound_to_all_artifacts_and_becomes_stale() (+1 more)

### Community 170 - "test_humanities_overlay.py"
Cohesion: 0.55
Nodes (9): map_diagram(), MapFeature, MapSpec, Drawing, timeline_diagram(), TimelineEvent, TimelineSpec, test_humanities_diagrams_reject_misleading_or_invalid_inputs() (+1 more)

### Community 172 - "CodingKeys"
Cohesion: 0.18
Nodes (11): CodingKey, CodingKeys, artifacts, configuration, createdAt, id, provenance, qualification (+3 more)

### Community 173 - "JobHistoryView"
Cohesion: 0.25
Nodes (9): GenerationJobState, .systemImage, .title, JobHistoryView, .body, .selectedRecord, GenerationJobRecord, Set (+1 more)

### Community 174 - "enum"
Cohesion: 0.18
Nodes (11): benchmark_done, benchmark_metric, benchmark_sample, done, error, file, hello, models (+3 more)

### Community 175 - "required"
Cohesion: 0.18
Nodes (11): difficulty_independently_verified, evidence_fingerprint, family, form_id, paper, policy, provenance, sample (+3 more)

### Community 176 - "ObjectivePolicy"
Cohesion: 0.22
Nodes (4): ObjectivePolicy, Any, Reject unsupported labels in new or persisted qualified contracts., CS tasks are not classified from their tariff or AO3 label alone.

### Community 177 - "add_page_structure_tree"
Cohesion: 0.31
Nodes (9): add_page_structure_tree(), has_logical_page_order(), _has_structure_tree(), _new_object(), Document, Page, Path, Attach a deterministic page-level structure tree and marked content. Each page… (+1 more)

### Community 178 - "properties"
Cohesion: 0.20
Nodes (10): approved, draft, retired, minLength, type, properties, approved_by_identity_class, policy_id (+2 more)

### Community 179 - "OllamaModelRecommendation"
Cohesion: 0.31
Nodes (7): tiers, .currentRecommendation, OllamaModelRecommendation, .downloadDescription, Bool, Double, UInt64

### Community 180 - "enum"
Cohesion: 0.22
Nodes (9): anthropic, apple, ollama, openai, enum, supported_providers, items, type (+1 more)

### Community 181 - "required"
Cohesion: 0.22
Nodes (9): blueprint, contract, prompt, renderer, syllabus, versions, additionalProperties, required (+1 more)

### Community 182 - "required"
Cohesion: 0.22
Nodes (9): detail, qualification, title, required, checks, id, items, type (+1 more)

### Community 183 - "properties"
Cohesion: 0.22
Nodes (9): minimum, type, type, candidates, groups, response_rows, minimum, type (+1 more)

### Community 184 - "subject"
Cohesion: 0.67
Nodes (3): subject, pattern, type

### Community 185 - "PhysicsPlugin"
Cohesion: 0.43
Nodes (3): PhysicsPlugin, Any, test_physics_requires_uncertainty_for_uncertainty_items()

### Community 186 - ".baseQuery"
Cohesion: 0.39
Nodes (4): SecretStore, Any, String, Security

### Community 187 - "sample"
Cohesion: 0.25
Nodes (8): candidates, groups, response_rows, items, sample, additionalProperties, required, type

### Community 188 - "required"
Cohesion: 0.25
Nodes (8): collected_at, collector_role, consent_basis, dataset_id, row_level_data, source, required, specification_version

### Community 189 - "enum"
Cohesion: 0.25
Nodes (8): failed, not_applicable, not_run, passed, enum, additionalProperties, type, gate_results

### Community 190 - "empirical-calibration.schema.json"
Cohesion: 0.25
Nodes (7): additionalProperties, $id, not, anyOf, $schema, title, type

### Community 191 - "_call_name"
Cohesion: 0.38
Nodes (6): Call, _call_name(), parametrize, Path, test_production_pdf_renderers_run_inside_atomic_transactions(), test_shared_family_adapter_owns_atomic_pdf_transaction()

### Community 192 - "build_backend.sh"
Cohesion: 0.29
Nodes (5): MPLCONFIGDIR, PYINSTALLER_CONFIG_DIR, PYTHONPATH, build_backend.sh script, XDG_CACHE_HOME

### Community 193 - "topic_id"
Cohesion: 0.29
Nodes (7): 4.10, 4.12, 4.2, topic_id, enum, title, type

### Community 194 - "enum"
Cohesion: 0.29
Nodes (7): automation, examiner, internal_reviewer, psychometrician, subject_specialist, reviewer_identity_class, enum

### Community 195 - "stratum"
Cohesion: 0.29
Nodes (7): context-incomplete, core, mixed, stratum, enum, title, type

### Community 196 - "model"
Cohesion: 0.29
Nodes (7): digest, name, provider, additionalProperties, required, type, model

### Community 197 - "test_configured_family.py"
Cohesion: 0.62
Nodes (6): _family_syllabus(), Path, _syllabus(), test_aqa_mathematics_preview_covers_pure_mechanics_and_statistics(), test_cambridge_computer_science_preview_covers_theory_and_practical_roles(), test_cambridge_economics_preview_covers_all_official_components()

### Community 198 - "aqa_front_matter_pages"
Cohesion: 0.47
Nodes (4): aqa_front_matter_pages(), Flowable, Shared examiner instructions belong in one introduction, not every section., test_aqa_common_marking_guidance_is_emitted_once_per_scheme()

### Community 200 - "non_comparable_features"
Cohesion: 0.33
Nodes (6): const, additionalProperties, propertyNames, title, type, non_comparable_features

### Community 201 - "test_aqa_accounting_calibration.py"
Cohesion: 0.53
Nodes (4): report(), test_both_papers_pass_multi_seed_automated_checks(), test_external_difficulty_gates_remain_false(), test_reference_evidence_is_aggregate_only()

### Community 202 - "test_aqa_business_calibration.py"
Cohesion: 0.53
Nodes (4): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence()

### Community 203 - "test_difficulty_calibration.py"
Cohesion: 0.53
Nodes (4): report(), test_calibration_retains_no_official_text_or_paths(), test_difficulty_is_not_promoted_without_human_and_psychometric_evidence(), test_every_paper_has_multi_seed_structural_evidence()

### Community 204 - "test_ocr_economics_calibration.py"
Cohesion: 0.53
Nodes (4): report(), test_calibration_retains_only_aggregate_reference_evidence(), test_difficulty_is_not_promoted_without_external_evidence(), test_every_paper_has_multi_seed_structural_evidence()

### Community 206 - "generator_working_directory"
Cohesion: 0.40
Nodes (4): generator_working_directory(), fixture, MonkeyPatch, FixtureRequest

### Community 207 - "xcbuild.sh"
Cohesion: 0.67
Nodes (3): HOME, xcbuild.sh script, usage()

### Community 208 - "capabilities"
Cohesion: 0.50
Nodes (4): items, type, type, capabilities

### Community 212 - "app_board"
Cohesion: 0.67
Nodes (3): minLength, type, app_board

### Community 213 - "app_subject"
Cohesion: 0.67
Nodes (3): minLength, type, app_subject

### Community 214 - "backend_subject"
Cohesion: 0.67
Nodes (3): pattern, type, backend_subject

### Community 215 - "board_profile"
Cohesion: 0.67
Nodes (3): pattern, type, board_profile

### Community 216 - "entry_point"
Cohesion: 0.67
Nodes (3): pattern, type, entry_point

### Community 217 - "id"
Cohesion: 0.67
Nodes (3): pattern, type, id

### Community 218 - "package"
Cohesion: 0.67
Nodes (3): pattern, type, package

### Community 219 - "specification_version"
Cohesion: 0.67
Nodes (3): specification_version, minLength, type

## Knowledge Gaps
- **850 isolated node(s):** `CurriculumVersion`, `BoardLayout`, `examforge-aqa-accounting`, `$schema`, `$id` (+845 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `test_written_diagram_renderer_prints_the_declared_economic_structure()` connect `paths` to `test_aqa_economics.py`, `aqaecongen/render_pdf.py`?**
  _High betweenness centrality (0.119) - this node is a cross-community bridge._
- **Why does `profiles` connect `paths` to `reference-demand-profile.schema.json`?**
  _High betweenness centrality (0.119) - this node is a cross-community bridge._
- **Why does `properties` connect `reference-demand-profile.schema.json` to `paths`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Are the 25 inferred relationships involving `GeneratedQuestion` (e.g. with `AssessmentLLMClient` and `GenerationPolicy`) actually correct?**
  _`GeneratedQuestion` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `ApplicationCoordinator` (e.g. with `PaperCreator` and `.body`) actually correct?**
  _`ApplicationCoordinator` has 20 INFERRED edges - model-reasoned connections that need verification._
- **What connects `CurriculumVersion`, `BoardLayout`, `examforge-aqa-accounting` to the rest of the system?**
  _850 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `document_dsl/__init__.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05963480963480963 - nodes in this community are weakly interconnected._