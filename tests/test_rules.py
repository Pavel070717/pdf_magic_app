"""
Tests for utils/rules.py — replace rules, accompanying prefixes, name normalization.
"""

from utils.rules import (
    apply_rules_to_name,
    apply_symbol_rules,
    get_accompanying_prefixes,
    get_replace_rules,
    is_accompanying_doc,
    normalize_name,
    save_accompanying_prefixes,
    save_replace_rules,
)


class TestReplaceRules:
    """Text and symbol replace rules CRUD + application."""

    def test_get_rules_empty(self, clean_state):
        """Empty rules by default."""
        rules = get_replace_rules()
        assert rules == []

    def test_save_and_get_rules(self, clean_state):
        """Save rules and retrieve them."""
        rules = [
            {"id": "1", "type": "text", "from": "ГОСТ", "to": "ГОСТ Р"},
            {"id": "2", "type": "symbol", "from": "_", "to": "/"},
        ]
        save_replace_rules(rules)
        loaded = get_replace_rules()
        assert loaded == rules

    def test_apply_text_rule(self, clean_state):
        """Text rule replaces first match (case-insensitive, once)."""
        save_replace_rules(
            [
                {"id": "1", "type": "text", "from": "ГОСТ", "to": "ГОСТ Р"},
            ]
        )
        result = apply_rules_to_name("Документ ГОСТ 12345-2020")
        assert result == "Документ ГОСТ Р 12345-2020"

    def test_apply_text_rule_case_insensitive(self, clean_state):
        """Text matching is case-insensitive."""
        save_replace_rules(
            [
                {"id": "1", "type": "text", "from": "гост", "to": "ГОСТ Р"},
            ]
        )
        result = apply_rules_to_name("Документ ГОСТ 12345")
        assert "ГОСТ Р" in result

    def test_apply_text_rule_skips_when_already_present(self, clean_state):
        """Rule is skipped if the target text is already present."""
        save_replace_rules(
            [
                {"id": "1", "type": "text", "from": "серт.", "to": "Сертификат соответствия"},
            ]
        )
        # "Сертификат" is already in the name → rule should skip
        result = apply_rules_to_name("Сертификат соответствия №123")
        assert result == "Сертификат соответствия №123"

    def test_apply_symbol_rule(self, clean_state):
        """Symbol rule replaces all occurrences of a character."""
        save_replace_rules(
            [
                {"id": "1", "type": "symbol", "from": "_", "to": "/"},
            ]
        )
        result = apply_symbol_rules("section_1_part_2")
        assert result == "section/1/part/2"

    def test_apply_rules_to_name_multiple_rules(self, clean_state):
        """Multiple text rules are applied in order."""
        save_replace_rules(
            [
                {"id": "1", "type": "text", "from": "свид.", "to": "Свидетельство"},
                {"id": "2", "type": "text", "from": "серт.", "to": "Сертификат"},
            ]
        )
        result = apply_rules_to_name("свид. серт. документ")
        assert "Свидетельство" in result
        assert "Сертификат" in result

    def test_apply_rules_to_name_no_match(self, clean_state):
        """No rules match — original name returned unchanged."""
        save_replace_rules(
            [
                {"id": "1", "type": "text", "from": "XYZ", "to": "ABC"},
            ]
        )
        result = apply_rules_to_name("Документ.pdf")
        assert result == "Документ.pdf"


class TestAccompanyingPrefixes:
    """Accompanying document prefix detection and management."""

    def test_no_prefixes_by_default(self, clean_state):
        """Empty prefixes by default."""
        prefixes = get_accompanying_prefixes()
        assert isinstance(prefixes, list)
        assert prefixes == []

    def test_save_and_get_prefixes(self, clean_state):
        """Save custom prefixes and retrieve them."""
        custom = ["Сертификат", "Декларация"]
        save_accompanying_prefixes(custom)
        assert get_accompanying_prefixes() == custom

    def test_is_accompanying_doc_true(self, clean_state):
        """Document starting with a prefix is detected."""
        save_accompanying_prefixes(["Сертификат", "Паспорт", "Декларация"])
        assert is_accompanying_doc("Сертификат соответствия №123.pdf") is True
        assert is_accompanying_doc("Паспорт качества А.pdf") is True
        assert is_accompanying_doc("Декларация о соответствии.pdf") is True

    def test_is_accompanying_doc_false(self, clean_state):
        """Document NOT starting with a prefix is excluded."""
        assert is_accompanying_doc("Акт освидетельствования.pdf") is False
        assert is_accompanying_doc("Протокол испытаний.pdf") is False
        assert is_accompanying_doc("") is False

    def test_is_accompanying_doc_case_insensitive(self, clean_state):
        """Matching is case-insensitive."""
        save_accompanying_prefixes(["Сертификат"])
        assert is_accompanying_doc("сертификат.pdf") is True
        assert is_accompanying_doc("СЕРТИФИКАТ.pdf") is True


class TestNormalizeName:
    """Full name normalization: rules + accompanying doc cleanup."""

    def test_normalize_accompanying_adds_copy(self, clean_state):
        """Accompanying doc gets '(копия)' appended."""
        save_accompanying_prefixes(["Сертификат"])
        result = normalize_name("Сертификат №123 (оригинал)")
        assert "(копия)" in result
        assert "оригинал" not in result.lower()

    def test_normalize_accompanying_preserves_existing_copy(self, clean_state):
        """If '(копия)' already present, don't duplicate."""
        save_accompanying_prefixes(["Паспорт"])
        result = normalize_name("Паспорт качества (копия)")
        assert result.count("(копия)") == 1

    def test_normalize_non_accompanying_unchanged(self, clean_state):
        """Non-accompanying docs pass through unchanged (except rules)."""
        result = normalize_name("Акт освидетельствования скрытых работ №1")
        assert "Акт" in result
        assert "(копия)" not in result

    def test_normalize_applies_rules_then_prefixes(self, clean_state):
        """Text rules are applied BEFORE accompanying prefix logic."""
        save_replace_rules(
            [
                {"id": "1", "type": "text", "from": "lowercase", "to": "Uppercase"},
            ]
        )
        result = normalize_name("lowercase document")
        # "lowercase" does NOT start with an accompanying prefix → no (копия)
        assert result.startswith("Uppercase")
        assert "(copy)" not in result.lower() and "Uppercase" in result
