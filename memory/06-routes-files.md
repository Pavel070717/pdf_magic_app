# routes/files.py — Управление файлами

**Путь**: `routes/files.py` (199 строк)

## Что делает

Загрузка, удаление и реорганизация файлов для обработки.

## Эндпоинты

| Путь | Метод | Описание |
|---|---|---|
| `/api/files` | GET | Список файлов с порядком |
| `/api/files/add` | POST | Загрузка файлов (multipart) |
| `/api/files/remove` | POST | Удаление файла |
| `/api/files/reorder` | POST | Переупорядочивание |

## Допустимые расширения

`.pdf`, `.jpg`, `.jpeg`, `.png`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.dwg`, `.dxf`

## Поведение

- Файлы сохраняются в `temp_uploads/`
- Проверяется расширение и MIME-тип
- Дублирующиеся имена получают суффикс `_1`, `_2` и т.д.
- Каждому файлу присваивается UUID
- При удалении физический файл удаляется с диска

## Формат ответа

```json
{
  "files": [
    {
      "id": "uuid",
      "name": "filename.pdf",
      "display_order": 0
    }
  ]
}
```

## Зависимости

- `routes.core` (TEMP_UPLOADS_DIR, sanitize_text)
- `utils.state` (load_state, save_state)

---
Связано: [[03-routes-core]] | [[09-routes-magic]]
