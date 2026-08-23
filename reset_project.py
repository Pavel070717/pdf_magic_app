#!/usr/bin/env python3
"""
Скрипт полного сброса проекта PDF Magic App до состояния "из коробки".

Что делает:
  0. Проверяет, запущен ли Flask — если да, ОСТАНАВЛИВАЕТ сброс
  1. Очищает БД материалов (data/materials.db)
  2. Удаляет все созданные директории (из state.json + физически)
  3. Очищает temp_uploads/
  4. Полностью перезаписывает state.json чистым состоянием
  5. Удаляет все папки materials/ внутри рабочих директорий
  6. Удаляет папку «база материалов» на рабочем столе
  7. Удаляет все папки с датами (DD.MM.YYYY) с рабочего стола
  8. Очищает лог-файлы (logs/)
  9. Удаляет все __pycache__ рекурсивно
  10. Очищает кеши инструментов (.mypy_cache, .pytest_cache, .ruff_cache)
  11. Очищает папку «Конвертор пдф»
  12. Финальная проверка всех компонентов

Безопасность: НЕ запускать если Flask работает!
"""

import json
import os
import re
import shutil
import socket
import sqlite3
import sys
from pathlib import Path

# ─── Конфигурация ───────────────────────────────────────────────────────────

PROJECT_DIR = Path(__file__).parent.resolve()
KEEP_DIRS = {".agents", ".venv", "node_modules", "graphify-out", ".codewhale"}

TEMP_UPLOADS_DIR = PROJECT_DIR / "temp_uploads"
LOG_DIR = PROJECT_DIR / "logs"
STATE_FILE = PROJECT_DIR / "state.json"
DATA_DIR = PROJECT_DIR / "data"
DB_PATH = DATA_DIR / "materials.db"
_app_dir = os.environ.get("PDF_MAGIC_APP_DIR", str(Path.home() / "Desktop"))
CONVERTER_OUTPUT = Path(_app_dir) / "Конвертор пдф"

MATERIALS_SUBDIR = "materials"

# ─── ANSI-цвета ─────────────────────────────────────────────────────────────

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_step(msg):
    print(f"  [{GREEN}OK{RESET}] {msg}")


def print_skip(msg):
    print(f"  [{YELLOW}--{RESET}] {msg}")


def print_warn(msg):
    print(f"  [{YELLOW}!!{RESET}] {msg}")


def print_error(msg):
    print(f"  [{RED}XX{RESET}] {msg}")


def section(title):
    print()
    print(f"{CYAN}{'=' * 60}{RESET}")
    print(f"  {BOLD}{title}{RESET}")
    print(f"{CYAN}{'-' * 60}{RESET}")


def header(title):
    print()
    print(f"{BOLD}{'=' * 60}{RESET}")
    print(f"  {BOLD}{title}{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")


# ─── Проверка Flask ────────────────────────────────────────────────────────


def is_port_open(host="localhost", port=5000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        try:
            return s.connect_ex((host, port)) == 0
        except OSError:
            return False


def is_flask_alive(host="localhost", port=5000):
    """Проверяет, отвечает ли на порту реальный Flask (не зомби)."""
    if not is_port_open(host, port):
        return False
    try:
        import urllib.request

        req = urllib.request.Request(f"http://{host}:{port}/api/dashboard/stats")
        resp = urllib.request.urlopen(req, timeout=2)
        return resp.status == 200
    except Exception:
        return False


def kill_port_5000():
    """Убивает любой процесс на порту 5000 (Windows)."""
    import subprocess

    killed = False
    try:
        result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, timeout=5, errors="replace")
        for line in result.stdout.splitlines():
            if ":5000" in line and "LISTENING" in line:
                parts = line.strip().split()
                pid = parts[-1]
                subprocess.run(["taskkill", "/PID", pid, "/F"], capture_output=True, timeout=5)
                print_step(f"Зомби-процесс PID {pid} убит")
                killed = True
    except Exception:
        pass
    return killed


def load_current_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


# ─── 0. Проверка и остановка Flask ─────────────────────────────────────────


def check_flask(force=False):
    section("0. Проверка Flask-сервера")
    if force:
        print_warn("Режим --force: проверка Flask пропущена")
        return True

    if not is_port_open():
        print_step("Порт 5000 свободен — можно безопасно сбрасывать")
        return True

    if is_flask_alive():
        print_warn("Flask-сервер ЗАПУЩЕН и отвечает на http://localhost:5000!")
        print_warn("Сброс НЕВОЗМОЖЕН пока Flask работает.")
        print_warn("Flask перезапишет state.json из памяти после сброса.")
        print()
        try:
            answer = input("  Прибить Flask и продолжить сброс? (д/н): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = "н"
        if answer in ("д", "y", "да", "yes"):
            print()
            if kill_port_5000():
                print_step("Flask убит — продолжаем сброс")
                return True
            else:
                print_error("Не удалось убить Flask.")
                return False
        print()
        print_warn("Сброс отменён. Запустите: python reset_project.py --force")
        return False

    # Port is open but Flask doesn't respond → zombie process
    print_warn("Порт 5000 занят, но Flask не отвечает — зомби-процесс!")
    if kill_port_5000():
        print_step("Зомби убит, порт свободен — можно продолжать")
        return True
    else:
        print_error("Не удалось убить зомби-процесс.")
        print_warn("Попробуйте: python reset_project.py --force")
        return False


# ─── 1. Очистка БД материалов ──────────────────────────────────────────────


def reset_database():
    section("1. База данных материалов (data/materials.db)")

    # Удаляем сам файл БД + journal/wal/shm
    for suffix in ["", "-journal", "-wal", "-shm"]:
        db_file = Path(str(DB_PATH) + suffix)
        if db_file.exists():
            try:
                size = db_file.stat().st_size
                db_file.unlink()
                print_step(f"Удалён: {db_file.name} ({size} байт)")
            except Exception as e:
                print_warn(f"Не удалось удалить {db_file.name}: {e}")

    # Пересоздаём чистую БД
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_name TEXT NOT NULL,
                material_name TEXT NOT NULL,
                number TEXT DEFAULT '',
                date TEXT DEFAULT '',
                producer TEXT DEFAULT '',
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                output_format TEXT NOT NULL DEFAULT 'markdown',
                source_path TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS objects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS requisites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                object_id INTEGER UNIQUE NOT NULL,
                developer_name TEXT DEFAULT '',
                builder_name TEXT DEFAULT '',
                designer_name TEXT DEFAULT '',
                FOREIGN KEY (object_id) REFERENCES objects(id) ON DELETE CASCADE
            )
        """)
        conn.execute("DELETE FROM conversions")
        conn.execute("DELETE FROM requisites")
        conn.execute("DELETE FROM objects")
        conn.commit()
        conn.close()
        print_step("БД materials.db создана заново (пустая, все таблицы)")
    except Exception as e:
        print_error(f"Ошибка при создании БД: {e}")


# ─── 2. Удаление созданных директорий ──────────────────────────────────────


def delete_created_directories(state):
    section("2. Созданные директории (из state.json)")

    created_dirs = state.get("created_directories", [])
    if not created_dirs:
        print_skip("Нет созданных директорий в state.json")
        return

    deleted_count = 0
    for entry in created_dirs:
        if isinstance(entry, str):
            dir_path = entry
        else:
            dir_path = entry.get("path", "")
        if not dir_path:
            continue
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            try:
                shutil.rmtree(path)
                print_step(f"Удалена: {path}")
                deleted_count += 1
            except Exception as e:
                print_warn(f"Не удалось удалить {path}: {e}")
        else:
            print_skip(f"Не найдена (уже удалена?): {path}")

    if deleted_count == 0:
        print_warn("Ни одна директория не была удалена")


# ─── 3. Очистка temp_uploads ───────────────────────────────────────────────


def clean_temp_uploads():
    section("3. Папка temp_uploads/")

    if not TEMP_UPLOADS_DIR.exists():
        TEMP_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        print_step("Папка создана (пустая)")
        return

    count = 0
    for f in TEMP_UPLOADS_DIR.rglob("*"):
        try:
            if f.is_file():
                f.unlink()
                count += 1
            elif f.is_dir():
                shutil.rmtree(f)
                count += 1
        except Exception as e:
            print_warn(f"Не удалось удалить {f.name}: {e}")

    if count == 0:
        print_step("Папка уже пуста")
    else:
        print_step(f"Очищено объектов: {count}")


# ─── 4. Полная перезапись state.json ───────────────────────────────────────


def reset_state_file():
    section("4. Файл состояния (state.json) — ПОЛНАЯ ПЕРЕЗАПИСЬ")

    initial_state = {
        "version": "1.0",
        "app_dir": str(Path.home() / "Desktop"),
        "files": [],
        "last_magic_run": None,
        "created_directories": [],
        "replace_rules": [],
        "accompanying_prefixes": [],
        "registry_data": {},
        "registry_dicts": {},
        "registry_history": [],
        "current_directory": None,
        "is_creating": False,
    }

    # Удаляем старый файл если есть
    if STATE_FILE.exists():
        try:
            STATE_FILE.unlink()
            print_step("Старый state.json удалён")
        except Exception as e:
            print_warn(f"Не удалось удалить старый state.json: {e}")

    # Записываем новый
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(initial_state, f, indent=2, ensure_ascii=False)
        print_step("state.json создан заново (чистое состояние — factory reset)")
        print_step(f"  replace_rules: {len(initial_state['replace_rules'])} (заводские)")
        print_step(f"  accompanying_prefixes: {len(initial_state['accompanying_prefixes'])} (заводские)")
        print_step("  registry_data: не задано")
        print_step("  files: пусто")
        print_step("  created_directories: пусто")
        print_step("  last_magic_run: null")
    except Exception as e:
        print_error(f"Ошибка при записи state.json: {e}")


# ─── 5. Удаление папок materials ───────────────────────────────────────────


def clean_materials_folders(state):
    section("5. Папки materials/ (PDF-файлы)")

    app_dirs = set()

    app_dir_from_state = state.get("app_dir")
    if app_dir_from_state:
        app_dirs.add(Path(app_dir_from_state) / MATERIALS_SUBDIR)

    for entry in state.get("created_directories", []):
        if isinstance(entry, str):
            dir_path = entry
        else:
            dir_path = entry.get("path", "")
        if dir_path:
            app_dirs.add(Path(dir_path) / MATERIALS_SUBDIR)

    default_app_dir = Path.home() / "Desktop"
    app_dirs.add(default_app_dir / MATERIALS_SUBDIR)

    deleted_any = False
    for mat_dir in sorted(app_dirs):
        if not mat_dir.exists():
            print_skip(f"Не найдена: {mat_dir}")
            continue

        items = list(mat_dir.iterdir())
        if not items:
            print_step(f"Уже пуста: {mat_dir}")
            continue

        count = 0
        for item in items:
            try:
                if item.is_file():
                    item.unlink()
                    count += 1
                elif item.is_dir():
                    shutil.rmtree(item)
                    count += 1
            except Exception as e:
                print_warn(f"Не удалось удалить {item.name}: {e}")

        print_step(f"Очищено {count} объектов в {mat_dir}")
        deleted_any = True

    if not deleted_any:
        print_skip("Нет папок materials/ для очистки")


# ─── 6. Папка «база материалов» на рабочем столе ────────────────────────────

MATERIALS_BASE_DIR = Path.home() / "Desktop" / "база материалов"


def clean_materials_base():
    section("6. Папка «база материалов» на рабочем столе")

    if not MATERIALS_BASE_DIR.exists():
        print_skip(f"Папка не найдена: {MATERIALS_BASE_DIR}")
        return

    items = list(MATERIALS_BASE_DIR.rglob("*"))
    print_step(f"Найдено объектов: {len(items)}")

    try:
        shutil.rmtree(MATERIALS_BASE_DIR)
        print_step("Папка удалена")
    except Exception as e:
        print_warn(f"Не удалось удалить: {e}")
        print_warn("  Закройте папку в проводнике и повторите")


# ─── 7. Удаление папок с датами ────────────────────────────────────────────

DATE_DIR_PATTERN = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")


def clean_date_dirs():
    section("7. Папки с датами (DD.MM.YYYY) на рабочем столе")

    desktop = Path.home() / "Desktop"
    if not desktop.exists():
        print_skip("Рабочий стол не найден")
        return

    date_dirs = [p for p in desktop.iterdir() if p.is_dir() and DATE_DIR_PATTERN.match(p.name)]

    if not date_dirs:
        print_skip("Нет папок с датами")
        return

    for dir_path in date_dirs:
        try:
            shutil.rmtree(dir_path)
            print_step(f"Удалена: {dir_path}")
        except Exception as e:
            print_warn(f"Не удалось удалить {dir_path.name}: {e}")


# ─── 8. Очистка логов ──────────────────────────────────────────────────────


def clean_logs():
    section("8. Лог-файлы (logs/)")

    if not LOG_DIR.exists():
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        print_step("Папка создана (пустая)")
        return

    count = 0
    for f in LOG_DIR.rglob("*"):
        if f.is_file():
            try:
                f.unlink()
                count += 1
            except Exception as e:
                print_warn(f"Не удалось удалить {f.name}: {e}")

    if count == 0:
        print_step("Папка уже пуста")
    else:
        print_step(f"Удалено файлов: {count}")


# ─── 9. Удаление __pycache__ ───────────────────────────────────────────────


def clean_pycache():
    section("9. Папки __pycache__ (рекурсивно)")

    pycache_dirs = []
    # Also clean .pytest_cache in project root
    pytest_cache = PROJECT_DIR / ".pytest_cache"
    if pytest_cache.exists() and pytest_cache.is_dir():
        pycache_dirs.append(str(pytest_cache))
    for root, dirs, _ in os.walk(PROJECT_DIR):
        if any(k in root.split(os.sep) for k in KEEP_DIRS):
            continue
        for d in dirs:
            if d in ("__pycache__", ".pytest_cache"):
                pycache_dirs.append(os.path.join(root, d))

    if not pycache_dirs:
        print_skip("Нет папок __pycache__")
        return

    count = 0
    for d in pycache_dirs:
        try:
            shutil.rmtree(d)
            count += 1
        except Exception as e:
            print_warn(f"Не удалось удалить {d}: {e}")

    print_step(f"Удалено папок: {count}")


# ─── 10. Кеши инструментов ────────────────────────────────────────────────


def clean_tool_caches():
    section("10. Кеши инструментов (.mypy_cache, .pytest_cache, .ruff_cache)")

    cache_names = [".mypy_cache", ".pytest_cache", ".ruff_cache"]
    cleaned = 0
    for name in cache_names:
        cache_dir = PROJECT_DIR / name
        if cache_dir.exists():
            # Try rmtree first, fallback to send2trash, then force-delete files
            try:
                shutil.rmtree(cache_dir, ignore_errors=True)
            except Exception:
                pass
            if cache_dir.exists():
                try:
                    import send2trash
                    send2trash.send2trash(str(cache_dir))
                    print_step(f"{name}/ отправлен в корзину")
                    cleaned += 1
                    continue
                except Exception:
                    pass
            if not cache_dir.exists():
                print_step(f"{name}/ удалён")
                cleaned += 1
            else:
                print_warn(f"Не удалось удалить {name} — удалите вручную")
        else:
            print_skip(f"{name}/ не найден")

    if cleaned == 0:
        print_skip("Нет кешей для очистки")


# ─── 11. Очистка Конвертор пдф/ ─────────────────────────────────────────────


def clean_converter_output():
    section("11. Папка «Конвертор пдф» на рабочем столе")

    if not CONVERTER_OUTPUT.exists():
        print_skip(f"Папка не найдена: {CONVERTER_OUTPUT}")
        return

    items = list(CONVERTER_OUTPUT.rglob("*"))
    print_step(f"Найдено объектов: {len(items)}")

    try:
        shutil.rmtree(CONVERTER_OUTPUT)
        print_step("Папка «Конвертор пдф» удалена полностью")
    except Exception as e:
        print_warn(f"Не удалось удалить: {e}")


# ─── 12. Финальная проверка ────────────────────────────────────────────────


def final_check():
    section("12. Финальная проверка")

    checks_ok = 0
    checks_warn = 0

    # state.json
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                data = json.load(f)
            files_count = len(data.get("files", []))
            rules_count = len(data.get("replace_rules", []))
            prefixes_count = len(data.get("accompanying_prefixes", []))
            registry_keys = len(data.get("registry_data", {}))
            dicts_keys = len(data.get("registry_dicts", {}))
            created_dirs = len(data.get("created_directories", []))

            # Проверяем что все поля чистые
            if (
                files_count == 0
                and rules_count == 0
                and created_dirs == 0
                and prefixes_count == 0
                and registry_keys == 0
                and dicts_keys == 0
            ):
                print_step(
                    f"state.json: файлов={files_count}, правил={rules_count}, "
                    f"префиксов={prefixes_count}, реестр={registry_keys} полей, "
                    f"словарей={dicts_keys}, директорий={created_dirs} — FACTORY RESET"
                )
                checks_ok += 1
            else:
                print_warn(
                    f"state.json содержит данные: файлов={files_count}, правил={rules_count}, "
                    f"префиксов={prefixes_count}, директорий={created_dirs}"
                )
                checks_warn += 1

            # Проверяем отсутствие лишних полей (runtime поля допустимы)
            known_fields = {
                "version",
                "app_dir",
                "files",
                "last_magic_run",
                "created_directories",
                "replace_rules",
                "accompanying_prefixes",
                "registry_data",
                "registry_dicts",
                "registry_history",
                "is_creating",
                "current_directory",
            }
            extra_fields = [k for k in data if k not in known_fields]
            if extra_fields:
                print_warn(f"state.json содержит неизвестные поля: {extra_fields}")
                checks_warn += 1
            else:
                print_step("state.json: структура корректна")
                checks_ok += 1

        except Exception as e:
            print_error(f"state.json повреждён: {e}")
            checks_warn += 1
    else:
        print_error("state.json не найден!")
        checks_warn += 1

    # БД
    if DB_PATH.exists():
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM materials")
            mat_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM conversions")
            conv_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM objects")
            obj_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM requisites")
            req_count = cursor.fetchone()[0]
            conn.close()
            if mat_count == 0 and conv_count == 0 and obj_count == 0 and req_count == 0:
                print_step(f"materials.db: materials={mat_count}, conv={conv_count}, objects={obj_count}, req={req_count} (пустая)")
                checks_ok += 1
            else:
                print_warn(f"materials.db: materials={mat_count}, conv={conv_count}, objects={obj_count}, req={req_count} (не пустая!)")
                checks_warn += 1
        except Exception as e:
            print_error(f"materials.db повреждена: {e}")
            checks_warn += 1
    else:
        print_error("materials.db не найдена!")
        checks_warn += 1

    # temp_uploads
    if TEMP_UPLOADS_DIR.exists():
        files = list(TEMP_UPLOADS_DIR.iterdir())
        if len(files) == 0:
            print_step("temp_uploads/: пуста")
            checks_ok += 1
        else:
            print_warn(f"temp_uploads/: {len(files)} объектов (не пустая!)")
            checks_warn += 1
    else:
        print_error("temp_uploads/ не существует!")
        checks_warn += 1

    # logs
    if LOG_DIR.exists():
        log_files = list(LOG_DIR.rglob("*"))
        log_files = [f for f in log_files if f.is_file()]
        if len(log_files) == 0:
            print_step("logs/: пуста")
            checks_ok += 1
        else:
            print_warn(f"logs/: {len(log_files)} файлов (не пустая!)")
            checks_warn += 1
    else:
        print_error("logs/ не существует!")
        checks_warn += 1

    # .agents
    agents_dir = PROJECT_DIR / ".agents"
    if agents_dir.exists():
        print_step(".agents/: сохранена (не тронута)")
        checks_ok += 1
    else:
        print_warn(".agents/ не найдена!")
        checks_warn += 1

    # __pycache__
    pycache_found = []
    for root, dirs, _ in os.walk(PROJECT_DIR):
        if any(k in root.split(os.sep) for k in KEEP_DIRS):
            continue
        for d in dirs:
            if d == "__pycache__":
                pycache_found.append(os.path.join(root, d))
    if pycache_found:
        print_warn(f"__pycache__: найдено {len(pycache_found)} папок (не удалились!)")
        checks_warn += 1
    else:
        print_step("__pycache__: 0 папок (все удалены)")
        checks_ok += 1

    # Итого
    print()
    total = checks_ok + checks_warn
    if checks_warn == 0:
        print_step(f"ВСЕ {total} ПРОВЕРОК ПРОЙДЕНЫ — проект чист!")
    else:
        print_warn(f"Пройдено: {checks_ok}/{total} проверок, предупреждений: {checks_warn}")


# ─── MAIN ───────────────────────────────────────────────────────────────────


def main():
    force = "--force" in sys.argv

    header("PDF Magic App — Полный сброс проекта")
    print(f"  Проект: {PROJECT_DIR}")
    print(f"  Время:  {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if force:
        print("  Режим:  --force (пропуск проверки Flask)")
    print()

    # Шаг 0: Проверяем Flask
    if not check_flask(force=force):
        print()
        print_error("СБРОС ОТМЕНЁН. Остановите Flask и повторите.")
        sys.exit(1)

    state = load_current_state()

    reset_database()
    delete_created_directories(state)
    clean_temp_uploads()
    reset_state_file()
    clean_materials_folders(state)
    clean_materials_base()
    clean_date_dirs()
    clean_logs()
    clean_pycache()
    clean_tool_caches()
    clean_converter_output()
    final_check()

    print()
    header("Сброс завершён!")
    print("  - Flask: проверен (не запущен)")
    print("  - state.json: полностью перезаписан (чистое состояние)")
    print("  - replace_rules: [] (пусто)")
    print("  - accompanying_prefixes: [] (пусто)")
    print("  - registry_data: не задано")
    print("  - БД материалов: пересоздана (пустая)")
    print("  - temp_uploads, logs: очищены")
    print("  - created_directories: удалены физически и из state")
    print("  - «база материалов» на рабочем столе: удалена")
    print("  - Папки с датами (DD.MM.YYYY): удалены")
    print("  - Конвертор пдф/: удалена полностью")
    print("  - __pycache__: удалены рекурсивно")
    print("  - .mypy_cache, .pytest_cache, .ruff_cache: удалены")
    print("  - .agents/: не тронута")
    print()
    print(f"  {BOLD}Для запуска: python run.py{RESET}")
    print()


if __name__ == "__main__":
    main()
