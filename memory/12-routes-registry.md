# routes/registry.py — Данные реестра

**Путь**: `routes/registry.py` (108 строк)

## Что делает

Управление данными реестра исполнительной документации.

## Эндпоинты

| Путь | Метод | Описание |
|---|---|---|
| `/api/registry/form` | GET | HTML-форма реестра |
| `/api/registry/data` | GET | JSON с data, dicts, history |
| `/api/registry/data` | POST | Сохранение данных |

## Поля реестра

| Поле | Описание |
|---|---|
| `org_name` | Название организации |
| `object_name` | Название объекта |
| `customer` | Заказчик |
| `sk_representative` | Представитель СК |
| `general_contractor` | Генеральный подрядчик |
| `work_executor` | Исполнитель работ |
| `registry_number` | Номер реестра |
| `signature_sdal` | Подпись "Сдал" |
| `signature_proveril` | Подпись "Проверил" |
| `signature_prinyal` | Подпись "Принял" |

## Словари автодополнения

`registry_dicts` — списки значений для полей формы. Новые значения добавляются без дубликатов.

## Зависимости

- `routes.core` (load_state, save_state)

---
Связано: [[09-routes-magic]] | [[18-utils-excel-registry]]
