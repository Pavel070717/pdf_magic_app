# routes/core.py — Ядро приложения

**Путь**: `routes/core.py` (489 строк)

## Что делает

Самый важный модуль в проекте. Содержит общее состояние, логирование, константы и все вспомогательные функции для работы с файловой системой и деревьями папок.

## Константы

| Константа | Значение | Зачем |
|---|---|---|
| `PROJECT_DIR` | Корень проекта | Базовый путь для всех относительных путей |
| `LOG_DIR` | `PROJECT_DIR/logs` | Директория логов |
| `LOG_FILE` | `LOG_DIR/app.log` | Основной лог-файл |
| `DESKTOP_PATH` | `~/Desktop` | Рабочий стол пользователя |
| `APP_DIR` | Desktop или `PDF_MAGIC_APP_DIR` | Рабочая директория приложения |
| `TEMP_UPLOADS_DIR` | `PROJECT_DIR/temp_uploads` | Временные загрузки |
| `MATERIALS_DIR` | `~/Desktop/база материалов` | Хранилище PDF материалов |
| `STATE_FILE` | `PROJECT_DIR/state.json` | Файл состояния |

## Глобальное состояние

- `magic_progress` — dict с прогрессом операции копирования:
  - `running` — выполняется ли операция
  - `progress` — процент (0-100)
  - `current_file` — имя текущего файла
  - `total_files` — общее количество
  - `files_copied` — сколько скопировано
  - `error` — текст ошибки
  - `cancel_requested` — запрошена ли отмена
- `_magic_lock` — threading.Lock для потокобезопасности

## Ключевые функции

### Логирование
- `setup_logging()` → Logger — 3 обработчика: файл (DEBUG), ошибки (ERROR), консоль (INFO)

### Работа с директориями
- `get_app_dir()` → Path — текущая рабочая директория
- `set_app_dir(path)` — установить рабочую директорию
- `ensure_app_dirs()` — создать `temp_uploads/`, `logs/`, инициализировать `state.json`

### Очистка имён
- `sanitize_text(text)` → str — удаляет HTML-теги и символы `<>`
- `sanitize_folder_name(name)` → str — заменяет `\/:*?"<>|` на `_`

### Деревья папок
- `create_subfolders(base_path, tree)` → dict — рекурсивно создаёт дерево подпапок
- `build_tree_from_fs(directory)` → list — строит дерево из файловой системы
- `sync_tree_from_fs(entry, base_path)` — синхронизирует дерево с ФС
- `update_tree_paths(tree_nodes, old_base, new_base)` — обновляет пути при переименовании
- `build_tree_from_created(created_dirs)` → list — строит дерево из записей (группировка по датам)
- `tree_from_subfolders(tree_nodes, base_path)` → list — конвертирует дерево для фронтенда
- `scan_filesystem_for_dirs()` → list — сканирует рабочий стол на предмет папок `DD.MM.YYYY`

## Зачем это нужно

Все остальные модули импортируют из `core.py`:
- Константы путей (`APP_DIR`, `MATERIALS_DIR`, `STATE_FILE`)
- Логгер (`logger`)
- Функции работы с деревьями
- Глобальное состояние `magic_progress`

## Зависимости

- `logging`, `os`, `re`, `threading`, `collections.defaultdict`, `datetime`, `pathlib.Path`
- `utils.state` (load_state, save_state)

---
Связано: [[01-Архитектура]] | [[02-app.py]] | [[16-utils-state]]
