"""Helm dependency scanning."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ruamel.yaml import YAML

if TYPE_CHECKING:
    from typing import List

__all__ = [
    "HelmDependency",
    "HelmScanner",
]


@dataclass(frozen=True)
class HelmDependency:
    """Represents a single Helm dependency."""

    version: str
    """The version of the dependency (may be a match pattern)."""

    path: str
    """The file that contains the dependency declaration."""

    name: str
    """The name of the external dependency."""

    repository: str
    """The name of the chart repository containing the dependency."""


class HelmScanner:
    """Scan a source tree for Helm version references.

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

        Returns
        -------
        results : List[`HelmDependency`]
            A list of all discovered dependencies.
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
        results : List[`Dependency`]
            A list of all discovered Helm chart dependencies.
        """
        results = []

        with path.open() as f:
            requirements = self._yaml.load(f)
        for data in requirements.get("dependencies", []):
            if not all(k in data for k in ("name", "version", "repository")):
                logging.warning("Malformed dependency in %s", str(path))
                continue
            if data["version"].startswith("v"):
                version = data["version"][1:]
            else:
                version = data["version"]
            dependency = HelmDependency(
                name=data["name"],
                version=version,
                path=str(path),
                repository=data["repository"],
            )
            results.append(dependency)

        return results
