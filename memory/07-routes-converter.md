# routes/converter.py — Конвертация PDF

**Путь**: `routes/converter.py` (420 строк)

## Что делает

Конвертация PDF-файлов через Java CLI (OpenDataLoader) с отслеживанием прогресса.

## Эндпоинты

| Путь | Метод | Описание |
|---|---|---|
| `/api/converter/convert` | POST | Запуск конвертации |
| `/api/converter/progress/<job_id>` | GET | Прогресс задачи |
| `/api/converter/download/<job_id>` | GET | Скачивание результата |
| `/api/converter/history` | GET | История конвертаций |
| `/api/converter/history/<id>` | DELETE | Удаление из истории |

## Допустимые форматы

`markdown`, `json`, `html`, `text`, `tagged-pdf`

## Поведение

1. Задачи запускаются в фоновом потоке (daemon)
2. Прогресс отслеживается через парсинг stdout Java
3. Время конвертации: ~2 сек/страница (эстимация)
4. Результаты читаются из текстовых файлов (макс. 50000 символов preview)
5. История хранится в SQLite (таблица `conversions`)

## Внутренние функции

- `_find_jar()` — находит JAR-файл OpenDataLoader
- `_run_conversion(job_id, pdf_path, fmt)` — основной воркер
- `_update_job(job_id, **kwargs)` — обновление состояния задачи

## Зависимости

- `routes.core` (APP_DIR, logger)
- `utils.database` (add_conversion, get_conversions)
- `pypdf` (чтение страниц)
- `subprocess` (запуск Java)

---
Связано: [[03-routes-core]] | [[15-utils-database]]
