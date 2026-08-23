"""
Blueprint: /api/registry/* — registry data CRUD.
"""

from flask import Blueprint, jsonify, render_template, request

from routes.core import logger, sanitize_text

registry_bp = Blueprint("registry", __name__)


@registry_bp.route("/api/registry/form", methods=["GET"])
def get_registry_form():
    """Return HTML form for the registry modal."""
    from utils.state import load_state

    state = load_state()
    data = state.get("registry_data", {})
    return render_template("registry_form.html", data=data)


@registry_bp.route("/api/registry/data", methods=["GET"])
def get_registry_data():
    from utils.state import load_state

    state = load_state()
    registry_data = state.get("registry_data", {})
    registry_dicts = state.get("registry_dicts", {})
    registry_history = state.get("registry_history", [])
    return jsonify(
        {
            "success": True,
            "data": registry_data,
            "dicts": registry_dicts,
            "history": registry_history,
        }
    )


@registry_bp.route("/api/registry/data", methods=["POST"])
def save_registry_data():
    from utils.state import load_state, save_state

    try:
        data = request.get_json(silent=True) or {}
        state = load_state()

        registry_data = state.get("registry_data", {})
        registry_data["org_name"] = sanitize_text(data.get("org_name", ""))
        registry_data["object_name"] = sanitize_text(data.get("object_name", ""))
        registry_data["customer"] = sanitize_text(data.get("customer", ""))
        registry_data["sk_representative"] = sanitize_text(
            data.get("sk_representative", "")
        )
        registry_data["general_contractor"] = sanitize_text(
            data.get("general_contractor", "")
        )
        registry_data["work_executor"] = sanitize_text(data.get("work_executor", ""))
        registry_data["registry_number"] = sanitize_text(
            data.get("registry_number", "")
        )
        registry_data["signature_sdal"] = sanitize_text(data.get("signature_sdal", ""))
        registry_data["signature_proveril"] = sanitize_text(
            data.get("signature_proveril", "")
        )
        registry_data["signature_prinyal"] = sanitize_text(
            data.get("signature_prinyal", "")
        )
        state["registry_data"] = registry_data

        registry_dicts = state.get("registry_dicts", {})
        incoming_dicts = data.get("dicts", {})
        for dict_key, values in incoming_dicts.items():
            if isinstance(values, list):
                existing = registry_dicts.get(dict_key, [])
                for val in values:
                    sanitized = sanitize_text(val)
                    if sanitized and sanitized not in existing:
                        existing.append(sanitized)
                registry_dicts[dict_key] = existing
        state["registry_dicts"] = registry_dicts

        save_state(state)
        logger.info("Данные реестра сохранены")
        # Re-render the form with saved data
        return render_template("registry_form.html", data=registry_data)
    except Exception as e:
        logger.exception("Ошибка сохранения данных реестра")
        return jsonify({"success": False, "error": str(e)}), 500
