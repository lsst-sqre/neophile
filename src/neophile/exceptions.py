"""Exceptions for neophile."""

from __future__ import annotations


class DependencyNotFoundError(Exception):
    """The specified dependency was not found to update."""
