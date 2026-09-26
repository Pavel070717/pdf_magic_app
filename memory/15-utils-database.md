# utils/database.py — SQLite хранилище

**Путь**: `utils/database.py` (340 строк)

## Что делает

Полный CRUD для SQLite базы данных. 4 таблицы: материалы, конвертации, объекты, реквизиты.

## Путь к БД

```
PROJECT_DIR/data/materials.db
```

## Таблицы

### materials — Материалы

| Поле | Тип | Описание |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `doc_name` | TEXT | Тип документа |
| `material_name` | TEXT | Название материала |
| `number` | TEXT | Номер |
| `date` | TEXT | Дата паспорта |
| `producer` | TEXT | Производитель |
| `unit` | TEXT | Единица измерения (для datalist по ранее введённым) |
| `arrival_date` | TEXT | Дата поступления (ISO `YYYY-MM-DD`) — имя папки хранения |
| `quantity` | REAL | Количество (default 0) |
| `folder` | TEXT | Имя папки поступления |
| `filename` | TEXT | Относительный путь `folder/filename` |
| `original_filename` | TEXT | Оригинальное имя |
| `created_at` | TIMESTAMP | Время создания |

### conversions — Конвертации

| Поле | Тип | Описание |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `filename` | TEXT | Имя файла |
| `output_format` | TEXT | Формат вывода |
| `source_path` | TEXT | Исходный путь |
| `status` | TEXT | Статус |
| `created_at` | TIMESTAMP | Время создания |

### objects — Объекты

| Поле | Тип | Описание |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `name` | TEXT UNIQUE | Название объекта |
| `created_at` | TIMESTAMP | Время создания |

### requisites — Реквизиты

| Поле | Тип | Описание |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `object_id` | INTEGER FK | Ссылка на objects (CASCADE) |
| `dev_*` | TEXT | Реквизиты застройщика (11 полей) |
| `builder_*` | TEXT | Реквизиты подрядчика (11 полей) |
| `designer_*` | TEXT | Реквизиты проектировщика (6 полей) |
| `control_*` | TEXT | Технадзор (6 полей) |
| `rep_*` | TEXT | Представители (12 полей) |
| `created_at` | TIMESTAMP | Время создания |

## Ключевые функции

### Материалы
- `_ensure_materials_new_schema(conn)` — миграция: добавляет недостающие колонки (`arrival_date`, `quantity`, `folder`, `unit`) через `ALTER TABLE ADD COLUMN` без потери данных + индексы
- `add_material(...)` → int — добавление (последние параметры `arrival_date`, `quantity`, `folder`, `unit` со значениями по умолчанию)
- `get_all_materials()` → list[dict] — все (DESC по created_at)
- `get_material(id)` → dict | None
- `delete_material(id)` → bool
- `search_materials(query)` → list[dict] — поиск по полям
- `get_material_passports()` → list[dict] — уникальные комбинации (doc_name, material_name, number, date, producer, unit) + label
- `get_material_units()` → list[str] — уникальные ранее введённые единицы измерения
- `count_materials_in_folder(folder)` → int — число строк в папке поступления
- `reset_materials()` → None — обнуляет только таблицу материалов

### Конвертации
- `add_conversion(filename, fmt, source_path)` → int
- `get_conversions()` → list[dict] — последние 50
- `delete_conversion(id)` → bool

### Объекты и реквизиты
- `get_objects()` → list[dict]
- `add_object(name)` → int
- `delete_object(id)` → bool — CASCADE удалит реквизиты
- `get_requisites(obj_id)` → dict | None
- `save_requisites(obj_id, data)` — UPSERT (INSERT или UPDATE)

## Поведение

- Все соединения закрываются в `finally`
- WAL-режим для параллельного чтения
- `foreign_keys = ON` для поддержкиCASCADE

---
Связано: [[11-routes-materials]] | [[07-routes-converter]] | [[13-routes-requisites]]
