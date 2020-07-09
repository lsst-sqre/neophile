"""Exceptions for neophile."""

from __future__ import annotations

__all__ = [
    "DependencyNotFoundError",
    "PushError",
    "UncommittedChangesError",
]


class DependencyNotFoundError(Exception):
    """The specified dependency was not found to update."""


class PushError(Exception):
    """Pushing a branch to GitHub failed."""


class UncommittedChangesError(Exception):
    """The repository contains uncommitted changes.

    This interferes with some types of dependency analysis, which rely on
    checking whether an action causes repository files to change.
    """
