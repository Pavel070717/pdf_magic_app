"""
Blueprint: /msg + /api/msg/* — МСГ (месячно-суточный график) и ОЖР (общий журнал работ).
"""

import calendar
import datetime

from flask import Blueprint, jsonify, request

from routes.core import logger
from utils.msg_db import (
    add_ozh_items,
    delete_ozh_item,
    get_available_months,
    get_month_rows,
    get_ozh_items,
)

msg_bp = Blueprint("msg", __name__)

MONTHS_RU = [
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
]


def _month_label(year: int, month: int) -> str:
    return f"{MONTHS_RU[month - 1]} {year}"


def _parse_month(month: str | None) -> tuple[int, int, str] | tuple[None, None, str]:
    if month:
        try:
            y, m = (int(p) for p in month.split("-")[:2])
            if 1 <= m <= 12:
                return y, m, f"{y:04d}-{m:02d}"
        except (TypeError, ValueError):
            pass
    today = datetime.date.today()
    return None, None, f"{today.year:04d}-{today.month:02d}"


@msg_bp.route("/api/msg/months")
def api_msg_months():
    try:
        today = datetime.date.today()
        available = set(get_available_months())
        available.add(f"{today.year:04d}-{today.month:02d}")
        months = [
            {
                "value": m,
                "label": _month_label(int(m[:4]), int(m[5:7])),
                "has_data": m in available,
            }
            for m in sorted(available)
        ]
        return jsonify(
            {
                "success": True,
                "months": months,
                "current": f"{today.year:04d}-{today.month:02d}",
            }
        )
    except Exception as e:
        logger.error(f"Ошибка получения списка месяцев: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@msg_bp.route("/api/msg/ozh/items", methods=["POST"])
def api_add_ozh_items():
    try:
        data = request.get_json() or {}
        date = str(data.get("date", "")).strip()
        items = data.get("items") or []
        if not date:
            return jsonify({"success": False, "error": "Укажите дату"}), 400
        try:
            datetime.date(*(int(p) for p in date.split("-")[:3]))
        except (TypeError, ValueError):
            return jsonify({"success": False, "error": "Некорректная дата"}), 400

        cleaned = []
        for it in items:
            if not isinstance(it, dict):
                continue
            work_name = str(it.get("work_name") or "").strip()
            if not work_name:
                continue
            cleaned.append(
                {
                    "work_name": work_name,
                    "position": str(it.get("position") or "").strip(),
                    "unit": str(it.get("unit") or "").strip(),
                    "volume": it.get("volume", 0) or 0,
                }
            )
        count = add_ozh_items(date, cleaned)
        if count == 0:
            return (
                jsonify({"success": False, "error": "Нет ни одной заполненной работы"}),
                400,
            )
        return jsonify({"success": True, "count": count, "date": date})
    except Exception as e:
        logger.exception("Ошибка сохранения ОЖР")
        return jsonify({"success": False, "error": str(e)}), 500


@msg_bp.route("/api/msg/ozh/items")
def api_get_ozh_items():
    try:
        date = (request.args.get("date") or "").strip()
        items = get_ozh_items(date or None)
        return jsonify({"success": True, "items": items})
    except Exception as e:
        logger.error(f"Ошибка получения ОЖР: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@msg_bp.route("/api/msg/ozh/items/<int:item_id>", methods=["DELETE"])
def api_delete_ozh_item(item_id):
    try:
        deleted = delete_ozh_item(item_id)
        return jsonify({"success": deleted, "id": item_id})
    except Exception as e:
        logger.error(f"Ошибка удаления записи ОЖР: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@msg_bp.route("/api/msg/month")
def api_msg_month():
    try:
        year, month, value = _parse_month(request.args.get("month"))
        if year is None:
            year, month = (
                datetime.date.today().year,
                datetime.date.today().month,
            )
        days_in_month = calendar.monthrange(year, month)[1]
        weekends = {
            d
            for d in range(1, days_in_month + 1)
            if datetime.date(year, month, d).weekday() >= 5
        }
        today = datetime.date.today()
        today_day = today.day if (today.year, today.month) == (year, month) else None

        rows = get_month_rows(value)
        day_totals = {d: 0.0 for d in range(1, days_in_month + 1)}
        for row in rows:
            row_total = 0.0
            for day, vol in row["days"].items():
                day_totals[day] = day_totals.get(day, 0.0) + vol
                row_total += vol
            row["total"] = round(row_total, 2)
        day_totals = {
            d: round(day_totals.get(d, 0.0), 2) for d in range(1, days_in_month + 1)
        }
        grand_total = round(sum(day_totals.values()), 2)

        return jsonify(
            {
                "success": True,
                "month": value,
                "label": _month_label(year, month),
                "days_in_month": days_in_month,
                "weekends": sorted(weekends),
                "today": today_day,
                "rows": rows,
                "day_totals": day_totals,
                "grand_total": grand_total,
            }
        )
    except Exception as e:
        logger.error(f"Ошибка формирования МСГ: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
