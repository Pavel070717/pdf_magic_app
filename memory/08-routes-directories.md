# routes/directories.py — Управление директориями

**Путь**: `routes/directories.py` (388 строк)

## Что делает

CRUD-операции с директориями проектов на рабочем столе.

## Эндпоинты

| Путь | Метод | Описание |
|---|---|---|
| `/api/directory/create` | POST | Создание папки проекта |
| `/api/directory/delete` | POST | Удаление в корзину |
| `/api/directory/add-folder` | POST | Добавление подпапки |
| `/api/directory/rename` | POST | Переименование |
| `/api/directory/recreate` | POST | Пересоздание из state |
| `/api/directory/scan` | POST | Сканирование ФС |
| `/api/directory/current` | GET | Текущая директория |
| `/api/directories/list` | GET | Список всех директорий |

## Структура директорий

```
Desktop/
└── DD.MM.YYYY/
    └── шифр_проекта/
        ├── подпапка1/
        └── подпапка2/
```

## Безопасность

- Проверка path traversal: путь должен быть на рабочем столе
- Флаг `is_creating` защищает от параллельных операций
- Удаление только через `send2trash` (безопасно)

## Зависимости

- `routes.core` (APP_DIR, ensure_app_dirs, деревья папок)
- `utils.state` (load_state, save_state)
- `send2trash` (безопасное удаление)

---
Связано: [[03-routes-core]] | [[09-routes-magic]]
