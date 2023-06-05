"""Representations of dependencies."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

__all__ = [
    "Dependency",
    "HelmDependency",
    "KustomizeDependency",
    "PreCommitDependency",
]


@dataclass(frozen=True, order=True)
class Dependency:
    """Base class for a dependency returned by a scanner."""

    path: Path
    """The file that contains the dependency declaration."""

    def to_dict(self) -> dict[str, str]:
        """Convert the object to a dict.

        Notes
        -----
        Required because ruamel.yaml cannot serialize `~pathlib.Path`.
        """
        result = asdict(self)
        result["path"] = str(result["path"])
        return result


@dataclass(frozen=True, order=True)
class HelmDependency(Dependency):
    """Represents a single Helm dependency."""

    version: str
    """The version of the dependency (may be a match pattern)."""

    name: str
    """The name of the external dependency."""

    repository: str
    """The name of the chart repository containing the dependency."""


@dataclass(frozen=True, order=True)
class KustomizeDependency(Dependency):
    """Represents a single Kustomize dependency."""

    url: str
    """The full URL of the dependency."""

    owner: str
    """The owner of the referenced GitHub repository."""

    repo: str
    """The name of the referenced GitHub repository."""

    version: str
    """The version of the dependency."""


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
