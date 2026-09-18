"""
SQLite database for МСГ (месячно-суточный график) / ОЖР (общий журнал работ).

Хранение: одна таблица ozh_items. Каждая запись журнала — отдельная строка.
МСГ-представление агрегирует записи по ключу (работа, позиция, единица изм.)
в порядке первого появления в журнале (как заполнено в ОЖР).
"""

import sqlite3
from pathlib import Path

DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "msg.db"


def get_db() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_msg_db() -> None:
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ozh_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                work_name TEXT NOT NULL,
                position TEXT NOT NULL DEFAULT '',
                unit TEXT NOT NULL DEFAULT '',
                volume REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
    finally:
        conn.close()


def add_ozh_items(date: str, items: list[dict]) -> int:
    """Сохраняет список работ за один день. Возвращает число строк."""
    conn = get_db()
    try:
        count = 0
        for it in items:
            try:
                volume = float(it.get("volume", 0) or 0)
            except (TypeError, ValueError):
                volume = 0.0
            cursor = conn.execute(
                """INSERT INTO ozh_items (date, work_name, position, unit, volume)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    date,
                    str(it.get("work_name", "")).strip(),
                    str(it.get("position", "")).strip(),
                    str(it.get("unit", "")).strip(),
                    volume,
                ),
            )
            count += cursor.rowcount
        conn.commit()
        return count
    finally:
        conn.close()


def get_ozh_items(date: str | None = None) -> list[dict]:
    conn = get_db()
    try:
        if date:
            cursor = conn.execute(
                "SELECT * FROM ozh_items WHERE date = ? ORDER BY id", (date,)
            )
        else:
            cursor = conn.execute("SELECT * FROM ozh_items ORDER BY date DESC, id")
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def delete_ozh_item(item_id: int) -> bool:
    conn = get_db()
    try:
        cursor = conn.execute("DELETE FROM ozh_items WHERE id = ?", (item_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_available_months() -> list[str]:
    conn = get_db()
    try:
        cursor = conn.execute(
            "SELECT DISTINCT substr(date, 1, 7) AS month FROM ozh_items ORDER BY month"
        )
        return [r["month"] for r in cursor.fetchall()]
    finally:
        conn.close()


def get_month_rows(month: str) -> list[dict]:
    """Агрегированные строки для МСГ.

    Группировка: (работа, позиция, единица изм.) — при 100% совпадении
    объёмы суммируются по дням. Порядок: как впервые встретилось в ОЖР.
    """
    conn = get_db()
    try:
        cursor = conn.execute(
            "SELECT * FROM ozh_items WHERE substr(date, 1, 7) = ? ORDER BY id",
            (month,),
        )
        records = [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

    order: list[tuple] = []
    grouped: dict[tuple, dict] = {}
    for r in records:
        key = (
            str(r["work_name"]).strip(),
            str(r["position"]).strip(),
            str(r["unit"]).strip(),
        )
        if key not in grouped:
            order.append(key)
            grouped[key] = {
                "work_name": key[0],
                "position": key[1],
                "unit": key[2],
                "days": {},
            }
        day = int(str(r["date"])[8:10])
        grouped[key]["days"][day] = grouped[key]["days"].get(day, 0.0) + r["volume"]
    return [grouped[k] for k in order]
