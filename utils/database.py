"""
SQLite database for materials — with type hints.
"""

import sqlite3
from pathlib import Path

DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "materials.db"


def get_db() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    conn = get_db()
    try:
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
        conn.commit()
    finally:
        conn.close()


def add_material(
    doc_name: str,
    material_name: str,
    number: str,
    date: str,
    producer: str,
    filename: str,
    original_filename: str,
) -> int:
    conn = get_db()
    try:
        cursor = conn.execute(
            """INSERT INTO materials (doc_name, material_name, number, date, producer, filename, original_filename)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                doc_name,
                material_name,
                number or "",
                date or "",
                producer or "",
                filename,
                original_filename,
            ),
        )
        conn.commit()
        return cursor.lastrowid or 0
    finally:
        conn.close()


def get_all_materials() -> list[dict[str, object]]:
    conn = get_db()
    try:
        cursor = conn.execute(
            """SELECT id, doc_name, material_name, number, date, producer, filename, original_filename, created_at
               FROM materials ORDER BY created_at DESC"""
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_material(material_id: int) -> dict[str, object] | None:
    conn = get_db()
    try:
        cursor = conn.execute("SELECT * FROM materials WHERE id = ?", (material_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def delete_material(material_id: int) -> bool:
    conn = get_db()
    try:
        cursor = conn.execute("DELETE FROM materials WHERE id = ?", (material_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def search_materials(query: str) -> list[dict[str, object]]:
    conn = get_db()
    try:
        like = f"%{query}%"
        cursor = conn.execute(
            """SELECT id, doc_name, material_name, number, date, producer, filename, original_filename, created_at
               FROM materials
               WHERE doc_name LIKE ? OR material_name LIKE ? OR number LIKE ? OR producer LIKE ?
               ORDER BY created_at DESC""",
            (like, like, like, like),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


# ─── Converter ────────────────────────────────────────────────────


def init_converter_db() -> None:
    conn = get_db()
    try:
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
        conn.commit()
    finally:
        conn.close()


def add_conversion(filename: str, fmt: str, source_path: str) -> int:
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO conversions (filename, output_format, source_path) VALUES (?, ?, ?)",
            (filename, fmt, source_path),
        )
        conn.commit()
        return cursor.lastrowid or 0
    finally:
        conn.close()


def get_conversions() -> list[dict[str, object]]:
    conn = get_db()
    try:
        cursor = conn.execute("SELECT * FROM conversions ORDER BY created_at DESC LIMIT 50")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def delete_conversion(conv_id: int) -> bool:
    conn = get_db()
    try:
        cursor = conn.execute("DELETE FROM conversions WHERE id = ?", (conv_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ─── Requisites (реквизиты) ───────────────────────────────────────


def init_requisites_db() -> None:
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS objects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS requisites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                object_id INTEGER NOT NULL UNIQUE,
                developer_name TEXT DEFAULT '',
                developer_ogrn TEXT DEFAULT '',
                developer_inn TEXT DEFAULT '',
                developer_address TEXT DEFAULT '',
                developer_phone TEXT DEFAULT '',
                builder_name TEXT DEFAULT '',
                builder_ogrn TEXT DEFAULT '',
                builder_inn TEXT DEFAULT '',
                builder_address TEXT DEFAULT '',
                builder_phone TEXT DEFAULT '',
                builder_sro_number TEXT DEFAULT '',
                builder_sro_name TEXT DEFAULT '',
                builder_sro_ogrn TEXT DEFAULT '',
                builder_sro_inn TEXT DEFAULT '',
                designer_name TEXT DEFAULT '',
                designer_ogrn TEXT DEFAULT '',
                designer_inn TEXT DEFAULT '',
                designer_sro_number TEXT DEFAULT '',
                designer_sro_name TEXT DEFAULT '',
                designer_sro_ogrn TEXT DEFAULT '',
                designer_sro_inn TEXT DEFAULT '',
                designer_address TEXT DEFAULT '',
                designer_phone TEXT DEFAULT '',
                control_name TEXT DEFAULT '',
                control_ogrn TEXT DEFAULT '',
                control_inn TEXT DEFAULT '',
                control_address TEXT DEFAULT '',
                control_phone TEXT DEFAULT '',
                control_sro_number TEXT DEFAULT '',
                control_sro_name TEXT DEFAULT '',
                control_sro_ogrn TEXT DEFAULT '',
                control_sro_inn TEXT DEFAULT '',
                rep_developer_position TEXT DEFAULT '',
                rep_developer_name TEXT DEFAULT '-',
                rep_developer_doc TEXT DEFAULT '',
                rep_builder_position TEXT DEFAULT '',
                rep_builder_name TEXT DEFAULT '-',
                rep_builder_doc TEXT DEFAULT '',
                rep_builder_ctrl_position TEXT DEFAULT '',
                rep_builder_ctrl_name TEXT DEFAULT '-',
                rep_builder_ctrl_doc TEXT DEFAULT '',
                rep_designer_position TEXT DEFAULT '',
                rep_designer_name TEXT DEFAULT '-',
                rep_designer_doc TEXT DEFAULT '',
                rep_contractor_position TEXT DEFAULT '',
                rep_contractor_name TEXT DEFAULT '-',
                rep_contractor_doc TEXT DEFAULT '',
                rep_others_org TEXT DEFAULT '',
                rep_others_position TEXT DEFAULT '',
                rep_others_name TEXT DEFAULT '-',
                rep_others_doc TEXT DEFAULT '',
                rep_others_continued TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (object_id) REFERENCES objects(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
    finally:
        conn.close()


# ─── Objects CRUD ─────────────────────────────────────────────────


def get_objects() -> list[dict[str, object]]:
    conn = get_db()
    try:
        cursor = conn.execute("SELECT * FROM objects ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def add_object(name: str) -> int:
    conn = get_db()
    try:
        cursor = conn.execute("INSERT INTO objects (name) VALUES (?)", (name,))
        conn.commit()
        return cursor.lastrowid or 0
    finally:
        conn.close()


def delete_object(obj_id: int) -> bool:
    conn = get_db()
    try:
        cursor = conn.execute("DELETE FROM objects WHERE id = ?", (obj_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ─── Requisites CRUD ──────────────────────────────────────────────


def get_requisites(obj_id: int) -> dict[str, object] | None:
    conn = get_db()
    try:
        cursor = conn.execute("SELECT * FROM requisites WHERE object_id = ?", (obj_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def save_requisites(obj_id: int, data: dict[str, str]) -> None:
    conn = get_db()
    try:
        existing = conn.execute("SELECT id FROM requisites WHERE object_id = ?", (obj_id,)).fetchone()
        fields = [
            "developer_name",
            "developer_ogrn",
            "developer_inn",
            "developer_address",
            "developer_phone",
            "builder_name",
            "builder_ogrn",
            "builder_inn",
            "builder_address",
            "builder_phone",
            "builder_sro_number",
            "builder_sro_name",
            "builder_sro_ogrn",
            "builder_sro_inn",
            "designer_name",
            "designer_ogrn",
            "designer_inn",
            "designer_sro_number",
            "designer_sro_name",
            "designer_sro_ogrn",
            "designer_sro_inn",
            "designer_address",
            "designer_phone",
            "control_name",
            "control_ogrn",
            "control_inn",
            "control_address",
            "control_phone",
            "control_sro_number",
            "control_sro_name",
            "control_sro_ogrn",
            "control_sro_inn",
            "rep_developer_position",
            "rep_developer_name",
            "rep_developer_doc",
            "rep_builder_position",
            "rep_builder_name",
            "rep_builder_doc",
            "rep_builder_ctrl_position",
            "rep_builder_ctrl_name",
            "rep_builder_ctrl_doc",
            "rep_designer_position",
            "rep_designer_name",
            "rep_designer_doc",
            "rep_contractor_position",
            "rep_contractor_name",
            "rep_contractor_doc",
            "rep_others_org",
            "rep_others_position",
            "rep_others_name",
            "rep_others_doc",
            "rep_others_continued",
        ]
        values = [data.get(f, "") for f in fields]
        if existing:
            sets = ", ".join(f"{f} = ?" for f in fields)
            conn.execute(
                f"UPDATE requisites SET {sets} WHERE object_id = ?",
                values + [obj_id],  # type: ignore
            )
        else:
            placeholders = ", ".join("?" * len(fields))
            conn.execute(
                f"INSERT INTO requisites (object_id, {', '.join(fields)}) VALUES (?, {placeholders})",
                [obj_id] + values,  # type: ignore
            )
        conn.commit()
    finally:
        conn.close()
