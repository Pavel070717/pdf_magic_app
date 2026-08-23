"""
Replace rules and accompanying prefixes — with type hints.
"""

import logging
import re
from typing import Any

from utils.state import load_state, save_state

logger = logging.getLogger(__name__)

DEFAULT_ACCOMPANYING_PREFIXES: list[str] = [
    "Сертификат",
    "Серт.",
    "Паспорт",
    "Декларация",
    "Декл.",
    "Свидетельство",
    "Свид.",
    "Исх. письмо",
    "Исх. письм",
    "Сертификат соответствия",
    "Паспорт качества",
    "Декларация о соответствии",
    "Свидетельство о государственной регистрации",
    "Исполнительная схема",
]

DEFAULT_REPLACE_RULES: list[dict[str, Any]] = [
    {"type": "symbol", "from": "_", "to": "/"},
]


def get_replace_rules() -> list[dict[str, Any]]:
    state = load_state()
    return state.get("replace_rules", [])


def save_replace_rules(rules: list[dict[str, Any]]) -> None:
    state = load_state()
    state["replace_rules"] = rules
    save_state(state)


def get_accompanying_prefixes() -> list[str]:
    state = load_state()
    return state.get("accompanying_prefixes", [])


def save_accompanying_prefixes(prefixes: list[str]) -> None:
    state = load_state()
    state["accompanying_prefixes"] = prefixes
    save_state(state)


def is_accompanying_doc(name: str) -> bool:
    prefixes = get_accompanying_prefixes()
    name_lower = name.lower().strip()
    for prefix in prefixes:
        if name_lower.startswith(prefix.lower()):
            return True
    return False


def normalize_name(raw_name: str) -> str:
    name = apply_rules_to_name(raw_name)
    if name is None:
        name = raw_name
    if is_accompanying_doc(name):
        # Удаляем всё в скобках КРОМЕ любого упоминания "копия" (в любом регистре)
        name = re.sub(r"\s*\((?!.*копия)[^)]*\)", "", name, flags=re.IGNORECASE)
        name = re.sub(r"\s{2,}", " ", name).strip()
        if not re.search(r"\(копия", name, re.IGNORECASE):
            name = name + " (копия)"
    return name


def apply_rules_to_name(raw_name: str) -> str:
    rules = get_replace_rules()
    text_rules = [r for r in rules if r.get("type") == "text"]
    result = raw_name
    for rule in text_rules:
        from_str: str = rule.get("from", "")
        to_str: str = rule.get("to", "")
        if not from_str:
            continue
        escaped = re.escape(from_str)
        pattern = rf"{escaped}"
        match = re.search(pattern, result, re.IGNORECASE)
        if match:
            to_main = re.sub(r"\s*\([^)]*\)", "", to_str).strip().lower()
            result_lower = result.lower()
            if to_main and to_main in result_lower:
                continue
            result = re.sub(pattern, to_str, result, flags=re.IGNORECASE, count=1)
    return result


def apply_symbol_rules(text: str) -> str:
    rules = get_replace_rules()
    symbol_rules = [r for r in rules if r.get("type") == "symbol"]
    result = text
    for rule in symbol_rules:
        from_str: str = rule.get("from", "")
        to_str: str = rule.get("to", "")
        if not from_str:
            continue
        result = result.replace(from_str, to_str)
    return result
