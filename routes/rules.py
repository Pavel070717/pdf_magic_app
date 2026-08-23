"""
Blueprint: /api/replace-rules/* + /api/accompanying-prefixes/*
"""

import uuid

from flask import Blueprint, jsonify, request

from routes.core import logger
from utils.rules import (
    get_accompanying_prefixes,
    get_replace_rules,
    save_accompanying_prefixes,
    save_replace_rules,
)

rules_bp = Blueprint("rules", __name__)


@rules_bp.route("/api/replace-rules", methods=["GET"])
def api_get_replace_rules():
    try:
        rules = get_replace_rules()
        return jsonify({"success": True, "rules": rules})
    except Exception as e:
        logger.error(f"Ошибка получения правил: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@rules_bp.route("/api/replace-rules", methods=["POST"])
def api_add_replace_rule():
    try:
        data = request.get_json()
        rule_type = data.get("type", "text")
        from_str = data.get("from", "").strip()
        to_str = data.get("to", "").strip()
        if not from_str:
            return jsonify({"success": False, "error": "Введите что заменять"}), 400

        rules = get_replace_rules()
        new_rule = {
            "id": str(uuid.uuid4())[:8],
            "type": rule_type,
            "from": from_str,
            "to": to_str or "",
            "is_default": False,
        }
        rules.append(new_rule)
        save_replace_rules(rules)
        return jsonify({"success": True, "rules": rules})
    except Exception as e:
        logger.exception("Ошибка добавления правила")
        return jsonify({"success": False, "error": str(e)}), 500


@rules_bp.route("/api/replace-rules/<rule_id>", methods=["DELETE"])
def api_delete_replace_rule(rule_id):
    try:
        rules = get_replace_rules()
        rules = [r for r in rules if r.get("id") != rule_id]
        save_replace_rules(rules)
        return jsonify({"success": True, "rules": rules})
    except Exception as e:
        logger.error(f"Ошибка удаления правила: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@rules_bp.route("/api/replace-rules/clear", methods=["POST"])
def api_clear_replace_rules():
    try:
        save_replace_rules([])
        return jsonify({"success": True, "rules": []})
    except Exception as e:
        logger.error(f"Ошибка очистки правил: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@rules_bp.route("/api/accompanying-prefixes", methods=["GET"])
def api_get_accompanying_prefixes():
    try:
        prefixes = get_accompanying_prefixes()
        return jsonify({"success": True, "prefixes": prefixes})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@rules_bp.route("/api/accompanying-prefixes", methods=["POST"])
def api_save_accompanying_prefixes():
    try:
        data = request.get_json()
        prefixes = data.get("prefixes", [])
        if not isinstance(prefixes, list):
            return jsonify({"success": False, "error": "prefixes must be a list"}), 400
        save_accompanying_prefixes(prefixes)
        return jsonify({"success": True, "prefixes": prefixes})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
