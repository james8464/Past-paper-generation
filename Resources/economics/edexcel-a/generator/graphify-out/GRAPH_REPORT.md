# Graph Report - Resources/economics/edexcel-a/generator  (2026-07-27)

## Corpus Check
- 52 files · ~120,669 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 643 nodes · 2144 edges · 22 communities (16 shown, 6 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 219 edges (avg confidence: 0.59)
- Token cost: 11,300 input · 4,900 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Blueprint Pipeline|Blueprint Pipeline]]
- [[_COMMUNITY_PDF Layout Rendering|PDF Layout Rendering]]
- [[_COMMUNITY_Domain Models|Domain Models]]
- [[_COMMUNITY_Syllabus Concepts|Syllabus Concepts]]
- [[_COMMUNITY_Question Construction|Question Construction]]
- [[_COMMUNITY_Assessment Content|Assessment Content]]
- [[_COMMUNITY_Interactive Runner|Interactive Runner]]
- [[_COMMUNITY_Exam Dates and Mark Schemes|Exam Dates and Mark Schemes]]
- [[_COMMUNITY_Revision Notes Retrieval|Revision Notes Retrieval]]
- [[_COMMUNITY_Package CLI|Package CLI]]
- [[_COMMUNITY_Fidelity Tests and Renderers|Fidelity Tests and Renderers]]
- [[_COMMUNITY_Case Study Sources|Case Study Sources]]
- [[_COMMUNITY_Model Client Protocol|Model Client Protocol]]
- [[_COMMUNITY_Syllabus Data|Syllabus Data]]
- [[_COMMUNITY_User Generation Flow|User Generation Flow]]
- [[_COMMUNITY_Market Welfare|Market Welfare]]
- [[_COMMUNITY_Business Objectives|Business Objectives]]
- [[_COMMUNITY_Exam Schedule|Exam Schedule]]
- [[_COMMUNITY_Cost Theory|Cost Theory]]
- [[_COMMUNITY_Question Model|Question Model]]
- [[_COMMUNITY_Progress Reporting|Progress Reporting]]

## God Nodes (most connected - your core abstractions)
1. `build_paper_blueprint()` - 126 edges
2. `load_syllabus()` - 114 edges
3. `load_builtin_paper_config()` - 114 edges
4. `Canvas` - 64 edges
5. `str` - 59 edges
6. `str` - 51 edges
7. `float` - 47 edges
8. `Syllabus` - 45 edges
9. `render_question_paper()` - 42 edges
10. `PaperBlueprint` - 39 edges

## Surprising Connections (you probably didn't know these)
- `Edexcel Economics A Syllabus Seed` --conceptually_related_to--> `Indirect Taxation`  [INFERRED]
  Resources/economics/edexcel-a/generator/data/syllabus_seed.json → Resources/economics/edexcel-a/generator/data/notes/text/1.4. Government Intervention.txt
- `Edexcel Economics A Syllabus Seed` --conceptually_related_to--> `Economies and Diseconomies of Scale`  [INFERRED]
  Resources/economics/edexcel-a/generator/data/syllabus_seed.json → Resources/economics/edexcel-a/generator/data/notes/text/3.3. Revenues, Costs and Profits.txt
- `main()` --calls--> `default_output_dir()`  [EXTRACTED]
  generate_paper.py → pastpapergen/cli.py
- `main()` --calls--> `generate_package()`  [EXTRACTED]
  generate_paper.py → pastpapergen/cli.py
- `test_default_output_dir_is_downloads()` --calls--> `default_output_dir()`  [EXTRACTED]
  tests/test_generate_paper_runner.py → pastpapergen/cli.py

## Import Cycles
- None detected.

## Communities (22 total, 6 thin omitted)

### Community 0 - "Blueprint Pipeline"
Cohesion: 0.06
Nodes (122): build_paper_blueprint(), generate_questions_with_ollama(), load_builtin_paper_config(), render_question_paper(), load_syllabus(), validate_blueprint(), test_blueprint_contains_structured_mcq_and_mark_scheme_content(), test_blueprint_is_deterministic_for_seed() (+114 more)

### Community 1 - "PDF Layout Rendering"
Cohesion: 0.08
Nodes (109): Canvas, _answer_line_count(), _axis_labels_for_draw_prompt(), _bar_chart_data(), _bar_label(), _brief_source_evidence(), _calculation_answer_lines(), _cleanup_graph_cache() (+101 more)

### Community 2 - "Domain Models"
Cohesion: 0.10
Nodes (52): BaseModel, GraphParams, MultipleChoiceOption, bool, PaperBlueprint, PaperConfig, Syllabus, GraphParams (+44 more)

### Community 3 - "Syllabus Concepts"
Cohesion: 0.05
Nodes (52): Nature of Economics, Scarcity, Specialisation, Externalities, Market Failure, Public Goods, Measures of Economic Performance, Gross Domestic Product (+44 more)

### Community 4 - "Question Construction"
Cohesion: 0.13
Nodes (51): _best_section_a_context_point(), _build_part(), _build_parts(), _choice_group_name(), _choice_lookup(), _choose_topic(), _compatible_stimulus_kind(), _data_response_extract() (+43 more)

### Community 5 - "Assessment Content"
Cohesion: 0.05
Nodes (49): Profit Maximisation, Revenue Maximisation, Sales Maximisation, Generate Paper Package, Build Paper Blueprint, Economics Exam Question Templates, Indicative Content Builder, Mark Scheme Builder (+41 more)

### Community 6 - "Interactive Runner"
Cohesion: 0.10
Nodes (23): int, main(), _format_elapsed(), PlainProgressReporter, _progress_bar(), progress_reporter(), ProgressSnapshot, ProgressState (+15 more)

### Community 7 - "Exam Dates and Mark Schemes"
Cohesion: 0.17
Nodes (30): date, economics_exam_schedule(), ExamSchedule, formatted_economics_exam_date(), str, _ms_row_height(), render_mark_scheme(), test_edexcel_9ec0_2026_timetable_dates() (+22 more)

### Community 8 - "Revision Notes Retrieval"
Cohesion: 0.22
Nodes (22): _clean_chunk(), essay_capable_topic_ids(), _flush_note_chunk(), _is_exam_point(), _is_note_noise(), _looks_like_heading(), _note_chunks(), note_context_for_topic() (+14 more)

### Community 9 - "Package CLI"
Cohesion: 0.19
Nodes (13): default_output_dir(), generate_package(), main(), _normalise_paper_id(), bool, int, object, Path (+5 more)

### Community 10 - "Fidelity Tests and Renderers"
Cohesion: 0.17
Nodes (18): Edexcel Reference Layout System, Mark Scheme Renderer, Edexcel PDF Rendering Module, Question Paper Renderer, Source Booklet Renderer, JSON Syllabus Loader, Deterministic Paper Blueprint Specification, Edexcel 9EC0 Exam Schedule Specification (+10 more)

### Community 11 - "Case Study Sources"
Cohesion: 0.39
Nodes (11): _article_length_extract(), data_response_extract(), _is_macro_title(), _macro_fallback(), _micro_fallback(), _normalise(), bool, int (+3 more)

### Community 13 - "Syllabus Data"
Cohesion: 0.50
Nodes (3): qualification, source, topics

### Community 14 - "User Generation Flow"
Cohesion: 0.67
Nodes (4): Interactive Paper Generator Runner, Paper Package Workflow Specification, Interactive Runner Specification, Generation Progress Reporting Specification

### Community 15 - "Market Welfare"
Cohesion: 0.67
Nodes (3): Consumer and Producer Surplus, Market Equilibrium, Price Mechanism

## Knowledge Gaps
- **47 isolated node(s):** `int`, `int`, `float`, `int`, `str` (+42 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `build_paper_blueprint()` connect `Blueprint Pipeline` to `Domain Models`, `Question Construction`, `Exam Dates and Mark Schemes`, `Revision Notes Retrieval`, `Package CLI`?**
  _High betweenness centrality (0.186) - this node is a cross-community bridge._
- **Why does `generate_package()` connect `Package CLI` to `Blueprint Pipeline`, `PDF Layout Rendering`, `Interactive Runner`, `Exam Dates and Mark Schemes`?**
  _High betweenness centrality (0.116) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Canvas` (e.g. with `GraphParams` and `PaperBlueprint`) actually correct?**
  _`Canvas` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `str` (e.g. with `GraphParams` and `PaperBlueprint`) actually correct?**
  _`str` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `int`, `int`, `float` to the rest of the system?**
  _47 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Blueprint Pipeline` be split into smaller, more focused modules?**
  _Cohesion score 0.06080707573244887 - nodes in this community are weakly interconnected._
- **Should `PDF Layout Rendering` be split into smaller, more focused modules?**
  _Cohesion score 0.07773144286905755 - nodes in this community are weakly interconnected._