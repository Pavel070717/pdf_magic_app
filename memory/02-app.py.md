# app.py — Точка входа приложения

**Путь**: `app.py` (213 строк)

## Что делает

Главный файл приложения. Создаёт Flask-приложение, регистрирует HTML-маршруты, настраивает CORS, логирование и запускает production-сервер Waitress.

## Конфигурация Flask

- `MAX_CONTENT_LENGTH` = 100 МБ (максимум загружаемый файл)
- `SECRET_KEY` из переменной окружения или随机ный
- CORS: `localhost:5000`, `localhost:5173`, `localhost:5174`

## HTML-маршруты

| Путь | Шаблон | Страница |
|---|---|---|
| `/` | `dashboard.html` | Дашборд (главная) |
| `/directories/create` | `directories.html` | Управление директориями |
| `/converter` | `converter.html` | Конвертер PDF |
| `/aocr` | `aocr.html` | Генерация АОСР |
| `/requisites` | `requisites.html` | Реквизиты объектов |
| `/rules` | `rules.html` | Правила замены |
| `/materials` | `materials.html` | База материалов |

## API-эндпоинты

| Путь | Описание |
|---|---|
| `/api/health` | Health check (возвращает `{"status": "ok"}`) |
| `/static/<path>` | Статические файлы |

## Запуск (функция main)

1. Убивает зомби-процессы на порту 5000 (Windows: `netstat` + `taskkill`)
2. Создаёт необходимые директории (`ensure_app_dirs()`)
3. Инициализирует БД (`init_db()`, `init_converter_db()`, `init_requisites_db()`)
4. Открывает браузер через 1.5 сек (в фоновом потоке)
5. Запускает Waitress на `127.0.0.1:5000`
6. Обрабатывает `SIGINT` и Windows `SetConsoleCtrlHandler` для graceful shutdown

## Логирование

- Запросы к `/api/*` логируются (начало и конец)
- werkzeug логи отключены (WARNING level)
- Логи в `logs/app.log` (DEBUG, 10MB, 5 бэкапов)

## Зависимости

- `flask`, `flask_cors`, `waitress`, `python-dotenv`
- `routes.core` (константы, хелперы)
- `utils.database` (инициализация БД)

---
Связано: [[00-Обзор-проекта]] | [[01-Архитектура]] | [[03-routes-core]]
