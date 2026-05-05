# Graph Report - Economics Past Paper Generator  (2026-05-05)

## Corpus Check
- 48 files · ~99,399 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 287 nodes · 502 edges · 24 communities detected
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 8 edges (avg confidence: 0.6)
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `Uploaded notes system` - 26 edges
2. `build_paper_blueprint()` - 18 edges
3. `_wrap()` - 14 edges
4. `_draw_section_a_question()` - 13 edges
5. `_draw_question_pages()` - 11 edges
6. `render_source_booklet()` - 10 edges
7. `Blueprint generator` - 10 edges
8. `_pdf_text()` - 9 edges
9. `generate_package pipeline` - 9 edges
10. `_build_part()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `generate_package pipeline` --loads--> `Syllabus seed JSON`  [EXTRACTED]
  pastpapergen/cli.py → data/syllabus_seed.json
- `Blueprint generator` --uses topic pools--> `Syllabus seed JSON`  [EXTRACTED]
  pastpapergen/generator.py → data/syllabus_seed.json
- `1.1. Nature of Economics` --feeds context to--> `Uploaded notes system`  [EXTRACTED]
  data/notes/text/1.1. Nature of Economics.txt → pastpapergen/notes.py
- `1.2. How Markets Work` --feeds context to--> `Uploaded notes system`  [EXTRACTED]
  data/notes/text/1.2. How Markets Work.txt → pastpapergen/notes.py
- `1.3. Market Failure` --feeds context to--> `Uploaded notes system`  [EXTRACTED]
  data/notes/text/1.3. Market Failure.txt → pastpapergen/notes.py
- `1.4. Government Intervention` --feeds context to--> `Uploaded notes system`  [EXTRACTED]
  data/notes/text/1.4. Government Intervention.txt → pastpapergen/notes.py
- `2.1. Measures of Economic Performance` --feeds context to--> `Uploaded notes system`  [EXTRACTED]
  data/notes/text/2.1. Measures of Economic Performance.txt → pastpapergen/notes.py
- `2.2. Aggregate Demand` --feeds context to--> `Uploaded notes system`  [EXTRACTED]
  data/notes/text/2.2. Aggregate Demand.txt → pastpapergen/notes.py

## Communities

### Community 0 - "render_pdf.py / _answer_line_count()"
Cohesion: 0.07
Nodes (67): _answer_line_count(), _draw_answer_lines(), _draw_answer_lines_until(), _draw_bar_chart(), _draw_blank_answer_axes(), _draw_boxes(), _draw_context_box(), _draw_continuation_lines() (+59 more)

### Community 1 - "generator.py / build_paper_blueprint()"
Cohesion: 0.14
Nodes (32): build_paper_blueprint(), _build_part(), _build_parts(), _choice_group_name(), _choice_lookup(), _choose_topic(), _data_response_extract(), _essay_question_prompt() (+24 more)

### Community 2 - "1.1. Nature of Economics / 1.2. How Markets Work"
Cohesion: 0.16
Nodes (24): 1.1. Nature of Economics, 1.2. How Markets Work, 1.3. Market Failure, 1.4. Government Intervention, 2.1. Measures of Economic Performance, 2.2. Aggregate Demand, 2.3. Aggregate Supply, 2.4. National Income (+16 more)

### Community 3 - "Audit JSON / PaperBlueprint"
Cohesion: 0.13
Nodes (21): Audit JSON, PaperBlueprint, generate_package pipeline, Essay-capable topic guard, Blueprint generator, Mark scheme PDF, Ollama LLM enrichment, Paper 1 (+13 more)

### Community 4 - "test_render_pdf.py / _first_page_containing()"
Cohesion: 0.16
Nodes (12): _first_page_containing(), _pdf_page_count(), _pdf_text(), test_paper_1_render_uses_question_specific_pages(), test_paper_1_section_b_intro_matches_reference_wording(), test_paper_1_section_b_prompt_page_lists_subquestions_with_marks(), test_paper_1_section_b_starts_near_reference_page(), test_section_a_context_uses_specific_source_text() (+4 more)

### Community 5 - "BaseModel / models.py"
Cohesion: 0.25
Nodes (10): BaseModel, MultipleChoiceOption, PaperBlueprint, PaperConfig, QuestionBlueprint, QuestionPart, SectionConfig, Syllabus (+2 more)

### Community 6 - "test_ollama_generation.py / DriftedPartsOllamaClient"
Cohesion: 0.23
Nodes (9): DriftedPartsOllamaClient, FakeOllamaClient, NoisyOllamaClient, test_generate_questions_with_ollama_cleans_essay_and_draw_prompt_drift(), test_generate_questions_with_ollama_keeps_source_and_mark_scheme(), test_generate_questions_with_ollama_preserves_fallback_mark_schemes_when_llm_returns_empty_lists(), test_generate_questions_with_ollama_rejects_drifted_section_b_wording(), test_generate_questions_with_ollama_reports_question_progress() (+1 more)

### Community 7 - "ollama_client.py / build_question_prompt()"
Cohesion: 0.33
Nodes (10): build_question_prompt(), _clean_prompt(), generate_questions_with_ollama(), _matches_expected_question_style(), _merge_part_prompt(), _merge_parts(), _merge_question_text(), _merge_source_text() (+2 more)

### Community 8 - "test_question_styles.py / test_choice_pairs_do_not_repeat_topic_for_seed_that_would_duplicate()"
Cohesion: 0.18
Nodes (0): 

### Community 9 - "notes.py / _clean_chunk()"
Cohesion: 0.38
Nodes (8): _clean_chunk(), note_context_for_topic(), note_file_for_topic(), note_points_for_topic(), _note_prefix(), _note_text(), _ranked_note_chunks(), _search_terms()

### Community 10 - "test_mark_scheme_layout.py / _pdf_page_count()"
Cohesion: 0.46
Nodes (7): _pdf_page_count(), _pdf_text(), test_mark_scheme_has_subquestion_tables_mcq_explanations_and_levels(), test_mark_scheme_includes_question_specific_focus_and_answer_points(), test_mark_scheme_mcq_explanations_are_option_specific(), test_mark_scheme_uses_reference_style_sections(), test_mark_scheme_uses_uploaded_note_points_for_extended_questions()

### Community 11 - "generate_paper.py / main()"
Cohesion: 0.29
Nodes (0): 

### Community 12 - "cli.py / default_output_dir()"
Cohesion: 0.6
Nodes (5): default_output_dir(), generate_package(), main(), _normalise_paper_id(), _write_audit()

### Community 13 - "test_source_booklet.py / _pdf_page_count()"
Cohesion: 0.47
Nodes (4): _pdf_page_count(), _pdf_text(), test_source_booklet_for_paper_1_only_uses_section_b(), test_source_booklet_has_figure_extracts_and_source_attributions()

### Community 14 - "test_blueprint.py / test_blueprint_contains_structured_mcq_and_mark_scheme_content()"
Cohesion: 0.4
Nodes (0): 

### Community 15 - "test_validation.py / test_validate_blueprint_accepts_generated_paper()"
Cohesion: 0.4
Nodes (0): 

### Community 16 - "test_cli.py / test_cli_dry_run_creates_paper_package()"
Cohesion: 0.5
Nodes (0): 

### Community 17 - "test_notes.py / test_note_context_and_points_are_relevant_to_topic()"
Cohesion: 0.67
Nodes (0): 

### Community 18 - "test_ollama_prompt.py / test_ollama_prompt_includes_uploaded_notes_context_for_topic()"
Cohesion: 0.67
Nodes (0): 

### Community 19 - "test_paper_configs.py / test_paper_1_matches_core_edexcel_structure()"
Cohesion: 0.67
Nodes (0): 

### Community 20 - "test_syllabus.py / test_load_seed_syllabus_has_theme_topics()"
Cohesion: 0.67
Nodes (0): 

### Community 21 - "__init__.py / A-Level Economics A practice paper generator."
Cohesion: 1.0
Nodes (1): A-Level Economics A practice paper generator.

### Community 22 - "syllabus.py / load_syllabus()"
Cohesion: 1.0
Nodes (0): 

### Community 23 - "__main__.py"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **5 isolated node(s):** `A-Level Economics A practice paper generator.`, `Random run seed`, `Essay-capable topic guard`, `Mark scheme PDF`, `Audit JSON`
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `__init__.py / A-Level Economics A practice paper generator.`** (2 nodes): `__init__.py`, `A-Level Economics A practice paper generator.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `syllabus.py / load_syllabus()`** (2 nodes): `syllabus.py`, `load_syllabus()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `__main__.py`** (1 nodes): `__main__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Blueprint generator` connect `Audit JSON / PaperBlueprint` to `1.1. Nature of Economics / 1.2. How Markets Work`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **What connects `A-Level Economics A practice paper generator.`, `Random run seed`, `Essay-capable topic guard` to the rest of the system?**
  _5 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `render_pdf.py / _answer_line_count()` be split into smaller, more focused modules?**
  _Cohesion score 0.07 - nodes in this community are weakly interconnected._
- **Should `generator.py / build_paper_blueprint()` be split into smaller, more focused modules?**
  _Cohesion score 0.14 - nodes in this community are weakly interconnected._
- **Should `Audit JSON / PaperBlueprint` be split into smaller, more focused modules?**
  _Cohesion score 0.13 - nodes in this community are weakly interconnected._