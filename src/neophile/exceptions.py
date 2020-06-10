"""Exceptions for neophile."""

from __future__ import annotations

__all__ = [
    "DependencyNotFoundError",
    "PushError",
]


class DependencyNotFoundError(Exception):
    """The specified dependency was not found to update."""


class PushError(Exception):
    """Pushing a branch to GitHub failed."""
