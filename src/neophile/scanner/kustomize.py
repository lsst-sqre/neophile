"""Kustomize dependency scanning."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ruamel.yaml import YAML

if TYPE_CHECKING:
    from typing import List

__all__ = [
    "KustomizeDependency",
    "KustomizeScanner",
]


@dataclass(frozen=True, order=True)
class KustomizeDependency:
    """Represents a single Kustomize dependency."""

    url: str
    """The full URL of the dependency."""

    owner: str
    """The owner of the referenced GitHub repository."""

    repo: str
    """The name of the referenced GitHub repository."""

    version: str
    """The version of the dependency."""

    path: str
    """The file that contains the dependency declaration."""


class KustomizeScanner:
    """Scan a source tree for Kustomize version references.

    This recognizes external resources in the format::

       github.com/<owner>/<repo>(.git)?//<path>?ref=<version>

    Parameters
    ----------
    root : `str`
        The root of the source tree.
    """

    _RESOURCE_REGEX = re.compile("github.com/([^/]+)/([^/.]+).*?ref=(.*)")
    """The regex to match external resources and extract data from them.

    The first match group will be the repository owner, the second match group
    will be the repository name, and the third match group will be the tag.
    """

    def __init__(self, root: str) -> None:
        self._root = root
        self._yaml = YAML()

    def scan(self) -> List[KustomizeDependency]:
        """Scan a source tree for version references.

        Returns
        -------
        results : List[`KustomizeDependency`]
            A list of all discovered dependencies.
        """
        results = []

        for dirpath, _, filenames in os.walk(self._root):
            if dirpath.startswith(os.path.join(self._root, "tests")):
                continue
            for name in filenames:
                if name != "kustomization.yaml":
                    continue
                path = Path(dirpath) / name
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
        results : List[`KustomizeDependency`]
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
                path=str(path),
            )
            results.append(dependency)

        return results
