"""A Helm chart dependency."""

from __future__ import annotations

from dataclasses import dataclass

from neophile.dependency.base import Dependency

__all__ = ["HelmDependency"]


@dataclass(frozen=True, order=True)
class HelmDependency(Dependency):
    """Represents a single Helm dependency."""

    version: str
    """The version of the dependency (may be a match pattern)."""

    name: str
    """The name of the external dependency."""

    repository: str
    """The name of the chart repository containing the dependency."""
