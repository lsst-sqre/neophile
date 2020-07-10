"""Kustomize dependency scanning."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from ruamel.yaml import YAML

from neophile.dependency.kustomize import KustomizeDependency
from neophile.scanner.base import BaseScanner
from neophile.scanner.util import find_files

if TYPE_CHECKING:
    from typing import List

__all__ = ["KustomizeScanner"]


class KustomizeScanner(BaseScanner):
    """Scan a source tree for Kustomize version references.

    This recognizes external resources in the format::

       github.com/<owner>/<repo>(.git)?//<path>?ref=<version>

    Parameters
    ----------
    root : `pathlib.Path`
        The root of the source tree.
    """

    _RESOURCE_REGEX = re.compile("github.com/([^/]+)/([^/.]+).*?ref=(.*)")
    """The regex to match external resources and extract data from them.

    The first match group will be the repository owner, the second match group
    will be the repository name, and the third match group will be the tag.
    """

    def __init__(self, root: Path) -> None:
        self._root = root
        self._yaml = YAML()

    def name(self) -> str:
        return "kustomize"

    def scan(self) -> List[KustomizeDependency]:
        """Scan a source tree for version references.

        Returns
        -------
        results : List[`neophile.dependency.kustomize.KustomizeDependency`]
            A list of all discovered dependencies.
        """
        dependency_paths = find_files(self._root, {"kustomization.yaml"})

        results = []
        for path in dependency_paths:
            results.extend(self._build_kustomize_dependencies(path))

        return results

    def _build_kustomize_dependencies(
        self, path: Path
    ) -> List[KustomizeDependency]:
        """Build Kustomize dependencies from a ``kustomization.yaml`` file.

        Given the path to a ``kustomization.yaml`` file, construct a list of
        all external GitHub dependencies present.

        Parameters
        ----------
        path : `pathlib.Path`
            Path to the ``kustomization.yaml`` file.

        Returns
        -------
        results : List[`neophile.dependency.kustomize.KustomizeDependency`]
            A list of all discovered Helm chart dependencies.
        """
        results = []

        with path.open() as f:
            kustomization = self._yaml.load(f)
        for resource in kustomization.get("resources", []):
            match = self._RESOURCE_REGEX.match(resource)
            if not match:
                continue
            dependency = KustomizeDependency(
                url=resource,
                owner=match.group(1),
                repo=match.group(2),
                version=match.group(3),
                path=path,
            )
            results.append(dependency)

        return results
