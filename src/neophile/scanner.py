"""Source tree scanning."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ruamel.yaml import YAML

if TYPE_CHECKING:
    from typing import List

__all__ = [
    "Dependency",
    "HelmDependency",
    "Scanner",
]


@dataclass(frozen=True, eq=True)
class Dependency:
    """Base class for a dependency on some external resource."""

    name: str
    """The name of the external dependency."""

    version: str
    """The version of the dependency (may be a match pattern)."""

    path: str
    """The file that contains the dependency declaration."""


@dataclass(frozen=True, eq=True)
class HelmDependency(Dependency):
    """Represents a single Helm dependency."""

    repository: str
    """The name of the chart repository containing the dependency."""


class Scanner:
    """Scan a source tree for version references.

    Parameters
    ----------
    root : `str`
        The root of the source tree.
    """

    def __init__(self, root: str) -> None:
        self._root = root
        self._yaml = YAML()

    def scan(self) -> List[HelmDependency]:
        """Scan a source tree for version references.

        Currently only looks for Helm chart dependencies.

        Returns
        -------
        results : List[`HelmDependency`]
            A list of all discovered Helm chart dependencies.
        """
        results = []
        for dirpath, _, filenames in os.walk(self._root):
            for name in filenames:
                if name not in ("Chart.yaml", "requirements.yaml"):
                    continue
                path = Path(dirpath) / name
                results.extend(self._build_helm_dependencies(path))
        return results

    def _build_helm_dependencies(self, path: Path) -> List[HelmDependency]:
        """Build Helm dependencies from chart dependencies.

        Given the path to a Helm chart file specifying dependencies, construct
        a list of all dependencies present.

        Parameters
        ----------
        path : `pathlib.Path`
            Path to the file containing the dependencies, either
            ``Chart.yaml`` (the new syntax) or ``requirements.yaml`` (the old
            syntax).

        Returns
        -------
        results : List[`HelmDependency`]
            A list of all discovered Helm chart dependencies.
        """
        results = []
        with path.open() as f:
            requirements = self._yaml.load(f)
        for data in requirements.get("dependencies", []):
            if not all(k in data for k in ("name", "version", "repository")):
                continue
            dependency = HelmDependency(
                name=data["name"],
                version=data["version"],
                path=str(path),
                repository=data["repository"],
            )
            results.append(dependency)
        return results
