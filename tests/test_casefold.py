"""Milestone 2 test suite: tr_casefold, tr_equals, NFC/NFD equivalence, and Hypothesis laws."""

from __future__ import annotations

import unicodedata

import pytest
from golden_case_folding import TURKIC_CASEFOLD_RULES
from hypothesis import given, settings
from hypothesis import strategies as st

from trtext import (
    az_casefold,
    az_equals,
    tr_casefold,
    tr_equals,
    tr_lower,
    tr_titlecase,
    tr_upper,
)


@pytest.mark.parametrize("rule", TURKIC_CASEFOLD_RULES)
def test_unicode_casefolding_turkic_golden_vectors(rule: dict[str, str]) -> None:
    src = rule["source"]
    target = rule["target"]
    assert tr_casefold(src) == target
    assert az_casefold(src) == target
    assert tr_equals(src, target)
    assert az_equals(src, target)


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ("", ""),
        ("i", "İ"),
        ("ı", "I"),
        ("istanbul", "İSTANBUL"),
        ("İstanbul", "iSTANBUL"),
        ("diyarbakır", "DİYARBAKIR"),
        ("IĞDIR", "ığdır"),
        ("ışık ılık süt iç", "IŞIK ILIK SÜT İÇ"),
        ("azərbaycan", "AZƏRBAYCAN"),
        ("bakı", "BAKI"),
        # Full casefolding (status F) still works alongside Turkish rules:
        ("İSTANBUL STRASSE", "istanbul straße"),
    ],
)
def test_tr_equals_positive_pairs(a: str, b: str) -> None:
    assert tr_equals(a, b)
    assert tr_equals(b, a)
    assert az_equals(a, b)


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ("i", "I"),
        ("ı", "İ"),
        ("istanbul", "ISTANBUL"),
        ("diyarbakır", "DIYARBAKIR"),
        ("ışık", "işik"),
        ("IŞIK", "İŞİK"),
        ("bakı", "baki"),
    ],
)
def test_tr_equals_negative_pairs_caught(a: str, b: str) -> None:
    # Standard Python wrongly thinks "i".casefold() == "I".casefold(); tr_equals must reject!
    assert not tr_equals(a, b)
    assert not tr_equals(b, a)
    assert not az_equals(a, b)


def test_nfc_and_nfd_equivalence() -> None:
    # Words with diacritics that decompose into base + combining mark in NFD
    decomposable_words = [
        "İstanbul",
        "İSTANBUL",
        "DİYARBAKIR",
        "Şanlıurfa",
        "Çanakkale",
        "Gümüşhane",
        "Ödemiş",
    ]
    for w in decomposable_words:
        nfc = unicodedata.normalize("NFC", w)
        nfd = unicodedata.normalize("NFD", w)
        assert nfc != nfd  # Confirm they have distinct code point representations
        assert tr_casefold(nfc) == tr_casefold(nfd)
        assert tr_equals(nfc, nfd)
        assert tr_equals(nfc, tr_lower(nfd))
        assert tr_equals(nfd, tr_upper(nfc))

    # Dotless 'ı' (U+0131) is a base letter (no combining mark in NFD),
    # while uppercase 'DİYARBAKIR' decomposes 'İ' -> 'I\u0307' in NFD:
    assert unicodedata.normalize("NFD", "Diyarbakır") == "Diyarbakır"
    assert tr_equals("Diyarbakır", unicodedata.normalize("NFD", "DİYARBAKIR"))


def test_broken_python_lower_healed_in_comparison() -> None:
    # Python's built-in "İSTANBUL".lower() -> "i\u0307stanbul"
    broken_lower = "İSTANBUL".lower()
    broken_cf = "İSTANBUL".casefold()
    assert broken_lower == "i\u0307stanbul"
    assert broken_cf == "i\u0307stanbul"

    # By default (heal_broken_i=True), tr_equals heals the broken string and matches "istanbul"
    assert tr_equals(broken_lower, "istanbul")
    assert tr_equals(broken_cf, "İSTANBUL")

    # With heal_broken_i=False, the extra U+0307 is preserved and does NOT equal clean "istanbul"
    assert not tr_equals(broken_lower, "istanbul", heal_broken_i=False)


def test_casefold_invalid_lang_raises() -> None:
    with pytest.raises(ValueError, match="Unsupported lang"):
        tr_casefold("istanbul", lang="de")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Unsupported lang"):
        tr_equals("a", "A", lang="fr")  # type: ignore[arg-type]


# --- Hypothesis Property-Based Tests for Casefolding & Equivalence ---

_TR_AZ_ALPHABET = (
    "abcçdefgğhıijklmnoöprsştuüvyz"
    "ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ"
    "əƏß0123456789 .,!?;:-_'\""
)


@settings(max_examples=250)
@given(st.text())
def test_property_casefold_idempotence_and_nfd_equivalence(s: str) -> None:
    folded = tr_casefold(s)
    assert tr_casefold(folded) == folded
    # Reflexivity across NFC and NFD
    nfd = unicodedata.normalize("NFD", s)
    assert tr_equals(s, s)
    assert tr_equals(s, nfd)


@settings(max_examples=250)
@given(st.text(alphabet=_TR_AZ_ALPHABET))
def test_property_casing_preserves_tr_equals(s: str) -> None:
    assert tr_equals(s, tr_lower(s))
    assert tr_equals(s, tr_upper(s))
    assert tr_equals(s, tr_titlecase(s))
    assert tr_equals(tr_lower(s), tr_upper(s))


@settings(max_examples=200)
@given(st.text(alphabet=_TR_AZ_ALPHABET), st.text(alphabet=_TR_AZ_ALPHABET))
def test_property_tr_equals_symmetry(a: str, b: str) -> None:
    assert tr_equals(a, b) == tr_equals(b, a)
