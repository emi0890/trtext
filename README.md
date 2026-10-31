# trtext

[![CI](https://github.com/emi0890/trtext/actions/workflows/ci.yml/badge.svg)](https://github.com/emi0890/trtext/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

Deterministic, zero-dependency Turkish (`tr`) and Azeri (`az`) text casing, caseless comparison, slugification, and ICAO Doc 9303 MRZ transliteration.

## Why `trtext`?

Turkish and Azeri have four `i`-shaped letters with distinct casing pairs: **`i` ↔ `İ`** (dotted) and **`ı` ↔ `I`** (dotless).
Python's built-in `str.upper()`, `str.lower()`, and `str.casefold()` ignore locale and silently corrupt Turkish text:

| Operation | Input | Built-in Python (`str`) | `trtext` (Correct) |
| :--- | :--- | :--- | :--- |
| Uppercase | `"istanbul"` | `"ISTANBUL"` ❌ | `tr_upper("istanbul")` → `"İSTANBUL"` ✅ |
| Lowercase | `"DİYARBAKIR"` | `"di̇yarbakir"` (`i` + `U+0307`) ❌ | `tr_lower("DİYARBAKIR")` → `"diyarbakır"` ✅ |
| Lowercase | `"IĞDIR"` | `"iğdir"` ❌ | `tr_lower("IĞDIR")` → `"ığdır"` ✅ |
| Casefold / Equals | `"İSTANBUL"`, `"istanbul"` | `False` (`"i\u0307..."` != `"i..."`) ❌ | `tr_equals("İSTANBUL", "istanbul")` → `True` ✅ |
| Distinct `I` vs `i` | `"IŞIK"`, `"ışık"` | `False` ❌ | `tr_equals("IŞIK", "ışık")` → `True` ✅ |

Unlike `locale` or `PyICU`, `trtext` requires **zero OS locale configuration and zero C extensions**—it works identically on Linux, macOS, Windows, Docker, and Google Colab.

## Quickstart

    from trtext import (
        tr_lower,
        tr_upper,
        tr_titlecase,
        tr_swapcase,
        tr_casefold,
        tr_equals,
        az_lower,
        az_upper,
    )

    assert tr_upper("istanbul") == "İSTANBUL"
    assert tr_lower("DİYARBAKIR") == "diyarbakır"
    assert tr_titlecase("ışık ılık süt iç") == "Işık Ilık Süt İç"
    assert tr_equals("İSTANBUL", "istanbul") is True
    assert tr_equals("I", "i") is False

    # Auto-heals strings previously corrupted by Python's built-in "İ".lower() -> "i\u0307"
    broken = "İSTANBUL".lower()
    assert tr_upper(broken) == "İSTANBUL"

    # Full Azeri ('az') support via lang="az" or az_* aliases
    assert az_upper("azərbaycan bakı") == "AZƏRBAYCAN BAKI"
