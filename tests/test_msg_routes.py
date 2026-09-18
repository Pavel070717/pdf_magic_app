"""
Tests for МСГ / ОЖР (mesyachno-sutochny grafik / obshchiy zhurnal rabot).
"""

import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_msg_db(monkeypatch):
    """Mock msg DB_PATH to a temporary database, isolated per test."""
    import utils.msg_db

    tmp_dir = Path(tempfile.mkdtemp())
    tmp_db = tmp_dir / "test_msg.db"
    monkeypatch.setattr(utils.msg_db, "DB_PATH", tmp_db)
    utils.msg_db.init_msg_db()
    yield tmp_db
    shutil.rmtree(tmp_dir, ignore_errors=True)


def _post_items(client, date, items):
    return client.post(
        "/api/msg/ozh/items",
        json={"date": date, "items": items},
    )


def test_add_ozh_items_and_month_aggregation(app_client, temp_msg_db):
    """Две записи с 100% совпадением (работа+позиция+ед.) в один день
    агрегируются в одну строку МСГ с суммой объёмов в этом дне."""
    resp = _post_items(
        app_client,
        "2026-08-15",
        [
            {
                "work_name": "Изготовление свай",
                "position": "204",
                "unit": "м",
                "volume": 10,
            },
            {
                "work_name": "Изготовление свай",
                "position": "204",
                "unit": "м",
                "volume": 5,
            },
        ],
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True and data["count"] == 2

    resp = app_client.get("/api/msg/month?month=2026-08")
    data = resp.get_json()
    assert data["success"] is True
    assert len(data["rows"]) == 1
    row = data["rows"][0]
    assert row["work_name"] == "Изготовление свай"
    assert row["days"]["15"] == 15.0  # 10 + 5
    assert row["total"] == 15.0
    assert data["day_totals"]["15"] == 15.0
    assert data["grand_total"] == 15.0


def test_same_work_different_unit_new_row(app_client, temp_msg_db):
    """Если единица измерения отличается — это уже НЕ 100% идентичность,
    в МСГ появляется отдельная строка."""
    _post_items(
        app_client,
        "2026-08-15",
        [{"work_name": "Котлован", "position": "1", "unit": "м3", "volume": 2}],
    )
    _post_items(
        app_client,
        "2026-08-15",
        [{"work_name": "Котлован", "position": "1", "unit": "м2", "volume": 3}],
    )

    data = app_client.get("/api/msg/month?month=2026-08").get_json()
    assert len(data["rows"]) == 2


def test_same_work_different_days_volume_to_day(app_client, temp_msg_db):
    """Одна работа в разные дни — одна строка, объёмы в своих днях."""
    _post_items(
        app_client,
        "2026-08-15",
        [
            {
                "work_name": "Монтаж оголовков",
                "position": "205",
                "unit": "шт",
                "volume": 4,
            }
        ],
    )
    _post_items(
        app_client,
        "2026-08-17",
        [
            {
                "work_name": "Монтаж оголовков",
                "position": "205",
                "unit": "шт",
                "volume": 6,
            }
        ],
    )

    data = app_client.get("/api/msg/month?month=2026-08").get_json()
    assert len(data["rows"]) == 1
    row = data["rows"][0]
    assert row["days"]["15"] == 4.0
    assert row["days"]["17"] == 6.0
    assert row["total"] == 10.0


def test_rows_order_as_in_ozh(app_client, temp_msg_db):
    """Порядок строк МСГ — как впервые внесены в ОЖР."""
    _post_items(
        app_client,
        "2026-08-01",
        [{"work_name": "Бета", "position": "2", "unit": "шт", "volume": 1}],
    )
    _post_items(
        app_client,
        "2026-08-02",
        [{"work_name": "Альфа", "position": "1", "unit": "шт", "volume": 1}],
    )
    _post_items(
        app_client,
        "2026-08-03",
        [{"work_name": "Вера", "position": "3", "unit": "шт", "volume": 1}],
    )

    data = app_client.get("/api/msg/month?month=2026-08").get_json()
    assert [r["work_name"] for r in data["rows"]] == ["Бета", "Альфа", "Вера"]


def test_month_structure_and_weekends(app_client, temp_msg_db):
    _post_items(
        app_client,
        "2026-08-10",
        [{"work_name": "Сваи", "position": "1", "unit": "м", "volume": 1}],
    )
    data = app_client.get("/api/msg/month?month=2026-08").get_json()
    assert data["days_in_month"] == 31
    assert data["label"] == "Август 2026"
    # 1 августа 2026 — суббота, 2 — воскресенье
    assert 1 in data["weekends"] and 2 in data["weekends"]
    assert 3 not in data["weekends"]
    assert "today" in data


def test_invalid_date_rejected(app_client, temp_msg_db):
    resp = _post_items(app_client, "2026-13-40", [{"work_name": "X", "volume": 1}])
    assert resp.status_code == 400


def test_empty_work_rejected(app_client, temp_msg_db):
    resp = _post_items(app_client, "2026-08-15", [{"work_name": "  ", "volume": 1}])
    assert resp.status_code == 400


def test_delete_ozh_item(app_client, temp_msg_db):
    _post_items(
        app_client,
        "2026-08-15",
        [{"work_name": "Сваи", "position": "1", "unit": "м", "volume": 7}],
    )
    items = app_client.get("/api/msg/ozh/items?date=2026-08-15").get_json()["items"]
    assert len(items) == 1
    item_id = items[0]["id"]

    resp = app_client.delete(f"/api/msg/ozh/items/{item_id}")
    assert resp.get_json()["success"] is True
    assert (
        app_client.get("/api/msg/ozh/items?date=2026-08-15").get_json()["items"] == []
    )
    assert app_client.get("/api/msg/month?month=2026-08").get_json()["rows"] == []


def test_get_ozh_by_date(app_client, temp_msg_db):
    _post_items(app_client, "2026-08-15", [{"work_name": "A", "volume": 1}])
    _post_items(app_client, "2026-08-16", [{"work_name": "B", "volume": 1}])
    items = app_client.get("/api/msg/ozh/items?date=2026-08-16").get_json()["items"]
    assert len(items) == 1 and items[0]["work_name"] == "B"


def test_months_list(app_client, temp_msg_db):
    _post_items(app_client, "2026-08-15", [{"work_name": "A", "volume": 1}])
    data = app_client.get("/api/msg/months").get_json()
    assert data["success"] is True
    values = [m["value"] for m in data["months"]]
    assert "2026-08" in values
    assert any(m["has_data"] for m in data["months"])


def test_msg_page_renders(app_client, temp_msg_db):
    resp = app_client.get("/msg")
    assert resp.status_code == 200
    assert "МСГ".encode() in resp.data or "Общий журнал" in resp.get_data(as_text=True)
