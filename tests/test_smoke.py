"""Milestone 0 smoke tests."""

from __future__ import annotations

import sys

import trtext


def test_version_and_python_requirement() -> None:
    assert trtext.__version__ == "0.1.0"
    assert sys.version_info >= (3, 10)
