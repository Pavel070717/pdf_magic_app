# Graph Report - pdf_magic_app  (2026-09-06)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 919 nodes · 1989 edges · 35 communities (26 shown, 6 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 22 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `db3b626e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- htmx.min.js
- ._ws
- save_replace_rules
- database.py
- test_database_converter.py
- test_database.py
- sanitize_text
- test_routes.py
- create_subfolders
- generate_aocr
- core.py
- reset_project.py
- save_state
- load_state
- app.py
- TestPageRoutes
- TestRequisitesObjects
- run.py
- conftest.py
- test_magic_routes.py
- test_files_routes.py
- Flask
- magic.py
- test_directories_routes.py
- TestRegistryData
- TestAddFiles
- TestConvertPDF
- registry.py
- TestAddSubfolder
- TestCreateDirectory
- TestRenameDirectory
- TestDeleteDirectory

## God Nodes (most connected - your core abstractions)
1. `load_state()` - 62 edges
2. `save_state()` - 52 edges
3. `sanitize_text()` - 32 edges
4. `ne()` - 28 edges
5. `De()` - 27 edges
6. `se()` - 27 edges
7. `ue()` - 27 edges
8. `e()` - 25 edges
9. `sanitize_folder_name()` - 25 edges
10. `ee()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `copy_files_worker()` --calls--> `generate_excel_registry()`  [EXTRACTED]
  routes/magic.py → utils/excel_registry.py
- `scan_filesystem_for_dirs()` --calls--> `load_state()`  [EXTRACTED]
  routes/core.py → utils/state.py
- `scan_filesystem_for_dirs()` --calls--> `save_state()`  [EXTRACTED]
  routes/core.py → utils/state.py
- `add_subfolder()` --calls--> `load_state()`  [EXTRACTED]
  routes/directories.py → utils/state.py
- `add_subfolder()` --calls--> `save_state()`  [EXTRACTED]
  routes/directories.py → utils/state.py

## Import Cycles
- None detected.

## Communities (35 total, 6 thin omitted)

### Community 0 - "htmx.min.js"
Cohesion: 0.08
Nodes (100): A(), ae(), an(), at(), B(), be(), bn(), bt() (+92 more)

### Community 1 - "._ws"
Cohesion: 0.06
Nodes (24): Tests for utils/excel_registry.py — pure functions and workbook helpers., TestBuildHeader, TestBuildInfoBlock, TestBuildSignatures, TestFillRows, TestMergeSet, TestParseFilename, TestSafeFilename (+16 more)

### Community 2 - "save_replace_rules"
Cohesion: 0.06
Nodes (45): api_add_replace_rule(), api_clear_replace_rules(), api_delete_replace_rule(), api_get_accompanying_prefixes(), api_get_replace_rules(), api_save_accompanying_prefixes(), route, Blueprint: /api/replace-rules/* + /api/accompanying-prefixes/* (+37 more)

### Community 3 - "database.py"
Cohesion: 0.07
Nodes (43): Connection, create_object(), get_aocr_data(), _get_object_name(), list_objects(), route, Blueprint: /api/requisites/* — Управление объектами строительства и их…, GET /api/requisites/<object_id>/aocr — merged data ready for AOCP form… (+35 more)

### Community 4 - "test_database_converter.py"
Cohesion: 0.06
Nodes (44): convert_pdf(), delete_history_entry(), download_result(), _find_jar(), get_history(), get_progress(), Path, route (+36 more)

### Community 5 - "test_database.py"
Cohesion: 0.06
Nodes (38): add_material_endpoint(), delete_material_endpoint(), get_material_pdf(), get_materials(), route, Blueprint: /api/materials/* — materials CRUD with PDF storage., Tests for utils/database.py — SQLite materials CRUD., Empty strings for optional fields are stored correctly. (+30 more)

### Community 6 - "sanitize_text"
Cohesion: 0.06
Nodes (11): sanitize_folder_name(), sanitize_text(), TestSanitizeFolderName, TestSanitizeText, Attempting to serve materials PDF with path traversal should fail., Adding material with empty data should not crash., Saving rule with empty from should return 400., Adding object with empty name should return 400. (+3 more)

### Community 7 - "test_routes.py"
Cohesion: 0.04
Nodes (12): Integration tests for Flask routes via test_client., TestConverterRoutes, TestDashboardRoutes, TestDirectoriesRoutes, TestFilesRoutes, TestHealthCheck, TestMaterialsRoutes, TestPageRoutes (+4 more)

### Community 8 - "create_subfolders"
Cohesion: 0.10
Nodes (9): build_tree_from_fs(), create_subfolders(), tree_from_subfolders(), update_tree_paths(), Tests for routes/core.py — sanitization, tree builders, subfolder creation., TestBuildTreeFromFs, TestCreateSubfolders, TestTreeFromSubfolders (+1 more)

### Community 9 - "generate_aocr"
Cohesion: 0.09
Nodes (19): _export_pdf(), _fill_sheet1(), _fill_sheet2(), generate_aocr(), _get_output_dir(), Any, Path, route (+11 more)

### Community 10 - "core.py"
Cohesion: 0.14
Nodes (21): Logger, build_tree_from_created(), get_app_dir(), Any, Path, Shared state, utilities, and helpers — with type hints for mypy., scan_filesystem_for_dirs(), set_app_dir() (+13 more)

### Community 11 - "reset_project.py"
Cohesion: 0.26
Nodes (27): check_flask(), clean_converter_output(), clean_date_dirs(), clean_logs(), clean_materials_base(), clean_materials_folders(), clean_pycache(), clean_temp_uploads() (+19 more)

### Community 12 - "save_state"
Cohesion: 0.11
Nodes (9): ensure_app_dirs(), Tests for routes/dashboard.py — dashboard statistics., TestDashboardStats, patch, TestStartMagic, _atomic_save(), Any, Thread-safe atomic state.json persistence — with type hints. (+1 more)

### Community 13 - "load_state"
Cohesion: 0.15
Nodes (20): add_files(), get_files(), route, Blueprint: /api/files/* — file upload, list, reorder, delete., remove_file(), reorder_files(), Tests for utils/state.py — thread-safe atomic state.json persistence., When state.json doesn't exist, load_state returns a default dict. (+12 more)

### Community 14 - "app.py"
Cohesion: 0.14
Nodes (20): after_request, aocr_page(), converter_page(), directories_page(), health_check(), index(), _kill_port_5000(), log_request_end() (+12 more)

### Community 15 - "TestPageRoutes"
Cohesion: 0.10
Nodes (6): Tests for app.py — page routes, health check, and request logging., TestAppConfig, TestHealthCheck, TestPageRoutes, TestRequestLogging, TestStaticFiles

### Community 16 - "TestRequisitesObjects"
Cohesion: 0.10
Nodes (4): Tests for routes/requisites.py — construction objects and requisites CRUD., TestAOCRData, TestRequisitesCRUD, TestRequisitesObjects

### Community 17 - "run.py"
Cohesion: 0.24
Nodes (16): check_java(), check_uv(), fail(), find_cmd(), install_python_deps(), launch(), main(), ok() (+8 more)

### Community 18 - "conftest.py"
Cohesion: 0.18
Nodes (14): fixture, app_client(), clean_state(), Fixtures for pdf_magic_app tests., Mock STATE_FILE to a temporary path, isolated per test., Return a clean default state, saved to temp file., Mock DB_PATH to a temporary database, isolated per test., Mock DB_PATH to a temporary database with all tables initialized. (+6 more)

### Community 19 - "test_magic_routes.py"
Cohesion: 0.17
Nodes (7): generate_numbered_filename(), Сквозная нумерация: '01.Имя.ext, Tests for routes/magic.py — file copy/numbering/registry endpoints., TestCancelMagic, TestGenerateNumberedFilename, TestMagicProgress, TestMagicResult

### Community 20 - "test_files_routes.py"
Cohesion: 0.13
Nodes (4): Tests for routes/files.py — file upload, list, reorder, delete., TestGetFiles, TestRemoveFile, TestReorderFiles

### Community 21 - "Flask"
Cohesion: 0.19
Nodes (10): Flask, Blueprint: /api/aocr/* — Генерация формы АОСР (Акт освидетельствования скрытых…, get_dashboard_stats(), route, Blueprint: /api/dashboard/stats, Routes package — registers all blueprints on a Flask app., register_blueprints(), clear_state() (+2 more)

### Community 22 - "magic.py"
Cohesion: 0.21
Nodes (11): cancel_magic(), copy_files_worker(), get_magic_progress(), get_magic_result(), route, Blueprint: /api/magic/* — file copy, numbering, and Excel registry generation., Cancel running magic job., Get magic result after completion. (+3 more)

### Community 23 - "test_directories_routes.py"
Cohesion: 0.15
Nodes (5): Tests for routes/directories.py — directory CRUD endpoints., TestGetCurrentDirectory, TestListDirectories, TestRecreateDirectory, TestScanDirectories

### Community 24 - "TestRegistryData"
Cohesion: 0.18
Nodes (3): Tests for routes/registry.py — registry data CRUD., TestRegistryData, TestRegistryForm

### Community 27 - "registry.py"
Cohesion: 0.38
Nodes (6): get_registry_data(), get_registry_form(), route, Blueprint: /api/registry/* — registry data CRUD., Return HTML form for the registry modal., save_registry_data()

## Knowledge Gaps
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_state()` connect `load_state` to `save_replace_rules`, `generate_aocr`, `core.py`, `save_state`, `test_magic_routes.py`, `test_files_routes.py`, `Flask`, `magic.py`, `test_directories_routes.py`, `registry.py`?**
  _High betweenness centrality (0.124) - this node is a cross-community bridge._
- **Why does `save_state()` connect `save_state` to `save_replace_rules`, `core.py`, `load_state`, `conftest.py`, `test_magic_routes.py`, `test_files_routes.py`, `Flask`, `magic.py`, `test_directories_routes.py`, `registry.py`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Why does `sanitize_text()` connect `sanitize_text` to `save_replace_rules`, `test_database.py`, `create_subfolders`, `generate_aocr`, `core.py`, `Flask`, `registry.py`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Should `htmx.min.js` be split into smaller, more focused modules?**
  _Cohesion score 0.07823002240477969 - nodes in this community are weakly interconnected._
- **Should `._ws` be split into smaller, more focused modules?**
  _Cohesion score 0.0609009009009009 - nodes in this community are weakly interconnected._
- **Should `save_replace_rules` be split into smaller, more focused modules?**
  _Cohesion score 0.056265984654731455 - nodes in this community are weakly interconnected._
- **Should `database.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0701484895033282 - nodes in this community are weakly interconnected._