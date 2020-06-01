"""Tests for neophile, the top-level import."""

import neophile


def test_version() -> None:
    assert isinstance(neophile.__version__, str)
