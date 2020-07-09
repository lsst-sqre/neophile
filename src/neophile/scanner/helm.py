"""Helm dependency scanning."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from ruamel.yaml import YAML

from neophile.dependency.helm import HelmDependency
from neophile.scanner.base import BaseScanner
from neophile.scanner.util import find_files

if TYPE_CHECKING:
    from typing import List

__all__ = ["HelmScanner"]


class HelmScanner(BaseScanner):
    """Scan a source tree for Helm version references.

    Parameters
    ----------
    root : `pathlib.Path`
        The root of the source tree.
    """

    def __init__(self, root: Path) -> None:
        self._root = root
        self._yaml = YAML()

    def scan(self) -> List[HelmDependency]:
        """Scan a source tree for version references.

        Returns
        -------
        results : List[`HelmDependency`]
            A list of all discovered dependencies.
        """
        wanted_files = {"Chart.yaml", "requirements.yaml"}
        dependency_paths = find_files(self._root, wanted_files)

        results = []
        for path in dependency_paths:
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
                logging.warning("Malformed dependency in %s", str(path))
                continue
            if data["version"].startswith("v"):
                version = data["version"][1:]
            else:
                version = data["version"]
            dependency = HelmDependency(
                name=data["name"],
                version=version,
                path=path,
                repository=data["repository"],
            )
            results.append(dependency)

        return results
