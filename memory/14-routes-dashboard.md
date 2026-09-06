# routes/dashboard.py — Дашборд

**Путь**: `routes/dashboard.py` (134 строки)

## Что делает

API дашборда — агрегированная статистика приложения.

## Эндпоинты

| Путь | Метод | Описание |
|---|---|---|
| `/api/dashboard/stats` | GET | Статистика |

## Возвращаемые данные

```json
{
  "total_files": 5,
  "total_dirs": 12,
  "total_materials": 45,
  "total_rules": 3,
  "last_activity": "2026-09-06T12:00:00",
  "activity": [
    {"date": "2026-09-06", "files": 2, "dirs": 1},
    ...
  ],
  "recent_events": [
    {"type": "files_copied", "count": 5, "time": "..."},
    {"type": "registry_created", "count": 1, "time": "..."}
  ]
}
```

## Источники данных

- `total_files` — из `state["files"]`
- `total_dirs` — из `state["created_directories"]`
- `total_materials` — из SQLite (таблица `materials`)
- `total_rules` — из `state["replace_rules"]`
- `last_activity` — из `state["last_magic_run"]`
- `activity` — агрегация за 7 дней
- `recent_events` — последние события

## Зависимости

- `routes.core` (load_state, APP_DIR)
- `utils.database` (get_all_materials)

---
Связано: [[03-routes-core]] | [[15-utils-database]]
