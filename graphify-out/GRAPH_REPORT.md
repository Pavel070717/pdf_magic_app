# Graph Report - .  (2026-07-14)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 433 nodes · 930 edges · 16 communities (15 shown, 1 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 3 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1876a219`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- load_state
- app.py
- save_replace_rules
- DesignTokenGenerator
- PersonaGenerator
- test_database.py
- reset_project.py
- landing_page_scaffolder.py
- Flask
- excel_registry.py
- run.py
- conftest.py
- check_contrast
- validate-api.sh

## God Nodes (most connected - your core abstractions)
1. `load_state()` - 43 edges
2. `save_state()` - 34 edges
3. `DesignTokenGenerator` - 23 edges
4. `PersonaGenerator` - 19 edges
5. `get_db()` - 18 edges
6. `save_replace_rules()` - 17 edges
7. `main()` - 17 edges
8. `print_step()` - 15 edges
9. `print_warn()` - 14 edges
10. `section()` - 14 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `init_db()`  [EXTRACTED]
  app.py → utils/database.py
- `_get_output_dir()` --calls--> `load_state()`  [EXTRACTED]
  routes/aocr.py → utils/state.py
- `ensure_app_dirs()` --calls--> `save_state()`  [EXTRACTED]
  routes/core.py → utils/state.py
- `get_dashboard_stats()` --calls--> `get_all_materials()`  [EXTRACTED]
  routes/dashboard.py → utils/database.py
- `get_dashboard_stats()` --calls--> `load_state()`  [EXTRACTED]
  routes/dashboard.py → utils/state.py

## Import Cycles
- None detected.

## Communities (16 total, 1 thin omitted)

### Community 0 - "load_state"
Cohesion: 0.07
Nodes (59): Logger, build_tree_from_created(), build_tree_from_fs(), create_subfolders(), get_app_dir(), Any, Path, Shared state, utilities, and helpers — with type hints for mypy. (+51 more)

### Community 1 - "app.py"
Cohesion: 0.06
Nodes (45): _kill_port_5000(), main(), open_browser(), Убивает зомби-процессы на порту 5000 (Windows)., Launch the app. Starts Flask+Waitress directly (not as subprocess)., Connection, convert_pdf(), delete_history_entry() (+37 more)

### Community 2 - "save_replace_rules"
Cohesion: 0.06
Nodes (40): api_add_replace_rule(), api_clear_replace_rules(), api_delete_replace_rule(), api_get_accompanying_prefixes(), api_get_replace_rules(), api_save_accompanying_prefixes(), Blueprint: /api/replace-rules/* + /api/accompanying-prefixes/*, Tests for utils/rules.py — replace rules, accompanying prefixes, name normalizat (+32 more)

### Community 3 - "DesignTokenGenerator"
Cohesion: 0.08
Nodes (19): DesignTokenGenerator, main(), Generate color scale from base color, Generate neutral color scale, Generate typography system, Generate modular type scale, Generate pre-composed text styles, Generate spacing system based on 8pt grid (+11 more)

### Community 4 - "PersonaGenerator"
Cohesion: 0.08
Nodes (20): create_sample_user_data(), main(), PersonaGenerator, Generate persona from user data and optional interview insights, Analyze patterns in user data, Identify persona archetype based on patterns, Generate persona name based on archetype, Generate persona tagline (+12 more)

### Community 5 - "test_database.py"
Cohesion: 0.10
Nodes (35): sanitize_text(), add_material_endpoint(), delete_material_endpoint(), get_material_pdf(), get_materials(), Blueprint: /api/materials/* — materials CRUD with PDF storage., Tests for utils/database.py — SQLite materials CRUD., Empty strings for optional fields are stored correctly. (+27 more)

### Community 6 - "reset_project.py"
Cohesion: 0.28
Nodes (26): check_flask(), clean_converter_output(), clean_date_dirs(), clean_logs(), clean_materials_base(), clean_materials_folders(), clean_pycache(), clean_temp_uploads() (+18 more)

### Community 7 - "landing_page_scaffolder.py"
Cohesion: 0.24
Nodes (22): escape(), generate_css(), generate_html(), generate_tsx(), main(), Any, Generate complete Next.js/React TSX landing page with Tailwind CSS., Generate responsive CSS from config theme. (+14 more)

### Community 8 - "Flask"
Cohesion: 0.13
Nodes (20): Flask, _export_pdf(), _fill_sheet1(), _fill_sheet2(), generate_aocr(), _get_output_dir(), Any, Path (+12 more)

### Community 9 - "excel_registry.py"
Cohesion: 0.20
Nodes (19): build_header(), build_info_block(), build_signatures(), collect_files(), fill_rows(), fix_page_margins_in_xlsx(), generate_excel_registry(), merge_set() (+11 more)

### Community 10 - "run.py"
Cohesion: 0.21
Nodes (18): CompletedProcess, check_java(), check_uv(), fail(), find_cmd(), install_python_deps(), launch(), main() (+10 more)

### Community 11 - "conftest.py"
Cohesion: 0.25
Nodes (7): clean_state(), Fixtures for pdf_magic_app tests., Mock STATE_FILE to a temporary path, isolated per test., Return a clean default state, saved to temp file., Mock DB_PATH to a temporary database, isolated per test., temp_db(), temp_state_file()

### Community 12 - "check_contrast"
Cohesion: 0.47
Nodes (5): calculate_luminance(), check_contrast(), main(), Calculates relative luminance for a given hex color., Checks contrast ratio between foreground and background.

## Knowledge Gaps
- **1 isolated node(s):** `validate-api.sh script`
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_state()` connect `load_state` to `Flask`, `save_replace_rules`?**
  _High betweenness centrality (0.096) - this node is a cross-community bridge._
- **Why does `save_state()` connect `load_state` to `app.py`, `save_replace_rules`, `conftest.py`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Why does `save_replace_rules()` connect `save_replace_rules` to `load_state`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **What connects `Calculates relative luminance for a given hex color.`, `Checks contrast ratio between foreground and background.`, `validate-api.sh script` to the rest of the system?**
  _131 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `load_state` be split into smaller, more focused modules?**
  _Cohesion score 0.07374254049445865 - nodes in this community are weakly interconnected._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05706214689265537 - nodes in this community are weakly interconnected._
- **Should `save_replace_rules` be split into smaller, more focused modules?**
  _Cohesion score 0.06497175141242938 - nodes in this community are weakly interconnected._