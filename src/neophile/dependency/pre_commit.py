"""A pre-commit hook dependency."""

from __future__ import annotations

from dataclasses import dataclass

from neophile.dependency.base import Dependency

__all__ = ["PreCommitDependency"]


@dataclass(frozen=True, order=True)
class PreCommitDependency(Dependency):
    """Represents a single pre-commit dependency."""

    repository: str
    """The URL of the GitHub repository providing this pre-commit hook."""

    owner: str
    """The GitHub repository owner of the pre-commit hook."""

    repo: str
    """The GitHub repository name of the pre-commit hook."""

    version: str
    """The version of the dependency (may be a match pattern)."""
