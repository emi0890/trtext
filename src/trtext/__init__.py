"""trtext: Deterministic Turkish (tr) and Azeri (az) text processing."""

from __future__ import annotations

from trtext._casing import (
    SupportedLang,
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

__all__ = [
    "SupportedLang",
    "__version__",
    "az_lower",
    "az_swapcase",
    "az_titlecase",
    "az_upper",
    "normalize_tr",
    "tr_lower",
    "tr_swapcase",
    "tr_titlecase",
    "tr_upper",
]
__version__ = "0.1.0"
