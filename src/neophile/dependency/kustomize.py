"""A Kustomize external dependency."""

from __future__ import annotations

from dataclasses import dataclass

from neophile.dependency.base import BaseDependency

__all__ = ["KustomizeDependency"]


@dataclass(frozen=True, order=True)
class KustomizeDependency(BaseDependency):
    """Represents a single Kustomize dependency."""

    url: str
    """The full URL of the dependency."""

    owner: str
    """The owner of the referenced GitHub repository."""

    repo: str
    """The name of the referenced GitHub repository."""

    version: str
    """The version of the dependency."""
