"""Core Turkish (tr) and Azeri (az) casing, casefolding, and normalization logic."""

from __future__ import annotations

import unicodedata
from typing import Literal

SupportedLang = Literal["tr", "az"]
_VALID_LANGS: frozenset[str] = frozenset({"tr", "az"})

# Fast translation tables for the common path (when no combining dot U+0307 remains)
_LOWER_TABLE = str.maketrans({"İ": "i", "I": "ı"})
_UPPER_TABLE = str.maketrans({"i": "İ", "ı": "I"})


def _validate_lang(lang: str) -> None:
    if lang not in _VALID_LANGS:
        msg = f"Unsupported lang {lang!r}. Expected 'tr' or 'az'."
        raise ValueError(msg)


def _strip_broken_i_dots(text: str) -> str:
    """Remove redundant U+0307 following 'i' or 'İ' (with no intervening ccc=0/230)."""
    if "\u0307" not in text:
        return text
    out: list[str] = []
    after_dotted_i = False
    for ch in text:
        if ch == "\u0307" and after_dotted_i:
            # Drop redundant combining dot above on an already-dotted i/İ
            continue
        out.append(ch)
        if ch in ("i", "İ"):
            after_dotted_i = True
        else:
            ccc = unicodedata.combining(ch)
            if ccc in (0, 230):
                after_dotted_i = False
    return "".join(out)


def normalize_tr(text: str, *, heal_broken_i: bool = True) -> str:
    """Normalize text to NFC and optionally heal broken 'i\\u0307' / 'İ\\u0307' sequences."""
    norm = unicodedata.normalize("NFC", text)
    if heal_broken_i and "\u0307" in norm:
        norm = unicodedata.normalize("NFC", _strip_broken_i_dots(norm))
    return norm


def _is_before_dot(text: str, index: int) -> bool:
    """Unicode Before_Dot: followed by U+0307 with no intervening ccc=0 or ccc=230."""
    n = len(text)
    for j in range(index + 1, n):
        ch = text[j]
        if ch == "\u0307":
            return True
        ccc = unicodedata.combining(ch)
        if ccc in (0, 230):
            return False
    return False


def _lower_with_context(text: str) -> str:
    """Apply Unicode SpecialCasing tr/az lowercasing when U+0307 is present."""
    out: list[str] = []
    after_i = False
    for idx, ch in enumerate(text):
        if ch == "I":
            if _is_before_dot(text, idx):
                out.append("i")
            else:
                out.append("ı")
            after_i = True
        elif ch == "İ":
            out.append("i")
            after_i = False
        elif ch == "\u0307" and after_i:
            # Unicode After_I rule: consume the combining dot above
            after_i = False
        else:
            ccc = unicodedata.combining(ch)
            if ccc in (0, 230):
                after_i = False
            out.append(ch.lower())
    return "".join(out)


def _casefold_with_context(text: str) -> str:
    """Apply Unicode CaseFolding (C + F + T) with Before_Dot/After_I context."""
    out: list[str] = []
    after_i = False
    for idx, ch in enumerate(text):
        if ch == "I":
            if _is_before_dot(text, idx):
                out.append("i")
            else:
                out.append("ı")
            after_i = True
        elif ch == "İ":
            out.append("i")
            after_i = False
        elif ch == "\u0307" and after_i:
            after_i = False
        else:
            ccc = unicodedata.combining(ch)
            if ccc in (0, 230):
                after_i = False
            out.append(ch.casefold())
    return "".join(out)


def tr_lower(
    text: str,
    *,
    lang: SupportedLang = "tr",
    heal_broken_i: bool = True,
) -> str:
    """Convert text to lowercase using Turkish ('tr') or Azeri ('az') rules."""
    _validate_lang(lang)
    norm = normalize_tr(text, heal_broken_i=heal_broken_i)
    if "\u0307" not in norm:
        result = norm.translate(_LOWER_TABLE).lower()
    else:
        result = _lower_with_context(norm)
    return normalize_tr(result, heal_broken_i=heal_broken_i)


def tr_upper(
    text: str,
    *,
    lang: SupportedLang = "tr",
    heal_broken_i: bool = True,
) -> str:
    """Convert text to uppercase using Turkish ('tr') or Azeri ('az') rules."""
    _validate_lang(lang)
    norm = normalize_tr(text, heal_broken_i=heal_broken_i)
    result = norm.translate(_UPPER_TABLE).upper()
    return normalize_tr(result, heal_broken_i=heal_broken_i)


def _is_cased(ch: str) -> bool:
    return ch.islower() or ch.isupper() or unicodedata.category(ch) == "Lt"


def _titlecase_char(ch: str) -> str:
    if ch in ("i", "İ"):
        return "İ"
    if ch in ("ı", "I"):
        return "I"
    return ch.title()


def tr_titlecase(
    text: str,
    *,
    lang: SupportedLang = "tr",
    heal_broken_i: bool = True,
) -> str:
    """Convert text to titlecase using Turkish ('tr') or Azeri ('az') rules."""
    _validate_lang(lang)
    norm = normalize_tr(text, heal_broken_i=heal_broken_i)
    out: list[str] = []
    prev_cased = False
    after_i = False

    for idx, ch in enumerate(norm):
        if not prev_cased:
            if ch == "\u0307" and after_i:
                after_i = False
                continue
            out.append(_titlecase_char(ch))
            after_i = False
        else:
            if ch == "I":
                out.append("i" if _is_before_dot(norm, idx) else "ı")
                after_i = True
            elif ch == "İ":
                out.append("i")
                after_i = False
            elif ch == "\u0307" and after_i:
                after_i = False
                continue
            else:
                if unicodedata.combining(ch) in (0, 230):
                    after_i = False
                out.append(ch.lower())

        if _is_cased(ch):
            prev_cased = True
        elif not unicodedata.category(ch).startswith("M"):
            prev_cased = False

    return normalize_tr("".join(out), heal_broken_i=heal_broken_i)


def tr_swapcase(
    text: str,
    *,
    lang: SupportedLang = "tr",
    heal_broken_i: bool = True,
) -> str:
    """Swap uppercase and lowercase characters using Turkish ('tr') or Azeri ('az') rules."""
    _validate_lang(lang)
    norm = normalize_tr(text, heal_broken_i=heal_broken_i)
    out: list[str] = []
    after_i = False

    for idx, ch in enumerate(norm):
        if ch == "i":
            out.append("İ")
            after_i = False
        elif ch == "ı":
            out.append("I")
            after_i = False
        elif ch == "İ":
            out.append("i")
            after_i = False
        elif ch == "I":
            out.append("i" if _is_before_dot(norm, idx) else "ı")
            after_i = True
        elif ch == "\u0307" and after_i:
            after_i = False
        else:
            if unicodedata.combining(ch) in (0, 230):
                after_i = False
            out.append(ch.swapcase())

    return normalize_tr("".join(out), heal_broken_i=heal_broken_i)


def tr_casefold(
    text: str,
    *,
    lang: SupportedLang = "tr",
    heal_broken_i: bool = True,
) -> str:
    """Return a Turkish/Azeri casefolded string suitable for caseless comparison.

    Applies Unicode CaseFolding.txt status 'T' rules ('İ' -> 'i', 'I' -> 'ı')
    alongside standard 'C' and 'F' full casefolding (e.g. 'ß' -> 'ss').
    """
    _validate_lang(lang)
    norm = normalize_tr(text, heal_broken_i=heal_broken_i)
    if "\u0307" not in norm:
        result = norm.translate(_LOWER_TABLE).casefold()
    else:
        result = _casefold_with_context(norm)
    return normalize_tr(result, heal_broken_i=heal_broken_i)


def tr_equals(
    a: str,
    b: str,
    *,
    lang: SupportedLang = "tr",
    heal_broken_i: bool = True,
) -> bool:
    """Return True if strings `a` and `b` are equal under Turkish/Azeri caseless comparison."""
    _validate_lang(lang)
    return tr_casefold(a, lang=lang, heal_broken_i=heal_broken_i) == tr_casefold(
        b, lang=lang, heal_broken_i=heal_broken_i
    )


def az_lower(text: str, *, heal_broken_i: bool = True) -> str:
    """Convert text to lowercase using Azeri ('az') rules."""
    return tr_lower(text, lang="az", heal_broken_i=heal_broken_i)


def az_upper(text: str, *, heal_broken_i: bool = True) -> str:
    """Convert text to uppercase using Azeri ('az') rules."""
    return tr_upper(text, lang="az", heal_broken_i=heal_broken_i)


def az_titlecase(text: str, *, heal_broken_i: bool = True) -> str:
    """Convert text to titlecase using Azeri ('az') rules."""
    return tr_titlecase(text, lang="az", heal_broken_i=heal_broken_i)


def az_swapcase(text: str, *, heal_broken_i: bool = True) -> str:
    """Swap uppercase and lowercase characters using Azeri ('az') rules."""
    return tr_swapcase(text, lang="az", heal_broken_i=heal_broken_i)


def az_casefold(text: str, *, heal_broken_i: bool = True) -> str:
    """Casefold text using Azeri ('az') rules."""
    return tr_casefold(text, lang="az", heal_broken_i=heal_broken_i)


def az_equals(a: str, b: str, *, heal_broken_i: bool = True) -> bool:
    """Return True if `a` and `b` are equal under Azeri ('az') caseless comparison."""
    return tr_equals(a, b, lang="az", heal_broken_i=heal_broken_i)
