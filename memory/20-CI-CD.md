# CI/CD — GitHub Actions

## Конфигурация

**Файл**: `.github/workflows/ci.yml`

**Триггер**: push на `master`

**Матрица**: Python 3.10, 3.12 на `ubuntu-latest`

## Проверки

| Инструмент | Что проверяет |
|---|---|
| `flake8` | Стиль кода (PEP 8) |
| `black` | Форматирование |
| `isort` | Сортировка импортов |
| `mypy` | Типизация |
| `bandit` | Безопасность |
| `safety` | Уязвимости зависимостей |
| `pytest` | Тесты с покрытием |

## Установка зависимостей

```bash
pip install flake8 black isort mypy bandit safety pytest pytest-cov
```

**Примечание**: CI НЕ устанавливает `requirements.txt`. Только dev-зависимости для проверок.

## Запуск

```bash
black --check .
isort --profile black --check .
flake8 .
mypy --ignore-missing-imports .
bandit -r . -f json
safety check
pytest tests/ --cov=. --cov-report=xml
```

## Текущий статус

- **Последний успешный CI**: #34 (commit `c941d71`)
- **Все проверки проходят**: ✅

---
Связано: [[19-Тесты]] | [[00-Обзор-проекта]]
