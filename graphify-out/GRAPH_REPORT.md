# Graph Report - pdf_magic_app  (2026-09-18)

## Corpus Check
- 84 files · ~72,546 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1301 nodes · 2480 edges · 83 communities (62 shown, 15 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 22 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `80493476`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- htmx.min.js
- ._ws
- save_replace_rules
- strip_leading_number
- load_state
- database.py
- sanitize_text
- test_routes.py
- build_tree_from_created
- generate_aocr
- get_requisites
- reset_project.py
- save_state
- What You Must Do When Invoked
- app.py
- TestPageRoutes
- TestRequisitesObjects
- run.py
- conftest.py
- generate_numbered_filename
- test_files_routes.py
- magic.py
- test_msg_routes.py
- test_directories_routes.py
- TestRegistryData
- TestAddFiles
- init_converter_db
- core.py
- files.py
- TestAddMaterial
- directories.py
- Архитектура PDF Magic App
- utils/database.py — SQLite хранилище
- Ключевые функции
- routes/core.py — Ядро приложения
- routes/requisites.py — Реквизиты объектов
- Текущее состояние проекта
- requisites.py
- 00-Обзор-проекта.md
- utils/excel_registry.py — Генерация Excel-реестра
- app.py — Точка входа приложения
- routes/aocr.py — Генерация АОСР
- graphify reference: extra exports and benchmark
- PDF Magic App — Обзор проекта
- utils/state.py — Атомарная работа с JSON
- can_share_number
- routes/rules.py — Правила замены
- routes/files.py — Управление файлами
- routes/converter.py — Конвертация PDF
- routes/magic.py — Копирование и нумерация
- routes/materials.py — База материалов
- routes/directories.py — Управление директориями
- routes/registry.py — Данные реестра
- routes/dashboard.py — Дашборд
- CI/CD — GitHub Actions
- graphify reference: query, path, explain
- routes/state.py — Очистка состояния
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- opencode.json
- graphify.js
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- AGENTS.md
- extraction-spec.md
- init_requisites_db
- TestAddSubfolder
- TestAddFilesFromDir
- TestRenameDirectory
- TestDeleteDirectory
- parse_filename
- test_excel_registry.py
- excel_registry.py
- build_info_block
- safe_filename
- merge_set

## God Nodes (most connected - your core abstractions)
1. `load_state()` - 69 edges
2. `save_state()` - 59 edges
3. `sanitize_text()` - 32 edges
4. `ne()` - 28 edges
5. `se()` - 27 edges
6. `ue()` - 27 edges
7. `De()` - 27 edges
8. `sanitize_folder_name()` - 25 edges
9. `e()` - 25 edges
10. `save_replace_rules()` - 21 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `ensure_app_dirs()`  [EXTRACTED]
  app.py → routes/core.py
- `main()` --calls--> `init_converter_db()`  [EXTRACTED]
  app.py → utils/database.py
- `main()` --calls--> `init_db()`  [EXTRACTED]
  app.py → utils/database.py
- `main()` --calls--> `init_requisites_db()`  [EXTRACTED]
  app.py → utils/database.py
- `reset_database()` --calls--> `init_converter_db()`  [EXTRACTED]
  reset_project.py → utils/database.py

## Import Cycles
- None detected.

## Communities (83 total, 15 thin omitted)

### Community 0 - "htmx.min.js"
Cohesion: 0.08
Nodes (100): A(), ae(), an(), at(), B(), be(), bn(), bt() (+92 more)

### Community 1 - "._ws"
Cohesion: 0.25
Nodes (4): TestFillRows, TestSetCell, fill_rows(), set_cell()

### Community 2 - "save_replace_rules"
Cohesion: 0.06
Nodes (45): api_add_replace_rule(), api_clear_replace_rules(), api_delete_replace_rule(), api_get_accompanying_prefixes(), api_get_replace_rules(), api_save_accompanying_prefixes(), route, Blueprint: /api/replace-rules/* + /api/accompanying-prefixes/* (+37 more)

### Community 3 - "strip_leading_number"
Cohesion: 0.36
Nodes (3): Убирает старый порядковый номер 'NN.' в начале имени файла. '01.Акт.pdf' →…, strip_leading_number(), TestStripLeadingNumber

### Community 4 - "load_state"
Cohesion: 0.12
Nodes (13): copy_files_worker(), Background worker: copy and number files, generate Excel registry., Start file copy/numbering worker in background thread., start_magic(), patch, Tests for routes/magic.py — file copy/numbering/registry endpoints., Одинаковые документы в итоговой папке различаются номером (01/02), а не…, TestCancelMagic (+5 more)

### Community 5 - "database.py"
Cohesion: 0.10
Nodes (38): add_material_endpoint(), delete_material_endpoint(), get_material_pdf(), get_materials(), route, Blueprint: /api/materials/* — materials CRUD with PDF storage., Tests for utils/database.py — SQLite materials CRUD., Empty strings for optional fields are stored correctly. (+30 more)

### Community 6 - "sanitize_text"
Cohesion: 0.06
Nodes (11): sanitize_folder_name(), sanitize_text(), TestSanitizeFolderName, TestSanitizeText, Attempting to serve materials PDF with path traversal should fail., Adding material with empty data should not crash., Saving rule with empty from should return 400., Adding object with empty name should return 400. (+3 more)

### Community 7 - "test_routes.py"
Cohesion: 0.04
Nodes (12): Integration tests for Flask routes via test_client., TestConverterRoutes, TestDashboardRoutes, TestDirectoriesRoutes, TestFilesRoutes, TestHealthCheck, TestMaterialsRoutes, TestPageRoutes (+4 more)

### Community 8 - "build_tree_from_created"
Cohesion: 0.08
Nodes (12): build_tree_from_created(), build_tree_from_fs(), create_subfolders(), Any, tree_from_subfolders(), update_tree_paths(), Tests for routes/core.py — sanitization, tree builders, subfolder creation., TestBuildTreeFromCreated (+4 more)

### Community 9 - "generate_aocr"
Cohesion: 0.09
Nodes (19): _export_pdf(), _fill_sheet1(), _fill_sheet2(), generate_aocr(), _get_output_dir(), Any, Path, route (+11 more)

### Community 10 - "get_requisites"
Cohesion: 0.19
Nodes (12): Tests for utils/database.py — requisites and objects subsystem., Saving requisites for existing object updates (upsert)., Saving with partial data preserves defaults for missing fields., Saving with empty data uses all defaults., Requisites dict contains all expected fields., Deleting an object cascades to requisites., Save and verify all 51 fields round-trip correctly., Save requisites and retrieve them. (+4 more)

### Community 11 - "reset_project.py"
Cohesion: 0.26
Nodes (27): check_flask(), clean_converter_output(), clean_date_dirs(), clean_logs(), clean_materials_base(), clean_materials_folders(), clean_pycache(), clean_temp_uploads() (+19 more)

### Community 12 - "save_state"
Cohesion: 0.10
Nodes (19): Tests for routes/dashboard.py — dashboard statistics., TestDashboardStats, Tests for utils/state.py — thread-safe atomic state.json persistence., When state.json doesn't exist, load_state returns a default dict., Save state and load it back — round-trip integrity., Partial writes should not corrupt state.json (atomic replace)., Corrupt JSON falls back to default state., Multiple threads writing state concurrently should not corrupt it. (+11 more)

### Community 13 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 14 - "app.py"
Cohesion: 0.08
Nodes (42): after_request, aocr_page(), converter_page(), directories_page(), health_check(), index(), _kill_port_5000(), log_request_end() (+34 more)

### Community 15 - "TestPageRoutes"
Cohesion: 0.09
Nodes (6): Tests for app.py — page routes, health check, and request logging., TestAppConfig, TestHealthCheck, TestPageRoutes, TestRequestLogging, TestStaticFiles

### Community 16 - "TestRequisitesObjects"
Cohesion: 0.10
Nodes (4): Tests for routes/requisites.py — construction objects and requisites CRUD., TestAOCRData, TestRequisitesCRUD, TestRequisitesObjects

### Community 17 - "run.py"
Cohesion: 0.24
Nodes (16): check_java(), check_uv(), fail(), find_cmd(), install_python_deps(), launch(), main(), ok() (+8 more)

### Community 18 - "conftest.py"
Cohesion: 0.18
Nodes (14): app_client(), clean_state(), fixture, Fixtures for pdf_magic_app tests., Mock STATE_FILE to a temporary path, isolated per test., Return a clean default state, saved to temp file., Mock DB_PATH to a temporary database, isolated per test., Mock DB_PATH to a temporary database with all tables initialized. (+6 more)

### Community 19 - "generate_numbered_filename"
Cohesion: 0.43
Nodes (3): generate_numbered_filename(), Сквозная нумерация: '01.Имя.ext, TestGenerateNumberedFilename

### Community 20 - "test_files_routes.py"
Cohesion: 0.11
Nodes (5): Tests for routes/files.py — file upload, list, reorder, delete., TestClearFiles, TestGetFiles, TestRemoveFile, TestReorderFiles

### Community 21 - "magic.py"
Cohesion: 0.28
Nodes (7): cancel_magic(), get_magic_progress(), get_magic_result(), route, Blueprint: /api/magic/* — file copy, numbering, and Excel registry generation., Cancel running magic job., Get magic result after completion.

### Community 22 - "test_msg_routes.py"
Cohesion: 0.14
Nodes (19): _post_items(), fixture, Tests for МСГ / ОЖР (mesyachno-sutochny grafik / obshchiy zhurnal rabot)., Порядок строк МСГ — как впервые внесены в ОЖР., Mock msg DB_PATH to a temporary database, isolated per test., Две записи с 100% совпадением (работа+позиция+ед.) в один день агрегируются в…, Если единица измерения отличается — это уже НЕ 100% идентичность, в МСГ…, Одна работа в разные дни — одна строка, объёмы в своих днях. (+11 more)

### Community 23 - "test_directories_routes.py"
Cohesion: 0.10
Nodes (6): Tests for routes/directories.py — directory CRUD endpoints., TestCreateDirectory, TestGetCurrentDirectory, TestListDirectories, TestRecreateDirectory, TestScanDirectories

### Community 24 - "TestRegistryData"
Cohesion: 0.18
Nodes (3): Tests for routes/registry.py — registry data CRUD., TestRegistryData, TestRegistryForm

### Community 26 - "init_converter_db"
Cohesion: 0.05
Nodes (46): convert_pdf(), delete_history_entry(), download_result(), _find_jar(), get_history(), get_progress(), Path, route (+38 more)

### Community 28 - "core.py"
Cohesion: 0.11
Nodes (20): Flask, Logger, Blueprint: /api/aocr/* — Генерация формы АОСР (Акт освидетельствования скрытых…, ensure_app_dirs(), Shared state, utilities, and helpers — with type hints for mypy., setup_logging(), get_dashboard_stats(), route (+12 more)

### Community 29 - "files.py"
Cohesion: 0.23
Nodes (15): Очищает имя загружаемого файла от недопустимых в Windows символов. Сохраняет…, sanitize_upload_name(), add_files(), add_files_from_dir(), clear_files(), _collect_dir_files(), get_files(), Path (+7 more)

### Community 30 - "TestAddMaterial"
Cohesion: 0.11
Nodes (5): Tests for routes/materials.py — materials CRUD with PDF storage., TestAddMaterial, TestDeleteMaterial, TestGetMaterialPDF, TestGetMaterials

### Community 31 - "directories.py"
Cohesion: 0.24
Nodes (15): get_app_dir(), Path, scan_filesystem_for_dirs(), set_app_dir(), sync_tree_from_fs(), add_subfolder(), create_directory(), delete_directory() (+7 more)

### Community 35 - "Архитектура PDF Magic App"
Cohesion: 0.15
Nodes (13): data/materials.db — SQLite, routes/ — API-слой, state.json — JSON-хранилище, utils/ — Бизнес-логика, Архитектура PDF Magic App, Безопасность, Генерация АОСР, Копирование файлов (magic) (+5 more)

### Community 36 - "utils/database.py — SQLite хранилище"
Cohesion: 0.15
Nodes (13): conversions — Конвертации, materials — Материалы, objects — Объекты, requisites — Реквизиты, utils/database.py — SQLite хранилище, Ключевые функции, Конвертации, Материалы (+5 more)

### Community 37 - "Ключевые функции"
Cohesion: 0.15
Nodes (13): apply_rules_to_name(raw_name) → str, apply_symbol_rules(text) → str, DEFAULT_ACCOMPANYING_PREFIXES (14 шт.), DEFAULT_REPLACE_RULES, get_accompanying_prefixes() / save_accompanying_prefixes(prefixes), get_replace_rules() / save_replace_rules(rules), is_accompanying_doc(name) → bool, normalize_name(raw_name) → str (+5 more)

### Community 38 - "routes/core.py — Ядро приложения"
Cohesion: 0.18
Nodes (11): routes/core.py — Ядро приложения, Глобальное состояние, Деревья папок, Зависимости, Зачем это нужно, Ключевые функции, Константы, Логирование (+3 more)

### Community 39 - "routes/requisites.py — Реквизиты объектов"
Cohesion: 0.18
Nodes (11): routes/requisites.py — Реквизиты объектов, Зависимости, Застройщик (developer), Подрядчик (builder), Представители (representatives), Проектировщик (designer), Структура реквизитов, Технадзор (control) (+3 more)

### Community 40 - "Текущее состояние проекта"
Cohesion: 0.18
Nodes (11): Dev, Зависимости, Известные ограничения, Как запускать, Контакты, Опциональные, Основные, Статус (+3 more)

### Community 41 - "requisites.py"
Cohesion: 0.14
Nodes (20): create_object(), get_aocr_data(), _get_object_name(), list_objects(), route, Blueprint: /api/requisites/* — Управление объектами строительства и их…, GET /api/requisites/<object_id>/aocr — merged data ready for AOCP form…, Return the name of an object by its id, or None if not found. (+12 more)

### Community 42 - "00-Обзор-проекта.md"
Cohesion: 0.27
Nodes (6): Coverage по модулям, Как запускать, Общая статистика, Структура тестов, Тесты — Покрытие и структура, Фикстуры (conftest.py)

### Community 43 - "utils/excel_registry.py — Генерация Excel-реестра"
Cohesion: 0.18
Nodes (11): utils/excel_registry.py — Генерация Excel-реестра, АОСР, Зависимости, Ключевые функции, Подписи (после таблицы), Стили, Структура документа, Таблица (строки 29+) (+3 more)

### Community 44 - "app.py — Точка входа приложения"
Cohesion: 0.22
Nodes (8): API-эндпоинты, app.py — Точка входа приложения, HTML-маршруты, Зависимости, Запуск (функция main), Конфигурация Flask, Логирование, Что делает

### Community 45 - "routes/aocr.py — Генерация АОСР"
Cohesion: 0.22
Nodes (9): routes/aocr.py — Генерация АОСР, Зависимости, Лист "1" (18 полей), Лист "2" (27 полей), Поведение, Что делает, Шаблон, Экспорт PDF (+1 more)

### Community 46 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 47 - "PDF Magic App — Обзор проекта"
Cohesion: 0.25
Nodes (8): CI/CD, PDF Magic App — Обзор проекта, Как запускать, Ключевые возможности, Структура проекта, Тестирование, Хранилище данных, Что это за проект

### Community 48 - "utils/state.py — Атомарная работа с JSON"
Cohesion: 0.25
Nodes (8): _atomic_save(state), load_state() → dict, save_state(state), utils/state.py — Атомарная работа с JSON, Зависимости, Зачем это нужно, Ключевые функции, Что делает

### Community 49 - "can_share_number"
Cohesion: 0.36
Nodes (3): can_share_number(), PDF и Excel (АОСР) с одинаковым наименованием получают один номер., TestCanShareNumber

### Community 50 - "routes/rules.py — Правила замены"
Cohesion: 0.29
Nodes (7): routes/rules.py — Правила замены, Зависимости, Сопровождающие префиксы, Типы правил, Формат правила, Что делает, Эндпоинты

### Community 51 - "routes/files.py — Управление файлами"
Cohesion: 0.22
Nodes (8): routes/files.py — Управление файлами, Допустимые расширения, Зависимости, Импорт папки (`/api/files/add-from-dir`), Поведение, Формат ответа, Что делает, Эндпоинты

### Community 52 - "routes/converter.py — Конвертация PDF"
Cohesion: 0.29
Nodes (7): routes/converter.py — Конвертация PDF, Внутренние функции, Допустимые форматы, Зависимости, Поведение, Что делает, Эндпоинты

### Community 53 - "routes/magic.py — Копирование и нумерация"
Cohesion: 0.25
Nodes (8): routes/magic.py — Копирование и нумерация, Зависимости, Нумерация (актуальная логика), Поток копирования, Проверки, Формат нумерации, Что делает, Эндпоинты

### Community 54 - "routes/materials.py — База материалов"
Cohesion: 0.29
Nodes (7): routes/materials.py — База материалов, Зависимости, Поведение, Формат файла материала, Хранение, Что делает, Эндпоинты

### Community 55 - "routes/directories.py — Управление директориями"
Cohesion: 0.29
Nodes (6): routes/directories.py — Управление директориями, Безопасность, Зависимости, Структура директорий, Что делает, Эндпоинты

### Community 56 - "routes/registry.py — Данные реестра"
Cohesion: 0.33
Nodes (6): routes/registry.py — Данные реестра, Зависимости, Поля реестра, Словари автодополнения, Что делает, Эндпоинты

### Community 57 - "routes/dashboard.py — Дашборд"
Cohesion: 0.33
Nodes (6): routes/dashboard.py — Дашборд, Возвращаемые данные, Зависимости, Источники данных, Что делает, Эндпоинты

### Community 58 - "CI/CD — GitHub Actions"
Cohesion: 0.33
Nodes (6): CI/CD — GitHub Actions, Запуск, Конфигурация, Проверки, Текущий статус, Установка зависимостей

### Community 59 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 60 - "routes/state.py — Очистка состояния"
Cohesion: 0.40
Nodes (5): routes/state.py — Очистка состояния, Зачем это нужно, Поведение, Что делает, Эндпоинты

### Community 61 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 62 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 63 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 72 - "init_requisites_db"
Cohesion: 0.17
Nodes (9): init_requisites_db creates objects and requisites tables., Multiple calls to init_requisites_db are safe., Add an object and verify it exists., get_objects returns all objects., Empty table returns empty list., Deleting non-existent ID returns False., Object dict contains expected fields., TestObjects (+1 more)

### Community 78 - "test_excel_registry.py"
Cohesion: 0.22
Nodes (5): Tests for utils/excel_registry.py — pure functions and workbook helpers., TestBuildHeader, TestBuildSignatures, build_header(), build_signatures()

### Community 79 - "excel_registry.py"
Cohesion: 0.29
Nodes (9): aosr_name_from_cell(), collect_files(), fix_page_margins_in_xlsx(), generate_excel_registry(), Path, Модуль генерации Excel-реестра исполнительной документации. Использует openpyxl…, Формирует имя строки АОСР: 'АОСР. <текст из ячейки>'. Если в ячейке уже есть…, read_aosr_cell_from_xlsx() (+1 more)

## Knowledge Gaps
- **197 isolated node(s):** `$schema`, `plugin`, `Usage`, `What graphify is for`, `Step 0 - GitHub repos and multi-path merge (only if a URL or several paths)` (+192 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 555 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_state()` connect `load_state` to `save_replace_rules`, `generate_aocr`, `save_state`, `test_files_routes.py`, `magic.py`, `test_directories_routes.py`, `core.py`, `files.py`, `directories.py`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Why does `save_state()` connect `save_state` to `save_replace_rules`, `load_state`, `conftest.py`, `test_files_routes.py`, `magic.py`, `test_directories_routes.py`, `core.py`, `files.py`, `directories.py`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `init_requisites_db()` connect `init_requisites_db` to `database.py`, `requisites.py`, `get_requisites`, `reset_project.py`, `app.py`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **What connects `$schema`, `plugin`, `Usage` to the rest of the system?**
  _197 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `htmx.min.js` be split into smaller, more focused modules?**
  _Cohesion score 0.07823002240477969 - nodes in this community are weakly interconnected._
- **Should `save_replace_rules` be split into smaller, more focused modules?**
  _Cohesion score 0.056265984654731455 - nodes in this community are weakly interconnected._
- **Should `load_state` be split into smaller, more focused modules?**
  _Cohesion score 0.11692307692307692 - nodes in this community are weakly interconnected._