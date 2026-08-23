"""
Blueprint: /api/dashboard/stats
"""

from datetime import datetime, timedelta
from pathlib import Path

from flask import Blueprint, jsonify

from routes.core import logger

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/api/dashboard/stats", methods=["GET"])
def get_dashboard_stats():
    from utils.database import get_all_materials
    from utils.state import load_state

    try:
        state = load_state()
        total_files = len(state.get("files", []))
        created_dirs = state.get("created_directories", [])
        total_dirs = sum(1 for d in created_dirs if Path(d if isinstance(d, str) else d.get("path", "")).exists())
        total_materials = len(get_all_materials())
        total_rules = len(state.get("replace_rules", []))

        last_magic = state.get("last_magic_run")
        last_activity = last_magic.get("timestamp") if last_magic else None

        now = datetime.now()
        week_ago = now - timedelta(days=7)
        activity_by_day = {}
        for i in range(7):
            day = (week_ago + timedelta(days=i)).strftime("%d.%m")
            activity_by_day[day] = {"files": 0, "dirs": 0}

        for d in created_dirs:
            created_at = d.get("created_at", "")
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    day_key = dt.strftime("%d.%m")
                    if day_key in activity_by_day:
                        activity_by_day[day_key]["dirs"] += 1
                except (ValueError, TypeError):
                    pass

        if last_magic and last_magic.get("timestamp"):
            try:
                dt = datetime.fromisoformat(last_magic["timestamp"].replace("Z", "+00:00"))
                day_key = dt.strftime("%d.%m")
                if day_key in activity_by_day:
                    activity_by_day[day_key]["files"] += last_magic.get("files_copied", 0)
            except (ValueError, TypeError):
                pass

        day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        activity_data = []
        for i in range(7):
            day = week_ago + timedelta(days=i)
            day_key = day.strftime("%d.%m")
            activity_data.append(
                {
                    "day": day_names[day.weekday()],
                    "files": activity_by_day.get(day_key, {}).get("files", 0),
                    "dirs": activity_by_day.get(day_key, {}).get("dirs", 0),
                }
            )

        recent_events = []
        if last_magic:
            ts = last_magic.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                time_str = dt.strftime("%H:%M")
            except (ValueError, TypeError):
                time_str = "--:--"
            recent_events.append(
                {
                    "time": time_str,
                    "action": f"Скопировано {last_magic.get('files_copied', 0)} файлов",
                    "status": "success",
                    "details": last_magic.get("output_dir", ""),
                }
            )
            if last_magic.get("registry_name"):
                recent_events.append(
                    {
                        "time": time_str,
                        "action": "Создан Excel-реестр",
                        "status": "success",
                        "details": last_magic["registry_name"],
                    }
                )

        return jsonify(
            {
                "success": True,
                "total_files": total_files,
                "total_dirs": total_dirs,
                "total_materials": total_materials,
                "total_rules": total_rules,
                "last_activity": last_activity,
                "activity": activity_data,
                "recent_events": recent_events,
            }
        )
    except Exception as e:
        logger.exception("Ошибка статистики дашборда")
        return jsonify({"success": False, "error": str(e)}), 500
