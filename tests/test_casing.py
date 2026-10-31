"""Milestone 1 test suite: SpecialCasing golden vectors, edge cases, and Hypothesis properties."""

from __future__ import annotations

import string
import unicodedata

import pytest
from golden_special_casing import SPECIAL_CASING_RULES
from hypothesis import given, settings
from hypothesis import strategies as st

from trtext import (
    az_lower,
    az_swapcase,
    az_titlecase,
    az_upper,
    normalize_tr,
    tr_lower,
    tr_swapcase,
    tr_titlecase,
    tr_upper,
)


@pytest.mark.parametrize("rule", SPECIAL_CASING_RULES)
def test_unicode_special_casing_golden_vectors(rule: dict[str, str]) -> None:
    lang = rule["lang"]  # 'tr' or 'az'
    ctx = rule["context"]
    src = rule["source"]

    if ctx == "":
        assert tr_lower(src, lang=lang) == rule["lower"]  # type: ignore[arg-type]
        assert tr_titlecase(src, lang=lang) == rule["title"]  # type: ignore[arg-type]
        assert tr_upper(src, lang=lang) == rule["upper"]  # type: ignore[arg-type]
    elif ctx in ("Before_Dot", "After_I"):
        # Direct 'I\u0307' and 'I' + intervening ccc=202 (cedilla) + '\u0307'
        assert tr_lower("I\u0307", lang=lang) == "i"  # type: ignore[arg-type]
        assert tr_lower("I\u0327\u0307", lang=lang) == unicodedata.normalize("NFC", "i\u0327")  # type: ignore[arg-type]
    elif ctx == "Not_Before_Dot":
        assert tr_lower("I", lang=lang) == "ı"  # type: ignore[arg-type]
        assert tr_lower("IA", lang=lang) == "ıa"  # type: ignore[arg-type]
        # U+030A (Combining Ring Above, ccc=230) does not precompose with 'I' under NFC
        # and blocks the later U+0307, triggering Not_Before_Dot ('I' -> 'ı')
        assert tr_lower("I\u030a\u0307", lang=lang, heal_broken_i=False) == "ı\u030a\u0307"  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("lower_str", "upper_str", "title_str"),
    [
        ("", "", ""),
        ("i", "İ", "İ"),
        ("ı", "I", "I"),
        ("istanbul", "İSTANBUL", "İstanbul"),
        ("diyarbakır", "DİYARBAKIR", "Diyarbakır"),
        ("ığdır", "IĞDIR", "Iğdır"),
        ("izmir", "İZMİR", "İzmir"),
        ("şanlıurfa", "ŞANLIURFA", "Şanlıurfa"),
        ("çanakkale", "ÇANAKKALE", "Çanakkale"),
        ("gümüşhane", "GÜMÜŞHANE", "Gümüşhane"),
        ("ışık ılık süt iç", "IŞIK ILIK SÜT İÇ", "Işık Ilık Süt İç"),
    ],
)
def test_turkish_handwritten_vectors(lower_str: str, upper_str: str, title_str: str) -> None:
    assert tr_upper(lower_str) == upper_str
    assert tr_upper(upper_str) == upper_str
    assert tr_lower(upper_str) == lower_str
    assert tr_lower(lower_str) == lower_str
    assert tr_titlecase(lower_str) == title_str
    assert tr_titlecase(upper_str) == title_str
    assert tr_swapcase(lower_str) == upper_str
    assert tr_swapcase(upper_str) == lower_str


@pytest.mark.parametrize(
    ("lower_str", "upper_str", "title_str"),
    [
        ("azərbaycan", "AZƏRBAYCAN", "Azərbaycan"),
        ("bakı", "BAKI", "Bakı"),
        ("imişli", "İMİŞLİ", "İmişli"),
        ("ismayıllı", "İSMAYILLI", "İsmayıllı"),
        ("şəki", "ŞƏKİ", "Şəki"),
    ],
)
def test_azeri_handwritten_vectors(lower_str: str, upper_str: str, title_str: str) -> None:
    assert az_upper(lower_str) == upper_str
    assert az_lower(upper_str) == lower_str
    assert az_titlecase(lower_str) == title_str
    assert az_titlecase(upper_str) == title_str
    assert az_swapcase(lower_str) == upper_str
    assert az_swapcase(upper_str) == lower_str


def test_mixed_language_deterministic_core_footgun() -> None:
    # Phase 0 design decision: core tr_lower is strictly deterministic (no hidden heuristics)
    assert tr_lower("iPhone'um") == "iphone'um"
    assert tr_upper("iPhone'um") == "İPHONE'UM"


def test_heal_broken_i_flag() -> None:
    # Python's built-in "İSTANBUL".lower() produces broken "i\u0307stanbul"
    broken = "İSTANBUL".lower()
    assert broken == "i\u0307stanbul"

    # Default heal_broken_i=True heals it cleanly
    assert normalize_tr(broken) == "istanbul"
    assert tr_lower(broken) == "istanbul"
    assert tr_upper(broken) == "İSTANBUL"
    assert tr_titlecase(broken) == "İstanbul"

    # Repeatedly broken string with multiple stacked U+0307 marks
    multi_broken = "i\u0307\u0307stanbul"
    assert tr_upper(multi_broken, heal_broken_i=True) == "İSTANBUL"

    # When heal_broken_i=False, raw U+0307 after lowercase 'i' is preserved
    assert tr_lower(broken, heal_broken_i=False) == "i\u0307stanbul"
    assert tr_upper(broken, heal_broken_i=False) == "İ\u0307STANBUL"


def test_invalid_lang_raises() -> None:
    with pytest.raises(ValueError, match="Unsupported lang"):
        tr_lower("istanbul", lang="en")  # type: ignore[arg-type]


# --- Hypothesis Property-Based Tests ---

_ASCII_WITHOUT_I = "".join(c for c in string.printable if c not in ("i", "I"))
_TR_AZ_ALPHABET = (
    "abcçdefgğhıijklmnoöprsştuüvyz"
    "ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ"
    "əƏqwxQWX0123456789 .,!?;:-_'\""
)


@settings(max_examples=250)
@given(st.text(alphabet=_ASCII_WITHOUT_I))
def test_property_ascii_without_i_invariance(s: str) -> None:
    assert tr_lower(s) == s.lower()
    assert tr_upper(s) == s.upper()
    assert tr_swapcase(s) == s.swapcase()


@settings(max_examples=250)
@given(st.text())
def test_property_idempotence_arbitrary_unicode(s: str) -> None:
    lowered = tr_lower(s)
    assert tr_lower(lowered) == lowered

    uppered = tr_upper(s)
    assert tr_upper(uppered) == uppered

    titled = tr_titlecase(s)
    assert tr_titlecase(titled) == titled


@settings(max_examples=250)
@given(st.text(alphabet=_TR_AZ_ALPHABET))
def test_property_roundtrip_and_swapcase_involution_tr_az(s: str) -> None:
    assert tr_swapcase(tr_swapcase(s)) == s
    assert tr_lower(tr_upper(s)) == tr_lower(s)
    assert tr_upper(tr_lower(s)) == tr_upper(s)
    assert len(tr_lower(s)) == len(s)
    assert len(tr_upper(s)) == len(s)
