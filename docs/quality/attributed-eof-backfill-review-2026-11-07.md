# Attributed bounded EOF review backfill, 7 November 2026

This aggregates prior explicitly complete source/test reads, not a fresh EOF
review by the metadata author. All 95 candidate source hashes and line counts
were rechecked against CAPACITY after rebase at
`e86db8cc7dc5a7f44f42aa7919aba65f867fe7a3` / tree
`4c25be0bf6fa955f01c894068ee65cc86506eafc`. All match: no composite
194 fixture-delta attribution or historical-blob substitution is needed.

The 95 rows (62 maintained sources, 33 tests) are proposed for their bounded
file-level reviews only. Each row binds current bytes, actual line count and a
specific positive complete-EOF item in a pinned earlier receipt. Passing tests,
formatting, inventory, filename matches and scoped dependency spans are not EOF
proof. Existing unrelated attestations and current-headroom reviews are preserved.

Method **P** means prior complete-file semantic source/test read explicitly
enumerated at the cited receipt position, followed by this exact-byte/line-count
recheck; it does not mean a fresh full read. **R#** identifies the pinned receipt
below; the suffix is its JSON pointer, not an inferred read span. Where a receipt
records contiguous read ranges, those remain in that item. Some explicitly
complete collections do not record finer ranges; none are fabricated here.

## Receipt provenance

Earlier receipts are retained under the ignored ROOT `tmp/` directory. Their
explicit complete source/test collections, not incidental mentions or recursive
dependency inventories, supply the positive EOF attribution.

| ID | Receipt | SHA-256 |
| --- | --- | --- |
| R1 | `nov7-entrypoint-eof-audit-batch2.json` | `a2605a3a90203c4ef601f9bb63906a2db38463b595e104f58fbe235ca2e47476` |
| R2 | `nov7-entrypoint-eof-audit.json` | `a8f5022bc92e87874219c7cc0b21563dbd17bdc83b3d7b2dd00ab2cafed4d58c` |
| R3 | `nov7-french-boundary-eof-audit-batch2.json` | `a64c2ca9e62bb0f2aa0d23fc84c0545a6ae98c532e06d03ac5317811b10e0253` |
| R4 | `nov7-french-boundary-eof-audit-medium2.json` | `d83a625e73ae6c02ac1c817edfbffb5179897305007dc3dbe4b197899ef29524` |
| R5 | `nov7-french-medium-boundary-eof-audit.json` | `be1a1037bd5b5df9964dffc1227647766cecfad684b4c1175ab3c7a816a0039d` |
| R6 | `nov7-french-small-boundary-eof-audit.json` | `53ad17e73a7d63535acf677fe6bdd0753f1ad4a98498283be3c77807e9a8e50c` |
| R7 | `nov7-french-teacher-review-eof-audit.json` | `f9c0758df784e5395c2ce1cd8f8f56d4ffffd4589532effff81f47cf2a024e21` |

## Exact-current complete-file rows

All rows use method P. Test reads inspect assertions only; their execution is
not claimed here. French retained finite families/contracts are not evidence of
novel current V36 content, official equivalence, learner timing, teacher approval
or empirical qualification. Wrapper/syllabus/date reads do not certify all
downstream behavior, official dates or syllabus semantics. The second entrypoint
batch inspected bounded active/optional/developer roles, not full subjects.

| Path | Lines | Current SHA-256 | Positive EOF position | Scope |
| --- | ---: | --- | --- | --- |
| `Resources/business/aqa/generator/aqabizgen/cli.py` | 92 | `0df49e3d1b36160b43a4977feef86fcebefc51dae5d9f78f25c797d2f4f79dd2` | R2`/files/0` | entrypoint leaf; downstream scope partial |
| `Resources/computer-science/aqa/generator/cspapergen/__main__.py` | 7 | `79aa6f72a41646c490c844e25c4b654dfc470cad0afe8eb43f9182305c3f9c07` | R2`/files/1` | entrypoint leaf; downstream scope partial |
| `Resources/computer-science/aqa/generator/cspapergen/exam_dates.py` | 29 | `ba10fa492a08ee357ab9db6db5cd971dbcfaf69b81b7a12a484f821d3f3bb58e` | R2`/files/2` | named source module; scoped callers only |
| `Resources/computer-science/aqa/generator/cspapergen/syllabus.py` | 17 | `6e1eb15a211d811f4a93a80da755b27a14bb87d293df39407bc6f49793cbeb26` | R2`/files/3` | named source module; scoped callers only |
| `Resources/computer-science/ocr/generator/ocrcsgen/cli.py` | 79 | `3b3b7921f0e14e03a316c16d39e77d9fa5d8459a36022a35628d294c40f21a40` | R2`/files/4` | entrypoint leaf; downstream scope partial |
| `Resources/computer-science/ocr/generator/ocrcsgen/syllabus.py` | 35 | `1e1d568e05b482e8b8de59b41d03f357693147a10d6cfb459d83fa5c6ed8c89b` | R2`/files/5` | named source module; scoped callers only |
| `Resources/configured-generators/generator/configuredgen/models.py` | 87 | `2ab369fce8f42ddb439fea48460a847f276f90ead1dc970f6e256654b1b13e54` | R2`/files/6` | named source module; scoped callers only |
| `Resources/economics/edexcel-a/generator/keldin_edexcel/__main__.py` | 4 | `0fe3d271d438f7d02aa15a386ba2d8cc936cde4feddbe377f6d3df98e28462f0` | R2`/files/7` | entrypoint leaf; downstream scope partial |
| `Resources/economics/edexcel-a/generator/keldin_edexcel/cli.py` | 5 | `c2728de673c8b70292f24674e9a9eab798c273a36dc99a065e127593685fb553` | R2`/files/8` | entrypoint leaf; downstream scope partial |
| `Resources/economics/edexcel-a/generator/pastpapergen/__main__.py` | 5 | `bf22d34cdcbc8ee456ab69233d66eac5abe9bec9e4a7561a7c5750f065180d6f` | R2`/files/9` | entrypoint leaf; downstream scope partial |
| `Resources/economics/edexcel-a/generator/pastpapergen/exam_dates.py` | 34 | `8f80bdb8e2ee4a39fc720e49408bdf905a35a3f03a02620021c850c083ac7a54` | R2`/files/10` | named source module; scoped callers only |
| `Resources/economics/edexcel-a/generator/pastpapergen/syllabus.py` | 13 | `ada6fa2e89d7083667f1734848b250434a7b29747be6ce92a2850970af6b0bb1` | R2`/files/11` | named source module; scoped callers only |
| `Resources/computer-science/aqa/generator/cspapergen/objective_calibration.py` | 178 | `0a1caa8775649d83d991bf90410f6c09680c9fe8c91b71fe44a4e003f119dfe6` | R1`/complete_source_eof/1` | named source module; scoped callers only |
| `Resources/computer-science/aqa/generator/cspapergen/validation.py` | 208 | `895af20afb237bcd6daf2617cbb9b1880a06acf7a12b77e2a4ac35828443e08e` | R1`/complete_source_eof/2` | named source module; scoped callers only |
| `Resources/computer-science/ocr/generator/ocrcsgen/configs.py` | 272 | `7009fa424625b1ceeddcaaa84751369751a0ee1b7c642e3545e3bcdd82123add` | R1`/complete_source_eof/3` | named source module; scoped callers only |
| `Resources/computer-science/ocr/generator/ocrcsgen/task_calibration.py` | 338 | `6482091750bebfb39eaafaecc0930abba4bd400d58448e4a05a243b0fbb6066c` | R1`/complete_source_eof/4` | named source module; scoped callers only |
| `Resources/economics/edexcel-a/generator/pastpapergen/notes.py` | 216 | `9dda4594eabbd445b7d675c4dc855099578a2970d89e073f4ec80a615a12b1ed` | R1`/complete_source_eof/6` | named source module; scoped callers only |
| `Resources/economics/edexcel-a/generator/pastpapergen/selection_contracts.py` | 171 | `c71596f2f491eb9134d3d3acd93f15241018020f5e4f12dde00b960459f323c5` | R1`/complete_source_eof/7` | named source module; scoped callers only |
| `Resources/economics/edexcel-a/generator/pastpapergen/source_credit.py` | 202 | `06fcabdd4817a5deb13e24f6e7faa04dcd4ac206f4017bdf81e85bb7a66b08d9` | R1`/complete_source_eof/8` | named source module; scoped callers only |
| `Resources/economics/edexcel-a/generator/pastpapergen/stimulus_data.py` | 142 | `d4a112d5c1b0d2acfbd094bf60a531ef7b4913f88d30ce9eff837a645ea87fb3` | R1`/complete_source_eof/9` | named source module; scoped callers only |
| `macOS/scripts/export_app_icon.py` | 100 | `eb6c733e8af6826d4d9ad4fe622879545e50efe746eb57a6de851e8565ff38dc` | R1`/complete_source_eof/10` | developer tool; not live generation |
| `tools/aqa_accounting_calibration.py` | 239 | `09533c86df1e4de8a19b8f3f83d177844e3683c21f9533d77596fd000f266433` | R1`/complete_source_eof/11` | developer tool; not live generation |
| `Backend/Core/france/archetypes.py` | 248 | `ab07d50e072bfcc8a3e2f90dd58fe0049815977a3a97d0bbdec6c7ed2b16b5fa` | R3`/sources/0` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/database_depth_contract.py` | 250 | `9572553c328328c36c3696df97c550ab78f0f12be39a828a3c11f8120c3246c0` | R3`/sources/1` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/database_depth_prose.py` | 300 | `fd08a424761d9070c07033eafc8df1ee312c3cac8e8126823cfeec555f15c330` | R3`/sources/2` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/database_reconciliation_contract.py` | 260 | `848f5af9af331cddf0d9f34132072bf7284999fc086f339a54434cdd6266e604` | R3`/sources/3` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/expression_exercise.py` | 257 | `98c4701101aebafc2aa075f9287a26c819a9dca794d7bea7e3543598003013d3` | R3`/sources/4` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/expression_synthesis.py` | 136 | `483ef1415d08b59d9b18d0d0e7a7a8f4ac3b0db69b1f0c9d941b6994568d3388` | R3`/sources/5` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/graph_resilience_authoring.py` | 157 | `b4e8cbae0666ebf566edf0b3bdaf5f96415db73efc97efa6a03d145716adcaeb` | R3`/sources/6` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/graph_resilience_contract.py` | 102 | `4cba6c3120779174771ef0abaf520280264aec58317bebe4b830983d83c91dd8` | R3`/sources/7` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/graph_route_trace_authoring.py` | 161 | `eab4c0059106526b1c40f3d5f1c5e20d98e00694564ce92fb2d1dcfe7cc2edfd` | R3`/sources/8` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/graph_route_trace_contract.py` | 114 | `5417e572682b45732e1c495042ac4002c9d9077711aedc55248d7698a1e7f864` | R3`/sources/9` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/graph_route_trace_prose.py` | 226 | `0f341b0111e3e6aa4e77984d0e6d0f41ffa5cf58b0f89ff14b0d68c2d78f6977` | R3`/sources/10` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/graph_tree_binding.py` | 249 | `cba1ba6a63a8792a78a7b5fa831395385604006c9d0882092580c1e489b5384f` | R3`/sources/11` | French boundary/owned-domain source; no live-quality claim |
| `tests/test_french_database_depth_contract.py` | 110 | `683f9d3bf1acf73bc40acebb59b49af78e0c1e71778f18cce57d4eda0fb88161` | R3`/tests/0` | test assertions; not executed |
| `tests/test_french_database_reconciliation_contract.py` | 92 | `a6dfb0a2c936e0f9a968b4cd6edb669dad8faf67490f3b0397a17ae8a6475e5a` | R3`/tests/1` | test assertions; not executed |
| `tests/test_french_expression_synthesis.py` | 106 | `537aa529ea782408ff494c7dbe1713b377c028b3cf8ef31d9c0e71b7ef120833` | R3`/tests/2` | test assertions; not executed |
| `tests/test_french_expression_exercise.py` | 187 | `1d77f0fff0d5e9637bbf3120c4a437fe0f7f614e4644850c5fc6c388b4742afa` | R3`/tests/3` | test assertions; not executed |
| `tests/test_french_graph_resilience_contract.py` | 77 | `a90ec67656527e8a546a1d1bbbae5d31dc7601db72932f59beec36aaae17d6db` | R3`/tests/4` | test assertions; not executed |
| `tests/test_french_graph_resilience_authoring.py` | 141 | `4634b945e9f6c880f2acb92c70f7ea3280f3056a3c81ae1025e0bc5cdaab71ec` | R3`/tests/5` | test assertions; not executed |
| `tests/test_french_graph_route_trace_contract.py` | 123 | `fffa5c0f1dbf515647f29872931768eb75109847ea48767a06b7997b6fc83f37` | R3`/tests/6` | test assertions; not executed |
| `tests/test_french_graph_route_trace_authoring.py` | 114 | `d6b720e84558f915612bb128fcd50cfd9da15b01dcbba58d886c964d27503445` | R3`/tests/7` | test assertions; not executed |
| `tests/test_french_graph_route_trace_prose.py` | 153 | `a4508fc7a0dea45ca7666ed72680920d3f515750abf0087f489e0932575447d7` | R3`/tests/8` | test assertions; not executed |
| `Backend/Core/france/database_audit_prose.py` | 347 | `c0efb403b19fa775c9b122158bc2a4649abc1240064472ddbb9176939dbf317e` | R4`/complete_source_eof/0` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/database_case_families.py` | 438 | `1ccf39018b1d3f21b0e3e09202988864bdcd59e3e94fd8a0c447b47ff7d530ac` | R4`/complete_source_eof/1` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/database_case_prose.py` | 540 | `015122b7859f79ff13ec650a9c18e34a6e4622d4ed053dfd9092f0b8cc806250` | R4`/complete_source_eof/2` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/database_reasoning_prose.py` | 341 | `aabae91a6d1de77235562131955b67e9d04b0ce0fe849184e2a8eceb4f28cf31` | R4`/complete_source_eof/3` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/database_reconciliation_prose.py` | 372 | `55bf5d092ce119376eda72258febf8fd5867923159d2f6426179dc17a8cfb409` | R4`/complete_source_eof/4` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/expanded_pipeline.py` | 309 | `f8859f0189e6726e4c3d5ffe026a90bd4875eff222b325ee308fa1e8b2612742` | R4`/complete_source_eof/5` | French boundary/owned-domain source; no live-quality claim |
| `tests/test_french_database_audit_prose.py` | 151 | `1f63ced56a58e4e811e155b5f778d8f057454bf96673e856861fb59f6319898d` | R4`/complete_test_eof_read_not_run/0` | test assertions; not executed |
| `tests/test_french_database_reasoning_prose.py` | 119 | `0d6231363aa528f43319529b15371f25814a5f1b4d90671505c369b709946809` | R4`/complete_test_eof_read_not_run/1` | test assertions; not executed |
| `tests/test_french_database_reconciliation_prose.py` | 159 | `169dab6cfb38f2ba5892b2e188d61e770ccd2e33b78e50a70bf04230af1a8060` | R4`/complete_test_eof_read_not_run/2` | test assertions; not executed |
| `tests/test_french_expanded_family.py` | 56 | `877cb3aff45b4e603b905147df6a1b4ac29934a153eb8a01faca792ce62615a0` | R4`/complete_test_eof_read_not_run/3` | test assertions; not executed |
| `tests/test_french_expanded_pipeline.py` | 209 | `5a861322659d1ae11996c52c15c48ba956957b1e469c35bbc91c171e97380882` | R4`/complete_test_eof_read_not_run/4` | test assertions; not executed |
| `Backend/Core/france/allocation_exercise.py` | 126 | `2aaf41cf0b0e3b8627562e5f2fad9a3de5190daa01064d53f641ffe0aeb4303a` | R5`/source_eof/0` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/channel_exercise.py` | 142 | `0c4766a2222f10b88b01b2e58adf62a802e1a6a6921898d8ffd5796c907ce1b0` | R5`/source_eof/1` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/database_audit_authoring.py` | 157 | `bad76bed175d3fa5e8c9fbde75267b9eef2afea7bcd11343953af2281546ebd6` | R5`/source_eof/2` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/database_audit_contract.py` | 220 | `5dfe67cca156f075fc5249214ca74c32661693a25e9299532e52121520127b15` | R5`/source_eof/3` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/database_authoring.py` | 197 | `731c85ba4fb667ce60ffb4f309a97275c2589f0f7070ca502313531003bc8b56` | R5`/source_eof/4` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/database_construction_authoring.py` | 182 | `be31eb820467d0747761cd44446c29025241fc5e5d4106ecc7b4fc34a6cd9feb` | R5`/source_eof/5` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/database_depth_authoring.py` | 207 | `9a0c3fdda0b1f1a03a7eedc683b66badc2f4281170aa7f45dd01a0b7a54599c8` | R5`/source_eof/6` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/database_reasoning_authoring.py` | 157 | `3d1da4ec6e1519057e06b5b49e28d4c137dd37686c88e7ee485915b41e3ef206` | R5`/source_eof/7` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/database_reconciliation_authoring.py` | 181 | `599ae16237bfbae373ff9e27f780b91ba7496ab48d31494e15911d581ee703d8` | R5`/source_eof/8` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/directory_exercise.py` | 145 | `a69a371d25f8afac8feac22cb6bc36960e5d43656ce9344599e9a60cc3c9a941` | R5`/source_eof/9` | French boundary/owned-domain source; no live-quality claim |
| `tests/test_french_allocation_exercise.py` | 32 | `a8c34a95755b3f334324d53af2a52b63de1fad876530571305d4010d1739da23` | R5`/complete_test_eof_read_not_executed/0` | test assertions; not executed |
| `tests/test_french_channel_exercise.py` | 19 | `c35bfb5d7484a93ed04c672165474b8104e1f6e56110e533f433498c7fbd31fb` | R5`/complete_test_eof_read_not_executed/1` | test assertions; not executed |
| `tests/test_french_directory_exercise.py` | 47 | `facd22e8cebeb8dda675dc31ba96eb5d96be6ab906458cad5f36f06aa04d07a6` | R5`/complete_test_eof_read_not_executed/2` | test assertions; not executed |
| `tests/test_french_database_audit_authoring.py` | 139 | `3937637484e4b0d186ff6921d52e38a8080b99e438bcec5d3f2e1836309e7ea0` | R5`/complete_test_eof_read_not_executed/3` | test assertions; not executed |
| `tests/test_french_database_audit_contract.py` | 119 | `c182c25517761fd3000c1bee192f82f599ee948b59282f874e4104b382faf360` | R5`/complete_test_eof_read_not_executed/4` | test assertions; not executed |
| `tests/test_french_database_authoring.py` | 157 | `e33c558299734ef961e77ee2365dab6ded01dc22e44da25561e5a75b665b01f5` | R5`/complete_test_eof_read_not_executed/5` | test assertions; not executed |
| `tests/test_french_database_reasoning_authoring.py` | 85 | `7fbee424d4aa26b10b900d4694b89143d89c617d6fd567c136de3add611b7cf0` | R5`/complete_test_eof_read_not_executed/6` | test assertions; not executed |
| `tests/test_french_database_reconciliation_authoring.py` | 101 | `3e592298fb7a3bbb01762735232c34e94f0af1154003d5124fbfdd258821368b` | R5`/complete_test_eof_read_not_executed/7` | test assertions; not executed |
| `tests/test_french_database_construction.py` | 147 | `24b4e00593400c2b0b9b5d288264c3a0080f18a3aa378f7b25de7cf9f4500ac5` | R5`/complete_test_eof_read_not_executed/8` | test assertions; not executed |
| `Backend/Core/france/allocation_case.py` | 74 | `55cafddf51720faf9cd49cbaf71cc2aace02d69f36a459339fc7ba3b27739f88` | R6`/sources/0` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/channel_case.py` | 68 | `f557de4f9432de077487d94e92f389389699004769522d288dda04f813b7e0bc` | R6`/sources/1` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/database_binding.py` | 74 | `883bf6f2d22c7fd5196e3acbdbe16527a6b47f81be2251047e2cdf8c633987b4` | R6`/sources/2` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/database_case_authoring.py` | 76 | `65c5ae44547e0df9554a819425b3941c39a69953e2a013f5620f8227f333722c` | R6`/sources/3` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/database_curriculum_prose.py` | 97 | `38a392592d910b6bda3c757b5aa3ebd7bf972962625b1f84f4f6f185dae09398` | R6`/sources/4` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/directory_case.py` | 77 | `1c86cc07bad41cdaf3d6e6ce941da1cbd70f5ff02368f380a6ca55bad8191915` | R6`/sources/5` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/expression_stack.py` | 86 | `03a85c4eca16d9064bd67fd125f1f4cb9235decceebb37190d17269f58e7c2aa` | R6`/sources/6` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/graph_two_outage_contract.py` | 79 | `e7cfb2bdcb94614b4d10e72e3c9f58c651cd9b2f8ad04ef2831c5b4e759b2db9` | R6`/sources/7` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/network_binding.py` | 73 | `b0fdfff462dd62364d3b1cfedb7871b7b2ae3fc5194a7b30e134cb761fe41d52` | R6`/sources/8` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/network_incident_timeline_contract.py` | 76 | `cb339782a75cbfe14496c0c3855913c88f856aed9e0a784974a1da48c39f38e4` | R6`/sources/9` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/round_robin_case.py` | 79 | `778c5a73926e145ec7073a210d84ab19a2df5951e2e21e7317b093260ad667e4` | R6`/sources/10` | French boundary/owned-domain source; no live-quality claim |
| `Backend/Core/france/system_case_authoring.py` | 72 | `0a23803da75193a59951436f2e9bec7cdb617264342c8a5a66ca0529f0267220` | R6`/sources/11` | French boundary/owned-domain source; no live-quality claim |
| `tests/test_french_allocation_case.py` | 94 | `711999cca876033d9ba5118d3a1a9eee0b5fd2582c5825dc613f8e310ee25787` | R6`/tests/0` | test assertions; not executed |
| `tests/test_french_channel_case.py` | 126 | `9949ce44f8213273ab6b89e57b4d4510e31a3fd881420b957a3238b5e918b862` | R6`/tests/1` | test assertions; not executed |
| `tests/test_french_database_curriculum.py` | 50 | `c4cc416ac71caa28b29b59abb214c2a546cd847b6becc2836353649cb5c02e72` | R6`/tests/2` | test assertions; not executed |
| `tests/test_french_directory_case.py` | 134 | `a193e783e58214de0226a6710109614863f9789024b0cf3e7da9664b422f207c` | R6`/tests/3` | test assertions; not executed |
| `tests/test_french_expression_stack.py` | 90 | `f46a6a2c4c8fa0ac17cd3a8f0228a3873c7d4187727d45afac6c241d9f829452` | R6`/tests/4` | test assertions; not executed |
| `tests/test_french_round_robin_case.py` | 130 | `5f1bd449057c410e27cba69943748a9f48cf129a23d44bf0d86041f53774632f` | R6`/tests/5` | test assertions; not executed |
| `tests/test_french_graph_two_outage_contract.py` | 113 | `b193f40421b2b8e39508b0ab3f104eca21de3975d8fff19f4b392472ab698a89` | R6`/tests/6` | test assertions; not executed |
| `tests/test_french_network_incident_timeline_contract.py` | 89 | `067e469202b951c067942041795a18476b239d6730461a14e7115bab5bf1cc4c` | R6`/tests/7` | test assertions; not executed |
| `tests/test_french_database_case_authoring.py` | 140 | `9d22ec2c7df8d09d00d73dc4f3dc00389ab23fb493d9b66f20c526251cedd1fd` | R6`/tests/8` | test assertions; not executed |
| `tests/test_french_system_case_authoring.py` | 54 | `1aad660d6dcc4e90d86fc40eb54a93a2cf97e9e2abf30da7a4f439c5deaa3af3` | R6`/tests/9` | test assertions; not executed |

## Held evidence: no promotion

- `Backend/Core/france/teacher_review.py` and `tests/test_french_review.py`:
  exact earlier EOF evidence exists, but the deferred low repeat-submission
  collision remains open. Existing self-attested teacher/empirical `not_run`
  status is unchanged; no approval is fabricated.
- `Resources/configured-generators/generator/configuredgen/render_pdf.py`:
  Cambridge-only cover branding remains a caveat for unadvertised AQA Mathematics.
  Keep pending; this is not established as an ordinary advertised-native defect.
- `Resources/computer-science/aqa/generator/cspapergen/notes.py`: old 115-line
  `9dd9a966…` EOF evidence cannot bind the repaired 138-line current source.
  The new source is reviewed separately below, not promoted through stale proof.
- All 18 exact-pinned scoped-only paths listed below remain pending. A matching
  source hash does not convert partial reads into complete-file review.

- `Backend/Core/france/database_contract.py`
- `Backend/Core/france/database_prose.py`
- `Backend/Core/france/extended_pipeline.py`
- `Backend/Core/france/graph_resilience_prose.py`
- `Backend/Core/france/graph_tree_depth_contract.py`
- `Backend/Core/france/network_contract.py`
- `Backend/Core/france/network_prose.py`
- `Backend/Core/france/pipeline.py`
- `Backend/Core/france/postfix_exercise.py`
- `Backend/Core/france/round_robin_exercise.py`
- `Backend/Core/france/runtime.py`
- `Backend/Core/france/synthesized_authoring.py`
- `Backend/Core/france/synthesized_pipeline.py`
- `Backend/Core/france/tree_case_families.py`
- `Resources/computer-science/aqa/generator/cspapergen/cli.py`
- `Resources/economics/edexcel-a/generator/pastpapergen/generator.py`
- `tests/test_french_database_depth_authoring.py`
- `tests/test_nsi_pipeline.py`

## Separately reviewed optional-notes repair

Current `cspapergen/notes.py` is 138 lines, SHA-256
`09d5b7817df75f320aab81f2f9678d3e68985bb023428bfd4a353bae78b59dff`;
`tests/test_cs_notes_cache_integrity.py` is 189 lines, SHA-256
`3d8b3b9eca6dcc0d2453a1bf6a914f8ff65293d96536c4f62eaa849708cc1370`.
These two rows bind instead to the unchanged 60-line tracked note
`docs/quality/cs-notes-cache-integrity-review-2026-11-07.md`, SHA-256
`507e482695053b66aed875a0ca1b320dcf1ce9d9cdf95241dff1937dec094974`.
The final independent repair review is
`nov7-cs-notes-cache-independent-review.json`, SHA-256
`0c8c5d156b36d73af7e69f10fef9d03aa7ca7060adc463f6b40a16ace4361fcf`.
It preserves the initial InterruptedError miss/HOLD chronology; final narrow
repair/test review, not that superseded acceptance, is the binding evidence.
This optional API/CLI cache fix is not claimed as a normal installed-native
failure or a model/PDF qualification.

No broad dependency, whole-project completion, model capability, official
paper equivalence or general bug-free guarantee follows. Metadata producers are
not semantic reviewers. Source/test/repair-note bytes remain unchanged.
